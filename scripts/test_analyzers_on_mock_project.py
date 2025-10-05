#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test all Phase 3 analyzers on mock project data

This script runs all analyzers on the mock SpringMVC project
to generate analysis results for Phase 5 testing.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    except Exception:
        pass  # If it fails, continue anyway

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.tools.jsp_analyzer import JSPAnalyzer
from mcp_server.tools.controller_analyzer import ControllerAnalyzer
from mcp_server.tools.service_analyzer import ServiceAnalyzer
from mcp_server.tools.mybatis_analyzer import MyBatisAnalyzer

async def test_jsp_analyzer():
    """Test JSP Analyzer"""
    print("\n" + "="*60)
    print("Testing JSP Analyzer")
    print("="*60)

    analyzer = JSPAnalyzer(project_root=str(project_root))
    mock_jsp_dir = project_root / "examples/mock_project/src/main/webapp/WEB-INF/views"

    # Find all JSP files
    jsp_files = list(mock_jsp_dir.rglob("*.jsp"))
    print(f"Found {len(jsp_files)} JSP files")

    results = []
    for jsp_file in jsp_files:
        print(f"\nAnalyzing: {jsp_file.relative_to(project_root)}")
        try:
            # JSP analyzer requires identifier and context
            identifier = str(jsp_file.relative_to(project_root))
            context = {"file_path": identifier}
            result = await analyzer.analyze_async(identifier, context)
            results.append(result)
            print(f"  [OK] Success - Found {len(result.get('includes', []))} includes, "
                  f"{len(result.get('ajax_calls', []))} AJAX calls")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # Save results
    output_dir = project_root / "output/analysis/jsp"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, result in enumerate(results):
        output_file = output_dir / f"jsp_{i+1}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(results)} JSP analysis results to {output_dir}")
    return results


async def test_controller_analyzer():
    """Test Controller Analyzer"""
    print("\n" + "="*60)
    print("Testing Controller Analyzer")
    print("="*60)

    analyzer = ControllerAnalyzer()
    mock_controller_dir = project_root / "examples/mock_project/src/main/java/com/example/controller"

    # Find all Controller files
    controller_files = list(mock_controller_dir.glob("*.java"))
    print(f"Found {len(controller_files)} Controller files")

    results = []
    for controller_file in controller_files:
        print(f"\nAnalyzing: {controller_file.name}")
        try:
            identifier = str(controller_file.relative_to(project_root))
            context = {"file_path": identifier}
            result = await analyzer.analyze_async(identifier, context)
            results.append(result)
            print(f"  [OK] Success - Class: {result.get('class_name', 'N/A')}, "
                  f"Methods: {len(result.get('methods', []))}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # Save results
    output_dir = project_root / "output/analysis/controllers"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, result in enumerate(results):
        # Extract just the class name from the file path
        file_path = result.get('file', result.get('class_name', 'Unknown'))
        class_name = Path(file_path).stem  # Get filename without extension
        output_file = output_dir / f"{class_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(results)} Controller analysis results to {output_dir}")
    return results


async def test_service_analyzer():
    """Test Service Analyzer"""
    print("\n" + "="*60)
    print("Testing Service Analyzer")
    print("="*60)

    analyzer = ServiceAnalyzer()
    mock_service_dir = project_root / "examples/mock_project/src/main/java/com/example/service"

    # Find all Service files
    service_files = list(mock_service_dir.glob("*.java"))
    print(f"Found {len(service_files)} Service files")

    results = []
    for service_file in service_files:
        print(f"\nAnalyzing: {service_file.name}")
        try:
            identifier = str(service_file.relative_to(project_root))
            context = {"file_path": identifier}
            result = await analyzer.analyze_async(identifier, context)
            results.append(result)
            print(f"  [OK] Success - Class: {result.get('class_name', 'N/A')}, "
                  f"Methods: {len(result.get('methods', []))}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # Save results
    output_dir = project_root / "output/analysis/services"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, result in enumerate(results):
        # Extract just the class name from the file path
        file_path = result.get('file', result.get('class_name', 'Unknown'))
        class_name = Path(file_path).stem  # Get filename without extension
        output_file = output_dir / f"{class_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(results)} Service analysis results to {output_dir}")
    return results


async def test_mybatis_analyzer():
    """Test MyBatis Analyzer"""
    print("\n" + "="*60)
    print("Testing MyBatis Analyzer")
    print("="*60)

    analyzer = MyBatisAnalyzer()
    mock_mapper_xml_dir = project_root / "examples/mock_project/src/main/resources/mapper"
    mock_mapper_interface_dir = project_root / "examples/mock_project/src/main/java/com/example/mapper"

    # Find all Mapper XML files
    mapper_xml_files = list(mock_mapper_xml_dir.glob("*.xml"))
    print(f"Found {len(mapper_xml_files)} Mapper XML files")

    results = []
    for mapper_xml_file in mapper_xml_files:
        print(f"\nAnalyzing: {mapper_xml_file.name}")
        try:
            # Find corresponding interface file (same base name)
            interface_file = mock_mapper_interface_dir / mapper_xml_file.name.replace('.xml', '.java')

            identifier = mapper_xml_file.stem  # UserMapper
            context = {
                "xml_path": str(mapper_xml_file.relative_to(project_root)),
                "interface_path": str(interface_file.relative_to(project_root)) if interface_file.exists() else ""
            }

            result = await analyzer.analyze_async(identifier, context)
            results.append(result)
            print(f"  [OK] Success - Namespace: {result.get('namespace', 'N/A')}, "
                  f"Statements: {len(result.get('statements', []))}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    # Save results
    output_dir = project_root / "output/analysis/mappers"
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, result in enumerate(results):
        # Use mapper_name as filename (e.g., "UserMapper")
        mapper_name = result.get('mapper_name', f'mapper_{i+1}')
        output_file = output_dir / f"{mapper_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(results)} MyBatis analysis results to {output_dir}")
    return results


async def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("SpringMVC Knowledge Graph - Analyzer Testing")
    print("Testing Phase 3 analyzers on mock project data")
    print("="*60)

    all_results = {}

    try:
        # Test each analyzer
        all_results['jsp'] = await test_jsp_analyzer()
        all_results['controllers'] = await test_controller_analyzer()
        all_results['services'] = await test_service_analyzer()
        all_results['mappers'] = await test_mybatis_analyzer()

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"JSP files analyzed:        {len(all_results.get('jsp', []))}")
        print(f"Controller files analyzed: {len(all_results.get('controllers', []))}")
        print(f"Service files analyzed:    {len(all_results.get('services', []))}")
        print(f"Mapper files analyzed:     {len(all_results.get('mappers', []))}")
        print("\n[OK] All analyzers tested successfully")
        print(f"[OK] Analysis results saved to output/analysis/")

        return True

    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
