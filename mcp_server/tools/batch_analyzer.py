#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Analyzer

Orchestrates project-wide analysis of all SpringMVC components
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .project_scanner import ProjectScanner, ProjectStructure
from .pattern_detector import PatternDetector, DetectedFiles
from .parallel_executor import ParallelExecutor, AnalysisTask, BatchResult
from .progress_tracker import ProgressTracker
from .analysis_cache import AnalysisCache
from .dependency_graph import DependencyGraphBuilder
from ..config import ANALYZER, CACHE


@dataclass
class BatchAnalysisReport:
    """Comprehensive batch analysis report"""
    project_root: Path
    analyzed_at: datetime
    project_type: str
    summary: Dict[str, Any]
    components: Dict[str, List[Dict[str, Any]]]
    statistics: Dict[str, Any]
    issues: List[Dict[str, Any]] = field(default_factory=list)
    analysis_duration: float = 0.0
    dependency_graph: Optional[Dict[str, Any]] = None
    cache_stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "project_root": str(self.project_root),
            "analyzed_at": self.analyzed_at.isoformat(),
            "project_type": self.project_type,
            "summary": self.summary,
            "components": self.components,
            "statistics": self.statistics,
            "issues": self.issues,
            "analysis_duration_seconds": self.analysis_duration
        }

        if self.dependency_graph:
            result["dependency_graph"] = self.dependency_graph

        if self.cache_stats:
            result["cache_stats"] = self.cache_stats

        return result


