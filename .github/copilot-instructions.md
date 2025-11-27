# EAModeler Project Instructions

EAModeler is a Python toolkit for generating Enterprise Architect documentation and diagrams from CSV data. It specializes in creating Mermaid.js visualizations for interface flows, ERD diagrams, and integration networks.

## Critical Architecture Knowledge

### Three Core Generators (in `src/eamodeler/utils/`)
1. **`interface_lvl1_docs.py`** - Generates interface documentation showing application connections
2. **`erd_generator.py`** - Creates ERD/class diagrams from canonical data models  
3. **`integration_diagram.py`** - Builds full integration network diagrams with BFS traversal

All three follow the same pattern:
- Take CSV input from `input/` directory
- Apply domain/country/app filters
- Sanitize text for Mermaid.js compatibility (critical: replace spaces/special chars, handle NaN)
- Generate markdown with embedded Mermaid diagrams to `output/` directory
- Return Path object and metrics (interface count, node count, etc.)

### Integration Diagram - Graph Traversal Details
The integration diagram generator uses **bidirectional BFS** to discover connected applications:

**Graph Structure:**
- Nodes: Applications (from "Source System/ APP" and "Target System/APP" columns)
- Edges: Interfaces with metadata (INT ID, country, descriptions)
- Two graph views maintained: `full_graph` (outgoing) and `reverse_graph` (incoming)

**Traversal Behavior:**
- Starts from application matching `app_name` (case-insensitive partial match on app code)
- Explores both directions: downstream targets AND upstream sources
- `--depth` parameter controls hops from starting node (e.g., depth=2 means 2 levels out)
- Without `--depth`: traverses entire connected component
- Returns subgraph of visited nodes and edges connecting them

**Example:**
```bash
# Get immediate neighbors only (1 hop)
uv run eamodeler gen-diagram input/data.csv "APP-0080" --depth 1

# Full network (all reachable nodes)
uv run eamodeler gen-diagram input/data.csv "APP-0080" --country UK
```

### Mermaid Sanitization - CRITICAL PATTERN
Every generator has a `sanitize_for_mermaid*()` function. When editing generators, always:
- Handle NaN/null/empty values → convert to safe defaults (e.g., "string" for data types)
- Replace problematic chars: `[^a-zA-Z0-9_]` → `_`, remove consecutive underscores
- Escape quotes in labels: `"` → `#quot;`, `'` → `#39;`
- Ensure node IDs start with letters (Mermaid requirement)

Example from `erd_generator.py`:
```python
if text.lower() in ['nan', 'null', 'none', '']:
    return 'string'  # Default safe data type
```

### Virtual Environment Setup - NON-STANDARD
This project uses a **fixed virtual environment location** at `~/development/uv/eamodeler` (not `.venv` in project root).

**Critical commands:**
- Setup: `./setup-env.sh` (creates venv, installs deps including pandas)
- Run scripts: `./run.sh python script.py` or `./run.sh eamodeler <command>`
- Direct activation: `source ~/development/uv/eamodeler/bin/activate`
- Install packages: `VIRTUAL_ENV=~/development/uv/eamodeler uv pip install <package>`

Why: Shared environment across projects/workflows. Always use these helpers, never plain `python`.

## CLI Command Structure (src/eamodeler/cli/main.py)

Commands follow Click conventions with consistent patterns:

```bash
# Interface docs: APP-NAME is the pivot point
uv run eamodeler gen-interface-docs input/data.csv "APP-0080" --direction target --country UK

# ERD: Multiple domains allowed (variadic)
uv run eamodeler gen-erd input/classes.csv input/attributes.csv input/relationships.csv "Site" "Customer & Contract"

# Integration diagram: Uses BFS to traverse connections
uv run eamodeler gen-diagram input/interfaces.csv "APP-0080" --country UK --depth 2
```

**CSV Input Expectations:**
- Interface CSVs: Must have `['INT ID', 'Source System/ APP', 'Target System/APP', 'Country', 'Interface short Description', 'Data Payload Description']`
- ERD CSVs: Classes need `['Data Domain', 'Data Entity']`, Attributes need `['Data Entity', 'Attribute', 'Data Type', 'PK']`, Relationships need `['Parent Entity', 'Child Entity', 'Cardinality']`
- Encoding handled automatically (tries utf-8, latin-1, cp1252, iso-8859-1)

## Development Workflow

### Adding New Diagram Generators
1. Create new file in `src/eamodeler/utils/` with sanitization function
2. Follow pattern: load CSV → validate columns → filter data → generate Mermaid → write markdown
3. Add Click command to `src/eamodeler/cli/main.py` with proper error handling
4. Update README.md with examples (users rely on it heavily)

### Testing
- Quick test: Use `test_erd_generator.py` pattern - direct imports, print results
- Proper tests: `uv run pytest tests/` (pytest configured in pyproject.toml)
- Manual verification: Check `output/*.md` files render correctly in Mermaid Live Editor

### Common Gotchas
- **Pandas import errors**: Run `VIRTUAL_ENV=~/development/uv/eamodeler uv pip install pandas` explicitly
- **Mermaid lexical errors**: Usually NaN or invalid data types - check sanitization (see `docs/mermaid_lexical_error_fix.md`)
- **File encoding**: Let pandas try multiple encodings, don't hardcode utf-8
- **Cardinality notation**: Map variations (`1:N`, `ONE_TO_MANY`, `1:M`) to consistent Mermaid syntax in `get_cardinality_connector()`

## Key Files Reference
- `pyproject.toml` - Entry point is `eamodeler.cli.main:main`, dependencies include click/pandas/pydantic
- `run.sh` - Hardcoded path to venv, use for all command execution
- `setup-env.sh` - Creates venv, installs deps, verifies pandas installation
- `docs/` - Contains fix documentation and usage guides for generators