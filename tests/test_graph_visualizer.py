#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test GraphVisualizer with mock graph
"""

import sys
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
from mcp_server.tools.graph_visualizer import GraphVisualizer


def test_graph_visualizer():
    """Test GraphVisualizer with existing graph"""
    print("=" * 60)
    print("Testing GraphVisualizer")
    print("=" * 60)

    # Build graph first
    print("\n[1] Building graph...")
    builder = CodeGraphBuilder(base_dir=str(project_root / "output"))
    graph = builder.build_graph()

    print(f"  Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    # Create visualizer
    print("\n[2] Creating GraphVisualizer...")
    visualizer = GraphVisualizer(graph)

    # Clean up previous visualizations
    vis_dir = project_root / "output" / "graph" / "visualizations"
    if vis_dir.exists():
        shutil.rmtree(vis_dir)

    # Test 1: PyVis HTML
    print("\n[3] Testing PyVis Interactive HTML...")
    try:
        html_file = visualizer.create_pyvis_html(
            output_file=str(vis_dir / "interactive.html"),
            height="900px",
            width="100%"
        )

        html_path = Path(html_file)
        assert html_path.exists(), f"HTML file not created: {html_file}"

        file_size = html_path.stat().st_size
        assert file_size > 0, "HTML file is empty"

        print(f"  [OK] PyVis HTML created: {html_file}")
        print(f"  [OK] File size: {file_size:,} bytes")

        # Verify HTML content
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        assert '<!DOCTYPE html>' in html_content or '<html' in html_content, "Not valid HTML"
        assert graph.number_of_nodes() > 0, "No nodes in graph"

        print(f"  [OK] HTML content valid")

    except ImportError as e:
        print(f"  [SKIP] PyVis not available: {e}")
    except Exception as e:
        print(f"  [ERROR] PyVis test failed: {e}")
        return False

    # Test 2: Mermaid Diagram
    print("\n[4] Testing Mermaid Diagram...")
    try:
        mermaid_file = visualizer.create_mermaid_diagram(
            output_file=str(vis_dir / "diagram.mmd"),
            max_nodes=30
        )

        mermaid_path = Path(mermaid_file)
        assert mermaid_path.exists(), f"Mermaid file not created: {mermaid_file}"

        file_size = mermaid_path.stat().st_size
        assert file_size > 0, "Mermaid file is empty"

        print(f"  [OK] Mermaid diagram created: {mermaid_file}")
        print(f"  [OK] File size: {file_size:,} bytes")

        # Verify Mermaid content
        with open(mermaid_path, 'r', encoding='utf-8') as f:
            mermaid_content = f.read()

        assert 'graph TD' in mermaid_content, "Not valid Mermaid diagram"
        assert '-->' in mermaid_content, "No edges in Mermaid diagram"

        print(f"  [OK] Mermaid content valid")

    except Exception as e:
        print(f"  [ERROR] Mermaid test failed: {e}")
        return False

    # Test 3: GraphViz DOT
    print("\n[5] Testing GraphViz DOT...")
    try:
        dot_file = visualizer.create_graphviz_dot(
            output_file=str(vis_dir / "graph.dot")
        )

        dot_path = Path(dot_file)
        assert dot_path.exists(), f"DOT file not created: {dot_file}"

        file_size = dot_path.stat().st_size
        assert file_size > 0, "DOT file is empty"

        print(f"  [OK] GraphViz DOT created: {dot_file}")
        print(f"  [OK] File size: {file_size:,} bytes")

        # Verify DOT content
        with open(dot_path, 'r', encoding='utf-8') as f:
            dot_content = f.read()

        assert 'digraph KnowledgeGraph' in dot_content, "Not valid DOT format"
        assert '->' in dot_content, "No edges in DOT file"

        print(f"  [OK] DOT content valid")

    except Exception as e:
        print(f"  [ERROR] GraphViz DOT test failed: {e}")
        return False

    # Test 4: Export all formats
    print("\n[6] Testing export_all_formats()...")
    try:
        all_vis_dir = project_root / "output" / "graph" / "all_visualizations"
        exported = visualizer.export_all_formats(
            output_dir=str(all_vis_dir),
            max_mermaid_nodes=50
        )

        print(f"  Exported {len(exported)} formats:")
        for format_name, file_path in exported.items():
            path = Path(file_path)
            assert path.exists(), f"File not created: {file_path}"
            size = path.stat().st_size
            print(f"    {format_name}: {size:,} bytes")

        # Verify we got all 3 formats
        expected_formats = {"pyvis_html", "mermaid", "graphviz_dot"}
        assert set(exported.keys()) == expected_formats, f"Missing formats: {expected_formats - set(exported.keys())}"

        print(f"  [OK] All formats exported successfully")

    except Exception as e:
        print(f"  [ERROR] export_all_formats failed: {e}")
        return False

    # Test 5: Node/edge color and size calculations
    print("\n[7] Testing helper methods...")

    # Test edge color
    green = visualizer._get_edge_color(0.95)
    assert green == "#27AE60", "High confidence should be green"

    orange = visualizer._get_edge_color(0.75)
    assert orange == "#F39C12", "Medium confidence should be orange"

    red = visualizer._get_edge_color(0.5)
    assert red == "#E74C3C", "Low confidence should be red"

    print(f"  [OK] Edge color calculation works")

    # Test node size
    if graph.number_of_nodes() > 0:
        first_node = list(graph.nodes())[0]
        size = visualizer._calculate_node_size(first_node)
        assert isinstance(size, int), "Node size should be integer"
        assert 20 <= size <= 100, f"Node size out of range: {size}"
        print(f"  [OK] Node size calculation works (size={size})")

    # Test Mermaid ID sanitization
    safe_id = visualizer._sanitize_mermaid_id("CONTROLLER:com.example.UserController")
    assert safe_id[0].isalpha(), "Mermaid ID should start with letter"
    assert safe_id.replace('_', '').isalnum(), "Mermaid ID should be alphanumeric"
    print(f"  [OK] Mermaid ID sanitization works: {safe_id}")

    # Test node selection
    if graph.number_of_nodes() > 10:
        selected = visualizer._select_important_nodes(
            max_nodes=10,
            important_types=["MAPPER_METHOD"]
        )
        assert len(selected) <= 10, "Should respect max_nodes"
        print(f"  [OK] Node selection works ({len(selected)} nodes selected)")

    # Test result
    print("\n" + "=" * 60)
    print("[OK] GraphVisualizer test PASSED")
    print("=" * 60)

    print("\n📊 Visualization Files Created:")
    print(f"  1. Interactive HTML: {vis_dir / 'interactive.html'}")
    print(f"  2. Mermaid Diagram: {vis_dir / 'diagram.mmd'}")
    print(f"  3. GraphViz DOT: {vis_dir / 'graph.dot'}")
    print(f"\n💡 Open the HTML file in a browser to explore the graph interactively!")

    return True


if __name__ == "__main__":
    success = test_graph_visualizer()
    sys.exit(0 if success else 1)
