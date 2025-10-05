#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Graph Builder - Phase 5.1.4

Builds a NetworkX directed graph from nodes and edges.
Exports graph to JSON format with statistics.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import networkx as nx

from mcp_server.tools.graph_data_loader import GraphDataLoader
from mcp_server.tools.graph_node_builder import NodeBuilder
from mcp_server.tools.graph_edge_builder import EdgeBuilder

logger = logging.getLogger(__name__)


class CodeGraphBuilder:
    """
    Builds a complete code knowledge graph using NetworkX.

    Orchestrates:
    1. Data loading (GraphDataLoader)
    2. Node creation (NodeBuilder)
    3. Edge creation (EdgeBuilder)
    4. NetworkX graph construction
    5. Export to JSON
    """

    def __init__(self, base_dir: str = "output"):
        """
        Initialize CodeGraphBuilder.

        Args:
            base_dir: Base directory containing analysis results
        """
        self.base_dir = Path(base_dir)
        self.graph = nx.DiGraph()

        # Initialize components
        self.loader = GraphDataLoader(base_dir=str(base_dir))
        self.node_builder = None  # Will be initialized after data load
        self.edge_builder = None  # Will be initialized after node creation

        # Track statistics
        self.statistics = {}

    def build_graph(self, force_reload: bool = False) -> nx.DiGraph:
        """
        Build complete code-based graph.

        Args:
            force_reload: If True, reload data even if already loaded

        Returns:
            NetworkX DiGraph with all nodes and edges
        """
        logger.info("Building code knowledge graph...")

        # Step 1: Load analysis data
        logger.info("Step 1: Loading analysis data...")
        # Check if data is actually populated (not just initialized as empty dict)
        data_loaded = any([
            len(self.loader.data.get("jsp", [])) > 0,
            len(self.loader.data.get("controllers", [])) > 0,
            len(self.loader.data.get("services", [])) > 0,
            len(self.loader.data.get("mappers", [])) > 0
        ])

        if force_reload or not data_loaded:
            self.loader.load_all_analysis_results()

        # Validate data
        if not self.loader.validate_data():
            logger.warning(f"Data validation found {len(self.loader.validation_issues)} issues")
            for issue in self.loader.validation_issues:
                logger.warning(f"  - {issue}")

        # Step 2: Create nodes
        logger.info("Step 2: Creating graph nodes...")
        self.node_builder = NodeBuilder(self.loader)
        all_nodes = self.node_builder.build_all_nodes()

        logger.info(f"Created {len(all_nodes)} nodes")

        # Step 3: Add nodes to NetworkX graph
        logger.info("Step 3: Adding nodes to graph...")
        for node in all_nodes:
            self.graph.add_node(
                node.id,
                type=node.type,
                name=node.name,
                path=node.path,
                **node.metadata
            )

        logger.info(f"Graph now has {self.graph.number_of_nodes()} nodes")

        # Step 4: Create edges
        logger.info("Step 4: Creating graph edges...")
        self.edge_builder = EdgeBuilder(self.node_builder)
        all_edges = self.edge_builder.build_all_edges()

        logger.info(f"Created {len(all_edges)} edges")

        # Step 5: Add edges to NetworkX graph
        logger.info("Step 5: Adding edges to graph...")
        for edge in all_edges:
            self.graph.add_edge(
                edge.source,
                edge.target,
                relation=edge.type,
                confidence=edge.confidence,
                source_type=edge.source_type,
                description=edge.description,
                **edge.metadata
            )

        logger.info(f"Graph now has {self.graph.number_of_edges()} edges")

        # Step 6: Calculate statistics
        logger.info("Step 6: Calculating statistics...")
        self.statistics = self._calculate_statistics()

        logger.info("Graph construction complete!")
        return self.graph

    def export_graph(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Export graph to JSON files.

        Args:
            output_dir: Output directory (default: {base_dir}/graph)

        Returns:
            Dict with file paths: {
                "graph": "path/to/code_based_graph.json",
                "low_confidence": "path/to/low_confidence_edges.json",
                "statistics": "path/to/graph_statistics.json"
            }
        """
        if self.graph.number_of_nodes() == 0:
            raise ValueError("Graph is empty. Call build_graph() first.")

        # Determine output directory
        if output_dir is None:
            output_dir = self.base_dir / "graph"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare file paths
        graph_file = output_dir / "code_based_graph.json"
        low_conf_file = output_dir / "low_confidence_edges.json"
        stats_file = output_dir / "graph_statistics.json"

        logger.info(f"Exporting graph to {output_dir}...")

        # Export complete graph
        self._export_complete_graph(graph_file)

        # Export low confidence edges
        self._export_low_confidence_edges(low_conf_file)

        # Export statistics
        self._export_statistics(stats_file)

        logger.info("Graph export complete!")

        return {
            "graph": str(graph_file),
            "low_confidence": str(low_conf_file),
            "statistics": str(stats_file)
        }

    def _export_complete_graph(self, output_file: Path):
        """Export complete graph to JSON."""
        graph_data = {
            "metadata": {
                "format": "code_knowledge_graph",
                "version": "1.0",
                "layer": "code_based",
                "generated_by": "CodeGraphBuilder"
            },
            "nodes": [
                {
                    "id": node_id,
                    **self.graph.nodes[node_id]
                }
                for node_id in self.graph.nodes
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    **self.graph.edges[u, v]
                }
                for u, v in self.graph.edges
            ],
            "statistics": self.statistics
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported complete graph: {output_file}")

    def _export_low_confidence_edges(self, output_file: Path, threshold: float = 0.8):
        """
        Export edges with confidence < threshold for LLM verification.

        Args:
            output_file: Output file path
            threshold: Confidence threshold (default: 0.8)
        """
        low_confidence_edges = [
            {
                "source": u,
                "target": v,
                "source_node": self.graph.nodes[u],
                "target_node": self.graph.nodes[v],
                **self.graph.edges[u, v]
            }
            for u, v in self.graph.edges
            if self.graph.edges[u, v].get("confidence", 1.0) < threshold
        ]

        output_data = {
            "metadata": {
                "threshold": threshold,
                "total_edges": len(low_confidence_edges),
                "purpose": "LLM verification candidates"
            },
            "edges": low_confidence_edges
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(low_confidence_edges)} low confidence edges: {output_file}")

    def _export_statistics(self, output_file: Path):
        """Export graph statistics to JSON."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.statistics, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported statistics: {output_file}")

    def _calculate_statistics(self) -> Dict[str, Any]:
        """
        Calculate graph statistics.

        Returns:
            Statistics dictionary with:
            - Node counts by type
            - Edge counts by relation
            - Confidence distribution
            - Coverage metrics
            - Graph properties (connected components, etc.)
        """
        stats = {
            "nodes": {
                "total": self.graph.number_of_nodes(),
                "by_type": self._count_nodes_by_type()
            },
            "edges": {
                "total": self.graph.number_of_edges(),
                "by_relation": self._count_edges_by_relation(),
                "by_confidence": self._count_edges_by_confidence()
            },
            "coverage": self._calculate_coverage(),
            "graph_properties": self._calculate_graph_properties()
        }

        return stats

    def _count_nodes_by_type(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node_id in self.graph.nodes:
            node_type = self.graph.nodes[node_id].get("type", "UNKNOWN")
            counts[node_type] = counts.get(node_type, 0) + 1
        return dict(sorted(counts.items()))

    def _count_edges_by_relation(self) -> Dict[str, int]:
        """Count edges by relation type."""
        counts = {}
        for u, v in self.graph.edges:
            relation = self.graph.edges[u, v].get("relation", "UNKNOWN")
            counts[relation] = counts.get(relation, 0) + 1
        return dict(sorted(counts.items()))

    def _count_edges_by_confidence(self) -> Dict[str, int]:
        """Count edges by confidence level."""
        counts = {
            "high (>= 0.9)": 0,
            "medium (0.7-0.9)": 0,
            "low (< 0.7)": 0
        }

        for u, v in self.graph.edges:
            confidence = self.graph.edges[u, v].get("confidence", 1.0)

            if confidence >= 0.9:
                counts["high (>= 0.9)"] += 1
            elif confidence >= 0.7:
                counts["medium (0.7-0.9)"] += 1
            else:
                counts["low (< 0.7)"] += 1

        return counts

    def _calculate_coverage(self) -> Dict[str, float]:
        """
        Calculate coverage metrics (% of nodes with expected connections).

        Returns:
            Coverage percentages for each layer connection
        """
        coverage = {}

        # Get node counts by type
        node_counts = self._count_nodes_by_type()

        # JSP with controller connections
        jsp_count = node_counts.get("JSP", 0)
        if jsp_count > 0:
            jsp_with_controllers = len([
                n for n in self.graph.nodes
                if self.graph.nodes[n].get("type") == "JSP" and
                len(list(self.graph.successors(n))) > 0
            ])
            coverage["jsp_with_controllers"] = round(jsp_with_controllers / jsp_count, 2)
        else:
            coverage["jsp_with_controllers"] = 0.0

        # Controllers with service connections
        controller_method_count = node_counts.get("CONTROLLER_METHOD", 0)
        if controller_method_count > 0:
            controllers_with_services = len([
                n for n in self.graph.nodes
                if self.graph.nodes[n].get("type") == "CONTROLLER_METHOD" and
                any(self.graph.edges[n, succ].get("relation") == "INVOKES"
                    for succ in self.graph.successors(n))
            ])
            coverage["controllers_with_services"] = round(
                controllers_with_services / controller_method_count, 2
            )
        else:
            coverage["controllers_with_services"] = 0.0

        # Services with mapper connections
        service_method_count = node_counts.get("SERVICE_METHOD", 0)
        if service_method_count > 0:
            services_with_mappers = len([
                n for n in self.graph.nodes
                if self.graph.nodes[n].get("type") == "SERVICE_METHOD" and
                any(self.graph.edges[n, succ].get("relation") == "USES"
                    for succ in self.graph.successors(n))
            ])
            coverage["services_with_mappers"] = round(
                services_with_mappers / service_method_count, 2
            )
        else:
            coverage["services_with_mappers"] = 0.0

        # Mappers with SQL connections
        mapper_method_count = node_counts.get("MAPPER_METHOD", 0)
        if mapper_method_count > 0:
            mappers_with_sql = len([
                n for n in self.graph.nodes
                if self.graph.nodes[n].get("type") == "MAPPER_METHOD" and
                any(self.graph.edges[n, succ].get("relation") == "EXECUTES"
                    for succ in self.graph.successors(n))
            ])
            coverage["mappers_with_sql"] = round(
                mappers_with_sql / mapper_method_count, 2
            )
        else:
            coverage["mappers_with_sql"] = 0.0

        return coverage

    def _calculate_graph_properties(self) -> Dict[str, Any]:
        """
        Calculate graph structural properties.

        Returns:
            Graph properties: density, connected components, etc.
        """
        properties = {}

        # Graph density (0 = sparse, 1 = complete)
        if self.graph.number_of_nodes() > 1:
            properties["density"] = round(nx.density(self.graph), 4)
        else:
            properties["density"] = 0.0

        # Number of connected components (undirected view)
        undirected = self.graph.to_undirected()
        properties["connected_components"] = nx.number_connected_components(undirected)

        # Number of weakly connected components (directed)
        properties["weakly_connected_components"] = nx.number_weakly_connected_components(
            self.graph
        )

        # Identify orphan nodes (no incoming or outgoing edges)
        orphan_nodes = [
            n for n in self.graph.nodes
            if self.graph.in_degree(n) == 0 and self.graph.out_degree(n) == 0
        ]
        properties["orphan_nodes"] = len(orphan_nodes)

        # Identify source nodes (no incoming edges)
        source_nodes = [
            n for n in self.graph.nodes
            if self.graph.in_degree(n) == 0 and self.graph.out_degree(n) > 0
        ]
        properties["source_nodes"] = len(source_nodes)

        # Identify sink nodes (no outgoing edges)
        sink_nodes = [
            n for n in self.graph.nodes
            if self.graph.in_degree(n) > 0 and self.graph.out_degree(n) == 0
        ]
        properties["sink_nodes"] = len(sink_nodes)

        # Average degree
        if self.graph.number_of_nodes() > 0:
            total_degree = sum(dict(self.graph.degree()).values())
            properties["average_degree"] = round(
                total_degree / self.graph.number_of_nodes(), 2
            )
        else:
            properties["average_degree"] = 0.0

        return properties

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the graph.

        Returns:
            Summary dictionary with key metrics
        """
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "node_types": len(self._count_nodes_by_type()),
            "edge_relations": len(self._count_edges_by_relation()),
            "statistics": self.statistics
        }

    def validate_graph(self) -> Tuple[bool, List[str]]:
        """
        Validate graph structure and data quality.

        Returns:
            (is_valid, issues) tuple
        """
        issues = []

        # Check for self-loops
        self_loops = list(nx.selfloop_edges(self.graph))
        if self_loops:
            issues.append(f"Found {len(self_loops)} self-loop edges (not recommended)")

        # Check confidence values
        for u, v in self.graph.edges:
            confidence = self.graph.edges[u, v].get("confidence", 1.0)
            if not 0.0 <= confidence <= 1.0:
                issues.append(
                    f"Invalid confidence {confidence} for edge {u} -> {v}"
                )

        # Check for missing edge attributes
        required_edge_attrs = ["relation", "confidence"]
        for u, v in self.graph.edges:
            edge_data = self.graph.edges[u, v]
            for attr in required_edge_attrs:
                if attr not in edge_data:
                    issues.append(
                        f"Missing required attribute '{attr}' in edge {u} -> {v}"
                    )

        # Check for missing node attributes
        required_node_attrs = ["type", "name"]
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            for attr in required_node_attrs:
                if attr not in node_data:
                    issues.append(
                        f"Missing required attribute '{attr}' in node {node_id}"
                    )

        is_valid = len(issues) == 0
        return is_valid, issues
