#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test LLMQueryEngine

Tests LLM query engine with mocked responses (no actual API calls)
"""

import sys
import shutil
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

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

from mcp_server.tools.llm_query_engine import LLMQueryEngine


async def test_llm_query_engine():
    """Test LLMQueryEngine with mocked API"""
    print("=" * 60)
    print("Testing LLMQueryEngine")
    print("=" * 60)

    # Create temporary cache directory
    temp_dir = tempfile.mkdtemp()
    cache_dir = Path(temp_dir) / "test_llm_cache"

    try:
        # Test 1: Initialization without API key
        print("\n[1] Testing initialization...")
        engine = LLMQueryEngine(cache_dir=str(cache_dir))
        assert engine.cache is not None, "Cache should be initialized"
        print(f"  [OK] Engine initialized: {engine}")

        # Test 2: Prompt building
        print("\n[2] Testing prompt building...")

        source_code = """
        $.post('${ctx}/user/save', {
            id: userId,
            name: userName
        }, function(result) {
            alert('Saved');
        });
        """

        target_code = """
        @PostMapping("/user/save")
        public Result saveUser(@RequestBody User user) {
            return userService.saveUser(user);
        }
        """

        context = {
            "source_type": "JSP_AJAX",
            "target_type": "CONTROLLER_METHOD",
            "http_method": "POST"
        }

        prompt = engine._build_verification_prompt(
            source_code, target_code, "AJAX_TO_CONTROLLER", context
        )

        assert "<task>" in prompt, "Prompt should have XML structure"
        assert "<context>" in prompt, "Prompt should include context"
        assert "<requirements>" in prompt, "Prompt should include requirements"
        assert "<examples>" in prompt, "Prompt should include examples"
        assert "AJAX_TO_CONTROLLER" in prompt, "Prompt should mention relationship type"

        print(f"  [OK] Prompt structure valid ({len(prompt)} chars)")
        print(f"  [OK] Contains XML tags: <task>, <context>, <requirements>, <examples>")

        # Test 3: Few-shot examples
        print("\n[3] Testing few-shot examples...")

        examples = engine._get_few_shot_examples("AJAX_TO_CONTROLLER")
        assert "positive" in examples.lower(), "Should include positive examples"
        assert "negative" in examples.lower(), "Should include negative examples"
        assert "edge_case" in examples.lower() or "edge case" in examples.lower(), "Should include edge cases"

        print(f"  [OK] Few-shot examples generated ({len(examples)} chars)")

        # Test 4: Code context limiting
        print("\n[4] Testing code context limiting...")

        long_code = "\n".join([f"line {i}" for i in range(100)])
        limited = engine._limit_code_context(long_code, max_lines=15)

        lines = limited.split('\n')
        assert len(lines) <= 16, f"Should limit to max_lines + 1 (for indicator), got {len(lines)}"
        assert "more lines" in limited, "Should indicate truncation"

        print(f"  [OK] Code context limited: 100 lines -> {len(lines)} lines")

        # Test 5: Mock LLM query
        print("\n[5] Testing LLM query with mock...")

        # Mock the client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """
        <thinking>
        The AJAX call uses POST method to '/user/save'
        The controller has @PostMapping("/user/save")
        Both URLs and methods match exactly
        </thinking>

        <conclusion>
        {
          "match": true,
          "confidence": 0.95,
          "reasoning": "URL pattern and HTTP method match exactly"
        }
        </conclusion>
        """

        mock_client.messages.create.return_value = mock_response
        engine.client = mock_client

        result = await engine.verify_relationship(
            source_code=source_code,
            target_code=target_code,
            relationship_type="AJAX_TO_CONTROLLER",
            context=context
        )

        assert result is not None, "Should return result"
        assert result["match"] is True, "Should detect match"
        assert result["confidence"] == 0.95, f"Should have confidence 0.95, got {result['confidence']}"
        assert "method" in result, "Should include method (llm or cache)"
        assert result["method"] == "llm", "First call should use LLM"

        print(f"  [OK] LLM query successful")
        print(f"    Match: {result['match']}")
        print(f"    Confidence: {result['confidence']}")
        print(f"    Method: {result['method']}")

        # Test 6: Cache hit on second query
        print("\n[6] Testing cache hit...")

        # Query same relationship again
        result2 = await engine.verify_relationship(
            source_code=source_code,
            target_code=target_code,
            relationship_type="AJAX_TO_CONTROLLER",
            context=context
        )

        assert result2["method"] == "cache", "Second call should use cache"
        assert result2["match"] == result["match"], "Cached result should match original"

        print(f"  [OK] Cache hit detected")
        print(f"    Method: {result2['method']}")

        # Test 7: Cache statistics
        print("\n[7] Testing cache statistics...")

        stats = engine.get_cache_stats()
        assert stats["total_entries"] >= 1, "Should have at least 1 cached entry"
        assert stats["hits"] >= 1, "Should have at least 1 cache hit"

        print(f"  [OK] Cache statistics:")
        print(f"    Entries: {stats['total_entries']}")
        print(f"    Hits: {stats['hits']}")
        print(f"    Misses: {stats['misses']}")
        print(f"    Hit rate: {stats['hit_rate']:.1%}")

        # Test 8: Different relationship types
        print("\n[8] Testing different relationship types...")

        relationship_types = [
            "CONTROLLER_TO_SERVICE",
            "SERVICE_TO_MAPPER",
            "MAPPER_TO_SQL"
        ]

        for rel_type in relationship_types:
            examples = engine._get_few_shot_examples(rel_type)
            assert len(examples) > 0, f"Should have examples for {rel_type}"
            print(f"  [OK] {rel_type}: {len(examples)} chars of examples")

        # Test 9: Error handling
        print("\n[9] Testing error handling...")

        # Test with malformed LLM response
        mock_response.content[0].text = "This is not valid JSON"
        result_error = await engine.verify_relationship(
            source_code="test",
            target_code="test",
            relationship_type="TEST",
            context={}
        )

        assert result_error["match"] is False, "Should return False on parse error"
        assert "Failed to parse" in result_error["reasoning"], "Should explain error"

        print(f"  [OK] Error handling works")

        # Test 10: No API key scenario
        print("\n[10] Testing no API key scenario...")

        engine_no_key = LLMQueryEngine(cache_dir=str(cache_dir))
        engine_no_key.client = None

        result_no_key = await engine_no_key.verify_relationship(
            source_code="test",
            target_code="test",
            relationship_type="TEST",
            context={}
        )

        assert result_no_key["method"] == "error", "Should return error method"
        assert "not available" in result_no_key["reasoning"].lower(), "Should explain unavailability"

        print(f"  [OK] No API key scenario handled")

        # Test result
        print("\n" + "=" * 60)
        print("[OK] LLMQueryEngine test PASSED")
        print("=" * 60)

        print(f"\n📊 Final Engine State: {engine}")
        print(f"  Cache directory: {cache_dir}")

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
    finally:
        # Cleanup
        if cache_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up test cache directory")


if __name__ == "__main__":
    success = asyncio.run(test_llm_query_engine())
    sys.exit(0 if success else 1)
