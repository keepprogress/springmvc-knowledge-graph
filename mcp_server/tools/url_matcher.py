#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL Matcher for JSP-to-Controller Relationship Detection

Matches AJAX calls in JSP to Spring Controller endpoints.
Handles EL expressions, path variables, and wildcards.
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

from mcp_server.tools.llm_query_engine import LLMQueryEngine

logger = logging.getLogger(__name__)


class URLMatcher:
    """Matches AJAX URLs to Controller endpoints."""

    def __init__(self, llm_engine: Optional[LLMQueryEngine] = None):
        """
        Initialize URL Matcher.

        Args:
            llm_engine: LLM Query Engine for disambiguation (optional)
        """
        self.llm = llm_engine or LLMQueryEngine()

    async def match_ajax_to_controller(
        self,
        ajax_call: Dict,
        controllers: List[Dict]
    ) -> Dict:
        """
        Match AJAX URL to controller endpoint.

        Args:
            ajax_call: AJAX call info with 'url', 'method', 'code_snippet'
            controllers: List of controller dicts with 'class_name', 'endpoints'

        Returns:
            Match result dict with:
                - target: Matched controller info or None
                - confidence: 0.0-1.0
                - method: "exact_match", "pattern_match", "llm", or "no_match"
                - reasoning: Explanation of match
        """
        # Extract URL and method from AJAX call
        url = ajax_call.get('url', '')
        method = ajax_call.get('method', 'GET').upper()

        # Normalize AJAX URL (remove EL expressions, etc.)
        normalized_url = self._normalize_ajax_url(url)

        # Find candidate controllers by URL pattern
        candidates = self._find_candidate_controllers(
            normalized_url, method, controllers
        )

        # Case 1: Exact single match
        if len(candidates) == 1:
            return {
                "target": candidates[0],
                "confidence": 0.9,
                "method": "pattern_match",
                "reasoning": f"Single exact match for {normalized_url} [{method}]"
            }

        # Case 2: No matches
        if len(candidates) == 0:
            return {
                "target": None,
                "confidence": 0.0,
                "method": "no_match",
                "reasoning": f"No controller found for {normalized_url} [{method}]"
            }

        # Case 3: Multiple candidates - use LLM to disambiguate
        logger.info(f"Multiple candidates for {normalized_url}: {len(candidates)}")

        context = {
            "ajax_call": ajax_call,
            "candidates": candidates,
            "source_type": "JSP_AJAX",
            "target_type": "CONTROLLER_METHOD",
            "http_method": method
        }

        # Build disambiguation prompt
        source_code = ajax_call.get('code_snippet', url)
        target_code = self._format_candidates_for_llm(candidates)

        try:
            result = await self.llm.verify_relationship(
                source_code=source_code,
                target_code=target_code,
                relationship_type="AJAX_TO_CONTROLLER",
                context=context
            )

            # Extract best match from LLM result
            if result.get("match"):
                # LLM should indicate which candidate in reasoning
                # For now, return first candidate with LLM confidence
                return {
                    "target": candidates[0],  # TODO: Extract from LLM reasoning
                    "confidence": result.get("confidence", 0.7),
                    "method": "llm",
                    "reasoning": result.get("reasoning", "LLM disambiguation")
                }
            else:
                return {
                    "target": None,
                    "confidence": 0.0,
                    "method": "llm",
                    "reasoning": result.get("reasoning", "LLM found no match")
                }

        except Exception as e:
            logger.error(f"LLM disambiguation failed: {e}")
            # Fallback: return first candidate with low confidence
            return {
                "target": candidates[0],
                "confidence": 0.5,
                "method": "fallback",
                "reasoning": f"LLM failed, using first of {len(candidates)} candidates"
            }

    def _normalize_ajax_url(self, url: str) -> str:
        """
        Normalize AJAX URL for matching.

        Handles:
        - EL expressions: ${ctx}/user/list -> /user/list
        - Context path removal: /myapp/user/list -> /user/list
        - Query parameters: /user/list?id=1 -> /user/list
        - Dynamic parts: '/user/' + id -> /user/{id}

        Args:
            url: Original AJAX URL

        Returns:
            Normalized URL
        """
        # Remove quotes
        url = url.strip("'\"")

        # Handle EL expressions
        # ${ctx}/user/list -> /user/list
        # ${pageContext.request.contextPath}/user/list -> /user/list
        url = re.sub(r'\$\{[^}]+\}', '', url)

        # Remove query parameters
        url = url.split('?')[0]

        # Detect dynamic URL construction
        # '/user/' + id + '/edit' -> /user/{id}/edit
        if '+' in url:
            # Split by + and analyze
            parts = url.split('+')
            normalized_parts = []

            for part in parts:
                part = part.strip().strip("'\"")

                # If part starts with /, it's a path segment
                if part.startswith('/'):
                    normalized_parts.append(part)
                # If part is a variable name (no quotes), make it a path variable
                elif not part.startswith(("'", '"')) and part:
                    normalized_parts.append(f"{{{part}}}")
                # If part is a quoted string, add it
                elif part.strip("'\""):
                    normalized_parts.append(part.strip("'\""))

            url = ''.join(normalized_parts)

        # Ensure starts with /
        if not url.startswith('/'):
            url = '/' + url

        # Remove duplicate slashes
        url = re.sub(r'/+', '/', url)

        return url

    def _find_candidate_controllers(
        self,
        url: str,
        method: str,
        controllers: List[Dict]
    ) -> List[Dict]:
        """
        Find controllers matching URL pattern.

        Prioritizes exact matches over pattern matches (path variables, wildcards).

        Args:
            url: Normalized URL
            method: HTTP method (GET, POST, etc.)
            controllers: List of controller dicts

        Returns:
            List of matching controller endpoint dicts (exact matches first)
        """
        exact_matches = []
        pattern_matches = []

        for controller in controllers:
            for endpoint in controller.get('endpoints', []):
                endpoint_path = endpoint.get('path', '')
                endpoint_methods = endpoint.get('methods', [])

                # Convert single method to list
                if isinstance(endpoint_methods, str):
                    endpoint_methods = [endpoint_methods]

                # Check if URL and method match
                if self._url_matches(url, endpoint_path) and \
                   method.upper() in [m.upper() for m in endpoint_methods]:
                    candidate = {
                        "controller": controller.get('class_name'),
                        "method": endpoint.get('handler'),
                        "path": endpoint_path,
                        "http_methods": endpoint_methods
                    }

                    # Prioritize exact matches over pattern matches
                    if endpoint_path == url:
                        exact_matches.append(candidate)
                    else:
                        pattern_matches.append(candidate)

        # Return exact matches first, then pattern matches
        return exact_matches + pattern_matches

    def _url_matches(self, ajax_url: str, mapping_path: str) -> bool:
        """
        Check if AJAX URL matches @RequestMapping path.

        Handles:
        - Exact match: /user/list == /user/list
        - Path variables: /user/{id} matches /user/123
        - Wildcards: /user/* matches /user/anything
        - Ant-style patterns: /user/** matches /user/a/b/c

        Args:
            ajax_url: Normalized AJAX URL
            mapping_path: Spring @RequestMapping path

        Returns:
            True if URLs match
        """
        # Exact match
        if ajax_url == mapping_path:
            return True

        # Convert Spring path to regex pattern
        # /user/{id} -> /user/[^/]+
        # /user/* -> /user/[^/]+
        # /user/** -> /user/.*
        pattern = mapping_path

        # Use placeholders to avoid escaping issues
        # Step 1: Replace wildcards with unique placeholders
        pattern = pattern.replace('/**', '<<<DOUBLESTAR>>>')
        pattern = pattern.replace('/*', '<<<SINGLESTAR>>>')

        # Step 2: Handle path variables: {id} -> [^/]+
        pattern = re.sub(r'\{[^}]+\}', r'[^/]+', pattern)

        # Step 3: Escape other special regex chars (like dots in paths)
        pattern = pattern.replace('.', r'\.')

        # Step 4: Replace placeholders with actual regex patterns
        pattern = pattern.replace('<<<DOUBLESTAR>>>', '/.*')
        pattern = pattern.replace('<<<SINGLESTAR>>>', '/[^/]+')

        # Make it a full match
        pattern = f'^{pattern}$'

        # Test match
        return re.match(pattern, ajax_url) is not None

    def _format_candidates_for_llm(self, candidates: List[Dict]) -> str:
        """
        Format candidate controllers for LLM input.

        Args:
            candidates: List of candidate dicts

        Returns:
            Formatted string for LLM
        """
        formatted = []

        for i, candidate in enumerate(candidates, 1):
            formatted.append(
                f"Candidate {i}:\n"
                f"  Controller: {candidate['controller']}\n"
                f"  Method: {candidate['method']}\n"
                f"  Path: {candidate['path']}\n"
                f"  HTTP Methods: {', '.join(candidate['http_methods'])}"
            )

        return '\n\n'.join(formatted)

    async def batch_match(
        self,
        ajax_calls: List[Dict],
        controllers: List[Dict]
    ) -> List[Dict]:
        """
        Match multiple AJAX calls to controllers.

        Args:
            ajax_calls: List of AJAX call dicts
            controllers: List of controller dicts

        Returns:
            List of match results
        """
        results = []

        for ajax_call in ajax_calls:
            result = await self.match_ajax_to_controller(ajax_call, controllers)
            results.append(result)

        return results

    def __repr__(self) -> str:
        """String representation."""
        return f"URLMatcher(llm_engine={self.llm})"
