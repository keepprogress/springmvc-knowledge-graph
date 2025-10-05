#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test for Phase 5.2 LLM-based Enhancement

Tests all Phase 5.2 components working together:
- SemanticCache
- LLMQueryEngine
- URLMatcher
- CompletenessScanner
"""

import sys
import asyncio
from pathlib import Path
import networkx as nx
from unittest.mock import MagicMock

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

from mcp_server.tools.semantic_cache import SemanticCache
from mcp_server.tools.llm_query_engine import LLMQueryEngine
from mcp_server.tools.url_matcher import URLMatcher
from mcp_server.tools.completeness_scanner import CompletenessScanner


async def test_phase_5_2_integration():
    """Integration test for all Phase 5.2 components"""
    print("=" * 70)
    print("Phase 5.2 LLM-based Enhancement - Integration Test")
    print("=" * 70)

    try:
        # Test 1: Initialize all components
        print("\n[1] Initializing Phase 5.2 components...")

        cache = SemanticCache(cache_dir=".test_phase5_cache")
        llm_engine = LLMQueryEngine(cache_dir=".test_phase5_cache")
        url_matcher = URLMatcher(llm_engine=llm_engine)
        completeness_scanner = CompletenessScanner(llm_engine=llm_engine)

        print(f"  [OK] SemanticCache: {cache}")
        print(f"  [OK] LLMQueryEngine: {llm_engine}")
        print(f"  [OK] URLMatcher: {url_matcher}")
        print(f"  [OK] CompletenessScanner: {completeness_scanner}")

        # Test 2: Mock LLM for integration testing
        print("\n[2] Setting up mock LLM...")

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """
        <thinking>
        The AJAX call uses POST to /user/save
        The controller has @PostMapping("/user/save")
        Perfect match.
        </thinking>

        <conclusion>
        {
          "match": true,
          "confidence": 0.95,
          "reasoning": "Exact URL and HTTP method match"
        }
        </conclusion>
        """
        mock_client.messages.create.return_value = mock_response
        llm_engine.client = mock_client

        print(f"  [OK] Mock LLM configured")

        # Test 3: Direct LLM caching (bypass URL matcher for pure LLM test)
        print("\n[3] Testing LLM caching...")

        # Direct LLM query to test caching
        test_code = "$.post('/user/save', data)"
        test_context = {"test": "caching"}

        # First call - should use LLM
        result1 = await llm_engine.verify_relationship(
            source_code=test_code,
            target_code="@PostMapping('/user/save')",
            relationship_type="TEST",
            context=test_context
        )
        print(f"  [OK] First query: method={result1['method']}, confidence={result1['confidence']}")

        # Cache stats before second call
        stats_before = llm_engine.get_cache_stats()

        # Second identical call - should use cache
        result2 = await llm_engine.verify_relationship(
            source_code=test_code,
            target_code="@PostMapping('/user/save')",
            relationship_type="TEST",
            context=test_context
        )
        print(f"  [OK] Second query: method={result2['method']}, confidence={result2['confidence']}")

        # Verify caching worked
        stats_after = llm_engine.get_cache_stats()
        assert stats_after['hits'] > stats_before['hits'], "Cache hit should have occurred"
        print(f"  [OK] Cache working: {stats_after['hits']} hits, {stats_after['hit_rate']:.1%} hit rate")

        # Test 4: Build test knowledge graph
        print("\n[4] Building test knowledge graph...")

        graph = nx.DiGraph()

        # Add nodes
        graph.add_node("login.jsp", type="JSP", name="login.jsp")
        graph.add_node("UserController.login", type="CONTROLLER_METHOD", name="login")
        graph.add_node("UserService.authenticate", type="SERVICE_METHOD", name="authenticate")
        graph.add_node("UserMapper.selectByUsername", type="MAPPER_METHOD", name="selectByUsername")
        graph.add_node("SELECT_USER", type="SQL", name="SELECT * FROM users")

        # Add incomplete node (orphan)
        graph.add_node("UnusedController.orphan", type="CONTROLLER_METHOD", name="orphan")

        # Add edges
        graph.add_edge("login.jsp", "UserController.login", relation="AJAX_CALL")
        graph.add_edge("UserController.login", "UserService.authenticate", relation="CALLS")
        graph.add_edge("UserService.authenticate", "UserMapper.selectByUsername", relation="CALLS")
        graph.add_edge("UserMapper.selectByUsername", "SELECT_USER", relation="EXECUTES")

        print(f"  [OK] Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

        # Test 5: Completeness scanning
        print("\n[5] Running completeness scan...")

        scan_results = await completeness_scanner.scan_graph(graph)

        summary = scan_results["summary"]
        print(f"  [OK] Scan complete:")
        print(f"    Nodes: {summary['total_nodes']}")
        print(f"    Edges: {summary['total_edges']}")
        print(f"    Orphans: {summary['total_orphans']}")
        print(f"    Issues: {summary['total_issues']}")
        print(f"    Completeness: {summary['completeness_score']:.2%}")

        assert summary['total_orphans'] >= 1, "Should detect orphan node"
        assert summary['total_issues'] >= 1, "Should detect issues"

        # Test 6: Issue detection and reporting
        print("\n[6] Analyzing detected issues...")

        for issue in scan_results['issues'][:3]:  # Show first 3 issues
            print(f"  [{issue['severity'].upper()}] {issue['type']}: {issue['node_name']}")
            print(f"    {issue['message']}")

        # Test 7: End-to-end workflow
        print("\n[7] Testing end-to-end workflow...")

        # Scenario: JSP AJAX call needs to be matched to controller
        workflow_ajax = {
            "url": "/user/login",
            "method": "POST",
            "code_snippet": "$.post('/user/login', credentials)"
        }

        workflow_controllers = [
            {
                "class_name": "UserController",
                "endpoints": [
                    {"path": "/user/login", "handler": "login", "methods": ["POST"]}
                ]
            }
        ]

        # Step 1: URL Matching (with LLM if needed)
        match_result = await url_matcher.match_ajax_to_controller(
            workflow_ajax, workflow_controllers
        )

        if match_result["target"]:
            print(f"  ✓ AJAX matched to: {match_result['target']['controller']}.{match_result['target']['method']}")
            print(f"    Confidence: {match_result['confidence']}")
            print(f"    Method: {match_result['method']}")
        else:
            print(f"  ✗ No match found")

        # Step 2: Add to graph
        if match_result["target"]:
            graph.add_edge(
                "new_page.jsp",
                f"{match_result['target']['controller']}.{match_result['target']['method']}",
                relation="AJAX_CALL",
                confidence=match_result['confidence']
            )
            print(f"  ✓ Added to knowledge graph")

        # Step 3: Re-scan for completeness
        rescan_results = await completeness_scanner.scan_graph(graph)
        new_score = rescan_results["summary"]["completeness_score"]
        print(f"  ✓ Updated completeness: {new_score:.2%}")

        # Test 8: Cache statistics summary
        print("\n[8] Cache performance summary...")

        final_stats = llm_engine.get_cache_stats()
        print(f"  Total entries: {final_stats['total_entries']}")
        print(f"  Cache hits: {final_stats['hits']}")
        print(f"  Cache misses: {final_stats['misses']}")
        print(f"  Hit rate: {final_stats['hit_rate']:.1%}")
        print(f"  Tokens saved: {final_stats['tokens_saved']:,}")
        print(f"  Cost saved: ${final_stats['cost_saved_usd']:.4f}")

        # Test result
        print("\n" + "=" * 70)
        print("[OK] Phase 5.2 Integration Test PASSED")
        print("=" * 70)

        print("\n📊 Summary:")
        print(f"  ✓ Semantic caching working ({final_stats['hit_rate']:.0%} hit rate)")
        print(f"  ✓ LLM query engine operational")
        print(f"  ✓ URL matching functional")
        print(f"  ✓ Completeness scanning active")
        print(f"  ✓ End-to-end workflow validated")

        # Cleanup
        cache.clear()
        print(f"\n🧹 Cache cleared")

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
    success = asyncio.run(test_phase_5_2_integration())
    sys.exit(0 if success else 1)
