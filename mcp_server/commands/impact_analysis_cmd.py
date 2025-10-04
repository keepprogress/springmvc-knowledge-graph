#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/impact-analysis Slash Command

Analyze the impact of changing a component
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args

# Constants
MAX_SUGGESTED_NODES = 10


class ImpactAnalysisCommand(BaseCommand):
    """Command: /impact-analysis"""

    def get_name(self) -> str:
        return "impact-analysis"

    def get_description(self) -> str:
        return "Analyze impact of changing a component (shows upstream and downstream dependencies)"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /impact-analysis UserService
  /impact-analysis UserService --direction upstream
  /impact-analysis UserService --direction downstream
  /impact-analysis UserService --max-depth 3
  /impact-analysis UserService --project /path/to/project
  /impact-analysis UserService --format json
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'node',
            help='Node to analyze (e.g., UserService)'
        )

        parser.add_argument(
            '--direction', '-d',
            choices=['upstream', 'downstream', 'both'],
            default='both',
            help='Analysis direction (default: both)\n'
                 '  upstream: Find who depends on this node\n'
                 '  downstream: Find what this node depends on\n'
                 '  both: Show both directions'
        )

        parser.add_argument(
            '--project', '-p',
            default='.',
            help='Project root directory (default: current directory)'
        )

        parser.add_argument(
            '--max-depth', '-m',
            type=int,
            default=5,
            help='Maximum depth to analyze (default: 5)'
        )

        parser.add_argument(
            '--format', '-f',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )

        parser.add_argument(
            '--cache-dir',
            default='.batch_cache',
            help='Cache directory for loading previous analysis (default: .batch_cache)'
        )

        return parser

    @validate_args
    async def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute /impact-analysis command"""
        parsed_args = self.parse_args(args)

        # Load dependency graph from cache or analyze project
        from mcp_server.tools.graph_utils import load_or_build_graph

        try:
            graph = await load_or_build_graph(parsed_args.project, parsed_args.cache_dir)
        except Exception as e:
            return self.format_error(f"Failed to load dependency graph: {str(e)}")

        # Import query engine
        from mcp_server.tools.query_engine import QueryEngine

        # Create query engine
        engine = QueryEngine(graph)

        # Perform impact analysis
        try:
            result = engine.impact_analysis(
                node_id=parsed_args.node,
                direction=parsed_args.direction,
                max_depth=parsed_args.max_depth
            )
        except Exception as e:
            return self.format_error(f"Failed to perform impact analysis: {str(e)}")

        # Check if node exists
        if result is None:
            available_nodes = list(graph.nodes.keys())[:MAX_SUGGESTED_NODES]
            suggestion = f"Available nodes (first {MAX_SUGGESTED_NODES}): {', '.join(available_nodes)}"
            return self.format_error(f"Node '{parsed_args.node}' not found in graph. {suggestion}")

        # Format output
        if parsed_args.format == 'json':
            return self._format_json_output(result)
        else:
            return self._format_text_output(result, parsed_args.direction)

    def _format_text_output(self, result, direction: str) -> Dict[str, Any]:
        """Format output as text"""
        lines = [
            f"Impact Analysis: {result.target_node}",
            "=" * 60,
            ""
        ]

        # Upstream (who depends on this)
        if direction in ["upstream", "both"]:
            lines.append(f"UPSTREAM (Who depends on this): {result.total_upstream} components")
            lines.append("-" * 60)

            if result.upstream:
                for level_key in sorted(result.upstream.keys()):
                    nodes = result.upstream[level_key]
                    lines.append(f"  {level_key}:")
                    for node in nodes:
                        lines.append(f"    <- {node}")
                    lines.append("")
            else:
                lines.append("  (No upstream dependencies)")
                lines.append("")

        # Downstream (what this depends on)
        if direction in ["downstream", "both"]:
            lines.append(f"DOWNSTREAM (What this depends on): {result.total_downstream} components")
            lines.append("-" * 60)

            if result.downstream:
                for level_key in sorted(result.downstream.keys()):
                    nodes = result.downstream[level_key]
                    lines.append(f"  {level_key}:")
                    for node in nodes:
                        lines.append(f"    -> {node}")
                    lines.append("")
            else:
                lines.append("  (No downstream dependencies)")
                lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 60)
        lines.append(f"Total components affected: {result.total_upstream + result.total_downstream}")
        lines.append(f"  - Upstream (need testing if changed): {result.total_upstream}")
        lines.append(f"  - Downstream (dependencies to review): {result.total_downstream}")
        lines.append("")

        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 60)
        if result.total_upstream > 0:
            lines.append(f"  - Test all {result.total_upstream} upstream components after changes")
        if result.total_downstream > 0:
            lines.append(f"  - Review {result.total_downstream} downstream dependencies for breaking changes")
        if result.total_upstream == 0 and result.total_downstream == 0:
            lines.append("  - This component appears to be isolated (no dependencies found)")

        message = "\n".join(lines)
        data = result.to_dict()

        return self.format_success(message, data)

    def _format_json_output(self, result) -> Dict[str, Any]:
        """Format output as JSON"""
        data = result.to_dict()
        message = json.dumps(data, indent=2)
        return self.format_success(message, data)
