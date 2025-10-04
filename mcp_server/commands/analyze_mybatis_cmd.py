#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/analyze-mybatis Slash Command

Analyze MyBatis Mapper (interface + XML)
"""

import argparse
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args


class AnalyzeMyBatisCommand(BaseCommand):
    """Command: /analyze-mybatis"""

    def get_name(self) -> str:
        return "analyze-mybatis"

    def get_description(self) -> str:
        return "Analyze MyBatis Mapper (interface + XML)"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /analyze-mybatis UserMapper.java
  /analyze-mybatis UserMapper.java UserMapper.xml
  /analyze-mybatis UserMapper.java --xml UserMapper.xml
  /analyze-mybatis UserMapper.java UserMapper.xml --output analysis/mapper.json
  /analyze-mybatis UserMapper.java --force-refresh
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'interface_file',
            help='Path to Mapper interface Java file'
        )

        parser.add_argument(
            'xml_file',
            nargs='?',
            help='Path to Mapper XML file (optional, positional)'
        )

        parser.add_argument(
            '--xml', '-x',
            dest='xml_flag',
            help='Path to Mapper XML file (alternative to positional)'
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
        """Execute /analyze-mybatis command"""
        parsed_args = self.parse_args(args)

        # Prepare tool arguments
        tool_args = {
            'interface_file': parsed_args.interface_file,
            'force_refresh': parsed_args.force_refresh
        }

        # XML file can come from positional arg or --xml flag
        xml_file = parsed_args.xml_file or parsed_args.xml_flag
        if xml_file:
            tool_args['xml_file'] = xml_file

        if parsed_args.output:
            tool_args['output_file'] = parsed_args.output

        # Call MCP tool
        result = await self.server.handle_tool_call(
            tool_name='analyze_mybatis',
            arguments=tool_args
        )

        if result.get('success'):
            analysis = result.get('result', {})
            stats = analysis.get('statistics', {})

            message = f"✓ MyBatis analysis complete: {parsed_args.interface_file}"
            data = {
                'mapper_name': analysis.get('mapper_name'),
                'interface_methods': stats.get('interface_methods', 0),
                'xml_statements': stats.get('xml_statements', 0),
                'mapped_methods': stats.get('mapped_methods', 0),
                'coverage': f"{stats.get('mapped_methods', 0)}/{stats.get('interface_methods', 0)}",
                'output_file': result.get('output_file')
            }

            return self.format_success(message, data)
        else:
            return self.format_error(result.get('error', 'Unknown error'))
