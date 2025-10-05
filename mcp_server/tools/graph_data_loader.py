#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Data Loader - Phase 5.1.1

Loads all Phase 3 analysis results for knowledge graph construction.
Supports partial data loading and provides validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class GraphDataLoader:
    """
    Loads all analysis results from Phase 3 analyzers.

    Supports:
    - JSP analysis results
    - Controller analysis results
    - Service analysis results
    - MyBatis Mapper analysis results
    - Oracle DB schema (optional)
    - Procedure analysis results (optional)

    Handles missing files gracefully and validates JSON structure.
    """

    def __init__(self, base_dir: str = "output"):
        """
        Initialize data loader.

        Args:
            base_dir: Base directory for all analysis outputs (default: "output")
        """
        self.base_dir = Path(base_dir)
        self.analysis_dir = self.base_dir / "analysis"

        # Track loaded data
        self.data = {
            "jsp": [],
            "controllers": [],
            "services": [],
            "mappers": [],
            "db_schema": None,
            "procedures": []
        }

        # Track validation issues
        self.validation_issues = []

    def load_all_analysis_results(self) -> Dict[str, Any]:
        """
        Load all Phase 3 analysis results.

        Returns:
            Dict containing all loaded data with keys:
                - jsp: List[Dict]
                - controllers: List[Dict]
                - services: List[Dict]
                - mappers: List[Dict]
                - db_schema: Dict (optional)
                - procedures: List[Dict] (optional)
                - validation_issues: List[str]
        """
        logger.info(f"Loading analysis results from {self.base_dir}")

        # Load required components
        self.data["jsp"] = self.load_jsp_analysis()
        self.data["controllers"] = self.load_controller_analysis()
        self.data["services"] = self.load_service_analysis()
        self.data["mappers"] = self.load_mybatis_analysis()

        # Load optional components
        self.data["db_schema"] = self.load_db_schema()
        self.data["procedures"] = self.load_procedure_analysis()

        # Add validation issues to result
        self.data["validation_issues"] = self.validation_issues

        # Summary
        logger.info(f"Loaded: {len(self.data['jsp'])} JSP, "
                   f"{len(self.data['controllers'])} Controllers, "
                   f"{len(self.data['services'])} Services, "
                   f"{len(self.data['mappers'])} Mappers")

        if self.data["db_schema"]:
            logger.info("Loaded: DB Schema")

        if self.data["procedures"]:
            logger.info(f"Loaded: {len(self.data['procedures'])} Procedures")

        if self.validation_issues:
            logger.warning(f"Found {len(self.validation_issues)} validation issues")

        return self.data

    def load_jsp_analysis(self) -> List[Dict]:
        """
        Load JSP analysis results.

        Returns:
            List of JSP analysis dictionaries
        """
        jsp_dir = self.analysis_dir / "jsp"
        return self._load_json_files(jsp_dir, "JSP")

    def load_controller_analysis(self) -> List[Dict]:
        """
        Load Controller analysis results.

        Returns:
            List of Controller analysis dictionaries
        """
        controller_dir = self.analysis_dir / "controllers"
        return self._load_json_files(controller_dir, "Controller")

    def load_service_analysis(self) -> List[Dict]:
        """
        Load Service analysis results.

        Returns:
            List of Service analysis dictionaries
        """
        service_dir = self.analysis_dir / "services"
        return self._load_json_files(service_dir, "Service")

    def load_mybatis_analysis(self) -> List[Dict]:
        """
        Load MyBatis Mapper analysis results.

        Returns:
            List of Mapper analysis dictionaries
        """
        mapper_dir = self.analysis_dir / "mappers"
        return self._load_json_files(mapper_dir, "MyBatis Mapper")

    def load_db_schema(self) -> Optional[Dict]:
        """
        Load Oracle DB schema (optional).

        Returns:
            DB schema dictionary or None if not found
        """
        schema_file = self.base_dir / "db_schema.json"

        if not schema_file.exists():
            logger.info("DB schema file not found (optional)")
            return None

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            logger.info(f"Loaded DB schema from {schema_file}")
            return schema
        except json.JSONDecodeError as e:
            self.validation_issues.append(f"Invalid JSON in {schema_file}: {e}")
            logger.error(f"Failed to parse {schema_file}: {e}")
            return None
        except Exception as e:
            self.validation_issues.append(f"Error loading {schema_file}: {e}")
            logger.error(f"Error loading {schema_file}: {e}")
            return None

    def load_procedure_analysis(self) -> List[Dict]:
        """
        Load Procedure analysis results (optional).

        Returns:
            List of Procedure analysis dictionaries
        """
        procedure_dir = self.analysis_dir / "procedures"

        if not procedure_dir.exists():
            logger.info("Procedure analysis directory not found (optional)")
            return []

        return self._load_json_files(procedure_dir, "Procedure", required=False)

    def _load_json_files(self, directory: Path, component_type: str,
                        required: bool = True) -> List[Dict]:
        """
        Load all JSON files from a directory.

        Args:
            directory: Directory containing JSON files
            component_type: Type of component (for logging)
            required: Whether this directory is required

        Returns:
            List of parsed JSON dictionaries
        """
        if not directory.exists():
            msg = f"{component_type} directory not found: {directory}"
            if required:
                self.validation_issues.append(msg)
                logger.warning(msg)
            else:
                logger.info(f"{msg} (optional)")
            return []

        results = []
        json_files = list(directory.glob("*.json"))

        if not json_files:
            msg = f"No JSON files found in {directory}"
            if required:
                self.validation_issues.append(msg)
                logger.warning(msg)
            return []

        for json_file in json_files:
            # Skip summary files
            if json_file.name.startswith("_"):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Add source file info
                data["_source_file"] = str(json_file.relative_to(self.base_dir))

                results.append(data)
                logger.debug(f"Loaded {component_type}: {json_file.name}")

            except json.JSONDecodeError as e:
                msg = f"Invalid JSON in {json_file}: {e}"
                self.validation_issues.append(msg)
                logger.error(msg)

            except Exception as e:
                msg = f"Error loading {json_file}: {e}"
                self.validation_issues.append(msg)
                logger.error(msg)

        logger.info(f"Loaded {len(results)} {component_type} files from {directory}")
        return results

    def validate_data(self) -> bool:
        """
        Validate loaded data structure.

        Returns:
            True if data is valid for graph construction, False otherwise
        """
        # Check if we have at least some data
        has_data = (len(self.data["jsp"]) > 0 or
                   len(self.data["controllers"]) > 0 or
                   len(self.data["services"]) > 0 or
                   len(self.data["mappers"]) > 0)

        if not has_data:
            logger.error("No analysis data loaded - cannot build graph")
            return False

        # Validate individual components
        self._validate_jsp_data()
        self._validate_controller_data()
        self._validate_service_data()
        self._validate_mapper_data()

        return len(self.validation_issues) == 0

    def _validate_jsp_data(self):
        """Validate JSP analysis data structure."""
        for jsp in self.data["jsp"]:
            # JSP analyzer outputs "file" not "file_path"
            if "file" not in jsp:
                self.validation_issues.append(
                    f"JSP analysis missing 'file': {jsp.get('_source_file', 'unknown')}"
                )

    def _validate_controller_data(self):
        """Validate Controller analysis data structure."""
        for controller in self.data["controllers"]:
            if "class_name" not in controller:
                self.validation_issues.append(
                    f"Controller analysis missing 'class_name': {controller.get('_source_file', 'unknown')}"
                )
            if "methods" not in controller:
                self.validation_issues.append(
                    f"Controller analysis missing 'methods': {controller.get('_source_file', 'unknown')}"
                )

    def _validate_service_data(self):
        """Validate Service analysis data structure."""
        for service in self.data["services"]:
            if "class_name" not in service:
                self.validation_issues.append(
                    f"Service analysis missing 'class_name': {service.get('_source_file', 'unknown')}"
                )
            if "methods" not in service:
                self.validation_issues.append(
                    f"Service analysis missing 'methods': {service.get('_source_file', 'unknown')}"
                )

    def _validate_mapper_data(self):
        """Validate MyBatis Mapper analysis data structure."""
        for mapper in self.data["mappers"]:
            # MyBatis analyzer outputs nested structure with "xml" key
            if "xml" not in mapper:
                self.validation_issues.append(
                    f"Mapper analysis missing 'xml' section: {mapper.get('_source_file', 'unknown')}"
                )
                continue

            xml = mapper["xml"]
            if "namespace" not in xml:
                self.validation_issues.append(
                    f"Mapper analysis missing 'xml.namespace': {mapper.get('_source_file', 'unknown')}"
                )
            if "statements" not in xml:
                self.validation_issues.append(
                    f"Mapper analysis missing 'xml.statements': {mapper.get('_source_file', 'unknown')}"
                )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of loaded data.

        Returns:
            Summary dictionary with counts, details, and validation status
        """
        # Calculate detailed statistics
        total_controller_methods = sum(
            len(c.get("methods", [])) for c in self.data["controllers"]
        )
        total_service_methods = sum(
            len(s.get("methods", [])) for s in self.data["services"]
        )
        total_mapper_statements = sum(
            len(m.get("xml", {}).get("statements", [])) for m in self.data["mappers"]
        )

        return {
            "counts": {
                "jsp": len(self.data["jsp"]),
                "controllers": len(self.data["controllers"]),
                "services": len(self.data["services"]),
                "mappers": len(self.data["mappers"]),
                "procedures": len(self.data["procedures"]),
                "has_db_schema": self.data["db_schema"] is not None
            },
            "details": {
                "total_controller_methods": total_controller_methods,
                "total_service_methods": total_service_methods,
                "total_mapper_statements": total_mapper_statements
            },
            "validation": {
                "issues_count": len(self.validation_issues),
                "issues": self.validation_issues,
                "is_valid": len(self.validation_issues) == 0
            }
        }

    # ============================================================================
    # Data Access Helper Methods
    # ============================================================================
    # These methods abstract the analyzer output structure and provide safe
    # access to nested fields. This encapsulation makes downstream components
    # (Phase 5.1.2+) cleaner and more maintainable.

    def get_jsp_file_path(self, jsp_data: Dict) -> str:
        """
        Get file path from JSP analysis data.

        Args:
            jsp_data: JSP analysis dictionary

        Returns:
            File path string
        """
        return jsp_data.get("file", "")

    def get_controller_class_name(self, controller_data: Dict) -> str:
        """
        Get class name from Controller analysis data.

        Args:
            controller_data: Controller analysis dictionary

        Returns:
            Class name string
        """
        return controller_data.get("class_name", "")

    def get_controller_base_path(self, controller_data: Dict) -> str:
        """
        Get base path from Controller analysis data.

        Args:
            controller_data: Controller analysis dictionary

        Returns:
            Base path string (e.g., "/user")
        """
        return controller_data.get("base_path", "")

    def get_controller_methods(self, controller_data: Dict) -> List[Dict]:
        """
        Get methods from Controller analysis data.

        Args:
            controller_data: Controller analysis dictionary

        Returns:
            List of method dictionaries
        """
        return controller_data.get("methods", [])

    def get_service_class_name(self, service_data: Dict) -> str:
        """
        Get class name from Service analysis data.

        Args:
            service_data: Service analysis dictionary

        Returns:
            Class name string
        """
        return service_data.get("class_name", "")

    def get_service_methods(self, service_data: Dict) -> List[Dict]:
        """
        Get methods from Service analysis data.

        Args:
            service_data: Service analysis dictionary

        Returns:
            List of method dictionaries
        """
        return service_data.get("methods", [])

    def get_service_dependencies(self, service_data: Dict) -> List[Dict]:
        """
        Get dependencies from Service analysis data.

        Args:
            service_data: Service analysis dictionary

        Returns:
            List of dependency dictionaries
        """
        return service_data.get("dependencies", [])

    def get_mapper_name(self, mapper_data: Dict) -> str:
        """
        Get mapper name from Mapper analysis data.

        Args:
            mapper_data: Mapper analysis dictionary

        Returns:
            Mapper name string (e.g., "UserMapper")
        """
        return mapper_data.get("mapper_name", "")

    def get_mapper_namespace(self, mapper_data: Dict) -> str:
        """
        Get namespace from Mapper analysis data.

        Args:
            mapper_data: Mapper analysis dictionary

        Returns:
            Namespace string (e.g., "com.example.mapper.UserMapper")
        """
        return mapper_data.get("xml", {}).get("namespace", "")

    def get_mapper_statements(self, mapper_data: Dict) -> List[Dict]:
        """
        Get statements from Mapper analysis data.

        Args:
            mapper_data: Mapper analysis dictionary

        Returns:
            List of SQL statement dictionaries
        """
        return mapper_data.get("xml", {}).get("statements", [])

    def get_mapper_interface_methods(self, mapper_data: Dict) -> List[Dict]:
        """
        Get interface methods from Mapper analysis data.

        Args:
            mapper_data: Mapper analysis dictionary

        Returns:
            List of interface method dictionaries
        """
        return mapper_data.get("interface", {}).get("methods", [])

    # ============================================================================
    # Convenience Query Methods
    # ============================================================================

    def get_all_jsp_files(self) -> List[str]:
        """
        Get list of all JSP file paths.

        Returns:
            List of JSP file path strings
        """
        return [self.get_jsp_file_path(jsp) for jsp in self.data["jsp"]]

    def get_all_controller_classes(self) -> List[str]:
        """
        Get list of all controller class names.

        Returns:
            List of controller class name strings
        """
        return [self.get_controller_class_name(c) for c in self.data["controllers"]]

    def get_all_service_classes(self) -> List[str]:
        """
        Get list of all service class names.

        Returns:
            List of service class name strings
        """
        return [self.get_service_class_name(s) for s in self.data["services"]]

    def get_all_mapper_namespaces(self) -> List[str]:
        """
        Get list of all mapper namespaces.

        Returns:
            List of mapper namespace strings
        """
        return [self.get_mapper_namespace(m) for m in self.data["mappers"]]

    def find_controller_by_path(self, base_path: str) -> Optional[Dict]:
        """
        Find controller by base path.

        Args:
            base_path: Controller base path (e.g., "/user")

        Returns:
            Controller data dictionary or None if not found
        """
        for controller in self.data["controllers"]:
            if self.get_controller_base_path(controller) == base_path:
                return controller
        return None

    def find_service_by_class_name(self, class_name: str) -> Optional[Dict]:
        """
        Find service by class name.

        Args:
            class_name: Service class name

        Returns:
            Service data dictionary or None if not found
        """
        for service in self.data["services"]:
            if self.get_service_class_name(service) == class_name:
                return service
        return None

    def find_mapper_by_namespace(self, namespace: str) -> Optional[Dict]:
        """
        Find mapper by namespace.

        Args:
            namespace: Mapper namespace (e.g., "com.example.mapper.UserMapper")

        Returns:
            Mapper data dictionary or None if not found
        """
        for mapper in self.data["mappers"]:
            if self.get_mapper_namespace(mapper) == namespace:
                return mapper
        return None
