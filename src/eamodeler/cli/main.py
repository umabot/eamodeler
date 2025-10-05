"""
Main CLI entry point for EAModeler.
"""

import click
import importlib.metadata
from pathlib import Path

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
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('app_name')
@click.option('--direction', default='all', type=click.Choice(['source', 'target', 'all']), 
              help='Analysis perspective (default: all)')
@click.option('--country', help='Country code filter (e.g., ES, FR, IT, UK)')
@click.option('--output-dir', default='output', type=click.Path(path_type=Path), 
              help='Output directory (default: output)')
def generate_docs(input_file, app_name, direction, country, output_dir):
    """
    Generate interface documentation from CSV data.
    
    INPUT_FILE: Path to the CSV file containing interface data
    APP_NAME: Name of the application to analyze
    DIRECTION: Analysis perspective (source, target, or all)
    """
    from ..utils.interface_lvl1_docs import generate_interface_documentation
    
    try:
        # Show processing message
        click.echo(f"ℹ️  Processing interface data for {app_name}...")
        
        # Generate documentation
        output_file, interface_count = generate_interface_documentation(
            input_file=input_file,
            app_name=app_name,
            direction=direction,
            country=country,
            output_dir=output_dir
        )
        
        # Success message with file path
        click.echo(f"✅ Documentation generated successfully!")
        click.echo(f"📄 Output file: {output_file}")
        
        # Show summary statistics
        if interface_count > 0:
            click.echo(f"📊 Interfaces documented: {interface_count}")
                
    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"❌ Data validation error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()