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


@main.command('gen-interface-docs')
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


@main.command('gen-erd')
@click.argument('classes_csv', type=click.Path(exists=True, path_type=Path))
@click.argument('attributes_csv', type=click.Path(exists=True, path_type=Path))
@click.argument('relationships_csv', type=click.Path(exists=True, path_type=Path))
@click.argument('data_domains', nargs=-1, required=True)
@click.option('--diagram-type', default='erDiagram', type=click.Choice(['erDiagram', 'classDiagram']),
              help='Type of diagram to generate (default: erDiagram)')
@click.option('--output-dir', default='output', type=click.Path(path_type=Path),
              help='Output directory (default: output)')
def generate_erd(classes_csv, attributes_csv, relationships_csv, data_domains, diagram_type, output_dir):
    """
    Generate Mermaid ERD or Class diagrams from canonical data model CSV files.
    
    CLASSES_CSV: Path to CSV file with entity/class definitions
    ATTRIBUTES_CSV: Path to CSV file with attribute definitions
    RELATIONSHIPS_CSV: Path to CSV file with relationship definitions
    DATA_DOMAINS: One or more data domain names to filter by
    """
    from ..utils.erd_generator import generate_mermaid_diagram
    
    try:
        # Show processing message
        click.echo(f"ℹ️  Generating {diagram_type} for domains: {', '.join(data_domains)}...")
        
        # Generate diagram
        output_file = generate_mermaid_diagram(
            classes_csv_path=str(classes_csv),
            attributes_csv_path=str(attributes_csv),
            relationships_csv_path=str(relationships_csv),
            data_domains=list(data_domains),
            diagram_type=diagram_type,
            output_dir=str(output_dir)
        )
        
        # Success message already printed by the function
                
    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}", err=True)
        raise click.Abort()
    except ValueError as e:
        click.echo(f"❌ Data validation error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        raise click.Abort()


@main.command('gen-diagram')
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.argument('app_name')
@click.option('--country', help='Country code filter (e.g., ES, FR, IT, UK)')
@click.option('--output-dir', default='output', type=click.Path(path_type=Path),
              help='Output directory (default: output)')
@click.option('--depth', type=int, help='Traversal depth for the diagram (e.g., 1, 2).')
def generate_diagram(input_file, app_name, country, output_dir, depth):
    """
    Generate a full integration diagram starting from a given application.
    
    INPUT_FILE: Path to the CSV file containing interface data
    APP_NAME: Code of the application to start traversal from (e.g., APP-0080)
    """
    from ..utils.integration_diagram import generate_integration_diagram
    
    try:
        click.echo(f"ℹ️  Generating integration diagram for {app_name}...")
        
        output_file, node_count = generate_integration_diagram(
            file_path=input_file,
            app_name=app_name,
            country=country,
            output_dir=output_dir,
            depth=depth
        )
        
        click.echo(f"✅ Diagram generated successfully!")
        click.echo(f"📄 Output file: {output_file}")
        if node_count > 0:
            click.echo(f"📊 Diagram includes {node_count} application nodes.")

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