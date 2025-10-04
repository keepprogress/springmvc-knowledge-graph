#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progress Tracker

Real-time progress reporting for batch analysis
"""

import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ProgressInfo:
    """Progress information"""
    current: int
    total: int
    percentage: float
    current_file: str
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0

    def format_time(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


class ProgressTracker:
    """Tracks and displays analysis progress"""

    def __init__(self, total_tasks: int, show_progress: bool = True):
        self.total_tasks = total_tasks
        self.show_progress = show_progress
        self.completed_count = 0
        self.start_time = datetime.now()
        self.last_file = ""

    def update(self, current_file: str):
        """
        Update progress with current file

        Args:
            current_file: Name of file being processed
        """
        self.completed_count += 1
        self.last_file = current_file

        if self.show_progress:
            self._display_progress()

    def _display_progress(self):
        """Display progress bar"""
        if self.total_tasks == 0:
            return

        percentage = (self.completed_count / self.total_tasks) * 100
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # Calculate ETA
        if self.completed_count > 0:
            avg_time_per_task = elapsed / self.completed_count
            remaining_tasks = self.total_tasks - self.completed_count
            eta = avg_time_per_task * remaining_tasks
        else:
            eta = 0.0

        # Progress bar
        bar_width = 30
        filled = int(bar_width * percentage / 100)
        bar = '█' * filled + '░' * (bar_width - filled)

        # Truncate filename if too long
        display_file = self.last_file
        if len(display_file) > 40:
            display_file = "..." + display_file[-37:]

        # Format output
        progress_info = ProgressInfo(
            current=self.completed_count,
            total=self.total_tasks,
            percentage=percentage,
            current_file=display_file,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=eta
        )

        output = (
            f"\r[{bar}] {percentage:5.1f}% | "
            f"{self.completed_count}/{self.total_tasks} | "
            f"Elapsed: {progress_info.format_time(elapsed)} | "
            f"ETA: {progress_info.format_time(eta)} | "
            f"{display_file}"
        )

        # Write to stderr to not interfere with stdout
        print(output, end='', file=sys.stderr, flush=True)

    def finish(self):
        """Mark progress as complete"""
        if self.show_progress:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"\n✓ Completed {self.total_tasks} tasks in {ProgressInfo(0, 0, 0, '').format_time(elapsed)}", file=sys.stderr)

    def get_info(self) -> ProgressInfo:
        """Get current progress information"""
        percentage = (self.completed_count / self.total_tasks) * 100 if self.total_tasks > 0 else 0.0
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if self.completed_count > 0:
            avg_time = elapsed / self.completed_count
            eta = avg_time * (self.total_tasks - self.completed_count)
        else:
            eta = 0.0

        return ProgressInfo(
            current=self.completed_count,
            total=self.total_tasks,
            percentage=percentage,
            current_file=self.last_file,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=eta
        )
