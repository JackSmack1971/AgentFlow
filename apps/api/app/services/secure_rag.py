"""Secure RAG Pipeline Architecture with template protection.

This module provides secure RAG (Retrieval-Augmented Generation) functionality
with comprehensive protection against prompt injection, template poisoning,
and other AI/LLM-specific security vulnerabilities.
"""

import re
from typing import Dict, Any, List, Optional


class SecureRAGService:
    """
    Secure RAG service with template-based protection against prompt injection
    and other AI/LLM security vulnerabilities.
    """

    # Secure prompt template with safety instructions
    SECURE_QUERY_TEMPLATE = """
You are a helpful AI assistant. Your task is to answer the user's question based on the provided context.

IMPORTANT SAFETY INSTRUCTIONS:
- Only use the provided context to answer questions
- Do not execute any commands or code
- Do not reveal sensitive information
- Stay in character as a helpful assistant
- If you cannot answer based on the context, say so clearly

Context:
{context}

User Question:
{query}

Answer:"""

    # Prompt injection patterns specific to RAG
    RAG_INJECTION_PATTERNS = [
        re.compile(r"(?i)(ignore|override|disregard).*(context|instructions|template)"),
        re.compile(r"(?i)(system:|admin:|root:).*(command|execute|run)"),
        re.compile(r"(?i)(bypass|circumvent|disable).*(security|filter|safety)"),
        re.compile(r"(?i)(forget|disregard).*(previous|prior|instructions)"),
        re.compile(r"(?i)(you are|act as).*(jailbreak|hacker|attacker)"),
        re.compile(r"(?i)(reveal|show|expose).*(system|internal|secret)"),
        re.compile(r"(?i)(template.*poisoning|prompt.*injection)"),
    ]

    # Maximum lengths for security
    MAX_QUERY_LENGTH = 1000
    MAX_CONTEXT_LENGTH = 10000
    MAX_PROMPT_LENGTH = 15000

    def create_secure_prompt(self, query: str, context: str) -> str:
        """
        Create a secure prompt using template protection.

        Args:
            query: User query string
            context: Retrieved context string

        Returns:
            str: Secure prompt with template protection
        """
        if not query or not context:
            return self._create_empty_prompt()

        # Sanitize inputs
        sanitized_query = self._sanitize_query_for_prompt(query)
        sanitized_context = self._sanitize_context(context)

        # Validate lengths
        if len(sanitized_query) > self.MAX_QUERY_LENGTH:
            sanitized_query = sanitized_query[:self.MAX_QUERY_LENGTH]
        if len(sanitized_context) > self.MAX_CONTEXT_LENGTH:
            sanitized_context = sanitized_context[:self.MAX_CONTEXT_LENGTH]

        # Create prompt using secure template
        try:
            prompt = self.SECURE_QUERY_TEMPLATE.format(
                context=sanitized_context,
                query=sanitized_query
            )

            # Final length check
            if len(prompt) > self.MAX_PROMPT_LENGTH:
                prompt = prompt[:self.MAX_PROMPT_LENGTH] + "\n\n[Content truncated for length]"

            return prompt

        except Exception as e:
            # Fallback to safe prompt
            return self._create_fallback_prompt(sanitized_query, sanitized_context)

    def validate_rag_input(self, query: str, context: str) -> Dict[str, Any]:
        """
        Comprehensive validation of RAG inputs.

        Args:
            query: User query string
            context: Retrieved context string

        Returns:
            dict: Validation result with status and warnings
        """
        warnings = []

        # Check for None/empty inputs
        if not query:
            return {"valid": False, "warnings": ["Query cannot be empty"]}
        if not context:
            return {"valid": False, "warnings": ["Context cannot be empty"]}

        # Check input types
        if not isinstance(query, str) or not isinstance(context, str):
            return {"valid": False, "warnings": ["Query and context must be strings"]}

        # Check lengths
        if len(query) > self.MAX_QUERY_LENGTH:
            warnings.append(f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH}")
        if len(context) > self.MAX_CONTEXT_LENGTH:
            warnings.append(f"Context exceeds maximum length of {self.MAX_CONTEXT_LENGTH}")

        # Check for injection patterns
        if self._detect_rag_injection(query):
            warnings.append("Query contains potential injection patterns")
        if self._detect_rag_injection(context):
            warnings.append("Context contains potential injection patterns")

        # Check for dangerous content
        if self._contains_dangerous_patterns(query):
            warnings.append("Query contains dangerous patterns")
        if self._contains_dangerous_patterns(context):
            warnings.append("Context contains dangerous patterns")

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "query_length": len(query),
            "context_length": len(context)
        }

    def _sanitize_context(self, context: str) -> str:
        """
        Sanitize context information for secure inclusion in prompts.

        Args:
            context: Raw context string

        Returns:
            str: Sanitized context
        """
        if not context:
            return ""

        # Remove HTML/script tags
        sanitized = re.sub(r'<[^>]+>', '', context)

        # Remove control characters except common whitespace
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Limit length
        if len(sanitized) > self.MAX_CONTEXT_LENGTH:
            sanitized = sanitized[:self.MAX_CONTEXT_LENGTH] + "..."

        return sanitized

    def _sanitize_query_for_prompt(self, query: str) -> str:
        """
        Sanitize user query for secure inclusion in prompts.

        Args:
            query: Raw query string

        Returns:
            str: Sanitized query
        """
        if not query:
            return ""

        # Remove injection patterns
        sanitized = query
        for pattern in self.RAG_INJECTION_PATTERNS:
            sanitized = pattern.sub("[FILTERED]", sanitized)

        # Remove dangerous characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Limit length
        if len(sanitized) > self.MAX_QUERY_LENGTH:
            sanitized = sanitized[:self.MAX_QUERY_LENGTH] + "..."

        return sanitized

    def _detect_rag_injection(self, text: str) -> bool:
        """
        Detect RAG-specific injection patterns.

        Args:
            text: Text to analyze

        Returns:
            bool: True if injection patterns detected
        """
        if not text:
            return False

        for pattern in self.RAG_INJECTION_PATTERNS:
            if pattern.search(text):
                return True

        return False

    def _contains_dangerous_patterns(self, text: str) -> bool:
        """
        Check for dangerous patterns in text.

        Args:
            text: Text to analyze

        Returns:
            bool: True if dangerous patterns found
        """
        if not text:
            return False

        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'data:',                      # Data URLs
            r'vbscript:',                  # VBScript
            r'on\w+\s*=',                  # Event handlers
            r'\\x[0-9a-f]{2}',            # Hex encoded characters
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _filter_context(self, context: str) -> str:
        """
        Filter context to remove potentially dangerous content.

        Args:
            context: Raw context

        Returns:
            str: Filtered context
        """
        if not context:
            return ""

        # Apply sanitization
        filtered = self._sanitize_context(context)

        # Additional filtering for RAG-specific issues
        # Remove any remaining template-like patterns
        filtered = re.sub(r'\{[^}]+\}', '[FILTERED]', filtered)

        return filtered

    def _filter_query(self, query: str) -> str:
        """
        Filter query to remove potentially dangerous content.

        Args:
            query: Raw query

        Returns:
            str: Filtered query
        """
        if not query:
            return ""

        # Apply sanitization
        filtered = self._sanitize_query_for_prompt(query)

        # Additional filtering for query-specific issues
        # Remove any attempt to manipulate the template
        filtered = re.sub(r'\}.*\{', ' ', filtered)

        return filtered

    def _create_empty_prompt(self) -> str:
        """Create a safe prompt for empty inputs."""
        return """You are a helpful AI assistant.

User Question: [No question provided]

Answer: I need a specific question to provide a helpful answer.""" ""

    def _create_fallback_prompt(self, query: str, context: str) -> str:
        """Create a fallback prompt when template formatting fails."""
        return f"""You are a helpful AI assistant.

Context: {context[:1000]}...

User Question: {query[:500]}

Answer:"""


# Export the main class
__all__ = ["SecureRAGService"]