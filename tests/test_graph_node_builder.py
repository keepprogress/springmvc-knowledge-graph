#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GraphNodeBuilder with mock analysis data
"""

import sys
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
from mcp_server.tools.graph_node_builder import NodeBuilder, NODE_TYPES


def test_node_builder():
    """Test NodeBuilder with mock data"""
    print("=" * 60)
    print("Testing GraphNodeBuilder")
    print("=" * 60)

    # Load data
    print("\n[1] Loading analysis data...")
    loader = GraphDataLoader(base_dir=str(project_root / "output"))
    data = loader.load_all_analysis_results()

    print(f"  Loaded: {len(data['jsp'])} JSP, {len(data['controllers'])} Controllers, "
          f"{len(data['services'])} Services, {len(data['mappers'])} Mappers")

    # Create node builder
    print("\n[2] Creating NodeBuilder...")
    builder = NodeBuilder(loader)

    # Build all nodes
    print("\n[3] Building all nodes...")
    nodes = builder.build_all_nodes()

    # Display summary
    print("\n[4] Node Summary:")
    summary = builder.get_summary()
    print(f"  Total nodes: {summary['total_nodes']}")
    print(f"\n  Nodes by type:")
    for node_type, count in sorted(summary['by_type'].items()):
        print(f"    {node_type}: {count}")

    # Validate node types
    print("\n[5] Validating node types...")
    invalid_types = []
    for node in nodes:
        if node.type not in NODE_TYPES:
            invalid_types.append(node.type)

    if invalid_types:
        print(f"  [ERROR] Found invalid node types: {set(invalid_types)}")
        return False
    else:
        print(f"  [OK] All node types valid")

    # Validate node IDs are unique
    print("\n[6] Validating node ID uniqueness...")
    node_ids = [node.id for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        print(f"  [ERROR] Found duplicate node IDs")
        duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
        print(f"    Duplicates: {set(duplicates)}")
        return False
    else:
        print(f"  [OK] All node IDs unique")

    # Test node samples
    print("\n[7] Sample Nodes:")

    # JSP nodes
    jsp_nodes = builder.get_nodes_by_type("JSP")
    if jsp_nodes:
        print(f"\n  JSP Node Sample:")
        node = jsp_nodes[0]
        print(f"    ID: {node.id}")
        print(f"    Name: {node.name}")
        print(f"    Path: {node.path}")
        print(f"    Metadata: {node.metadata}")

    # Controller nodes
    controller_nodes = builder.get_nodes_by_type("CONTROLLER")
    if controller_nodes:
        print(f"\n  Controller Node Sample:")
        node = controller_nodes[0]
        print(f"    ID: {node.id}")
        print(f"    Name: {node.name}")
        print(f"    Metadata: {node.metadata}")

    # Controller method nodes
    method_nodes = builder.get_nodes_by_type("CONTROLLER_METHOD")
    if method_nodes:
        print(f"\n  Controller Method Node Sample:")
        node = method_nodes[0]
        print(f"    ID: {node.id}")
        print(f"    Name: {node.name}")
        print(f"    HTTP Method: {node.metadata.get('http_method')}")
        print(f"    URL Path: {node.metadata.get('url_path')}")

    # Service nodes
    service_nodes = builder.get_nodes_by_type("SERVICE")
    if service_nodes:
        print(f"\n  Service Node Sample:")
        node = service_nodes[0]
        print(f"    ID: {node.id}")
        print(f"    Name: {node.name}")
        print(f"    Method count: {node.metadata.get('method_count')}")

    # Service method nodes
    service_method_nodes = builder.get_nodes_by_type("SERVICE_METHOD")
    if service_method_nodes:
        print(f"\n  Service Method Node Sample:")
        node = service_method_nodes[0]
        print(f"    ID: {node.id}")
        print(f"    Name: {node.name}")
        print(f"    Transactional: {node.metadata.get('is_transactional')}")

    # Mapper nodes
    mapper_nodes = builder.get_nodes_by_type("MAPPER")
    if mapper_nodes:
        print(f"\n  Mapper Node Sample:")
        node = mapper_nodes[0]
        print(f"    ID: {node.id}")
        print(f"    Name: {node.name}")
        print(f"    Namespace: {node.metadata.get('namespace')}")

    # SQL nodes
    sql_nodes = builder.get_nodes_by_type("SQL_STATEMENT")
    if sql_nodes:
        print(f"\n  SQL Statement Node Sample:")
        node = sql_nodes[0]
        print(f"    ID: {node.id}")
        print(f"    Name: {node.name}")
        print(f"    SQL Type: {node.metadata.get('sql_type')}")
        print(f"    Tables: {node.metadata.get('tables')}")

    # Test node lookup methods
    print("\n[8] Testing node lookup methods:")
    if nodes:
        # Test get_node_by_id
        first_node = nodes[0]
        found_node = builder.get_node_by_id(first_node.id)
        print(f"  get_node_by_id('{first_node.id[:50]}...'): {found_node is not None}")

        # Test get_nodes_by_type
        for node_type in ["JSP", "CONTROLLER", "SERVICE", "MAPPER"]:
            type_nodes = builder.get_nodes_by_type(node_type)
            print(f"  get_nodes_by_type('{node_type}'): {len(type_nodes)} nodes")

    # Test node serialization
    print("\n[9] Testing node serialization:")
    if nodes:
        node_dict = nodes[0].to_dict()
        required_fields = ["id", "type", "name", "path", "color", "shape", "metadata"]
        missing_fields = [f for f in required_fields if f not in node_dict]

        if missing_fields:
            print(f"  [ERROR] Missing fields in serialization: {missing_fields}")
            return False
        else:
            print(f"  [OK] All required fields present in serialization")

    # Verify expected node counts
    print("\n[10] Verifying expected node counts:")

    expected = {
        "JSP": 5,  # 5 JSP files in mock data
        "CONTROLLER": 2,  # 2 controller classes
        "SERVICE": 2,  # 2 service classes
        "MAPPER": 2,  # 2 mapper interfaces
    }

    all_passed = True
    for node_type, expected_count in expected.items():
        actual_count = len(builder.get_nodes_by_type(node_type))
        status = "[OK]" if actual_count == expected_count else "[WARN]"
        print(f"  {status} {node_type}: expected {expected_count}, got {actual_count}")
        if actual_count != expected_count:
            all_passed = False

    # Test result
    print("\n" + "=" * 60)
    if all_passed and len(nodes) > 0:
        print("[OK] GraphNodeBuilder test PASSED")
        print("=" * 60)
        return True
    else:
        print("[ERROR] GraphNodeBuilder test FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_node_builder()
    sys.exit(0 if success else 1)
