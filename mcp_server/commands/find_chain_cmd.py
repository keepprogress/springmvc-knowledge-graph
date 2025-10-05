#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/find-chain Slash Command

Find call chains in the dependency graph
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args
from ..config import QUERY


class FindChainCommand(BaseCommand):
    """Command: /find-chain"""

    def get_name(self) -> str:
        return "find-chain"

    def get_description(self) -> str:
        return "Find call chains from start node to end node in dependency graph"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /find-chain UserController
  /find-chain UserController UserMapper
  /find-chain UserController --max-depth 5
  /find-chain UserController UserMapper --project /path/to/project
  /find-chain --start UserController --end UserMapper
  /find-chain UserController --format json
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'start_node',
            nargs='?',
            help='Starting node (e.g., UserController)'
        )

        parser.add_argument(
            'end_node',
            nargs='?',
            help='Ending node (optional, shows direct dependencies if not provided)'
        )

        parser.add_argument(
            '--start',
            help='Alternative way to specify start node'
        )

        parser.add_argument(
            '--end',
            help='Alternative way to specify end node'
        )

        parser.add_argument(
            '--project', '-p',
            default='.',
            help='Project root directory (default: current directory)'
        )

        parser.add_argument(
            '--max-depth', '-d',
            type=int,
            default=QUERY.DEFAULT_MAX_DEPTH_CHAIN,
            help=f'Maximum depth to search (default: {QUERY.DEFAULT_MAX_DEPTH_CHAIN}, max: {QUERY.MAX_DEPTH_LIMIT})'
        )

        parser.add_argument(
            '--max-paths',
            type=int,
            default=QUERY.MAX_PATHS_LIMIT,
            help=f'Maximum number of paths to return (default: {QUERY.MAX_PATHS_LIMIT})'
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
        """Execute /find-chain command"""
        parsed_args = self.parse_args(args)

        # Determine start and end nodes
        start_node = parsed_args.start or parsed_args.start_node
        end_node = parsed_args.end or parsed_args.end_node

        if not start_node:
            return self.format_error("Start node is required. Usage: /find-chain <start_node> [end_node]")

        # Validate max_depth
        if parsed_args.max_depth > QUERY.MAX_DEPTH_LIMIT:
            return self.format_error(
                f"max_depth {parsed_args.max_depth} exceeds limit {QUERY.MAX_DEPTH_LIMIT}"
            )

        # Validate max_paths
        if parsed_args.max_paths <= 0:
            return self.format_error("max_paths must be greater than 0")

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

        # Find call chains
        try:
            chains = engine.find_call_chains(
                start_node=start_node,
                end_node=end_node,
                max_depth=parsed_args.max_depth,
                max_paths=parsed_args.max_paths
            )
        except Exception as e:
            return self.format_error(f"Failed to find call chains: {str(e)}")

        # Check if node exists
        if start_node not in graph.nodes:
            available_nodes = list(graph.nodes.keys())[:QUERY.MAX_SUGGESTED_NODES]
            suggestion = f"Available nodes (first {QUERY.MAX_SUGGESTED_NODES}): {', '.join(available_nodes)}"
            return self.format_error(f"Start node '{start_node}' not found in graph. {suggestion}")

        # Format output
        if parsed_args.format == 'json':
            return self._format_json_output(start_node, end_node, chains)
        else:
            return self._format_text_output(start_node, end_node, chains)

    def _format_text_output(self, start_node: str, end_node: str, chains) -> Dict[str, Any]:
        """Format output as text"""
        if not chains:
            if end_node:
                message = f"No call chains found from '{start_node}' to '{end_node}'"
            else:
                message = f"No direct dependencies found for '{start_node}'"

            return self.format_success(message, {})

        # Build message
        if end_node:
            message = f"Found {len(chains)} call chain(s) from '{start_node}' to '{end_node}':"
        else:
            message = f"Direct dependencies of '{start_node}':"

        lines = [message, ""]

        for i, chain in enumerate(chains, 1):
            lines.append(f"Chain {i} (depth: {chain.depth}):")
            lines.append(chain.format())
            lines.append("")

        data = {
            'start_node': start_node,
            'end_node': end_node,
            'total_chains': len(chains),
            'chains': [chain.to_dict() for chain in chains]
        }

        return {
            "success": True,
            "message": "\n".join(lines),
            "data": data
        }

    def _format_json_output(self, start_node: str, end_node: str, chains) -> Dict[str, Any]:
        """Format output as JSON"""
        data = {
            'start_node': start_node,
            'end_node': end_node,
            'total_chains': len(chains),
            'chains': [chain.to_dict() for chain in chains]
        }

        message = json.dumps(data, indent=2)
        return self.format_success(message, data)
