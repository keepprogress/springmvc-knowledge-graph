#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Merger for Knowledge Graph Construction

Merges code-based and LLM-verified graphs with conflict detection and resolution.
Implements confidence scoring and verification tracking.
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional, Any, Set
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts between graphs."""
    RELATION_MISMATCH = "relation_mismatch"  # Same edge, different relation types
    DIRECTION_CONFLICT = "direction_conflict"  # A→B vs B→A
    CONFIDENCE_CONFLICT = "confidence_conflict"  # Different confidence levels


class VerificationSource(Enum):
    """Source of edge verification."""
    CODE_ONLY = "code"  # Only from code-based analysis
    LLM_ONLY = "llm"  # Only from LLM verification
    CODE_AND_LLM = "code+llm"  # Verified by both


class GraphMerger:
    """
    Merges multiple knowledge graphs with conflict resolution.

    Features:
    - Conflict detection (relation mismatch, direction, confidence)
    - Configurable resolution rules
    - Combined confidence scoring with bonuses/penalties
    - Verification source tracking
    """

    def __init__(
        self,
        resolution_rules: Optional[Dict[str, Any]] = None,
        agreement_bonus: float = 0.1,
        llm_penalty: float = 0.9
    ):
        """
        Initialize Graph Merger.

        Args:
            resolution_rules: Custom resolution rules (defaults to code-based priority)
            agreement_bonus: Confidence bonus when both graphs agree (default: 0.1)
            llm_penalty: Confidence multiplier for LLM-only edges (default: 0.9)
        """
        # Default resolution rules: code-based always wins for conflicts
        self.resolution_rules = resolution_rules or {
            ConflictType.RELATION_MISMATCH: "code",  # Code-based relation wins
            ConflictType.DIRECTION_CONFLICT: "code",  # Code-based direction wins
            ConflictType.CONFIDENCE_CONFLICT: "highest"  # Highest confidence wins
        }

        self.agreement_bonus = agreement_bonus
        self.llm_penalty = llm_penalty

        # Statistics
        self.merge_stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "conflicts_detected": 0,
            "conflicts_by_type": defaultdict(int),
            "edges_by_source": defaultdict(int)
        }

    def merge_graphs(
        self,
        code_graph: nx.DiGraph,
        llm_graph: nx.DiGraph,
        track_sources: bool = True
    ) -> Tuple[nx.DiGraph, Dict[str, Any]]:
        """
        Merge code-based and LLM-verified graphs.

        Args:
            code_graph: Graph from code-based analysis
            llm_graph: Graph from LLM verification
            track_sources: Whether to track verification sources (default: True)

        Returns:
            Tuple of:
                - Merged graph
                - Merge statistics and conflict report
        """
        logger.info(
            f"Merging graphs: code({code_graph.number_of_nodes()} nodes, "
            f"{code_graph.number_of_edges()} edges) + "
            f"llm({llm_graph.number_of_nodes()} nodes, "
            f"{llm_graph.number_of_edges()} edges)"
        )

        # Reset statistics
        self.merge_stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "conflicts_detected": 0,
            "conflicts_by_type": defaultdict(int),
            "edges_by_source": defaultdict(int),
            "conflicts": []
        }

        # Create merged graph
        merged_graph = nx.DiGraph()

        # Step 1: Merge nodes (union)
        self._merge_nodes(merged_graph, code_graph, llm_graph)

        # Step 2: Merge edges with conflict detection and resolution
        self._merge_edges(merged_graph, code_graph, llm_graph, track_sources)

        # Prepare report
        report = self._generate_merge_report(code_graph, llm_graph, merged_graph)

        logger.info(
            f"Merge complete: {merged_graph.number_of_nodes()} nodes, "
            f"{merged_graph.number_of_edges()} edges, "
            f"{self.merge_stats['conflicts_detected']} conflicts"
        )

        return merged_graph, report

    def _merge_nodes(
        self,
        merged_graph: nx.DiGraph,
        code_graph: nx.DiGraph,
        llm_graph: nx.DiGraph
    ):
        """
        Merge nodes from both graphs (union).

        Args:
            merged_graph: Target merged graph
            code_graph: Code-based graph
            llm_graph: LLM-verified graph
        """
        # Add all nodes from code graph
        for node, attrs in code_graph.nodes(data=True):
            merged_graph.add_node(node, **attrs)
            self.merge_stats["nodes_added"] += 1

        # Add nodes from LLM graph (if not already present)
        for node, attrs in llm_graph.nodes(data=True):
            if node not in merged_graph:
                merged_graph.add_node(node, **attrs)
                self.merge_stats["nodes_added"] += 1
            else:
                # Node exists - merge attributes (code-based takes priority)
                existing_attrs = merged_graph.nodes[node]
                for key, value in attrs.items():
                    if key not in existing_attrs:
                        merged_graph.nodes[node][key] = value

    def _merge_edges(
        self,
        merged_graph: nx.DiGraph,
        code_graph: nx.DiGraph,
        llm_graph: nx.DiGraph,
        track_sources: bool
    ):
        """
        Merge edges with conflict detection and resolution.

        Args:
            merged_graph: Target merged graph
            code_graph: Code-based graph
            llm_graph: LLM-verified graph
            track_sources: Whether to track verification sources
        """
        # Build edge maps for efficient lookup
        code_edges = self._build_edge_map(code_graph)
        llm_edges = self._build_edge_map(llm_graph)

        # Track edges to skip due to direction conflicts
        edges_to_skip = set()

        # Detect direction conflicts (A→B in code vs B→A in LLM)
        for code_edge_key in code_edges.keys():
            source, target = code_edge_key
            reverse_key = (target, source)

            # Check if reverse edge exists in LLM graph (and forward doesn't)
            if reverse_key in llm_edges and code_edge_key not in llm_edges:
                # Direction conflict detected!
                conflict = {
                    "type": ConflictType.DIRECTION_CONFLICT,
                    "edge": f"{source} -> {target}",
                    "reverse_edge": f"{target} -> {source}",
                    "code_direction": f"{source} -> {target}",
                    "llm_direction": f"{target} -> {source}"
                }
                self.merge_stats["conflicts"].append(conflict)
                self.merge_stats["conflicts_by_type"][ConflictType.DIRECTION_CONFLICT.value] += 1
                self.merge_stats["conflicts_detected"] += 1

                logger.debug(
                    f"Direction conflict: code has {source}->{target}, "
                    f"LLM has {target}->{source}"
                )

                # Apply resolution rule (default: code wins)
                rule = self.resolution_rules.get(ConflictType.DIRECTION_CONFLICT, "code")
                if rule == "code":
                    # Skip the reverse LLM edge
                    edges_to_skip.add(reverse_key)
                elif rule == "llm":
                    # Skip the code edge (use LLM direction)
                    edges_to_skip.add(code_edge_key)

        # Get all unique edge keys (source, target)
        all_edge_keys = set(code_edges.keys()) | set(llm_edges.keys())

        for edge_key in all_edge_keys:
            # Skip edges that lost in direction conflict resolution
            if edge_key in edges_to_skip:
                continue

            source, target = edge_key

            code_attrs = code_edges.get(edge_key)
            llm_attrs = llm_edges.get(edge_key)

            # Case 1: Edge exists in both graphs
            if code_attrs is not None and llm_attrs is not None:
                self._handle_edge_in_both_graphs(
                    merged_graph, source, target, code_attrs, llm_attrs, track_sources
                )

            # Case 2: Edge only in code graph
            elif code_attrs is not None:
                self._handle_code_only_edge(
                    merged_graph, source, target, code_attrs, track_sources
                )

            # Case 3: Edge only in LLM graph
            else:
                self._handle_llm_only_edge(
                    merged_graph, source, target, llm_attrs, track_sources
                )

    def _build_edge_map(self, graph: nx.DiGraph) -> Dict[Tuple[str, str], Dict]:
        """
        Build edge map for efficient lookup.

        Args:
            graph: Input graph

        Returns:
            Dict mapping (source, target) to edge attributes
        """
        edge_map = {}
        for source, target, attrs in graph.edges(data=True):
            edge_map[(source, target)] = attrs
        return edge_map

    def _handle_edge_in_both_graphs(
        self,
        merged_graph: nx.DiGraph,
        source: str,
        target: str,
        code_attrs: Dict,
        llm_attrs: Dict,
        track_sources: bool
    ):
        """
        Handle edge that exists in both graphs.

        Checks for conflicts and applies resolution rules.

        Args:
            merged_graph: Target merged graph
            source: Source node
            target: Target node
            code_attrs: Attributes from code graph
            llm_attrs: Attributes from LLM graph
            track_sources: Whether to track verification sources
        """
        # Detect conflicts
        conflicts = self._detect_edge_conflicts(source, target, code_attrs, llm_attrs)

        if conflicts:
            # Apply resolution rules
            resolved_attrs = self._resolve_conflicts(
                source, target, code_attrs, llm_attrs, conflicts
            )
            merged_graph.add_edge(source, target, **resolved_attrs)
        else:
            # No conflicts - agreement!
            # Boost confidence and combine attributes
            combined_confidence = self._calculate_combined_confidence(
                code_attrs.get("confidence", 1.0),
                llm_attrs.get("confidence", 0.7),
                agreement=True
            )

            # Merge attributes (code-based takes priority)
            merged_attrs = dict(code_attrs)
            merged_attrs["confidence"] = combined_confidence

            if track_sources:
                merged_attrs["verification_source"] = VerificationSource.CODE_AND_LLM.value

            merged_graph.add_edge(source, target, **merged_attrs)
            self.merge_stats["edges_by_source"][VerificationSource.CODE_AND_LLM.value] += 1

        self.merge_stats["edges_added"] += 1

    def _handle_code_only_edge(
        self,
        merged_graph: nx.DiGraph,
        source: str,
        target: str,
        attrs: Dict,
        track_sources: bool
    ):
        """
        Handle edge that only exists in code graph.

        Args:
            merged_graph: Target merged graph
            source: Source node
            target: Target node
            attrs: Edge attributes from code graph
            track_sources: Whether to track verification sources
        """
        merged_attrs = dict(attrs)

        if track_sources:
            merged_attrs["verification_source"] = VerificationSource.CODE_ONLY.value

        merged_graph.add_edge(source, target, **merged_attrs)
        self.merge_stats["edges_by_source"][VerificationSource.CODE_ONLY.value] += 1
        self.merge_stats["edges_added"] += 1

    def _handle_llm_only_edge(
        self,
        merged_graph: nx.DiGraph,
        source: str,
        target: str,
        attrs: Dict,
        track_sources: bool
    ):
        """
        Handle edge that only exists in LLM graph.

        Applies LLM penalty to confidence.

        Args:
            merged_graph: Target merged graph
            source: Source node
            target: Target node
            attrs: Edge attributes from LLM graph
            track_sources: Whether to track verification sources
        """
        merged_attrs = dict(attrs)

        # Apply LLM penalty to confidence
        original_confidence = attrs.get("confidence", 0.7)
        penalized_confidence = original_confidence * self.llm_penalty
        merged_attrs["confidence"] = penalized_confidence

        if track_sources:
            merged_attrs["verification_source"] = VerificationSource.LLM_ONLY.value

        merged_graph.add_edge(source, target, **merged_attrs)
        self.merge_stats["edges_by_source"][VerificationSource.LLM_ONLY.value] += 1
        self.merge_stats["edges_added"] += 1

    def _detect_edge_conflicts(
        self,
        source: str,
        target: str,
        code_attrs: Dict,
        llm_attrs: Dict
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between edges from different graphs.

        Args:
            source: Source node
            target: Target node
            code_attrs: Attributes from code graph
            llm_attrs: Attributes from LLM graph

        Returns:
            List of detected conflicts with details
        """
        conflicts = []

        # Check relation mismatch
        code_relation = code_attrs.get("relation")
        llm_relation = llm_attrs.get("relation")

        if code_relation and llm_relation and code_relation != llm_relation:
            conflicts.append({
                "type": ConflictType.RELATION_MISMATCH,
                "edge": f"{source} -> {target}",
                "code_value": code_relation,
                "llm_value": llm_relation
            })
            self.merge_stats["conflicts_by_type"][ConflictType.RELATION_MISMATCH.value] += 1

        # Check confidence conflict (large difference)
        code_confidence = code_attrs.get("confidence", 1.0)
        llm_confidence = llm_attrs.get("confidence", 0.7)

        confidence_diff = abs(code_confidence - llm_confidence)
        if confidence_diff > 0.3:  # Threshold for significant difference
            conflicts.append({
                "type": ConflictType.CONFIDENCE_CONFLICT,
                "edge": f"{source} -> {target}",
                "code_value": code_confidence,
                "llm_value": llm_confidence,
                "difference": confidence_diff
            })
            self.merge_stats["conflicts_by_type"][ConflictType.CONFIDENCE_CONFLICT.value] += 1

        # Update total conflict count
        if conflicts:
            self.merge_stats["conflicts_detected"] += 1
            self.merge_stats["conflicts"].extend(conflicts)

        return conflicts

    def _resolve_conflicts(
        self,
        source: str,
        target: str,
        code_attrs: Dict,
        llm_attrs: Dict,
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve conflicts using resolution rules.

        Args:
            source: Source node
            target: Target node
            code_attrs: Attributes from code graph
            llm_attrs: Attributes from LLM graph
            conflicts: List of detected conflicts

        Returns:
            Resolved edge attributes
        """
        # Start with code-based attributes (default priority)
        resolved_attrs = dict(code_attrs)

        for conflict in conflicts:
            conflict_type = conflict["type"]
            resolution_rule = self.resolution_rules.get(conflict_type)

            if conflict_type == ConflictType.RELATION_MISMATCH:
                if resolution_rule == "code":
                    # Code-based relation wins (already in resolved_attrs)
                    logger.debug(
                        f"Relation conflict on {source}->{target}: "
                        f"code '{conflict['code_value']}' wins over "
                        f"llm '{conflict['llm_value']}'"
                    )
                elif resolution_rule == "llm":
                    resolved_attrs["relation"] = llm_attrs.get("relation")

            elif conflict_type == ConflictType.CONFIDENCE_CONFLICT:
                if resolution_rule == "highest":
                    # Use highest confidence
                    code_conf = conflict["code_value"]
                    llm_conf = conflict["llm_value"]
                    resolved_attrs["confidence"] = max(code_conf, llm_conf)
                elif resolution_rule == "code":
                    # Code confidence wins (already in resolved_attrs)
                    pass
                elif resolution_rule == "llm":
                    resolved_attrs["confidence"] = llm_attrs.get("confidence")

        # Mark as having conflicts
        resolved_attrs["had_conflicts"] = True
        resolved_attrs["verification_source"] = VerificationSource.CODE_AND_LLM.value

        return resolved_attrs

    def _calculate_combined_confidence(
        self,
        code_confidence: float,
        llm_confidence: float,
        agreement: bool
    ) -> float:
        """
        Calculate combined confidence score.

        Args:
            code_confidence: Confidence from code-based analysis
            llm_confidence: Confidence from LLM verification
            agreement: Whether both graphs agree

        Returns:
            Combined confidence score (capped at 1.0)
        """
        if agreement:
            # Agreement bonus: max confidence + bonus
            combined = max(code_confidence, llm_confidence) + self.agreement_bonus
        else:
            # No agreement: average of both
            combined = (code_confidence + llm_confidence) / 2

        # Cap at 1.0
        return min(combined, 1.0)

    def _generate_merge_report(
        self,
        code_graph: nx.DiGraph,
        llm_graph: nx.DiGraph,
        merged_graph: nx.DiGraph
    ) -> Dict[str, Any]:
        """
        Generate comprehensive merge report.

        Args:
            code_graph: Original code-based graph
            llm_graph: Original LLM-verified graph
            merged_graph: Resulting merged graph

        Returns:
            Merge report with statistics and conflicts
        """
        return {
            "input_graphs": {
                "code": {
                    "nodes": code_graph.number_of_nodes(),
                    "edges": code_graph.number_of_edges()
                },
                "llm": {
                    "nodes": llm_graph.number_of_nodes(),
                    "edges": llm_graph.number_of_edges()
                }
            },
            "merged_graph": {
                "nodes": merged_graph.number_of_nodes(),
                "edges": merged_graph.number_of_edges()
            },
            "statistics": {
                "nodes_added": self.merge_stats["nodes_added"],
                "edges_added": self.merge_stats["edges_added"],
                "conflicts_detected": self.merge_stats["conflicts_detected"],
                "conflicts_by_type": dict(self.merge_stats["conflicts_by_type"]),
                "edges_by_source": dict(self.merge_stats["edges_by_source"])
            },
            "conflicts": self.merge_stats["conflicts"],
            "configuration": {
                "resolution_rules": {k.value: v for k, v in self.resolution_rules.items()},
                "agreement_bonus": self.agreement_bonus,
                "llm_penalty": self.llm_penalty
            }
        }

    def detect_direction_conflicts(
        self,
        graph1: nx.DiGraph,
        graph2: nx.DiGraph
    ) -> List[Dict[str, Any]]:
        """
        Detect direction conflicts between two graphs (A→B vs B→A).

        Args:
            graph1: First graph
            graph2: Second graph

        Returns:
            List of direction conflicts
        """
        conflicts = []

        for source, target in graph1.edges():
            # Check if reverse edge exists in graph2
            if graph2.has_edge(target, source) and not graph2.has_edge(source, target):
                conflicts.append({
                    "type": ConflictType.DIRECTION_CONFLICT,
                    "graph1_edge": f"{source} -> {target}",
                    "graph2_edge": f"{target} -> {source}",
                    "nodes": [source, target]
                })

        return conflicts

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"GraphMerger("
            f"rules={self.resolution_rules}, "
            f"agreement_bonus={self.agreement_bonus}, "
            f"llm_penalty={self.llm_penalty})"
        )
