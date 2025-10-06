#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Query Engine for Knowledge Graph Enhancement

Uses Claude API to verify relationships and fill gaps in the knowledge graph.
Implements semantic caching, XML-structured prompts, and few-shot learning.
"""

import json
import re
import os
from typing import Dict, List, Optional, Any
import logging

try:
    import anthropic
except ImportError:
    anthropic = None

from mcp_server.tools.semantic_cache import SemanticCache

logger = logging.getLogger(__name__)


class LLMQueryEngine:
    """LLM-based query engine for graph enhancement."""

    # Few-shot examples for different relationship types
    FEW_SHOT_EXAMPLES = {
        "AJAX_TO_CONTROLLER": [
            {
                "type": "positive",
                "ajax": "$.post('${ctx}/user/save', data)",
                "controller": "@PostMapping('/user/save')",
                "match": True,
                "confidence": 0.95,
                "reasoning": "URL pattern and HTTP method match exactly"
            },
            {
                "type": "negative",
                "ajax": "$.get('/api/users')",
                "controller": "@GetMapping('/user/list')",
                "match": False,
                "confidence": 0.0,
                "reasoning": "URL paths are different (/api/users vs /user/list)"
            },
            {
                "type": "edge_case",
                "ajax": "$.post('/user/' + id + '/update')",
                "controller": "@PostMapping('/user/{id}/update')",
                "match": True,
                "confidence": 0.85,
                "reasoning": "Path variable {id} matches dynamic URL construction"
            }
        ],
        "CONTROLLER_TO_SERVICE": [
            {
                "type": "positive",
                "controller": "return userService.getUser(id);",
                "service": "public User getUser(Long id)",
                "match": True,
                "confidence": 0.95,
                "reasoning": "Method name and parameters match exactly"
            },
            {
                "type": "negative",
                "controller": "return userService.listUsers();",
                "service": "public User getUser(Long id)",
                "match": False,
                "confidence": 0.0,
                "reasoning": "Different method names (listUsers vs getUser)"
            }
        ],
        "SERVICE_TO_MAPPER": [
            {
                "type": "positive",
                "service": "return userMapper.selectById(id);",
                "mapper": "User selectById(@Param(\"id\") Long id);",
                "match": True,
                "confidence": 0.95,
                "reasoning": "Direct mapper method call with matching signature"
            }
        ],
        "MAPPER_TO_SQL": [
            {
                "type": "positive",
                "mapper_method": "selectAllUsers",
                "sql": "SELECT * FROM users WHERE status = 'active'",
                "match": True,
                "confidence": 0.9,
                "reasoning": "SQL statement implements the selectAllUsers method"
            }
        ]
    }

    def __init__(
        self,
        cache_dir: str = ".llm_cache",
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize LLM Query Engine.

        Args:
            cache_dir: Directory for semantic cache
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: claude-sonnet-4-20250514)
        """
        self.cache = SemanticCache(cache_dir=cache_dir)
        self.model = model

        # Initialize Anthropic client if available
        if anthropic is None:
            logger.warning("anthropic package not installed. LLM queries will be disabled.")
            self.client = None
        else:
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("No API key provided. Set ANTHROPIC_API_KEY environment variable.")
                self.client = None
            else:
                self.client = anthropic.Anthropic(api_key=api_key)

    async def verify_relationship(
        self,
        source_code: str,
        target_code: str,
        relationship_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify a relationship using LLM.

        Args:
            source_code: Source code snippet
            target_code: Target code snippet
            relationship_type: Type of relationship (e.g., "AJAX_TO_CONTROLLER")
            context: Additional context information

        Returns:
            Dictionary with:
                - match: bool
                - confidence: float (0.0-1.0)
                - reasoning: str
                - method: str ("llm" or "cache")
        """
        if self.client is None:
            return {
                "match": False,
                "confidence": 0.0,
                "reasoning": "LLM client not available",
                "method": "error"
            }

        # Check cache first
        cache_key = f"{source_code}:{target_code}:{relationship_type}"
        cached = self.cache.get(cache_key, "verify_relationship")
        if cached:
            cached["method"] = "cache"
            return cached

        # Build XML-structured prompt
        prompt = self._build_verification_prompt(
            source_code, target_code, relationship_type, context or {}
        )

        # Check rate limit before querying LLM
        try:
            self.cache.check_rate_limit()
        except Exception as e:
            logger.warning(f"Rate limit check: {e}")
            return {
                "match": False,
                "confidence": 0.0,
                "reasoning": str(e),
                "method": "rate_limited"
            }

        # Query LLM
        try:
            result = await self._query_llm(prompt)

            # Cache result with estimated tokens
            estimated_tokens = len(prompt.split()) + len(str(result).split())
            self.cache.set(cache_key, "verify_relationship", result, estimated_tokens)

            result["method"] = "llm"
            return result

        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return {
                "match": False,
                "confidence": 0.0,
                "reasoning": f"LLM query error: {str(e)}",
                "method": "error"
            }

    def _build_verification_prompt(
        self,
        source_code: str,
        target_code: str,
        relationship_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Build XML-structured prompt for relationship verification.

        XML structure improves accuracy by 15-20% according to Anthropic research.

        Args:
            source_code: Source code snippet
            target_code: Target code snippet
            relationship_type: Type of relationship
            context: Additional context

        Returns:
            Formatted prompt string
        """
        # Get few-shot examples for this relationship type
        examples = self._get_few_shot_examples(relationship_type)

        # Limit context to ±15 lines (sweet spot for accuracy)
        source_snippet = self._limit_code_context(source_code, max_lines=15)
        target_snippet = self._limit_code_context(target_code, max_lines=15)

        # Build XML-structured prompt
        prompt = f"""<task>
Verify if a {relationship_type} relationship exists between source and target code.
</task>

<context>
<source>
<type>{context.get('source_type', 'unknown')}</type>
<code>
{source_snippet}
</code>
</source>

<target>
<type>{context.get('target_type', 'unknown')}</type>
<code>
{target_snippet}
</code>
</target>

<project_context>
{json.dumps(context, indent=2)}
</project_context>
</context>

<requirements>
1. Output JSON format with fields: match (bool), confidence (0.0-1.0), reasoning (str)
2. Use step-by-step reasoning in <thinking> tags
3. Consider edge cases like path variables, context paths, HTTP methods
4. Confidence should reflect certainty:
   - 0.9-1.0: Exact match with clear evidence
   - 0.7-0.89: Strong match with minor ambiguity
   - 0.5-0.69: Possible match with significant ambiguity
   - 0.0-0.49: Unlikely or no match
</requirements>

<examples>
{examples}
</examples>

<instructions>
Analyze the relationship step by step:

1. Extract key patterns from source code (URLs, method names, parameters)
2. Extract key patterns from target code
3. Compare patterns and check for matches
4. Consider context (HTTP method, path variables, wildcards)
5. Assign confidence based on match quality
6. Provide clear reasoning

Output format:
<thinking>
[Your step-by-step analysis here]
</thinking>

<conclusion>
{{
  "match": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "explanation"
}}
</conclusion>
</instructions>"""

        return prompt

    def _get_few_shot_examples(self, relationship_type: str) -> str:
        """Get few-shot examples for relationship type."""
        examples = self.FEW_SHOT_EXAMPLES.get(relationship_type, [])

        if not examples:
            return "No examples available for this relationship type."

        formatted_examples = []
        for i, example in enumerate(examples, 1):
            formatted_examples.append(f"""
Example {i} ({example['type']}):
- Match: {example['match']}
- Confidence: {example['confidence']}
- Reasoning: {example['reasoning']}
""")

        return "\n".join(formatted_examples)

    def _limit_code_context(self, code: str, max_lines: int = 15) -> str:
        """
        Limit code to ±N lines around key content.

        Args:
            code: Full code string
            max_lines: Maximum number of lines

        Returns:
            Truncated code with ... indicators
        """
        lines = code.split('\n')

        if len(lines) <= max_lines:
            return code

        # Take first max_lines lines and add indicator
        truncated = '\n'.join(lines[:max_lines])
        truncated += f"\n... ({len(lines) - max_lines} more lines)"

        return truncated

    async def _query_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Query Claude API with prompt.

        Args:
            prompt: Formatted prompt string

        Returns:
            Parsed JSON response
        """
        if self.client is None:
            raise RuntimeError("LLM client not initialized")

        # Use specified Claude model
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text from response
        response_text = response.content[0].text

        # Extract JSON from <conclusion> tags
        conclusion_match = re.search(
            r'<conclusion>\s*(\{.*?\})\s*</conclusion>',
            response_text,
            re.DOTALL
        )

        if conclusion_match:
            json_str = conclusion_match.group(1)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from conclusion: {e}")
                logger.error(f"JSON string: {json_str}")

        # Fallback: try to find any JSON in response
        json_match = re.search(r'\{[^{}]*"match"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # If all fails, return error
        logger.error(f"Could not extract JSON from LLM response: {response_text}")
        return {
            "match": False,
            "confidence": 0.0,
            "reasoning": "Failed to parse LLM response"
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.stats()

    def clear_cache(self):
        """Clear all cache entries."""
        self.cache.clear()

    def __repr__(self) -> str:
        """String representation."""
        stats = self.cache.stats()
        return (
            f"LLMQueryEngine("
            f"cache_entries={stats['total_entries']}, "
            f"hit_rate={stats['hit_rate']:.1%})"
        )
