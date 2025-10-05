#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test edge cases for GraphDataLoader and GraphNodeBuilder
"""

import sys
import json
import tempfile
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
from mcp_server.tools.graph_node_builder import NodeBuilder, Node


def test_empty_directory():
    """Test GraphDataLoader with empty directory"""
    print("=" * 60)
    print("Test 1: Empty Directory")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create empty analysis directories
        analysis_dir = Path(tmpdir) / "analysis"
        analysis_dir.mkdir(parents=True)
        (analysis_dir / "jsp").mkdir()
        (analysis_dir / "controllers").mkdir()
        (analysis_dir / "services").mkdir()
        (analysis_dir / "mappers").mkdir()

        loader = GraphDataLoader(base_dir=tmpdir)
        data = loader.load_all_analysis_results()

        # Verify all data is empty
        assert len(data["jsp"]) == 0, "JSP should be empty"
        assert len(data["controllers"]) == 0, "Controllers should be empty"
        assert len(data["services"]) == 0, "Services should be empty"
        assert len(data["mappers"]) == 0, "Mappers should be empty"

        # Validation should fail
        is_valid = loader.validate_data()
        assert not is_valid, "Validation should fail for empty data"
        assert len(loader.validation_issues) > 0, "Should have validation issues"

        print(f"  [OK] Empty directory handled correctly")
        print(f"  [OK] Validation issues: {loader.validation_issues}")
        return True


def test_corrupted_json():
    """Test GraphDataLoader with corrupted JSON file"""
    print("\n" + "=" * 60)
    print("Test 2: Corrupted JSON File")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        analysis_dir = Path(tmpdir) / "analysis"
        jsp_dir = analysis_dir / "jsp"
        jsp_dir.mkdir(parents=True)

        # Create one valid JSON
        valid_file = jsp_dir / "valid.json"
        with open(valid_file, 'w', encoding='utf-8') as f:
            json.dump({"file": "test.jsp", "forms": []}, f)

        # Create one corrupted JSON
        corrupted_file = jsp_dir / "corrupted.json"
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write("{invalid json content")

        loader = GraphDataLoader(base_dir=tmpdir)
        data = loader.load_all_analysis_results()

        # Should load the valid file
        assert len(data["jsp"]) == 1, "Should load 1 valid JSP file"

        # Should have validation issues for corrupted file
        assert len(loader.validation_issues) > 0, "Should report corrupted file"

        print(f"  [OK] Loaded {len(data['jsp'])} valid files")
        print(f"  [OK] Validation issues: {len(loader.validation_issues)}")
        return True


def test_missing_required_fields():
    """Test GraphDataLoader with missing required fields"""
    print("\n" + "=" * 60)
    print("Test 3: Missing Required Fields")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        analysis_dir = Path(tmpdir) / "analysis"
        controller_dir = analysis_dir / "controllers"
        controller_dir.mkdir(parents=True)

        # Create JSON with missing required fields
        invalid_file = controller_dir / "invalid.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump({
                # Missing "class_name"
                "package": "com.example",
                # Missing "methods"
            }, f)

        loader = GraphDataLoader(base_dir=tmpdir)
        data = loader.load_all_analysis_results()

        # Should load but validation should fail
        assert len(data["controllers"]) == 1, "Should load file"

        is_valid = loader.validate_data()
        assert not is_valid, "Validation should fail"
        assert len(loader.validation_issues) > 0, "Should have validation issues"

        print(f"  [OK] Detected missing required fields")
        print(f"  [OK] Validation issues: {loader.validation_issues}")
        return True


def test_node_equality_and_hashing():
    """Test Node __eq__ and __hash__ methods"""
    print("\n" + "=" * 60)
    print("Test 4: Node Equality and Hashing")
    print("=" * 60)

    # Create two nodes with same ID
    node1 = Node(
        id="TEST:node1",
        node_type="CONTROLLER",
        name="TestNode",
        path="/test/path"
    )

    node2 = Node(
        id="TEST:node1",
        node_type="CONTROLLER",
        name="DifferentName",  # Different name
        path="/different/path"  # Different path
    )

    # Create node with different ID
    node3 = Node(
        id="TEST:node2",
        node_type="CONTROLLER",
        name="TestNode",
        path="/test/path"
    )

    # Test equality
    assert node1 == node2, "Nodes with same ID should be equal"
    assert node1 != node3, "Nodes with different IDs should not be equal"
    assert node1 != "not a node", "Node should not equal non-Node object"

    # Test hashing
    assert hash(node1) == hash(node2), "Nodes with same ID should have same hash"

    # Test set operations
    node_set = {node1, node2, node3}
    assert len(node_set) == 2, "Set should deduplicate nodes with same ID"

    # Test dict operations
    node_dict = {node1: "value1", node2: "value2", node3: "value3"}
    assert len(node_dict) == 2, "Dict should use node ID for keys"
    assert node_dict[node1] == "value2", "Should update value for same ID"

    print(f"  [OK] Node equality works correctly")
    print(f"  [OK] Node hashing works correctly")
    print(f"  [OK] Set deduplication works: {len(node_set)} unique nodes")
    print(f"  [OK] Dict keying works correctly")
    return True


def test_sql_callable_detection():
    """Test SQL callable detection in NodeBuilder"""
    print("\n" + "=" * 60)
    print("Test 5: SQL Callable Detection")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock mapper data with callable statement
        analysis_dir = Path(tmpdir) / "analysis"
        mapper_dir = analysis_dir / "mappers"
        mapper_dir.mkdir(parents=True)

        mapper_data = {
            "mapper_name": "TestMapper",
            "interface": {
                "file": "TestMapper.java",
                "package": "com.example.mapper",
                "methods": []
            },
            "xml": {
                "file": "TestMapper.xml",
                "namespace": "com.example.mapper.TestMapper",
                "statements": [
                    {
                        "id": "callProcedure",
                        "type": "SELECT",
                        "sql": "{CALL SYNC_USER_DATA(#{userId, mode=IN, jdbcType=NUMERIC})}",
                        "parameters": ["userId"],
                        "tables": [],
                        "dynamic_sql": False
                    },
                    {
                        "id": "normalQuery",
                        "type": "SELECT",
                        "sql": "SELECT * FROM users WHERE id = #{id}",
                        "parameters": ["id"],
                        "tables": ["users"],
                        "dynamic_sql": False
                    }
                ],
                "result_maps": [],
                "sql_fragments": []
            }
        }

        mapper_file = mapper_dir / "TestMapper.json"
        with open(mapper_file, 'w', encoding='utf-8') as f:
            json.dump(mapper_data, f)

        # Load and build nodes
        loader = GraphDataLoader(base_dir=tmpdir)
        loader.load_all_analysis_results()

        builder = NodeBuilder(loader)
        nodes = builder.build_all_nodes()

        # Find SQL nodes
        sql_nodes = builder.get_nodes_by_type("SQL_STATEMENT")
        assert len(sql_nodes) == 2, "Should have 2 SQL nodes"

        # Check callable detection
        callable_node = builder.get_node_by_id("SQL:com.example.mapper.TestMapper.callProcedure")
        assert callable_node is not None, "Should find callable node"
        assert callable_node.metadata["is_callable"], "Should detect as callable"
        assert callable_node.metadata["procedure_name"] == "SYNC_USER_DATA", "Should extract procedure name"

        # Check normal query
        normal_node = builder.get_node_by_id("SQL:com.example.mapper.TestMapper.normalQuery")
        assert normal_node is not None, "Should find normal query node"
        assert not normal_node.metadata["is_callable"], "Should not detect as callable"
        assert normal_node.metadata["procedure_name"] is None, "Should not have procedure name"

        print(f"  [OK] Callable detection works correctly")
        print(f"  [OK] Procedure name extraction: {callable_node.metadata['procedure_name']}")
        print(f"  [OK] Normal query correctly identified")
        return True


def test_incomplete_project_warnings():
    """Test validation warnings for incomplete projects"""
    print("\n" + "=" * 60)
    print("Test 6: Incomplete Project Warnings")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create project with JSP but no controllers
        analysis_dir = Path(tmpdir) / "analysis"
        jsp_dir = analysis_dir / "jsp"
        jsp_dir.mkdir(parents=True)

        jsp_file = jsp_dir / "test.json"
        with open(jsp_file, 'w', encoding='utf-8') as f:
            json.dump({"file": "test.jsp", "forms": []}, f)

        loader = GraphDataLoader(base_dir=tmpdir)
        loader.load_all_analysis_results()

        is_valid = loader.validate_data()

        # Should have warnings about orphaned JSP and missing controllers
        warnings = [issue for issue in loader.validation_issues if issue.startswith("Warning")]
        assert len(warnings) > 0, "Should have warnings"

        print(f"  [OK] Generated {len(warnings)} warnings for incomplete project")
        for warning in warnings:
            print(f"  [OK] Warning: {warning}")
        return True


def run_all_tests():
    """Run all edge case tests"""
    print("\n" + "=" * 60)
    print("Testing Edge Cases for Graph Components")
    print("=" * 60)

    tests = [
        ("Empty Directory", test_empty_directory),
        ("Corrupted JSON", test_corrupted_json),
        ("Missing Required Fields", test_missing_required_fields),
        ("Node Equality & Hashing", test_node_equality_and_hashing),
        ("SQL Callable Detection", test_sql_callable_detection),
        ("Incomplete Project Warnings", test_incomplete_project_warnings),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except AssertionError as e:
            print(f"\n[ERROR] {name} failed: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"\n[ERROR] {name} error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("EDGE CASE TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print("\n" + "=" * 60)
    if passed == total:
        print(f"[OK] All {total} edge case tests PASSED")
        print("=" * 60)
        return True
    else:
        print(f"[ERROR] {total - passed}/{total} tests FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
