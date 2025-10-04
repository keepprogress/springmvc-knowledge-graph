#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple MCP Phase 3 Tool Integration Test (file-based output)"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.springmvc_mcp_server import SpringMVCMCPServer


async def main():
    """Main test function"""
    output_file = project_root / "output" / "test" / "mcp_test_results.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("MCP PHASE 3 TOOL INTEGRATION TESTS\n")
        f.write("="*70 + "\n\n")

        # Create single server instance
        server = SpringMVCMCPServer(project_root=str(project_root))
        f.write(f"Server initialized: {server.name} v{server.version}\n")
        f.write(f"Tools registered: {len(server.tools)}\n\n")

        # Test 1: analyze_mybatis (simple test with existing sample)
        f.write("="*60 + "\n")
        f.write("TEST: analyze_mybatis\n")
        f.write("="*60 + "\n")

        result = await server.handle_tool_call(
            tool_name="analyze_mybatis",
            arguments={
                "interface_file": "test_samples/mappers/UserMapper.java",
                "xml_file": "test_samples/mappers/UserMapper.xml",
                "output_file": "output/test/mybatis_mcp_test.json"
            }
        )

        f.write(f"Success: {result.get('success')}\n")
        f.write(f"Message: {result.get('message')}\n")

        if result.get('success'):
            analysis = result.get('result', {})
            stats = analysis.get('statistics', {})
            f.write(f"  Mapper: {analysis.get('mapper_name')}\n")
            f.write(f"  Interface methods: {stats.get('interface_methods', 0)}\n")
            f.write(f"  XML statements: {stats.get('xml_statements', 0)}\n")
            f.write(f"  Mapped methods: {stats.get('mapped_methods', 0)}\n")
            f.write(f"  ✓ TEST PASSED\n")
        else:
            f.write(f"  Error: {result.get('error')}\n")
            f.write(f"  ✗ TEST FAILED\n")

        f.write("\n" + "="*70 + "\n")
        f.write(f"TEST COMPLETE - Results saved to: {output_file}\n")
        f.write("="*70 + "\n")

    print(f"Test results written to: {output_file}")
    print("Check the file for detailed results.")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
