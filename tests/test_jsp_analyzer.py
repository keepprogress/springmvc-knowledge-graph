#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for JSP Structure Extractor

Tests critical functionality identified in code review:
- Static vs dynamic include distinction (compilation units)
- AJAX call extraction (multiple frameworks)
- EL expression parsing
- Form extraction
- web.xml integration
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.tools.jsp_analyzer import JSPAnalyzer


class TestJSPAnalyzer(unittest.TestCase):
    """Test JSP Structure Extractor"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = JSPAnalyzer(project_root=self.temp_dir)

    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== Critical: Compilation Unit Modeling ====================

    def test_static_vs_dynamic_includes(self):
        """
        Test static vs dynamic include distinction (research-critical)

        Static includes: translation-time merge, shared namespace
        Dynamic includes: runtime execution, isolated scope
        """
        jsp_content = """
        <%@ include file="header.jsp" %>
        <jsp:include page="sidebar.jsp" />
        <c:import url="footer.jsp" />
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        # Verify static includes
        self.assertEqual(len(result["static_includes"]), 1)
        static_inc = result["static_includes"][0]
        self.assertEqual(static_inc["type"], "static")
        self.assertEqual(static_inc["namespace"], "shared")
        self.assertEqual(static_inc["merge_type"], "translation_time")

        # Verify dynamic includes
        self.assertEqual(len(result["dynamic_includes"]), 2)
        for dynamic_inc in result["dynamic_includes"]:
            self.assertEqual(dynamic_inc["namespace"], "isolated")
            self.assertTrue(dynamic_inc["runtime"])

    def test_compilation_unit_id_generation(self):
        """Test unique compilation unit ID generation"""
        jsp_file = Path(self.temp_dir) / "user" / "list.jsp"
        jsp_file.parent.mkdir(parents=True, exist_ok=True)
        jsp_file.write_text("<html></html>")

        result = self.analyzer.analyze(
            identifier="user/list.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        # Verify CU ID format
        cu_id = result["compilation_unit_id"]
        self.assertTrue(cu_id.startswith("cu_"))
        self.assertIn("user", cu_id)
        self.assertIn("list", cu_id)

    # ==================== AJAX Call Extraction ====================

    def test_ajax_extraction_jquery(self):
        """Test jQuery AJAX pattern extraction"""
        jsp_content = """
        <script>
            $.ajax({url: '/api/users', type: 'GET'});
            $.get('/user/detail', callback);
            $.post('/user/save', data);
        </script>
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        ajax_calls = result["ajax_calls"]
        self.assertGreaterEqual(len(ajax_calls), 2)  # At least $.get and $.post

        # Verify methods detected
        methods = [call["method"] for call in ajax_calls]
        self.assertIn("GET", methods)
        self.assertIn("POST", methods)

    def test_ajax_extraction_fetch_xhr(self):
        """Test Fetch API and XMLHttpRequest extraction"""
        jsp_content = """
        <script>
            fetch('/api/users/123');
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/user/delete');
        </script>
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        ajax_calls = result["ajax_calls"]
        self.assertEqual(len(ajax_calls), 2)

        types = [call["type"] for call in ajax_calls]
        self.assertIn("fetch_api", types)
        self.assertIn("xmlhttprequest", types)

    # ==================== EL Expression Parsing ====================

    def test_el_expression_extraction(self):
        """Test EL and Spring EL extraction with variable chains"""
        jsp_content = """
        <p>${user.name}</p>
        <p>${userCount}</p>
        <p>#{systemProperties['user.home']}</p>
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        el_expressions = result["el_expressions"]
        self.assertEqual(len(el_expressions), 3)

        # Verify standard EL
        standard_el = [e for e in el_expressions if e["type"] == "standard_el"]
        self.assertEqual(len(standard_el), 2)

        # Verify Spring EL
        spring_el = [e for e in el_expressions if e["type"] == "spring_el"]
        self.assertEqual(len(spring_el), 1)

        # Verify variable chain extraction
        user_name_expr = next(e for e in el_expressions if "user.name" in e["expression"])
        self.assertIn("user", user_name_expr["variables"])
        self.assertIn("name", user_name_expr["variables"])

    # ==================== Form Extraction ====================

    def test_form_extraction(self):
        """Test HTML form parsing with input fields"""
        jsp_content = """
        <form action="/user/search" method="POST">
            <input type="text" name="username" required />
            <input type="email" name="email" />
            <select name="status"></select>
            <button type="submit">Search</button>
        </form>
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        forms = result["forms"]
        self.assertEqual(len(forms), 1)

        form = forms[0]
        self.assertEqual(form["action"], "/user/search")
        self.assertEqual(form["method"], "POST")
        self.assertEqual(len(form["inputs"]), 3)

        # Verify required field detection
        username_input = next(inp for inp in form["inputs"] if inp["name"] == "username")
        self.assertTrue(username_input["required"])

    # ==================== URL Classification ====================

    def test_url_classification(self):
        """Test URL extraction and intelligent classification"""
        jsp_content = """
        <a href="/user/add">Add</a>
        <a href="userDetail.jsp">Details</a>
        <a href="https://example.com">External</a>
        <script src="/static/js/app.js"></script>
        <a href="${ctx}/user/edit">Edit</a>
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        urls = result["urls"]
        self.assertGreaterEqual(len(urls), 5)

        # Verify classifications
        classifications = {url["url"]: url["classification"] for url in urls}
        self.assertEqual(classifications["/user/add"], "controller")
        self.assertEqual(classifications["userDetail.jsp"], "jsp")
        self.assertEqual(classifications["https://example.com"], "external")
        self.assertEqual(classifications["/static/js/app.js"], "static")
        self.assertEqual(classifications["${ctx}/user/edit"], "dynamic_expression")

    # ==================== Taglib Extraction ====================

    def test_taglib_extraction(self):
        """Test taglib directive parsing"""
        jsp_content = """
        <%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
        <%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        taglibs = result["taglibs"]
        self.assertEqual(len(taglibs), 2)

        prefixes = [t["prefix"] for t in taglibs]
        self.assertIn("c", prefixes)
        self.assertIn("fmt", prefixes)

    # ==================== Java Scriptlet Extraction ====================

    def test_scriptlet_extraction(self):
        """Test Java scriptlet parsing"""
        jsp_content = """
        <%
            String message = "Hello";
            int count = 0;
        %>
        <%= message %>
        """

        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text(jsp_content)

        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        scriptlets = result["scriptlets"]
        self.assertEqual(len(scriptlets), 2)

        # Verify code scriptlet
        code_scriptlet = next(s for s in scriptlets if s["type"] == "code")
        self.assertIn("String message", code_scriptlet["code"])

        # Verify expression scriptlet
        expr_scriptlet = next(s for s in scriptlets if s["type"] == "expression")
        self.assertEqual(expr_scriptlet["code"], "message")

    # ==================== web.xml Integration ====================

    def test_web_xml_integration(self):
        """Test web.xml parsing for implicit includes (critical for CU modeling)"""
        # Create WEB-INF directory
        web_inf = Path(self.temp_dir) / "WEB-INF"
        web_inf.mkdir(parents=True, exist_ok=True)

        # Create web.xml with jsp-property-group
        web_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <web-app xmlns="http://java.sun.com/xml/ns/javaee"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://java.sun.com/xml/ns/javaee
                 http://java.sun.com/xml/ns/javaee/web-app_3_0.xsd"
                 version="3.0">
            <jsp-config>
                <jsp-property-group>
                    <url-pattern>*.jsp</url-pattern>
                    <include-prelude>/WEB-INF/jsp/common/header.jsp</include-prelude>
                    <include-coda>/WEB-INF/jsp/common/footer.jsp</include-coda>
                </jsp-property-group>
            </jsp-config>
        </web-app>
        """

        web_xml_path = web_inf / "web.xml"
        web_xml_path.write_text(web_xml_content)

        # Create test JSP
        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text("<html><body>Test</body></html>")

        # Analyze with web.xml
        result = self.analyzer.analyze(
            identifier="test.jsp",
            context={
                "file_path": str(jsp_file),
                "web_xml_path": str(web_xml_path)
            },
            force_refresh=True
        )

        # Verify implicit includes parsed
        implicit = result["web_xml_implicit_includes"]
        self.assertIn("prelude", implicit)
        self.assertIn("coda", implicit)
        self.assertEqual(len(implicit["prelude"]), 1)
        self.assertEqual(len(implicit["coda"]), 1)

        # Verify URL patterns
        prelude = implicit["prelude"][0]
        self.assertIn("*.jsp", prelude["applies_to"])

    # ==================== Batch Analysis ====================

    def test_batch_analysis(self):
        """Test batch analysis of multiple JSP files"""
        # Create multiple JSP files
        for i in range(3):
            jsp_file = Path(self.temp_dir) / f"test{i}.jsp"
            jsp_file.write_text(f"<html><body>Test {i}</body></html>")

        # Batch analyze
        targets = [
            {"identifier": f"test{i}.jsp", "context": {"file_path": str(Path(self.temp_dir) / f"test{i}.jsp")}}
            for i in range(3)
        ]

        result = self.analyzer.batch_analyze(targets, force_refresh=True)

        self.assertEqual(result["total"], 3)
        successful = sum(1 for r in result["results"] if r["status"] == "success")
        failed = sum(1 for r in result["results"] if r["status"] == "error")
        self.assertEqual(successful, 3)
        self.assertEqual(failed, 0)

    # ==================== Caching ====================

    def test_caching_mechanism(self):
        """Test result caching works correctly"""
        jsp_file = Path(self.temp_dir) / "test.jsp"
        jsp_file.write_text("<html><body>Test</body></html>")

        # First analysis (fresh)
        result1 = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=False
        )

        # Second analysis (should use cache)
        result2 = self.analyzer.analyze(
            identifier="test.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=False
        )

        # Should have cached_at timestamp
        self.assertIn("cached_at", result2)

        # Results should be identical
        self.assertEqual(result1["compilation_unit_id"], result2["compilation_unit_id"])


class TestJSPAnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = JSPAnalyzer(project_root=self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_file_error(self):
        """Test graceful handling of missing files"""
        with self.assertRaises(FileNotFoundError):
            self.analyzer.analyze(
                identifier="nonexistent.jsp",
                context={"file_path": "nonexistent.jsp"},
                force_refresh=True
            )

    def test_malformed_jsp(self):
        """Test handling of malformed JSP (should not crash)"""
        jsp_content = """
        <%@ include file="
        <form action=
        ${unclosed
        """

        jsp_file = Path(self.temp_dir) / "malformed.jsp"
        jsp_file.write_text(jsp_content)

        # Should not crash
        result = self.analyzer.analyze(
            identifier="malformed.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        # Should still produce some results
        self.assertIn("statistics", result)

    def test_empty_jsp_file(self):
        """Test handling of empty JSP file"""
        jsp_file = Path(self.temp_dir) / "empty.jsp"
        jsp_file.write_text("")

        result = self.analyzer.analyze(
            identifier="empty.jsp",
            context={"file_path": str(jsp_file)},
            force_refresh=True
        )

        # Should have zero statistics
        self.assertEqual(result["statistics"]["static_includes"], 0)
        self.assertEqual(result["statistics"]["ajax_calls"], 0)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
