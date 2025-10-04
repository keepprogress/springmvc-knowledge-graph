#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pattern Detector

Detects and categorizes analyzable files by pattern
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from .project_scanner import ProjectStructure


@dataclass
class DetectedFiles:
    """Detected files by type"""
    jsp_files: List[Path]
    controller_files: List[Path]
    service_files: List[Path]
    mapper_interfaces: List[Path]
    mapper_xmls: List[Path]
    entity_files: List[Path]

    def total_count(self) -> int:
        """Return total number of detected files"""
        return (
            len(self.jsp_files) +
            len(self.controller_files) +
            len(self.service_files) +
            len(self.mapper_interfaces) +
            len(self.mapper_xmls) +
            len(self.entity_files)
        )

    def by_type_count(self) -> Dict[str, int]:
        """Return count by type"""
        return {
            'jsp': len(self.jsp_files),
            'controller': len(self.controller_files),
            'service': len(self.service_files),
            'mapper_interface': len(self.mapper_interfaces),
            'mapper_xml': len(self.mapper_xmls),
            'entity': len(self.entity_files)
        }


class PatternDetector:
    """Detects files by pattern matching"""

    # File patterns for different component types
    PATTERNS = {
        'jsp': '**/*.jsp',
        'controller': '**/*Controller.java',
        'service': '**/*Service.java',
        'service_impl': '**/*ServiceImpl.java',
        'mapper_interface': '**/*Mapper.java',
        'mapper_xml': '**/*Mapper.xml',
        'entity': ['**/*Entity.java', '**/*DO.java', '**/*DTO.java', '**/*VO.java'],
    }

    def __init__(self, project_structure: ProjectStructure):
        self.structure = project_structure

    def detect_all(self, file_types: List[str] = None) -> DetectedFiles:
        """
        Detect all files by type

        Args:
            file_types: List of types to detect, or None for all
                       Choices: 'jsp', 'controller', 'service', 'mybatis', 'entity', 'all'

        Returns:
            DetectedFiles with all detected files
        """
        if file_types is None or 'all' in file_types:
            file_types = ['jsp', 'controller', 'service', 'mybatis', 'entity']

        detected = DetectedFiles(
            jsp_files=[],
            controller_files=[],
            service_files=[],
            mapper_interfaces=[],
            mapper_xmls=[],
            entity_files=[]
        )

        if 'jsp' in file_types:
            detected.jsp_files = self._detect_jsp_files()

        if 'controller' in file_types:
            detected.controller_files = self._detect_controller_files()

        if 'service' in file_types:
            detected.service_files = self._detect_service_files()

        if 'mybatis' in file_types:
            detected.mapper_interfaces = self._detect_mapper_interfaces()
            detected.mapper_xmls = self._detect_mapper_xmls()

        if 'entity' in file_types:
            detected.entity_files = self._detect_entity_files()

        return detected

    def _detect_jsp_files(self) -> List[Path]:
        """Detect JSP files"""
        if not self.structure.webapp_dir:
            return []

        jsp_files = list(self.structure.webapp_dir.rglob('*.jsp'))
        return sorted(jsp_files)

    def _detect_controller_files(self) -> List[Path]:
        """Detect Spring MVC Controller files"""
        controller_files = set()

        for java_dir in self.structure.java_dirs:
            # Pattern: *Controller.java
            for file in java_dir.rglob('*Controller.java'):
                controller_files.add(file)

        return sorted(list(controller_files))

    def _detect_service_files(self) -> List[Path]:
        """Detect Spring Service files"""
        service_files = set()

        for java_dir in self.structure.java_dirs:
            # Pattern: *Service.java and *ServiceImpl.java
            for file in java_dir.rglob('*Service.java'):
                service_files.add(file)

            for file in java_dir.rglob('*ServiceImpl.java'):
                service_files.add(file)

        return sorted(list(service_files))

    def _detect_mapper_interfaces(self) -> List[Path]:
        """Detect MyBatis Mapper interface files"""
        mapper_files = set()

        for java_dir in self.structure.java_dirs:
            # Pattern: *Mapper.java
            for file in java_dir.rglob('*Mapper.java'):
                mapper_files.add(file)

        return sorted(list(mapper_files))

    def _detect_mapper_xmls(self) -> List[Path]:
        """Detect MyBatis Mapper XML files"""
        xml_files = set()

        # Check resource directories
        for res_dir in self.structure.resource_dirs:
            for file in res_dir.rglob('*Mapper.xml'):
                xml_files.add(file)

        # Also check Java directories (some projects put XML alongside Java)
        for java_dir in self.structure.java_dirs:
            for file in java_dir.rglob('*Mapper.xml'):
                xml_files.add(file)

        return sorted(list(xml_files))

    def _detect_entity_files(self) -> List[Path]:
        """Detect Entity/DTO/VO files"""
        entity_files = set()

        for java_dir in self.structure.java_dirs:
            # Multiple patterns for entity files
            for pattern in ['*Entity.java', '*DO.java', '*DTO.java', '*VO.java']:
                for file in java_dir.rglob(pattern):
                    entity_files.add(file)

        return sorted(list(entity_files))

    def match_mapper_pairs(
        self,
        mapper_interfaces: List[Path],
        mapper_xmls: List[Path]
    ) -> Dict[Path, Path]:
        """
        Match Mapper interfaces with their corresponding XML files

        Args:
            mapper_interfaces: List of Mapper interface files
            mapper_xmls: List of Mapper XML files

        Returns:
            Dictionary mapping interface Path to XML Path
        """
        pairs = {}

        # Create a mapping of base names to XML paths
        xml_by_name = {}
        for xml_file in mapper_xmls:
            base_name = xml_file.stem  # e.g., "UserMapper" from "UserMapper.xml"
            xml_by_name[base_name] = xml_file

        # Match interfaces to XMLs
        for interface_file in mapper_interfaces:
            base_name = interface_file.stem  # e.g., "UserMapper" from "UserMapper.java"
            if base_name in xml_by_name:
                pairs[interface_file] = xml_by_name[base_name]

        return pairs

    def get_analysis_tasks(self, detected: DetectedFiles) -> List[Dict[str, any]]:
        """
        Convert detected files to analysis tasks

        Args:
            detected: DetectedFiles with all detected files

        Returns:
            List of analysis tasks with type and file info
        """
        tasks = []

        # JSP tasks
        for jsp_file in detected.jsp_files:
            tasks.append({
                'type': 'jsp',
                'file': jsp_file,
                'identifier': jsp_file.stem
            })

        # Controller tasks
        for controller_file in detected.controller_files:
            tasks.append({
                'type': 'controller',
                'file': controller_file,
                'identifier': controller_file.stem
            })

        # Service tasks
        for service_file in detected.service_files:
            tasks.append({
                'type': 'service',
                'file': service_file,
                'identifier': service_file.stem
            })

        # MyBatis tasks (match interfaces with XMLs)
        mapper_pairs = self.match_mapper_pairs(
            detected.mapper_interfaces,
            detected.mapper_xmls
        )

        for interface_file, xml_file in mapper_pairs.items():
            tasks.append({
                'type': 'mybatis',
                'interface_file': interface_file,
                'xml_file': xml_file,
                'identifier': interface_file.stem
            })

        # Unmatched mapper interfaces (interface-only)
        matched_interfaces = set(mapper_pairs.keys())
        for interface_file in detected.mapper_interfaces:
            if interface_file not in matched_interfaces:
                tasks.append({
                    'type': 'mybatis',
                    'interface_file': interface_file,
                    'xml_file': None,
                    'identifier': interface_file.stem
                })

        return tasks


