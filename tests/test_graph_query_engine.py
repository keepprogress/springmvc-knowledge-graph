#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GraphQueryEngine

Tests graph querying capabilities including path finding,
dependency analysis, and impact analysis
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

from mcp_server.tools.graph_query_engine import GraphQueryEngine


def create_test_graph():
    """Create a test knowledge graph with SpringMVC structure."""
    G = nx.DiGraph()

    # Layer 1: JSPs
    G.add_node("user_list.jsp", type="JSP", name="user_list.jsp", file="user_list.jsp")
    G.add_node("user_edit.jsp", type="JSP", name="user_edit.jsp", file="user_edit.jsp")

    # Layer 2: Controllers
    G.add_node("UserController", type="CONTROLLER", name="UserController", file="UserController.java")
    G.add_node("UserController.listUsers", type="CONTROLLER_METHOD", name="listUsers", file="UserController.java")
    G.add_node("UserController.saveUser", type="CONTROLLER_METHOD", name="saveUser", file="UserController.java")

    # Layer 3: Services
    G.add_node("UserService", type="SERVICE", name="UserService", file="UserService.java")
    G.add_node("UserService.getAllUsers", type="SERVICE_METHOD", name="getAllUsers", file="UserService.java")
    G.add_node("UserService.updateUser", type="SERVICE_METHOD", name="updateUser", file="UserService.java")

    # Layer 4: Mappers
    G.add_node("UserMapper", type="MAPPER", name="UserMapper", file="UserMapper.java")
    G.add_node("UserMapper.selectAll", type="MAPPER_METHOD", name="selectAll", file="UserMapper.java")
    G.add_node("UserMapper.update", type="MAPPER_METHOD", name="update", file="UserMapper.java")

    # Layer 5: SQL
    G.add_node("SELECT_ALL_USERS", type="SQL", name="SELECT * FROM users", file="UserMapper.xml")
    G.add_node("UPDATE_USER", type="SQL", name="UPDATE users SET...", file="UserMapper.xml")

    # Layer 6: Tables
    G.add_node("USERS_TABLE", type="TABLE", name="users", file="database")

    # Add edges with relations
    # JSP -> Controller
    G.add_edge("user_list.jsp", "UserController.listUsers", relation="AJAX_CALL", confidence=0.95)
    G.add_edge("user_edit.jsp", "UserController.saveUser", relation="AJAX_CALL", confidence=0.95)

    # Controller -> Service
    G.add_edge("UserController.listUsers", "UserService.getAllUsers", relation="CALLS", confidence=1.0)
    G.add_edge("UserController.saveUser", "UserService.updateUser", relation="CALLS", confidence=1.0)

    # Service -> Mapper
    G.add_edge("UserService.getAllUsers", "UserMapper.selectAll", relation="CALLS", confidence=1.0)
    G.add_edge("UserService.updateUser", "UserMapper.update", relation="CALLS", confidence=1.0)

    # Mapper -> SQL
    G.add_edge("UserMapper.selectAll", "SELECT_ALL_USERS", relation="EXECUTES", confidence=1.0)
    G.add_edge("UserMapper.update", "UPDATE_USER", relation="EXECUTES", confidence=1.0)

    # SQL -> Table
    G.add_edge("SELECT_ALL_USERS", "USERS_TABLE", relation="QUERIES", confidence=1.0)
    G.add_edge("UPDATE_USER", "USERS_TABLE", relation="MODIFIES", confidence=1.0)

    # Add orphan node for testing
    G.add_node("OrphanController.orphan", type="CONTROLLER_METHOD", name="orphan", file="OrphanController.java")

    return G


