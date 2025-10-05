#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GraphMerger

Tests graph merging with conflict detection and resolution.
"""

import sys
from pathlib import Path
import networkx as nx

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except Exception:
        pass

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.tools.graph_merger import (
    GraphMerger,
    ConflictType,
    VerificationSource
)


def create_test_code_graph():
    """Create a test code-based graph."""
    G = nx.DiGraph()

    # Add nodes
    G.add_node("A", type="JSP", name="page.jsp")
    G.add_node("B", type="CONTROLLER", name="Controller")
    G.add_node("C", type="SERVICE", name="Service")
    G.add_node("D", type="MAPPER", name="Mapper")
    G.add_node("E", type="TABLE", name="users")

    # Add edges with high confidence (code-based)
    # Use 0.85 for A->B so agreement bonus can show (0.85 + 0.1 = 0.95)
    G.add_edge("A", "B", relation="AJAX_CALL", confidence=0.85)
    G.add_edge("B", "C", relation="CALLS", confidence=1.0)
    G.add_edge("C", "D", relation="CALLS", confidence=0.95)
    G.add_edge("D", "E", relation="QUERIES", confidence=1.0)

    return G


def create_test_llm_graph_agreeing():
    """Create a test LLM graph that agrees with code graph."""
    G = nx.DiGraph()

    # Add nodes (same as code graph)
    G.add_node("A", type="JSP", name="page.jsp")
    G.add_node("B", type="CONTROLLER", name="Controller")
    G.add_node("C", type="SERVICE", name="Service")
    G.add_node("D", type="MAPPER", name="Mapper")
    G.add_node("E", type="TABLE", name="users")

    # Add edges with LLM confidence (same relations as code)
    G.add_edge("A", "B", relation="AJAX_CALL", confidence=0.9)
    G.add_edge("B", "C", relation="CALLS", confidence=0.85)
    G.add_edge("C", "D", relation="CALLS", confidence=0.8)

    # LLM found an additional edge
    G.add_edge("D", "E", relation="QUERIES", confidence=0.75)

    return G


def create_test_llm_graph_with_conflicts():
    """Create a test LLM graph with conflicts."""
    G = nx.DiGraph()

    # Add nodes
    G.add_node("A", type="JSP", name="page.jsp")
    G.add_node("B", type="CONTROLLER", name="Controller")
    G.add_node("C", type="SERVICE", name="Service")
    G.add_node("D", type="MAPPER", name="Mapper")
    G.add_node("E", type="TABLE", name="users")
    G.add_node("F", type="TABLE", name="orders")  # New node

    # Relation mismatch: A->B has different relation
    G.add_edge("A", "B", relation="FORM_SUBMIT", confidence=0.7)  # Conflict!

    # Agreement
    G.add_edge("B", "C", relation="CALLS", confidence=0.9)

    # Confidence conflict: C->D has very low confidence
    G.add_edge("C", "D", relation="CALLS", confidence=0.4)  # Low confidence

    # LLM-only edge
    G.add_edge("C", "F", relation="QUERIES", confidence=0.8)

    return G


def create_direction_conflict_graphs():
    """Create graphs with direction conflicts."""
    G1 = nx.DiGraph()
    G1.add_node("A", type="SERVICE")
    G1.add_node("B", type="MAPPER")
    G1.add_edge("A", "B", relation="CALLS", confidence=1.0)

    G2 = nx.DiGraph()
    G2.add_node("A", type="SERVICE")
    G2.add_node("B", type="MAPPER")
    G2.add_edge("B", "A", relation="CALLS", confidence=0.8)  # Reverse direction!

    return G1, G2


def test_graph_merger():
    """Test GraphMerger functionality"""
    print("=" * 70)
    print("Testing GraphMerger")
    print("=" * 70)

    try:
        # Test 1: Merge graphs with full agreement
        print("\n[1] Testing merge with full agreement...")

        code_graph = create_test_code_graph()
        llm_graph = create_test_llm_graph_agreeing()

        merger = GraphMerger()
        merged, report = merger.merge_graphs(code_graph, llm_graph)

        assert merged.number_of_nodes() == 5, "Should have 5 nodes"
        assert merged.number_of_edges() == 4, "Should have 4 edges"
        assert report["statistics"]["conflicts_detected"] == 0, "Should have no conflicts"

        # Check agreement bonus (0.85 code + 0.9 llm -> max(0.85, 0.9) + 0.1 = 1.0)
        edge_data = merged.get_edge_data("A", "B")
        assert edge_data["confidence"] == 1.0, f"Agreement should boost confidence to 1.0, got {edge_data['confidence']}"
        assert edge_data["verification_source"] == "code+llm", "Should be verified by both"

        print(f"  [OK] Merged {merged.number_of_nodes()} nodes, {merged.number_of_edges()} edges")
        print(f"  [OK] Agreement bonus applied: conf={edge_data['confidence']:.2f}")
        print(f"  [OK] No conflicts detected")

        # Test 2: Merge graphs with conflicts
        print("\n[2] Testing merge with conflicts...")

        code_graph = create_test_code_graph()
        llm_graph = create_test_llm_graph_with_conflicts()

        merger = GraphMerger()
        merged, report = merger.merge_graphs(code_graph, llm_graph)

        assert merged.number_of_nodes() == 6, "Should have 6 nodes (including F)"
        assert report["statistics"]["conflicts_detected"] > 0, "Should detect conflicts"

        # Check relation mismatch resolution (code should win)
        edge_data = merged.get_edge_data("A", "B")
        assert edge_data["relation"] == "AJAX_CALL", "Code relation should win"
        assert edge_data["had_conflicts"] == True, "Should mark conflicts"

        print(f"  [OK] Merged {merged.number_of_nodes()} nodes, {merged.number_of_edges()} edges")
        print(f"  [OK] Conflicts detected: {report['statistics']['conflicts_detected']}")
        print(f"  [OK] Relation conflict resolved: code wins ({edge_data['relation']})")

        # Test 3: LLM-only edge penalty
        print("\n[3] Testing LLM-only edge penalty...")

        code_graph = create_test_code_graph()
        llm_graph = create_test_llm_graph_with_conflicts()

        merger = GraphMerger(llm_penalty=0.9)
        merged, report = merger.merge_graphs(code_graph, llm_graph)

        # Check C->F edge (LLM-only)
        edge_data = merged.get_edge_data("C", "F")
        assert edge_data is not None, "LLM-only edge should be added"
        assert edge_data["confidence"] < 0.8, "LLM confidence should be penalized"
        assert edge_data["verification_source"] == "llm", "Should be marked as LLM-only"

        print(f"  [OK] LLM-only edge added with penalty: conf={edge_data['confidence']:.2f}")
        print(f"  [OK] Edge by source: {report['statistics']['edges_by_source']}")

        # Test 4: Direction conflict detection
        print("\n[4] Testing direction conflict detection...")

        g1, g2 = create_direction_conflict_graphs()
        merger = GraphMerger()

        direction_conflicts = merger.detect_direction_conflicts(g1, g2)
        assert len(direction_conflicts) == 1, "Should detect 1 direction conflict"
        assert direction_conflicts[0]["type"] == ConflictType.DIRECTION_CONFLICT

        print(f"  [OK] Direction conflict detected: {direction_conflicts[0]['graph1_edge']} vs {direction_conflicts[0]['graph2_edge']}")

        # Test 5: Code-only edges
        print("\n[5] Testing code-only edges...")

        code_graph = create_test_code_graph()
        llm_graph = nx.DiGraph()  # Empty LLM graph
        llm_graph.add_node("A", type="JSP")
        llm_graph.add_node("B", type="CONTROLLER")
        # No edges in LLM graph

        merger = GraphMerger()
        merged, report = merger.merge_graphs(code_graph, llm_graph)

        assert merged.number_of_edges() == 4, "Should have all code edges"
        assert report["statistics"]["edges_by_source"]["code"] == 4, "All edges should be code-only"

        print(f"  [OK] Code-only edges: {report['statistics']['edges_by_source']['code']}")

        # Test 6: Confidence conflict resolution
        print("\n[6] Testing confidence conflict resolution...")

        code_graph = nx.DiGraph()
        code_graph.add_node("A", type="JSP")
        code_graph.add_node("B", type="CONTROLLER")
        code_graph.add_edge("A", "B", relation="CALLS", confidence=0.95)

        llm_graph = nx.DiGraph()
        llm_graph.add_node("A", type="JSP")
        llm_graph.add_node("B", type="CONTROLLER")
        llm_graph.add_edge("A", "B", relation="CALLS", confidence=0.5)  # Low confidence

        merger = GraphMerger()  # Default: highest confidence wins
        merged, report = merger.merge_graphs(code_graph, llm_graph)

        edge_data = merged.get_edge_data("A", "B")
        # Should detect confidence conflict (diff > 0.3)
        assert report["statistics"]["conflicts_detected"] > 0, "Should detect confidence conflict"
        # Should use highest confidence for conflicts
        assert edge_data["confidence"] == 0.95, "Should use highest confidence"

        print(f"  [OK] Confidence conflict resolved: {edge_data['confidence']}")
        print(f"  [OK] Conflicts by type: {report['statistics']['conflicts_by_type']}")

        # Test 7: Custom resolution rules
        print("\n[7] Testing custom resolution rules...")

        merger_custom = GraphMerger(
            resolution_rules={
                ConflictType.RELATION_MISMATCH: "llm",  # LLM wins (non-default)
                ConflictType.CONFIDENCE_CONFLICT: "llm"
            }
        )

        code_graph = nx.DiGraph()
        code_graph.add_node("A", type="JSP")
        code_graph.add_node("B", type="CONTROLLER")
        code_graph.add_edge("A", "B", relation="AJAX_CALL", confidence=1.0)

        llm_graph = nx.DiGraph()
        llm_graph.add_node("A", type="JSP")
        llm_graph.add_node("B", type="CONTROLLER")
        llm_graph.add_edge("A", "B", relation="FORM_SUBMIT", confidence=0.7)

        merged, report = merger_custom.merge_graphs(code_graph, llm_graph)

        edge_data = merged.get_edge_data("A", "B")
        assert edge_data["relation"] == "FORM_SUBMIT", "LLM relation should win with custom rule"

        print(f"  [OK] Custom rule applied: LLM relation wins ({edge_data['relation']})")

        # Test 8: Merge report structure
        print("\n[8] Testing merge report structure...")

        code_graph = create_test_code_graph()
        llm_graph = create_test_llm_graph_agreeing()

        merger = GraphMerger()
        merged, report = merger.merge_graphs(code_graph, llm_graph)

        assert "input_graphs" in report, "Report should have input_graphs"
        assert "merged_graph" in report, "Report should have merged_graph"
        assert "statistics" in report, "Report should have statistics"
        assert "conflicts" in report, "Report should have conflicts"
        assert "configuration" in report, "Report should have configuration"

        print(f"  [OK] Report structure valid")
        print(f"  [OK] Input: code={report['input_graphs']['code']['edges']}, llm={report['input_graphs']['llm']['edges']}")
        print(f"  [OK] Merged: {report['merged_graph']['edges']} edges")

        # Test 9: Agreement bonus calculation
        print("\n[9] Testing agreement bonus calculation...")

        merger = GraphMerger(agreement_bonus=0.2)  # Custom bonus

        code_graph = nx.DiGraph()
        code_graph.add_node("A", type="JSP")
        code_graph.add_node("B", type="CONTROLLER")
        code_graph.add_edge("A", "B", relation="CALLS", confidence=0.8)

        llm_graph = nx.DiGraph()
        llm_graph.add_node("A", type="JSP")
        llm_graph.add_node("B", type="CONTROLLER")
        llm_graph.add_edge("A", "B", relation="CALLS", confidence=0.75)

        merged, report = merger.merge_graphs(code_graph, llm_graph)

        edge_data = merged.get_edge_data("A", "B")
        expected_conf = 0.8 + 0.2  # max(0.8, 0.75) + 0.2
        assert edge_data["confidence"] == expected_conf, f"Agreement bonus should be {expected_conf}"

        print(f"  [OK] Agreement bonus: {edge_data['confidence']:.2f} (expected {expected_conf})")

        # Test 10: Direction conflict in main merge
        print("\n[10] Testing direction conflict in main merge...")

        g1, g2 = create_direction_conflict_graphs()
        merger = GraphMerger()  # Default: code wins

        merged, report = merger.merge_graphs(g1, g2)

        # Should have only 1 edge (A->B from code), not both A->B and B->A
        assert merged.number_of_edges() == 1, f"Should have 1 edge, got {merged.number_of_edges()}"
        assert merged.has_edge("A", "B"), "Should have code direction A->B"
        assert not merged.has_edge("B", "A"), "Should NOT have reverse LLM direction B->A"
        assert report["statistics"]["conflicts_detected"] == 1, "Should detect 1 direction conflict"
        assert "direction_conflict" in report["statistics"]["conflicts_by_type"], "Should log direction conflict"

        print(f"  [OK] Direction conflict detected and resolved in main merge")
        print(f"  [OK] Only code direction preserved: A->B")
        print(f"  [OK] Conflicts: {report['statistics']['conflicts_by_type']}")

        # Test 11: Edge attribute merging
        print("\n[11] Testing edge attribute merging...")

        code_graph = nx.DiGraph()
        code_graph.add_node("A", type="JSP")
        code_graph.add_node("B", type="CONTROLLER")
        code_graph.add_edge("A", "B", relation="CALLS", confidence=0.9, file="A.jsp", line=10)

        llm_graph = nx.DiGraph()
        llm_graph.add_node("A", type="JSP")
        llm_graph.add_node("B", type="CONTROLLER")
        llm_graph.add_edge("A", "B", relation="CALLS", confidence=0.85, reasoning="LLM analysis")

        merger = GraphMerger()
        merged, report = merger.merge_graphs(code_graph, llm_graph)

        edge_data = merged.get_edge_data("A", "B")
        assert "file" in edge_data, "Should preserve code attributes"
        assert "line" in edge_data, "Should preserve code attributes"
        assert edge_data["file"] == "A.jsp", "Code attributes should be preserved"

        print(f"  [OK] Edge attributes merged: {list(edge_data.keys())}")

        # Test result
        print("\n" + "=" * 70)
        print("[OK] GraphMerger test PASSED")
        print("=" * 70)

        print("\n📊 Graph Merger Capabilities Verified:")
        print("  ✓ Full agreement merging with confidence bonus")
        print("  ✓ Conflict detection (relation, confidence)")
        print("  ✓ Conflict resolution with configurable rules")
        print("  ✓ LLM-only edge penalty")
        print("  ✓ Code-only edge preservation")
        print("  ✓ Direction conflict detection (utility method)")
        print("  ✓ Direction conflict detection (integrated in merge)")
        print("  ✓ Verification source tracking")
        print("  ✓ Comprehensive merge reporting")
        print("  ✓ Custom resolution rules")
        print("  ✓ Edge attribute merging")

        return True

    except AssertionError as e:
        print(f"\n[ERROR] Assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_graph_merger()
    sys.exit(0 if success else 1)
