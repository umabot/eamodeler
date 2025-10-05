"""
Core logic for generating Level 1 interface documentation.

This module provides the main functionality for processing CSV interface data
and generating Markdown documentation with Mermaid diagrams.
"""
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
except ImportError:
    print("Error: pandas library is required. Install it with: uv add pandas")
    sys.exit(1)


def sanitize_for_mermaid(text: str) -> str:
    """Sanitize text for use as Mermaid node IDs and filenames."""
    if not isinstance(text, str):
        text = str(text)
    
    sanitized = re.sub(r'[^a-zA-Z0-9]', '_', text)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip('_')
    
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'N_' + sanitized
    
    if not sanitized:
        sanitized = 'Node_' + str(hash(text))[:8]
    
    return sanitized


def generate_markdown(filtered_df: pd.DataFrame, app_name: str, direction: str, country: Optional[str]) -> str:
    """Generate Markdown content with Mermaid diagram and interface details table."""
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build header
    if direction == 'all':
        direction_text = "source and target"
    else:
        direction_text = direction

    country_text = f" ({country})" if country else ""
    markdown_content = f"""# Interface Documentation for: {app_name}{country_text}

>[!Important] Generated on: {timestamp}
This document outlines all interfaces where {app_name} acts as the {direction_text}{" in " + country if country else ""}.

## Visual Flow Diagram

```mermaid
graph LR;
"""
    
    # Add style for the main node
    main_node_id = sanitize_for_mermaid(app_name)
    markdown_content += f"    style {main_node_id} fill:#007bff,stroke:#333,stroke-width:2px,color:#fff\n"
    
    # Build Mermaid diagram links
    for _, row in filtered_df.iterrows():
        source_app = str(row['Source System/ APP']).strip()
        target_app = str(row['Target System/APP']).strip()
        int_id = str(row['INT ID']).strip()
        
        source_id = sanitize_for_mermaid(source_app)
        target_id = sanitize_for_mermaid(target_app)
        
        # Escape labels for Mermaid by wrapping in quotes
        source_label = f'"{source_app}"'
        target_label = f'"{target_app}"'
        
        markdown_content += f'    {source_id}[{source_label}] -- "{int_id}" --> {target_id}[{target_label}];\n'
    
    # Close Mermaid block
    markdown_content += "```\n\n"
    
    # Add connected applications summary table
    if direction == 'target':
        connected_column = 'Source System/ APP'
        connected_role = 'Source Applications'
        connected_apps = filtered_df[connected_column].value_counts().sort_index()
        
        markdown_content += f"""## Connected {connected_role}

| Application | Number of Interfaces |
| ----------- | -------------------- |
"""
        for app_name_conn, interface_count in connected_apps.items():
            markdown_content += f"| {app_name_conn} | {interface_count} |\n"

    elif direction == 'source':
        connected_column = 'Target System/APP'
        connected_role = 'Target Applications'
        connected_apps = filtered_df[connected_column].value_counts().sort_index()

        markdown_content += f"""## Connected {connected_role}

| Application | Number of Interfaces |
| ----------- | -------------------- |
"""
        for app_name_conn, interface_count in connected_apps.items():
            markdown_content += f"| {app_name_conn} | {interface_count} |\n"

    else:  # direction == 'all'
        app_name_lower = app_name.lower()
        
        # Source interfaces (outgoing)
        source_df = filtered_df[filtered_df['Source System/ APP'].str.lower().str.contains(app_name_lower, na=False)]
        target_apps = source_df['Target System/APP'].value_counts().sort_index()
        
        if not target_apps.empty:
            markdown_content += """## Connected Target Applications (Outgoing)

| Application | Number of Interfaces |
| ----------- | -------------------- |
"""
            for app_name_conn, interface_count in target_apps.items():
                markdown_content += f"| {app_name_conn} | {interface_count} |\n"
            markdown_content += "\n"

        # Target interfaces (incoming)
        target_df = filtered_df[filtered_df['Target System/APP'].str.lower().str.contains(app_name_lower, na=False)]
        source_apps = target_df['Source System/ APP'].value_counts().sort_index()

        if not source_apps.empty:
            markdown_content += """## Connected Source Applications (Incoming)

| Application | Number of Interfaces |
| ----------- | -------------------- |
"""
            for app_name_conn, interface_count in source_apps.items():
                markdown_content += f"| {app_name_conn} | {interface_count} |\n"
    
    markdown_content += "\n"
    
    # Add interface details table
    country_display = country if country else "All Countries"
    markdown_content += f"""## Interface Details

**Country:** {country_display}  
**Application:** {app_name}  
**Role:** {direction.title()}  
**Total Interfaces:** {len(filtered_df)}

| INT ID | Source App | Target App | Interface Description | Integration Pattern | Direction | Country |
| ------ | ---------- | ---------- | -------------------- | ------------------- | --------- | ------- |
"""
    
    # Add table rows
    for _, row in filtered_df.iterrows():
        int_id = str(row['INT ID']).strip().replace('\n', ' ').replace('\r', ' ')
        source_app = str(row['Source System/ APP']).strip().replace('\n', ' ').replace('\r', ' ')
        target_app = str(row['Target System/APP']).strip().replace('\n', ' ').replace('\r', ' ')
        interface_desc = str(row.get('Interface short Description', 'N/A')).strip().replace('\n', ' ').replace('\r', ' ')
        integration_pattern = str(row.get('Integration Pattern', 'N/A')).strip().replace('\n', ' ').replace('\r', ' ')
        direction_col = str(row.get('Direction', 'N/A')).strip().replace('\n', ' ').replace('\r', ' ')
        country_col = str(row.get('Country', 'N/A')).strip().replace('\n', ' ').replace('\r', ' ')
        
        markdown_content += f"| {int_id} | {source_app} | {target_app} | {interface_desc} | {integration_pattern} | {direction_col} | {country_col} |\n"
    
    return markdown_content


