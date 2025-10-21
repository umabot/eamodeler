# ERD Generator - Mermaid Lexical Error Fix

## Issue
The generated Mermaid diagrams contained lexical errors due to invalid data types in the CSV input files:

```
Error: Lexical error on line 2. Unrecognized text.
...Diagram    Account {        string Cit
----------------------^
```

## Root Cause
The issue was caused by problematic values in the "Data Type" column of the attributes CSV:

1. **NaN values**: When pandas read empty or missing data type cells, they became `nan` which is not valid Mermaid syntax
2. **Invalid data types**: Some entries contained values like `multivalued` which are not recognized Mermaid data types
3. **Missing sanitization**: The raw data types weren't properly validated before being used in Mermaid syntax

## Solution
Updated the `generate_mermaid_diagram` function in `erd_generator.py` to handle these cases:

### 1. Data Type Validation and Cleanup
```python
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
```

### 2. Enhanced Sanitization Function
Updated `sanitize_for_mermaid_erd()` to handle common problematic values:
```python
# Handle common problematic values
if text.lower() in ['nan', 'null', 'none', '']:
    return 'string'
```

## Data Type Mapping
The fix implements the following mapping for problematic data types:

| Original Value | Mapped To | Reason |
|---------------|-----------|---------|
| `nan`, `null`, empty | `string` | Default safe data type |
| `multivalued`, `multivalue`, `multiocc` | `array` | Semantic mapping for collections |
| Invalid characters | Sanitized with underscores | Mermaid compatibility |

## Testing
After applying the fix:
- ✅ Class diagrams generate without lexical errors
- ✅ ERD diagrams work correctly  
- ✅ All data types are valid Mermaid syntax
- ✅ No functionality is lost - attributes are preserved with appropriate data types

## Files Modified
- `/src/eamodeler/utils/erd_generator.py`: Main fix implementation
- Enhanced data type validation and sanitization logic

## Usage
The fix is transparent to users - no changes needed in CLI usage:
```bash
uv run eamodeler gen-erd input/EliorClasses.csv input/EliorAttributes.csv input/EliorRelationships.csv "Customer & Contract" --diagram-type classDiagram
```