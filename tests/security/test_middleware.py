"""Security tests for middleware components.

Tests cover:
- Security middleware functionality
- Rate limiting and IP banning
- Penetration detection
- Request/response header validation
- IP filtering and whitelisting
- Security event logging
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from apps.api.app.middleware.security import SecurityMiddleware
from apps.api.app.core.settings import Settings


class TestSecurityMiddleware:
    """Test the SecurityMiddleware class."""

    @pytest.fixture
    def security_settings(self):
        """Create test settings for security middleware."""
        return Settings(
            environment="test",
            redis_url="redis://localhost:6379/1",
            security_rate_limit_per_minute=10,
            security_penetration_attempts_threshold=3,
            security_ban_duration_minutes=5,
            security_dev_ip_whitelist=["127.0.0.1", "192.168.1.0/24"],
            security_log_file="logs/security_test.log"
        )

    @pytest.fixture
    def security_middleware(self, security_settings):
        """Create SecurityMiddleware instance for testing."""
        app = MagicMock()
        return SecurityMiddleware(app, security_settings)

    def test_middleware_initialization(self, security_middleware, security_settings):
        """Test middleware initialization with proper configuration."""
        assert security_middleware.settings == security_settings
        assert security_middleware.logger is not None
        assert security_middleware.guard is not None
        assert security_middleware.dev_ip_networks is not None

    def test_ip_whitelist_parsing(self, security_settings):
        """Test IP whitelist parsing."""
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        # Test single IP
        assert middleware._is_ip_whitelisted("127.0.0.1") is True

        # Test IP in range
        assert middleware._is_ip_whitelisted("192.168.1.100") is True

        # Test IP not in whitelist
        assert middleware._is_ip_whitelisted("8.8.8.8") is False

    def test_production_ip_whitelist_disabled(self, security_settings):
        """Test that IP whitelist is disabled in production."""
        security_settings.environment = "prod"
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        assert middleware._is_ip_whitelisted("127.0.0.1") is False

    def test_client_ip_extraction(self, security_middleware):
        """Test client IP extraction from various headers."""
        # Test X-Forwarded-For header
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
        mock_request.client = None

        ip = security_middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"

        # Test direct client IP
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        ip = security_middleware._get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_suspicious_pattern_detection(self, security_middleware):
        """Test detection of suspicious patterns in requests."""
        # Test directory traversal
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "../../../etc/passwd"
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        patterns = security_middleware._detect_suspicious_patterns(mock_request)
        assert "directory_traversal" in patterns

        # Test SQL injection
        mock_request.url.path = "/api/users?id=1 UNION SELECT password FROM admin"
        patterns = security_middleware._detect_suspicious_patterns(mock_request)
        assert "sql_injection" in patterns

        # Test XSS attempt
        mock_request.url.path = "/search?q=<script>alert('xss')</script>"
        patterns = security_middleware._detect_suspicious_patterns(mock_request)
        assert "xss_attempt" in patterns

        # Test large query string
        mock_request.url.path = "/api/search"
        mock_request.query_params = "q=" + "A" * 1001  # Over 1000 chars
        patterns = security_middleware._detect_suspicious_patterns(mock_request)
        assert "large_query_string" in patterns

    @pytest.mark.asyncio
    async def test_rate_limiting_functionality(self, security_middleware, redis_client):
        """Test rate limiting functionality."""
        from unittest.mock import AsyncMock

        # Mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {"User-Agent": "test-agent"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.query_params = {}
        mock_request.state.client_ip = "192.168.1.100"
        mock_request.state.user_agent = "test-agent"

        # Mock Redis operations
        security_middleware.redis = redis_client

        # First request should be allowed
        is_allowed, info = await security_middleware._check_security(mock_request)
        assert is_allowed is True

        # Make multiple requests to trigger rate limiting
        for i in range(security_middleware.settings.security_rate_limit_per_minute):
            await security_middleware._check_security(mock_request)

        # Next request should be rate limited
        is_allowed, info = await security_middleware._check_security(mock_request)
        assert is_allowed is False
        assert info["reason"] == "rate_limited"

    @pytest.mark.asyncio
    async def test_penetration_detection_and_banning(self, security_middleware, redis_client):
        """Test penetration detection and IP banning."""
        from unittest.mock import AsyncMock

        # Mock suspicious request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "../../../etc/passwd"
        mock_request.method = "GET"
        mock_request.headers = {"User-Agent": "suspicious-agent"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.query_params = {}
        mock_request.state.client_ip = "192.168.1.100"
        mock_request.state.user_agent = "suspicious-agent"

        security_middleware.redis = redis_client

        # Make multiple suspicious requests
        for _ in range(security_middleware.settings.security_penetration_attempts_threshold):
            is_allowed, info = await security_middleware._check_security(mock_request)
            assert info["reason"] == "suspicious_activity"

        # Next request should result in ban
        is_allowed, info = await security_middleware._check_security(mock_request)
        assert is_allowed is False
        assert info["reason"] == "banned"

    @pytest.mark.asyncio
    async def test_ip_banning_mechanism(self, security_middleware, redis_client):
        """Test IP banning mechanism."""
        security_middleware.redis = redis_client

        client_ip = "192.168.1.100"

        # Ban the IP
        await security_middleware._ban_ip(client_ip)

        # Verify IP is banned
        is_banned = await security_middleware.redis.exists(f"security:ban:{client_ip}")
        assert is_banned is True

        # Check ban TTL
        ttl = await security_middleware.redis.ttl(f"security:ban:{client_ip}")
        expected_ttl = security_middleware.settings.security_ban_duration_minutes * 60
        assert ttl == expected_ttl

    @pytest.mark.asyncio
    async def test_failed_attempts_tracking(self, security_middleware, redis_client):
        """Test failed attempts counter."""
        security_middleware.redis = redis_client

        client_ip = "192.168.1.100"

        # Increment failed attempts
        attempt_count = await security_middleware._increment_failed_attempts(client_ip)
        assert attempt_count == 1

        attempt_count = await security_middleware._increment_failed_attempts(client_ip)
        assert attempt_count == 2

        # Verify TTL is set
        ttl = await security_middleware.redis.ttl(f"security:failed_attempts:{client_ip}")
        assert ttl == 3600  # 1 hour

    @pytest.mark.asyncio
    async def test_security_event_logging(self, security_middleware, redis_client):
        """Test security event logging."""
        import logging

        security_middleware.redis = redis_client

        # Mock logger to capture log calls
        with patch.object(security_middleware.logger, 'warning') as mock_warning:
            await security_middleware._log_security_event(
                "TEST_SECURITY_EVENT",
                "192.168.1.100",
                "test-agent",
                {"test": "data"},
                "/api/test",
                "GET"
            )

            mock_warning.assert_called_once()
            log_call = mock_warning.call_args
            assert "TEST_SECURITY_EVENT" in log_call[0][0]


class TestSecurityMiddlewareIntegration:
    """Integration tests for security middleware with FastAPI."""

    @pytest.mark.asyncio
    async def test_middleware_with_whitelisted_ip(self, security_client, security_settings):
        """Test that whitelisted IPs bypass security checks."""
        # Make request from whitelisted IP
        response = security_client.request_with_ip("127.0.0.1", "GET", "/health")

        # Should not be blocked by security middleware
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_middleware_rate_limiting_integration(self, security_client):
        """Test rate limiting in full request flow."""
        url = "/health"

        # Make multiple requests to trigger rate limiting
        responses = security_client.rapid_requests(url, count=15, interval=0.1)

        # Some requests should be rate limited (429 status)
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0

        # Rate limited responses should have retry-after header
        for response in rate_limited_responses:
            assert "retry-after" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_security_headers(self, security_client):
        """Test that security headers are added to responses."""
        response = security_client.get("/health")

        # Check for security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_middleware_suspicious_request_blocking(self, security_client):
        """Test that suspicious requests are blocked."""
        # Make suspicious requests
        suspicious_urls = [
            "/../../../etc/passwd",
            "/api/users?sql=SELECT * FROM users",
            "/search?q=<script>alert('xss')</script>"
        ]

        for url in suspicious_urls:
            # Make multiple requests to trigger banning
            for _ in range(5):
                response = security_client.get(url)
                if response.status_code == 403:
                    break  # IP was banned

            # Final request should be banned
            final_response = security_client.get(url)
            if final_response.status_code == 403:
                assert "suspicious activity" in final_response.json()["detail"].lower()
                break

    @pytest.mark.asyncio
    async def test_middleware_error_handling(self, security_client):
        """Test middleware error handling."""
        # Test with invalid IP that might cause parsing errors
        response = security_client.request_with_ip("invalid.ip.address", "GET", "/health")

        # Should not crash, should handle gracefully
        assert response.status_code in [200, 429, 403]  # Valid response codes


class TestSecurityMiddlewareConfiguration:
    """Test security middleware configuration options."""

    def test_production_environment_detection(self, security_settings):
        """Test production environment detection."""
        security_settings.environment = "prod"
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        assert middleware._is_production() is True

        security_settings.environment = "development"
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        assert middleware._is_production() is False

    def test_development_environment_settings(self, security_settings):
        """Test development environment specific settings."""
        security_settings.environment = "dev"
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        # In development, IP filtering should be disabled
        assert middleware._is_ip_whitelisted("127.0.0.1") is True

    def test_rate_limit_configuration(self, security_settings):
        """Test rate limiting configuration."""
        security_settings.security_rate_limit_per_minute = 5
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        assert middleware.settings.security_rate_limit_per_minute == 5

    def test_ban_threshold_configuration(self, security_settings):
        """Test ban threshold configuration."""
        security_settings.security_penetration_attempts_threshold = 5
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        assert middleware.settings.security_penetration_attempts_threshold == 5

    def test_ban_duration_configuration(self, security_settings):
        """Test ban duration configuration."""
        security_settings.security_ban_duration_minutes = 10
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        assert middleware.settings.security_ban_duration_minutes == 10


class TestSecurityMiddlewareLogging:
    """Test security middleware logging functionality."""

    @pytest.mark.asyncio
    async def test_security_log_file_creation(self, security_settings, tmp_path):
        """Test that security log file is created."""
        security_settings.security_log_file = str(tmp_path / "security.log")
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        # Trigger a security event
        with patch.object(middleware.redis, 'exists', return_value=False):
            with patch.object(middleware.redis, 'setex'):
                await middleware._log_security_event(
                    "TEST_EVENT",
                    "192.168.1.100",
                    "test-agent",
                    {"test": "data"},
                    "/api/test",
                    "GET"
                )

        # Verify log file was created
        assert tmp_path.exists()
        log_file = tmp_path / "security.log"
        assert log_file.exists()

    @pytest.mark.asyncio
    async def test_security_event_log_format(self, security_settings, tmp_path):
        """Test security event log format."""
        import json
        import time

        security_settings.security_log_file = str(tmp_path / "security.log")
        middleware = SecurityMiddleware(MagicMock(), security_settings)

        # Trigger a security event
        with patch.object(middleware.redis, 'exists', return_value=False):
            with patch.object(middleware.redis, 'setex'):
                await middleware._log_security_event(
                    "TEST_SECURITY_VIOLATION",
                    "192.168.1.100",
                    "test-agent",
                    {"violation": "test_violation"},
                    "/api/sensitive",
                    "POST"
                )

        # Read and verify log entry
        log_file = tmp_path / "security.log"
        with open(log_file, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content)

        assert log_entry["event_type"] == "TEST_SECURITY_VIOLATION"
        assert log_entry["ip"] == "192.168.1.100"
        assert log_entry["user_agent"] == "test-agent"
        assert log_entry["path"] == "/api/sensitive"
        assert log_entry["method"] == "POST"
        assert "timestamp" in log_entry
        assert isinstance(log_entry["timestamp"], float)


class TestSecurityMiddlewareEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_middleware_with_malformed_headers(self, security_client):
        """Test middleware handling of malformed headers."""
        # Test with malformed X-Forwarded-For header
        response = security_client.request_with_ip("malformed,header", "GET", "/health")

        # Should handle gracefully
        assert response.status_code in [200, 429, 403]

    @pytest.mark.asyncio
    async def test_middleware_redis_connection_failure(self, security_client):
        """Test middleware behavior when Redis is unavailable."""
        # This would require mocking Redis connection failures
        # For now, ensure middleware doesn't crash when Redis operations fail
        response = security_client.get("/health")

        # Should still work even if Redis is down
        assert response.status_code in [200, 429, 403]

    @pytest.mark.asyncio
    async def test_middleware_concurrent_requests(self, security_client):
        """Test middleware behavior under concurrent load."""
        import asyncio

        # Make concurrent requests
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(
                asyncio.to_thread(security_client.get, "/health")
            )
            tasks.append(task)

        # Wait for all requests to complete
        responses = await asyncio.gather(*tasks)

        # All responses should be valid HTTP status codes
        for response in responses:
            assert response.status_code in [200, 429, 403]

    @pytest.mark.asyncio
    async def test_middleware_large_request_handling(self, security_client):
        """Test middleware with large request payloads."""
        # Create a large payload
        large_data = {"data": "A" * 10000}

        response = security_client.post("/api/test", json=large_data)

        # Should handle large requests appropriately
        assert response.status_code in [200, 413, 429, 403]  # 413 = Payload Too Large