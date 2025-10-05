#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Visualizer - Phase 5.4

Creates interactive and static visualizations of the knowledge graph.
Supports PyVis HTML, Mermaid diagrams, and GraphViz DOT format.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import networkx as nx

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """
    Creates visualizations of the knowledge graph.

    Supports multiple formats:
    - PyVis: Interactive HTML visualization
    - Mermaid: Text-based diagram (for documentation)
    - GraphViz: DOT format (for static images)
    """

    def __init__(self, graph: nx.DiGraph):
        """
        Initialize GraphVisualizer.

        Args:
            graph: NetworkX DiGraph to visualize
        """
        self.graph = graph

        # Color mapping for node types
        self.node_colors = {
            "JSP": "#3498DB",  # Blue
            "CONTROLLER": "#27AE60",  # Green
            "CONTROLLER_METHOD": "#2ECC71",  # Light green
            "SERVICE": "#E67E22",  # Orange
            "SERVICE_METHOD": "#F39C12",  # Light orange
            "MAPPER": "#9B59B6",  # Purple
            "MAPPER_METHOD": "#AF7AC5",  # Light purple
            "SQL_STATEMENT": "#E74C3C",  # Red
            "TABLE": "#95A5A6",  # Gray
            "VIEW": "#BDC3C7",  # Light gray
            "PROCEDURE": "#34495E",  # Dark gray
        }

        # Shape mapping for node types
        self.node_shapes = {
            "JSP": "box",
            "CONTROLLER": "diamond",
            "CONTROLLER_METHOD": "dot",
            "SERVICE": "diamond",
            "SERVICE_METHOD": "dot",
            "MAPPER": "diamond",
            "MAPPER_METHOD": "dot",
            "SQL_STATEMENT": "star",
            "TABLE": "box",
            "VIEW": "box",
            "PROCEDURE": "box",
        }

    def create_pyvis_html(
        self,
        output_file: str = "output/graph/interactive_graph.html",
        height: str = "800px",
        width: str = "100%",
        notebook: bool = False
    ) -> str:
        """
        Create interactive PyVis HTML visualization.

        Args:
            output_file: Output HTML file path
            height: Canvas height
            width: Canvas width
            notebook: Whether to run in Jupyter notebook mode

        Returns:
            Path to created HTML file
        """
        try:
            from pyvis.network import Network
        except ImportError:
            logger.error("PyVis not installed. Run: pip install pyvis")
            raise

        logger.info(f"Creating PyVis visualization...")

        # Create PyVis network
        net = Network(
            height=height,
            width=width,
            directed=True,
            notebook=notebook,
            cdn_resources='in_line'  # Embed resources for offline viewing
        )

        # Configure physics for better layout
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 150,
              "springConstant": 0.08,
              "damping": 0.4,
              "avoidOverlap": 0.1
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "timestep": 0.5,
            "stabilization": {
              "enabled": true,
              "iterations": 1000,
              "updateInterval": 25
            }
          },
          "nodes": {
            "font": {
              "size": 14,
              "face": "arial"
            },
            "borderWidth": 2,
            "borderWidthSelected": 4
          },
          "edges": {
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 1.0
              }
            },
            "smooth": {
              "type": "continuous"
            },
            "font": {
              "size": 10,
              "align": "middle"
            }
          },
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """)

        # Add nodes
        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get('type', 'UNKNOWN')
            node_name = attrs.get('name', node_id)

            # Create tooltip
            tooltip = self._create_node_tooltip(node_id, attrs)

            # Get color and shape
            color = self.node_colors.get(node_type, "#95A5A6")
            shape = self.node_shapes.get(node_type, "dot")

            # Calculate node size based on degree
            size = self._calculate_node_size(node_id)

            net.add_node(
                node_id,
                label=node_name,
                title=tooltip,
                color=color,
                shape=shape,
                size=size
            )

        # Add edges
        for u, v, attrs in self.graph.edges(data=True):
            relation = attrs.get('relation', 'UNKNOWN')
            confidence = attrs.get('confidence', 0.5)

            # Create edge tooltip
            edge_tooltip = self._create_edge_tooltip(u, v, attrs)

            # Get edge color based on confidence
            edge_color = self._get_edge_color(confidence)

            # Edge width based on confidence
            edge_width = confidence * 3

            net.add_edge(
                u, v,
                title=edge_tooltip,
                label=relation,
                color=edge_color,
                width=edge_width
            )

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save HTML file
        # Use PyVis's generate_html() to get HTML string, then save with UTF-8
        try:
            html_content = net.generate_html()

            # Write with explicit UTF-8 encoding
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

        except AttributeError:
            # Fallback: generate_html() may not exist in older versions
            # Use save_graph but handle encoding issues
            import os
            import locale

            # Try to set UTF-8 environment
            old_env = os.environ.get('PYTHONIOENCODING')
            try:
                os.environ['PYTHONIOENCODING'] = 'utf-8'
                net.save_graph(str(output_path))
            finally:
                if old_env:
                    os.environ['PYTHONIOENCODING'] = old_env
                elif 'PYTHONIOENCODING' in os.environ:
                    del os.environ['PYTHONIOENCODING']

        logger.info(f"PyVis visualization saved to: {output_path}")
        return str(output_path)

    def create_mermaid_diagram(
        self,
        output_file: str = "output/graph/graph_diagram.mmd",
        max_nodes: int = 50,
        important_node_types: Optional[List[str]] = None
    ) -> str:
        """
        Create Mermaid diagram (text-based).

        Args:
            output_file: Output Mermaid file path
            max_nodes: Maximum nodes to include (for readability)
            important_node_types: Node types to prioritize (if limiting)

        Returns:
            Path to created Mermaid file
        """
        logger.info(f"Creating Mermaid diagram...")

        # Select nodes to include
        if self.graph.number_of_nodes() > max_nodes:
            selected_nodes = self._select_important_nodes(max_nodes, important_node_types)

            # Also include direct neighbors to maintain edges
            # (targets of selected nodes)
            extended_nodes = set(selected_nodes)
            for node in selected_nodes:
                # Add successors (outgoing edges)
                successors = list(self.graph.successors(node))
                # Limit to avoid too many nodes
                extended_nodes.update(successors[:2])  # Max 2 successors per node

            # Limit total nodes
            if len(extended_nodes) > max_nodes * 1.5:
                # Keep only selected + some successors
                extended_nodes = selected_nodes
                for node in list(selected_nodes)[:max_nodes // 2]:
                    extended_nodes.update(list(self.graph.successors(node))[:1])

            subgraph = self.graph.subgraph(extended_nodes)
        else:
            subgraph = self.graph

        # Start Mermaid diagram
        mermaid_lines = ["graph TD"]
        mermaid_lines.append("")

        # Add nodes with styling
        for node_id, attrs in subgraph.nodes(data=True):
            node_type = attrs.get('type', 'UNKNOWN')
            node_name = attrs.get('name', node_id)

            # Sanitize ID for Mermaid
            safe_id = self._sanitize_mermaid_id(node_id)

            # Escape quotes in name
            safe_name = node_name.replace('"', "'")

            # Choose node style based on type
            if node_type in ["CONTROLLER", "SERVICE", "MAPPER"]:
                # Diamond shape
                mermaid_lines.append(f'    {safe_id}{{{safe_name}}}')
            elif node_type == "SQL_STATEMENT":
                # Hexagon
                mermaid_lines.append(f'    {safe_id}{{{{"{safe_name}"}}}}')
            elif node_type in ["TABLE", "VIEW", "PROCEDURE"]:
                # Cylinder
                mermaid_lines.append(f'    {safe_id}[("{safe_name}")]')
            else:
                # Rectangle (default)
                mermaid_lines.append(f'    {safe_id}["{safe_name}"]')

        mermaid_lines.append("")

        # Add edges
        for u, v, attrs in subgraph.edges(data=True):
            relation = attrs.get('relation', 'UNKNOWN')

            safe_u = self._sanitize_mermaid_id(u)
            safe_v = self._sanitize_mermaid_id(v)

            mermaid_lines.append(f'    {safe_u} -->|{relation}| {safe_v}')

        mermaid_lines.append("")

        # Add style classes
        mermaid_lines.append("    %% Style definitions")
        for node_type, color in self.node_colors.items():
            mermaid_lines.append(f'    classDef {node_type.lower()} fill:{color}')

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write Mermaid file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(mermaid_lines))

        logger.info(f"Mermaid diagram saved to: {output_path}")
        logger.info(f"  Nodes: {subgraph.number_of_nodes()}")
        logger.info(f"  Edges: {subgraph.number_of_edges()}")

        return str(output_path)

    def create_graphviz_dot(
        self,
        output_file: str = "output/graph/graph.dot"
    ) -> str:
        """
        Create GraphViz DOT format file.

        Args:
            output_file: Output DOT file path

        Returns:
            Path to created DOT file
        """
        logger.info(f"Creating GraphViz DOT file...")

        # Start DOT format
        dot_lines = ['digraph KnowledgeGraph {']
        dot_lines.append('    rankdir=TB;')  # Top to bottom
        dot_lines.append('    node [style=filled];')
        dot_lines.append('')

        # Add nodes
        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get('type', 'UNKNOWN')
            node_name = attrs.get('name', node_id)

            # Escape quotes
            safe_name = node_name.replace('"', '\\"')

            # Get color
            color = self.node_colors.get(node_type, "#95A5A6")

            # Get shape
            dot_shape = self._get_graphviz_shape(node_type)

            # Create node ID (replace special characters)
            safe_id = f'node_{abs(hash(node_id)) % 1000000}'

            dot_lines.append(
                f'    {safe_id} [label="{safe_name}", '
                f'fillcolor="{color}", shape={dot_shape}];'
            )

        dot_lines.append('')

        # Add edges
        for u, v, attrs in self.graph.edges(data=True):
            relation = attrs.get('relation', 'UNKNOWN')

            safe_u = f'node_{abs(hash(u)) % 1000000}'
            safe_v = f'node_{abs(hash(v)) % 1000000}'

            dot_lines.append(f'    {safe_u} -> {safe_v} [label="{relation}"];')

        dot_lines.append('}')

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write DOT file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(dot_lines))

        logger.info(f"GraphViz DOT file saved to: {output_path}")
        logger.info(f"  To generate PNG: dot -Tpng {output_path} -o graph.png")

        return str(output_path)

    def _create_node_tooltip(self, node_id: str, attrs: Dict[str, Any]) -> str:
        """Create HTML tooltip for node."""
        html_parts = [f"<b>{node_id}</b><br>"]
        html_parts.append(f"Type: {attrs.get('type', 'UNKNOWN')}<br>")

        if 'path' in attrs:
            path = str(attrs['path'])
            # Truncate long paths
            if len(path) > 50:
                path = "..." + path[-47:]
            html_parts.append(f"Path: {path}<br>")

        # Add type-specific attributes
        node_type = attrs.get('type', '')
        if node_type == 'CONTROLLER_METHOD':
            if 'http_method' in attrs:
                html_parts.append(f"HTTP: {attrs['http_method']}<br>")
            if 'url_path' in attrs:
                html_parts.append(f"URL: {attrs['url_path']}<br>")
        elif node_type == 'SQL_STATEMENT':
            if 'sql_type' in attrs:
                html_parts.append(f"SQL Type: {attrs['sql_type']}<br>")
            if 'tables' in attrs:
                tables = attrs['tables']
                if isinstance(tables, list):
                    html_parts.append(f"Tables: {', '.join(tables[:3])}<br>")

        return ''.join(html_parts)

    def _create_edge_tooltip(self, u: str, v: str, attrs: Dict[str, Any]) -> str:
        """Create tooltip for edge."""
        relation = attrs.get('relation', 'UNKNOWN')
        confidence = attrs.get('confidence', 0.0)

        tooltip = f"{relation} (confidence: {confidence:.2f})"
        return tooltip

    def _get_edge_color(self, confidence: float) -> str:
        """Get edge color based on confidence."""
        if confidence >= 0.9:
            return "#27AE60"  # Green - high confidence
        elif confidence >= 0.7:
            return "#F39C12"  # Orange - medium confidence
        else:
            return "#E74C3C"  # Red - low confidence

    def _calculate_node_size(self, node_id: str) -> int:
        """Calculate node size based on degree (connections)."""
        in_degree = self.graph.in_degree(node_id)
        out_degree = self.graph.out_degree(node_id)
        total_degree = in_degree + out_degree

        # Size between 20 and 50
        base_size = 25
        degree_bonus = min(total_degree * 5, 25)
        return base_size + degree_bonus

    def _select_important_nodes(
        self,
        max_nodes: int,
        important_types: Optional[List[str]] = None
    ) -> Set[str]:
        """
        Select most important nodes for visualization.

        Prioritizes nodes with edges to maintain graph connectivity.
        """
        if important_types is None:
            important_types = ["CONTROLLER_METHOD", "SERVICE_METHOD", "MAPPER_METHOD"]

        selected = set()

        # Strategy: Select nodes with highest degree first (most connected)
        # This ensures we get nodes that have edges
        nodes_by_degree = sorted(
            self.graph.nodes(),
            key=lambda n: self.graph.in_degree(n) + self.graph.out_degree(n),
            reverse=True
        )

        # Add high-degree nodes first
        for node_id in nodes_by_degree:
            if len(selected) >= max_nodes:
                break

            # Prefer important types if specified
            node_type = self.graph.nodes[node_id].get('type')
            if important_types and node_type in important_types:
                selected.add(node_id)
            elif len(selected) < max_nodes // 2:  # Fill remaining quota
                selected.add(node_id)

        # Fill remaining quota with important type nodes that have connections
        if len(selected) < max_nodes:
            for node_id, attrs in self.graph.nodes(data=True):
                if len(selected) >= max_nodes:
                    break

                if attrs.get('type') in important_types:
                    # Only add if it has at least one edge
                    if self.graph.in_degree(node_id) > 0 or self.graph.out_degree(node_id) > 0:
                        selected.add(node_id)

        return selected

    def _sanitize_mermaid_id(self, node_id: str) -> str:
        """Sanitize node ID for Mermaid (alphanumeric + underscore)."""
        # Replace special characters with underscore
        safe_id = ''.join(c if c.isalnum() or c == '_' else '_' for c in node_id)

        # Ensure starts with letter (Mermaid requirement)
        if not safe_id[0].isalpha():
            safe_id = 'N' + safe_id

        return safe_id

    def _get_graphviz_shape(self, node_type: str) -> str:
        """Get GraphViz shape for node type."""
        shape_map = {
            "JSP": "box",
            "CONTROLLER": "diamond",
            "CONTROLLER_METHOD": "ellipse",
            "SERVICE": "diamond",
            "SERVICE_METHOD": "ellipse",
            "MAPPER": "diamond",
            "MAPPER_METHOD": "ellipse",
            "SQL_STATEMENT": "hexagon",
            "TABLE": "cylinder",
            "VIEW": "cylinder",
            "PROCEDURE": "box3d",
        }
        return shape_map.get(node_type, "ellipse")

    def export_all_formats(
        self,
        output_dir: str = "output/graph",
        max_mermaid_nodes: int = 50
    ) -> Dict[str, str]:
        """
        Export graph in all supported formats.

        Args:
            output_dir: Output directory for all files
            max_mermaid_nodes: Max nodes for Mermaid diagram

        Returns:
            Dict with paths to created files
        """
        logger.info(f"Exporting graph in all formats to: {output_dir}")

        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # PyVis HTML
        try:
            pyvis_file = self.create_pyvis_html(
                output_file=str(output_dir_path / "interactive_graph.html")
            )
            exported_files["pyvis_html"] = pyvis_file
        except Exception as e:
            logger.error(f"Failed to create PyVis HTML: {e}")

        # Mermaid diagram
        try:
            mermaid_file = self.create_mermaid_diagram(
                output_file=str(output_dir_path / "graph_diagram.mmd"),
                max_nodes=max_mermaid_nodes
            )
            exported_files["mermaid"] = mermaid_file
        except Exception as e:
            logger.error(f"Failed to create Mermaid diagram: {e}")

        # GraphViz DOT
        try:
            dot_file = self.create_graphviz_dot(
                output_file=str(output_dir_path / "graph.dot")
            )
            exported_files["graphviz_dot"] = dot_file
        except Exception as e:
            logger.error(f"Failed to create GraphViz DOT: {e}")

        logger.info(f"Exported {len(exported_files)} formats successfully")
        return exported_files
