"""Tests for MDW vs RICEFW diff utility."""

from pathlib import Path

import pytest

from eamodeler.utils.mdw_ricefw_diff import compare_mdw_ricefw


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_compare_mdw_ricefw_happy_path(tmp_path: Path):
    """Diff should produce OK, EXTRA, and MISSING categories as expected in new-only mode."""
    mdw_file = tmp_path / "mdw.csv"
    ricefw_file = tmp_path / "ricefw.csv"
    output_file = tmp_path / "report.md"

    _write_csv(
        mdw_file,
        "\n".join(
            [
                "New/Review,Reference,INT ID",
                "New,RICEFW,INT-001",
                "New,RICEFW,INT-002",
                "Review,RICEFW,INT-IGNORED",
                "New,OTHER,INT-IGNORED2",
            ]
        ),
    )

    _write_csv(
        ricefw_file,
        "\n".join(
            [
                "RICEFW  Type,ID RICEFW",
                "Interface,INT-001",
                "Interface,INT-003",
                "Enhancement,INT-IGNORED",
            ]
        ),
    )

    report_path, stats = compare_mdw_ricefw(
        mdw_flow_file=mdw_file,
        ricefw_file=ricefw_file,
        output_file=output_file,
        new_only=True,
    )

    assert report_path == output_file
    assert stats["mdw_filtered"] == 2
    assert stats["ricefw_filtered"] == 2
    assert stats["ok"] == 1
    assert stats["extra"] == 1
    assert stats["missing"] == 1

    report_text = report_path.read_text(encoding="utf-8")
    assert "## Summary" in report_text
    assert "## OK - Intersection" in report_text
    assert "## EXTRA - Only in MDW (warning)" in report_text
    assert "## MISSING - Only in RICEFW (attention)" in report_text


def test_compare_mdw_ricefw_default_all_mode(tmp_path: Path):
    """Default mode should include all MDW rows where Reference = RICEFW."""
    mdw_file = tmp_path / "mdw.csv"
    ricefw_file = tmp_path / "ricefw.csv"
    output_file = tmp_path / "report.md"

    _write_csv(
        mdw_file,
        "\n".join(
            [
                "New/Review,Reference,INT ID",
                "New,RICEFW,INT-001",
                "New,RICEFW,INT-002",
                "Review,RICEFW,INT-IGNORED",
                "New,OTHER,INT-IGNORED2",
            ]
        ),
    )

    _write_csv(
        ricefw_file,
        "\n".join(
            [
                "RICEFW  Type,ID RICEFW",
                "Interface,INT-001",
                "Interface,INT-003",
                "Enhancement,INT-IGNORED",
            ]
        ),
    )

    report_path, stats = compare_mdw_ricefw(
        mdw_flow_file=mdw_file,
        ricefw_file=ricefw_file,
        output_file=output_file,
    )

    assert report_path == output_file
    assert stats["mdw_filtered"] == 3
    assert stats["ricefw_filtered"] == 2
    assert stats["ok"] == 1
    assert stats["extra"] == 2
    assert stats["missing"] == 1


def test_compare_mdw_ricefw_default_output_name(tmp_path: Path):
    """Default output file should follow the requested naming convention."""
    mdw_file = tmp_path / "MDW-FLOW.csv"
    ricefw_file = tmp_path / "RICEFW_2026-03-30.csv"
    output_dir = tmp_path / "out"

    _write_csv(mdw_file, "New/Review,Reference,INT ID\nNew,RICEFW,INT-001\n")
    _write_csv(ricefw_file, "RICEFW  Type,ID RICEFW\nInterface,INT-001\n")

    report_path, _ = compare_mdw_ricefw(
        mdw_flow_file=mdw_file,
        ricefw_file=ricefw_file,
        output_dir=output_dir,
    )

    assert report_path.parent == output_dir
    assert report_path.name.startswith("MDW-FLOW-RICEFW_2026-03-30-diff-")
    assert report_path.name.endswith(".md")


def test_compare_mdw_ricefw_missing_column_raises(tmp_path: Path):
    """Missing required columns should raise ValueError."""
    mdw_file = tmp_path / "mdw.csv"
    ricefw_file = tmp_path / "ricefw.csv"

    _write_csv(mdw_file, "New/Review,Reference\nNew,RICEFW\n")
    _write_csv(ricefw_file, "RICEFW  Type,ID RICEFW\nInterface,INT-001\n")

    with pytest.raises(ValueError) as exc_info:
        compare_mdw_ricefw(mdw_flow_file=mdw_file, ricefw_file=ricefw_file)

    assert "Missing required columns in MDW-FLOW" in str(exc_info.value)
