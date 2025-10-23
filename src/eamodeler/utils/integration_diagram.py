"""
Generates a full integration diagram from interface data.
"""

import pandas as pd
import collections
import logging
import os
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_app_code(app_name):
    """Extracts the application code from the full application name."""
    if isinstance(app_name, str) and " - " in app_name:
        return app_name.split(" - ", 1)[0]
    return app_name

def sanitize_for_mermaid(text):
    """Sanitizes text for use in Mermaid.js diagrams."""
    if not isinstance(text, str):
        return ""
    # Replace problematic characters with safe alternatives
    return text.replace('"', '#quot;').replace("'", '#39;').replace('(', ' ').replace(')', ' ')

def sanitize_filename(name):
    """Creates a safe filename from a string."""
    name = name.lower()
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^a-z0-9_-]', '', name)
    return name

def build_graph_from_csv(file_path, country=None):
    """
    Reads and validates the CSV, filters data, and builds the graph.
    """
    mandatory_columns = ['INT ID', 'Source System/ APP', 'Target System/APP', 'Interface short Description', 'Data Payload Description', 'Country']
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except FileNotFoundError:
        logging.critical(f"File not found: {file_path}")
        return None
    except Exception as e:
        logging.critical(f"Error reading CSV file: {e}")
        return None

    # Validate columns
    if not all(col in df.columns for col in mandatory_columns):
        missing_cols = [col for col in mandatory_columns if col not in df.columns]
        logging.critical(f"CSV is missing mandatory columns: {', '.join(missing_cols)}")
        return None

    # Filter by country
    if country:
        logging.info(f"Filtering data for country: {country}")
        df = df[df['Country'].str.upper() == country.upper()]

    if df.empty:
        logging.warning("No data available after filtering.")
        return {}

    graph = collections.defaultdict(list)
    all_apps = set(df['Source System/ APP'].unique()) | set(df['Target System/APP'].unique())

    for app in all_apps:
        if pd.notna(app):
            graph[app] # Ensure all apps are in the graph, even if they are only targets

    for _, row in df.iterrows():
        source = row['Source System/ APP']
        target = row['Target System/APP']
        if pd.notna(source) and pd.notna(target):
            interface_details = {
                'source': source,
                'target': target,
                'id': row['INT ID'],
                'country': row['Country'],
                'short_desc': row['Interface short Description'],
                'payload_desc': row['Data Payload Description']
            }
            graph[source].append(interface_details)
            
    logging.info(f"Graph built with {len(graph)} nodes.")
    return dict(graph)

def bfs_and_collect_interfaces(graph, start_node_code, depth: int | None = None):
    """
    Traverses the graph from start_node and collects all interfaces it passes through.
    This version finds all nodes connected to the start_node, both upstream and downstream.
    """
    full_graph = collections.defaultdict(list)
    reverse_graph = collections.defaultdict(list)
    all_edges = []

    for source, edges in graph.items():
        for edge in edges:
            target = edge['target']
            full_graph[source].append(edge)
            reverse_graph[target].append(edge)
            all_edges.append(edge)

    start_node = None
    for node in full_graph.keys():
        if start_node_code.lower() in get_app_code(node).lower():
            start_node = node
            break
    
    if not start_node:
        for node in reverse_graph.keys():
            if start_node_code.lower() in get_app_code(node).lower():
                start_node = node
                break

    if not start_node:
        logging.error(f"Start node containing '{start_node_code}' not found in graph.")
        return set(), []

    logging.info(f"Starting graph traversal from: {start_node}")
    
    queue = collections.deque([(start_node, 0)])
    visited_nodes = {start_node}
    
    while queue:
        current_node, level = queue.popleft()

        if depth is not None and level >= depth:
            continue
        
        # Outgoing connections
        if current_node in full_graph:
            for edge in full_graph[current_node]:
                neighbor = edge['target']
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    queue.append((neighbor, level + 1))
        
        # Incoming connections
        if current_node in reverse_graph:
            for edge in reverse_graph[current_node]:
                neighbor = edge['source']
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    queue.append((neighbor, level + 1))

    # Collect all edges that are part of the subgraph
    subgraph_edges = [
        edge for edge in all_edges 
        if edge['source'] in visited_nodes and edge['target'] in visited_nodes
    ]
    
    logging.info(f"Traversal visited {len(visited_nodes)} nodes and found {len(subgraph_edges)} related interfaces.")
    return visited_nodes, subgraph_edges


