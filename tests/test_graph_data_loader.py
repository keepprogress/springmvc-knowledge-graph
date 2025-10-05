#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GraphDataLoader with mock analysis data
"""

import sys
import json
from pathlib import Path

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

from mcp_server.tools.graph_data_loader import GraphDataLoader


def test_data_loader():
    """Test GraphDataLoader with mock data"""
    print("=" * 60)
    print("Testing GraphDataLoader")
    print("=" * 60)

    # Initialize loader
    loader = GraphDataLoader(base_dir=str(project_root / "output"))

    # Load all data
    print("\n[1] Loading all analysis results...")
    data = loader.load_all_analysis_results()

    # Display summary
    print("\n[2] Data Summary:")
    summary = loader.get_summary()

    print(f"\nCounts:")
    for key, count in summary["counts"].items():
        print(f"  {key}: {count}")

    print(f"\nValidation:")
    print(f"  Issues: {summary['validation']['issues_count']}")
    if summary['validation']['issues']:
        for issue in summary['validation']['issues']:
            print(f"    - {issue}")

    # Validate data
    print("\n[3] Validating data structure...")
    is_valid = loader.validate_data()
    print(f"  Valid: {is_valid}")

    if not is_valid:
        print("\n  Validation Issues:")
        for issue in loader.validation_issues:
            print(f"    - {issue}")

    # Sample data inspection
    print("\n[4] Sample Data Inspection:")

    if data["jsp"]:
        print(f"\n  JSP Sample ({data['jsp'][0].get('file', 'unknown')}):")
        jsp = data["jsp"][0]
        print(f"    - Static includes: {len(jsp.get('static_includes', []))}")
        print(f"    - Dynamic includes: {len(jsp.get('dynamic_includes', []))}")
        print(f"    - AJAX calls: {len(jsp.get('ajax_calls', []))}")
        print(f"    - Forms: {len(jsp.get('forms', []))}")

    if data["controllers"]:
        print(f"\n  Controller Sample ({data['controllers'][0].get('class_name', 'unknown')}):")
        controller = data["controllers"][0]
        print(f"    - Package: {controller.get('package', 'N/A')}")
        print(f"    - Base path: {controller.get('base_path', 'N/A')}")
        print(f"    - Methods: {len(controller.get('methods', []))}")
        if controller.get('methods'):
            method = controller['methods'][0]
            print(f"    - First method: {method.get('name', 'N/A')} -> {method.get('request_mapping', {}).get('path', 'N/A')}")

    if data["services"]:
        print(f"\n  Service Sample ({data['services'][0].get('class_name', 'unknown')}):")
        service = data["services"][0]
        print(f"    - Package: {service.get('package', 'N/A')}")
        print(f"    - Methods: {len(service.get('methods', []))}")
        print(f"    - Dependencies: {len(service.get('dependencies', []))}")

    if data["mappers"]:
        mapper = data["mappers"][0]
        mapper_name = mapper.get('mapper_name', 'unknown')
        xml = mapper.get('xml', {})
        print(f"\n  Mapper Sample ({mapper_name}):")
        print(f"    - Namespace: {xml.get('namespace', 'N/A')}")
        print(f"    - Statements: {len(xml.get('statements', []))}")
        if xml.get('statements'):
            stmt = xml['statements'][0]
            print(f"    - First statement: {stmt.get('id', 'N/A')} ({stmt.get('type', 'N/A')})")

    # Test helper methods
    print("\n[5] Testing Data Access Helper Methods:")

    if data["controllers"]:
        controller = data["controllers"][0]
        print(f"\n  Controller Helper Methods:")
        print(f"    - get_controller_class_name(): {loader.get_controller_class_name(controller)}")
        print(f"    - get_controller_base_path(): {loader.get_controller_base_path(controller)}")
        print(f"    - get_controller_methods(): {len(loader.get_controller_methods(controller))} methods")

    if data["services"]:
        service = data["services"][0]
        print(f"\n  Service Helper Methods:")
        print(f"    - get_service_class_name(): {loader.get_service_class_name(service)}")
        print(f"    - get_service_methods(): {len(loader.get_service_methods(service))} methods")
        print(f"    - get_service_dependencies(): {len(loader.get_service_dependencies(service))} dependencies")

    if data["mappers"]:
        mapper = data["mappers"][0]
        print(f"\n  Mapper Helper Methods:")
        print(f"    - get_mapper_name(): {loader.get_mapper_name(mapper)}")
        print(f"    - get_mapper_namespace(): {loader.get_mapper_namespace(mapper)}")
        print(f"    - get_mapper_statements(): {len(loader.get_mapper_statements(mapper))} statements")

    print("\n  Convenience Query Methods:")
    all_controllers = loader.get_all_controller_classes()
    print(f"    - get_all_controller_classes(): {len(all_controllers)} controllers")
    found_user_controller = loader.find_controller_by_path('/user')
    print(f"    - find_controller_by_path('/user'): {found_user_controller is not None}")
    if all_controllers:
        found_service = loader.find_service_by_class_name(all_controllers[0])
        print(f"    - find_service_by_class_name(): Can query by class name")

    # Test result
    print("\n" + "=" * 60)
    if is_valid and summary["counts"]["jsp"] > 0:
        print("[OK] GraphDataLoader test PASSED")
        print("=" * 60)
        return True
    else:
        print("[ERROR] GraphDataLoader test FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_data_loader()
    sys.exit(0 if success else 1)
