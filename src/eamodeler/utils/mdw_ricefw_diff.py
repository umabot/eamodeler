"""
MDW vs RICEFW diff utility.

Compares MDW-FLOW interfaces with RICEFW interfaces using:
- MDW key: INT ID
- RICEFW key: ID RICEFW
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


MDW_REQUIRED_COLUMNS = ["New/Review", "Reference", "INT ID"]
RICEFW_REQUIRED_COLUMNS = ["RICEFW  Type", "ID RICEFW"]

READ_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]


@dataclass
class DiffResult:
    """Container for diff result sets and source counts."""

    mdw_filtered_count: int
    ricefw_filtered_count: int
    ok_ids: list[str]
    extra_ids: list[str]
    missing_ids: list[str]

    def as_stats(self) -> dict[str, int]:
        """Return summary stats for CLI output and callers."""
        return {
            "mdw_filtered": self.mdw_filtered_count,
            "ricefw_filtered": self.ricefw_filtered_count,
            "ok": len(self.ok_ids),
            "extra": len(self.extra_ids),
            "missing": len(self.missing_ids),
        }


def _read_csv_with_fallback(file_path: Path) -> pd.DataFrame:
    """Read CSV file using a fallback list of common encodings."""
    errors: list[str] = []

    for encoding in READ_ENCODINGS:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            errors.append(f"{encoding}: UnicodeDecodeError")
            continue
        except pd.errors.ParserError as parse_err:
            # Some source files contain malformed rows with extra commas.
            # Retry in a tolerant mode to keep processing valid records.
            try:
                return pd.read_csv(
                    file_path,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip",
                )
            except Exception as tolerant_err:  # pragma: no cover - defensive
                errors.append(
                    f"{encoding}: ParserError ({parse_err}) | tolerant mode failed ({tolerant_err})"
                )
                continue
        except Exception as unexpected_err:  # pragma: no cover - defensive
            errors.append(f"{encoding}: {type(unexpected_err).__name__} ({unexpected_err})")
            continue

    raise ValueError(
        f"Could not read CSV file with any supported encoding: {file_path}. "
        f"Tried: {READ_ENCODINGS}. Details: {'; '.join(errors)}"
    )


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace around all column names."""
    normalized = df.copy()
    normalized.columns = [str(col).strip() for col in normalized.columns]
    return normalized


