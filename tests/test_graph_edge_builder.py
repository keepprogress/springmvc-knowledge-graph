#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GraphEdgeBuilder with mock data
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
from mcp_server.tools.graph_node_builder import NodeBuilder
from mcp_server.tools.graph_edge_builder import EdgeBuilder, Edge, EDGE_TYPES


def test_edge_builder():
    """Test EdgeBuilder with mock data"""
    print("=" * 60)
    print("Testing GraphEdgeBuilder")
    print("=" * 60)

    # Load data and build nodes first
    print("\n[1] Loading data and building nodes...")
    loader = GraphDataLoader(base_dir=str(project_root / "output"))
    loader.load_all_analysis_results()

    node_builder = NodeBuilder(loader)
    nodes = node_builder.build_all_nodes()
    print(f"  Loaded {len(nodes)} nodes")

    # Create edge builder
    print("\n[2] Creating EdgeBuilder...")
    edge_builder = EdgeBuilder(node_builder)

    # Build all edges
    print("\n[3] Building all edges...")
    edges = edge_builder.build_all_edges()

    # Display summary
    print("\n[4] Edge Summary:")
    summary = edge_builder.get_summary()
    print(f"  Total edges: {summary['total_edges']}")
    print(f"  Average confidence: {summary['average_confidence']:.2f}")
    print(f"\n  Edges by type:")
    for edge_type, count in sorted(summary['by_type'].items()):
        print(f"    {edge_type}: {count}")

    # Validate edge types
    print("\n[5] Validating edge types...")
    invalid_types = []
    for edge in edges:
        if edge.type not in EDGE_TYPES:
            invalid_types.append(edge.type)

    if invalid_types:
        print(f"  [ERROR] Found invalid edge types: {set(invalid_types)}")
        return False
    else:
        print(f"  [OK] All edge types valid")

    # Validate edge confidence
    print("\n[6] Validating edge confidence scores...")
    invalid_confidence = []
    for edge in edges:
        if not 0.0 <= edge.confidence <= 1.0:
            invalid_confidence.append(edge)

    if invalid_confidence:
        print(f"  [ERROR] Found {len(invalid_confidence)} edges with invalid confidence")
        return False
    else:
        print(f"  [OK] All confidence scores valid (0.0-1.0)")

    # Test edge samples
    print("\n[7] Sample Edges:")

    # Mapper -> SQL edges
    executes_edges = edge_builder.get_edges_by_type("EXECUTES")
    if executes_edges:
        print(f"\n  EXECUTES Edge Sample (Mapper -> SQL):")
        edge = executes_edges[0]
        print(f"    Source: {edge.source}")
        print(f"    Target: {edge.target}")
        print(f"    Confidence: {edge.confidence}")
        print(f"    Metadata: {edge.metadata}")

    # Service -> Mapper edges
    uses_edges = edge_builder.get_edges_by_type("USES")
    if uses_edges:
        print(f"\n  USES Edge Sample (Service -> Mapper):")
        edge = uses_edges[0]
        print(f"    Source: {edge.source}")
        print(f"    Target: {edge.target}")
        print(f"    Confidence: {edge.confidence}")
    else:
        print(f"\n  [INFO] No USES edges (Service -> Mapper) created")

    # Test edge equality and hashing
    print("\n[8] Testing edge equality and hashing:")
    if len(edges) >= 2:
        edge1 = edges[0]
        edge2 = Edge(
            source=edge1.source,
            target=edge1.target,
            edge_type=edge1.type,
            confidence=0.5  # Different confidence
        )
        edge3 = Edge(
            source="different",
            target="nodes",
            edge_type=edge1.type
        )

        assert edge1 == edge2, "Edges with same source/target/type should be equal"
        assert edge1 != edge3, "Edges with different source/target should not be equal"
        assert hash(edge1) == hash(edge2), "Equal edges should have same hash"

        print(f"  [OK] Edge equality works correctly")
        print(f"  [OK] Edge hashing works correctly")

    # Test edge lookup methods
    print("\n[9] Testing edge lookup methods:")
    if edges:
        first_edge = edges[0]

        # Test get_edges_from_node
        from_edges = edge_builder.get_edges_from_node(first_edge.source)
        print(f"  get_edges_from_node('{first_edge.source[:50]}...'): {len(from_edges)} edges")

        # Test get_edges_to_node
        to_edges = edge_builder.get_edges_to_node(first_edge.target)
        print(f"  get_edges_to_node('{first_edge.target[:50]}...'): {len(to_edges)} edges")

        # Test get_edges_by_type
        for edge_type in ["EXECUTES", "USES", "QUERIES", "MODIFIES"]:
            type_edges = edge_builder.get_edges_by_type(edge_type)
            if type_edges:
                print(f"  get_edges_by_type('{edge_type}'): {len(type_edges)} edges")

    # Test edge serialization
    print("\n[10] Testing edge serialization:")
    if edges:
        edge_dict = edges[0].to_dict()
        required_fields = ["source", "target", "type", "confidence", "source_type", "description", "metadata"]
        missing_fields = [f for f in required_fields if f not in edge_dict]

        if missing_fields:
            print(f"  [ERROR] Missing fields in serialization: {missing_fields}")
            return False
        else:
            print(f"  [OK] All required fields present in serialization")

    # Verify expected edge types exist
    print("\n[11] Verifying expected edge types:")
    expected_types = ["EXECUTES"]  # At minimum, should have Mapper->SQL edges

    all_found = True
    for edge_type in expected_types:
        count = len(edge_builder.get_edges_by_type(edge_type))
        status = "[OK]" if count > 0 else "[WARN]"
        print(f"  {status} {edge_type}: {count} edges")
        if count == 0:
            all_found = False

    # Test result
    print("\n" + "=" * 60)
    if len(edges) > 0 and not invalid_types and not invalid_confidence:
        print("[OK] GraphEdgeBuilder test PASSED")
        print("=" * 60)
        return True
    else:
        print("[ERROR] GraphEdgeBuilder test FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_edge_builder()
    sys.exit(0 if success else 1)
