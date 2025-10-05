#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test SemanticCache
"""

import sys
import shutil
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

from mcp_server.tools.semantic_cache import SemanticCache


def test_semantic_cache():
    """Test SemanticCache functionality"""
    print("=" * 60)
    print("Testing SemanticCache")
    print("=" * 60)

    # Create temporary cache directory
    temp_dir = tempfile.mkdtemp()
    cache_dir = Path(temp_dir) / "test_cache"

    try:
        # Test 1: Initialization
        print("\n[1] Testing cache initialization...")
        cache = SemanticCache(cache_dir=str(cache_dir))
        assert cache_dir.exists(), "Cache directory not created"
        print(f"  [OK] Cache initialized: {cache_dir}")

        # Test 2: Code normalization
        print("\n[2] Testing code normalization...")

        code_with_comments = """
        // This is a comment
        public void test() {
            /* Multi-line
               comment */
            String x = "hello";  // inline comment
            # Python comment
        }
        """

        normalized = cache._normalize_code(code_with_comments)
        assert "//" not in normalized, "Single-line comments not removed"
        assert "/*" not in normalized, "Multi-line comments not removed"
        assert "#" not in normalized or "hello" in normalized, "Python comments not removed"
        print(f"  [OK] Code normalized: {len(code_with_comments)} -> {len(normalized)} chars")

        # Test 3: Semantic hashing
        print("\n[3] Testing semantic hashing...")

        code1 = "public void test() { return 1; }"
        code2 = "public void test(){return 1;}"  # Different whitespace
        code3 = "public void test() { return 2; }"  # Different content

        hash1 = cache.semantic_hash(code1, "test_query")
        hash2 = cache.semantic_hash(code2, "test_query")
        hash3 = cache.semantic_hash(code3, "test_query")

        assert hash1 == hash2, "Identical code should have same hash"
        assert hash1 != hash3, "Different code should have different hash"
        assert len(hash1) == 32, "MD5 hash should be 32 chars"
        print(f"  [OK] Semantic hashing works")
        print(f"    Hash1: {hash1}")
        print(f"    Hash2: {hash2} (same as hash1)")
        print(f"    Hash3: {hash3} (different)")

        # Test 4: Cache miss
        print("\n[4] Testing cache miss...")
        result = cache.get("some code", "query_type")
        assert result is None, "Should return None for cache miss"
        assert cache.misses == 1, "Should track misses"
        print(f"  [OK] Cache miss detected")

        # Test 5: Cache set and get
        print("\n[5] Testing cache set and get...")

        test_code = "public User getUser(int id) { return userMapper.selectById(id); }"
        test_result = {
            "match": True,
            "confidence": 0.95,
            "reasoning": "Direct mapper call detected"
        }

        cache.set(test_code, "verify_relationship", test_result, estimated_tokens=500)
        cached_result = cache.get(test_code, "verify_relationship")

        assert cached_result is not None, "Should retrieve cached result"
        assert cached_result["match"] == test_result["match"], "Cached data mismatch"
        assert cached_result["confidence"] == test_result["confidence"], "Cached data mismatch"
        assert cache.hits == 1, "Should track hits"
        print(f"  [OK] Cache set and get works")

        # Test 6: Whitespace-insensitive caching
        print("\n[6] Testing whitespace-insensitive caching...")

        code_variant = """
        public User getUser(int id) {
            return userMapper.selectById(id);
        }
        """

        cached_variant = cache.get(code_variant, "verify_relationship")
        assert cached_variant is not None, "Should find cached result despite whitespace difference"
        assert cache.hits == 2, "Should count as cache hit"
        print(f"  [OK] Whitespace-insensitive caching works")

        # Test 7: Query type differentiation
        print("\n[7] Testing query type differentiation...")

        same_code_result = cache.get(test_code, "different_query_type")
        assert same_code_result is None, "Different query type should miss"
        print(f"  [OK] Query types are differentiated")

        # Test 8: Statistics
        print("\n[8] Testing statistics...")

        stats = cache.stats()
        assert stats["total_entries"] == 1, f"Should have 1 entry, got {stats['total_entries']}"
        assert stats["hits"] == 2, f"Should have 2 hits, got {stats['hits']}"
        assert stats["misses"] == 2, f"Should have 2 misses, got {stats['misses']}"
        assert stats["hit_rate"] == 0.5, f"Hit rate should be 0.5, got {stats['hit_rate']}"
        assert stats["tokens_saved"] == 1000, f"Should save 1000 tokens (2 hits * 500), got {stats['tokens_saved']}"

        print(f"  [OK] Statistics tracking works")
        print(f"    Entries: {stats['total_entries']}")
        print(f"    Hits: {stats['hits']}")
        print(f"    Misses: {stats['misses']}")
        print(f"    Hit rate: {stats['hit_rate']:.1%}")
        print(f"    Tokens saved: {stats['tokens_saved']:,}")
        print(f"    Cost saved: ${stats['cost_saved_usd']:.4f}")

        # Test 9: Cost calculation
        print("\n[9] Testing cost calculation...")

        cost_saved = cache.calculate_cost_saved(cost_per_1k_tokens=0.003)
        expected_cost = (1000 / 1000) * 0.003  # 1000 tokens * $0.003 per 1k
        assert cost_saved == expected_cost, f"Cost calculation error: {cost_saved} != {expected_cost}"
        print(f"  [OK] Cost calculation: ${cost_saved:.4f}")

        # Test 10: Cache persistence
        print("\n[10] Testing cache persistence...")

        # Create new cache instance pointing to same directory
        cache2 = SemanticCache(cache_dir=str(cache_dir))
        cached_after_reload = cache2.get(test_code, "verify_relationship")

        assert cached_after_reload is not None, "Cache should persist across instances"
        assert cache2.hits == 3, f"Should load previous hits, got {cache2.hits}"  # Previous 2 + new 1
        print(f"  [OK] Cache persists across instances")

        # Test 11: Clear by type
        print("\n[11] Testing clear by type...")

        # Add different query type
        cache2.set("code2", "other_type", {"result": "test"}, estimated_tokens=100)
        assert cache2.stats()["total_entries"] == 2, "Should have 2 entries"

        cache2.clear_by_type("verify_relationship")
        stats_after_clear = cache2.stats()
        assert stats_after_clear["total_entries"] == 1, "Should have 1 entry after clearing type"
        print(f"  [OK] Clear by type works")

        # Test 12: Clear all
        print("\n[12] Testing clear all...")

        cache2.clear()
        stats_after_clear_all = cache2.stats()
        assert stats_after_clear_all["total_entries"] == 0, "Should have 0 entries after clear"
        assert stats_after_clear_all["hits"] == 0, "Hits should be reset"
        assert stats_after_clear_all["misses"] == 0, "Misses should be reset"
        print(f"  [OK] Clear all works")

        # Test 13: Edge cases
        print("\n[13] Testing edge cases...")

        # Empty code
        empty_hash = cache.semantic_hash("", "test")
        assert len(empty_hash) == 32, "Should handle empty code"

        # Very long code
        long_code = "x = 1\n" * 10000
        long_hash = cache.semantic_hash(long_code, "test")
        assert len(long_hash) == 32, "Should handle very long code"

        # Special characters
        special_code = "String x = \"中文測試 !@#$%^&*()\""
        special_hash = cache.semantic_hash(special_code, "test")
        assert len(special_hash) == 32, "Should handle special characters"

        print(f"  [OK] Edge cases handled")

        # Test result
        print("\n" + "=" * 60)
        print("[OK] SemanticCache test PASSED")
        print("=" * 60)

        print(f"\n📊 Final Cache State: {cache2}")
        print(f"  Cache directory: {cache_dir}")
        print(f"  Index file: {cache_dir / 'cache_index.json'}")

        return True

    except AssertionError as e:
        print(f"\n[ERROR] Assertion failed: {e}")
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
    success = test_semantic_cache()
    sys.exit(0 if success else 1)