# CLI for testing
if __name__ == "__main__":
    import sys
    import json
    from .project_scanner import ProjectScanner

    if len(sys.argv) < 2:
        print("Usage: python pattern_detector.py <project_root>")
        sys.exit(1)

    # Scan project
    scanner = ProjectScanner(sys.argv[1])
    structure = scanner.scan()

    # Detect files
    detector = PatternDetector(structure)
    detected = detector.detect_all()

    # Print results
    print(f"Detected Files:")
    print(f"  JSP: {len(detected.jsp_files)}")
    print(f"  Controllers: {len(detected.controller_files)}")
    print(f"  Services: {len(detected.service_files)}")
    print(f"  Mapper Interfaces: {len(detected.mapper_interfaces)}")
    print(f"  Mapper XMLs: {len(detected.mapper_xmls)}")
    print(f"  Entities: {len(detected.entity_files)}")
    print(f"  Total: {detected.total_count()}")

    # Show mapper pairs
    pairs = detector.match_mapper_pairs(detected.mapper_interfaces, detected.mapper_xmls)
    print(f"\nMapper Pairs: {len(pairs)}")

    # Show analysis tasks
    tasks = detector.get_analysis_tasks(detected)
    print(f"\nAnalysis Tasks: {len(tasks)}")
    print(f"  By type: {json.dumps({t: sum(1 for task in tasks if task['type'] == t) for t in ['jsp', 'controller', 'service', 'mybatis']}, indent=2)}")
