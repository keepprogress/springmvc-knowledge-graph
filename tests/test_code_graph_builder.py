#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test CodeGraphBuilder with mock data
"""

import sys
import json
import shutil
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

from mcp_server.tools.code_graph_builder import CodeGraphBuilder


def test_code_graph_builder():
    """Test CodeGraphBuilder with mock data"""
    print("=" * 60)
    print("Testing CodeGraphBuilder")
    print("=" * 60)

    # Use mock project data
    base_dir = project_root / "output"
    output_dir = project_root / "output" / "graph"

    # Clean up previous test output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    print("\n[1] Creating CodeGraphBuilder...")
    builder = CodeGraphBuilder(base_dir=str(base_dir))

    # Build graph
    print("\n[2] Building graph...")
    graph = builder.build_graph()

    # Display graph summary
    print("\n[3] Graph Summary:")
    summary = builder.get_summary()
    print(f"  Total nodes: {summary['nodes']}")
    print(f"  Total edges: {summary['edges']}")
    print(f"  Node types: {summary['node_types']}")
    print(f"  Edge relations: {summary['edge_relations']}")

    # Display statistics
    print("\n[4] Detailed Statistics:")
    stats = builder.statistics

    print(f"\n  Nodes by type:")
    for node_type, count in stats["nodes"]["by_type"].items():
        print(f"    {node_type}: {count}")

    print(f"\n  Edges by relation:")
    for relation, count in stats["edges"]["by_relation"].items():
        print(f"    {relation}: {count}")

    print(f"\n  Edges by confidence:")
    for level, count in stats["edges"]["by_confidence"].items():
        print(f"    {level}: {count}")

    print(f"\n  Coverage:")
    for metric, value in stats["coverage"].items():
        print(f"    {metric}: {value}")

    print(f"\n  Graph properties:")
    for prop, value in stats["graph_properties"].items():
        print(f"    {prop}: {value}")

    # Validate graph
    print("\n[5] Validating graph...")
    is_valid, issues = builder.validate_graph()

    if is_valid:
        print(f"  [OK] Graph validation passed")
    else:
        print(f"  [WARN] Found {len(issues)} validation issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"    - {issue}")

    # Export graph
    print("\n[6] Exporting graph...")
    exported_files = builder.export_graph()

    for file_type, file_path in exported_files.items():
        file_path_obj = Path(file_path)
        if file_path_obj.exists():
            file_size = file_path_obj.stat().st_size
            print(f"  [OK] {file_type}: {file_path} ({file_size} bytes)")
        else:
            print(f"  [ERROR] {file_type} file not created: {file_path}")
            return False

    # Verify exported files
    print("\n[7] Verifying exported files...")

    # Check main graph file
    graph_file = Path(exported_files["graph"])
    with open(graph_file, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)

    assert "metadata" in graph_data, "Graph file missing metadata"
    assert "nodes" in graph_data, "Graph file missing nodes"
    assert "edges" in graph_data, "Graph file missing edges"
    assert "statistics" in graph_data, "Graph file missing statistics"

    assert len(graph_data["nodes"]) == summary["nodes"], "Node count mismatch"
    assert len(graph_data["edges"]) == summary["edges"], "Edge count mismatch"

    print(f"  [OK] Main graph file valid")
    print(f"    - Nodes: {len(graph_data['nodes'])}")
    print(f"    - Edges: {len(graph_data['edges'])}")

    # Check low confidence file
    low_conf_file = Path(exported_files["low_confidence"])
    with open(low_conf_file, 'r', encoding='utf-8') as f:
        low_conf_data = json.load(f)

    assert "metadata" in low_conf_data, "Low confidence file missing metadata"
    assert "edges" in low_conf_data, "Low confidence file missing edges"

    print(f"  [OK] Low confidence edges file valid")
    print(f"    - Low confidence edges: {len(low_conf_data['edges'])}")

    # Check statistics file
    stats_file = Path(exported_files["statistics"])
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats_data = json.load(f)

    assert "nodes" in stats_data, "Statistics file missing nodes"
    assert "edges" in stats_data, "Statistics file missing edges"
    assert "coverage" in stats_data, "Statistics file missing coverage"
    assert "graph_properties" in stats_data, "Statistics file missing graph_properties"

    print(f"  [OK] Statistics file valid")

    # Test specific graph queries
    print("\n[8] Testing graph queries...")

    # Find all mapper methods
    mapper_methods = [
        n for n in graph.nodes
        if graph.nodes[n].get("type") == "MAPPER_METHOD"
    ]
    print(f"  Found {len(mapper_methods)} mapper methods")

    # Find all SQL statements
    sql_statements = [
        n for n in graph.nodes
        if graph.nodes[n].get("type") == "SQL_STATEMENT"
    ]
    print(f"  Found {len(sql_statements)} SQL statements")

    # Check mapper -> SQL edges
    if mapper_methods and sql_statements:
        sample_mapper = mapper_methods[0]
        outgoing_edges = list(graph.successors(sample_mapper))

        if outgoing_edges:
            print(f"\n  Sample mapper method: {sample_mapper}")
            print(f"  Outgoing edges: {len(outgoing_edges)}")

            for target in outgoing_edges[:3]:  # Show first 3
                edge_data = graph.edges[sample_mapper, target]
                print(f"    -> {target}")
                print(f"       Relation: {edge_data.get('relation')}")
                print(f"       Confidence: {edge_data.get('confidence')}")

    # Test path finding
    print("\n[9] Testing path finding...")

    # Find a path from controller method to SQL statement (if exists)
    controller_methods = [
        n for n in graph.nodes
        if graph.nodes[n].get("type") == "CONTROLLER_METHOD"
    ]

    if controller_methods and sql_statements:
        import networkx as nx

        sample_controller = controller_methods[0]
        sample_sql = sql_statements[0]

        # Check if path exists
        if nx.has_path(graph, sample_controller, sample_sql):
            paths = list(nx.all_simple_paths(
                graph, sample_controller, sample_sql, cutoff=5
            ))

            if paths:
                print(f"  Found {len(paths)} path(s) from controller to SQL")
                print(f"  Sample path:")
                for i, node in enumerate(paths[0]):
                    node_type = graph.nodes[node].get("type")
                    node_name = graph.nodes[node].get("name")
                    print(f"    {i+1}. [{node_type}] {node_name}")

                    if i < len(paths[0]) - 1:
                        next_node = paths[0][i+1]
                        edge_data = graph.edges[node, next_node]
                        print(f"       --{edge_data.get('relation')}-->")
        else:
            print(f"  [INFO] No path from controller to SQL (expected - depends on mock data)")
    else:
        print(f"  [INFO] Skipping path test - missing controller methods or SQL statements")

    # Test result
    print("\n" + "=" * 60)
    if summary["nodes"] > 0 and summary["edges"] > 0 and is_valid:
        print("[OK] CodeGraphBuilder test PASSED")
        print("=" * 60)
        return True
    else:
        print("[ERROR] CodeGraphBuilder test FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_code_graph_builder()
    sys.exit(0 if success else 1)
