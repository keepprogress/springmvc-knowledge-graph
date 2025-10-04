#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/analyze-service Slash Command

Analyze Spring Service layer
"""

import argparse
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args


class AnalyzeServiceCommand(BaseCommand):
    """Command: /analyze-service"""

    def get_name(self) -> str:
        return "analyze-service"

    def get_description(self) -> str:
        return "Analyze Spring Service layer structure"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /analyze-service UserService.java
  /analyze-service src/main/java/com/example/service/UserService.java
  /analyze-service UserService.java --output analysis/service.json
  /analyze-service UserService.java --force-refresh
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'service_file',
            help='Path to Service Java file'
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
        """Execute /analyze-service command"""
        parsed_args = self.parse_args(args)

        # Prepare tool arguments
        tool_args = {
            'service_file': parsed_args.service_file,
            'force_refresh': parsed_args.force_refresh
        }

        if parsed_args.output:
            tool_args['output_file'] = parsed_args.output

        # Call MCP tool
        result = await self.server.handle_tool_call(
            tool_name='analyze_service',
            arguments=tool_args
        )

        if result.get('success'):
            analysis = result.get('result', {})
            stats = analysis.get('statistics', {})

            message = f"✓ Service analysis complete: {parsed_args.service_file}"
            data = {
                'service_name': analysis.get('service_name'),
                'total_methods': stats.get('total_methods', 0),
                'public_methods': stats.get('public_methods', 0),
                'transactional_methods': stats.get('transactional_methods', 0),
                'is_service': analysis.get('is_service', False),
                'output_file': result.get('output_file')
            }

            return self.format_success(message, data)
        else:
            return self.format_error(result.get('error', 'Unknown error'))
