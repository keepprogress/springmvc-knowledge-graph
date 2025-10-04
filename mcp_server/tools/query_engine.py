#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Engine for Knowledge Graph

Provides query capabilities for dependency graph analysis including:
- Call chain discovery
- Impact analysis
- Graph queries
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .dependency_graph import DependencyGraph

logger = logging.getLogger(__name__)


@dataclass
class CallChain:
    """Represents a call chain from start to end"""
    path: List[str]
    node_types: List[str]
    edge_types: List[str]
    depth: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'path': self.path,
            'node_types': self.node_types,
            'edge_types': self.edge_types,
            'depth': self.depth
        }

    def format(self) -> str:
        """Format call chain as readable string"""
        lines = []
        for i, (node, node_type) in enumerate(zip(self.path, self.node_types)):
            indent = "  " * i
            arrow = "->" if i > 0 else ""
            lines.append(f"{indent}{arrow} [{node_type}] {node}")
        return "\n".join(lines)


@dataclass
class ImpactAnalysisResult:
    """Result of impact analysis"""
    target_node: str
    upstream: Dict[str, List[str]]  # Nodes that depend on target
    downstream: Dict[str, List[str]]  # Nodes that target depends on
    total_upstream: int
    total_downstream: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'target_node': self.target_node,
            'upstream': self.upstream,
            'downstream': self.downstream,
            'total_upstream': self.total_upstream,
            'total_downstream': self.total_downstream
        }


