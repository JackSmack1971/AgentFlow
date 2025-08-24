"""Security tests for MCP (Model Context Protocol) tools.

Tests cover:
- Authentication requirements for MCP tools
- Input sanitization and validation
- SQL injection and XSS prevention
- Audit logging functionality
- Error handling and security boundaries
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.app.core.settings import Settings
from apps.mcp.tools.security import (
    AuthenticationError,
    AuthorizationError,
    InputValidationError,
    audit_log,
    extract_user_from_context,
    require_auth,
    sanitize_input,
    validate_token,
)


class TestInputSanitization:
    """Test input sanitization and validation."""

    def test_sanitize_normal_input(self):
        """Test sanitization of normal input."""
        input_text = "Hello, this is normal input!"
        sanitized = sanitize_input(input_text)
        assert sanitized == input_text

    def test_sanitize_input_with_null_bytes(self):
        """Test removal of null bytes and control characters."""
        input_text = "Hello\x00World\x01Test"
        sanitized = sanitize_input(input_text)
        assert sanitized == "HelloWorldTest"

    def test_sanitize_input_length_limit(self):
        """Test input length validation."""
        long_input = "A" * 10001  # Exceeds default limit of 10000

        with pytest.raises(InputValidationError):
            sanitize_input(long_input)

    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        sql_injections = [
            "SELECT * FROM users",
            "DROP TABLE users;",
            "UNION SELECT password FROM admin",
            "' OR '1'='1",
            "-- DROP DATABASE",
            "/* malicious code */"
        ]

        for injection in sql_injections:
            with pytest.raises(InputValidationError):
                sanitize_input(injection)

    def test_xss_attack_detection(self):
        """Test XSS attack pattern detection."""
        xss_attacks = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<iframe src='evil.com'>",
            "onload=alert('xss')",
            "<object data='evil.swf'>",
            "<embed src='evil.html'>"
        ]

        for attack in xss_attacks:
            with pytest.raises(InputValidationError):
                sanitize_input(attack)

    def test_case_insensitive_sql_detection(self):
        """Test case-insensitive SQL injection detection."""
        mixed_case_sql = "select * from Users where id = 1"
        with pytest.raises(InputValidationError):
            sanitize_input(mixed_case_sql)


class TestTokenValidation:
    """Test JWT token validation."""

    def test_valid_token_validation(self, settings):
        """Test validation of valid JWT token."""
        import jwt
        import time

        # Create a valid token
        payload = {
            "sub": "test@example.com",
            "exp": int(time.time()) + 3600,  # Expires in 1 hour
            "iat": int(time.time()),
            "type": "access"
        }

        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

        # Should not raise exception
        result = validate_token(token, settings)
        assert result["sub"] == "test@example.com"

    def test_expired_token_rejection(self, settings):
        """Test rejection of expired tokens."""
        import jwt
        import time

        # Create an expired token
        payload = {
            "sub": "test@example.com",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "iat": int(time.time()) - 7200,
            "type": "access"
        }

        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

        with pytest.raises(AuthenticationError):
            validate_token(token, settings)

    def test_invalid_token_rejection(self, settings):
        """Test rejection of invalid tokens."""
        invalid_tokens = [
            "not.a.jwt.token",
            "invalid_token_format",
            "header.payload.signature.extra",
            ""
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises(AuthenticationError):
                validate_token(invalid_token, settings)

    def test_tampered_token_rejection(self, settings):
        """Test rejection of tampered tokens."""
        import jwt
        import time

        # Create a valid token
        payload = {
            "sub": "test@example.com",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "type": "access"
        }

        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

        # Tamper with the token by changing the payload
        parts = token.split('.')
        tampered_payload = jwt.encode(
            {"sub": "hacker@example.com", "exp": int(time.time()) + 3600},
            "wrong_key",
            algorithm="HS256"
        ).split('.')[1]  # Get just the payload part

        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

        with pytest.raises(AuthenticationError):
            validate_token(tampered_token, settings)


class TestAuthenticationDecorator:
    """Test the require_auth decorator."""

    @pytest.mark.asyncio
    async def test_require_auth_with_valid_user(self):
        """Test require_auth allows authenticated users."""
        from mcp.server.fastmcp import Context

        # Mock context with user info
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"sub": "test@example.com"}

        @require_auth
        async def mock_tool(ctx):
            return "success"

        result = await mock_tool(ctx)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_require_auth_without_user_info(self):
        """Test require_auth rejects requests without user info."""
        from mcp.server.fastmcp import Context

        # Mock context without user info
        ctx = MagicMock(spec=Context)
        ctx.user_info = None
        ctx.error = AsyncMock()

        @require_auth
        async def mock_tool(ctx):
            return "should not reach here"

        with pytest.raises(AuthenticationError):
            await mock_tool(ctx)

        ctx.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_require_auth_with_invalid_user_info(self):
        """Test require_auth rejects invalid user info."""
        from mcp.server.fastmcp import Context

        # Mock context with invalid user info
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"invalid": "data"}
        ctx.error = AsyncMock()

        @require_auth
        async def mock_tool(ctx):
            return "should not reach here"

        with pytest.raises(AuthenticationError):
            await mock_tool(ctx)


class TestAuditLogging:
    """Test audit logging functionality."""

    @pytest.mark.asyncio
    async def test_audit_log_successful_operation(self, tmp_path):
        """Test audit logging for successful operations."""
        from mcp.server.fastmcp import Context
        import json
        import os

        log_file = tmp_path / "test_audit.log"

        # Mock context
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"sub": "test@example.com"}

        @audit_log(log_file=str(log_file))
        async def mock_tool(ctx, param1="value1"):
            return "success"

        # Execute the tool
        result = await mock_tool(ctx, param1="test_value")
        assert result == "success"

        # Verify audit log was created
        assert log_file.exists()

        # Read and verify log entry
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.read())

        assert log_entry["user"] == "test@example.com"
        assert log_entry["tool"] == "mock_tool"
        assert log_entry["args"]["param1"] == "test_value"
        assert log_entry["status"] == "completed"

    @pytest.mark.asyncio
    async def test_audit_log_failed_operation(self, tmp_path):
        """Test audit logging for failed operations."""
        from mcp.server.fastmcp import Context
        import json

        log_file = tmp_path / "test_audit.log"

        # Mock context
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"sub": "test@example.com"}

        @audit_log(log_file=str(log_file))
        async def mock_tool(ctx):
            raise ValueError("Test error")

        # Execute the tool (should fail)
        with pytest.raises(ValueError):
            await mock_tool(ctx)

        # Verify audit log was created with error
        assert log_file.exists()

        # Read and verify log entry
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.read())

        assert log_entry["status"] == "failed"
        assert log_entry["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_audit_log_input_sanitization(self, tmp_path):
        """Test that audit log sanitizes sensitive inputs."""
        from mcp.server.fastmcp import Context
        import json

        log_file = tmp_path / "test_audit.log"

        # Mock context
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"sub": "test@example.com"}

        @audit_log(log_file=str(log_file))
        async def mock_tool(ctx, long_param="A" * 200):
            return "success"

        # Execute the tool
        result = await mock_tool(ctx, long_param="A" * 200)
        assert result == "success"

        # Verify audit log was created and input was sanitized
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.read())

        # Long parameter should be truncated
        assert len(log_entry["args"]["long_param"]) <= 100


class TestInputValidationDecorator:
    """Test the validate_input decorator."""

    @pytest.mark.asyncio
    async def test_validate_input_success(self):
        """Test successful input validation."""
        from mcp.server.fastmcp import Context

        # Mock context
        ctx = MagicMock(spec=Context)

        @validate_input(max_length={'param1': 100})
        async def mock_tool(ctx, param1="short_value"):
            return f"processed: {param1}"

        result = await mock_tool(ctx, param1="test_value")
        assert result == "processed: test_value"

    @pytest.mark.asyncio
    async def test_validate_input_required_field(self):
        """Test validation of required fields."""
        from mcp.server.fastmcp import Context

        # Mock context
        ctx = MagicMock(spec=Context)

        @validate_input(required={'param1': True})
        async def mock_tool(ctx, param1=""):
            return f"processed: {param1}"

        with pytest.raises(InputValidationError):
            await mock_tool(ctx, param1="")

    @pytest.mark.asyncio
    async def test_validate_input_sanitization(self):
        """Test that validate_input applies sanitization."""
        from mcp.server.fastmcp import Context

        # Mock context
        ctx = MagicMock(spec=Context)

        @validate_input(max_length={'param1': 100})
        async def mock_tool(ctx, param1=""):
            return f"processed: {param1}"

        # Input with potential XSS
        result = await mock_tool(ctx, param1="<script>alert('xss')</script>")
        # Should be sanitized (script tags removed)
        assert "<script>" not in result


class TestMCPToolSecurityIntegration:
    """Test MCP tool security in realistic scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_tool_with_comprehensive_security(self, tmp_path):
        """Test MCP tool with multiple security layers."""
        from mcp.server.fastmcp import Context
        import json

        log_file = tmp_path / "security_test.log"

        # Mock context
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"sub": "test@example.com"}
        ctx.error = AsyncMock()

        @require_auth
        @audit_log(log_file=str(log_file))
        @validate_input(max_length={'query': 1000})
        async def secure_search_tool(ctx, query="test query"):
            """A secure search tool with multiple security layers."""
            # Simulate some processing
            return f"Search results for: {query}"

        # Test successful execution
        result = await secure_search_tool(ctx, query="safe query")
        assert "safe query" in result

        # Verify audit log
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.read())

        assert log_entry["status"] == "completed"
        assert log_entry["user"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_mcp_tool_attack_prevention(self):
        """Test that MCP tools prevent various attacks."""
        from mcp.server.fastmcp import Context

        # Mock context
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"sub": "test@example.com"}
        ctx.error = AsyncMock()

        @require_auth
        @validate_input(max_length={'query': 100})
        async def search_tool(ctx, query=""):
            return f"Results: {query}"

        # Test SQL injection prevention
        with pytest.raises(InputValidationError):
            await search_tool(ctx, query="SELECT * FROM users")

        # Test XSS prevention
        with pytest.raises(InputValidationError):
            await search_tool(ctx, query="<script>alert('xss')</script>")

        # Test length limit
        with pytest.raises(InputValidationError):
            await search_tool(ctx, query="A" * 10000)

    @pytest.mark.asyncio
    async def test_mcp_tool_error_handling(self):
        """Test error handling in secured MCP tools."""
        from mcp.server.fastmcp import Context

        # Mock context
        ctx = MagicMock(spec=Context)
        ctx.user_info = {"sub": "test@example.com"}
        ctx.error = AsyncMock()

        @require_auth
        async def failing_tool(ctx):
            raise RuntimeError("Internal error")

        # Should handle errors gracefully
        with pytest.raises(RuntimeError):
            await failing_tool(ctx)

        # Should have called error handler
        ctx.error.assert_called_once()


