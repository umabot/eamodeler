"""
Entity Relationship Diagram (ERD) and Class Diagram generator for canonical data models.

This module provides functionality for generating Mermaid.js diagrams from CSV files
that define a canonical logical data model, with filtering by data domains.
"""
import re
import sys
from pathlib import Path
from typing import List

try:
    import pandas as pd
except ImportError:
    print("Error: pandas library is required. Install it with: uv add pandas")
    sys.exit(1)


def sanitize_for_mermaid_erd(text: str) -> str:
    """
    Sanitize text for use in Mermaid ERD and Class diagrams.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text suitable for Mermaid syntax
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Handle common problematic values
    if text.lower() in ['nan', 'null', 'none', '']:
        return 'string'
    
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', text)
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it starts with a letter (Mermaid requirement)
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'Entity_' + sanitized
    
    # Handle empty strings
    if not sanitized:
        sanitized = 'string'
    
    return sanitized


def load_and_validate_csv(file_path: str, required_columns: List[str]) -> pd.DataFrame:
    """
    Load and validate a CSV file with required columns.
    
    Args:
        file_path: Path to the CSV file
        required_columns: List of required column names
        
    Returns:
        Loaded and validated DataFrame
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    # Check if file exists
    if not Path(file_path).exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    # Load CSV with encoding detection
    df = None
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise ValueError(f"Could not read CSV file with any supported encoding: {file_path}")
    
    # Clean column headers
    df.columns = df.columns.str.strip()
    
    # Validate required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        available_columns = list(df.columns)
        raise ValueError(
            f"Missing required columns in {file_path}: {missing_columns}. "
            f"Available columns: {available_columns}"
        )
    
    # Clean string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()
    
    return df


def get_cardinality_connector(cardinality: str) -> str:
    """
    Map cardinality notation to Mermaid ERD connector syntax.
    
    Args:
        cardinality: Cardinality string (e.g., "1:N", "1:1", "N:M")
        
    Returns:
        Mermaid connector syntax
    """
    cardinality = str(cardinality).strip().upper()
    
    cardinality_mapping = {
        "1:N": "|o--o{",
        "1:1": "|o--||", 
        "N:M": "}o--o{",
        "N:1": "}o--o|",
        "1:M": "|o--o{",  # Alternative notation for 1:N
        "M:N": "}o--o{",  # Alternative notation for N:M
        "M:1": "}o--o|",  # Alternative notation for N:1
        "ONE_TO_MANY": "|o--o{",
        "ONE_TO_ONE": "|o--||",
        "MANY_TO_MANY": "}o--o{",
        "MANY_TO_ONE": "}o--o|"
    }
    
    # Default to one-to-many for unknown cardinality values (valid Mermaid syntax)
    return cardinality_mapping.get(cardinality, "|o--o{")


def generate_filename_from_domains(data_domains: List[str], diagram_type: str) -> str:
    """
    Generate a filename from data domains and diagram type.
    
    Args:
        data_domains: List of data domain names
        diagram_type: Type of diagram (erDiagram or classDiagram)
        
    Returns:
        Sanitized filename
    """
    # Sanitize domain names for filename
    sanitized_domains = []
    for domain in data_domains:
        # Replace spaces and special chars with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9]', '_', domain)
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')
        sanitized_domains.append(sanitized)
    
    # Join domains with underscores
    domains_part = '_'.join(sanitized_domains)
    
    # Create filename
    filename = f"{domains_part}_{diagram_type}.md"
    
    return filename


