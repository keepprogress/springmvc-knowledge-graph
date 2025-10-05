#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Edge Builder - Phase 5.1.3

Creates graph edges representing relationships between nodes.
Each edge has a type, confidence score, and source information.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


# Edge type definitions with confidence ranges and descriptions
EDGE_TYPES = {
    "INCLUDES": {
        "confidence": 1.0,
        "source": "static_include",
        "description": "JSP includes another JSP"
    },
    "CALLS": {
        "confidence_range": (0.6, 1.0),
        "source": "url_pattern",
        "description": "JSP calls Controller via AJAX/form"
    },
    "INVOKES": {
        "confidence": 1.0,
        "source": "autowired",
        "description": "Controller invokes Service method"
    },
    "USES": {
        "confidence": 1.0,
        "source": "dependency_injection",
        "description": "Service uses Mapper"
    },
    "EXECUTES": {
        "confidence": 1.0,
        "source": "mapper_xml",
        "description": "Mapper method executes SQL statement"
    },
    "QUERIES": {
        "confidence_range": (0.8, 1.0),
        "source": "sql_parse",
        "description": "SQL queries database table (SELECT)"
    },
    "MODIFIES": {
        "confidence_range": (0.8, 1.0),
        "source": "sql_parse",
        "description": "SQL modifies database table (INSERT/UPDATE/DELETE)"
    },
    "CALLS_PROCEDURE": {
        "confidence": 1.0,
        "source": "callable_statement",
        "description": "SQL calls stored procedure"
    },
    "TRIGGERED_BY": {
        "confidence": 1.0,
        "source": "db_trigger",
        "description": "Procedure triggered by database trigger"
    },
    "SCHEDULED_BY": {
        "confidence": 1.0,
        "source": "oracle_job",
        "description": "Procedure scheduled by Oracle job"
    }
}


class Edge:
    """
    Represents an edge (relationship) in the knowledge graph.

    Attributes:
        source: Source node ID
        target: Target node ID
        edge_type: Edge type (from EDGE_TYPES)
        confidence: Confidence score (0.0-1.0)
        metadata: Additional edge-specific attributes
    """

    def __init__(self, source: str, target: str, edge_type: str,
                 confidence: float = 1.0, metadata: Optional[Dict] = None):
        """
        Initialize a graph edge.

        Args:
            source: Source node ID
            target: Target node ID
            edge_type: Edge type (must be in EDGE_TYPES)
            confidence: Confidence score (0.0-1.0)
            metadata: Additional attributes
        """
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"Invalid edge type: {edge_type}. Must be one of {list(EDGE_TYPES.keys())}")

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        self.source = source
        self.target = target
        self.type = edge_type
        self.confidence = confidence
        self.metadata = metadata or {}

        # Add edge type metadata
        self.source_type = EDGE_TYPES[edge_type]["source"]
        self.description = EDGE_TYPES[edge_type]["description"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary format."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "description": self.description,
            "metadata": self.metadata
        }

    def __eq__(self, other) -> bool:
        """Check equality based on source, target, and type."""
        if not isinstance(other, Edge):
            return False
        return (self.source == other.source and
                self.target == other.target and
                self.type == other.type)

    def __hash__(self) -> int:
        """Hash based on source, target, and type."""
        return hash((self.source, self.target, self.type))

    def __repr__(self) -> str:
        return f"Edge('{self.source}' --{self.type}({self.confidence:.2f})--> '{self.target}')"