def generate_output_file(output_path, visited_nodes, subgraph_edges, start_node_code, scope, depth: int | None = None):
    """
    Creates the final Markdown report file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Integration Network Analysis\n\n")
        scope_display = f"Scope: {scope}"
        if depth is not None:
            scope_display += f", Depth: {depth}"
        f.write(f"## Integration Diagram for {start_node_code} ({scope_display})\n\n")
        f.write("```mermaid\n")
        f.write("graph TD\n")
        
        # Only connections from the subgraph
        for edge in subgraph_edges:
            source_app_code = get_app_code(edge['source'])
            target_app_code = get_app_code(edge['target'])
            source_id = sanitize_for_mermaid(source_app_code)
            target_id = sanitize_for_mermaid(target_app_code)
            source_label = edge['source'].replace('"', '#quot;')
            target_label = edge['target'].replace('"', '#quot;')
            int_id_label = edge['id'].replace('"', '#quot;')
            
            f.write(f'  {source_id}["{source_label}"] --"{int_id_label}"--> {target_id}["{target_label}"];\n')
        
        # Highlight the start node
        start_node_id = None
        for node in visited_nodes:
            if start_node_code.lower() in get_app_code(node).lower():
                start_node_id = sanitize_for_mermaid(get_app_code(node))
                break
        if start_node_id:
             f.write(f'  style {start_node_id} fill:#007bff,stroke:#333,stroke-width:2px,color:#fff\n')

        f.write("```\n\n")

        f.write(f"## Interfaces related to {start_node_code} ({scope_display})\n\n")
        if subgraph_edges:
            # Manually create the markdown table to remove dependency on 'tabulate'
            f.write("| Country | INT ID | Interface short Description | Source | Target | Data Payload Description |\n")
            f.write("|---|---|---|---|---|---|\n")
            # Sort interfaces for consistent output
            sorted_edges = sorted(subgraph_edges, key=lambda x: (x.get('source', ''), x.get('target', '')))
            for interface in sorted_edges:
                country = str(interface.get('country', 'N/A')).replace('|', '\|')
                int_id = str(interface.get('id', 'N/A')).replace('|', '\|')
                short_desc = str(interface.get('short_desc', 'N/A')).replace('|', '\|')
                source = str(interface.get('source', 'N/A')).replace('|', '\|')
                target = str(interface.get('target', 'N/A')).replace('|', '\|')
                payload_desc = str(interface.get('payload_desc', 'N/A')).replace('|', '\|')
                f.write(f"| {country} | {int_id} | {short_desc} | {source} | {target} | {payload_desc} |\n")
        else:
            f.write("No interfaces were found for the specified application.\n")
        f.write("\n")

    logging.info(f"Markdown report generated at: {output_path}")

def generate_integration_diagram(file_path: Path, app_name: str, country: str | None, output_dir: Path, depth: int | None = None):
    """
    Main logic to generate the integration diagram.
    """
    scope = country.upper() if country else "ALL"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_app_name = sanitize_filename(app_name)
    output_filename = f"{scope.lower()}_{safe_app_name}_network.md"
    output_file_path = output_dir / output_filename

    logging.info(f"Processing file: {file_path} for app: {app_name} with scope: {scope}")
    
    graph = build_graph_from_csv(file_path, country)
    
    if graph is None:
        raise ValueError("Failed to build graph from CSV. Check logs for details.")

    if not graph:
        logging.warning("Graph is empty. No output will be generated.")
        return output_file_path, 0

    visited_nodes, subgraph_edges = bfs_and_collect_interfaces(graph, app_name, depth)
    
    generate_output_file(output_file_path, visited_nodes, subgraph_edges, app_name, scope, depth)
    
    return output_file_path, len(visited_nodes)
