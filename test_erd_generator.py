#!/usr/bin/env python3
"""
Test script for the ERD generator functionality.

This script demonstrates how to use the generate_mermaid_diagram function
with the example CSV files.
"""

import sys
from pathlib import Path

# Add the src directory to Python path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from eamodeler.utils.erd_generator import generate_mermaid_diagram


def main():
    """Test the ERD generator with example data."""
    
    # Define paths to the CSV files
    classes_csv = "input/classes.csv"
    attributes_csv = "input/attributes.csv" 
    relationships_csv = "input/relationships.csv"
    
    # Test 1: Generate ERD for Site and Customer domains
    print("=== Test 1: ERD for Site and Customer & Contract domains ===")
    try:
        output_file = generate_mermaid_diagram(
            classes_csv_path=classes_csv,
            attributes_csv_path=attributes_csv,
            relationships_csv_path=relationships_csv,
            data_domains=["Site", "Customer & Contract"],
            diagram_type="erDiagram",
            output_dir="output"
        )
        print(f"✅ Test 1 completed successfully")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Generate Class Diagram for HR domain only
    print("=== Test 2: Class Diagram for HR domain ===")
    try:
        output_file = generate_mermaid_diagram(
            classes_csv_path=classes_csv,
            attributes_csv_path=attributes_csv,
            relationships_csv_path=relationships_csv,
            data_domains=["HR"],
            diagram_type="classDiagram",
            output_dir="output"
        )
        print(f"✅ Test 2 completed successfully")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 3: Generate ERD for all domains
    print("=== Test 3: ERD for all domains ===")
    try:
        output_file = generate_mermaid_diagram(
            classes_csv_path=classes_csv,
            attributes_csv_path=attributes_csv,
            relationships_csv_path=relationships_csv,
            data_domains=["Site", "Customer & Contract", "Finance", "HR"],
            diagram_type="erDiagram",
            output_dir="output"
        )
        print(f"✅ Test 3 completed successfully")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")


if __name__ == "__main__":
    main()