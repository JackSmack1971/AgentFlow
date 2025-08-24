"""Security tests for MCP tools."""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import Context

from apps.mcp.tools.rag_search import rag_search_tool
from apps.mcp.tools.schemas import RagSearchRequest, RagSearchResponse
from apps.mcp.tools.security import (
    AuthenticationError,
    InputValidationError,
    audit_log,
    extract_user_from_context,
    require_auth,
    sanitize_input,
    validate_input,
    validate_token,
)


class TestSecurity:
    """Test security utilities and decorators."""

    def test_sanitize_input_valid(self):
        """Test input sanitization with valid input."""
        assert sanitize_input("Hello World") == "Hello World"
        assert sanitize_input("Test query with numbers 123") == "Test query with numbers 123"

    def test_sanitize_input_sql_injection(self):
        """Test input sanitization blocks SQL injection."""
        with pytest.raises(InputValidationError, match="Potential SQL injection detected"):
            sanitize_input("SELECT * FROM users WHERE id = 1")

        with pytest.raises(InputValidationError, match="Potential SQL injection detected"):
            sanitize_input("DROP TABLE users")

    def test_sanitize_input_xss(self):
        """Test input sanitization blocks XSS attacks."""
        with pytest.raises(InputValidationError, match="Potential XSS attack detected"):
            sanitize_input("<script>alert('xss')</script>")

        with pytest.raises(InputValidationError, match="Potential XSS attack detected"):
            sanitize_input("javascript:alert('xss')")

    def test_sanitize_input_length_limit(self):
        """Test input sanitization enforces length limits."""
        long_input = "a" * 1001
        with pytest.raises(InputValidationError, match="Input exceeds maximum length"):
            sanitize_input(long_input, max_length=1000)

    def test_sanitize_input_null_bytes(self):
        """Test input sanitization removes null bytes."""
        result = sanitize_input("test\x00null\x01bytes")
        assert "\x00" not in result
        assert "\x01" not in result

    def test_extract_user_from_context_valid(self):
        """Test extracting user info from valid context."""
        ctx = MagicMock()
        ctx.user_info = {"sub": "test@example.com", "role": "user"}

        user = extract_user_from_context(ctx)
        assert user == "test@example.com"

    def test_extract_user_from_context_missing(self):
        """Test extracting user info from context without user_info."""
        ctx = MagicMock()
        del ctx.user_info  # Simulate missing user_info

        with pytest.raises(AuthenticationError, match="No user information in context"):
            extract_user_from_context(ctx)

    def test_extract_user_from_context_none(self):
        """Test extracting user info from context with None user_info."""
        ctx = MagicMock()
        ctx.user_info = None

        with pytest.raises(AuthenticationError, match="No user information in context"):
            extract_user_from_context(ctx)


class TestAuditLogging:
    """Test audit logging functionality."""

    @pytest.mark.asyncio
    async def test_audit_log_decorator(self):
        """Test audit log decorator writes to log file."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
            log_file = tmp.name

        try:
            @audit_log(log_file)
            async def test_function(ctx, arg1, arg2="default"):
                return "success"

            ctx = MagicMock()
            ctx.user_info = {"sub": "test@example.com"}

            result = await test_function(ctx, "value1", arg2="value2")
            assert result == "success"

            # Check audit log was written
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "test@example.com" in log_content
                assert "test_function" in log_content
                assert "started" in log_content
                assert "completed" in log_content

        finally:
            os.unlink(log_file)

    @pytest.mark.asyncio
    async def test_audit_log_decorator_failure(self):
        """Test audit log decorator logs failures."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
            log_file = tmp.name

        try:
            @audit_log(log_file)
            async def failing_function(ctx):
                raise ValueError("Test error")

            ctx = MagicMock()
            ctx.user_info = {"sub": "test@example.com"}

            with pytest.raises(ValueError):
                await failing_function(ctx)

            # Check failure was logged
            with open(log_file, 'r') as f:
                log_content = f.read()
                assert "failed" in log_content
                assert "Test error" in log_content

        finally:
            os.unlink(log_file)


class TestAuthentication:
    """Test authentication decorator."""

    @pytest.mark.asyncio
    async def test_require_auth_success(self):
        """Test successful authentication."""
        @require_auth
        async def protected_function(ctx):
            return "success"

        ctx = MagicMock()
        ctx.user_info = {"sub": "test@example.com"}

        result = await protected_function(ctx)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_require_auth_failure(self):
        """Test authentication failure."""
        @require_auth
        async def protected_function(ctx):
            return "success"

        ctx = MagicMock()
        ctx.error = AsyncMock()  # Make error method async
        # No user_info attribute

        with pytest.raises(AuthenticationError):
            await protected_function(ctx)


class TestInputValidation:
    """Test input validation decorator."""

    @pytest.mark.asyncio
    async def test_validate_input_success(self):
        """Test successful input validation."""
        @validate_input(query={"max_length": 100, "required": True})
        async def test_function(ctx, query):
            return f"processed: {query}"

        ctx = MagicMock()
        result = await test_function(ctx, query="valid query")
        assert result == "processed: valid query"

    @pytest.mark.asyncio
    async def test_validate_input_required_missing(self):
        """Test validation with missing required parameter."""
        @validate_input(query={"required": True})
        async def test_function(ctx, query=None):
            return f"processed: {query}"

        ctx = MagicMock()

        # Test with None value
        with pytest.raises(InputValidationError, match="Required parameter query is empty"):
            await test_function(ctx, query=None)

    @pytest.mark.asyncio
    async def test_validate_input_sanitization(self):
        """Test that input validation applies sanitization."""
        @validate_input(query={"max_length": 100})
        async def test_function(ctx, query):
            return f"processed: {query}"

        ctx = MagicMock()

        # Test with valid input that gets sanitized
        result = await test_function(ctx, query="valid query with spaces")
        assert result == "processed: valid query with spaces"


class TestRagSearchSecurity:
    """Test RAG search tool security."""

    @pytest.mark.asyncio
    async def test_rag_search_unauthenticated(self):
        """Test RAG search fails without authentication."""
        ctx = MagicMock()
        ctx.error = AsyncMock()  # Make error method async
        # No user_info

        request = RagSearchRequest(query="test query", top_k=5)

        with pytest.raises(Exception):  # Will be ToolExecutionError wrapping AuthenticationError
            await rag_search_tool(ctx, request)

    @pytest.mark.asyncio
    async def test_rag_search_authenticated(self):
        """Test RAG search succeeds with authentication."""
        ctx = MagicMock()
        ctx.user_info = {"sub": "test@example.com"}
        ctx.info = AsyncMock()
        ctx.error = AsyncMock()

        request = RagSearchRequest(query="test query", top_k=5)

        # Mock the external API call
        with patch('apps.mcp.tools.rag_search._get_rag_api_url', return_value='http://test.api'), \
             patch('apps.mcp.tools.rag_search._build_headers', return_value={}), \
             patch('httpx.AsyncClient') as mock_client:

            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"answer": "test response", "sources": []}

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await rag_search_tool(ctx, request)
            assert isinstance(result, RagSearchResponse)

    @pytest.mark.asyncio
    async def test_rag_search_input_validation(self):
        """Test RAG search input validation."""
        ctx = MagicMock()
        ctx.user_info = {"sub": "test@example.com"}

        # Test with malicious input
        request = RagSearchRequest(query="<script>alert('xss')</script>", top_k=5)

        with pytest.raises(InputValidationError):
            await rag_search_tool(ctx, request)


if __name__ == "__main__":
    pytest.main([__file__])