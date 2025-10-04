#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/analyze-all Slash Command

Batch analyze entire SpringMVC project
"""

import argparse
import asyncio
from typing import Any, Dict, List

from .base_command import BaseCommand, validate_args


class AnalyzeAllCommand(BaseCommand):
    """Command: /analyze-all"""

    def get_name(self) -> str:
        return "analyze-all"

    def get_description(self) -> str:
        return "Batch analyze entire SpringMVC project"

    def _create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=self.get_name(),
            description=self.get_description(),
            epilog="""
Examples:
  /analyze-all
  /analyze-all /path/to/project
  /analyze-all --types controller,service
  /analyze-all -o analysis/report.json -p 20
  /analyze-all --types mybatis --output mappers.json
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'project_dir',
            nargs='?',
            default='.',
            help='Project root directory (default: current directory)'
        )

        parser.add_argument(
            '--output', '-o',
            default='output/batch_analysis.json',
            help='Output report file path (default: output/batch_analysis.json)'
        )

        parser.add_argument(
            '--types', '-t',
            help='Component types to analyze (comma-separated: jsp,controller,service,mybatis,all)'
        )

        parser.add_argument(
            '--parallel', '-p',
            type=int,
            default=10,
            help='Number of parallel workers (default: 10)'
        )

        parser.add_argument(
            '--no-graph',
            action='store_true',
            help='Exclude dependency graph from report'
        )

        parser.add_argument(
            '--no-cache',
            action='store_true',
            help='Force refresh all analyses (ignore cache)'
        )

        return parser

    @validate_args
    async def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute /analyze-all command"""
        parsed_args = self.parse_args(args)

        # Parse file types
        file_types = None
        if parsed_args.types:
            file_types = [t.strip() for t in parsed_args.types.split(',')]

        # Import batch analyzer (lazy import to avoid circular dependencies)
        from mcp_server.tools.batch_analyzer import BatchAnalyzer

        # Create analyzers dictionary
        analyzers = {
            'jsp': self.server.jsp_analyzer,
            'controller': self.server.controller_analyzer,
            'service': self.server.service_analyzer,
            'mybatis': self.server.mybatis_analyzer,
        }

        # Create batch analyzer
        batch = BatchAnalyzer(
            project_root=parsed_args.project_dir,
            analyzers=analyzers,
            max_workers=parsed_args.parallel
        )

        # Progress tracking
        progress_messages = []

        def progress_callback(msg: str):
            progress_messages.append(msg)
            # Could print here for real-time progress, but keep quiet for now

        try:
            # Execute batch analysis
            report = await batch.analyze_project(
                file_types=file_types,
                include_graph=not parsed_args.no_graph,
                progress_callback=progress_callback
            )

            # Export report
            await batch.export_report(report, parsed_args.output)

            # Build success response
            summary = report.summary
            message = f"✓ Batch analysis complete: {summary['total_components']} components analyzed"

            data = {
                'project_root': str(report.project_root),
                'total_components': summary['total_components'],
                'by_type': summary['by_type'],
                'success_rate': summary['success_rate'],
                'completed': summary['completed'],
                'failed': summary['failed'],
                'duration_seconds': report.analysis_duration,
                'output_file': parsed_args.output,
                'issues_count': len(report.issues)
            }

            # Add issues summary if any
            if report.issues:
                high_severity = sum(1 for i in report.issues if i.get('severity') == 'high')
                medium_severity = sum(1 for i in report.issues if i.get('severity') == 'medium')
                data['issues_summary'] = {
                    'total': len(report.issues),
                    'high': high_severity,
                    'medium': medium_severity
                }

            return self.format_success(message, data)

        except Exception as e:
            return self.format_error(f"Batch analysis failed: {str(e)}")
