#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/analyze-controller Slash Command

Analyze Spring MVC Controller
"""

import argparse
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args


class AnalyzeControllerCommand(BaseCommand):
    """Command: /analyze-controller"""

    def get_name(self) -> str:
        return "analyze-controller"

    def get_description(self) -> str:
        return "Analyze Spring MVC Controller structure"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /analyze-controller UserController.java
  /analyze-controller src/main/java/com/example/controller/UserController.java
  /analyze-controller UserController.java --output analysis/controller.json
  /analyze-controller UserController.java --force-refresh
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'controller_file',
            help='Path to Controller Java file'
        )

        parser.add_argument(
            '--output', '-o',
            help='Output JSON file path'
        )

        parser.add_argument(
            '--force-refresh', '-f',
            action='store_true',
            help='Force refresh (ignore cache)'
        )

        return parser

    @validate_args
    async def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute /analyze-controller command"""
        parsed_args = self.parse_args(args)

        # Prepare tool arguments
        tool_args = {
            'controller_file': parsed_args.controller_file,
            'force_refresh': parsed_args.force_refresh
        }

        if parsed_args.output:
            tool_args['output_file'] = parsed_args.output

        # Call MCP tool
        result = await self.server.handle_tool_call(
            tool_name='analyze_controller',
            arguments=tool_args
        )

        if result.get('success'):
            analysis = result.get('result', {})
            stats = analysis.get('statistics', {})
            http_methods = stats.get('http_methods', {})

            message = f"✓ Controller analysis complete: {parsed_args.controller_file}"
            data = {
                'controller_name': analysis.get('controller_name'),
                'total_endpoints': stats.get('total_endpoints', 0),
                'GET': http_methods.get('GET', 0),
                'POST': http_methods.get('POST', 0),
                'PUT': http_methods.get('PUT', 0),
                'DELETE': http_methods.get('DELETE', 0),
                'output_file': result.get('output_file')
            }

            return self.format_success(message, data)
        else:
            return self.format_error(result.get('error', 'Unknown error'))
