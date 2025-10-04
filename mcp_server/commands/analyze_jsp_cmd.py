#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/analyze-jsp Slash Command

Analyze JSP file structure
"""

import argparse
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args


class AnalyzeJSPCommand(BaseCommand):
    """Command: /analyze-jsp"""

    def get_name(self) -> str:
        return "analyze-jsp"

    def get_description(self) -> str:
        return "Analyze JSP file structure and extract UI components"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /analyze-jsp user_list.jsp
  /analyze-jsp src/main/webapp/WEB-INF/views/user/list.jsp
  /analyze-jsp user_list.jsp --output analysis/jsp.json
  /analyze-jsp user_list.jsp --force-refresh
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'jsp_file',
            help='Path to JSP file'
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
        """Execute /analyze-jsp command"""
        parsed_args = self.parse_args(args)

        # Prepare tool arguments
        tool_args = {
            'jsp_file': parsed_args.jsp_file,
            'force_refresh': parsed_args.force_refresh
        }

        if parsed_args.output:
            tool_args['output_file'] = parsed_args.output

        # Call MCP tool
        result = await self.server.handle_tool_call(
            tool_name='analyze_jsp',
            arguments=tool_args
        )

        if result.get('success'):
            analysis = result.get('result', {})
            stats = analysis.get('statistics', {})

            message = f"✓ JSP analysis complete: {parsed_args.jsp_file}"
            data = {
                'jsp_file': analysis.get('jsp_file'),
                'total_elements': stats.get('total_elements', 0),
                'forms': stats.get('total_forms', 0),
                'tables': stats.get('total_tables', 0),
                'scripts': stats.get('total_scripts', 0),
                'output_file': result.get('output_file')
            }

            return self.format_success(message, data)
        else:
            return self.format_error(result.get('error', 'Unknown error'))
