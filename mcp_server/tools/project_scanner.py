#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Scanner

Scans project structure and detects source directories
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ProjectStructure:
    """Project structure information"""
    project_root: Path
    project_type: str  # 'maven', 'gradle', 'unknown'
    webapp_dir: Optional[Path] = None
    java_dirs: List[Path] = None
    resource_dirs: List[Path] = None
    test_dirs: List[Path] = None

    def __post_init__(self):
        if self.java_dirs is None:
            self.java_dirs = []
        if self.resource_dirs is None:
            self.resource_dirs = []
        if self.test_dirs is None:
            self.test_dirs = []


class ProjectScanner:
    """Scans project structure and identifies source directories"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def scan(self) -> ProjectStructure:
        """
        Scan project and return structure

        Returns:
            ProjectStructure with detected directories
        """
        project_type = self._detect_project_type()

        structure = ProjectStructure(
            project_root=self.project_root,
            project_type=project_type
        )

        # Detect directories based on project type
        if project_type == 'maven':
            structure.webapp_dir = self._find_maven_webapp_dir()
            structure.java_dirs = self._find_maven_java_dirs()
            structure.resource_dirs = self._find_maven_resource_dirs()
            structure.test_dirs = self._find_maven_test_dirs()
        elif project_type == 'gradle':
            structure.webapp_dir = self._find_gradle_webapp_dir()
            structure.java_dirs = self._find_gradle_java_dirs()
            structure.resource_dirs = self._find_gradle_resource_dirs()
            structure.test_dirs = self._find_gradle_test_dirs()
        else:
            # Unknown project type - try generic detection
            structure.webapp_dir = self._find_generic_webapp_dir()
            structure.java_dirs = self._find_generic_java_dirs()
            structure.resource_dirs = self._find_generic_resource_dirs()

        return structure

    def _detect_project_type(self) -> str:
        """
        Detect project build system type

        Returns:
            'maven', 'gradle', or 'unknown'
        """
        # Check for Maven
        if (self.project_root / 'pom.xml').exists():
            return 'maven'

        # Check for Gradle
        gradle_files = [
            'build.gradle',
            'build.gradle.kts',
            'settings.gradle',
            'settings.gradle.kts'
        ]
        if any((self.project_root / f).exists() for f in gradle_files):
            return 'gradle'

        return 'unknown'

    # Maven-specific detection
    def _find_maven_webapp_dir(self) -> Optional[Path]:
        """Find Maven webapp directory"""
        webapp_path = self.project_root / 'src' / 'main' / 'webapp'
        return webapp_path if webapp_path.exists() else None

    def _find_maven_java_dirs(self) -> List[Path]:
        """Find Maven Java source directories"""
        dirs = []
        main_java = self.project_root / 'src' / 'main' / 'java'
        if main_java.exists():
            dirs.append(main_java)
        return dirs

    def _find_maven_resource_dirs(self) -> List[Path]:
        """Find Maven resource directories"""
        dirs = []
        main_resources = self.project_root / 'src' / 'main' / 'resources'
        if main_resources.exists():
            dirs.append(main_resources)
        return dirs

    def _find_maven_test_dirs(self) -> List[Path]:
        """Find Maven test directories"""
        dirs = []
        test_java = self.project_root / 'src' / 'test' / 'java'
        if test_java.exists():
            dirs.append(test_java)
        return dirs

    # Gradle-specific detection
    def _find_gradle_webapp_dir(self) -> Optional[Path]:
        """Find Gradle webapp directory"""
        # Try standard Gradle webapp location
        webapp_path = self.project_root / 'src' / 'main' / 'webapp'
        if webapp_path.exists():
            return webapp_path

        # Try alternative Gradle locations
        alt_path = self.project_root / 'webapp'
        if alt_path.exists():
            return alt_path

        return None

    def _find_gradle_java_dirs(self) -> List[Path]:
        """Find Gradle Java source directories"""
        dirs = []
        main_java = self.project_root / 'src' / 'main' / 'java'
        if main_java.exists():
            dirs.append(main_java)
        return dirs

    def _find_gradle_resource_dirs(self) -> List[Path]:
        """Find Gradle resource directories"""
        dirs = []
        main_resources = self.project_root / 'src' / 'main' / 'resources'
        if main_resources.exists():
            dirs.append(main_resources)
        return dirs

    def _find_gradle_test_dirs(self) -> List[Path]:
        """Find Gradle test directories"""
        dirs = []
        test_java = self.project_root / 'src' / 'test' / 'java'
        if test_java.exists():
            dirs.append(test_java)
        return dirs

    # Generic detection (fallback)
    def _find_generic_webapp_dir(self) -> Optional[Path]:
        """Find webapp directory using generic patterns"""
        # Common webapp directory names
        webapp_names = ['webapp', 'web', 'WebContent', 'public']

        for name in webapp_names:
            # Check root level
            path = self.project_root / name
            if path.exists() and path.is_dir():
                return path

            # Check src/main level
            src_main_path = self.project_root / 'src' / 'main' / name
            if src_main_path.exists() and src_main_path.is_dir():
                return src_main_path

        return None

    def _find_generic_java_dirs(self) -> List[Path]:
        """Find Java source directories using generic patterns"""
        dirs = []

        # Common Java source locations
        candidates = [
            self.project_root / 'src' / 'main' / 'java',
            self.project_root / 'src' / 'java',
            self.project_root / 'src',
            self.project_root / 'java',
        ]

        for path in candidates:
            if path.exists() and path.is_dir():
                # Check if it contains .java files
                if self._contains_java_files(path):
                    dirs.append(path)

        return dirs

    def _find_generic_resource_dirs(self) -> List[Path]:
        """Find resource directories using generic patterns"""
        dirs = []

        # Common resource locations
        candidates = [
            self.project_root / 'src' / 'main' / 'resources',
            self.project_root / 'src' / 'resources',
            self.project_root / 'resources',
        ]

        for path in candidates:
            if path.exists() and path.is_dir():
                dirs.append(path)

        return dirs

    def _contains_java_files(self, directory: Path, max_depth: int = 3) -> bool:
        """
        Check if directory contains Java files (recursively up to max_depth)

        Args:
            directory: Directory to check
            max_depth: Maximum depth to search

        Returns:
            True if Java files found
        """
        try:
            # Quick check for .java files
            for path in directory.rglob('*.java'):
                # Calculate depth
                try:
                    relative = path.relative_to(directory)
                    depth = len(relative.parts) - 1
                    if depth <= max_depth:
                        return True
                except ValueError:
                    continue
        except Exception:
            pass

        return False

    def get_all_source_files(self, structure: ProjectStructure, extensions: List[str]) -> List[Path]:
        """
        Get all source files with specified extensions

        Args:
            structure: ProjectStructure to scan
            extensions: File extensions to find (e.g., ['.java', '.xml'])

        Returns:
            List of matching file paths
        """
        files = []

        # Scan Java directories
        for java_dir in structure.java_dirs:
            for ext in extensions:
                files.extend(java_dir.rglob(f'*{ext}'))

        # Scan resource directories
        for res_dir in structure.resource_dirs:
            for ext in extensions:
                files.extend(res_dir.rglob(f'*{ext}'))

        # Scan webapp directory
        if structure.webapp_dir:
            for ext in extensions:
                files.extend(structure.webapp_dir.rglob(f'*{ext}'))

        return sorted(set(files))  # Remove duplicates and sort


# CLI for testing
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python project_scanner.py <project_root>")
        sys.exit(1)

    scanner = ProjectScanner(sys.argv[1])
    structure = scanner.scan()

    # Print structure as JSON
    result = {
        "project_root": str(structure.project_root),
        "project_type": structure.project_type,
        "webapp_dir": str(structure.webapp_dir) if structure.webapp_dir else None,
        "java_dirs": [str(d) for d in structure.java_dirs],
        "resource_dirs": [str(d) for d in structure.resource_dirs],
        "test_dirs": [str(d) for d in structure.test_dirs],
    }

    print(json.dumps(result, indent=2))

    # Show some statistics
    print(f"\nStatistics:", file=sys.stderr)
    print(f"  Java files: {len(scanner.get_all_source_files(structure, ['.java']))}", file=sys.stderr)
    print(f"  XML files: {len(scanner.get_all_source_files(structure, ['.xml']))}", file=sys.stderr)
    print(f"  JSP files: {len(scanner.get_all_source_files(structure, ['.jsp']))}", file=sys.stderr)
