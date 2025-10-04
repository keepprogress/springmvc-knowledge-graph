#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Utilities

Shared utilities for dependency graph operations
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

from .dependency_graph import DependencyGraph
from .batch_analyzer import BatchAnalyzer

# Constants
CACHE_MAX_AGE_HOURS = 24

logger = logging.getLogger(__name__)


async def load_or_build_graph(
    project_dir: str,
    cache_dir: str = '.batch_cache',
    show_progress: bool = False
) -> DependencyGraph:
    """
    Load dependency graph from cache or build new one

    Args:
        project_dir: Project root directory
        cache_dir: Cache directory for loading previous analysis
        show_progress: Whether to show progress during analysis

    Returns:
        DependencyGraph instance

    Raises:
        Exception: If failed to build dependency graph
    """
    cache_path = Path(cache_dir) / "batch_analysis.json"

    # Try to load from cache first
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            # Validate cache version and timestamp
            cache_version = cached_data.get('version', '0.0.0')
            cache_timestamp = cached_data.get('timestamp')

            # Check if cache is recent (within CACHE_MAX_AGE_HOURS)
            current_time = time.time()
            cache_age_hours = (current_time - cache_timestamp) / 3600 if cache_timestamp else float('inf')

            if cache_age_hours > CACHE_MAX_AGE_HOURS:
                logger.info(f"Cache is {cache_age_hours:.1f} hours old (max: {CACHE_MAX_AGE_HOURS}), rebuilding graph")
                # Fall through to build new graph
            elif 'dependency_graph' in cached_data:
                graph_data = cached_data['dependency_graph']
                # Reconstruct graph from JSON
                graph = DependencyGraph()

                # Add nodes
                for node_data in graph_data.get('nodes', []):
                    graph.add_node(node_data['name'], node_data['type'])

                # Add edges
                for edge_data in graph_data.get('edges', []):
                    graph.add_edge(edge_data['from'], edge_data['to'], edge_data['type'])

                logger.info(f"Loaded dependency graph from cache (age: {cache_age_hours:.1f} hours)")
                return graph
        except Exception as e:
            logger.warning(f"Failed to load cached graph: {e}, rebuilding")
            # Fall through to build new graph
            pass

    # Build new graph if cache doesn't exist or failed to load
    # Create analyzers
    from .jsp_analyzer import JSPAnalyzer
    from .controller_analyzer import ControllerAnalyzer
    from .service_analyzer import ServiceAnalyzer
    from .mybatis_analyzer import MyBatisAnalyzer

    analyzers = {
        'jsp': JSPAnalyzer(project_root=project_dir),
        'controller': ControllerAnalyzer(project_root=project_dir),
        'service': ServiceAnalyzer(project_root=project_dir),
        'mybatis': MyBatisAnalyzer(project_root=project_dir),
    }

    # Create batch analyzer
    batch = BatchAnalyzer(
        project_root=project_dir,
        analyzers=analyzers,
        max_workers=10,
        use_cache=True,
        cache_dir=cache_dir,
        show_progress=show_progress
    )

    # Analyze project
    report = await batch.analyze_project(include_graph=True)

    if not report.dependency_graph:
        raise Exception("Failed to build dependency graph")

    # Reconstruct graph from report
    graph = DependencyGraph()
    graph_data = report.dependency_graph

    # Add nodes
    for node_data in graph_data.get('nodes', []):
        graph.add_node(node_data['name'], node_data['type'])

    # Add edges
    for edge_data in graph_data.get('edges', []):
        graph.add_edge(edge_data['from'], edge_data['to'], edge_data['type'])

    return graph
