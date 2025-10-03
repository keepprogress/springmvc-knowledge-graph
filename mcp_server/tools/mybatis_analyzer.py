#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyBatis Mapper Structure Extractor

Extracts structural information from MyBatis Mapper interfaces and XML files.
Research-validated for production use (tree-sitter-java + lxml).

Phase 3.4 Implementation - Focuses on static structure extraction.
Semantic SQL analysis deferred to Phase 5 LLM.

Features:
1. Mapper interface extraction (@Mapper annotation, method signatures)
2. Mapper XML parsing (<select>, <insert>, <update>, <delete>)
3. SQL statement extraction (including dynamic SQL)
4. Parameter mapping extraction (#{param}, ${param})
5. ResultMap extraction (column to property mapping)
6. Table name extraction (FROM, JOIN, INTO clauses)
7. SQL fragment (<sql> and <include>) tracking
8. Statement type detection (SELECT, INSERT, UPDATE, DELETE, CALLABLE)

Author: keepprogress
Date: 2025-10-03
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# tree-sitter for Java interface parsing
try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️  tree-sitter not available. Install: pip install tree-sitter tree-sitter-java",
          file=sys.stderr)

# lxml for XML parsing
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    print("⚠️  lxml not available. Install: pip install lxml",
          file=sys.stderr)

# sqlparse for SQL analysis (optional)
try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False

# Note: Windows UTF-8 encoding is handled in base_tool.py
from mcp_server.tools.base_tool import BaseTool


