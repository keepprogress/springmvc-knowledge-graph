#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phase 6.1 Commands

Tests /build-graph and /graph-stats slash commands
"""

import asyncio
import json
import sys
from pathlib import Path
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.springmvc_mcp_server import SpringMVCMCPServer


def setup_test_data():
    """
    Create minimal test analysis data for graph building
    """
    test_output_dir = project_root / "output" / "test_graph"
    test_analysis_dir = test_output_dir / "analysis"
    test_graph_dir = test_output_dir / "graph"

    # Clean up if exists
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)

    # Create directory structure expected by GraphDataLoader
    # analysis/jsp/, analysis/controllers/, analysis/services/, analysis/mappers/
    (test_analysis_dir / "jsp").mkdir(parents=True, exist_ok=True)
    (test_analysis_dir / "controllers").mkdir(parents=True, exist_ok=True)
    (test_analysis_dir / "services").mkdir(parents=True, exist_ok=True)
    (test_analysis_dir / "mappers").mkdir(parents=True, exist_ok=True)
    test_graph_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal JSP analysis
    jsp_analysis = {
        "jsp_analysis": [
            {
                "jsp_file": "test_samples/jsp/user_list.jsp",
                "analysis": {
                    "ajax_calls": [
                        {
                            "url": "/user/list",
                            "method": "GET",
                            "confidence": 0.95
                        }
                    ]
                }
            }
        ]
    }

    # Create minimal controller analysis
    controller_analysis = {
        "controller_analysis": [
            {
                "java_file": "test_samples/controllers/UserController.java",
                "analysis": {
                    "class_name": "UserController",
                    "endpoints": [
                        {
                            "path": "/user/list",
                            "method": "GET",
                            "handler_method": "listUsers",
                            "confidence": 1.0
                        }
                    ],
                    "service_dependencies": [
                        {
                            "service_name": "UserService",
                            "methods": ["listUsers"],
                            "confidence": 1.0
                        }
                    ]
                }
            }
        ]
    }

    # Create minimal service analysis
    service_analysis = {
        "service_analysis": [
            {
                "java_file": "test_samples/services/UserService.java",
                "analysis": {
                    "class_name": "UserService",
                    "mapper_dependencies": [
                        {
                            "mapper_name": "UserMapper",
                            "methods": ["selectAllUsers"],
                            "confidence": 1.0
                        }
                    ]
                }
            }
        ]
    }

    # Create minimal mybatis analysis
    mybatis_analysis = {
        "mybatis_analysis": [
            {
                "interface_file": "test_samples/mappers/UserMapper.java",
                "xml_file": "test_samples/mappers/UserMapper.xml",
                "analysis": {
                    "mapper_name": "UserMapper",
                    "sql_statements": [
                        {
                            "id": "selectAllUsers",
                            "type": "SELECT",
                            "tables": ["users"],
                            "confidence": 1.0
                        }
                    ]
                }
            }
        ]
    }

    # Write analysis files to respective subdirectories
    with open(test_analysis_dir / "jsp" / "user_list.json", 'w', encoding='utf-8') as f:
        json.dump(jsp_analysis, f, indent=2)

    with open(test_analysis_dir / "controllers" / "UserController.json", 'w', encoding='utf-8') as f:
        json.dump(controller_analysis, f, indent=2)

    with open(test_analysis_dir / "services" / "UserService.json", 'w', encoding='utf-8') as f:
        json.dump(service_analysis, f, indent=2)

    with open(test_analysis_dir / "mappers" / "UserMapper.json", 'w', encoding='utf-8') as f:
        json.dump(mybatis_analysis, f, indent=2)

    return test_output_dir


async def test_build_graph_basic():
    """Test /build-graph command with basic usage"""
    print("\n[Test 1/6] /build-graph - Basic usage")
    print("-" * 60)

    test_dir = setup_test_data()
    server = SpringMVCMCPServer(project_root=str(project_root))

    # Use relative paths (resolve_path will make them absolute)
    result = await server.handle_command(
        "/build-graph --base-dir=output/test_graph/analysis --output=output/test_graph/graph/test_graph.json"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: {result.get('message')}")
        print(f"  Graph file: {data.get('graph_file')}")
        print(f"  Nodes: {data.get('statistics', {}).get('total_nodes', 0)}")
        print(f"  Edges: {data.get('statistics', {}).get('total_edges', 0)}")

        # Verify graph file exists
        graph_file = Path(data.get('graph_file'))
        if graph_file.exists():
            print(f"  ✓ Graph file created: {graph_file.name}")
            return True
        else:
            print(f"  ✗ Graph file not found")
            return False
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_build_graph_with_exports():
    """Test /build-graph command with statistics and low-confidence exports"""
    print("\n[Test 2/6] /build-graph - With exports")
    print("-" * 60)

    test_dir = setup_test_data()
    server = SpringMVCMCPServer(project_root=str(project_root))

    result = await server.handle_command(
        "/build-graph --base-dir=output/test_graph/analysis --output=output/test_graph/graph/test_graph_full.json"
    )

    if result.get('success'):
        data = result.get('data', {})
        exports = data.get('exports', {})
        print(f"✓ PASS: Graph built with exports")

        # Check all export files
        all_exist = True
        for export_type, export_path in exports.items():
            if export_path:
                export_file = Path(export_path)
                if export_file.exists():
                    print(f"  ✓ {export_type}: {export_file.name}")
                else:
                    print(f"  ✗ {export_type}: NOT FOUND")
                    all_exist = False

        return all_exist
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_build_graph_no_exports():
    """Test /build-graph command with exports disabled"""
    print("\n[Test 3/6] /build-graph - No exports")
    print("-" * 60)

    test_dir = setup_test_data()
    server = SpringMVCMCPServer(project_root=str(project_root))

    result = await server.handle_command(
        "/build-graph --base-dir=output/test_graph/analysis --output=output/test_graph/graph/minimal.json "
        "--no-export-stats --no-export-low-conf"
    )

    if result.get('success'):
        data = result.get('data', {})
        exports = data.get('exports', {})
        print(f"✓ PASS: Graph built without optional exports")

        # Verify stats and low_confidence are None
        if exports.get('stats') is None and exports.get('low_confidence') is None:
            print(f"  ✓ Optional exports disabled correctly")
            return True
        else:
            print(f"  ✗ Exports should be None when disabled")
            return False
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_build_graph_missing_dir():
    """Test /build-graph command with non-existent analysis directory"""
    print("\n[Test 4/6] /build-graph - Missing analysis directory")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root))

    result = await server.handle_command(
        "/build-graph --base-dir=nonexistent/analysis"
    )

    if not result.get('success'):
        print(f"✓ PASS: Correctly rejected missing directory")
        print(f"  Error: {result.get('error')[:80]}...")
        return True
    else:
        print(f"✗ FAIL: Should have rejected missing directory")
        return False


async def test_graph_stats_basic():
    """Test /graph-stats command with basic usage"""
    print("\n[Test 5/6] /graph-stats - Basic usage")
    print("-" * 60)

    # First build a graph
    test_dir = setup_test_data()
    server = SpringMVCMCPServer(project_root=str(project_root))

    build_result = await server.handle_command(
        "/build-graph --base-dir=output/test_graph/analysis --output=output/test_graph/graph/stats_test.json"
    )

    if not build_result.get('success'):
        print(f"✗ FAIL: Could not build graph for test")
        return False

    # Now test graph-stats
    result = await server.handle_command(
        "/graph-stats --graph-file=output/test_graph/graph/stats_test.json"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: {result.get('message')}")
        print(f"  Total Nodes: {data.get('total_nodes', 0)}")
        print(f"  Total Edges: {data.get('total_edges', 0)}")
        print(f"  Density: {data.get('density', 0.0)}")
        print(f"  Connected Components: {data.get('connected_components', 0)}")
        return True
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_graph_stats_detailed():
    """Test /graph-stats command with detailed breakdown"""
    print("\n[Test 6/6] /graph-stats - Detailed breakdown")
    print("-" * 60)

    # Build a graph first
    test_dir = setup_test_data()
    server = SpringMVCMCPServer(project_root=str(project_root))

    build_result = await server.handle_command(
        "/build-graph --base-dir=output/test_graph/analysis --output=output/test_graph/graph/detailed_stats.json"
    )

    if not build_result.get('success'):
        print(f"✗ FAIL: Could not build graph for test")
        return False

    # Now test detailed stats
    result = await server.handle_command(
        "/graph-stats --graph-file=output/test_graph/graph/detailed_stats.json --detailed"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: Detailed stats retrieved")

        # Verify detailed data exists
        has_detailed = (
            'nodes_by_type' in data and
            'edges_by_relation' in data
        )

        if has_detailed:
            print(f"  ✓ Nodes by type: {len(data.get('nodes_by_type', {}))}")
            print(f"  ✓ Edges by relation: {len(data.get('edges_by_relation', {}))}")
            return True
        else:
            print(f"  ✗ Detailed data missing")
            return False
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Phase 6.1 Commands (/build-graph, /graph-stats)")
    print("=" * 60)

    tests = [
        test_build_graph_basic(),
        test_build_graph_with_exports(),
        test_build_graph_no_exports(),
        test_build_graph_missing_dir(),
        test_graph_stats_basic(),
        test_graph_stats_detailed()
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
