"""
Tests for CLI functionality.
"""

from pathlib import Path

from click.testing import CliRunner
from eamodeler.cli.main import main


def test_main_command():
    """Test main CLI command."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "EAModeler" in result.output


def test_hello_command():
    """Test hello command."""
    runner = CliRunner()
    result = runner.invoke(main, ["hello"])
    assert result.exit_code == 0
    assert "Hello from EAModeler!" in result.output


def test_mdw_ricefw_diff_command_with_output_file(tmp_path: Path):
    """Test mdw-ricefw-diff command with explicit output file argument."""
    runner = CliRunner()

    mdw_file = tmp_path / "mdw.csv"
    ricefw_file = tmp_path / "ricefw.csv"
    output_file = tmp_path / "custom-report.md"

    mdw_file.write_text(
        "\n".join(
            [
                "New/Review,Reference,INT ID",
                "New,RICEFW,INT-001",
                "New,RICEFW,INT-EXTRA",
            ]
        ),
        encoding="utf-8",
    )

    ricefw_file.write_text(
        "\n".join(
            [
                "RICEFW  Type,ID RICEFW",
                "Interface,INT-001",
                "Interface,INT-MISSING",
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        main,
        [
            "mdw-ricefw-diff",
            str(mdw_file),
            str(ricefw_file),
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Diff completed successfully" in result.output
    assert output_file.exists()


def test_mdw_ricefw_diff_command_default_output_dir(tmp_path: Path):
    """Test mdw-ricefw-diff command default naming when output file is omitted."""
    runner = CliRunner()

    mdw_file = tmp_path / "MDW-FLOW.csv"
    ricefw_file = tmp_path / "RICEFW_2026-03-30.csv"
    output_dir = tmp_path / "reports"

    mdw_file.write_text("New/Review,Reference,INT ID\nNew,RICEFW,INT-001\n", encoding="utf-8")
    ricefw_file.write_text("RICEFW  Type,ID RICEFW\nInterface,INT-001\n", encoding="utf-8")

    result = runner.invoke(
        main,
        [
            "mdw-ricefw-diff",
            str(mdw_file),
            str(ricefw_file),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Diff completed successfully" in result.output

    generated_files = list(output_dir.glob("MDW-FLOW-RICEFW_2026-03-30-diff-*.md"))
    assert len(generated_files) == 1