def generate_interface_documentation(
    input_file: Path,
    app_name: str,
    direction: str,
    country: Optional[str] = None,
    output_dir: Path = Path("output")
) -> tuple[Path, int]:
    """
    Generate interface documentation and return output file path and count.
    
    Args:
        input_file: Path to the CSV file containing interface data
        app_name: Name of the application to analyze
        direction: Analysis perspective ('source', 'target', or 'all')
        country: Optional country code filter
        output_dir: Directory for output file
        
    Returns:
        Tuple of (Path to the generated markdown file, number of interfaces documented)
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If CSV format is invalid or app not found
        Exception: For other processing errors
    """
    # Validate input file
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Load CSV with encoding detection
    df = None
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise ValueError("Could not read CSV file with any supported encoding")
    
    # Clean column headers
    df.columns = df.columns.str.strip()
    
    # Validate required columns
    required_columns = ['Source System/ APP', 'Target System/APP', 'INT ID']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Clean key text columns
    for col in ['Source System/ APP', 'Target System/APP', 'Country']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Clean data - remove rows with missing critical data
    df = df.dropna(subset=['Source System/ APP', 'Target System/APP', 'INT ID'])
    
    # Handle country filtering
    if country:
        if 'Country' in df.columns:
            original_count = len(df)
            df = df[df['Country'].str.upper() == country.upper()]
            if df.empty:
                raise ValueError(f"No data found for country: {country}")
        else:
            raise ValueError("Country filter specified but 'Country' column not found in CSV")
    
    # Filter by application and direction
    app_name_lower = app_name.lower()
    
    if direction == 'source':
        filtered_df = df[df['Source System/ APP'].str.lower().str.contains(app_name_lower, na=False)]
    elif direction == 'target':
        filtered_df = df[df['Target System/APP'].str.lower().str.contains(app_name_lower, na=False)]
    else:  # direction == 'all'
        source_matches = df['Source System/ APP'].str.lower().str.contains(app_name_lower, na=False)
        target_matches = df['Target System/APP'].str.lower().str.contains(app_name_lower, na=False)
        filtered_df = df[source_matches | target_matches]
    
    if filtered_df.empty:
        raise ValueError(f"No interfaces found for application '{app_name}' in direction '{direction}'" + 
                        (f" for country '{country}'" if country else ""))
    
    # Generate markdown content
    markdown_content = generate_markdown(filtered_df, app_name, direction, country)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    country_suffix = f"_{country}" if country else "_ALL"
    safe_app_name = sanitize_for_mermaid(app_name)
    output_filename = f"{safe_app_name}{country_suffix}_{direction}_interfaces.md"
    output_file = output_dir / output_filename
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return output_file, len(filtered_df)