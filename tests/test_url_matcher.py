#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test URLMatcher

Tests URL matching for AJAX to Controller relationships
"""

import sys
import asyncio
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

from mcp_server.tools.url_matcher import URLMatcher


async def test_url_matcher():
    """Test URLMatcher functionality"""
    print("=" * 60)
    print("Testing URLMatcher")
    print("=" * 60)

    try:
        # Initialize matcher (without LLM for basic tests)
        matcher = URLMatcher(llm_engine=None)

        # Test 1: URL normalization
        print("\n[1] Testing URL normalization...")

        test_cases = [
            # (input, expected_output)
            ("'${ctx}/user/list'", "/user/list"),
            ("${pageContext.request.contextPath}/user/list", "/user/list"),
            ("/myapp/user/list?id=123", "/myapp/user/list"),
            ("'/user/' + id + '/edit'", "/user/{id}/edit"),
            ("'/user/' + userId", "/user/{userId}"),
            ("'user/list'", "/user/list"),  # Add leading /
            ("'/user//list'", "/user/list"),  # Remove duplicate /
        ]

        for input_url, expected in test_cases:
            result = matcher._normalize_ajax_url(input_url)
            assert result == expected, f"Failed: {input_url} -> {result} (expected {expected})"
            print(f"  [OK] {input_url:50s} -> {result}")

        # Test 2: URL pattern matching
        print("\n[2] Testing URL pattern matching...")

        pattern_test_cases = [
            # (ajax_url, mapping_path, should_match)
            ("/user/list", "/user/list", True),
            ("/user/123", "/user/{id}", True),
            ("/user/123", "/user/{userId}", True),
            ("/user/edit", "/user/{action}", True),
            ("/user/123/edit", "/user/{id}/edit", True),
            ("/user/123/edit", "/user/{id}/{action}", True),
            ("/user/anything", "/user/*", True),
            ("/user/a/b/c", "/user/**", True),
            ("/user/list", "/order/list", False),
            ("/user", "/user/list", False),
            ("/user/123/edit", "/user/{id}", False),
        ]

        for ajax_url, mapping_path, should_match in pattern_test_cases:
            result = matcher._url_matches(ajax_url, mapping_path)
            assert result == should_match, \
                f"Failed: {ajax_url} vs {mapping_path} -> {result} (expected {should_match})"
            match_str = "✓ match" if result else "✗ no match"
            print(f"  [OK] {ajax_url:25s} vs {mapping_path:25s} -> {match_str}")

        # Test 3: Find candidate controllers - exact match
        print("\n[3] Testing candidate finding (exact match)...")

        controllers = [
            {
                "class_name": "UserController",
                "endpoints": [
                    {"path": "/user/list", "handler": "listUsers", "methods": ["GET"]},
                    {"path": "/user/save", "handler": "saveUser", "methods": ["POST"]},
                    {"path": "/user/{id}", "handler": "getUser", "methods": ["GET"]},
                ]
            },
            {
                "class_name": "OrderController",
                "endpoints": [
                    {"path": "/order/list", "handler": "listOrders", "methods": ["GET"]},
                ]
            }
        ]

        candidates = matcher._find_candidate_controllers("/user/list", "GET", controllers)
        # Note: /user/list matches both /user/list AND /user/{id}, so we get 2 candidates
        assert len(candidates) >= 1, f"Should find at least 1 candidate, found {len(candidates)}"
        # First should be exact match
        exact_matches = [c for c in candidates if c["path"] == "/user/list"]
        assert len(exact_matches) == 1, "Should have 1 exact match"
        assert exact_matches[0]["controller"] == "UserController"
        assert exact_matches[0]["method"] == "listUsers"
        print(f"  [OK] Found matches: {len(candidates)} candidates ({len(exact_matches)} exact)")

        # Test 4: Find candidates - path variable
        print("\n[4] Testing candidate finding (path variable)...")

        candidates = matcher._find_candidate_controllers("/user/123", "GET", controllers)
        assert len(candidates) == 1, f"Should find 1 candidate, found {len(candidates)}"
        assert candidates[0]["path"] == "/user/{id}"
        print(f"  [OK] Path variable match: {candidates[0]['path']}")

        # Test 5: Find candidates - HTTP method filtering
        print("\n[5] Testing HTTP method filtering...")

        # /user/save GET will match /user/{id} GET (where id="save")
        candidates = matcher._find_candidate_controllers("/user/save", "GET", controllers)
        # Should match /user/{id} with GET
        path_variable_matches = [c for c in candidates if '{' in c["path"]]
        assert len(path_variable_matches) >= 1, f"Should match path variable endpoint"
        print(f"  [OK] GET /user/save: {len(candidates)} candidates (path variable match)")

        # /user/save POST will match both /user/save POST and /user/{id} GET (wrong method)
        candidates = matcher._find_candidate_controllers("/user/save", "POST", controllers)
        exact_post = [c for c in candidates if c["path"] == "/user/save"]
        assert len(exact_post) == 1, f"Should have exact POST match"
        print(f"  [OK] POST /user/save: {len(candidates)} candidates (exact match)")

        # Test 6: Match AJAX to controller (single match)
        print("\n[6] Testing AJAX to Controller matching (single match)...")

        # Use /order/list which only has one match (no path variables to confuse it)
        ajax_call = {
            "url": "${ctx}/order/list",
            "method": "GET",
            "code_snippet": "$.get('${ctx}/order/list', function(data) {...})"
        }

        result = await matcher.match_ajax_to_controller(ajax_call, controllers)

        assert result["target"] is not None, "Should find target"
        assert result["target"]["controller"] == "OrderController"
        assert result["method"] == "pattern_match"
        assert result["confidence"] >= 0.9

        print(f"  [OK] Match found:")
        print(f"    Controller: {result['target']['controller']}")
        print(f"    Method: {result['target']['method']}")
        print(f"    Confidence: {result['confidence']}")
        print(f"    Match method: {result['method']}")

        # Test 7: Match AJAX to controller (no match)
        print("\n[7] Testing AJAX to Controller matching (no match)...")

        ajax_call_no_match = {
            "url": "/api/external/data",
            "method": "GET",
            "code_snippet": "$.get('/api/external/data')"
        }

        result = await matcher.match_ajax_to_controller(ajax_call_no_match, controllers)

        assert result["target"] is None, "Should not find target"
        assert result["method"] == "no_match"
        assert result["confidence"] == 0.0

        print(f"  [OK] No match found (as expected)")
        print(f"    Reasoning: {result['reasoning']}")

        # Test 8: Dynamic URL construction
        print("\n[8] Testing dynamic URL construction...")

        ajax_call_dynamic = {
            "url": "'/user/' + userId + '/edit'",
            "method": "GET",
            "code_snippet": "var url = '/user/' + userId + '/edit';"
        }

        # Add endpoint for this pattern
        controllers[0]["endpoints"].append({
            "path": "/user/{id}/edit",
            "handler": "editUser",
            "methods": ["GET"]
        })

        result = await matcher.match_ajax_to_controller(ajax_call_dynamic, controllers)

        assert result["target"] is not None, "Should match dynamic URL"
        assert result["target"]["path"] == "/user/{id}/edit"

        print(f"  [OK] Dynamic URL matched:")
        print(f"    Original: '/user/' + userId + '/edit'")
        print(f"    Normalized: /user/{{userId}}/edit")
        print(f"    Matched to: {result['target']['path']}")

        # Test 9: Batch matching
        print("\n[9] Testing batch matching...")

        # Use URLs that each have only one match (no ambiguity)
        ajax_calls = [
            {"url": "${ctx}/order/list", "method": "GET", "code_snippet": "..."},
            {"url": "/user/save", "method": "POST", "code_snippet": "..."},
            {"url": "/user/999/edit", "method": "GET", "code_snippet": "..."},
        ]

        # batch_match is async
        results = await matcher.batch_match(ajax_calls, controllers)

        assert len(results) == 3, f"Should have 3 results, got {len(results)}"
        assert results[0]["target"]["controller"] == "OrderController"
        assert results[1]["target"]["controller"] == "UserController"
        assert results[2]["target"]["controller"] == "UserController"

        print(f"  [OK] Batch matching: {len(results)} results")
        for i, result in enumerate(results):
            if result["target"]:
                print(f"    [{i+1}] -> {result['target']['controller']}.{result['target']['method']}")
            else:
                print(f"    [{i+1}] -> No match")

        # Test result
        print("\n" + "=" * 60)
        print("[OK] URLMatcher test PASSED")
        print("=" * 60)

        return True

    except AssertionError as e:
        print(f"\n[ERROR] Assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_url_matcher())
    sys.exit(0 if success else 1)