def _validate_required_columns(df: pd.DataFrame, required_columns: list[str], file_label: str) -> None:
    """Validate required columns are present in DataFrame."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        available = ", ".join(df.columns)
        raise ValueError(
            f"Missing required columns in {file_label}: {missing}. Available columns: [{available}]"
        )


def _normalize_key_series(series: pd.Series) -> pd.Series:
    """Normalize key values for safe set comparison."""
    normalized = series.fillna("").astype(str).str.strip()
    return normalized[normalized != ""]


def _build_default_output_filename(mdw_file: Path, ricefw_file: Path, now: datetime | None = None) -> str:
    """Build default output file name as requested by the user."""
    timestamp = (now or datetime.now()).strftime("%Y-%m-%d_%H:%M")
    return f"{mdw_file.stem}-{ricefw_file.stem}-diff-{timestamp}.md"


def _build_markdown_report(
    mdw_file: Path,
    ricefw_file: Path,
    diff_result: DiffResult,
) -> str:
    """Generate markdown report with summary and category sections."""
    stats = diff_result.as_stats()

    lines: list[str] = []
    lines.append("# MDW vs RICEFW Diff Report")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- MDW file: {mdw_file}")
    lines.append(f"- RICEFW file: {ricefw_file}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---:|")
    lines.append(f"| MDW filtered rows (selected MDW filter) | {stats['mdw_filtered']} |")
    lines.append(f"| RICEFW filtered rows (Interface) | {stats['ricefw_filtered']} |")
    lines.append(f"| OK (intersection) | {stats['ok']} |")
    lines.append(f"| EXTRA (only in MDW, warning) | {stats['extra']} |")
    lines.append(f"| MISSING (only in RICEFW, attention) | {stats['missing']} |")
    lines.append("")

    lines.append("## OK - Intersection")
    lines.append("")
    lines.append("These IDs exist in both MDW and RICEFW.")
    lines.append("")
    lines.extend(_ids_table(diff_result.ok_ids))
    lines.append("")

    lines.append("## EXTRA - Only in MDW (warning)")
    lines.append("")
    lines.append("These IDs exist in MDW but not in RICEFW.")
    lines.append("")
    lines.extend(_ids_table(diff_result.extra_ids))
    lines.append("")

    lines.append("## MISSING - Only in RICEFW (attention)")
    lines.append("")
    lines.append("These IDs exist in RICEFW but not in MDW.")
    lines.append("")
    lines.extend(_ids_table(diff_result.missing_ids))
    lines.append("")

    return "\n".join(lines)


def _ids_table(ids: list[str]) -> list[str]:
    """Render a one-column markdown table for IDs."""
    if not ids:
        return ["_No rows in this category._"]

    rows = ["| ID |", "|---|"]
    rows.extend([f"| {value} |" for value in ids])
    return rows


def compare_mdw_ricefw(
    mdw_flow_file: Path,
    ricefw_file: Path,
    output_file: Path | None = None,
    output_dir: Path | None = None,
    new_only: bool = False,
) -> tuple[Path, dict[str, Any]]:
    """
    Compare MDW-FLOW and RICEFW interfaces and write a markdown diff report.

    Args:
        mdw_flow_file: Path to MDW-FLOW CSV file.
        ricefw_file: Path to RICEFW CSV file.
        output_file: Optional full output file path (supports custom directory).
        output_dir: Optional output directory used only when output_file is not provided.
        new_only: When True, restrict MDW rows to New/Review = New; otherwise keep all
            rows where Reference = RICEFW.

    Returns:
        Tuple[Path, dict]: (report_path, stats)
    """
    mdw_path = Path(mdw_flow_file)
    ricefw_path = Path(ricefw_file)

    if not mdw_path.exists():
        raise FileNotFoundError(f"Input file not found: {mdw_path}")
    if not ricefw_path.exists():
        raise FileNotFoundError(f"Input file not found: {ricefw_path}")

    mdw_df = _normalize_columns(_read_csv_with_fallback(mdw_path))
    ricefw_df = _normalize_columns(_read_csv_with_fallback(ricefw_path))

    _validate_required_columns(mdw_df, MDW_REQUIRED_COLUMNS, "MDW-FLOW")
    _validate_required_columns(ricefw_df, RICEFW_REQUIRED_COLUMNS, "RICEFW")

    # 1) MDW filter: always keep Reference = RICEFW; optionally restrict to New rows only
    mdw_reference_mask = (
        mdw_df["Reference"].fillna("").astype(str).str.strip().str.casefold() == "ricefw"
    )

    if new_only:
        mdw_new_mask = (
            mdw_df["New/Review"].fillna("").astype(str).str.strip().str.casefold() == "new"
        )
        mdw_filtered = mdw_df[mdw_reference_mask & mdw_new_mask].copy()
    else:
        mdw_filtered = mdw_df[mdw_reference_mask].copy()

    # 2) RICEFW filter: RICEFW  Type = Interface
    ricefw_filtered = ricefw_df[
        ricefw_df["RICEFW  Type"].fillna("").astype(str).str.strip().str.casefold() == "interface"
    ].copy()

    mdw_ids = set(_normalize_key_series(mdw_filtered["INT ID"]))
    ricefw_ids = set(_normalize_key_series(ricefw_filtered["ID RICEFW"]))

    ok_ids = sorted(mdw_ids.intersection(ricefw_ids))
    extra_ids = sorted(mdw_ids.difference(ricefw_ids))
    missing_ids = sorted(ricefw_ids.difference(mdw_ids))

    diff_result = DiffResult(
        mdw_filtered_count=len(mdw_filtered),
        ricefw_filtered_count=len(ricefw_filtered),
        ok_ids=ok_ids,
        extra_ids=extra_ids,
        missing_ids=missing_ids,
    )

    report_content = _build_markdown_report(
        mdw_file=mdw_path,
        ricefw_file=ricefw_path,
        diff_result=diff_result,
    )

    if output_file is not None:
        report_path = Path(output_file)
    else:
        target_dir = Path(output_dir) if output_dir is not None else Path("output")
        default_name = _build_default_output_filename(mdw_path, ricefw_path)
        report_path = target_dir / default_name

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_content, encoding="utf-8")

    return report_path, diff_result.as_stats()