class TestSecurityBoundaryValidation:
    """Test security boundaries and access control."""

    @pytest.mark.asyncio
    async def test_user_context_isolation(self):
        """Test that user contexts are properly isolated."""
        from mcp.server.fastmcp import Context

        # Mock contexts for different users
        ctx1 = MagicMock(spec=Context)
        ctx1.user_info = {"sub": "user1@example.com"}

        ctx2 = MagicMock(spec=Context)
        ctx2.user_info = {"sub": "user2@example.com"}

        results = []

        @require_auth
        async def user_specific_tool(ctx):
            user = extract_user_from_context(ctx)
            results.append(user)
            return f"Hello {user}"

        # Execute for different users
        result1 = await user_specific_tool(ctx1)
        result2 = await user_specific_tool(ctx2)

        assert result1 == "Hello user1@example.com"
        assert result2 == "Hello user2@example.com"
        assert results == ["user1@example.com", "user2@example.com"]

    @pytest.mark.asyncio
    async def test_unauthenticated_access_prevention(self):
        """Test that unauthenticated access is properly prevented."""
        from mcp.server.fastmcp import Context

        # Mock unauthenticated context
        ctx = MagicMock(spec=Context)
        ctx.user_info = None
        ctx.error = AsyncMock()

        call_count = 0

        @require_auth
        async def protected_tool(ctx):
            nonlocal call_count
            call_count += 1
            return "This should not be reached"

        # Should fail authentication
        with pytest.raises(AuthenticationError):
            await protected_tool(ctx)

        # Tool should not have been executed
        assert call_count == 0
        ctx.error.assert_called_once()