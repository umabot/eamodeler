"""
Tests for CLI functionality.
"""

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