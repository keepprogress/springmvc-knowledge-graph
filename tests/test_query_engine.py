#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests for Query Engine

Tests Phase 4.4 query engine features
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.tools.query_engine import QueryEngine, CallChain, ImpactAnalysisResult
from mcp_server.tools.dependency_graph import DependencyGraph, DependencyGraphBuilder


async def test_query_engine_basic():
    """Test basic query engine functionality"""
    print("\n[Test 1/5] Query Engine Basic Functionality")
    print("-" * 60)

    # Create a simple test graph
    graph = DependencyGraph()
    graph.add_node("UserController", "controller")
    graph.add_node("UserService", "service")
    graph.add_node("UserMapper", "mybatis")
    graph.add_node("user.jsp", "jsp")

    graph.add_edge("UserController", "UserService", "uses")
    graph.add_edge("UserService", "UserMapper", "uses")
    graph.add_edge("user.jsp", "UserController", "calls")

    # Create query engine
    engine = QueryEngine(graph)

    # Test statistics
    stats = engine.get_statistics()

    if (stats['total_nodes'] == 4 and
        stats['total_edges'] == 3 and
        'controller' in stats['by_type']):
        print("[PASS]: Query engine basic functionality")
        print(f"  Total nodes: {stats['total_nodes']}")
        print(f"  Total edges: {stats['total_edges']}")
        print(f"  Node types: {list(stats['by_type'].keys())}")
        return True
    else:
        print("[FAIL]: Query engine statistics incorrect")
        return False


async def test_find_call_chains():
    """Test finding call chains"""
    print("\n[Test 2/5] Find Call Chains")
    print("-" * 60)

    # Create test graph
    graph = DependencyGraph()
    graph.add_node("UserController", "controller")
    graph.add_node("UserService", "service")
    graph.add_node("UserMapper", "mybatis")

    graph.add_edge("UserController", "UserService", "uses")
    graph.add_edge("UserService", "UserMapper", "uses")

    # Create query engine
    engine = QueryEngine(graph)

    # Find chain from Controller to Mapper
    chains = engine.find_call_chains("UserController", "UserMapper", max_depth=5)

    if len(chains) > 0:
        chain = chains[0]
        if (chain.path == ["UserController", "UserService", "UserMapper"] and
            chain.depth == 2):
            print("[PASS]: Call chain finding")
            print(f"  Found {len(chains)} chain(s)")
            print(f"  Chain path: {' -> '.join(chain.path)}")
            print(f"  Chain depth: {chain.depth}")
            return True

    print("[FAIL]: Call chain not found or incorrect")
    return False


async def test_direct_dependencies():
    """Test finding direct dependencies"""
    print("\n[Test 3/5] Direct Dependencies")
    print("-" * 60)

    # Create test graph
    graph = DependencyGraph()
    graph.add_node("UserController", "controller")
    graph.add_node("UserService", "service")
    graph.add_node("OrderService", "service")

    graph.add_edge("UserController", "UserService", "uses")
    graph.add_edge("UserController", "OrderService", "uses")

    # Create query engine
    engine = QueryEngine(graph)

    # Find direct dependencies (no end node specified)
    chains = engine.find_call_chains("UserController")

    if len(chains) == 2:
        print("[PASS]: Direct dependencies")
        print(f"  Found {len(chains)} direct dependencies")
        for chain in chains:
            print(f"    -> {chain.path[1]}")
        return True
    else:
        print(f"[FAIL]: Expected 2 direct dependencies, got {len(chains)}")
        return False


async def test_impact_analysis():
    """Test impact analysis (upstream and downstream)"""
    print("\n[Test 4/5] Impact Analysis")
    print("-" * 60)

    # Create test graph
    graph = DependencyGraph()
    graph.add_node("UserController", "controller")
    graph.add_node("AdminController", "controller")
    graph.add_node("UserService", "service")
    graph.add_node("UserMapper", "mybatis")

    graph.add_edge("UserController", "UserService", "uses")
    graph.add_edge("AdminController", "UserService", "uses")
    graph.add_edge("UserService", "UserMapper", "uses")

    # Create query engine
    engine = QueryEngine(graph)

    # Test upstream (who depends on UserService)
    result = engine.impact_analysis("UserService", direction="upstream", max_depth=3)

    if result and result.total_upstream == 2:
        print("[PASS]: Impact analysis (upstream)")
        print(f"  Target: {result.target_node}")
        print(f"  Upstream components: {result.total_upstream}")
        print(f"  Downstream components: {result.total_downstream}")
        return True
    else:
        expected = 2
        actual = result.total_upstream if result else 0
        print(f"[FAIL]: Expected {expected} upstream, got {actual}")
        return False


async def test_query_by_type():
    """Test querying nodes by type"""
    print("\n[Test 5/5] Query by Type")
    print("-" * 60)

    # Create test graph
    graph = DependencyGraph()
    graph.add_node("UserController", "controller")
    graph.add_node("AdminController", "controller")
    graph.add_node("UserService", "service")
    graph.add_node("OrderService", "service")
    graph.add_node("UserMapper", "mybatis")

    # Create query engine
    engine = QueryEngine(graph)

    # Query by type
    controllers = engine.query_by_type("controller")
    services = engine.query_by_type("service")
    mappers = engine.query_by_type("mybatis")

    if len(controllers) == 2 and len(services) == 2 and len(mappers) == 1:
        print("[PASS]: Query by type")
        print(f"  Controllers: {len(controllers)}")
        print(f"  Services: {len(services)}")
        print(f"  Mappers: {len(mappers)}")
        return True
    else:
        print(f"[FAIL]: Query by type returned incorrect counts")
        print(f"  Controllers: {len(controllers)} (expected 2)")
        print(f"  Services: {len(services)} (expected 2)")
        print(f"  Mappers: {len(mappers)} (expected 1)")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Query Engine")
    print("=" * 60)

    tests = [
        test_query_engine_basic(),
        test_find_call_chains(),
        test_direct_dependencies(),
        test_impact_analysis(),
        test_query_by_type()
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    # Count results
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is not True)

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{len(results)} tests passed")
    if failed > 0:
        print(f"         {failed} tests failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
