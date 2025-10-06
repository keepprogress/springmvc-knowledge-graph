#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Cache for LLM Query Results

Caches LLM verification results based on semantic hash of code.
Reduces API costs and improves response time.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from time import time
import logging

logger = logging.getLogger(__name__)


class SemanticCache:
    """Cache LLM query results based on semantic code similarity."""

    def __init__(self, cache_dir: str = ".llm_cache", rate_limit_per_minute: int = 60):
        """
        Initialize semantic cache.

        Args:
            cache_dir: Directory to store cache files
            rate_limit_per_minute: Maximum LLM queries per minute (default: 60)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_index()

        # Statistics tracking
        self.hits = self.cache_index.get("_stats", {}).get("hits", 0)
        self.misses = self.cache_index.get("_stats", {}).get("misses", 0)
        self.total_tokens_saved = self.cache_index.get("_stats", {}).get("total_tokens_saved", 0)

        # Rate limiting
        self.rate_limit = rate_limit_per_minute
        self.query_timestamps: List[float] = []

        # Remove stats from index if present
        if "_stats" in self.cache_index:
            del self.cache_index["_stats"]

    def _load_index(self) -> Dict[str, Any]:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                return {}
        return {}

    def _save_index(self):
        """Save cache index to disk."""
        # Include stats in index file
        index_with_stats = {
            **self.cache_index,
            "_stats": {
                "hits": self.hits,
                "misses": self.misses,
                "total_tokens_saved": self.total_tokens_saved,
                "last_updated": datetime.now().isoformat()
            }
        }

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_with_stats, f, indent=2, ensure_ascii=False)

    def _normalize_code(self, code: str) -> str:
        """
        Normalize code for semantic comparison.

        Removes:
        - Leading/trailing whitespace
        - Multiple consecutive spaces
        - Single-line comments (// and #)
        - Multi-line comments (/* */ and ''' ''')
        - Empty lines

        Args:
            code: Source code string

        Returns:
            Normalized code string
        """
        # Remove single-line comments
        # Java/JS style: // comment
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        # Python style: # comment
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)

        # Remove multi-line comments
        # Java/JS style: /* comment */
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Python style: ''' comment ''' or """ comment """
        code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)

        # Normalize all whitespace to single spaces
        normalized = re.sub(r'\s+', ' ', code)

        # Remove spaces around common syntax elements for semantic equivalence
        # This makes "test() {" equivalent to "test(){"
        normalized = re.sub(r'\s*([(){}\[\];,=<>!+\-*/])\s*', r'\1', normalized)

        return normalized.strip()

    def semantic_hash(self, code: str, query_type: str) -> str:
        """
        Create semantic hash for caching.

        Uses SHA256 for better collision resistance and future-proofing.

        Args:
            code: Source code to hash
            query_type: Type of query (e.g., "verify_relationship", "match_url")

        Returns:
            SHA256 hash string
        """
        normalized = self._normalize_code(code)
        hash_input = f"{normalized}:{query_type}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    def get(self, code: str, query_type: str) -> Optional[Dict[str, Any]]:
        """
        Get cached LLM result.

        Args:
            code: Source code
            query_type: Type of query

        Returns:
            Cached result dict or None if not found
        """
        cache_key = self.semantic_hash(code, query_type)

        if cache_key in self.cache_index:
            cache_file = self.cache_dir / f"{cache_key}.json"

            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)

                    # Update statistics
                    self.hits += 1
                    tokens_saved = result.get('_metadata', {}).get('estimated_tokens', 0)
                    self.total_tokens_saved += tokens_saved
                    self._save_index()

                    logger.info(f"Cache HIT: {query_type} ({tokens_saved} tokens saved)")

                    # Remove metadata before returning
                    if '_metadata' in result:
                        del result['_metadata']

                    return result

                except Exception as e:
                    logger.warning(f"Failed to load cached result: {e}")
                    # Remove invalid cache entry
                    del self.cache_index[cache_key]
                    self._save_index()

        # Cache miss
        self.misses += 1
        self._save_index()
        logger.info(f"Cache MISS: {query_type}")

        return None

    def check_rate_limit(self):
        """
        Check if rate limit allows new query.

        Raises:
            Exception: If rate limit exceeded
        """
        now = time()
        # Remove timestamps older than 1 minute
        self.query_timestamps = [t for t in self.query_timestamps if now - t < 60]

        if len(self.query_timestamps) >= self.rate_limit:
            raise Exception(
                f"Rate limit exceeded: {self.rate_limit} queries per minute. "
                f"Please wait before making more requests."
            )

        # Record this query timestamp
        self.query_timestamps.append(now)

    def set(self, code: str, query_type: str, result: Dict[str, Any],
            estimated_tokens: int = 0):
        """
        Cache LLM result.

        Args:
            code: Source code
            query_type: Type of query
            result: LLM result to cache
            estimated_tokens: Estimated tokens used (for cost calculation)
        """
        cache_key = self.semantic_hash(code, query_type)
        cache_file = self.cache_dir / f"{cache_key}.json"

        # Add metadata
        result_with_metadata = {
            **result,
            '_metadata': {
                'query_type': query_type,
                'cached_at': datetime.now().isoformat(),
                'estimated_tokens': estimated_tokens,
                'code_hash': cache_key
            }
        }

        # Save cache file
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result_with_metadata, f, indent=2, ensure_ascii=False)

        # Update index
        self.cache_index[cache_key] = {
            'query_type': query_type,
            'cached_at': datetime.now().isoformat(),
            'file': str(cache_file.name)
        }
        self._save_index()

        logger.info(f"Cached result: {query_type} ({estimated_tokens} tokens)")

    def calculate_cost_saved(self, cost_per_1k_tokens: float = 0.003) -> float:
        """
        Calculate cost saved by caching.

        Args:
            cost_per_1k_tokens: Cost per 1000 tokens (default: $0.003 for Claude Sonnet)

        Returns:
            Total cost saved in USD
        """
        return (self.total_tokens_saved / 1000) * cost_per_1k_tokens

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_queries = self.hits + self.misses
        hit_rate = self.hits / total_queries if total_queries > 0 else 0.0

        return {
            "total_entries": len(self.cache_index),
            "total_queries": total_queries,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3),
            "tokens_saved": self.total_tokens_saved,
            "cost_saved_usd": round(self.calculate_cost_saved(), 4)
        }

    def clear(self):
        """Clear all cache entries."""
        # Remove all cache files
        for cache_key in self.cache_index:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_file.unlink()

        # Reset index and stats
        self.cache_index = {}
        self.hits = 0
        self.misses = 0
        self.total_tokens_saved = 0
        self._save_index()

        logger.info("Cache cleared")

    def clear_by_type(self, query_type: str):
        """
        Clear cache entries of specific query type.

        Args:
            query_type: Type of query to clear
        """
        to_remove = []

        for cache_key, entry in self.cache_index.items():
            if entry.get('query_type') == query_type:
                cache_file = self.cache_dir / f"{cache_key}.json"
                if cache_file.exists():
                    cache_file.unlink()
                to_remove.append(cache_key)

        for cache_key in to_remove:
            del self.cache_index[cache_key]

        self._save_index()
        logger.info(f"Cleared {len(to_remove)} cache entries of type: {query_type}")

    def __repr__(self) -> str:
        """String representation of cache."""
        stats = self.stats()
        return (
            f"SemanticCache("
            f"entries={stats['total_entries']}, "
            f"hit_rate={stats['hit_rate']:.1%}, "
            f"tokens_saved={stats['tokens_saved']:,})"
        )
