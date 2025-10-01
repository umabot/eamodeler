"""
Main CLI entry point for EAModeler.
"""

import click
import importlib.metadata

try:
    __version__ = importlib.metadata.version("eamodeler")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0.dev0"  # Default version if not installed


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
@click.argument('country', required=False)
@click.option('--output-dir', default='output', help='Output directory (default: output)')
def generate_docs(input_file, app_name, direction, country, output_dir):
    """
    Generate interface documentation from CSV data.
    
    INPUT_FILE: Path to the CSV file containing interface data
    APP_NAME: Name of the application to analyze
    DIRECTION: Analysis perspective (source or target)
    COUNTRY: Optional country code filter (e.g., ES, FR, IT, UK)
    """
    import subprocess
    import sys
    from pathlib import Path
    
    # Get the path to the standalone script
    script_path = Path(__file__).parent.parent.parent.parent / 'generate_interface_docs.py'
    
    # Prepare command
    cmd = [
        sys.executable, str(script_path),
        input_file, app_name, direction
    ]
    
    # Add country parameter if provided
    if country:
        cmd.append(country)
        
    # Add output dir parameter
    cmd.extend(['--output_dir', output_dir])
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error running interface documentation generator: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()