def generate_mermaid_diagram(
    classes_csv_path: str,
    attributes_csv_path: str,
    relationships_csv_path: str,
    data_domains: List[str],
    diagram_type: str = "erDiagram",
    output_dir: str = "output"
) -> Path:
    """
    Generate Mermaid.js diagrams from canonical data model CSV files.
    
    This function creates Entity Relationship Diagrams (ERD) or Class Diagrams
    from CSV files defining a canonical logical data model, filtered by data domains.
    
    Args:
        classes_csv_path: Path to CSV file containing class/entity definitions
        attributes_csv_path: Path to CSV file containing attribute definitions  
        relationships_csv_path: Path to CSV file containing relationship definitions
        data_domains: List of data domain names to filter by
        diagram_type: Type of diagram to generate ("erDiagram" or "classDiagram")
        output_dir: Directory to save the generated diagram file
        
    Returns:
        Path to the generated markdown file
        
    Raises:
        FileNotFoundError: If any input CSV file doesn't exist
        ValueError: If CSV files are missing required columns or data validation fails
    """
    # Validate diagram type
    valid_diagram_types = ["erDiagram", "classDiagram"]
    if diagram_type not in valid_diagram_types:
        raise ValueError(f"Invalid diagram_type: {diagram_type}. Must be one of: {valid_diagram_types}")
    
    # Load and validate CSV files
    print(f"Loading classes data from: {classes_csv_path}")
    classes_df = load_and_validate_csv(
        classes_csv_path, 
        required_columns=["Data Domain", "Data Entity"]
    )
    
    print(f"Loading attributes data from: {attributes_csv_path}")
    attributes_df = load_and_validate_csv(
        attributes_csv_path,
        required_columns=["Data Entity", "Attribute", "Data Type", "PK"]
    )
    
    print(f"Loading relationships data from: {relationships_csv_path}")
    relationships_df = load_and_validate_csv(
        relationships_csv_path,
        required_columns=["Parent Entity", "Child Entity", "Parent to Child Verb Phrase", "Cardinality"]
    )
    
    # Filter classes by data domains
    print(f"Filtering by data domains: {data_domains}")
    filtered_classes = classes_df[classes_df["Data Domain"].isin(data_domains)]
    
    if filtered_classes.empty:
        available_domains = classes_df["Data Domain"].unique().tolist()
        raise ValueError(
            f"No entities found for the specified data domains: {data_domains}. "
            f"Available domains: {available_domains}"
        )
    
    # Get the list of entities for filtering
    selected_entities = filtered_classes["Data Entity"].unique().tolist()
    print(f"Found {len(selected_entities)} entities in selected domains")
    
    # Filter attributes by selected entities
    filtered_attributes = attributes_df[attributes_df["Data Entity"].isin(selected_entities)]
    
    # Filter relationships - both parent and child must be in selected entities
    filtered_relationships = relationships_df[
        (relationships_df["Parent Entity"].isin(selected_entities)) &
        (relationships_df["Child Entity"].isin(selected_entities))
    ]
    
    # Start building the Mermaid diagram
    mermaid_content = f"{diagram_type}\n"
    
    # Generate entities and their attributes
    for entity in sorted(selected_entities):
        sanitized_entity = sanitize_for_mermaid_erd(entity)
        mermaid_content += f"    {sanitized_entity} {{\n"
        
        # Get attributes for this entity
        entity_attributes = filtered_attributes[filtered_attributes["Data Entity"] == entity]
        
        # Sort attributes to have primary keys first
        entity_attributes = entity_attributes.sort_values(
            by=["PK", "Attribute"], 
            ascending=[False, True]
        )
        
        for _, attr_row in entity_attributes.iterrows():
            attribute_name = sanitize_for_mermaid_erd(attr_row["Attribute"])
            
            # Handle data type - clean up invalid values
            raw_data_type = attr_row["Data Type"]
            if pd.isna(raw_data_type) or str(raw_data_type).lower() in ['nan', '', 'null']:
                data_type = "string"  # Default to string for missing data types
            elif str(raw_data_type).lower() in ['multivalued', 'multivalue', 'multiocc']:
                data_type = "array"   # Convert multivalued to array
            else:
                data_type = sanitize_for_mermaid_erd(str(raw_data_type))
            
            # Validate that the data type is suitable for Mermaid
            if not data_type or data_type == "_":
                data_type = "string"  # Fallback to string
                
            is_pk = str(attr_row["PK"]).lower() in ["yes", "true", "1"]
            
            pk_suffix = " PK" if is_pk else ""
            mermaid_content += f"        {data_type} {attribute_name}{pk_suffix}\n"
        
        mermaid_content += "    }\n"
    
    # Add a blank line before relationships
    if not filtered_relationships.empty:
        mermaid_content += "\n"
    
    # Generate relationships
    for _, rel_row in filtered_relationships.iterrows():
        parent_entity = sanitize_for_mermaid_erd(rel_row["Parent Entity"])
        child_entity = sanitize_for_mermaid_erd(rel_row["Child Entity"])
        verb_phrase = rel_row["Parent to Child Verb Phrase"]
        cardinality = rel_row["Cardinality"]
        
        connector = get_cardinality_connector(cardinality)
        
        mermaid_content += f'    {parent_entity} {connector} {child_entity} : "{verb_phrase}"\n'
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    output_filename = generate_filename_from_domains(data_domains, diagram_type)
    output_file = output_path / output_filename
    
    # Create the complete markdown content
    markdown_content = f"""# {diagram_type.title()} for Data Domains: {', '.join(data_domains)}

Generated from canonical data model CSV files.

**Entities included:** {len(selected_entities)}  
**Relationships included:** {len(filtered_relationships)}  
**Data Domains:** {', '.join(data_domains)}

```mermaid
{mermaid_content}```

## Entity Summary

| Entity | Attributes | Domain |
| ------ | ---------- | ------ |
"""
    
    # Add entity summary table
    for entity in sorted(selected_entities):
        entity_attributes = filtered_attributes[filtered_attributes["Data Entity"] == entity]
        attr_count = len(entity_attributes)
        
        # Get domain for this entity
        entity_domain = filtered_classes[filtered_classes["Data Entity"] == entity]["Data Domain"].iloc[0]
        
        markdown_content += f"| {entity} | {attr_count} | {entity_domain} |\n"
    
    # Write the file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    # Print confirmation message
    print(f"✅ Mermaid diagram generated successfully!")
    print(f"📄 Output file: {output_file}")
    print(f"📊 Entities: {len(selected_entities)}, Relationships: {len(filtered_relationships)}")
    
    return output_file