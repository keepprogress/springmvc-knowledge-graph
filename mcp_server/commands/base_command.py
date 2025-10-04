#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Command Class for Slash Commands

Provides common functionality for all slash commands
"""

import argparse
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def validate_args(func: Callable) -> Callable:
    """
    Decorator to handle argument parsing errors consistently

    Catches SystemExit from argparse and converts to error response.
    Also catches general exceptions during command execution.
    """
    @wraps(func)
    async def wrapper(self, args: List[str]) -> Dict[str, Any]:
        try:
            return await func(self, args)
        except SystemExit:
            return self.format_error(
                f"Invalid arguments. Use '/{self.get_name()} --help' for usage information."
            )
        except Exception as e:
            return self.format_error(f"Command failed: {str(e)}")
    return wrapper


class BaseCommand(ABC):
    """Base class for all slash commands"""

    def __init__(self, server):
        """
        Initialize command

        Args:
            server: SpringMVCMCPServer instance
        """
        self.server = server
        self.parser = self._create_parser()

    @abstractmethod
    def get_name(self) -> str:
        """Return command name (e.g., 'analyze-jsp')"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return command description"""
        pass

    @abstractmethod
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for this command"""
        pass

    @abstractmethod
    async def execute(self, args: List[str]) -> Dict[str, Any]:
        """
        Execute the command

        Args:
            args: Command arguments (excluding command name)

        Returns:
            Result dictionary with success status and data
        """
        pass

    def parse_args(self, args: List[str]) -> argparse.Namespace:
        """
        Parse command arguments

        Args:
            args: Command arguments

        Returns:
            Parsed arguments

        Raises:
            SystemExit: If parsing fails (caught by caller)
        """
        return self.parser.parse_args(args)

    def format_success(self, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format success response"""
        result = {
            "success": True,
            "message": message
        }
        if data:
            result["data"] = data
        return result

    def format_error(self, error: str) -> Dict[str, Any]:
        """Format error response"""
        return {
            "success": False,
            "error": error
        }

    def resolve_path(self, file_path: str) -> Path:
        """
        Resolve file path relative to project root

        Args:
            file_path: Relative or absolute file path

        Returns:
            Resolved Path object
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.server.project_root / path
        return path
