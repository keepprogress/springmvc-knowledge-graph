#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Completeness Scanner for Knowledge Graph

Detects gaps and anomalies in the knowledge graph:
- Orphan nodes (no connections)
- Missing relationships (suspicious patterns)
- LLM verification of questionable structures
"""

import networkx as nx
from typing import Dict, List, Optional, Set
import logging

from mcp_server.tools.llm_query_engine import LLMQueryEngine

logger = logging.getLogger(__name__)


class CompletenessScanner:
    """Scans knowledge graph for completeness and quality issues."""

    # Verification query templates
    VERIFICATION_QUERIES = {
        "orphan_controller": {
            "question": "This controller has no service calls. Is this intentional or a data quality issue?",
            "expected_pattern": "Controllers usually call services"
        },
        "orphan_service": {
            "question": "This service has no mapper usage. Does it call external APIs or is this incomplete?",
            "expected_pattern": "Services usually call mappers or external APIs"
        },
        "orphan_mapper": {
            "question": "This mapper is not called by any service. Is it legacy code or missing relationship?",
            "expected_pattern": "Mappers should be called by services"
        },
        "missing_ajax": {
            "question": "This JSP has forms but no AJAX calls detected. Are there missing endpoints?",
            "expected_pattern": "Forms usually have associated AJAX or submit endpoints"
        },
        "no_sql": {
            "question": "This mapper method has no SQL statement. Is it using annotations or is SQL missing?",
            "expected_pattern": "Mapper methods should have SQL statements or annotations"
        }
    }

    def __init__(self, llm_engine: Optional[LLMQueryEngine] = None):
        """
        Initialize Completeness Scanner.

        Args:
            llm_engine: LLM Query Engine for verification (optional)
        """
        self.llm = llm_engine or LLMQueryEngine()

    async def find_orphan_nodes(self, graph: nx.DiGraph) -> Dict[str, List[str]]:
        """
        Find nodes with no incoming or outgoing edges.

        Args:
            graph: Knowledge graph

        Returns:
            Dictionary mapping node types to lists of orphan node IDs
        """
        orphans = {}

        for node_id in graph.nodes():
            in_degree = graph.in_degree(node_id)
            out_degree = graph.out_degree(node_id)

            if in_degree == 0 and out_degree == 0:
                node_data = graph.nodes[node_id]
                node_type = node_data.get('type', 'UNKNOWN')

                if node_type not in orphans:
                    orphans[node_type] = []

                orphans[node_type].append({
                    "id": node_id,
                    "name": node_data.get('name', node_id),
                    "type": node_type,
                    "file": node_data.get('file', 'unknown')
                })

        return orphans

    async def find_missing_relationships(self, graph: nx.DiGraph) -> List[Dict]:
        """
        Find likely missing relationships using heuristics.

        Args:
            graph: Knowledge graph

        Returns:
            List of suspicious patterns
        """
        issues = []

        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            node_type = node_data.get('type')

            # Check type-specific patterns
            if node_type == 'CONTROLLER':
                issues.extend(self._check_controller_patterns(graph, node_id, node_data))

            elif node_type == 'CONTROLLER_METHOD':
                issues.extend(self._check_controller_method_patterns(graph, node_id, node_data))

            elif node_type == 'SERVICE':
                issues.extend(self._check_service_patterns(graph, node_id, node_data))

            elif node_type == 'SERVICE_METHOD':
                issues.extend(self._check_service_method_patterns(graph, node_id, node_data))

            elif node_type == 'MAPPER':
                issues.extend(self._check_mapper_patterns(graph, node_id, node_data))

            elif node_type == 'MAPPER_METHOD':
                issues.extend(self._check_mapper_method_patterns(graph, node_id, node_data))

            elif node_type == 'JSP':
                issues.extend(self._check_jsp_patterns(graph, node_id, node_data))

        return issues

    def _check_controller_method_patterns(
        self,
        graph: nx.DiGraph,
        node_id: str,
        node_data: Dict
    ) -> List[Dict]:
        """Check CONTROLLER_METHOD node patterns."""
        issues = []

        # Check if controller method has no service calls
        successors = list(graph.successors(node_id))
        service_calls = [s for s in successors if graph.nodes[s].get('type') in ['SERVICE_METHOD', 'SERVICE']]

        if not service_calls:
            issues.append({
                "type": "orphan_controller",
                "severity": "medium",
                "node_id": node_id,
                "node_name": node_data.get('name', node_id),
                "message": f"Controller method '{node_data.get('name')}' has no service calls",
                "suggestion": "Verify if controller directly returns static content or if service call is missing"
            })

        return issues

    def _check_service_method_patterns(
        self,
        graph: nx.DiGraph,
        node_id: str,
        node_data: Dict
    ) -> List[Dict]:
        """Check SERVICE_METHOD node patterns."""
        issues = []

        # Check if service method has no mapper calls
        successors = list(graph.successors(node_id))
        mapper_calls = [s for s in successors if graph.nodes[s].get('type') in ['MAPPER_METHOD', 'MAPPER']]

        if not mapper_calls:
            issues.append({
                "type": "orphan_service",
                "severity": "medium",
                "node_id": node_id,
                "node_name": node_data.get('name', node_id),
                "message": f"Service method '{node_data.get('name')}' has no mapper calls",
                "suggestion": "Verify if service calls external API or if mapper relationship is missing"
            })

        return issues

    def _check_mapper_method_patterns(
        self,
        graph: nx.DiGraph,
        node_id: str,
        node_data: Dict
    ) -> List[Dict]:
        """Check MAPPER_METHOD node patterns."""
        issues = []

        # Check if mapper method is never called
        predecessors = list(graph.predecessors(node_id))
        if not predecessors:
            issues.append({
                "type": "orphan_mapper",
                "severity": "low",
                "node_id": node_id,
                "node_name": node_data.get('name', node_id),
                "message": f"Mapper method '{node_data.get('name')}' is not called by any service",
                "suggestion": "Possible legacy code or missing service relationship"
            })

        # Check if mapper method has no SQL
        successors = list(graph.successors(node_id))
        sql_statements = [s for s in successors if graph.nodes[s].get('type') == 'SQL']

        if not sql_statements:
            issues.append({
                "type": "no_sql",
                "severity": "high",
                "node_id": node_id,
                "node_name": node_data.get('name', node_id),
                "message": f"Mapper method '{node_data.get('name')}' has no SQL statement",
                "suggestion": "Check if using annotations (@Select, @Insert) or if SQL is missing from analysis"
            })

        return issues

    def _check_controller_patterns(
        self,
        graph: nx.DiGraph,
        node_id: str,
        node_data: Dict
    ) -> List[Dict]:
        """Check CONTROLLER node patterns."""
        # Controllers are classes, methods are separate nodes
        return []

    def _check_service_patterns(
        self,
        graph: nx.DiGraph,
        node_id: str,
        node_data: Dict
    ) -> List[Dict]:
        """Check SERVICE node patterns."""
        # Services are classes, methods are separate nodes
        return []

    def _check_mapper_patterns(
        self,
        graph: nx.DiGraph,
        node_id: str,
        node_data: Dict
    ) -> List[Dict]:
        """Check MAPPER node patterns."""
        # Mappers are classes/interfaces, methods are separate nodes
        return []

    def _check_jsp_patterns(
        self,
        graph: nx.DiGraph,
        node_id: str,
        node_data: Dict
    ) -> List[Dict]:
        """Check JSP node patterns."""
        issues = []

        # Check if JSP has no outgoing AJAX calls
        successors = list(graph.successors(node_id))
        ajax_calls = [s for s in successors
                     if graph.edges[node_id, s].get('relation') in ['AJAX_CALL', 'CALLS']]

        if not ajax_calls:
            # This might be intentional (static page), so only flag as low severity
            issues.append({
                "type": "missing_ajax",
                "severity": "low",
                "node_id": node_id,
                "node_name": node_data.get('name', node_id),
                "message": f"JSP '{node_data.get('name')}' has no AJAX calls detected",
                "suggestion": "Verify if page is static or if AJAX calls are missing from analysis"
            })

        return issues

    async def verify_suspicious_patterns(
        self,
        graph: nx.DiGraph,
        issues: List[Dict]
    ) -> List[Dict]:
        """
        Use LLM to verify suspicious patterns.

        Args:
            graph: Knowledge graph
            issues: List of suspicious patterns from find_missing_relationships

        Returns:
            Enhanced issues list with LLM verification results
        """
        verified_issues = []

        for issue in issues:
            issue_type = issue.get('type')
            query_template = self.VERIFICATION_QUERIES.get(issue_type)

            if not query_template:
                # No verification query for this type, keep as-is
                verified_issues.append(issue)
                continue

            # Get node data
            node_id = issue.get('node_id')
            if node_id not in graph.nodes:
                verified_issues.append(issue)
                continue

            node_data = graph.nodes[node_id]

            # Build verification context
            context = {
                "node_type": node_data.get('type'),
                "node_name": node_data.get('name'),
                "file": node_data.get('file'),
                "in_degree": graph.in_degree(node_id),
                "out_degree": graph.out_degree(node_id),
                "predecessors": [graph.nodes[p].get('name', p) for p in graph.predecessors(node_id)],
                "successors": [graph.nodes[s].get('name', s) for s in graph.successors(node_id)]
            }

            # Query LLM
            try:
                source_code = node_data.get('code', f"Node: {node_data.get('name')}")
                result = await self.llm.verify_relationship(
                    source_code=source_code,
                    target_code=query_template['question'],
                    relationship_type="COMPLETENESS_CHECK",
                    context=context
                )

                # Add LLM verification to issue
                issue['llm_verified'] = result.get('match', False)
                issue['llm_confidence'] = result.get('confidence', 0.0)
                issue['llm_reasoning'] = result.get('reasoning', '')

            except Exception as e:
                logger.error(f"LLM verification failed for {node_id}: {e}")
                issue['llm_verified'] = False
                issue['llm_error'] = str(e)

            verified_issues.append(issue)

        return verified_issues

    async def scan_graph(self, graph: nx.DiGraph) -> Dict:
        """
        Comprehensive graph completeness scan.

        Args:
            graph: Knowledge graph

        Returns:
            Scan results dictionary
        """
        logger.info("Starting completeness scan...")

        # Find orphan nodes
        orphans = await self.find_orphan_nodes(graph)

        # Find missing relationships
        missing_relationships = await self.find_missing_relationships(graph)

        # Verify suspicious patterns with LLM (optional)
        if missing_relationships:
            verified_issues = await self.verify_suspicious_patterns(
                graph, missing_relationships
            )
        else:
            verified_issues = []

        # Summary statistics
        total_nodes = graph.number_of_nodes()
        total_edges = graph.number_of_edges()
        total_orphans = sum(len(nodes) for nodes in orphans.values())
        total_issues = len(verified_issues)

        results = {
            "summary": {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "total_orphans": total_orphans,
                "total_issues": total_issues,
                "completeness_score": self._calculate_completeness_score(
                    total_nodes, total_edges, total_orphans, total_issues
                )
            },
            "orphans": orphans,
            "issues": verified_issues
        }

        logger.info(f"Completeness scan complete: {total_issues} issues, {total_orphans} orphans")

        return results

    def _calculate_completeness_score(
        self,
        total_nodes: int,
        total_edges: int,
        total_orphans: int,
        total_issues: int
    ) -> float:
        """
        Calculate graph completeness score (0.0 - 1.0).

        Higher score = more complete graph

        Args:
            total_nodes: Total number of nodes
            total_edges: Total number of edges
            total_orphans: Number of orphan nodes
            total_issues: Number of issues found

        Returns:
            Completeness score between 0.0 and 1.0
        """
        if total_nodes == 0:
            return 0.0

        # Ideal: high edge-to-node ratio, few orphans, few issues
        edge_ratio = min(total_edges / (total_nodes * 2), 1.0)  # Normalize to 0-1
        orphan_penalty = total_orphans / total_nodes
        issue_penalty = total_issues / total_nodes

        # Weighted score
        score = (
            edge_ratio * 0.5 +           # 50% weight on connectivity
            (1 - orphan_penalty) * 0.3 +  # 30% weight on no orphans
            (1 - issue_penalty) * 0.2     # 20% weight on no issues
        )

        return max(0.0, min(1.0, score))

    def __repr__(self) -> str:
        """String representation."""
        return f"CompletenessScanner(llm_engine={self.llm})"
