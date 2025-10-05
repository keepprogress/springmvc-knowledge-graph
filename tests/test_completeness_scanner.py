#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test CompletenessScanner

Tests completeness scanning for knowledge graphs
"""

import sys
import asyncio
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

from mcp_server.tools.completeness_scanner import CompletenessScanner


def create_test_graph():
    """Create a test graph with intentional issues."""
    G = nx.DiGraph()

    # Add nodes
    # Controllers
    G.add_node("UserController", type="CONTROLLER", name="UserController", file="UserController.java")
    G.add_node("UserController.getUser", type="CONTROLLER_METHOD", name="getUser", file="UserController.java")
    G.add_node("UserController.listUsers", type="CONTROLLER_METHOD", name="listUsers", file="UserController.java")
    G.add_node("OrphanController.orphan", type="CONTROLLER_METHOD", name="orphanMethod", file="OrphanController.java")

    # Services
    G.add_node("UserService", type="SERVICE", name="UserService", file="UserService.java")
    G.add_node("UserService.getUser", type="SERVICE_METHOD", name="getUser", file="UserService.java")
    G.add_node("OrphanService.orphan", type="SERVICE_METHOD", name="orphanMethod", file="OrphanService.java")

    # Mappers
    G.add_node("UserMapper", type="MAPPER", name="UserMapper", file="UserMapper.java")
    G.add_node("UserMapper.selectById", type="MAPPER_METHOD", name="selectById", file="UserMapper.java")
    G.add_node("OrphanMapper.unused", type="MAPPER_METHOD", name="unusedMethod", file="OrphanMapper.java")
    G.add_node("UserMapper.noSql", type="MAPPER_METHOD", name="noSqlMethod", file="UserMapper.java")

    # SQL
    G.add_node("SELECT_USER", type="SQL", name="SELECT * FROM users WHERE id = ?", file="UserMapper.xml")

    # JSP
    G.add_node("user_list.jsp", type="JSP", name="user_list.jsp", file="user_list.jsp")
    G.add_node("orphan.jsp", type="JSP", name="orphan.jsp", file="orphan.jsp")

    # Orphan node (completely disconnected)
    G.add_node("ORPHAN_NODE", type="UNKNOWN", name="orphan", file="unknown.java")

    # Add edges (relationships)
    # Normal flow: JSP -> Controller -> Service -> Mapper -> SQL
    G.add_edge("user_list.jsp", "UserController.listUsers", relation="AJAX_CALL")
    G.add_edge("UserController.listUsers", "UserService.getUser", relation="CALLS")
    G.add_edge("UserService.getUser", "UserMapper.selectById", relation="CALLS")
    G.add_edge("UserMapper.selectById", "SELECT_USER", relation="EXECUTES")

    # Intentional issues:
    # 1. OrphanController.orphan has no service calls (issue)
    # 2. OrphanService.orphan has no mapper calls (issue)
    # 3. OrphanMapper.unused is never called (issue)
    # 4. UserMapper.noSql has no SQL statement (issue)
    # 5. orphan.jsp has no AJAX calls (issue)
    # 6. ORPHAN_NODE is completely disconnected (orphan)

    return G


async def test_completeness_scanner():
    """Test CompletenessScanner functionality"""
    print("=" * 60)
    print("Testing CompletenessScanner")
    print("=" * 60)

    try:
        # Create test graph
        graph = create_test_graph()
        print(f"\nTest graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # Initialize scanner (without LLM for basic tests)
        scanner = CompletenessScanner(llm_engine=None)

        # Test 1: Find orphan nodes
        print("\n[1] Testing orphan detection...")

        orphans = await scanner.find_orphan_nodes(graph)

        assert "UNKNOWN" in orphans, "Should find orphan node"
        assert len(orphans["UNKNOWN"]) == 1, "Should have 1 orphan"
        assert orphans["UNKNOWN"][0]["name"] == "orphan", "Should be the ORPHAN_NODE"

        print(f"  [OK] Found {sum(len(v) for v in orphans.values())} orphan nodes:")
        for node_type, nodes in orphans.items():
            for node in nodes:
                print(f"    - {node_type}: {node['name']}")

        # Test 2: Find missing relationships
        print("\n[2] Testing missing relationship detection...")

        issues = await scanner.find_missing_relationships(graph)

        # Expected issues:
        # 1. OrphanController.orphan - no service calls
        # 2. OrphanService.orphan - no mapper calls
        # 3. OrphanMapper.unused - never called
        # 4. UserMapper.noSql - no SQL
        # 5. orphan.jsp - no AJAX

        assert len(issues) >= 4, f"Should find at least 4 issues, found {len(issues)}"

        print(f"  [OK] Found {len(issues)} potential issues:")
        for issue in issues:
            severity = issue['severity']
            severity_icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🔵"
            print(f"    {severity_icon} [{issue['type']}] {issue['message']}")

        # Test 3: Check specific issue types
        print("\n[3] Testing specific issue patterns...")

        issue_types = {i['type'] for i in issues}

        assert "orphan_controller" in issue_types, "Should detect orphan controller"
        assert "orphan_service" in issue_types, "Should detect orphan service"
        assert "orphan_mapper" in issue_types, "Should detect orphan mapper"
        assert "no_sql" in issue_types, "Should detect missing SQL"

        print(f"  [OK] Detected issue types: {', '.join(sorted(issue_types))}")

        # Test 4: Completeness score
        print("\n[4] Testing completeness score calculation...")

        score = scanner._calculate_completeness_score(
            total_nodes=graph.number_of_nodes(),
            total_edges=graph.number_of_edges(),
            total_orphans=1,
            total_issues=len(issues)
        )

        assert 0.0 <= score <= 1.0, "Score should be between 0 and 1"
        print(f"  [OK] Completeness score: {score:.2f} (0.0 = incomplete, 1.0 = complete)")

        # Test 5: Full scan
        print("\n[5] Testing full graph scan...")

        results = await scanner.scan_graph(graph)

        assert "summary" in results, "Should have summary"
        assert "orphans" in results, "Should have orphans"
        assert "issues" in results, "Should have issues"

        summary = results["summary"]
        assert summary["total_nodes"] == graph.number_of_nodes()
        assert summary["total_edges"] == graph.number_of_edges()
        assert summary["total_orphans"] >= 1
        assert summary["total_issues"] >= 4

        print(f"  [OK] Full scan complete:")
        print(f"    Nodes: {summary['total_nodes']}")
        print(f"    Edges: {summary['total_edges']}")
        print(f"    Orphans: {summary['total_orphans']}")
        print(f"    Issues: {summary['total_issues']}")
        print(f"    Completeness: {summary['completeness_score']:.2%}")

        # Test 6: Issue severity levels
        print("\n[6] Testing issue severity levels...")

        high_severity = [i for i in issues if i['severity'] == 'high']
        medium_severity = [i for i in issues if i['severity'] == 'medium']
        low_severity = [i for i in issues if i['severity'] == 'low']

        print(f"  [OK] Severity distribution:")
        print(f"    High:   {len(high_severity)} issues")
        print(f"    Medium: {len(medium_severity)} issues")
        print(f"    Low:    {len(low_severity)} issues")

        # Test 7: Edge case - perfect graph
        print("\n[7] Testing edge case: perfect graph...")

        perfect_graph = nx.DiGraph()
        perfect_graph.add_node("A", type="TEST")
        perfect_graph.add_node("B", type="TEST")
        perfect_graph.add_edge("A", "B")

        perfect_orphans = await scanner.find_orphan_nodes(perfect_graph)
        perfect_issues = await scanner.find_missing_relationships(perfect_graph)

        assert len(perfect_orphans) == 0, "Perfect graph should have no orphans"
        # Note: perfect_issues might have issues due to type checking
        print(f"  [OK] Perfect graph: {len(perfect_orphans)} orphans")

        # Test 8: Edge case - empty graph
        print("\n[8] Testing edge case: empty graph...")

        empty_graph = nx.DiGraph()
        empty_results = await scanner.scan_graph(empty_graph)

        assert empty_results["summary"]["total_nodes"] == 0
        assert empty_results["summary"]["completeness_score"] == 0.0

        print(f"  [OK] Empty graph handled correctly")

        # Test result
        print("\n" + "=" * 60)
        print("[OK] CompletenessScanner test PASSED")
        print("=" * 60)

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
    success = asyncio.run(test_completeness_scanner())
    sys.exit(0 if success else 1)
