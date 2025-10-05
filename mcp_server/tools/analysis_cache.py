#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis Cache

Caching system for incremental batch analysis
"""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import CACHE


class AnalysisCache:
    """Caches analysis results for incremental analysis"""

    def __init__(self, cache_dir: str = None):
        cache_dir = cache_dir if cache_dir is not None else CACHE.DEFAULT_CACHE_DIR
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception:
            pass  # Fail silently for cache

    def _get_file_hash(self, file_path: Path) -> str:
        """
        Get hash of file (mtime + size for performance)

        Args:
            file_path: Path to file

        Returns:
            Hash string
        """
        try:
            stat = file_path.stat()
            hash_input = f"{stat.st_mtime}:{stat.st_size}".encode()
            return hashlib.md5(hash_input).hexdigest()
        except Exception:
            return ""

    def _get_cache_key(self, file_path: Path, analyzer_type: str) -> str:
        """
        Get cache key for file

        Args:
            file_path: Path to file
            analyzer_type: Type of analyzer

        Returns:
            Cache key
        """
        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()
        return f"{analyzer_type}_{path_hash}"

    def is_file_changed(self, file_path: Path, analyzer_type: str) -> bool:
        """
        Check if file has changed since last analysis

        Args:
            file_path: Path to file
            analyzer_type: Type of analyzer

        Returns:
            True if file changed or not in cache
        """
        cache_key = self._get_cache_key(file_path, analyzer_type)

        if cache_key not in self.metadata:
            return True  # Not in cache

        current_hash = self._get_file_hash(file_path)
        cached_hash = self.metadata[cache_key].get('file_hash', '')

        return current_hash != cached_hash

    def get_cached_result(
        self,
        file_path: Path,
        analyzer_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis result if file unchanged

        Args:
            file_path: Path to file
            analyzer_type: Type of analyzer

        Returns:
            Cached result or None if not cached/changed
        """
        if self.is_file_changed(file_path, analyzer_type):
            return None

        cache_key = self._get_cache_key(file_path, analyzer_type)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None

    def cache_result(
        self,
        file_path: Path,
        analyzer_type: str,
        result: Dict[str, Any]
    ):
        """
        Cache analysis result

        Args:
            file_path: Path to file
            analyzer_type: Type of analyzer
            result: Analysis result to cache
        """
        cache_key = self._get_cache_key(file_path, analyzer_type)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            # Save result
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            # Update metadata
            self.metadata[cache_key] = {
                'file_path': str(file_path),
                'analyzer_type': analyzer_type,
                'file_hash': self._get_file_hash(file_path)
            }
            self._save_metadata()

        except Exception:
            pass  # Fail silently for cache

    def clear(self):
        """Clear all cached results"""
        try:
            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()

            # Clear metadata
            self.metadata = {}
            self._save_metadata()

        except Exception:
            pass

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'total_entries': len(self.metadata),
            'cache_size_mb': sum(
                f.stat().st_size for f in self.cache_dir.glob("*.pkl")
            ) / (1024 * 1024)
        }