def test_graph_query_engine():
    """Test GraphQueryEngine functionality"""
    print("=" * 70)
    print("Testing GraphQueryEngine")
    print("=" * 70)

    try:
        # Create test graph
        graph = create_test_graph()
        print(f"\nTest graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # Initialize query engine
        engine = GraphQueryEngine(graph)
        print(f"Engine initialized: {engine}")

        # Test 1: Find path
        print("\n[1] Testing path finding...")

        path = engine.find_path("user_list.jsp", "USERS_TABLE")
        assert path is not None, "Should find path from JSP to Table"
        assert len(path) == 6, f"Path should have 6 nodes, got {len(path)}"
        print(f"  [OK] Found path: {' -> '.join([p.split('.')[-1] if '.' in p else p for p in path])}")

        # Test 2: Find all paths
        print("\n[2] Testing find all paths...")

        all_paths = engine.find_all_paths("user_list.jsp", "USERS_TABLE", max_length=10)
        assert len(all_paths) >= 1, "Should find at least one path"
        print(f"  [OK] Found {len(all_paths)} path(s)")

        # Test 3: Find shortest path with weight
        print("\n[3] Testing shortest path with weight...")

        path, weight = engine.find_shortest_path("user_list.jsp", "USERS_TABLE", weight="confidence")
        assert path is not None, "Should find weighted path"
        print(f"  [OK] Shortest weighted path: {len(path)} nodes, weight: {weight:.2f}")

        # Test 4: Relation-filtered path
        print("\n[4] Testing relation-filtered path...")

        ajax_path = engine.find_path("user_list.jsp", "UserController.listUsers", relation_types=["AJAX_CALL"])
        assert ajax_path is not None, "Should find AJAX path"
        print(f"  [OK] AJAX path: {' -> '.join(ajax_path)}")

        # Test 5: Get dependencies
        print("\n[5] Testing dependency analysis...")

        deps = engine.get_dependencies("UserMapper.selectAll", max_depth=3)
        assert deps["total_dependencies"] >= 2, "Should have dependencies"
        print(f"  [OK] Dependencies of UserMapper.selectAll:")
        print(f"    Total: {deps['total_dependencies']}")
        print(f"    Nodes: {', '.join([d.split('.')[-1] for d in deps['dependencies'][:3]])}")

        # Test 6: Get dependents
        print("\n[6] Testing dependent analysis...")

        dependents = engine.get_dependents("UserService.getAllUsers", max_depth=2)
        assert dependents["total_dependents"] >= 1, "Should have dependents"
        print(f"  [OK] Dependents of UserService.getAllUsers:")
        print(f"    Total: {dependents['total_dependents']}")

        # Test 7: Dependency chain
        print("\n[7] Testing dependency chain...")

        chains = engine.get_dependency_chain("user_list.jsp")
        assert len(chains) >= 1, "Should find at least one chain"
        print(f"  [OK] Found {len(chains)} dependency chain(s)")
        if chains:
            chain_str = ' -> '.join([n.split('.')[-1] if '.' in n else n for n in chains[0][:5]])
            print(f"    Chain 1: {chain_str}...")

        # Test 8: Impact analysis
        print("\n[8] Testing impact analysis...")

        impact = engine.analyze_impact("UserService.updateUser")
        assert "total_affected" in impact, "Should have impact data"
        assert impact["total_affected"] >= 2, "Should affect multiple nodes"
        print(f"  [OK] Impact of changing UserService.updateUser:")
        print(f"    Total affected: {impact['total_affected']}")
        print(f"    Impact score: {impact['impact_score']}")
        print(f"    Severity: {impact['severity']}")

        # Test 9: Critical nodes
        print("\n[9] Testing critical node detection...")

        critical = engine.find_critical_nodes(top_n=5)
        assert len(critical) >= 1, "Should find critical nodes"
        print(f"  [OK] Top {len(critical)} critical nodes:")
        for i, node in enumerate(critical[:3], 1):
            print(f"    {i}. {node['name']} ({node['type']}): score={node['criticality_score']:.2f}")

        # Test 10: Node metrics
        print("\n[10] Testing node metrics...")

        metrics = engine.get_node_metrics("UserController.listUsers")
        assert "degree" in metrics, "Should have degree metrics"
        assert metrics["degree"]["total"] >= 2, "Should have connections"
        print(f"  [OK] Metrics for UserController.listUsers:")
        print(f"    In-degree: {metrics['degree']['in']}")
        print(f"    Out-degree: {metrics['degree']['out']}")
        print(f"    Betweenness: {metrics['centrality']['betweenness']}")

        # Test 11: Graph statistics
        print("\n[11] Testing graph statistics...")

        stats = engine.get_graph_statistics()
        assert stats["nodes"]["total"] == graph.number_of_nodes()
        assert stats["edges"]["total"] == graph.number_of_edges()
        print(f"  [OK] Graph statistics:")
        print(f"    Nodes: {stats['nodes']['total']}")
        print(f"    Edges: {stats['edges']['total']}")
        print(f"    Density: {stats['connectivity']['density']}")
        print(f"    Avg degree: {stats['complexity']['avg_degree']}")

        # Test 12: No path scenario
        print("\n[12] Testing no path scenario...")

        no_path = engine.find_path("OrphanController.orphan", "USERS_TABLE")
        assert no_path is None, "Should return None for no path"
        print(f"  [OK] Correctly returns None for orphan node")

        # Test 13: Node not found
        print("\n[13] Testing node not found...")

        metrics_not_found = engine.get_node_metrics("NonExistentNode")
        assert "error" in metrics_not_found, "Should return error"
        print(f"  [OK] Correctly handles non-existent node")

        # Test result
        print("\n" + "=" * 70)
        print("[OK] GraphQueryEngine test PASSED")
        print("=" * 70)

        print("\n📊 Query Engine Capabilities Verified:")
        print("  ✓ Path finding (simple, all, shortest, weighted)")
        print("  ✓ Relation-filtered queries")
        print("  ✓ Dependency analysis (upstream, downstream)")
        print("  ✓ Dependency chains")
        print("  ✓ Impact analysis with severity")
        print("  ✓ Critical node detection")
        print("  ✓ Node metrics and centrality")
        print("  ✓ Graph statistics")
        print("  ✓ Error handling")

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
    success = test_graph_query_engine()
    sys.exit(0 if success else 1)