class QueryEngine:
    """Query engine for knowledge graph"""

    def __init__(self, graph: DependencyGraph):
        """
        Initialize query engine

        Args:
            graph: DependencyGraph to query
        """
        self.graph = graph

    def find_call_chains(
        self,
        start_node: str,
        end_node: Optional[str] = None,
        max_depth: int = 10
    ) -> List[CallChain]:
        """
        Find call chains from start node to end node

        Args:
            start_node: Starting node name
            end_node: Ending node name (if None, returns direct dependencies)
            max_depth: Maximum depth to search

        Returns:
            List of CallChain objects
        """
        if start_node not in self.graph.nodes:
            return []

        if end_node is None:
            # Return direct dependencies as single-hop chains
            chains = []
            deps = self.graph.get_dependencies(start_node)
            for dep in deps:
                chain = CallChain(
                    path=[start_node, dep],
                    node_types=[
                        self.graph.nodes[start_node].type,
                        self.graph.nodes[dep].type
                    ],
                    edge_types=self._get_edge_type(start_node, dep),
                    depth=1
                )
                chains.append(chain)
            return chains

        # Find all paths from start to end using DFS
        paths = self._find_all_paths(start_node, end_node, max_depth)

        # Convert paths to CallChain objects
        chains = []
        for path in paths:
            node_types = [self.graph.nodes[node].type for node in path]
            edge_types = []
            for i in range(len(path) - 1):
                edge_types.append(self._get_edge_type(path[i], path[i + 1]))

            chain = CallChain(
                path=path,
                node_types=node_types,
                edge_types=edge_types,
                depth=len(path) - 1
            )
            chains.append(chain)

        return chains

    def _find_all_paths(
        self,
        start: str,
        end: str,
        max_depth: int,
        visited: Optional[Set[str]] = None,
        path: Optional[List[str]] = None
    ) -> List[List[str]]:
        """
        Find all paths from start to end using DFS with backtracking

        Args:
            start: Start node
            end: End node
            max_depth: Maximum depth
            visited: Set of visited nodes (modified in-place, uses backtracking)
            path: Current path (modified in-place, uses backtracking)

        Returns:
            List of paths
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []

        # Add current node to path and visited set
        visited.add(start)
        path.append(start)

        # Check if we reached the end
        if start == end:
            result = [path.copy()]  # Must copy since we'll modify path during backtracking
        # Check max depth
        elif len(path) > max_depth:
            result = []
        else:
            # Explore dependencies
            paths = []
            for dep in self.graph.get_dependencies(start):
                if dep not in visited:
                    # Recurse without copying - backtracking handles cleanup
                    sub_paths = self._find_all_paths(dep, end, max_depth, visited, path)
                    paths.extend(sub_paths)
            result = paths

        # Backtrack: remove current node from path and visited set
        path.pop()
        visited.remove(start)

        return result

    def _get_edge_type(self, from_node: str, to_node: str) -> List[str]:
        """Get edge types between two nodes"""
        edge_types = []
        for edge in self.graph.edges:
            if edge[0] == from_node and edge[1] == to_node:
                edge_types.append(edge[2])

        if not edge_types:
            logger.debug(
                f"No edge type found between '{from_node}' and '{to_node}', "
                f"using 'unknown' as fallback"
            )
            return ['unknown']

        return edge_types

    def impact_analysis(
        self,
        node_id: str,
        direction: str = "both",
        max_depth: int = 5
    ) -> Optional[ImpactAnalysisResult]:
        """
        Analyze impact of changing a node

        Args:
            node_id: Node to analyze
            direction: "upstream", "downstream", or "both"
            max_depth: Maximum depth to analyze

        Returns:
            ImpactAnalysisResult or None if node doesn't exist
        """
        if node_id not in self.graph.nodes:
            return None

        upstream = {}
        downstream = {}

        if direction in ["upstream", "both"]:
            upstream = self._find_upstream(node_id, max_depth)

        if direction in ["downstream", "both"]:
            downstream = self._find_downstream(node_id, max_depth)

        total_upstream = sum(len(nodes) for nodes in upstream.values())
        total_downstream = sum(len(nodes) for nodes in downstream.values())

        return ImpactAnalysisResult(
            target_node=node_id,
            upstream=upstream,
            downstream=downstream,
            total_upstream=total_upstream,
            total_downstream=total_downstream
        )

    def _find_upstream(self, node: str, max_depth: int) -> Dict[str, List[str]]:
        """
        Find all upstream dependencies (nodes that depend on this node)

        Args:
            node: Target node
            max_depth: Maximum depth

        Returns:
            Dictionary mapping depth level to list of nodes
        """
        upstream = {}
        visited = set()

        def explore(current_node: str, depth: int):
            if depth > max_depth or current_node in visited:
                return

            visited.add(current_node)
            dependents = self.graph.get_dependents(current_node)

            if dependents:
                level_key = f"level_{depth}"
                if level_key not in upstream:
                    upstream[level_key] = []

                for dependent in dependents:
                    if dependent not in visited:
                        node_type = self.graph.nodes[dependent].type
                        upstream[level_key].append(f"[{node_type}] {dependent}")
                        explore(dependent, depth + 1)

        explore(node, 1)
        return upstream

    def _find_downstream(self, node: str, max_depth: int) -> Dict[str, List[str]]:
        """
        Find all downstream dependencies (nodes this node depends on)

        Args:
            node: Target node
            max_depth: Maximum depth

        Returns:
            Dictionary mapping depth level to list of nodes
        """
        downstream = {}
        visited = set()

        def explore(current_node: str, depth: int):
            if depth > max_depth or current_node in visited:
                return

            visited.add(current_node)
            dependencies = self.graph.get_dependencies(current_node)

            if dependencies:
                level_key = f"level_{depth}"
                if level_key not in downstream:
                    downstream[level_key] = []

                for dep in dependencies:
                    if dep not in visited:
                        node_type = self.graph.nodes[dep].type
                        downstream[level_key].append(f"[{node_type}] {dep}")
                        explore(dep, depth + 1)

        explore(node, 1)
        return downstream

    def query_by_type(self, node_type: str) -> List[str]:
        """
        Query all nodes of a specific type

        Args:
            node_type: Type to query (controller, service, mybatis, jsp)

        Returns:
            List of node names
        """
        return [
            node.name
            for node in self.graph.nodes.values()
            if node.type == node_type
        ]

    def get_node_info(self, node_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a node

        Args:
            node_name: Node name

        Returns:
            Dictionary with node information or None
        """
        if node_name not in self.graph.nodes:
            return None

        node = self.graph.nodes[node_name]
        return {
            'name': node.name,
            'type': node.type,
            'dependencies': list(node.dependencies),
            'dependents': list(node.dependents),
            'dependency_count': len(node.dependencies),
            'dependent_count': len(node.dependents)
        }

    def find_nodes_by_pattern(self, pattern: str) -> List[str]:
        """
        Find nodes matching a pattern

        Args:
            pattern: Pattern to match (case-insensitive substring)

        Returns:
            List of matching node names
        """
        pattern_lower = pattern.lower()
        return [
            node.name
            for node in self.graph.nodes.values()
            if pattern_lower in node.name.lower()
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get graph statistics

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_nodes': len(self.graph.nodes),
            'total_edges': len(self.graph.edges),
            'by_type': {},
            'most_dependencies': [],
            'most_dependents': []
        }

        # Count by type
        for node in self.graph.nodes.values():
            if node.type not in stats['by_type']:
                stats['by_type'][node.type] = 0
            stats['by_type'][node.type] += 1

        # Find nodes with most dependencies
        nodes_with_deps = sorted(
            self.graph.nodes.values(),
            key=lambda n: len(n.dependencies),
            reverse=True
        )[:5]
        stats['most_dependencies'] = [
            {'name': n.name, 'type': n.type, 'count': len(n.dependencies)}
            for n in nodes_with_deps
        ]

        # Find nodes with most dependents
        nodes_with_dependents = sorted(
            self.graph.nodes.values(),
            key=lambda n: len(n.dependents),
            reverse=True
        )[:5]
        stats['most_dependents'] = [
            {'name': n.name, 'type': n.type, 'count': len(n.dependents)}
            for n in nodes_with_dependents
        ]

        return stats