class BatchAnalyzer:
    """Main batch analyzer orchestrator"""

    def __init__(
        self,
        project_root: str,
        analyzers: Dict[str, Any],
        max_workers: int = None,
        use_cache: bool = None,
        cache_dir: str = None,
        show_progress: bool = None
    ):
        """
        Initialize batch analyzer

        Args:
            project_root: Root directory of project to analyze
            analyzers: Dictionary of analyzer instances
            max_workers: Maximum parallel workers
            use_cache: Whether to use caching for incremental analysis
            cache_dir: Directory for cache storage
            show_progress: Whether to show progress bar
        """
        self.project_root = Path(project_root)
        self.analyzers = analyzers
        self.max_workers = max_workers if max_workers is not None else ANALYZER.DEFAULT_MAX_WORKERS
        self.use_cache = use_cache if use_cache is not None else CACHE.USE_CACHE
        self.show_progress = show_progress if show_progress is not None else ANALYZER.SHOW_PROGRESS

        # Resolve cache_dir
        cache_dir = cache_dir if cache_dir is not None else CACHE.DEFAULT_CACHE_DIR

        # Initialize cache
        self.cache = AnalysisCache(cache_dir) if self.use_cache else None

    async def analyze_project(
        self,
        file_types: List[str] = None,
        include_graph: bool = True,
        progress_callback: Optional[callable] = None
    ) -> BatchAnalysisReport:
        """
        Analyze entire project

        Args:
            file_types: Types to analyze ('jsp', 'controller', 'service', 'mybatis', 'all')
            include_graph: Whether to build dependency graph
            progress_callback: Optional progress callback

        Returns:
            BatchAnalysisReport with complete analysis
        """
        start_time = datetime.now()

        # Step 1: Scan project structure
        if progress_callback:
            progress_callback("Scanning project structure...")

        scanner = ProjectScanner(str(self.project_root))
        structure = scanner.scan()

        # Step 2: Detect files by pattern
        if progress_callback:
            progress_callback("Detecting analyzable files...")

        detector = PatternDetector(structure)
        detected = detector.detect_all(file_types)

        # Step 3: Create analysis tasks (with cache awareness)
        if progress_callback:
            progress_callback(f"Creating {detected.total_count()} analysis tasks...")

        tasks = self._create_tasks(detector, detected)

        # Step 4: Execute parallel analysis with progress tracking
        if progress_callback:
            progress_callback(f"Analyzing {len(tasks)} components...")

        # Initialize progress tracker
        progress_tracker = ProgressTracker(
            total_tasks=len(tasks),
            show_progress=self.show_progress
        )

        def update_progress(file_name: str):
            progress_tracker.update(file_name)
            if progress_callback:
                progress_callback(f"Analyzed: {file_name}")

        executor = ParallelExecutor(
            analyzers=self.analyzers,
            max_workers=self.max_workers
        )

        batch_result = await executor.execute_all(tasks)
        progress_tracker.finish()

        # Step 5: Build dependency graph (if requested)
        dependency_graph = None
        if include_graph:
            if progress_callback:
                progress_callback("Building dependency graph...")

            graph_builder = DependencyGraphBuilder()
            graph = graph_builder.build(batch_result.by_type())

            # Detect circular dependencies
            cycles = graph_builder.detect_circular_dependencies()
            depths = graph_builder.calculate_depth()

            dependency_graph = graph.to_dict()
            dependency_graph['circular_dependencies'] = cycles
            dependency_graph['max_depth'] = max(depths.values()) if depths else 0

        # Step 6: Generate report
        if progress_callback:
            progress_callback("Generating report...")

        report = self._generate_report(
            structure=structure,
            detected=detected,
            batch_result=batch_result,
            dependency_graph=dependency_graph,
            start_time=start_time
        )

        if progress_callback:
            progress_callback("Analysis complete!")

        return report

    def _create_tasks(
        self,
        detector: PatternDetector,
        detected: DetectedFiles
    ) -> List[AnalysisTask]:
        """
        Create analysis tasks from detected files

        Args:
            detector: PatternDetector instance
            detected: DetectedFiles with all files

        Returns:
            List of AnalysisTask objects
        """
        task_data = detector.get_analysis_tasks(detected)
        tasks = []

        for idx, data in enumerate(task_data):
            task_type = data['type']

            # Create task based on type
            if task_type == 'mybatis':
                context = {
                    'interface_path': str(data['interface_file']),
                }
                if data.get('xml_file'):
                    context['xml_path'] = str(data['xml_file'])

                tasks.append(AnalysisTask(
                    task_id=f"mybatis_{idx}",
                    analyzer_type='mybatis',
                    identifier=data['identifier'],
                    context=context
                ))

            elif task_type in ['jsp', 'controller', 'service']:
                tasks.append(AnalysisTask(
                    task_id=f"{task_type}_{idx}",
                    analyzer_type=task_type,
                    identifier=data['identifier'],
                    context={'file_path': str(data['file'])}
                ))

        return tasks

    def _generate_report(
        self,
        structure: ProjectStructure,
        detected: DetectedFiles,
        batch_result: BatchResult,
        dependency_graph: Optional[Dict[str, Any]],
        start_time: datetime
    ) -> BatchAnalysisReport:
        """
        Generate comprehensive analysis report

        Args:
            structure: Project structure
            detected: Detected files
            batch_result: Batch execution results
            start_time: Analysis start time

        Returns:
            BatchAnalysisReport
        """
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Group results by type
        results_by_type = batch_result.by_type()

        # Build summary
        summary = {
            "total_components": batch_result.total_tasks,
            "by_type": detected.by_type_count(),
            "analysis_time_seconds": duration,
            "success_rate": f"{batch_result.success_rate():.1f}%",
            "completed": batch_result.completed,
            "failed": batch_result.failed
        }

        # Build component details
        components = {}

        for analyzer_type, results in results_by_type.items():
            components[f"{analyzer_type}s"] = [
                {
                    "identifier": r.identifier,
                    "success": r.success,
                    "result": r.result if r.success else None,
                    "error": r.error if not r.success else None,
                    "duration_seconds": r.duration_seconds
                }
                for r in results
            ]

        # Calculate statistics
        statistics = self._calculate_statistics(results_by_type)

        # Detect issues
        issues = self._detect_issues(results_by_type)

        # Get cache stats
        cache_stats = None
        if self.cache:
            cache_stats = self.cache.get_stats()

        return BatchAnalysisReport(
            project_root=self.project_root,
            analyzed_at=end_time,
            project_type=structure.project_type,
            summary=summary,
            components=components,
            statistics=statistics,
            issues=issues,
            analysis_duration=duration,
            dependency_graph=dependency_graph,
            cache_stats=cache_stats
        )

    def _calculate_statistics(
        self,
        results_by_type: Dict[str, List[Any]]
    ) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        stats = {
            "by_type": {}
        }

        # Per-type statistics
        for analyzer_type, results in results_by_type.items():
            successful_results = [r for r in results if r.success and r.result]

            type_stats = {
                "total": len(results),
                "successful": len(successful_results),
                "failed": len(results) - len(successful_results)
            }

            # Type-specific stats
            if analyzer_type == 'controller':
                total_endpoints = sum(
                    r.result.get('statistics', {}).get('total_endpoints', 0)
                    for r in successful_results
                )
                type_stats["total_endpoints"] = total_endpoints

            elif analyzer_type == 'service':
                total_methods = sum(
                    r.result.get('statistics', {}).get('total_methods', 0)
                    for r in successful_results
                )
                type_stats["total_methods"] = total_methods

            elif analyzer_type == 'mybatis':
                total_statements = sum(
                    r.result.get('statistics', {}).get('xml_statements', 0)
                    for r in successful_results
                )
                type_stats["total_sql_statements"] = total_statements

            stats["by_type"][analyzer_type] = type_stats

        return stats

    def _detect_issues(
        self,
        results_by_type: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        """Detect potential issues from analysis results"""
        issues = []

        # Check for unmapped MyBatis methods
        mybatis_results = results_by_type.get('mybatis', [])
        for result in mybatis_results:
            if result.success and result.result:
                stats = result.result.get('statistics', {})
                interface_methods = stats.get('interface_methods', 0)
                mapped_methods = stats.get('mapped_methods', 0)

                if interface_methods > mapped_methods:
                    issues.append({
                        "type": "warning",
                        "severity": "medium",
                        "component": result.identifier,
                        "component_type": "mybatis",
                        "message": f"{interface_methods - mapped_methods} method(s) not mapped in XML"
                    })

        # Check for failed analyses
        for analyzer_type, results in results_by_type.items():
            for result in results:
                if not result.success:
                    issues.append({
                        "type": "error",
                        "severity": "high",
                        "component": result.identifier,
                        "component_type": analyzer_type,
                        "message": result.error or "Analysis failed"
                    })

        return issues

    async def export_report(
        self,
        report: BatchAnalysisReport,
        output_file: str
    ):
        """
        Export report to JSON file

        Args:
            report: BatchAnalysisReport to export
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)


# CLI for testing
if __name__ == "__main__":
    import sys
    from .jsp_analyzer import JSPAnalyzer
    from .controller_analyzer import ControllerAnalyzer
    from .service_analyzer import ServiceAnalyzer
    from .mybatis_analyzer import MyBatisAnalyzer

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python batch_analyzer.py <project_root> [output_file]")
            sys.exit(1)

        project_root = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "output/batch_analysis.json"

        # Create analyzers
        analyzers = {
            'jsp': JSPAnalyzer(project_root=project_root),
            'controller': ControllerAnalyzer(project_root=project_root),
            'service': ServiceAnalyzer(project_root=project_root),
            'mybatis': MyBatisAnalyzer(project_root=project_root),
        }

        # Create batch analyzer
        batch = BatchAnalyzer(
            project_root=project_root,
            analyzers=analyzers,
            max_workers=10
        )

        # Progress callback
        def progress(msg):
            print(f"  {msg}")

        # Analyze
        print(f"Analyzing project: {project_root}")
        report = await batch.analyze_project(progress_callback=progress)

        # Export
        await batch.export_report(report, output_file)

        # Print summary
        print(f"\nAnalysis Complete!")
        print(f"  Total components: {report.summary['total_components']}")
        print(f"  Success rate: {report.summary['success_rate']}")
        print(f"  Duration: {report.analysis_duration:.2f}s")
        print(f"  Report saved to: {output_file}")

        if report.issues:
            print(f"\nIssues found: {len(report.issues)}")
            for issue in report.issues[:5]:  # Show first 5
                print(f"  [{issue['severity'].upper()}] {issue['component']}: {issue['message']}")

    if __name__ == "__main__":
        asyncio.run(main())
