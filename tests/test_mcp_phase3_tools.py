#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MCP Phase 3 Tool Integration

Tests all Phase 3 analyzers registered as MCP tools
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.springmvc_mcp_server import SpringMVCMCPServer


async def test_analyze_jsp(server):
    """Test analyze_jsp tool"""
    print("\n" + "="*60)
    print("TEST 1: analyze_jsp")
    print("="*60)

    result = await server.handle_tool_call(
        tool_name="analyze_jsp",
        arguments={
            "jsp_file": "test_samples/jsp/user_list.jsp",
            "output_file": "output/test/jsp_analysis.json"
        }
    )

    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")

    if result.get('success'):
        analysis = result.get('result', {})
        print(f"  ✓ JSP file: {analysis.get('jsp_file')}")
        print(f"  ✓ Total elements: {analysis.get('statistics', {}).get('total_elements', 0)}")
        print(f"  ✓ Forms: {analysis.get('statistics', {}).get('total_forms', 0)}")
        print(f"  ✓ Tables: {analysis.get('statistics', {}).get('total_tables', 0)}")
    else:
        print(f"  ✗ Error: {result.get('error')}")

    return result.get('success', False)


async def test_analyze_controller(server):
    """Test analyze_controller tool"""
    print("\n" + "="*60)
    print("TEST 2: analyze_controller")
    print("="*60)

    result = await server.handle_tool_call(
        tool_name="analyze_controller",
        arguments={
            "controller_file": "test_samples/controllers/UserController.java",
            "output_file": "output/test/controller_analysis.json"
        }
    )

    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")

    if result.get('success'):
        analysis = result.get('result', {})
        print(f"  ✓ Controller: {analysis.get('controller_name')}")
        print(f"  ✓ Endpoints: {analysis.get('statistics', {}).get('total_endpoints', 0)}")
        print(f"  ✓ GET methods: {analysis.get('statistics', {}).get('http_methods', {}).get('GET', 0)}")
        print(f"  ✓ POST methods: {analysis.get('statistics', {}).get('http_methods', {}).get('POST', 0)}")
    else:
        print(f"  ✗ Error: {result.get('error')}")

    return result.get('success', False)


async def test_analyze_service(server):
    """Test analyze_service tool"""
    print("\n" + "="*60)
    print("TEST 3: analyze_service")
    print("="*60)

    result = await server.handle_tool_call(
        tool_name="analyze_service",
        arguments={
            "service_file": "test_samples/services/UserService.java",
            "output_file": "output/test/service_analysis.json"
        }
    )

    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")

    if result.get('success'):
        analysis = result.get('result', {})
        print(f"  ✓ Service: {analysis.get('service_name')}")
        print(f"  ✓ Methods: {analysis.get('statistics', {}).get('total_methods', 0)}")
        print(f"  ✓ Is service: {analysis.get('is_service', False)}")
        print(f"  ✓ Transactional: {analysis.get('statistics', {}).get('transactional_methods', 0)}")
    else:
        print(f"  ✗ Error: {result.get('error')}")

    return result.get('success', False)


async def test_analyze_mybatis(server):
    """Test analyze_mybatis tool"""
    print("\n" + "="*60)
    print("TEST 4: analyze_mybatis")
    print("="*60)

    result = await server.handle_tool_call(
        tool_name="analyze_mybatis",
        arguments={
            "interface_file": "test_samples/mappers/UserMapper.java",
            "xml_file": "test_samples/mappers/UserMapper.xml",
            "output_file": "output/test/mybatis_analysis.json"
        }
    )

    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")

    if result.get('success'):
        analysis = result.get('result', {})
        print(f"  ✓ Mapper: {analysis.get('mapper_name')}")
        print(f"  ✓ Interface methods: {analysis.get('statistics', {}).get('interface_methods', 0)}")
        print(f"  ✓ XML statements: {analysis.get('statistics', {}).get('xml_statements', 0)}")
        print(f"  ✓ Mapped methods: {analysis.get('statistics', {}).get('mapped_methods', 0)}")
        print(f"  ✓ Is mapper: {analysis.get('interface', {}).get('is_mapper', False)}")
    else:
        print(f"  ✗ Error: {result.get('error')}")

    return result.get('success', False)


async def test_all_tools():
    """Run all tool tests"""
    print("\n" + "="*70)
    print("MCP PHASE 3 TOOL INTEGRATION TESTS")
    print("="*70)

    # Create single server instance to avoid stdout wrapping issues
    server = SpringMVCMCPServer(project_root=str(project_root))

    results = {
        'analyze_jsp': await test_analyze_jsp(server),
        'analyze_controller': await test_analyze_controller(server),
        'analyze_service': await test_analyze_service(server),
        'analyze_mybatis': await test_analyze_mybatis(server)
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    for tool, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {tool}")

    print(f"\nResults: {passed}/{total} tests passed")
    print("="*70)

    return passed == total


def main():
    """Main entry point"""
    success = asyncio.run(test_all_tools())
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
