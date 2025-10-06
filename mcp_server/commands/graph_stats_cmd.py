#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/graph-stats Slash Command

Display knowledge graph statistics and metrics
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args


class GraphStatsCommand(BaseCommand):
    """Command: /graph-stats"""

    def get_name(self) -> str:
        return "graph-stats"

    def get_description(self) -> str:
        return "Display knowledge graph statistics and metrics"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /graph-stats
  /graph-stats --detailed
  /graph-stats --graph-file=output/graph/my_graph.json
  /graph-stats --graph-file=output/graph/merged_graph.json --detailed
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            '--graph-file',
            help='Path to graph JSON file (default: latest in output/graph/)'
        )

        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdown by type'
        )

        return parser

    def _find_latest_graph(self) -> Path:
        """
        Find the latest graph file in output/graph/

        Returns:
            Path to latest graph JSON file

        Raises:
            FileNotFoundError: If no graph files found
        """
        graph_dir = self.server.project_root / "output" / "graph"

        if not graph_dir.exists():
            raise FileNotFoundError(f"Graph directory not found: {graph_dir}")

        # Find all JSON files (excluding stats and low_confidence files)
        graph_files = [
            f for f in graph_dir.glob("*.json")
            if not f.stem.endswith('_stats') and not f.stem.endswith('_low_confidence')
        ]

        if not graph_files:
            raise FileNotFoundError(
                f"No graph files found in {graph_dir}\n"
                f"Run /build-graph first to create a graph."
            )

        # Return most recently modified
        latest = max(graph_files, key=lambda f: f.stat().st_mtime)
        return latest

    @validate_args
    async def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute /graph-stats command"""
        parsed_args = self.parse_args(args)

        # Determine graph file
        if parsed_args.graph_file:
            graph_path = self.resolve_path(parsed_args.graph_file)
        else:
            try:
                graph_path = self._find_latest_graph()
            except FileNotFoundError as e:
                return self.format_error(str(e))

        # Check if file exists
        if not graph_path.exists():
            return self.format_error(f"Graph file not found: {graph_path}")

        # Import GraphQueryEngine (lazy import)
        from mcp_server.tools.graph_query_engine import GraphQueryEngine
        import networkx as nx

        try:
            # Load graph
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)

            # Reconstruct NetworkX graph from custom format
            # CodeGraphBuilder exports with "nodes" and "edges" keys, not NetworkX node-link format
            graph = nx.DiGraph()

            # Add nodes
            for node_data in graph_data.get("nodes", []):
                node_id = node_data["id"]
                node_attrs = {k: v for k, v in node_data.items() if k != "id"}
                graph.add_node(node_id, **node_attrs)

            # Add edges
            for edge_data in graph_data.get("edges", []):
                source = edge_data["source"]
                target = edge_data["target"]
                edge_attrs = {k: v for k, v in edge_data.items() if k not in ("source", "target")}
                graph.add_edge(source, target, **edge_attrs)

            # Create query engine for advanced stats
            query_engine = GraphQueryEngine(graph)

            # Basic statistics
            total_nodes = graph.number_of_nodes()
            total_edges = graph.number_of_edges()

            # Nodes by type
            nodes_by_type = {}
            for node, data in graph.nodes(data=True):
                node_type = data.get('type', 'UNKNOWN')
                nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1

            # Edges by relation
            edges_by_relation = {}
            for source, target, data in graph.edges(data=True):
                relation = data.get('relation', 'UNKNOWN')
                edges_by_relation[relation] = edges_by_relation.get(relation, 0) + 1

            # Graph density (actual edges / possible edges)
            max_edges = total_nodes * (total_nodes - 1)  # Directed graph
            density = total_edges / max_edges if max_edges > 0 else 0.0

            # Connected components (weakly connected for directed graph)
            num_components = nx.number_weakly_connected_components(graph)

            # Orphan nodes (no incoming or outgoing edges)
            orphan_nodes = [
                node for node in graph.nodes()
                if graph.in_degree(node) == 0 and graph.out_degree(node) == 0
            ]

            # Build basic message
            message = (
                f"Graph Statistics: {graph_path.name}\n"
                f"  • Total Nodes: {total_nodes}\n"
                f"  • Total Edges: {total_edges}\n"
                f"  • Density: {density:.4f}\n"
                f"  • Connected Components: {num_components}\n"
                f"  • Orphan Nodes: {len(orphan_nodes)}"
            )

            # Add detailed breakdown if requested
            if parsed_args.detailed:
                message += "\n\n--- Nodes by Type ---"
                for node_type, count in sorted(nodes_by_type.items(), key=lambda x: -x[1]):
                    message += f"\n  • {node_type}: {count}"

                message += "\n\n--- Edges by Relation ---"
                for relation, count in sorted(edges_by_relation.items(), key=lambda x: -x[1]):
                    message += f"\n  • {relation}: {count}"

                if orphan_nodes:
                    message += f"\n\n--- Orphan Nodes ({len(orphan_nodes)}) ---"
                    for orphan in orphan_nodes[:10]:  # Show first 10
                        message += f"\n  • {orphan}"
                    if len(orphan_nodes) > 10:
                        message += f"\n  ... and {len(orphan_nodes) - 10} more"

            # Prepare response data
            data = {
                'graph_file': str(graph_path),
                'total_nodes': total_nodes,
                'total_edges': total_edges,
                'density': round(density, 4),
                'connected_components': num_components,
                'orphan_nodes_count': len(orphan_nodes),
                'nodes_by_type': nodes_by_type,
                'edges_by_relation': edges_by_relation
            }

            if parsed_args.detailed:
                data['orphan_nodes'] = orphan_nodes

            return self.format_success(message, data)

        except json.JSONDecodeError as e:
            return self.format_error(f"Invalid graph JSON: {e}")
        except Exception as e:
            return self.format_error(f"Failed to analyze graph: {str(e)}")
