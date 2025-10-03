#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spring MVC Controller Structure Extractor

Extracts structural information from Spring MVC controllers using tree-sitter-java.
Research-validated for production use (error recovery, incremental parsing).

Phase 3.2 Implementation - Focuses on static structure extraction.
Semantic analysis deferred to Phase 5 LLM.

Features:
1. Annotation extraction (@Controller, @RequestMapping, etc.)
2. Request mapping patterns (URL, HTTP method, params, headers)
3. Dependency injection detection (@Autowired services)
4. Method call chain extraction
5. Return type analysis (View, ModelAndView, JSON)
6. Parameter binding extraction (@RequestParam, @PathVariable, @RequestBody)
7. Error recovery (handles incomplete/malformed code)
8. Compilation unit modeling

Author: keepprogress
Date: 2025-10-03
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# tree-sitter for production-grade Java parsing
try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️  tree-sitter not available. Install: pip install tree-sitter tree-sitter-java",
          file=sys.stderr)

from mcp_server.tools.base_tool import BaseTool


class ControllerAnalyzer(BaseTool):
    """
    Spring MVC Controller Structure Extractor

    Uses tree-sitter-java for production-grade parsing with error recovery.
    Focuses on static structure; semantic analysis in Phase 5.
    """

    def __init__(self, project_root: str = "."):
        super().__init__(
            tool_name="controllers",
            output_dir="output/structure"
        )
        self.project_root = Path(project_root)

        # Initialize tree-sitter-java parser
        self.java_parser = None
        if TREE_SITTER_AVAILABLE:
            try:
                # Load tree-sitter-java language
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
        Analyze Spring MVC Controller structure

        Args:
            identifier: Controller class name (e.g., "UserController")
            context: {"file_path": "path/to/UserController.java"}
            force_refresh: Force re-analysis

        Returns:
            Controller structure analysis
        """
        context = context or {}
        file_path = context.get("file_path")

        if not file_path:
            raise ValueError("file_path required in context")

        java_path = Path(file_path)
        if not java_path.exists():
            raise FileNotFoundError(f"Controller file not found: {file_path}")

        print(f"🔍 Analyzing Controller: {java_path}")

        # Read Java source
        with open(java_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse with tree-sitter-java
        tree = None
        if self.java_parser:
            tree = self.java_parser.parse(bytes(content, 'utf8'))

        # Extract structure
        result = {
            "file": str(java_path.relative_to(self.project_root)) if java_path.is_relative_to(self.project_root) else str(java_path),
            "class_name": identifier,
            "package": self._extract_package(content, tree),
            "imports": self._extract_imports(content, tree),
            "class_annotations": self._extract_class_annotations(content, tree),
            "is_controller": self._is_spring_controller(content, tree),
            "base_path": self._extract_base_request_mapping(content, tree),
            "methods": self._extract_controller_methods(content, tree),
            "dependencies": self._extract_dependencies(content, tree),
            "statistics": {},
            "parsing_errors": []
        }

        # Check for parsing errors
        if tree and tree.root_node.has_error:
            result["parsing_errors"] = self._extract_parsing_errors(tree)
            print(f"  ⚠️  Parsing errors detected: {len(result['parsing_errors'])} issues")

        # Add statistics
        result["statistics"] = {
            "total_methods": len(result["methods"]),
            "request_mappings": sum(1 for m in result["methods"] if m.get("request_mapping")),
            "dependencies": len(result["dependencies"]),
            "has_errors": len(result["parsing_errors"]) > 0
        }

        return result

    # ==================== Package & Imports ====================

    def _extract_package(self, content: str, tree) -> str:
        """Extract package declaration"""
        if tree:
            # tree-sitter query: (package_declaration (scoped_identifier) @package)
            package_node = self._find_node_by_type(tree.root_node, "package_declaration")
            if package_node:
                return self._get_node_text(package_node, content).replace("package ", "").replace(";", "").strip()

        # Fallback: regex
        match = re.search(r'package\s+([\w.]+);', content)
        return match.group(1) if match else ""

    def _extract_imports(self, content: str, tree) -> List[str]:
        """Extract import statements"""
        imports = []

        if tree:
            # tree-sitter: find all import_declaration nodes
            import_nodes = self._find_all_nodes_by_type(tree.root_node, "import_declaration")
            for node in import_nodes:
                import_text = self._get_node_text(node, content)
                import_text = import_text.replace("import ", "").replace(";", "").strip()
                imports.append(import_text)
        else:
            # Fallback: regex
            import_matches = re.findall(r'import\s+([\w.*]+);', content)
            imports = import_matches

        return imports

    # ==================== Class Annotations ====================

    def _extract_class_annotations(self, content: str, tree) -> List[Dict[str, Any]]:
        """Extract class-level annotations"""
        annotations = []

        if tree:
            # Find class declaration
            class_node = self._find_node_by_type(tree.root_node, "class_declaration")
            if class_node:
                # Find modifiers (contains annotations)
                modifiers_node = self._find_child_by_type(class_node, "modifiers")
                if modifiers_node:
                    # Handle both marker_annotation (@Controller) and annotation (@RequestMapping(...))
                    annotation_nodes = self._find_all_nodes_by_type(modifiers_node, "annotation") + \
                                     self._find_all_nodes_by_type(modifiers_node, "marker_annotation")
                    for ann_node in annotation_nodes:
                        annotations.append(self._parse_annotation(ann_node, content))
        else:
            # Fallback: regex for common patterns
            controller_match = re.search(r'@(Rest)?Controller', content)
            if controller_match:
                annotations.append({"name": controller_match.group(0).replace("@", ""), "arguments": {}})

            request_mapping_match = re.search(r'@RequestMapping\s*\(\s*"([^"]+)"\s*\)', content)
            if request_mapping_match:
                annotations.append({
                    "name": "RequestMapping",
                    "arguments": {"value": request_mapping_match.group(1)}
                })

        return annotations

    def _is_spring_controller(self, content: str, tree) -> bool:
        """Check if class is a Spring Controller"""
        class_annotations = self._extract_class_annotations(content, tree)
        controller_annotations = ["Controller", "RestController"]
        return any(ann["name"] in controller_annotations for ann in class_annotations)

    def _extract_base_request_mapping(self, content: str, tree) -> str:
        """Extract class-level @RequestMapping path"""
        class_annotations = self._extract_class_annotations(content, tree)
        for ann in class_annotations:
            if ann["name"] == "RequestMapping":
                # Extract value or path
                return ann["arguments"].get("value") or ann["arguments"].get("path") or ""
        return ""

    # ==================== Method Extraction ====================

    def _extract_controller_methods(self, content: str, tree) -> List[Dict[str, Any]]:
        """
        Extract controller methods with request mappings

        Expected Coverage: ~90% (tree-sitter production-validated)

        Known Limitations:
        - Complex annotation expressions may require Phase 5 LLM
        - Dynamic path variables in constants
        """
        methods = []

        if not tree:
            print("  ⚠️  tree-sitter not available, limited method extraction", file=sys.stderr)
            return methods

        # Find class declaration
        class_node = self._find_node_by_type(tree.root_node, "class_declaration")
        if not class_node:
            return methods

        # Find class body
        class_body = self._find_child_by_type(class_node, "class_body")
        if not class_body:
            return methods

        # Find all method declarations
        method_nodes = self._find_all_nodes_by_type(class_body, "method_declaration")

        for method_node in method_nodes:
            method_info = {
                "name": "",
                "return_type": "",
                "parameters": [],
                "annotations": [],
                "request_mapping": None,
                "service_calls": [],
                "has_errors": method_node.has_error
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
                # Handle both marker_annotation and annotation types
                annotation_nodes = self._find_all_nodes_by_type(modifiers_node, "annotation") + \
                                 self._find_all_nodes_by_type(modifiers_node, "marker_annotation")
                for ann_node in annotation_nodes:
                    ann = self._parse_annotation(ann_node, content)
                    method_info["annotations"].append(ann)

                    # Check if it's a request mapping annotation
                    if ann["name"] in ["RequestMapping", "GetMapping", "PostMapping",
                                      "PutMapping", "DeleteMapping", "PatchMapping"]:
                        method_info["request_mapping"] = self._parse_request_mapping(ann)

            # Extract service method calls (basic pattern matching)
            method_body = self._find_child_by_type(method_node, "block")
            if method_body:
                method_info["service_calls"] = self._extract_service_calls(method_body, content)

            methods.append(method_info)

        return methods

    def _extract_method_parameters(self, params_node, content: str) -> List[Dict[str, Any]]:
        """Extract method parameters with annotations"""
        parameters = []

        param_nodes = self._find_all_nodes_by_type(params_node, "formal_parameter")
        for param_node in param_nodes:
            param_info = {
                "name": "",
                "type": "",
                "annotations": []
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

            # Extract parameter annotations
            modifiers_node = self._find_child_by_type(param_node, "modifiers")
            if modifiers_node:
                # Handle both marker_annotation and annotation types
                annotation_nodes = self._find_all_nodes_by_type(modifiers_node, "annotation") + \
                                 self._find_all_nodes_by_type(modifiers_node, "marker_annotation")
                for ann_node in annotation_nodes:
                    param_info["annotations"].append(self._parse_annotation(ann_node, content))

            parameters.append(param_info)

        return parameters

    def _parse_request_mapping(self, annotation: Dict[str, Any]) -> Dict[str, Any]:
        """Parse @RequestMapping annotation into structured format"""
        mapping = {
            "annotation": annotation["name"],
            "path": "",
            "method": self._infer_http_method(annotation["name"]),
            "params": [],
            "headers": [],
            "consumes": [],
            "produces": []
        }

        args = annotation.get("arguments", {})

        # Extract path/value
        mapping["path"] = args.get("value") or args.get("path") or ""

        # Extract method (if specified)
        if "method" in args:
            mapping["method"] = args["method"]

        # Extract other attributes
        mapping["params"] = args.get("params", [])
        mapping["headers"] = args.get("headers", [])
        mapping["consumes"] = args.get("consumes", [])
        mapping["produces"] = args.get("produces", [])

        return mapping

    def _infer_http_method(self, annotation_name: str) -> str:
        """Infer HTTP method from annotation name"""
        method_map = {
            "GetMapping": "GET",
            "PostMapping": "POST",
            "PutMapping": "PUT",
            "DeleteMapping": "DELETE",
            "PatchMapping": "PATCH",
            "RequestMapping": "GET"  # Default
        }
        return method_map.get(annotation_name, "UNKNOWN")

    # ==================== Dependency Injection ====================

    def _extract_dependencies(self, content: str, tree) -> List[Dict[str, Any]]:
        """
        Extract @Autowired dependencies (Service layer)

        Detects:
        - Field injection: @Autowired private UserService userService;
        - Constructor injection: @Autowired public UserController(UserService service) {...}
        """
        dependencies = []

        if not tree:
            return dependencies

        # Find class declaration
        class_node = self._find_node_by_type(tree.root_node, "class_declaration")
        if not class_node:
            return dependencies

        class_body = self._find_child_by_type(class_node, "class_body")
        if not class_body:
            return dependencies

        # Extract field injections
        field_nodes = self._find_all_nodes_by_type(class_body, "field_declaration")
        for field_node in field_nodes:
            # Check for @Autowired annotation
            modifiers_node = self._find_child_by_type(field_node, "modifiers")
            if modifiers_node:
                # Handle both marker_annotation and annotation types
                annotations = self._find_all_nodes_by_type(modifiers_node, "annotation") + \
                             self._find_all_nodes_by_type(modifiers_node, "marker_annotation")
                has_autowired = any("Autowired" in self._get_node_text(ann, content) for ann in annotations)

                if has_autowired:
                    # Extract field type and name
                    type_node = self._find_child_by_type(field_node, "type_identifier") or \
                               self._find_child_by_type(field_node, "generic_type")
                    declarator_node = self._find_child_by_type(field_node, "variable_declarator")

                    if type_node and declarator_node:
                        field_type = self._get_node_text(type_node, content)
                        field_name_node = self._find_child_by_type(declarator_node, "identifier")
                        field_name = self._get_node_text(field_name_node, content) if field_name_node else ""

                        dependencies.append({
                            "type": field_type,
                            "name": field_name,
                            "injection_type": "field",
                            "is_service": "Service" in field_type or "Repository" in field_type
                        })

        # Extract constructor injections
        constructor_nodes = self._find_all_nodes_by_type(class_body, "constructor_declaration")
        for constructor_node in constructor_nodes:
            params_node = self._find_child_by_type(constructor_node, "formal_parameters")
            if params_node:
                param_nodes = self._find_all_nodes_by_type(params_node, "formal_parameter")
                for param_node in param_nodes:
                    type_node = self._find_child_by_type(param_node, "type_identifier") or \
                               self._find_child_by_type(param_node, "generic_type")
                    name_node = self._find_child_by_type(param_node, "identifier")

                    if type_node and name_node:
                        param_type = self._get_node_text(type_node, content)
                        param_name = self._get_node_text(name_node, content)

                        dependencies.append({
                            "type": param_type,
                            "name": param_name,
                            "injection_type": "constructor",
                            "is_service": "Service" in param_type or "Repository" in param_type
                        })

        return dependencies

    # ==================== Method Call Extraction ====================

    def _extract_service_calls(self, method_body_node, content: str) -> List[Dict[str, Any]]:
        """
        Extract service method calls from controller method body

        Expected Coverage: ~70% (basic pattern matching)
        Phase 5 LLM will handle complex call chains and conditional logic
        """
        service_calls = []

        # Find method invocations
        invocation_nodes = self._find_all_nodes_by_type(method_body_node, "method_invocation")

        for inv_node in invocation_nodes:
            call_info = {
                "method": "",
                "object": "",
                "arguments_count": 0
            }

            # Extract method name
            name_node = self._find_child_by_type(inv_node, "identifier")
            if name_node:
                call_info["method"] = self._get_node_text(name_node, content)

            # Extract object (e.g., userService.findById -> object: userService)
            object_node = self._find_child_by_type(inv_node, "field_access")
            if object_node:
                obj_identifier = self._find_child_by_type(object_node, "identifier")
                if obj_identifier:
                    call_info["object"] = self._get_node_text(obj_identifier, content)

            # Count arguments
            args_node = self._find_child_by_type(inv_node, "argument_list")
            if args_node:
                call_info["arguments_count"] = len(self._find_all_nodes_by_type(args_node, "argument"))

            service_calls.append(call_info)

        return service_calls

    # ==================== Annotation Parsing ====================

    def _parse_annotation(self, annotation_node, content: str) -> Dict[str, Any]:
        """Parse annotation into structured format"""
        annotation_text = self._get_node_text(annotation_node, content)

        # Extract annotation name
        name_match = re.match(r'@(\w+)', annotation_text)
        if not name_match:
            return {"name": "", "arguments": {}}

        ann_name = name_match.group(1)
        arguments = {}

        # Parse arguments
        # Simple patterns: @Ann("value"), @Ann(key="value"), @Ann(value={"a", "b"})

        # Single value: @RequestMapping("/users")
        single_value_match = re.search(r'@\w+\s*\(\s*"([^"]+)"\s*\)', annotation_text)
        if single_value_match:
            arguments["value"] = single_value_match.group(1)
            return {"name": ann_name, "arguments": arguments}

        # Key-value pairs: @RequestMapping(path="/users", method=RequestMethod.GET)
        kv_pattern = r'(\w+)\s*=\s*([^,)]+)'
        kv_matches = re.findall(kv_pattern, annotation_text)
        for key, value in kv_matches:
            # Clean up value (remove quotes, braces)
            value = value.strip().strip('"').strip('{').strip('}')
            arguments[key] = value

        return {"name": ann_name, "arguments": arguments}

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

    parser = argparse.ArgumentParser(description="Analyze Spring MVC Controller structure")
    parser.add_argument("controller_file", help="Path to Controller Java file")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--force", "-f", action="store_true", help="Force refresh (ignore cache)")

    args = parser.parse_args()

    analyzer = ControllerAnalyzer()

    controller_path = Path(args.controller_file)
    class_name = controller_path.stem  # UserController.java -> UserController

    result = analyzer.analyze(
        identifier=class_name,
        context={"file_path": str(controller_path)},
        force_refresh=args.force
    )

    if args.output:
        import json
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Analysis saved to: {args.output}")
    else:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
