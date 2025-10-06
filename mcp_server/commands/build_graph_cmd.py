#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/build-graph Slash Command

Build code-based knowledge graph from Phase 3 analysis results
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args


class BuildGraphCommand(BaseCommand):
    """Command: /build-graph"""

    def get_name(self) -> str:
        return "build-graph"

    def get_description(self) -> str:
        return "Build code-based knowledge graph from Phase 3 analysis results"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /build-graph
  /build-graph --base-dir=output/analysis
  /build-graph --output=output/graph/my_graph.json
  /build-graph --no-export-stats --no-export-low-conf
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            '--base-dir',
            default='output/analysis',
            help='Base directory for analysis results (default: output/analysis)'
        )

        parser.add_argument(
            '--output',
            default='output/graph/code_based_graph.json',
            help='Output path for graph JSON (default: output/graph/code_based_graph.json)'
        )

        parser.add_argument(
            '--no-export-stats',
            action='store_true',
            help='Disable exporting statistics JSON'
        )

        parser.add_argument(
            '--no-export-low-conf',
            action='store_true',
            help='Disable exporting low confidence edges JSON'
        )

        return parser

    @validate_args
    async def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute /build-graph command"""
        parsed_args = self.parse_args(args)

        # Resolve paths
        base_dir = self.resolve_path(parsed_args.base_dir)
        output_path = self.resolve_path(parsed_args.output)

        # Handle base_dir: if it ends with /analysis, strip it
        # (CodeGraphBuilder expects parent dir of "analysis")
        if base_dir.name == "analysis":
            base_dir = base_dir.parent

        # Check if base directory exists
        if not base_dir.exists():
            return self.format_error(
                f"Base directory not found: {base_dir}\n"
                f"Run /analyze-all first to generate analysis results."
            )

        # Check if analysis directory exists inside base_dir
        analysis_dir = base_dir / "analysis"
        if not analysis_dir.exists():
            return self.format_error(
                f"Analysis directory not found: {analysis_dir}\n"
                f"Run /analyze-all first to generate analysis results."
            )

        # Import CodeGraphBuilder (lazy import)
        from mcp_server.tools.code_graph_builder import CodeGraphBuilder

        try:
            # Create graph builder (pass base_dir, not analysis_dir)
            builder = CodeGraphBuilder(base_dir=str(base_dir))

            # Build graph
            graph = builder.build_graph()

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Export graph to specified directory
            # Note: export_graph creates: code_based_graph.json, low_confidence_edges.json, graph_statistics.json
            export_results = builder.export_graph(str(output_path.parent))

            # Rename main graph file to user-specified name if different
            default_graph_path = Path(export_results["graph"])
            if default_graph_path.name != output_path.name:
                default_graph_path.rename(output_path)
                export_results["graph"] = str(output_path)

            # Handle optional exports - delete if user requested not to export
            if parsed_args.no_export_stats:
                stats_file = Path(export_results["statistics"])
                if stats_file.exists():
                    stats_file.unlink()
                export_results["statistics"] = None

            if parsed_args.no_export_low_conf:
                low_conf_file = Path(export_results["low_confidence"])
                if low_conf_file.exists():
                    low_conf_file.unlink()
                export_results["low_confidence"] = None

            # Get statistics for response (from builder's statistics attribute)
            stats = builder.statistics

            # Build success message
            total_nodes = stats.get('nodes', {}).get('total', 0)
            total_edges = stats.get('edges', {}).get('total', 0)

            message = (
                f"Knowledge graph built successfully:\n"
                f"  • Nodes: {total_nodes}\n"
                f"  • Edges: {total_edges}\n"
                f"  • Output: {output_path}"
            )

            data = {
                'graph_file': export_results["graph"],
                'statistics': stats,
                'exports': export_results
            }

            return self.format_success(message, data)

        except FileNotFoundError as e:
            return self.format_error(
                f"Required analysis files not found: {e}\n"
                f"Run /analyze-all first to generate complete analysis results."
            )
        except Exception as e:
            return self.format_error(f"Graph building failed: {str(e)}")
