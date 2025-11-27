"""
Shared utilities for CSV file handling across all generators.

Provides encoding detection and validation for enterprise architecture data files.
This module centralizes CSV loading logic to ensure consistent handling of
international characters and data validation across all diagram generators.
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional

try:
    import pandas as pd
except ImportError:
    print("Error: pandas library is required. Install it with: uv add pandas")
    sys.exit(1)


def load_csv_with_encoding_fallback(
    file_path: str | Path,
    required_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load CSV file with automatic encoding detection and optional column validation.
    
    This function attempts to read a CSV file using multiple common encodings,
    falling back through the list until successful. Handles international
    characters from various source systems (SAP, Oracle, custom exports).
    
    Args:
        file_path: Path to the CSV file (string or Path object)
        required_columns: Optional list of column names that must be present
        
    Returns:
        Loaded and validated DataFrame with cleaned column headers and string data
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        ValueError: If no encoding works or required columns are missing
        
    Example:
        >>> df = load_csv_with_encoding_fallback(
        ...     'input/interfaces.csv',
        ...     required_columns=['INT ID', 'Source System/ APP']
        ... )
        >>> print(f"Loaded {len(df)} interfaces")
    """
    file_path = Path(file_path)
    
    # Check file exists
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    # Try multiple encodings in order of likelihood for enterprise data
    # utf-8: Modern systems, international standard
    # latin-1: Western European legacy systems
    # cp1252: Windows exports (common in Excel/SAP exports)
    # iso-8859-1: Unix/Linux legacy systems
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    last_error = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            logging.info(f"Successfully loaded {file_path.name} with {encoding} encoding")
            
            # Clean column headers - strip whitespace
            df.columns = df.columns.str.strip()
            
            # Handle common column name variations (e.g., "Country/BU" → "Country")
            if 'Country/BU' in df.columns and 'Country' not in df.columns:
                df.rename(columns={'Country/BU': 'Country'}, inplace=True)
            
            # Validate required columns if specified
            if required_columns:
                validate_csv_columns(df, required_columns, file_path)
            
            # Clean string columns - strip whitespace from all string data
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            
            return df
            
        except (UnicodeDecodeError, UnicodeError) as e:
            last_error = e
            logging.debug(f"Failed to decode {file_path.name} with {encoding}: {e}")
            continue
        except ValueError:
            # Re-raise validation errors immediately (don't try other encodings)
            raise
    
    # All encodings failed
    raise ValueError(
        f"Could not decode {file_path} with any supported encoding "
        f"({', '.join(encodings)}). Last error: {last_error}"
    )


def validate_csv_columns(
    df: pd.DataFrame,
    required_columns: List[str],
    file_path: str | Path
) -> None:
    """
    Validate that a DataFrame has all required columns.
    
    Useful when you've already loaded the CSV and need to validate columns
    separately from the load operation, or for additional validation after
    initial load.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names (exact match, case-sensitive)
        file_path: Path to the CSV file (for error messages)
        
    Raises:
        ValueError: If required columns are missing, with helpful error message
                   showing both missing and available columns
        
    Example:
        >>> validate_csv_columns(
        ...     df,
        ...     ['INT ID', 'Source System/ APP'],
        ...     'input/interfaces.csv'
        ... )
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        available_columns = list(df.columns)
        file_name = Path(file_path).name
        raise ValueError(
            f"Missing required columns in {file_name}: {missing_columns}. "
            f"Available columns: {available_columns}"
        )
