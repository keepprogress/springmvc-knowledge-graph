#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Query Engine for Knowledge Graph Analysis

Provides comprehensive querying capabilities:
- Path finding (shortest, all paths, specific types)
- Dependency analysis (upstream, downstream, trees)
- Impact analysis (change impact, affected nodes)
- Graph metrics and statistics
"""

import networkx as nx
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class GraphQueryEngine:
    """Query engine for knowledge graph analysis."""

    def __init__(self, graph: nx.DiGraph):
        """
        Initialize Graph Query Engine.

        Args:
            graph: NetworkX DiGraph to query
        """
        self.graph = graph

        # Lazy-loaded centrality caches for performance
        self._betweenness_cache = None
        self._closeness_cache = None

    # ========== Centrality Caching ==========

    def _get_betweenness_centrality(self) -> Dict[str, float]:
        """
        Get betweenness centrality with lazy loading and caching.

        Calculates once and caches for performance.

        Returns:
            Dictionary mapping node IDs to betweenness centrality scores
        """
        if self._betweenness_cache is None:
            try:
                self._betweenness_cache = nx.betweenness_centrality(self.graph)
                logger.debug(f"Calculated betweenness centrality for {len(self.graph.nodes())} nodes")
            except nx.NetworkXError as e:
                logger.warning(f"Failed to calculate betweenness centrality: {e}")
                self._betweenness_cache = defaultdict(float)

        return self._betweenness_cache

    def _get_closeness_centrality(self) -> Dict[str, float]:
        """
        Get closeness centrality with lazy loading and caching.

        Calculates once and caches for performance.

        Returns:
            Dictionary mapping node IDs to closeness centrality scores
        """
        if self._closeness_cache is None:
            try:
                self._closeness_cache = nx.closeness_centrality(self.graph)
                logger.debug(f"Calculated closeness centrality for {len(self.graph.nodes())} nodes")
            except nx.NetworkXError as e:
                logger.warning(f"Failed to calculate closeness centrality: {e}")
                self._closeness_cache = defaultdict(float)

        return self._closeness_cache

    # ========== Path Finding ==========

    def find_path(
        self,
        source: str,
        target: str,
        relation_types: Optional[List[str]] = None
    ) -> Optional[List[str]]:
        """
        Find a path from source to target.

        Args:
            source: Source node ID
            target: Target node ID
            relation_types: Optional list of allowed relation types

        Returns:
            List of node IDs forming the path, or None if no path exists
        """
        if source not in self.graph or target not in self.graph:
            return None

        try:
            # If no relation filter, use simple path finding
            if not relation_types:
                return nx.shortest_path(self.graph, source, target)

            # Filter edges by relation type
            filtered_edges = [
                (u, v) for u, v, data in self.graph.edges(data=True)
                if data.get('relation') in relation_types
            ]

            # Create subgraph with filtered edges
            subgraph = self.graph.edge_subgraph(filtered_edges)

            return nx.shortest_path(subgraph, source, target)

        except nx.NetworkXNoPath:
            return None

    def find_all_paths(
        self,
        source: str,
        target: str,
        max_length: Optional[int] = None,
        relation_types: Optional[List[str]] = None
    ) -> List[List[str]]:
        """
        Find all simple paths from source to target.

        Args:
            source: Source node ID
            target: Target node ID
            max_length: Maximum path length (None = unlimited)
            relation_types: Optional list of allowed relation types

        Returns:
            List of paths (each path is a list of node IDs)
        """
        if source not in self.graph or target not in self.graph:
            return []

        # Apply relation filter if specified
        if relation_types:
            filtered_edges = [
                (u, v) for u, v, data in self.graph.edges(data=True)
                if data.get('relation') in relation_types
            ]
            subgraph = self.graph.edge_subgraph(filtered_edges)
        else:
            subgraph = self.graph

        # Find all simple paths
        paths = nx.all_simple_paths(
            subgraph,
            source,
            target,
            cutoff=max_length
        )

        return list(paths)

    def find_shortest_path(
        self,
        source: str,
        target: str,
        weight: str = None
    ) -> Tuple[Optional[List[str]], float]:
        """
        Find shortest path with optional weight consideration.

        Args:
            source: Source node ID
            target: Target node ID
            weight: Edge attribute to use as weight (e.g., 'confidence')

        Returns:
            Tuple of (path, total_weight)
        """
        if source not in self.graph or target not in self.graph:
            return (None, float('inf'))

        try:
            if weight:
                # Invert confidence to use as distance (higher confidence = shorter distance)
                def weight_func(u, v, d):
                    conf = d.get('confidence', 0.5)
                    return 1.0 / conf if conf > 0 else 100.0

                length, path = nx.single_source_dijkstra(
                    self.graph,
                    source,
                    target,
                    weight=weight_func
                )
                return (path, length)
            else:
                path = nx.shortest_path(self.graph, source, target)
                return (path, len(path) - 1)

        except nx.NetworkXNoPath:
            return (None, float('inf'))

    # ========== Dependency Analysis ==========

    def get_dependencies(
        self,
        node: str,
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get all dependencies (predecessors) of a node.

        Args:
            node: Node ID
            max_depth: Maximum depth to traverse (None = unlimited)

        Returns:
            Dictionary with dependency information
        """
        if node not in self.graph:
            return {"error": f"Node {node} not found"}

        dependencies = set()
        dependency_tree = {}

        def traverse(current, depth=0):
            if max_depth is not None and depth >= max_depth:
                return

            for pred in self.graph.predecessors(current):
                if pred not in dependencies:
                    dependencies.add(pred)
                    edge_data = self.graph.edges[pred, current]

                    dependency_tree[pred] = {
                        "depth": depth,
                        "relation": edge_data.get('relation', 'UNKNOWN'),
                        "confidence": edge_data.get('confidence', 1.0),
                        "type": self.graph.nodes[pred].get('type', 'UNKNOWN')
                    }

                    traverse(pred, depth + 1)

        traverse(node)

        return {
            "node": node,
            "total_dependencies": len(dependencies),
            "dependencies": list(dependencies),
            "dependency_tree": dependency_tree,
            "max_depth_reached": max_depth if max_depth else "unlimited"
        }

    def get_dependents(
        self,
        node: str,
        max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get all dependents (successors) of a node.

        Args:
            node: Node ID
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary with dependent information
        """
        if node not in self.graph:
            return {"error": f"Node {node} not found"}

        dependents = set()
        dependent_tree = {}

        def traverse(current, depth=0):
            if max_depth is not None and depth >= max_depth:
                return

            for succ in self.graph.successors(current):
                if succ not in dependents:
                    dependents.add(succ)
                    edge_data = self.graph.edges[current, succ]

                    dependent_tree[succ] = {
                        "depth": depth,
                        "relation": edge_data.get('relation', 'UNKNOWN'),
                        "confidence": edge_data.get('confidence', 1.0),
                        "type": self.graph.nodes[succ].get('type', 'UNKNOWN')
                    }

                    traverse(succ, depth + 1)

        traverse(node)

        return {
            "node": node,
            "total_dependents": len(dependents),
            "dependents": list(dependents),
            "dependent_tree": dependent_tree,
            "max_depth_reached": max_depth if max_depth else "unlimited"
        }

    def get_dependency_chain(
        self,
        start_node: str,
        node_type_order: Optional[List[str]] = None
    ) -> List[List[str]]:
        """
        Get dependency chains following typical architecture layers.

        Args:
            start_node: Starting node ID
            node_type_order: Expected node type order (e.g., ['JSP', 'CONTROLLER', 'SERVICE'])

        Returns:
            List of chains (each chain is a list of node IDs)
        """
        if start_node not in self.graph:
            return []

        # Default SpringMVC layer order
        if not node_type_order:
            node_type_order = [
                'JSP',
                'CONTROLLER', 'CONTROLLER_METHOD',
                'SERVICE', 'SERVICE_METHOD',
                'MAPPER', 'MAPPER_METHOD',
                'SQL',
                'TABLE'
            ]

        chains = []

        def build_chain(node, current_chain, expected_types):
            current_chain.append(node)

            # Check if we've reached the end of expected types
            if not expected_types:
                chains.append(current_chain.copy())
                current_chain.pop()
                return

            # Get next expected type
            next_type = expected_types[0]

            # Find successors of the expected type
            found_successor = False
            for succ in self.graph.successors(node):
                succ_type = self.graph.nodes[succ].get('type')
                if succ_type == next_type:
                    build_chain(succ, current_chain, expected_types[1:])
                    found_successor = True

            # If no successor of expected type found, end this chain
            if not found_successor and current_chain:
                chains.append(current_chain.copy())

            current_chain.pop()

        # Get start node type
        start_type = self.graph.nodes[start_node].get('type')

        # Find index in type order
        if start_type in node_type_order:
            start_idx = node_type_order.index(start_type)
            expected_types = node_type_order[start_idx + 1:]
        else:
            expected_types = node_type_order

        build_chain(start_node, [], expected_types)

        return chains

    # ========== Impact Analysis ==========

    def analyze_impact(
        self,
        node: str,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze the impact of changing a node.

        Args:
            node: Node ID to analyze
            max_depth: Maximum depth for impact propagation

        Returns:
            Dictionary with impact analysis
        """
        if node not in self.graph:
            return {"error": f"Node {node} not found"}

        # Get all affected nodes (descendants)
        affected = nx.descendants(self.graph, node)

        # Group by type
        affected_by_type = defaultdict(list)
        for affected_node in affected:
            node_type = self.graph.nodes[affected_node].get('type', 'UNKNOWN')
            affected_by_type[node_type].append(affected_node)

        # Calculate impact score based on:
        # 1. Number of affected nodes
        # 2. Types of affected nodes (critical nodes weight more)
        type_weights = {
            'JSP': 5,  # User-facing, high impact
            'CONTROLLER': 4,
            'CONTROLLER_METHOD': 4,
            'SERVICE': 3,
            'SERVICE_METHOD': 3,
            'MAPPER': 2,
            'MAPPER_METHOD': 2,
            'SQL': 1,
            'TABLE': 1
        }

        impact_score = 0
        for node_type, nodes in affected_by_type.items():
            weight = type_weights.get(node_type, 1)
            impact_score += len(nodes) * weight

        # Normalize score to 0-100
        max_possible_score = len(affected) * max(type_weights.values())
        normalized_score = (impact_score / max_possible_score * 100) if max_possible_score > 0 else 0

        return {
            "node": node,
            "node_type": self.graph.nodes[node].get('type', 'UNKNOWN'),
            "total_affected": len(affected),
            "affected_by_type": dict(affected_by_type),
            "impact_score": round(normalized_score, 2),
            "severity": self._get_impact_severity(normalized_score),
            "affected_nodes": list(affected)
        }

    def _get_impact_severity(self, score: float) -> str:
        """Get impact severity based on score."""
        if score >= 75:
            return "CRITICAL"
        elif score >= 50:
            return "HIGH"
        elif score >= 25:
            return "MEDIUM"
        else:
            return "LOW"

    def find_critical_nodes(
        self,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find critical nodes based on various metrics.

        Args:
            top_n: Number of top critical nodes to return

        Returns:
            List of critical nodes with metrics
        """
        critical_nodes = []

        # Pre-calculate betweenness centrality once for all nodes
        betweenness_scores = self._get_betweenness_centrality()

        for node in self.graph.nodes():
            # Calculate metrics
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)
            total_degree = in_degree + out_degree

            # Betweenness centrality (how often node is on shortest paths)
            betweenness = betweenness_scores.get(node, 0)

            # Impact analysis
            impact = self.analyze_impact(node)

            # Calculate criticality score
            criticality = (
                total_degree * 0.3 +
                betweenness * 100 * 0.3 +
                impact['impact_score'] * 0.4
            )

            critical_nodes.append({
                "node": node,
                "name": self.graph.nodes[node].get('name', node),
                "type": self.graph.nodes[node].get('type', 'UNKNOWN'),
                "criticality_score": round(criticality, 2),
                "in_degree": in_degree,
                "out_degree": out_degree,
                "betweenness_centrality": round(betweenness, 4),
                "impact_score": impact['impact_score']
            })

        # Sort by criticality score
        critical_nodes.sort(key=lambda x: x['criticality_score'], reverse=True)

        return critical_nodes[:top_n]

    # ========== Graph Metrics ==========

    def get_node_metrics(self, node: str) -> Dict[str, Any]:
        """
        Get comprehensive metrics for a node.

        Args:
            node: Node ID

        Returns:
            Dictionary with node metrics
        """
        if node not in self.graph:
            return {"error": f"Node {node} not found"}

        node_data = self.graph.nodes[node]

        # Basic metrics
        in_degree = self.graph.in_degree(node)
        out_degree = self.graph.out_degree(node)

        # Get predecessors and successors
        predecessors = list(self.graph.predecessors(node))
        successors = list(self.graph.successors(node))

        # Centrality metrics (using cached values)
        betweenness_scores = self._get_betweenness_centrality()
        closeness_scores = self._get_closeness_centrality()

        betweenness = betweenness_scores.get(node, 0)
        closeness = closeness_scores.get(node, 0)

        return {
            "node": node,
            "name": node_data.get('name', node),
            "type": node_data.get('type', 'UNKNOWN'),
            "file": node_data.get('file', 'unknown'),
            "degree": {
                "in": in_degree,
                "out": out_degree,
                "total": in_degree + out_degree
            },
            "connections": {
                "predecessors": predecessors,
                "successors": successors
            },
            "centrality": {
                "betweenness": round(betweenness, 4),
                "closeness": round(closeness, 4)
            }
        }

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get overall graph statistics.

        Returns:
            Dictionary with graph statistics
        """
        # Node type distribution
        type_distribution = defaultdict(int)
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', 'UNKNOWN')
            type_distribution[node_type] += 1

        # Relation type distribution
        relation_distribution = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            relation = data.get('relation', 'UNKNOWN')
            relation_distribution[relation] += 1

        # Connected components
        if self.graph.number_of_nodes() > 0:
            try:
                # Convert to undirected for component analysis
                undirected = self.graph.to_undirected()
                num_components = nx.number_connected_components(undirected)
                largest_component_size = len(max(nx.connected_components(undirected), key=len))
            except:
                num_components = 1
                largest_component_size = self.graph.number_of_nodes()
        else:
            num_components = 0
            largest_component_size = 0

        return {
            "nodes": {
                "total": self.graph.number_of_nodes(),
                "by_type": dict(type_distribution)
            },
            "edges": {
                "total": self.graph.number_of_edges(),
                "by_relation": dict(relation_distribution)
            },
            "connectivity": {
                "connected_components": num_components,
                "largest_component_size": largest_component_size,
                "density": round(nx.density(self.graph), 4)
            },
            "complexity": {
                "avg_degree": round(
                    sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(), 2
                ) if self.graph.number_of_nodes() > 0 else 0,
                "max_degree": max(dict(self.graph.degree()).values()) if self.graph.number_of_nodes() > 0 else 0
            }
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"GraphQueryEngine("
            f"nodes={self.graph.number_of_nodes()}, "
            f"edges={self.graph.number_of_edges()})"
        )
