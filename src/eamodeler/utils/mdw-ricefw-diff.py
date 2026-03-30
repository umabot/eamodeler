"""
Compatibility wrapper for the MDW vs RICEFW diff utility.

This file exists to satisfy the requested utility naming.
Use `mdw_ricefw_diff.py` for imports.
"""

from pathlib import Path
import argparse

from eamodeler.utils.mdw_ricefw_diff import compare_mdw_ricefw


def main() -> None:
    """Run utility as a standalone script."""
    parser = argparse.ArgumentParser(
        description="Compare MDW-FLOW and RICEFW CSV files and produce markdown diff report"
    )
    parser.add_argument("mdw_flow_file", type=Path, help="Path to MDW-FLOW CSV")
    parser.add_argument("ricefw_file", type=Path, help="Path to RICEFW CSV")
    parser.add_argument(
        "output_file",
        nargs="?",
        type=Path,
        default=None,
        help="Optional output markdown path (can include directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Fallback output directory when output_file is not provided",
    )

    args = parser.parse_args()

    report_path, stats = compare_mdw_ricefw(
        mdw_flow_file=args.mdw_flow_file,
        ricefw_file=args.ricefw_file,
        output_file=args.output_file,
        output_dir=args.output_dir,
    )

    print(f"Output: {report_path}")
    print(f"MDW filtered: {stats['mdw_filtered']}")
    print(f"RICEFW filtered: {stats['ricefw_filtered']}")
    print(f"OK: {stats['ok']}")
    print(f"EXTRA: {stats['extra']}")
    print(f"MISSING: {stats['missing']}")


if __name__ == "__main__":
    main()
