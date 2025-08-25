"""Input validation and sanitization service for security.

This module provides comprehensive input validation and sanitization
to prevent injection attacks, XSS, and other security vulnerabilities.
"""

import re
import string
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse

from ..exceptions import SecurityError


class SecurityValidator:
    """
    Multi-layer input validation and sanitization system
    designed to prevent injection attacks and malicious input.
    """

    # Prompt injection patterns with context awareness
    PROMPT_INJECTION_PATTERNS = [
        re.compile(r"(?i)(ignore|override|system:|admin:|root:)"),
        re.compile(r"(?i)(execute|run|eval|exec|spawn)"),
        re.compile(r"(?i)(show|return|output).*(all|everything|data|secrets)"),
        re.compile(r"(?i)(bypass|disable|circumvent).*(security|auth|filter)"),
        re.compile(r"(?i)(as|acting as).*(admin|root|superuser)"),
        re.compile(r"(?i)(forget|disregard).*(previous|prior|instructions)"),
        re.compile(r"(?i)(you are|act as).*(jailbreak|hacker|attacker)"),
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        re.compile(r"(?i)(;|--|\*|\/\*|\*\/|xp_|sp_|exec|union|select|insert|update|delete|drop|create|alter)"),
        re.compile(r"(?i)('|" + r'"|`)'),  # Quote patterns
        re.compile(r"(?i)(\b(and|or)\b.*(=|>|<))"),  # Logic operators
    ]

    # XSS patterns
    XSS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<[^>]+>", re.IGNORECASE),  # Basic HTML tags
    ]

    # Collection name validation pattern
    ALLOWED_COLLECTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    # Email validation pattern
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    # URL validation pattern
    URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

    def validate_input(
        self,
        input_data: str,
        context: str = "general",
        max_length: int = 10000
    ) -> Dict[str, Any]:
        """
        Comprehensive input validation with security pattern detection.

        Args:
            input_data: Input string to validate
            context: Validation context (general, rag_query, collection_name, etc.)
            max_length: Maximum allowed input length

        Returns:
            dict: Validation result with status, threats, and sanitized content
        """
        if not input_data:
            return {
                "valid": False,
                "error": "Input cannot be empty",
                "threats": ["empty_input"]
            }

        if len(input_data) > max_length:
            return {
                "valid": False,
                "error": f"Input exceeds maximum length of {max_length}",
                "threats": ["length_exceeded"]
            }

        threats = []
        sanitized = input_data

        # Apply context-specific validation
        if context == "rag_query":
            sanitized = self.sanitize_rag_query(input_data)
            if self._detect_prompt_injection(input_data):
                threats.append("prompt_injection")
        elif context == "collection_name":
            sanitized = self.sanitize_collection_name(input_data)
            if not self.ALLOWED_COLLECTION_NAME_PATTERN.match(sanitized):
                threats.append("invalid_collection_name")
        elif context == "email":
            sanitized = self._sanitize_email(input_data)
            if not self.EMAIL_PATTERN.match(sanitized):
                threats.append("invalid_email")
        elif context == "url":
            sanitized = self._sanitize_url(input_data)
            if not self.URL_PATTERN.match(sanitized):
                threats.append("invalid_url")
        else:
            sanitized = self._sanitize_general_input(input_data)

        # General security checks
        if self._detect_sql_injection(input_data):
            threats.append("sql_injection")

        if self._detect_xss(input_data):
            threats.append("xss_attempt")

        return {
            "valid": len(threats) == 0,
            "threats": threats,
            "sanitized": sanitized,
            "original_length": len(input_data),
            "sanitized_length": len(sanitized)
        }

    @classmethod
    def sanitize_rag_query(cls, query: str, max_length: int = 1000) -> str:
        """
        Sanitize RAG queries for prompt injection and other attacks.

        Args:
            query: Raw RAG query
            max_length: Maximum allowed query length

        Returns:
            str: Sanitized query
        """
        if not query:
            return ""

        # Truncate if too long
        if len(query) > max_length:
            query = query[:max_length]

        # Remove or replace dangerous patterns
        sanitized = query

        # Replace prompt injection patterns with safe alternatives
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            sanitized = pattern.sub("[FILTERED]", sanitized)

        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

        return sanitized

    @classmethod
    def sanitize_collection_name(cls, name: str, max_length: int = 64) -> str:
        """
        Sanitize collection names for injection attacks.

        Args:
            name: Raw collection name
            max_length: Maximum allowed name length

        Returns:
            str: Sanitized collection name
        """
        if not name:
            return ""

        # Truncate if too long
        if len(name) > max_length:
            name = name[:max_length]

        # Remove dangerous characters
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", name)

        # Ensure it doesn't start or end with special characters
        sanitized = sanitized.strip("-_")

        return sanitized

    @classmethod
    def sanitize_user_input(cls, input_data: str, input_type: str = "general") -> str:
        """
        General user input sanitization with type-specific handling.

        Args:
            input_data: Raw user input
            input_type: Type of input (general, email, url, sql)

        Returns:
            str: Sanitized input
        """
        if not input_data:
            return ""

        if input_type == "email":
            return cls._sanitize_email(input_data)
        elif input_type == "url":
            return cls._sanitize_url(input_data)
        elif input_type == "sql":
            return cls._sanitize_sql_input(input_data)
        else:
            return cls._sanitize_general_input(input_data)

    @classmethod
    def _sanitize_email(cls, email: str) -> str:
        """Sanitize email address."""
        if not email:
            return ""

        # Basic email sanitization
        email = email.strip().lower()

        # Remove any whitespace
        email = re.sub(r'\s+', '', email)

        # Basic validation
        if cls.EMAIL_PATTERN.match(email):
            return email
        else:
            # Remove potentially dangerous characters
            safe_chars = string.ascii_letters + string.digits + "@.-_"
            return ''.join(c for c in email if c in safe_chars)

    @classmethod
    def _sanitize_url(cls, url: str) -> str:
        """Sanitize URL input."""
        if not url:
            return ""

        url = url.strip()

        # Remove dangerous protocols
        dangerous_protocols = ["javascript:", "data:", "vbscript:", "file:"]
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                return ""

        # Parse and reconstruct URL
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return ""

            # Reconstruct safe URL
            safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                safe_url += f"?{parsed.query}"
            if parsed.fragment:
                safe_url += f"#{parsed.fragment}"

            return safe_url
        except Exception:
            return ""

    @classmethod
    def _sanitize_sql_input(cls, input_data: str) -> str:
        """Sanitize SQL input parameters."""
        if not input_data:
            return ""

        # Remove dangerous SQL patterns
        sanitized = input_data

        for pattern in cls.SQL_INJECTION_PATTERNS:
            sanitized = pattern.sub("", sanitized)

        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        return sanitized

    @classmethod
    def _sanitize_general_input(cls, input_data: str) -> str:
        """General input sanitization."""
        if not input_data:
            return ""

        # Remove HTML/XSS patterns
        sanitized = input_data

        for pattern in cls.XSS_PATTERNS:
            sanitized = pattern.sub("", sanitized)

        # Remove control characters except common whitespace
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        return sanitized

    def _detect_prompt_injection(self, input_data: str) -> bool:
        """Detect prompt injection patterns."""
        if not input_data:
            return False

        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if pattern.search(input_data):
                return True

        return False

    def _detect_sql_injection(self, input_data: str) -> bool:
        """Detect SQL injection patterns."""
        if not input_data:
            return False

        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern.search(input_data):
                return True

        return False

    def _detect_xss(self, input_data: str) -> bool:
        """Detect XSS patterns."""
        if not input_data:
            return False

        for pattern in self.XSS_PATTERNS:
            if pattern.search(input_data):
                return True

        return False

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security validation statistics."""
        return {
            "patterns": {
                "prompt_injection": len(self.PROMPT_INJECTION_PATTERNS),
                "sql_injection": len(self.SQL_INJECTION_PATTERNS),
                "xss": len(self.XSS_PATTERNS)
            },
            "validation_rules": {
                "max_general_length": 10000,
                "max_rag_query_length": 1000,
                "max_collection_name_length": 64,
                "email_validation": True,
                "url_validation": True
            }
        }


# Export the main class
__all__ = ["SecurityValidator"]