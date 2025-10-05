#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Query Engine Slash Commands and MCP Tools

Tests for Phase 4.4 query engine functionality:
- /find-chain command
- /impact-analysis command
- find_chain MCP tool
- impact_analysis MCP tool
"""

import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress MCP SDK warning for tests
import warnings
warnings.filterwarnings("ignore", message=".*MCP SDK.*")

from mcp_server.springmvc_mcp_server import SpringMVCMCPServer


def setup_test_fixtures():
    """Set up test fixtures with graph data"""
    test_cache_dir = Path(__file__).parent / ".test_cache"
    test_cache_dir.mkdir(exist_ok=True)

    # Copy test graph to cache directory
    fixtures_dir = Path(__file__).parent / "fixtures"
    test_graph = fixtures_dir / "test_graph.json"

    if test_graph.exists():
        shutil.copy(test_graph, test_cache_dir / "dependency_graph.json")

    # Return absolute path for reliable lookup
    return str(test_cache_dir.absolute())


def cleanup_test_fixtures():
    """Clean up test fixtures"""
    test_cache_dir = Path(__file__).parent / ".test_cache"
    if test_cache_dir.exists():
        shutil.rmtree(test_cache_dir)


async def test_find_chain_command():
    """Test /find-chain slash command"""
    print("\n=== Test 1: /find-chain command ===")

    cache_dir = setup_test_fixtures()
    server = SpringMVCMCPServer(project_root=".")

    # Test basic usage with test fixtures (quote path for Windows compatibility)
    result = await server.handle_command(f'/find-chain UserController UserService --cache-dir "{cache_dir}"')

    print(f"Command: /find-chain UserController UserService")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', result.get('error'))}")
    if result.get('success'):
        print(f"Chains found: {result.get('data', {}).get('count', 0)}")

    return result.get('success')


async def test_find_chain_with_flags():
    """Test /find-chain with flags"""
    print("\n=== Test 2: /find-chain with flags ===")

    cache_dir = setup_test_fixtures()
    server = SpringMVCMCPServer(project_root=".")

    result = await server.handle_command(
        f'/find-chain UserController --max-depth 5 --format json --cache-dir "{cache_dir}"'
    )

    print(f"Command: /find-chain UserController --max-depth 5")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', result.get('error'))}")

    return result.get('success')


async def test_impact_analysis_command():
    """Test /impact-analysis slash command"""
    print("\n=== Test 3: /impact-analysis command ===")

    cache_dir = setup_test_fixtures()
    server = SpringMVCMCPServer(project_root=".")

    result = await server.handle_command(f'/impact-analysis UserService --cache-dir "{cache_dir}"')

    print(f"Command: /impact-analysis UserService")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', result.get('error'))}")
    if result.get('success'):
        print(f"Total affected: {result.get('data', {}).get('total_affected', 0)}")

    return result.get('success')


async def test_impact_analysis_with_direction():
    """Test /impact-analysis with direction"""
    print("\n=== Test 4: /impact-analysis with direction ===")

    cache_dir = setup_test_fixtures()
    server = SpringMVCMCPServer(project_root=".")

    result = await server.handle_command(
        f'/impact-analysis UserService --direction upstream --max-depth 3 --cache-dir "{cache_dir}"'
    )

    print(f"Command: /impact-analysis UserService --direction upstream")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', result.get('error'))}")

    return result.get('success')


async def test_find_chain_mcp_tool():
    """Test find_chain MCP tool"""
    print("\n=== Test 5: find_chain MCP tool ===")

    cache_dir = setup_test_fixtures()
    server = SpringMVCMCPServer(project_root=".")

    result = await server.handle_tool_call(
        tool_name="find_chain",
        arguments={
            "start_node": "UserController",
            "end_node": "UserService",
            "max_depth": 10,
            "cache_dir": cache_dir
        }
    )

    print(f"Tool: find_chain")
    print(f"Arguments: start_node=UserController, end_node=UserService")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', result.get('error'))}")
    if result.get('success') and result.get('chains'):
        print(f"Chains found: {result.get('count')}")

    return result.get('success')


async def test_impact_analysis_mcp_tool():
    """Test impact_analysis MCP tool"""
    print("\n=== Test 6: impact_analysis MCP tool ===")

    cache_dir = setup_test_fixtures()
    server = SpringMVCMCPServer(project_root=".")

    result = await server.handle_tool_call(
        tool_name="impact_analysis",
        arguments={
            "node": "UserService",
            "direction": "both",
            "max_depth": 5,
            "cache_dir": cache_dir
        }
    )

    print(f"Tool: impact_analysis")
    print(f"Arguments: node=UserService, direction=both")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', result.get('error'))}")
    if result.get('success'):
        print(f"Total affected: {result.get('total_affected', 0)}")

    return result.get('success')


async def test_command_aliases():
    """Test command aliases"""
    print("\n=== Test 7: Command aliases ===")

    cache_dir = setup_test_fixtures()
    server = SpringMVCMCPServer(project_root=".")

    # Test /chain alias
    result1 = await server.handle_command(f'/chain UserController --cache-dir "{cache_dir}"')
    print(f"Alias: /chain UserController")
    print(f"Success: {result1.get('success')}")

    # Test /impact alias
    result2 = await server.handle_command(f'/impact UserService --cache-dir "{cache_dir}"')
    print(f"Alias: /impact UserService")
    print(f"Success: {result2.get('success')}")

    return result1.get('success') and result2.get('success')


async def test_tool_registration():
    """Test that tools are registered correctly"""
    print("\n=== Test 8: Tool registration ===")

    server = SpringMVCMCPServer(project_root="test_samples/sample_project")

    # Check if tools are registered
    find_chain_registered = "find_chain" in server.tools
    impact_analysis_registered = "impact_analysis" in server.tools

    print(f"find_chain tool registered: {find_chain_registered}")
    print(f"impact_analysis tool registered: {impact_analysis_registered}")
    print(f"Total MCP tools: {len(server.tools)}")

    # Check if commands are registered
    find_chain_cmd = "find-chain" in server.commands
    chain_alias = "chain" in server.commands
    impact_cmd = "impact-analysis" in server.commands
    impact_alias = "impact" in server.commands

    print(f"/find-chain command registered: {find_chain_cmd}")
    print(f"/chain alias registered: {chain_alias}")
    print(f"/impact-analysis command registered: {impact_cmd}")
    print(f"/impact alias registered: {impact_alias}")
    print(f"Total commands: {len(server.commands)}")

    return (find_chain_registered and impact_analysis_registered and
            find_chain_cmd and chain_alias and impact_cmd and impact_alias)


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Query Engine Tests - Phase 4.4")
    print("=" * 60)

    results = []

    try:
        # Test tool registration first
        results.append(("Tool registration", await test_tool_registration()))

        # Test commands
        results.append(("find-chain command", await test_find_chain_command()))
        results.append(("find-chain with flags", await test_find_chain_with_flags()))
        results.append(("impact-analysis command", await test_impact_analysis_command()))
        results.append(("impact-analysis with direction", await test_impact_analysis_with_direction()))

        # Test MCP tools
        results.append(("find_chain MCP tool", await test_find_chain_mcp_tool()))
        results.append(("impact_analysis MCP tool", await test_impact_analysis_mcp_tool()))

        # Test aliases
        results.append(("Command aliases", await test_command_aliases()))

    finally:
        # Clean up test fixtures
        cleanup_test_fixtures()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nResults: {passed}/{len(results)} tests passed")

    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
