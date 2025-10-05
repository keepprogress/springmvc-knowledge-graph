#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Node Builder - Phase 5.1.2

Creates graph nodes from Phase 3 analysis results.
Each node represents a component in the SpringMVC application.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# Node type definitions with visualization attributes
NODE_TYPES = {
    "JSP": {"color": "#FF6B6B", "shape": "box", "description": "JSP page"},
    "CONTROLLER": {"color": "#4ECDC4", "shape": "ellipse", "description": "Spring MVC Controller"},
    "CONTROLLER_METHOD": {"color": "#4ECDC4", "shape": "box", "description": "Controller request mapping method"},
    "SERVICE": {"color": "#45B7D1", "shape": "ellipse", "description": "Spring Service"},
    "SERVICE_METHOD": {"color": "#45B7D1", "shape": "box", "description": "Service business logic method"},
    "MAPPER": {"color": "#96CEB4", "shape": "ellipse", "description": "MyBatis Mapper interface"},
    "MAPPER_METHOD": {"color": "#96CEB4", "shape": "box", "description": "Mapper interface method"},
    "SQL_STATEMENT": {"color": "#E17055", "shape": "box", "description": "MyBatis SQL statement"},
    "TABLE": {"color": "#FFEAA7", "shape": "database", "description": "Database table"},
    "VIEW": {"color": "#DFE6E9", "shape": "database", "description": "Database view"},
    "PROCEDURE": {"color": "#A29BFE", "shape": "hexagon", "description": "Oracle stored procedure"},
    "TRIGGER": {"color": "#FD79A8", "shape": "diamond", "description": "Database trigger"},
    "ORACLE_JOB": {"color": "#FDCB6E", "shape": "star", "description": "Oracle scheduled job"},
}


