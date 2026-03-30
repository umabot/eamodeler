# MDW vs RICEFW Diff Utility

## Overview

`mdw-ricefw-diff` compares interface IDs between:
- `MDW-FLOW` CSV
- `RICEFW` CSV

RICEFW is used as the source of truth.

## Filters Applied

1. MDW-FLOW filter:
- `New/Review` = `New`
- `Reference` = `RICEFW`

2. RICEFW filter:
- `RICEFW  Type` = `Interface`

## Comparison Keys

- MDW key: `INT ID`
- RICEFW key: `ID RICEFW`

## Output Categories

- `OK`: IDs found in both files (intersection)
- `EXTRA`: IDs only in MDW (warning)
- `MISSING`: IDs only in RICEFW (attention)

## Required Columns

MDW-FLOW must contain:
- `New/Review`
- `Reference`
- `INT ID`

RICEFW must contain:
- `RICEFW  Type`
- `ID RICEFW`

## CLI Usage

```bash
uv run eamodeler mdw-ricefw-diff input/MDW-FLOW.csv input/RICEFW_2026-03-30.csv
```

Optional third positional argument for report output file (supports path):

```bash
uv run eamodeler mdw-ricefw-diff input/MDW-FLOW.csv input/RICEFW_2026-03-30.csv ./output/custom-diff.md
```

Fallback output directory used only when the third argument is omitted:

```bash
uv run eamodeler mdw-ricefw-diff input/MDW-FLOW.csv input/RICEFW_2026-03-30.csv --output-dir output
```

## Default Report Name

When no output file is provided, report filename is:

`<input_file_1_stem>-<input_file_2_stem>-diff-<yyyy-mm-dd_HH:mm>.md`

Example:

`MDW-FLOW-RICEFW_2026-03-30-diff-2026-03-31_14:40.md`