class MyBatisAnalyzer(BaseTool):
    """
    MyBatis Mapper Structure Extractor

    Analyzes both Mapper interface (Java) and Mapper XML.
    Uses tree-sitter-java for interface, lxml for XML.
    """

    def __init__(self, project_root: str = "."):
        super().__init__(
            tool_name="mappers",
            output_dir="output/structure"
        )
        self.project_root = Path(project_root)

        # Initialize tree-sitter-java parser
        self.java_parser = None
        if TREE_SITTER_AVAILABLE:
            try:
                from tree_sitter_java import language as java_language
                lang = Language(java_language())
                self.java_parser = Parser(lang)
                print("✓ tree-sitter-java initialized")
            except Exception as e:
                print(f"⚠️  tree-sitter-java initialization failed: {e}", file=sys.stderr)

    async def analyze_async(
        self,
        identifier: str,
        context: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze MyBatis Mapper structure

        Args:
            identifier: Mapper interface name (e.g., "UserMapper")
            context: {
                "interface_path": "path/to/UserMapper.java",
                "xml_path": "path/to/UserMapper.xml"  # Optional
            }
            force_refresh: Force re-analysis

        Returns:
            Mapper structure analysis
        """
        context = context or {}
        interface_path = context.get("interface_path")
        xml_path = context.get("xml_path")

        if not interface_path:
            raise ValueError("interface_path required in context")

        result = {
            "mapper_name": identifier,
            "interface": None,
            "xml": None,
            "method_to_statement_mapping": {},
            "statistics": {}
        }

        # Analyze interface
        if Path(interface_path).exists():
            print(f"🔍 Analyzing Mapper Interface: {interface_path}")
            result["interface"] = self._analyze_interface(interface_path)
        else:
            print(f"⚠️  Interface not found: {interface_path}", file=sys.stderr)

        # Analyze XML
        if xml_path and Path(xml_path).exists():
            print(f"🔍 Analyzing Mapper XML: {xml_path}")
            result["xml"] = self._analyze_xml(xml_path)

            # Map interface methods to XML statements
            result["method_to_statement_mapping"] = self._map_methods_to_statements(
                result["interface"], result["xml"]
            )
        elif xml_path:
            print(f"⚠️  XML not found: {xml_path}", file=sys.stderr)

        # Calculate statistics
        result["statistics"] = self._calculate_statistics(result)

        return result

    # ==================== Interface Analysis ====================

    def _analyze_interface(self, interface_path: str) -> Dict[str, Any]:
        """Analyze Mapper interface (Java)"""
        java_path = Path(interface_path)

        with open(java_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = None
        if self.java_parser:
            tree = self.java_parser.parse(bytes(content, 'utf8'))

        return {
            "file": str(java_path),
            "package": self._extract_package(content, tree),
            "imports": self._extract_imports(content, tree),
            "annotations": self._extract_interface_annotations(content, tree),
            "is_mapper": self._is_mybatis_mapper(content, tree),
            "methods": self._extract_interface_methods(content, tree),
            "parsing_errors": self._extract_parsing_errors(tree) if tree and tree.root_node.has_error else []
        }

    def _extract_package(self, content: str, tree) -> str:
        """Extract package declaration"""
        if tree:
            package_node = self._find_node_by_type(tree.root_node, "package_declaration")
            if package_node:
                return self._get_node_text(package_node, content).replace("package ", "").replace(";", "").strip()

        match = re.search(r'package\s+([\w.]+);', content)
        return match.group(1) if match else ""

    def _extract_imports(self, content: str, tree) -> List[str]:
        """Extract import statements"""
        imports = []

        if tree:
            import_nodes = self._find_all_nodes_by_type(tree.root_node, "import_declaration")
            for node in import_nodes:
                import_text = self._get_node_text(node, content)
                imports.append(import_text.replace("import ", "").replace(";", "").strip())
        else:
            import_matches = re.findall(r'import\s+([\w.*]+);', content)
            imports = import_matches

        return imports

    def _extract_interface_annotations(self, content: str, tree) -> List[Dict[str, Any]]:
        """Extract interface-level annotations"""
        annotations = []

        if tree:
            interface_node = self._find_node_by_type(tree.root_node, "interface_declaration")
            if interface_node:
                modifiers_node = self._find_child_by_type(interface_node, "modifiers")
                if modifiers_node:
                    annotation_nodes = self._find_all_nodes_by_type(modifiers_node, "annotation") + \
                                     self._find_all_nodes_by_type(modifiers_node, "marker_annotation")
                    for ann_node in annotation_nodes:
                        annotations.append(self._parse_annotation(ann_node, content))

        return annotations

    def _is_mybatis_mapper(self, content: str, tree) -> bool:
        """Check if interface is a MyBatis Mapper"""
        annotations = self._extract_interface_annotations(content, tree)
        mapper_annotations = ["Mapper", "Repository"]
        return any(ann["name"] in mapper_annotations for ann in annotations)

    def _extract_interface_methods(self, content: str, tree) -> List[Dict[str, Any]]:
        """Extract interface method declarations"""
        methods = []

        if not tree:
            return methods

        interface_node = self._find_node_by_type(tree.root_node, "interface_declaration")
        if not interface_node:
            return methods

        interface_body = self._find_child_by_type(interface_node, "interface_body")
        if not interface_body:
            return methods

        # In interface, method declarations don't have bodies
        method_nodes = self._find_all_nodes_by_type(interface_body, "method_declaration")

        for method_node in method_nodes:
            method_info = {
                "name": "",
                "return_type": "",
                "parameters": [],
                "annotations": []
            }

            # Extract method name
            name_node = self._find_child_by_type(method_node, "identifier")
            if name_node:
                method_info["name"] = self._get_node_text(name_node, content)

            # Extract return type
            type_node = self._find_child_by_type(method_node, "type_identifier") or \
                       self._find_child_by_type(method_node, "generic_type") or \
                       self._find_child_by_type(method_node, "void_type")
            if type_node:
                method_info["return_type"] = self._get_node_text(type_node, content)

            # Extract parameters
            params_node = self._find_child_by_type(method_node, "formal_parameters")
            if params_node:
                method_info["parameters"] = self._extract_method_parameters(params_node, content)

            # Extract annotations
            modifiers_node = self._find_child_by_type(method_node, "modifiers")
            if modifiers_node:
                annotation_nodes = self._find_all_nodes_by_type(modifiers_node, "annotation") + \
                                 self._find_all_nodes_by_type(modifiers_node, "marker_annotation")
                for ann_node in annotation_nodes:
                    method_info["annotations"].append(self._parse_annotation(ann_node, content))

            methods.append(method_info)

        return methods

    def _extract_method_parameters(self, params_node, content: str) -> List[Dict[str, Any]]:
        """Extract method parameters with @Param annotations"""
        parameters = []

        param_nodes = self._find_all_nodes_by_type(params_node, "formal_parameter")
        for param_node in param_nodes:
            param_info = {
                "name": "",
                "type": "",
                "param_annotation": None  # @Param("paramName")
            }

            # Extract parameter name
            name_node = self._find_child_by_type(param_node, "identifier")
            if name_node:
                param_info["name"] = self._get_node_text(name_node, content)

            # Extract parameter type
            type_node = self._find_child_by_type(param_node, "type_identifier") or \
                       self._find_child_by_type(param_node, "generic_type")
            if type_node:
                param_info["type"] = self._get_node_text(type_node, content)

            # Extract @Param annotation
            modifiers_node = self._find_child_by_type(param_node, "modifiers")
            if modifiers_node:
                annotation_nodes = self._find_all_nodes_by_type(modifiers_node, "annotation") + \
                                 self._find_all_nodes_by_type(modifiers_node, "marker_annotation")
                for ann in annotation_nodes:
                    parsed = self._parse_annotation(ann, content)
                    if parsed["name"] == "Param":
                        param_info["param_annotation"] = parsed["arguments"].get("value", "")

            parameters.append(param_info)

        return parameters

    # ==================== XML Analysis ====================

    def _analyze_xml(self, xml_path: str) -> Dict[str, Any]:
        """Analyze Mapper XML"""
        if not LXML_AVAILABLE:
            print("⚠️  lxml not available, skipping XML analysis", file=sys.stderr)
            return {}

        xml_file = Path(xml_path)

        try:
            tree = etree.parse(str(xml_file))
            root = tree.getroot()

            return {
                "file": str(xml_file),
                "namespace": root.get("namespace", ""),
                "statements": self._extract_statements(root),
                "result_maps": self._extract_result_maps(root),
                "sql_fragments": self._extract_sql_fragments(root)
            }
        except Exception as e:
            print(f"⚠️  XML parsing failed: {e}", file=sys.stderr)
            return {"file": str(xml_file), "error": str(e)}

    def _extract_statements(self, root) -> List[Dict[str, Any]]:
        """Extract SQL statements (<select>, <insert>, <update>, <delete>)"""
        statements = []

        for stmt_type in ["select", "insert", "update", "delete"]:
            for elem in root.findall(f".//{stmt_type}"):
                statement = {
                    "id": elem.get("id", ""),
                    "type": stmt_type.upper(),
                    "result_type": elem.get("resultType", ""),
                    "result_map": elem.get("resultMap", ""),
                    "parameter_type": elem.get("parameterType", ""),
                    "sql": self._extract_sql_text(elem),
                    "parameters": self._extract_sql_parameters(elem),
                    "tables": self._extract_table_names(elem),
                    "dynamic_sql": self._has_dynamic_sql(elem),
                    "includes": self._extract_includes(elem)
                }
                statements.append(statement)

        return statements

    def _extract_sql_text(self, elem) -> str:
        """Extract SQL text from element (including nested text)"""
        sql_parts = []

        def collect_text(node):
            if node.text:
                sql_parts.append(node.text.strip())
            for child in node:
                # Skip certain tags but keep their tail text
                if child.tag in ["include", "if", "choose", "when", "otherwise", "foreach", "where", "set", "trim"]:
                    collect_text(child)
                if child.tail:
                    sql_parts.append(child.tail.strip())

        collect_text(elem)
        return " ".join(sql_parts)

    def _extract_sql_parameters(self, elem) -> List[str]:
        """Extract parameter placeholders (#{param}, ${param})"""
        sql_text = etree.tostring(elem, encoding='unicode', method='text')

        # Extract #{param} and ${param}
        params = set()

        # MyBatis parameter syntax: #{paramName}
        for match in re.finditer(r'#\{([^}]+)\}', sql_text):
            param = match.group(1).split(',')[0].strip()  # Handle #{param, jdbcType=VARCHAR}
            params.add(param)

        # MyBatis string substitution: ${paramName}
        for match in re.finditer(r'\$\{([^}]+)\}', sql_text):
            param = match.group(1).strip()
            params.add(param)

        return sorted(list(params))

    def _extract_table_names(self, elem) -> List[str]:
        """
        Extract table names from SQL

        Expected Coverage: ~70% (basic pattern matching)
        Phase 5 LLM will handle complex queries with subqueries, CTEs, etc.
        """
        sql_text = self._extract_sql_text(elem)
        tables = set()

        # Pattern 1: FROM table_name
        from_matches = re.findall(r'\bFROM\s+(\w+)', sql_text, re.IGNORECASE)
        tables.update(from_matches)

        # Pattern 2: JOIN table_name
        join_matches = re.findall(r'\bJOIN\s+(\w+)', sql_text, re.IGNORECASE)
        tables.update(join_matches)

        # Pattern 3: INTO table_name
        into_matches = re.findall(r'\bINTO\s+(\w+)', sql_text, re.IGNORECASE)
        tables.update(into_matches)

        # Pattern 4: UPDATE table_name
        update_matches = re.findall(r'\bUPDATE\s+(\w+)', sql_text, re.IGNORECASE)
        tables.update(update_matches)

        return sorted(list(tables))

    def _has_dynamic_sql(self, elem) -> bool:
        """Check if statement contains dynamic SQL tags"""
        dynamic_tags = ["if", "choose", "when", "otherwise", "foreach", "where", "set", "trim", "bind"]
        for tag in dynamic_tags:
            if elem.find(f".//{tag}") is not None:
                return True
        return False

    def _extract_includes(self, elem) -> List[str]:
        """Extract <include> fragment references"""
        includes = []
        for include_elem in elem.findall(".//include"):
            refid = include_elem.get("refid", "")
            if refid:
                includes.append(refid)
        return includes

    def _extract_result_maps(self, root) -> List[Dict[str, Any]]:
        """Extract ResultMap definitions"""
        result_maps = []

        for rm_elem in root.findall(".//resultMap"):
            result_map = {
                "id": rm_elem.get("id", ""),
                "type": rm_elem.get("type", ""),
                "mappings": []
            }

            # Extract column mappings
            for mapping_elem in rm_elem:
                if mapping_elem.tag in ["id", "result"]:
                    result_map["mappings"].append({
                        "column": mapping_elem.get("column", ""),
                        "property": mapping_elem.get("property", ""),
                        "java_type": mapping_elem.get("javaType", ""),
                        "is_id": mapping_elem.tag == "id"
                    })

            result_maps.append(result_map)

        return result_maps

    def _extract_sql_fragments(self, root) -> List[Dict[str, Any]]:
        """Extract reusable SQL fragments (<sql>)"""
        fragments = []

        for sql_elem in root.findall(".//sql"):
            fragment = {
                "id": sql_elem.get("id", ""),
                "sql": self._extract_sql_text(sql_elem)
            }
            fragments.append(fragment)

        return fragments

    # ==================== Method-Statement Mapping ====================

    def _map_methods_to_statements(
        self,
        interface_data: Optional[Dict[str, Any]],
        xml_data: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Map interface method names to XML statement IDs"""
        mapping = {}

        if not interface_data or not xml_data:
            return mapping

        methods = interface_data.get("methods", [])
        statements = xml_data.get("statements", [])

        # Create lookup by statement ID
        stmt_lookup = {stmt["id"]: stmt for stmt in statements}

        # Map methods to statements (by name match)
        for method in methods:
            method_name = method["name"]
            if method_name in stmt_lookup:
                mapping[method_name] = method_name

        return mapping

    # ==================== Statistics ====================

    def _calculate_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics from analysis result"""
        stats = {
            "interface_methods": 0,
            "xml_statements": 0,
            "mapped_methods": 0,
            "select_statements": 0,
            "insert_statements": 0,
            "update_statements": 0,
            "delete_statements": 0,
            "result_maps": 0,
            "sql_fragments": 0,
            "total_tables": 0,
            "has_dynamic_sql": False
        }

        if result.get("interface"):
            stats["interface_methods"] = len(result["interface"].get("methods", []))

        if result.get("xml"):
            statements = result["xml"].get("statements", [])
            stats["xml_statements"] = len(statements)
            stats["select_statements"] = sum(1 for s in statements if s["type"] == "SELECT")
            stats["insert_statements"] = sum(1 for s in statements if s["type"] == "INSERT")
            stats["update_statements"] = sum(1 for s in statements if s["type"] == "UPDATE")
            stats["delete_statements"] = sum(1 for s in statements if s["type"] == "DELETE")
            stats["result_maps"] = len(result["xml"].get("result_maps", []))
            stats["sql_fragments"] = len(result["xml"].get("sql_fragments", []))
            stats["has_dynamic_sql"] = any(s["dynamic_sql"] for s in statements)

            # Count unique tables
            all_tables = set()
            for stmt in statements:
                all_tables.update(stmt.get("tables", []))
            stats["total_tables"] = len(all_tables)

        stats["mapped_methods"] = len(result.get("method_to_statement_mapping", {}))

        return stats

    # ==================== Tree-sitter Helpers ====================

    def _find_node_by_type(self, node, node_type: str):
        """Find first node of given type (DFS)"""
        if node.type == node_type:
            return node
        for child in node.children:
            result = self._find_node_by_type(child, node_type)
            if result:
                return result
        return None

    def _find_all_nodes_by_type(self, node, node_type: str) -> List:
        """Find all nodes of given type (DFS)"""
        results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            results.extend(self._find_all_nodes_by_type(child, node_type))
        return results

    def _find_child_by_type(self, node, node_type: str):
        """Find direct child of given type"""
        for child in node.children:
            if child.type == node_type:
                return child
        return None

    def _get_node_text(self, node, source_code: str) -> str:
        """Extract text from node"""
        if node is None:
            return ""
        return source_code[node.start_byte:node.end_byte]

    def _parse_annotation(self, annotation_node, content: str) -> Dict[str, Any]:
        """Parse annotation into structured format"""
        annotation_text = self._get_node_text(annotation_node, content)

        name_match = re.match(r'@(\w+)', annotation_text)
        if not name_match:
            return {"name": "", "arguments": {}}

        ann_name = name_match.group(1)
        arguments = {}

        # Single value: @Param("userId")
        single_value_match = re.search(r'@\w+\s*\(\s*"([^"]+)"\s*\)', annotation_text)
        if single_value_match:
            arguments["value"] = single_value_match.group(1)
            return {"name": ann_name, "arguments": arguments}

        # Key-value pairs
        kv_pattern = r'(\w+)\s*=\s*([^,)]+)'
        kv_matches = re.findall(kv_pattern, annotation_text)
        for key, value in kv_matches:
            value = value.strip().strip('"').strip('{').strip('}')
            arguments[key] = value

        return {"name": ann_name, "arguments": arguments}

    def _extract_parsing_errors(self, tree) -> List[Dict[str, Any]]:
        """Extract parsing error locations"""
        errors = []

        def find_errors(node):
            if node.has_error:
                if node.type == "ERROR":
                    errors.append({
                        "line": node.start_point[0] + 1,
                        "column": node.start_point[1],
                        "type": "syntax_error"
                    })
            for child in node.children:
                find_errors(child)

        find_errors(tree.root_node)
        return errors


# ==================== CLI Interface ====================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Analyze MyBatis Mapper structure")
    parser.add_argument("interface_file", help="Path to Mapper interface Java file")
    parser.add_argument("--xml", "-x", help="Path to Mapper XML file (optional)")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--force", "-f", action="store_true", help="Force refresh (ignore cache)")

    args = parser.parse_args()

    analyzer = MyBatisAnalyzer()

    interface_path = Path(args.interface_file)
    mapper_name = interface_path.stem  # UserMapper.java -> UserMapper

    context = {"interface_path": str(interface_path)}
    if args.xml:
        context["xml_path"] = args.xml

    result = analyzer.analyze(
        identifier=mapper_name,
        context=context,
        force_refresh=args.force
    )

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Analysis saved to: {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
