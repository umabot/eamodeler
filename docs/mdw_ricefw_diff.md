# MDW vs RICEFW Diff Utility

## Overview

Compare `MDW-FLOW` and `RICEFW` interface inventories and generate a Markdown reconciliation report. This is useful for identifying matched interfaces, MDW-only extras, and RICEFW-only gaps.

The report groups IDs into:
- `OK` — IDs present in both files
- `EXTRA` — IDs present only in `MDW-FLOW`
- `MISSING` — IDs present only in `RICEFW`

By default, `RICEFW` is treated as the reference/source of truth.

## Filters applied

| Source | Default behavior (`--all`) | New-only behavior (`--new`) |
|---|---|---|
| `MDW-FLOW` | Keep rows where `Reference = RICEFW` | Keep rows where `Reference = RICEFW` and `New/Review = New` |
| `RICEFW` | Keep rows where `RICEFW  Type = Interface` | Same |

## Comparison keys

- MDW key: `INT ID`
- RICEFW key: `ID RICEFW`

## Required columns

| File | Required columns |
|---|---|
| `MDW-FLOW` | `New/Review`, `Reference`, `INT ID` |
| `RICEFW` | `RICEFW  Type`, `ID RICEFW` |

## CLI usage

```bash
# Default mode: compare all MDW rows that reference RICEFW
uv run eamodeler mdw-ricefw-diff input/MDW-FLOW_2026-04-03.csv input/RICEFW_2026-04-03.csv

# New-only mode: only compare rows marked as New in MDW-FLOW
uv run eamodeler mdw-ricefw-diff --new input/MDW-FLOW.csv input/RICEFW_2026-03-30.csv

# Save to an explicit report path
uv run eamodeler mdw-ricefw-diff input/MDW-FLOW.csv input/RICEFW_2026-03-30.csv ./output/custom-diff.md

# Use a custom fallback directory when no output filename is supplied
uv run eamodeler mdw-ricefw-diff input/MDW-FLOW.csv input/RICEFW_2026-03-30.csv --output-dir ./reports
```

## Default report name

If the output filename is omitted, the report name defaults to:

`<mdw_stem>-<ricefw_stem>-diff-<yyyy-mm-dd_HH:mm>.md`

Example:

`MDW-FLOW-RICEFW_2026-03-30-diff-2026-03-31_14:40.md`

## Output report structure

The generated report contains:
- a summary table with counts for filtered MDW rows, filtered RICEFW rows, `OK`, `EXTRA`, and `MISSING`
- an `OK` section listing IDs found in both files
- an `EXTRA` section listing IDs only found in `MDW-FLOW`
- a `MISSING` section listing IDs only found in `RICEFW`
