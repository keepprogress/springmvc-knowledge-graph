#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Constants for SpringMVC Knowledge Graph Analyzer

Centralized configuration for query engine, analyzers, and MCP server.
"""

from dataclasses import dataclass


@dataclass
class QueryConfig:
    """Query engine configuration"""

    # Path finding limits
    DEFAULT_MAX_DEPTH_CHAIN: int = 10
    DEFAULT_MAX_DEPTH_IMPACT: int = 5
    MAX_DEPTH_LIMIT: int = 20  # Hard limit to prevent performance issues
    MAX_PATHS_LIMIT: int = 100  # Maximum paths to return (prevent explosion)

    # Display limits
    MAX_SUGGESTED_NODES: int = 10

    # Performance
    ENABLE_EDGE_LOOKUP_CACHE: bool = True
    LOG_PERFORMANCE_METRICS: bool = True

    # Timeouts
    QUERY_TIMEOUT_SECONDS: int = 30


@dataclass
class CacheConfig:
    """Cache configuration"""

    # Cache expiration
    CACHE_MAX_AGE_HOURS: int = 24

    # Cache directories
    DEFAULT_CACHE_DIR: str = ".batch_cache"

    # Cache behavior
    USE_CACHE: bool = True
    FORCE_REFRESH: bool = False


@dataclass
class AnalyzerConfig:
    """Analyzer configuration"""

    # Batch processing
    DEFAULT_MAX_WORKERS: int = 10
    SHOW_PROGRESS: bool = False

    # File patterns
    SKIP_PATTERNS: list = None

    def __post_init__(self):
        if self.SKIP_PATTERNS is None:
            self.SKIP_PATTERNS = [
                '**/target/**',
                '**/build/**',
                '**/node_modules/**',
                '**/.git/**',
                '**/test/**'
            ]


@dataclass
class ServerConfig:
    """MCP Server configuration"""

    # Logging
    DEFAULT_LOG_LEVEL: str = "INFO"

    # Server info
    SERVER_NAME: str = "springmvc-analyzer"
    SERVER_VERSION: str = "0.4.4-alpha"

    # Encoding
    FORCE_UTF8_ENCODING: bool = True


# Global instances
QUERY = QueryConfig()
CACHE = CacheConfig()
ANALYZER = AnalyzerConfig()
SERVER = ServerConfig()
