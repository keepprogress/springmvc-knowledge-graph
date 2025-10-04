#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parallel Analysis Executor

Executes multiple analysis tasks concurrently using asyncio
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_tool import BaseTool


@dataclass
class AnalysisTask:
    """Single analysis task"""
    task_id: str
    analyzer_type: str  # 'jsp', 'controller', 'service', 'mybatis'
    identifier: str
    context: Dict[str, Any]
    priority: int = 0  # Higher priority executed first


@dataclass
class TaskResult:
    """Result of a single analysis task"""
    task_id: str
    analyzer_type: str
    identifier: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class BatchResult:
    """Results of batch execution"""
    total_tasks: int
    completed: int
    failed: int
    results: List[TaskResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed / self.total_tasks) * 100

    def by_type(self) -> Dict[str, List[TaskResult]]:
        """Group results by analyzer type"""
        by_type = {}
        for result in self.results:
            if result.analyzer_type not in by_type:
                by_type[result.analyzer_type] = []
            by_type[result.analyzer_type].append(result)
        return by_type


class ParallelExecutor:
    """Executes analysis tasks in parallel"""

    # Default timeouts per analyzer type (in seconds)
    DEFAULT_TIMEOUTS = {
        'jsp': 10.0,
        'controller': 15.0,
        'service': 15.0,
        'mybatis': 45.0,  # Longer for complex MyBatis XMLs
    }

    def __init__(
        self,
        analyzers: Dict[str, BaseTool],
        max_workers: int = 10,
        timeout_per_task: float = 30.0,
        timeouts_by_type: Optional[Dict[str, float]] = None,
        batch_size: int = 100
    ):
        """
        Initialize parallel executor

        Args:
            analyzers: Dictionary mapping analyzer type to analyzer instance
            max_workers: Maximum number of concurrent tasks
            timeout_per_task: Default timeout for each task in seconds
            timeouts_by_type: Custom timeouts per analyzer type
            batch_size: Number of tasks to process in each batch (prevents file descriptor exhaustion)
        """
        self.analyzers = analyzers
        self.max_workers = max_workers
        self.timeout_per_task = timeout_per_task
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_workers)

        # Merge default timeouts with custom timeouts
        self.timeouts = self.DEFAULT_TIMEOUTS.copy()
        if timeouts_by_type:
            self.timeouts.update(timeouts_by_type)

    async def execute_all(
        self,
        tasks: List[AnalysisTask],
        progress_callback: Optional[callable] = None
    ) -> BatchResult:
        """
        Execute all tasks in parallel with batching to prevent file descriptor exhaustion

        Args:
            tasks: List of analysis tasks
            progress_callback: Optional callback(completed, total) for progress updates

        Returns:
            BatchResult with all results
        """
        start_time = datetime.now()

        # Sort tasks by priority (higher priority first)
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

        # Process in batches to prevent file descriptor exhaustion
        all_results = []
        for i in range(0, len(sorted_tasks), self.batch_size):
            batch = sorted_tasks[i:i + self.batch_size]

            # Create async tasks for this batch
            async_tasks = [
                self._execute_task(task, progress_callback, len(tasks))
                for task in batch
            ]

            # Execute batch
            batch_results = await asyncio.gather(*async_tasks, return_exceptions=True)
            all_results.extend(batch_results)

        # Process results
        task_results = []
        completed = 0
        failed = 0

        for result in all_results:
            if isinstance(result, TaskResult):
                task_results.append(result)
                if result.success:
                    completed += 1
                else:
                    failed += 1
            elif isinstance(result, Exception):
                # Handle unexpected exceptions
                failed += 1
                task_results.append(TaskResult(
                    task_id="unknown",
                    analyzer_type="unknown",
                    identifier="unknown",
                    success=False,
                    error=f"Unexpected error: {str(result)}"
                ))

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return BatchResult(
            total_tasks=len(tasks),
            completed=completed,
            failed=failed,
            results=task_results,
            total_duration_seconds=duration,
            started_at=start_time,
            completed_at=end_time
        )

    async def _execute_task(
        self,
        task: AnalysisTask,
        progress_callback: Optional[callable],
        total_tasks: int
    ) -> TaskResult:
        """
        Execute a single task with semaphore control

        Args:
            task: AnalysisTask to execute
            progress_callback: Progress callback function
            total_tasks: Total number of tasks (for progress)

        Returns:
            TaskResult
        """
        async with self.semaphore:
            start_time = datetime.now()

            try:
                # Get analyzer
                analyzer = self.analyzers.get(task.analyzer_type)
                if not analyzer:
                    return TaskResult(
                        task_id=task.task_id,
                        analyzer_type=task.analyzer_type,
                        identifier=task.identifier,
                        success=False,
                        error=f"No analyzer found for type: {task.analyzer_type}"
                    )

                # Get timeout for this analyzer type
                timeout = self.timeouts.get(task.analyzer_type, self.timeout_per_task)

                # Execute analysis with type-specific timeout
                result = await asyncio.wait_for(
                    analyzer.analyze_async(
                        identifier=task.identifier,
                        context=task.context,
                        force_refresh=True  # Batch analysis always refreshes
                    ),
                    timeout=timeout
                )

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # Call progress callback if provided
                if progress_callback:
                    # This is a simplified progress tracking
                    # In reality, we'd need a shared counter
                    try:
                        progress_callback(1, total_tasks)
                    except Exception:
                        pass  # Ignore callback errors

                return TaskResult(
                    task_id=task.task_id,
                    analyzer_type=task.analyzer_type,
                    identifier=task.identifier,
                    success=True,
                    result=result,
                    duration_seconds=duration
                )

            except asyncio.TimeoutError:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # Get the timeout that was used for better error message
                timeout = self.timeouts.get(task.analyzer_type, self.timeout_per_task)

                return TaskResult(
                    task_id=task.task_id,
                    analyzer_type=task.analyzer_type,
                    identifier=task.identifier,
                    success=False,
                    error=f"Analysis timeout after {timeout}s",
                    duration_seconds=duration
                )

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                return TaskResult(
                    task_id=task.task_id,
                    analyzer_type=task.analyzer_type,
                    identifier=task.identifier,
                    success=False,
                    error=f"Analysis failed: {str(e)}",
                    duration_seconds=duration
                )

    async def execute_with_progress(
        self,
        tasks: List[AnalysisTask],
        show_progress: bool = True
    ) -> BatchResult:
        """
        Execute tasks with progress bar

        Args:
            tasks: List of analysis tasks
            show_progress: Whether to show progress output

        Returns:
            BatchResult
        """
        if not show_progress:
            return await self.execute_all(tasks)

        # Simple progress tracking
        completed_count = 0

        def progress_callback(delta: int, total: int):
            nonlocal completed_count
            completed_count += delta
            if show_progress:
                percentage = (completed_count / total) * 100
                print(f"\rProgress: {completed_count}/{total} ({percentage:.1f}%)", end='', flush=True)

        result = await self.execute_all(tasks, progress_callback)

        if show_progress:
            print()  # New line after progress

        return result


# CLI for testing
if __name__ == "__main__":
    import sys
    from .jsp_analyzer import JSPAnalyzer
    from .controller_analyzer import ControllerAnalyzer

    async def test_parallel_execution():
        # Create test analyzers
        analyzers = {
            'jsp': JSPAnalyzer(project_root="."),
            'controller': ControllerAnalyzer(project_root=".")
        }

        # Create test tasks
        tasks = [
            AnalysisTask(
                task_id="task_1",
                analyzer_type="jsp",
                identifier="test",
                context={"file_path": "test.jsp"}
            ),
            AnalysisTask(
                task_id="task_2",
                analyzer_type="controller",
                identifier="test",
                context={"file_path": "TestController.java"}
            )
        ]

        # Execute
        executor = ParallelExecutor(analyzers, max_workers=5)
        result = await executor.execute_with_progress(tasks)

        print(f"\nResults:")
        print(f"  Total: {result.total_tasks}")
        print(f"  Completed: {result.completed}")
        print(f"  Failed: {result.failed}")
        print(f"  Success Rate: {result.success_rate():.1f}%")
        print(f"  Duration: {result.total_duration_seconds:.2f}s")

    if __name__ == "__main__":
        asyncio.run(test_parallel_execution())
