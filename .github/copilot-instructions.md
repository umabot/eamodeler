# EAModeler Project Instructions

This is a Python project for creating tools for Enterprise Architect using:
- uv package manager
- Python 3.12
- Virtual environment at ~/development/uv/eamodeler

## Project Status
- [x] Create copilot-instructions.md file
- [x] Scaffold the project with uv
- [x] Configure Python environment
- [x] Install dependencies
- [x] Create project structure
- [x] Set up development tools
- [x] Create documentation

## Development Guidelines
- Use uv for package management
- Follow Python best practices
- Include proper documentation
- Use type hints where appropriate

## Project Structure
```
eamodeler/
├── src/
│   └── eamodeler/
│       ├── __init__.py
│       ├── core/         # Core EA functionality
│       ├── models/       # Data models and classes
│       ├── utils/        # Utility functions
│       └── cli/          # Command-line interface
├── tests/                # Test suite
├── docs/                 # Documentation
├── input/                # Input files (CSV, Excel, JSON, PDF, Markdown)
├── output/               # Generated output files (PDF, CSV, JSON, Markdown)
├── pyproject.toml        # Project configuration
├── hello.py              # Hello world example
└── README.md
```

## Input/Output Directories

### input/
Place files to be processed by EAModeler tools:
- **CSV files** - Data tables and model information
- **Excel files** (.xlsx, .xls) - Spreadsheet data for model generation
- **JSON files** - Structured data and configuration files
- **PDF files** - Documentation and diagrams to extract information from
- **Markdown files** (.md) - Documentation and text-based model descriptions

### output/
Generated files from EAModeler tools:
- **PDF files** - Generated reports, diagrams, and documentation
- **CSV files** - Exported data tables and model information
- **JSON files** - Structured output data and configuration files
- **Markdown files** (.md) - Generated documentation and reports

## Usage
- Activate virtual environment: `source ~/development/uv/eamodeler/bin/activate`
- Install dependencies: `uv sync`
- Run CLI: `uv run eamodeler --help`
- Run tests: `uv run pytest`
- Run hello world: `uv run python hello.py`

## Available Tools

### Interface Documentation Generator
Generate interface documentation from CSV data with Mermaid diagrams:

```bash
# Using standalone script
uv run python generate_interface_docs.py "input/data.csv" "APP-NAME" "target" "COUNTRY"

# Using CLI command
uv run eamodeler generate-docs "input/data.csv" "APP-NAME" "target" "COUNTRY"
```

Features:
- Generates Mermaid.js flow diagrams
- Creates detailed interface tables with descriptions
- Supports both source and target analysis
- Handles various CSV encodings
- Interactive filename selection
- Country-based filtering with validation
- Enhanced output with country-specific statistics
- Connected applications summary table
- Interface short descriptions included