class EdgeBuilder:
    """
    Builds graph edges from nodes.

    Uses node information to create edges representing relationships
    in the SpringMVC application.
    """

    def __init__(self, node_builder):
        """
        Initialize EdgeBuilder.

        Args:
            node_builder: NodeBuilder instance with created nodes
        """
        self.node_builder = node_builder
        self.edges = []
        self.edge_set = set()  # For deduplication

    def build_all_edges(self) -> List[Edge]:
        """
        Build all edges from created nodes.

        Returns:
            List of all created edges
        """
        logger.info("Building all graph edges...")

        self.edges = []
        self.edge_set = set()

        # Get nodes by type
        jsp_nodes = self.node_builder.get_nodes_by_type("JSP")
        controller_nodes = self.node_builder.get_nodes_by_type("CONTROLLER")
        controller_method_nodes = self.node_builder.get_nodes_by_type("CONTROLLER_METHOD")
        service_nodes = self.node_builder.get_nodes_by_type("SERVICE")
        service_method_nodes = self.node_builder.get_nodes_by_type("SERVICE_METHOD")
        mapper_nodes = self.node_builder.get_nodes_by_type("MAPPER")
        mapper_method_nodes = self.node_builder.get_nodes_by_type("MAPPER_METHOD")
        sql_nodes = self.node_builder.get_nodes_by_type("SQL_STATEMENT")
        table_nodes = self.node_builder.get_nodes_by_type("TABLE")
        procedure_nodes = self.node_builder.get_nodes_by_type("PROCEDURE")

        # Build edges for each relationship type
        self.edges.extend(self.build_jsp_includes(jsp_nodes))
        self.edges.extend(self.build_controller_to_service(controller_method_nodes, service_method_nodes))
        self.edges.extend(self.build_service_to_mapper(service_method_nodes, mapper_method_nodes))
        self.edges.extend(self.build_mapper_to_sql(mapper_method_nodes, sql_nodes))

        if table_nodes:
            self.edges.extend(self.build_sql_to_tables(sql_nodes, table_nodes))

        if procedure_nodes:
            self.edges.extend(self.build_sql_to_procedures(sql_nodes, procedure_nodes))

        logger.info(f"Created {len(self.edges)} edges total")
        return self.edges

    def build_jsp_includes(self, jsp_nodes: List) -> List[Edge]:
        """
        Build JSP include edges (JSP -> JSP).

        Args:
            jsp_nodes: List of JSP nodes

        Returns:
            List of INCLUDES edges
        """
        edges = []

        for jsp_node in jsp_nodes:
            # Get static includes from JSP metadata
            static_includes = jsp_node.metadata.get("static_includes", [])

            # Note: static_includes from analyzer are currently counts, not actual paths
            # This will be enhanced when JSP analyzer provides actual include paths

        logger.info(f"Created {len(edges)} JSP INCLUDES edges")
        return edges

    def build_controller_to_service(self, controller_method_nodes: List,
                                    service_method_nodes: List) -> List[Edge]:
        """
        Build Controller -> Service invocation edges.

        Args:
            controller_method_nodes: List of controller method nodes
            service_method_nodes: List of service method nodes

        Returns:
            List of INVOKES edges
        """
        edges = []

        # Get controller data from loader
        for controller_data in self.node_builder.loader.data["controllers"]:
            controller_class = self.node_builder._extract_class_identifier(
                controller_data.get("class_name", ""),
                controller_data.get("package", "")
            )

            # Process each method in controller
            for method in controller_data.get("methods", []):
                method_name = method.get("name", "")
                controller_method_id = f"CONTROLLER_METHOD:{controller_class}.{method_name}"

                # Analyze service calls in method
                service_calls = method.get("service_calls", [])

                # Find service dependencies from controller
                dependencies = controller_data.get("dependencies", [])
                service_deps = {
                    dep.get("name", ""): dep.get("type", "")
                    for dep in dependencies
                    if dep.get("is_service", False)
                }

                # Create edges for service method calls
                for call in service_calls:
                    call_method = call.get("method", "")
                    call_variable = call.get("variable", "")  # e.g., "userService"

                    # Find service type from dependencies
                    service_type = service_deps.get(call_variable)
                    if not service_type:
                        continue

                    # Try exact match first
                    service_method_id = f"SERVICE_METHOD:{service_type}.{call_method}"
                    service_method_node = self.node_builder.get_node_by_id(service_method_id)

                    # If no exact match, try fuzzy matching by class name
                    if not service_method_node:
                        class_name = service_type.split('.')[-1]  # Get "UserService" from "com.example.service.UserService"

                        # Search all service methods for matching class name
                        for service_method in service_method_nodes:
                            if f".{class_name}.{call_method}" in service_method.id:
                                service_method_id = service_method.id
                                service_method_node = service_method
                                break

                    # Create edge if service method found
                    if service_method_node:
                        edge = Edge(
                            source=controller_method_id,
                            target=service_method_id,
                            edge_type="INVOKES",
                            confidence=1.0,
                            metadata={
                                "service_variable": call_variable,
                                "method_call": call_method
                            }
                        )

                        if edge not in self.edge_set:
                            edges.append(edge)
                            self.edge_set.add(edge)

        logger.info(f"Created {len(edges)} Controller INVOKES Service edges")
        return edges

    def build_service_to_mapper(self, service_method_nodes: List,
                               mapper_method_nodes: List) -> List[Edge]:
        """
        Build Service -> Mapper usage edges.

        Args:
            service_method_nodes: List of service method nodes
            mapper_method_nodes: List of mapper method nodes

        Returns:
            List of USES edges
        """
        edges = []

        # Get service data from loader
        for service_data in self.node_builder.loader.data["services"]:
            service_class = self.node_builder._extract_class_identifier(
                service_data.get("class_name", ""),
                service_data.get("package", "")
            )

            # Get mapper dependencies
            dependencies = service_data.get("dependencies", [])
            mapper_deps = {
                dep.get("name", ""): dep.get("type", "")
                for dep in dependencies
                if "Mapper" in dep.get("type", "")
            }

            # Process each method
            for method in service_data.get("methods", []):
                method_name = method.get("name", "")
                service_method_id = f"SERVICE_METHOD:{service_class}.{method_name}"

                # Analyze mapper calls
                mapper_calls = method.get("mapper_calls", [])

                # Match mapper calls with actual mapper methods
                for call in mapper_calls:
                    call_method = call.get("method", "")

                    # Find matching mapper method node
                    for mapper_dep_name, mapper_type in mapper_deps.items():
                        # Try exact match first
                        mapper_method_id = f"MAPPER_METHOD:{mapper_type}.{call_method}"
                        mapper_method_node = self.node_builder.get_node_by_id(mapper_method_id)

                        # If no exact match, try fuzzy matching by class name
                        if not mapper_method_node:
                            class_name = mapper_type.split('.')[-1]  # Get "OrderMapper" from "com.example.mapper.OrderMapper"

                            # Search all mapper methods for matching class name
                            for mapper_method in mapper_method_nodes:
                                if f".{class_name}.{call_method}" in mapper_method.id:
                                    mapper_method_id = mapper_method.id
                                    mapper_method_node = mapper_method
                                    break

                        # Create edge if mapper method found
                        if mapper_method_node:
                            edge = Edge(
                                source=service_method_id,
                                target=mapper_method_id,
                                edge_type="USES",
                                confidence=1.0,
                                metadata={
                                    "mapper_variable": mapper_dep_name,
                                    "method_call": call_method
                                }
                            )

                            if edge not in self.edge_set:
                                edges.append(edge)
                                self.edge_set.add(edge)
                            break  # Found match, no need to check other mapper dependencies

        logger.info(f"Created {len(edges)} Service USES Mapper edges")
        return edges

    def build_mapper_to_sql(self, mapper_method_nodes: List,
                           sql_nodes: List) -> List[Edge]:
        """
        Build Mapper -> SQL execution edges.

        Args:
            mapper_method_nodes: List of mapper method nodes
            sql_nodes: List of SQL statement nodes

        Returns:
            List of EXECUTES edges
        """
        edges = []

        # Get mapper data from loader
        for mapper_data in self.node_builder.loader.data["mappers"]:
            namespace = self.node_builder.loader.get_mapper_namespace(mapper_data)

            # Get method to statement mapping
            method_to_stmt = mapper_data.get("method_to_statement_mapping", {})

            # Create edges for each mapping
            for method_name, stmt_id in method_to_stmt.items():
                mapper_method_id = f"MAPPER_METHOD:{namespace}.{method_name}"
                sql_id = f"SQL:{namespace}.{stmt_id}"

                # Verify both nodes exist
                mapper_method_node = self.node_builder.get_node_by_id(mapper_method_id)
                sql_node = self.node_builder.get_node_by_id(sql_id)

                if mapper_method_node and sql_node:
                    edge = Edge(
                        source=mapper_method_id,
                        target=sql_id,
                        edge_type="EXECUTES",
                        confidence=1.0,
                        metadata={
                            "statement_id": stmt_id,
                            "namespace": namespace
                        }
                    )

                    if edge not in self.edge_set:
                        edges.append(edge)
                        self.edge_set.add(edge)

        logger.info(f"Created {len(edges)} Mapper EXECUTES SQL edges")
        return edges

    def build_sql_to_tables(self, sql_nodes: List, table_nodes: List) -> List[Edge]:
        """
        Build SQL -> Table edges (QUERIES/MODIFIES).

        Args:
            sql_nodes: List of SQL statement nodes
            table_nodes: List of table nodes

        Returns:
            List of QUERIES/MODIFIES edges
        """
        edges = []

        for sql_node in sql_nodes:
            sql_type = sql_node.metadata.get("sql_type", "SELECT")
            tables = sql_node.metadata.get("tables", [])

            # Determine edge type based on SQL type
            if sql_type == "SELECT":
                edge_type = "QUERIES"
            else:  # INSERT, UPDATE, DELETE
                edge_type = "MODIFIES"

            # Create edges to each table
            for table_name in tables:
                table_id = f"TABLE:{table_name.upper()}"

                # Check if table node exists
                table_node = self.node_builder.get_node_by_id(table_id)
                if table_node:
                    edge = Edge(
                        source=sql_node.id,
                        target=table_id,
                        edge_type=edge_type,
                        confidence=1.0,  # High confidence from parser
                        metadata={
                            "sql_type": sql_type,
                            "table_name": table_name
                        }
                    )

                    if edge not in self.edge_set:
                        edges.append(edge)
                        self.edge_set.add(edge)

        logger.info(f"Created {len(edges)} SQL to Table edges (QUERIES/MODIFIES)")
        return edges

    def build_sql_to_procedures(self, sql_nodes: List,
                               procedure_nodes: List) -> List[Edge]:
        """
        Build SQL -> Procedure edges (CALLS_PROCEDURE).

        Args:
            sql_nodes: List of SQL statement nodes
            procedure_nodes: List of procedure nodes

        Returns:
            List of CALLS_PROCEDURE edges
        """
        edges = []

        for sql_node in sql_nodes:
            # Check if this is a callable statement
            is_callable = sql_node.metadata.get("is_callable", False)
            procedure_name = sql_node.metadata.get("procedure_name")

            if is_callable and procedure_name:
                procedure_id = f"PROCEDURE:{procedure_name.upper()}"

                # Check if procedure node exists
                procedure_node = self.node_builder.get_node_by_id(procedure_id)
                if procedure_node:
                    edge = Edge(
                        source=sql_node.id,
                        target=procedure_id,
                        edge_type="CALLS_PROCEDURE",
                        confidence=1.0,
                        metadata={
                            "procedure_name": procedure_name,
                            "sql": sql_node.metadata.get("sql", "")[:100]
                        }
                    )

                    if edge not in self.edge_set:
                        edges.append(edge)
                        self.edge_set.add(edge)

        logger.info(f"Created {len(edges)} SQL CALLS_PROCEDURE edges")
        return edges

    def get_edges_by_type(self, edge_type: str) -> List[Edge]:
        """
        Get all edges of a specific type.

        Args:
            edge_type: Edge type to filter by

        Returns:
            List of edges of the specified type
        """
        return [edge for edge in self.edges if edge.type == edge_type]

    def get_edges_from_node(self, node_id: str) -> List[Edge]:
        """
        Get all edges originating from a specific node.

        Args:
            node_id: Source node ID

        Returns:
            List of edges from this node
        """
        return [edge for edge in self.edges if edge.source == node_id]

    def get_edges_to_node(self, node_id: str) -> List[Edge]:
        """
        Get all edges targeting a specific node.

        Args:
            node_id: Target node ID

        Returns:
            List of edges to this node
        """
        return [edge for edge in self.edges if edge.target == node_id]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of created edges.

        Returns:
            Summary dictionary with counts by type
        """
        summary = {
            "total_edges": len(self.edges),
            "by_type": {},
            "average_confidence": 0.0
        }

        # Count by type
        for edge_type in EDGE_TYPES.keys():
            count = len(self.get_edges_by_type(edge_type))
            if count > 0:
                summary["by_type"][edge_type] = count

        # Calculate average confidence
        if self.edges:
            total_confidence = sum(edge.confidence for edge in self.edges)
            summary["average_confidence"] = total_confidence / len(self.edges)

        return summary
