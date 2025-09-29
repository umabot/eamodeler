"""
Main CLI entry point for EAModeler.
"""

import click
from eamodeler import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """EAModeler - A Python toolkit for Enterprise Architect tools and utilities."""
    pass


@main.command()
def hello():
    """A simple hello world command."""
    click.echo("Hello from EAModeler!")


@main.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('app_name')
@click.argument('direction', type=click.Choice(['source', 'target']))
@click.argument('country')
@click.option('--output-dir', default='output', help='Output directory (default: output)')
def generate_docs(input_file, app_name, direction, country, output_dir):
    """Generate interface documentation from CSV data."""
    import subprocess
    import sys
    from pathlib import Path
    
    # Get the path to the standalone script
    script_path = Path(__file__).parent.parent.parent.parent / 'generate_interface_docs.py'
    
    # Run the standalone script
    cmd = [
        sys.executable, str(script_path),
        input_file, app_name, direction, country,
        '--output_dir', output_dir
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running interface documentation generator: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()