#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Slash Commands Integration

Tests all Phase 4.2 slash commands
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.springmvc_mcp_server import SpringMVCMCPServer


async def test_analyze_jsp():
    """Test /analyze-jsp command"""
    print("\n[Test 1/4] /analyze-jsp command")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root))

    # Test 1: Basic usage
    result = await server.handle_command(
        "/analyze-jsp test_samples/jsp/user_list.jsp"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: {result.get('message')}")
        print(f"  JSP file: {data.get('jsp_file')}")
        print(f"  Total elements: {data.get('total_elements', 0)}")
        print(f"  Forms: {data.get('forms', 0)}")
        print(f"  Tables: {data.get('tables', 0)}")
        return True
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_analyze_controller():
    """Test /analyze-controller command"""
    print("\n[Test 2/4] /analyze-controller command")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root))

    result = await server.handle_command(
        "/analyze-controller test_samples/controllers/UserController.java"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: {result.get('message')}")
        print(f"  Controller: {data.get('controller_name')}")
        print(f"  Total endpoints: {data.get('total_endpoints', 0)}")
        print(f"  GET: {data.get('GET', 0)}, POST: {data.get('POST', 0)}")
        return True
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_analyze_service():
    """Test /analyze-service command"""
    print("\n[Test 3/4] /analyze-service command")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root))

    result = await server.handle_command(
        "/analyze-service test_samples/services/UserService.java"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: {result.get('message')}")
        print(f"  Service: {data.get('service_name')}")
        print(f"  Total methods: {data.get('total_methods', 0)}")
        print(f"  Public methods: {data.get('public_methods', 0)}")
        print(f"  Is @Service: {data.get('is_service', False)}")
        return True
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_analyze_mybatis():
    """Test /analyze-mybatis command"""
    print("\n[Test 4/4] /analyze-mybatis command")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root))

    # Test with both positional arguments
    result = await server.handle_command(
        "/analyze-mybatis test_samples/mappers/UserMapper.java test_samples/mappers/UserMapper.xml"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: {result.get('message')}")
        print(f"  Mapper: {data.get('mapper_name')}")
        print(f"  Interface methods: {data.get('interface_methods', 0)}")
        print(f"  XML statements: {data.get('xml_statements', 0)}")
        print(f"  Coverage: {data.get('coverage', '0/0')}")
        return True
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_command_with_flags():
    """Test command with flags (--output, --force-refresh)"""
    print("\n[Bonus Test] Command with flags")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root))

    result = await server.handle_command(
        "/analyze-mybatis test_samples/mappers/UserMapper.java --xml test_samples/mappers/UserMapper.xml --output output/test/mybatis_cmd.json --force-refresh"
    )

    if result.get('success'):
        data = result.get('data', {})
        print(f"✓ PASS: Command with flags works")
        print(f"  Output file: {data.get('output_file')}")
        return True
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_invalid_command():
    """Test invalid command handling"""
    print("\n[Error Test] Invalid command")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root), log_level="ERROR")

    result = await server.handle_command("/unknown-command test.jsp")

    if not result.get('success'):
        print(f"✓ PASS: Invalid command rejected")
        print(f"  Error: {result.get('error')}")
        return True
    else:
        print(f"✗ FAIL: Invalid command should have been rejected")
        return False


async def test_quoted_arguments():
    """Test quoted arguments with spaces (shlex parsing)"""
    print("\n[New Test 1] Quoted arguments with spaces")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root), log_level="ERROR")

    # Test with quoted path containing spaces
    result = await server.handle_command(
        '/analyze-jsp test_samples/jsp/user_list.jsp --output "output/test/path with spaces.json"'
    )

    if result.get('success'):
        data = result.get('data', {})
        output_file = data.get('output_file')
        if 'path with spaces.json' in output_file:
            print(f"✓ PASS: Quoted arguments parsed correctly")
            print(f"  Output file: {output_file}")
            return True
        else:
            print(f"✗ FAIL: Quoted argument not preserved")
            return False
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_command_aliases():
    """Test command aliases (short forms)"""
    print("\n[New Test 2] Command aliases")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root), log_level="ERROR")

    # Test short alias 'mb' for analyze-mybatis
    result = await server.handle_command(
        "/mb test_samples/mappers/UserMapper.java test_samples/mappers/UserMapper.xml"
    )

    if result.get('success'):
        print(f"✓ PASS: Command alias 'mb' works")
        print(f"  Mapper: {result.get('data', {}).get('mapper_name')}")
        return True
    else:
        print(f"✗ FAIL: {result.get('error')}")
        return False


async def test_list_commands():
    """Test list_commands() method"""
    print("\n[New Test 3] List commands discovery")
    print("-" * 60)

    server = SpringMVCMCPServer(project_root=str(project_root), log_level="ERROR")

    commands = server.list_commands()

    if len(commands) >= 4:
        print(f"✓ PASS: Found {len(commands)} commands")
        for cmd in commands:
            aliases_str = f" (aliases: {', '.join(cmd['aliases'])})" if cmd['aliases'] else ""
            print(f"  {cmd['name']}: {cmd['description']}{aliases_str}")
        return True
    else:
        print(f"✗ FAIL: Expected at least 4 commands, found {len(commands)}")
        return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Phase 4.2 Slash Commands (Enhanced)")
    print("=" * 60)

    tests = [
        test_analyze_jsp(),
        test_analyze_controller(),
        test_analyze_service(),
        test_analyze_mybatis(),
        test_command_with_flags(),
        test_invalid_command(),
        test_quoted_arguments(),
        test_command_aliases(),
        test_list_commands()
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
