"""
RICEFW Transformer - Transform S4 RICEFW CSV to MDW Flow format.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple


# Input columns to read from source CSV
INPUT_COLUMNS = [
    'ID', 'ID RICEFW', 'Stream', 'Business activity (BPML level 4)', 'Core Model', 'Country',
    'Name', 'Business Object SAP', 'Action in SAP', 'Scoping', 'Scoping ID',
    'Status', 'Description', 'RICEFW  Type', 'Pilot / Roll-out', 'Quantity',
    'From', 'To', 'Data Type', 'Data Object'
]

# Output columns in required order
OUTPUT_COLUMNS = [
    'New/Review', 'Comments', 'Scoping ID', 'E2E BP', 'Data Domain',
    'Business Model', 'Core', 'Data Type', 'Reference', 'seq', 'Country/BU',
    'Status', 'INT ID', 'Interface short Description', 'Source System/ APP',
    'Target System/APP', 'Integration Pattern', 'Direction', 'Middleware',
    'Protocol', 'Data Payload Format', 'Data Payload Description'
]


# Lookup table for Data Domain determination
# Key: (business_object_sap, data_object) -> return_value
DATA_DOMAIN_MAPPING = {
    ('G/L Account', 'Chart of Accounts'): 'Financial Organization↳Group Chart of Account Hierarchy',
    ('Supplier', 'Supplier'): 'Supplier↳Business partner',
    ('GL Accounts structure', 'GL Accounts'): 'Financial Organization↳Group Chart of Account Hierarchy',
    ('Group chart of account (Anaplan GL accounts hierarchy)', 'GL Accounts'): 'Financial Organization↳Group Chart of Account Hierarchy',
    ('Cost center', 'Cost Center'): 'Financial Organization↳Cost Center',
    ('Profit center', 'Profit Center'): 'Financial Organization↳Profit Center',
    ('Retail Site', 'Profit Center group'): 'Site↳Site',
    ('Profit center', 'Operational Hierarchy'): 'Financial Organization↳Profit Center Hierarchy',
    ('Customer', 'Customer'): 'Customer & Contract↳Customer',
    ('Customer hierarchy', 'Customer'): 'Customer & Contract↳Customer',
    ('Business partner (Supplier master data)', 'Supplier'): 'Supplier↳Business partner',
    ('Value list (Supplier & product)', 'Value list'): 'Product↳Price Conditions',
    ('Bank', 'Supplier'): 'Supplier↳Supplier bank Details',
    ('Plant', 'SDP'): 'Site↳SDP',
    ('Product', 'Raw Materials'): 'Product↳Material master data/ Product',
}


def determine_data_domain(business_object_sap: str, data_object: str, data_type: str) -> str:
    """
    Determine the Data Domain based on Business Object SAP, Data Object, and Data Type.
    
    Args:
        business_object_sap: Business Object SAP value
        data_object: Data Object value
        data_type: Data Type value
        
    Returns:
        Data Domain from lookup table if data_type is 'Master Data' and match found,
        otherwise empty string
    """
    # Only process Master Data type
    if pd.isna(data_type) or str(data_type).strip() != 'Master Data':
        return ""
    
    # Normalize inputs
    bo_sap = str(business_object_sap).strip() if not pd.isna(business_object_sap) else ""
    data_obj = str(data_object).strip() if not pd.isna(data_object) else ""
    
    # Lookup in the mapping table
    key = (bo_sap, data_obj)
    return DATA_DOMAIN_MAPPING.get(key, "")


def determine_core(from_system: str, to_system: str) -> str:
    """
    Determine the Core value based on From and To systems.
    
    Business logic:
    - If both systems are core apps: 'core - core'
    - If neither system is a core app: 'local - local'
    - Otherwise (one is core, one is local): 'core - local'
    
    Core apps: S4, NMO, Esker, MDM
    
    Args:
        from_system: Source system (From)
        to_system: Target system (To)
        
    Returns:
        Core value string ('core - core', 'local - local', or 'core - local')
    """
    # Define core apps (case-insensitive matching)
    core_apps = {'s4', 'nmo', 'esker', 'mdm'}
    
    # Normalize inputs for comparison
    from_normalized = str(from_system).strip().lower() if not pd.isna(from_system) else ""
    to_normalized = str(to_system).strip().lower() if not pd.isna(to_system) else ""
    
    from_is_core = from_normalized in core_apps
    to_is_core = to_normalized in core_apps
    
    if from_is_core and to_is_core:
        return 'core - core'
    elif not from_is_core and not to_is_core:
        return 'local - local'
    else:
        return 'core - local'


# Lookup table for system name to APP code mapping
SYSTEM_TO_APP_MAPPING = {
    'Anaplan': 'APP-0109 - Anaplan',
    'Diapason': 'APP-0090 - Diapasan',
    'ESKER': 'APP-0366 - Esker',
    'HR System': 'APP-0009 - HR employee records',
    'MDM': 'APP-0011 - MDM',
    'NMO': 'APP-0367 - NMO',
    'Operational ERP': 'APP-0374 - PROGIB',
    'Payroll system': 'APP-0009 - HR employee records',
    'S4': 'APP-0376 - SAP 4/HANA',
    'T&E System': 'APP-0088 - SAP Concur',
    'Thetys': 'APP-0159 - Thetys',
    'Thetys Mandate': 'APP-0330 - Thétys Mandat',
    'Data': 'APP-0204 - Azure Datalake',
    'Data platefom': 'APP-0204 - Azure Datalake',
    'Data platfom': 'APP-0204 - Azure Datalake',
    'Datalake': 'APP-0204 - Azure Datalake',
    'HMRC': 'UK-9995 - Unknown - HMRC',
    'MDM  Cost': 'APP-0011 - MDM',
    'MDM  Profit': 'APP-0011 - MDM',
    'PowerBI': 'APP-0204 - Azure Datalake',
    'BFC': 'APP-0215 - BFC',
    'PROGIB': 'APP-0374 - PROGIB',
}


def _lookup_app_code(value: str) -> str:
    """
    Look up the APP code for a given system name.
    
    Args:
        value: System name to look up
        
    Returns:
        APP code if found, otherwise the original value
    """
    if pd.isna(value):
        return ""
    value_str = str(value).strip()
    return SYSTEM_TO_APP_MAPPING.get(value_str, value_str)


def determine_source_app(from_value: str) -> str:
    """
    Determine the Source System/APP from the From column.
    
    Args:
        from_value: Value from the 'From' column in S4RICEFW
        
    Returns:
        Source System/APP value (mapped to APP code if found)
    """
    return _lookup_app_code(from_value)


def determine_target_app(to_value: str) -> str:
    """
    Determine the Target System/APP from the To column.
    
    Args:
        to_value: Value from the 'To' column in S4RICEFW
        
    Returns:
        Target System/APP value (mapped to APP code if found)
    """
    return _lookup_app_code(to_value)


def transform_data_type(data_type: str) -> str:
    """
    Transform Data Type value according to mapping rules.
    
    Args:
        data_type: Original Data Type value
        
    Returns:
        Transformed Data Type ('Master', 'Transactional', or original value)
    """
    if pd.isna(data_type):
        return ""
    
    mapping = {
        'Master Data': 'Master',
        'Transactional Data': 'Transactional'
    }
    return mapping.get(data_type.strip(), data_type)


def transform_short_description(name: str, business_object_sap: str) -> str:
    """
    Generate Interface short Description by concatenating Name and Business Object SAP.
    
    Args:
        name: Interface name
        business_object_sap: Business Object SAP value
        
    Returns:
        Concatenated short description
    """
    name_str = str(name) if not pd.isna(name) else ""
    bo_str = str(business_object_sap) if not pd.isna(business_object_sap) else ""
    
    parts = [p for p in [name_str.strip(), bo_str.strip()] if p]
    return " ".join(parts)


def transform_data_payload_description(action_in_sap: str, business_object_sap: str, description: str) -> str:
    """
    Generate Data Payload Description from Action, Business Object SAP, and Description.
    
    Args:
        action_in_sap: Action in SAP value
        business_object_sap: Business Object SAP value
        description: Description value
        
    Returns:
        Formatted data payload description
    """
    action_str = str(action_in_sap) if not pd.isna(action_in_sap) else ""
    bo_str = str(business_object_sap) if not pd.isna(business_object_sap) else ""
    desc_str = str(description) if not pd.isna(description) else ""
    
    # Format: "Action Business Object SAP: Description"
    prefix_parts = [p for p in [action_str.strip(), bo_str.strip()] if p]
    prefix = " ".join(prefix_parts)
    
    if prefix and desc_str.strip():
        return f"{prefix}: {desc_str.strip()}"
    elif prefix:
        return prefix
    else:
        return desc_str.strip()


def transform_ricefw(input_file: Path, output_dir: Path | None = None) -> Tuple[Path, int]:
    """
    Transform S4 RICEFW CSV to MDW Flow format.
    
    Args:
        input_file: Path to the input CSV file
        output_dir: Optional output directory (defaults to same as input file)
        
    Returns:
        Tuple of (output_file_path, row_count)
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If required columns are missing
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read input CSV
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    
    # Verify required columns exist
    missing_columns = [col for col in INPUT_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Filter rows: RICEFW Type = 'Interface' and Status in {'Validated', 'To Review'}
    valid_statuses = {'Validated', 'To review'}
    df = df[
        (df['RICEFW  Type'] == 'Interface') & 
        (df['Status'].isin(valid_statuses))
    ].copy()
    
    if len(df) == 0:
        raise ValueError("No rows match the filter criteria (RICEFW Type='Interface' and Status in {'Validated', 'To Review'})")
    
    # Special handling: Duplicate 'T&E System' rows into two output rows
    te_mask = df['From'] == 'T&E System'
    if te_mask.any():
        df_normal = df[~te_mask].copy()
        df_split = df[te_mask].copy()
        
        # Row 1: SAP Concur (UK)
        df_row1 = df_split.copy()
        df_row1['From'] = 'APP-0088 - SAP Concur'
        df_row1['ID RICEFW'] = df_row1['ID RICEFW'].astype(str) + '-bis'
        df_row1['Country'] = 'UK'
        
        # Row 2: Expensya (FR)
        df_row2 = df_split.copy()
        df_row2['From'] = 'APP-0342 - Expensya'
        df_row2['ID RICEFW'] = df_row2['ID RICEFW'].astype(str) + '-bis'
        df_row2['Country'] = 'FR'
        
        # Combine back
        df = pd.concat([df_normal, df_row1, df_row2], ignore_index=True)

    # Special handling: Duplicate 'Payroll system' rows into two output rows
    payroll_mask = df['From'] == 'Payroll system'
    if payroll_mask.any():
        df_normal = df[~payroll_mask].copy()
        df_split = df[payroll_mask].copy()
        
        # Row 1: HR employee records (UK)
        df_row1 = df_split.copy()
        df_row1['From'] = 'APP-0009 - HR employee records'
        df_row1['ID RICEFW'] = df_row1['ID RICEFW'].astype(str) + '-bis'
        df_row1['Country'] = 'UK'
        
        # Row 2: HR Access (FR)
        df_row2 = df_split.copy()
        df_row2['From'] = 'APP-0188 - HR Access'
        df_row2['ID RICEFW'] = df_row2['ID RICEFW'].astype(str) + '-bis'
        df_row2['Country'] = 'FR'
        
        # Combine back
        df = pd.concat([df_normal, df_row1, df_row2], ignore_index=True)
    
    # Create output DataFrame with same index as input to ensure row count matches
    output_df = pd.DataFrame(index=df.index)
    
    # Apply transformation rules
    
    # Constant values
    output_df['New/Review'] = 'New'
    output_df['Status'] = 'In Definition'
    output_df['Reference'] = 'RICEFW'
    
    # Direct mappings
    output_df['Scoping ID'] = df['Scoping ID'].fillna('')
    output_df['E2E BP'] = df['Stream'].fillna('')
    output_df['Business Model'] = df['Core Model'].fillna('')
    output_df['Country/BU'] = df['Country'].fillna('')
    output_df['INT ID'] = df['ID RICEFW'].fillna('')
    output_df['Source System/ APP'] = df['From'].apply(determine_source_app)
    output_df['Target System/APP'] = df['To'].apply(determine_target_app)
    
    # Transformed columns
    output_df['Data Type'] = df['Data Type'].apply(transform_data_type)
    
    output_df['Interface short Description'] = df.apply(
        lambda row: transform_short_description(row['Name'], row['Business Object SAP']),
        axis=1
    )
    
    output_df['Data Payload Description'] = df.apply(
        lambda row: transform_data_payload_description(
            row['Action in SAP'], 
            row['Business Object SAP'], 
            row['Description']
        ),
        axis=1
    )
    
    # Placeholder function columns
    output_df['Data Domain'] = df.apply(
        lambda row: determine_data_domain(
            row['Business Object SAP'],
            row['Data Object'],
            row['Data Type']
        ),
        axis=1
    )
    
    output_df['Core'] = df.apply(
        lambda row: determine_core(row['From'], row['To']),
        axis=1
    )
    
    # Empty columns
    output_df['Comments'] = ''
    output_df['seq'] = ''
    output_df['Integration Pattern'] = ''
    output_df['Direction'] = ''
    output_df['Middleware'] = ''
    output_df['Protocol'] = ''
    output_df['Data Payload Format'] = ''
    
    # Reorder columns to match expected output
    output_df = output_df[OUTPUT_COLUMNS]
    
    # Determine output path
    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    output_filename = f"{input_path.stem}_output.csv"
    output_path = output_dir / output_filename
    
    # Save output CSV
    output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    return output_path, len(output_df)
