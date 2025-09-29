#!/usr/bin/env python3
"""
Interface Documentation Generator

This script reads a CSV file containing system interface data, filters it based on user input,
and generates a Markdown file containing a Mermaid.js flow diagram and a detailed data table.

Usage:
    python generate_interface_docs.py <input_file> <app_name> <direction> <country> [--output_dir <dir>]

Example:
    python generate_interface_docs.py "input/data.csv" "APP-0100 - SAP FICO" "target" "ES"
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
import re

try:
    import pandas as pd
except ImportError:
    print("Error: pandas library is required. Install it with: uv add pandas")
    sys.exit(1)


def sanitize_for_mermaid(text):
    """
    Sanitize text for use as Mermaid node IDs and filenames.
    
    Args:
        text (str): Input text to sanitize
        
    Returns:
        str: Sanitized text with only letters, numbers, and underscores
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Replace any character that is not a letter or number with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9]', '_', text)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure the ID starts with a letter (Mermaid requirement)
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'N_' + sanitized
    
    # Ensure we have a valid ID (fallback if empty)
    if not sanitized:
        sanitized = 'Node_' + str(hash(text))[:8]
    
    return sanitized


def generate_markdown(filtered_df, app_name, direction, country):
    """
    Generate Markdown content with Mermaid diagram and interface details table.
    
    Args:
        filtered_df (pd.DataFrame): Filtered DataFrame with interface data
        app_name (str): Name of the application
        direction (str): Direction of analysis ('source' or 'target')
        country (str): Country code
        
    Returns:
        str: Complete Markdown content
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build header
    markdown_content = f"""# Interface Documentation for: {app_name} ({country})

> Generated on: {timestamp}

This document outlines all interfaces where {app_name} acts as the {direction} in {country}.

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
        
        # Escape labels for Mermaid by wrapping in quotes if they contain special characters
        source_label = f'"{source_app}"' if any(c in source_app for c in ['-', '/', '\\', '(', ')', '[', ']']) else source_app
        target_label = f'"{target_app}"' if any(c in target_app for c in ['-', '/', '\\', '(', ')', '[', ']']) else target_app
        
        markdown_content += f'    {source_id}[{source_label}] -- "{int_id}" --> {target_id}[{target_label}];\n'
    
    # Close Mermaid block
    markdown_content += "```\n\n"
    
    # Add connected applications summary table
    if direction == 'target':
        connected_column = 'Source System/ APP'
        connected_role = 'Source Applications'
    else:
        connected_column = 'Target System/APP'
        connected_role = 'Target Applications'
    
    # Get unique connected applications and count interfaces for each
    connected_apps = filtered_df[connected_column].value_counts().sort_index()
    
    markdown_content += f"""## Connected {connected_role}

| Application | Number of Interfaces |
| ----------- | -------------------- |
"""
    
    for app_name_conn, interface_count in connected_apps.items():
        markdown_content += f"| {app_name_conn} | {interface_count} |\n"
    
    markdown_content += "\n"
    
    # Add interface details table
    markdown_content += f"""## Interface Details

**Country:** {country}  
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
        direction_value = str(row.get('Direction', 'N/A')).strip().replace('\n', ' ').replace('\r', ' ')
        country_value = str(row.get('Country', 'N/A')).strip().replace('\n', ' ').replace('\r', ' ')
        
        markdown_content += f"| {int_id} | {source_app} | {target_app} | {interface_desc} | {integration_pattern} | {direction_value} | {country_value} |\n"
    
    return markdown_content


def main():
    """Main execution function."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Generate interface documentation from CSV data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_interface_docs.py "input/MDW-FLOW-31970-DataflowsInventoryAS-IS_v0.5.csv" "APP-0100 - SAP FICO" "target" "ES"
  python generate_interface_docs.py "input/data.csv" "SAP System" "source" "FR" --output_dir "reports"
        """
    )
    
    parser.add_argument('input_file', help='Path to the source CSV file')
    parser.add_argument('app_name', help='Name of the application to analyze (case-insensitive)')
    parser.add_argument('direction', choices=['source', 'target'], 
                       help='Analysis perspective: "source" or "target"')
    parser.add_argument('country', help='Country code to filter by (e.g., ES, FR, IT, UK)')
    parser.add_argument('--output_dir', default='output', 
                       help='Directory for output file (default: output)')
    
    args = parser.parse_args()
    
    try:
        # Read CSV file with encoding detection
        print(f"Reading CSV file: {args.input_file}")
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(args.input_file, encoding=encoding)
                print(f"Successfully read file with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Could not read CSV file with any supported encoding")
        
        # Clean column headers
        df.columns = df.columns.str.strip()
        
        # Display available columns for debugging
        print(f"Available columns: {list(df.columns)}")
        
        # Clean key text columns
        if 'Source System/ APP' in df.columns:
            df['Source System/ APP'] = df['Source System/ APP'].astype(str).str.strip()
        if 'Target System/APP' in df.columns:
            df['Target System/APP'] = df['Target System/APP'].astype(str).str.strip()
        if 'Country' in df.columns:
            df['Country'] = df['Country'].astype(str).str.strip()
        
        # Validate country
        if 'Country' not in df.columns:
            print("Error: 'Country' column not found in CSV file")
            print(f"Available columns: {list(df.columns)}")
            sys.exit(1)
        
        # Check if the specified country exists in the data
        available_countries = df['Country'].dropna().unique()
        if args.country not in available_countries:
            print(f"Error: Invalid country '{args.country}'")
            print(f"Available countries: {sorted(available_countries)}")
            sys.exit(1)
        
        print(f"Valid country: {args.country}")
        
        # Determine filter column based on direction
        if args.direction == 'source':
            filter_column = 'Source System/ APP'
        else:  # target
            filter_column = 'Target System/APP'
        
        if filter_column not in df.columns:
            print(f"Error: Column '{filter_column}' not found in CSV file")
            print(f"Available columns: {list(df.columns)}")
            sys.exit(1)
        
        # Filter data by country first, then by application (both case-insensitive)
        print(f"Filtering for country: {args.country} and {args.app_name} as {args.direction}")
        country_filtered_df = df[df['Country'].str.contains(args.country, case=False, na=False)]
        
        if country_filtered_df.empty:
            print(f"No data found for country '{args.country}'")
            sys.exit(0)
        
        filtered_df = country_filtered_df[country_filtered_df[filter_column].str.contains(args.app_name, case=False, na=False)]
        
        if filtered_df.empty:
            print(f"No interfaces found for '{args.app_name}' as {args.direction} in country '{args.country}'")
            sys.exit(0)
        
        print(f"Found {len(filtered_df)} interface(s)")
        
        # Ask for output filename
        default_filename = f"{sanitize_for_mermaid(args.app_name)}_{args.country}_{args.direction}_interfaces.md"
        print(f"\nDefault filename: {default_filename}")
        user_filename = input("Enter output filename (press Enter for default): ").strip()
        
        if not user_filename:
            output_filename = default_filename
        else:
            # Ensure .md extension
            if not user_filename.endswith('.md'):
                output_filename = user_filename + '.md'
            else:
                output_filename = user_filename
        
        # Create output directory if it doesn't exist
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate markdown content
        print("Generating markdown content...")
        markdown_content = generate_markdown(filtered_df, args.app_name, args.direction, args.country)
        
        # Write output file
        output_path = output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\nSuccess! Documentation generated: {output_path}")
        print(f"File contains {len(filtered_df)} interface(s) for {args.app_name} in {args.country}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()