class Node:
    """
    Represents a node in the knowledge graph.

    Attributes:
        id: Unique identifier (e.g., "JSP:user/list.jsp")
        type: Node type (from NODE_TYPES)
        name: Display name
        path: Full path or location
        metadata: Additional type-specific attributes
    """

    def __init__(self, id: str, node_type: str, name: str, path: str = "", metadata: Optional[Dict] = None):
        """
        Initialize a graph node.

        Args:
            id: Unique identifier
            node_type: Node type (must be in NODE_TYPES)
            name: Display name
            path: Full path or location
            metadata: Additional attributes
        """
        if node_type not in NODE_TYPES:
            raise ValueError(f"Invalid node type: {node_type}. Must be one of {list(NODE_TYPES.keys())}")

        self.id = id
        self.type = node_type
        self.name = name
        self.path = path
        self.metadata = metadata or {}

        # Add visualization attributes
        self.color = NODE_TYPES[node_type]["color"]
        self.shape = NODE_TYPES[node_type]["shape"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary format."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "color": self.color,
            "shape": self.shape,
            "metadata": self.metadata
        }

    def __eq__(self, other) -> bool:
        """
        Check equality based on node ID.

        Args:
            other: Another object to compare

        Returns:
            True if both are Node objects with same ID
        """
        if not isinstance(other, Node):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Hash based on node ID for use in sets and dicts.

        Returns:
            Hash of node ID
        """
        return hash(self.id)

    def __repr__(self) -> str:
        return f"Node(id='{self.id}', type='{self.type}', name='{self.name}')"


class NodeBuilder:
    """
    Builds graph nodes from Phase 3 analysis results.

    Uses GraphDataLoader to access analysis data and creates
    appropriate nodes for each component type.
    """

    def __init__(self, data_loader):
        """
        Initialize NodeBuilder.

        Args:
            data_loader: GraphDataLoader instance with loaded data
        """
        self.loader = data_loader
        self.nodes = []
        self.node_ids = set()  # For deduplication

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path to use forward slashes.

        Args:
            path: Path string (may contain backslashes on Windows)

        Returns:
            Normalized path with forward slashes
        """
        return path.replace("\\", "/")

    def _extract_class_identifier(self, class_name: str, package: str) -> str:
        """
        Extract clean class identifier.

        Args:
            class_name: Full file path or class name
            package: Package name (e.g., "com.example.controller")

        Returns:
            Clean identifier (e.g., "com.example.controller.UserController")
        """
        # Extract simple class name from path
        simple_name = Path(class_name).stem

        # Build qualified name
        if package:
            return f"{package}.{simple_name}"
        return simple_name

    def build_all_nodes(self) -> List[Node]:
        """
        Build all nodes from loaded analysis data.

        Returns:
            List of all created nodes
        """
        logger.info("Building all graph nodes...")

        self.nodes = []
        self.node_ids = set()

        # Build nodes for each component type
        self.nodes.extend(self.create_jsp_nodes())
        self.nodes.extend(self.create_controller_nodes())
        self.nodes.extend(self.create_service_nodes())
        self.nodes.extend(self.create_mapper_nodes())
        self.nodes.extend(self.create_sql_nodes())

        # Optional: Database nodes
        if self.loader.data.get("db_schema"):
            self.nodes.extend(self.create_database_nodes())

        logger.info(f"Created {len(self.nodes)} nodes total")
        return self.nodes

    def create_jsp_nodes(self) -> List[Node]:
        """
        Create JSP page nodes.

        Returns:
            List of JSP nodes
        """
        nodes = []

        for jsp_data in self.loader.data["jsp"]:
            file_path = self._normalize_path(self.loader.get_jsp_file_path(jsp_data))

            # Create unique ID
            node_id = f"JSP:{file_path}"

            # Skip duplicates
            if node_id in self.node_ids:
                continue

            # Extract display name (just filename)
            name = Path(file_path).name

            # Metadata
            metadata = {
                "static_includes": len(jsp_data.get("static_includes", [])),
                "dynamic_includes": len(jsp_data.get("dynamic_includes", [])),
                "forms": len(jsp_data.get("forms", [])),
                "ajax_calls": len(jsp_data.get("ajax_calls", [])),
                "taglibs": len(jsp_data.get("taglibs", [])),
                "el_expressions": len(jsp_data.get("el_expressions", [])),
            }

            node = Node(
                id=node_id,
                node_type="JSP",
                name=name,
                path=file_path,
                metadata=metadata
            )

            nodes.append(node)
            self.node_ids.add(node_id)

        logger.info(f"Created {len(nodes)} JSP nodes")
        return nodes

    def create_controller_nodes(self) -> List[Node]:
        """
        Create Controller and Controller Method nodes.

        Returns:
            List of Controller and ControllerMethod nodes
        """
        nodes = []

        for controller_data in self.loader.data["controllers"]:
            class_name_raw = self.loader.get_controller_class_name(controller_data)
            package = controller_data.get("package", "")
            base_path = self.loader.get_controller_base_path(controller_data)

            # Extract clean class identifier
            class_name = self._extract_class_identifier(class_name_raw, package)

            # Create Controller node
            controller_id = f"CONTROLLER:{class_name}"

            if controller_id not in self.node_ids:
                controller_node = Node(
                    id=controller_id,
                    node_type="CONTROLLER",
                    name=Path(class_name_raw).stem,  # Simple class name for display
                    path=self._normalize_path(class_name_raw),  # Original path
                    metadata={
                        "package": package,
                        "base_path": base_path,
                        "method_count": len(self.loader.get_controller_methods(controller_data)),
                        "class_identifier": class_name  # Clean identifier for matching
                    }
                )
                nodes.append(controller_node)
                self.node_ids.add(controller_id)

            # Create Controller Method nodes
            for method in self.loader.get_controller_methods(controller_data):
                method_name = method.get("name", "unknown")
                method_id = f"CONTROLLER_METHOD:{class_name}.{method_name}"

                if method_id in self.node_ids:
                    continue

                # Extract request mapping info
                request_mapping = method.get("request_mapping", {})
                path = request_mapping.get("path", "")
                http_method = request_mapping.get("method", "GET")

                # Build full URL path
                full_path = base_path + path if path else base_path

                method_node = Node(
                    id=method_id,
                    node_type="CONTROLLER_METHOD",
                    name=method_name,
                    path=f"{class_name}.{method_name}",
                    metadata={
                        "http_method": http_method,
                        "url_path": full_path,
                        "return_type": method.get("return_type", ""),
                        "parameters": method.get("parameters", []),
                        "annotations": [a.get("name", "") for a in method.get("annotations", [])]
                    }
                )

                nodes.append(method_node)
                self.node_ids.add(method_id)

        logger.info(f"Created {len(nodes)} Controller nodes (including methods)")
        return nodes

    def create_service_nodes(self) -> List[Node]:
        """
        Create Service and Service Method nodes.

        Returns:
            List of Service and ServiceMethod nodes
        """
        nodes = []

        for service_data in self.loader.data["services"]:
            class_name_raw = self.loader.get_service_class_name(service_data)
            package = service_data.get("package", "")

            # Extract clean class identifier
            class_name = self._extract_class_identifier(class_name_raw, package)

            # Create Service node
            service_id = f"SERVICE:{class_name}"

            if service_id not in self.node_ids:
                service_node = Node(
                    id=service_id,
                    node_type="SERVICE",
                    name=Path(class_name_raw).stem,
                    path=self._normalize_path(class_name_raw),
                    metadata={
                        "package": package,
                        "method_count": len(self.loader.get_service_methods(service_data)),
                        "dependency_count": len(self.loader.get_service_dependencies(service_data)),
                        "class_identifier": class_name
                    }
                )
                nodes.append(service_node)
                self.node_ids.add(service_id)

            # Create Service Method nodes
            for method in self.loader.get_service_methods(service_data):
                method_name = method.get("name", "unknown")
                method_id = f"SERVICE_METHOD:{class_name}.{method_name}"

                if method_id in self.node_ids:
                    continue

                method_node = Node(
                    id=method_id,
                    node_type="SERVICE_METHOD",
                    name=method_name,
                    path=f"{class_name}.{method_name}",
                    metadata={
                        "return_type": method.get("return_type", ""),
                        "parameters": method.get("parameters", []),
                        "annotations": [a.get("name", "") for a in method.get("annotations", [])],
                        "is_transactional": any(
                            a.get("name") == "Transactional"
                            for a in method.get("annotations", [])
                        )
                    }
                )

                nodes.append(method_node)
                self.node_ids.add(method_id)

        logger.info(f"Created {len(nodes)} Service nodes (including methods)")
        return nodes

    def create_mapper_nodes(self) -> List[Node]:
        """
        Create Mapper and Mapper Method nodes.

        Returns:
            List of Mapper and MapperMethod nodes
        """
        nodes = []

        for mapper_data in self.loader.data["mappers"]:
            namespace = self.loader.get_mapper_namespace(mapper_data)
            mapper_name = self.loader.get_mapper_name(mapper_data)

            # Create Mapper node
            mapper_id = f"MAPPER:{namespace}"

            if mapper_id not in self.node_ids:
                mapper_node = Node(
                    id=mapper_id,
                    node_type="MAPPER",
                    name=mapper_name,
                    path=namespace,
                    metadata={
                        "namespace": namespace,
                        "interface_methods": len(self.loader.get_mapper_interface_methods(mapper_data)),
                        "sql_statements": len(self.loader.get_mapper_statements(mapper_data))
                    }
                )
                nodes.append(mapper_node)
                self.node_ids.add(mapper_id)

            # Create Mapper Method nodes
            interface_methods = self.loader.get_mapper_interface_methods(mapper_data)
            for method in interface_methods:
                method_name = method.get("name", "unknown")
                method_id = f"MAPPER_METHOD:{namespace}.{method_name}"

                if method_id in self.node_ids:
                    continue

                method_node = Node(
                    id=method_id,
                    node_type="MAPPER_METHOD",
                    name=method_name,
                    path=f"{namespace}.{method_name}",
                    metadata={
                        "return_type": method.get("return_type", ""),
                        "parameters": method.get("parameters", []),
                        "annotations": [a.get("name", "") for a in method.get("annotations", [])]
                    }
                )

                nodes.append(method_node)
                self.node_ids.add(method_id)

        logger.info(f"Created {len(nodes)} Mapper nodes (including methods)")
        return nodes

    def _is_callable_statement(self, sql: str, stmt: Dict) -> bool:
        """
        Check if SQL statement is a stored procedure call.

        Args:
            sql: SQL statement text
            stmt: Statement dictionary with metadata

        Returns:
            True if this is a callable statement
        """
        if not sql:
            return False

        # Check for CALL keyword in SQL
        sql_upper = sql.upper().strip()
        if "CALL " in sql_upper or sql_upper.startswith("{CALL"):
            return True

        # Check statementType attribute (MyBatis specific)
        if stmt.get("statementType") == "CALLABLE":
            return True

        # Check for common procedure call patterns
        if sql_upper.startswith("EXEC ") or sql_upper.startswith("EXECUTE "):
            return True

        return False

    def _extract_procedure_name(self, sql: str) -> Optional[str]:
        """
        Extract procedure name from callable SQL statement.

        Args:
            sql: SQL statement text

        Returns:
            Procedure name or None if not found
        """
        import re

        if not sql:
            return None

        # Pattern 1: {CALL procedure_name(...)}
        match = re.search(r'\{?\s*CALL\s+(\w+)', sql, re.IGNORECASE)
        if match:
            return match.group(1)

        # Pattern 2: EXEC procedure_name ...
        match = re.search(r'EXEC(?:UTE)?\s+(\w+)', sql, re.IGNORECASE)
        if match:
            return match.group(1)

        # Pattern 3: Schema.procedure_name
        match = re.search(r'\{?\s*CALL\s+(\w+\.\w+)', sql, re.IGNORECASE)
        if match:
            # Return just the procedure name without schema
            parts = match.group(1).split('.')
            return parts[-1]

        return None

    def create_sql_nodes(self) -> List[Node]:
        """
        Create SQL statement nodes from MyBatis Mapper XML.

        Returns:
            List of SQL statement nodes
        """
        nodes = []

        for mapper_data in self.loader.data["mappers"]:
            namespace = self.loader.get_mapper_namespace(mapper_data)
            statements = self.loader.get_mapper_statements(mapper_data)

            for stmt in statements:
                stmt_id = stmt.get("id", "unknown")
                stmt_type = stmt.get("type", "SELECT")

                # Create unique ID
                node_id = f"SQL:{namespace}.{stmt_id}"

                if node_id in self.node_ids:
                    continue

                # Check if this is a callable statement (stored procedure call)
                sql = stmt.get("sql", "")
                is_callable = self._is_callable_statement(sql, stmt)

                # Extract procedure name if callable
                procedure_name = None
                if is_callable:
                    procedure_name = self._extract_procedure_name(sql)

                # Metadata
                metadata = {
                    "sql_type": stmt_type,
                    "result_type": stmt.get("result_type", ""),
                    "result_map": stmt.get("result_map", ""),
                    "parameter_type": stmt.get("parameter_type", ""),
                    "parameters": stmt.get("parameters", []),
                    "tables": stmt.get("tables", []),
                    "dynamic_sql": stmt.get("dynamic_sql", False),
                    "sql": stmt.get("sql", "")[:200],  # First 200 chars for preview
                    "is_callable": is_callable,
                    "procedure_name": procedure_name
                }

                node = Node(
                    id=node_id,
                    node_type="SQL_STATEMENT",
                    name=f"{stmt_id} ({stmt_type})",
                    path=f"{namespace}.{stmt_id}",
                    metadata=metadata
                )

                nodes.append(node)
                self.node_ids.add(node_id)

        logger.info(f"Created {len(nodes)} SQL statement nodes")
        return nodes

    def create_database_nodes(self) -> List[Node]:
        """
        Create database nodes (Tables, Views, Procedures, Triggers, Jobs).

        Requires db_schema to be loaded.

        Returns:
            List of database nodes
        """
        nodes = []
        db_schema = self.loader.data.get("db_schema")

        if not db_schema:
            logger.info("No database schema loaded, skipping database nodes")
            return nodes

        # Create Table nodes
        for table in db_schema.get("tables", []):
            table_name = table.get("table_name", "unknown")
            node_id = f"TABLE:{table_name}"

            if node_id in self.node_ids:
                continue

            node = Node(
                id=node_id,
                node_type="TABLE",
                name=table_name,
                path=table_name,
                metadata={
                    "columns": len(table.get("columns", [])),
                    "primary_keys": table.get("primary_keys", []),
                    "indexes": len(table.get("indexes", [])),
                    "foreign_keys": len(table.get("foreign_keys", [])),
                    "triggers": len(table.get("triggers", []))
                }
            )

            nodes.append(node)
            self.node_ids.add(node_id)

        # Create View nodes
        for view in db_schema.get("views", []):
            view_name = view.get("view_name", "unknown")
            node_id = f"VIEW:{view_name}"

            if node_id in self.node_ids:
                continue

            node = Node(
                id=node_id,
                node_type="VIEW",
                name=view_name,
                path=view_name,
                metadata={
                    "columns": len(view.get("columns", [])),
                    "text_length": len(view.get("text", ""))
                }
            )

            nodes.append(node)
            self.node_ids.add(node_id)

        # Create Procedure nodes
        for proc in db_schema.get("procedures", []):
            proc_name = proc.get("object_name", "unknown")
            node_id = f"PROCEDURE:{proc_name}"

            if node_id in self.node_ids:
                continue

            node = Node(
                id=node_id,
                node_type="PROCEDURE",
                name=proc_name,
                path=proc_name,
                metadata={
                    "object_type": proc.get("object_type", "PROCEDURE"),
                    "parameters": len(proc.get("parameters", [])),
                    "source_lines": len(proc.get("source", []))
                }
            )

            nodes.append(node)
            self.node_ids.add(node_id)

        logger.info(f"Created {len(nodes)} database nodes")
        return nodes

    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """
        Get node by ID.

        Args:
            node_id: Node ID to find

        Returns:
            Node if found, None otherwise
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """
        Get all nodes of a specific type.

        Args:
            node_type: Node type to filter by

        Returns:
            List of nodes of the specified type
        """
        return [node for node in self.nodes if node.type == node_type]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of created nodes.

        Returns:
            Summary dictionary with counts by type
        """
        summary = {
            "total_nodes": len(self.nodes),
            "by_type": {}
        }

        for node_type in NODE_TYPES.keys():
            count = len(self.get_nodes_by_type(node_type))
            if count > 0:
                summary["by_type"][node_type] = count

        return summary
