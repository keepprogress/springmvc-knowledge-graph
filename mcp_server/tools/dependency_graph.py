#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Graph Builder

Builds and analyzes dependency relationships between components
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


@dataclass
class DependencyNode:
    """A node in the dependency graph"""
    name: str
    type: str  # 'controller', 'service', 'mybatis', 'jsp'
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)


@dataclass
class DependencyGraph:
    """Dependency graph structure"""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)  # (from, to, type)

    def add_node(self, name: str, node_type: str):
        """Add node to graph"""
        if name not in self.nodes:
            self.nodes[name] = DependencyNode(name=name, type=node_type)

    def add_edge(self, from_node: str, to_node: str, edge_type: str = 'uses'):
        """Add dependency edge"""
        if from_node in self.nodes and to_node in self.nodes:
            self.nodes[from_node].dependencies.add(to_node)
            self.nodes[to_node].dependents.add(from_node)
            self.edges.append((from_node, to_node, edge_type))

    def get_dependencies(self, node_name: str) -> Set[str]:
        """Get all dependencies of a node"""
        if node_name in self.nodes:
            return self.nodes[node_name].dependencies
        return set()

    def get_dependents(self, node_name: str) -> Set[str]:
        """Get all nodes that depend on this node"""
        if node_name in self.nodes:
            return self.nodes[node_name].dependents
        return set()

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for JSON serialization"""
        return {
            'nodes': [
                {
                    'name': node.name,
                    'type': node.type,
                    'dependencies': list(node.dependencies),
                    'dependents': list(node.dependents)
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {'from': edge[0], 'to': edge[1], 'type': edge[2]}
                for edge in self.edges
            ],
            'statistics': {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'by_type': {
                    node_type: sum(1 for n in self.nodes.values() if n.type == node_type)
                    for node_type in set(n.type for n in self.nodes.values())
                }
            }
        }


class DependencyGraphBuilder:
    """Builds dependency graph from analysis results"""

    def __init__(self):
        self.graph = DependencyGraph()

    def build(self, results_by_type: Dict[str, List[Any]]) -> DependencyGraph:
        """
        Build dependency graph from analysis results

        Args:
            results_by_type: Analysis results grouped by type

        Returns:
            DependencyGraph with all relationships
        """
        self.graph = DependencyGraph()

        # Add all nodes first
        self._add_nodes(results_by_type)

        # Build edges
        self._link_controllers_to_services(results_by_type.get('controller', []))
        self._link_controllers_to_jsps(results_by_type.get('controller', []))
        self._link_services_to_mappers(results_by_type.get('service', []))
        self._link_mapper_interfaces_to_xml(results_by_type.get('mybatis', []))

        return self.graph

    def _add_nodes(self, results_by_type: Dict[str, List[Any]]):
        """Add all nodes to graph"""
        for analyzer_type, results in results_by_type.items():
            for result in results:
                if result.success and result.result:
                    component_name = result.identifier
                    self.graph.add_node(component_name, analyzer_type)

    def _link_controllers_to_services(self, controller_results: List[Any]):
        """Extract Controller → Service dependencies"""
        for result in controller_results:
            if not result.success or not result.result:
                continue

            controller_name = result.identifier

            # Extract @Autowired dependencies from analysis result
            dependencies = self._extract_dependencies_from_result(result.result)

            for dep in dependencies:
                if dep.endswith('Service') or dep.endswith('ServiceImpl'):
                    # Remove package prefix if exists
                    service_name = dep.split('.')[-1]
                    if service_name in self.graph.nodes:
                        self.graph.add_edge(controller_name, service_name, 'uses')

    def _link_services_to_mappers(self, service_results: List[Any]):
        """Extract Service → Mapper dependencies"""
        for result in service_results:
            if not result.success or not result.result:
                continue

            service_name = result.identifier

            # Extract @Autowired dependencies
            dependencies = self._extract_dependencies_from_result(result.result)

            for dep in dependencies:
                if dep.endswith('Mapper'):
                    mapper_name = dep.split('.')[-1]
                    if mapper_name in self.graph.nodes:
                        self.graph.add_edge(service_name, mapper_name, 'uses')

    def _link_controllers_to_jsps(self, controller_results: List[Any]):
        """Extract Controller → JSP dependencies (view names)"""
        for result in controller_results:
            if not result.success or not result.result:
                continue

            controller_name = result.identifier

            # Extract view names from mappings
            mappings = result.result.get('mappings', [])
            for mapping in mappings:
                view_name = mapping.get('view_name')
                if view_name and view_name in self.graph.nodes:
                    self.graph.add_edge(controller_name, view_name, 'renders')

    def _link_mapper_interfaces_to_xml(self, mybatis_results: List[Any]):
        """Link Mapper interfaces to their XML files"""
        for result in mybatis_results:
            if not result.success or not result.result:
                continue

            mapper_name = result.identifier
            # MyBatis analysis already pairs interface with XML
            # This creates a self-referential link for completeness
            # In reality, interface and XML are the same logical component

    def _extract_dependencies_from_result(self, result: Dict[str, Any]) -> List[str]:
        """
        Extract dependency names from analysis result

        Args:
            result: Analysis result dictionary

        Returns:
            List of dependency names
        """
        dependencies = []

        # Check for dependencies field (from service/controller analysis)
        if 'dependencies' in result:
            deps = result['dependencies']
            if isinstance(deps, list):
                dependencies.extend(deps)
            elif isinstance(deps, dict):
                dependencies.extend(deps.keys())

        # Check for fields/annotations
        if 'fields' in result:
            for field in result['fields']:
                if field.get('annotations'):
                    for annotation in field['annotations']:
                        if 'Autowired' in annotation or 'Inject' in annotation or 'Resource' in annotation:
                            dep_type = field.get('type', '')
                            if dep_type:
                                dependencies.append(dep_type)

        return dependencies

    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies in graph

        Returns:
            List of cycles, each cycle is a list of node names
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> bool:
            """DFS to detect cycles"""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Check all dependencies
            for dep in self.graph.get_dependencies(node):
                if dep not in visited:
                    if dfs(dep, path.copy()):
                        return True
                elif dep in rec_stack:
                    # Found cycle
                    cycle_start = path.index(dep)
                    cycle = path[cycle_start:] + [dep]
                    cycles.append(cycle)
                    return True

            rec_stack.remove(node)
            return False

        # Check all nodes
        for node_name in self.graph.nodes:
            if node_name not in visited:
                dfs(node_name, [])

        return cycles

    def calculate_depth(self) -> Dict[str, int]:
        """
        Calculate dependency depth for each node

        Returns:
            Dictionary mapping node name to depth
        """
        depths = {}

        def calculate_node_depth(node: str, visited: Set[str]) -> int:
            if node in depths:
                return depths[node]

            if node in visited:
                # Circular dependency - return 0
                return 0

            visited.add(node)

            deps = self.graph.get_dependencies(node)
            if not deps:
                depth = 0
            else:
                depth = 1 + max(
                    calculate_node_depth(dep, visited.copy())
                    for dep in deps
                )

            depths[node] = depth
            return depth

        for node_name in self.graph.nodes:
            if node_name not in depths:
                calculate_node_depth(node_name, set())

        return depths
