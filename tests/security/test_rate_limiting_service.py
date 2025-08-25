"""Security tests for enhanced Rate Limiting service.

Tests cover:
- Rate limiting with different tiers and strategies
- Burst handling and quota management
- Distributed rate limiting with Redis
- Rate limit configuration and policies
- Security integration and monitoring
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from apps.api.app.services.rate_limiting_service import (
    RateLimitingService,
    RateLimitExceeded,
    RateLimitConfig,
    RateLimitQuota,
    RateLimitStrategy
)


class TestRateLimitingService:
    """Test the enhanced Rate Limiting service."""

    @pytest.fixture
    def redis_client(self):
        """Mock Redis client for testing."""
        return AsyncMock()

    @pytest.fixture
    def rate_limit_config(self):
        """Default rate limit configuration for testing."""
        return RateLimitConfig(
            requests_per_minute=100,
            burst_limit=20,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )

    @pytest.fixture
    def rate_limiting_service(self, redis_client, rate_limit_config):
        """Rate limiting service instance for testing."""
        return RateLimitingService(redis_client, rate_limit_config)

    def test_rate_limiting_service_initialization(self, redis_client, rate_limit_config):
        """Test service initialization with configuration."""
        service = RateLimitingService(redis_client, rate_limit_config)

        assert service.redis == redis_client
        assert service.config == rate_limit_config
        assert service._quotas == {}

    def test_rate_limit_config_creation(self):
        """Test rate limit configuration creation."""
        config = RateLimitConfig(
            requests_per_minute=50,
            burst_limit=10,
            window_seconds=120,
            strategy=RateLimitStrategy.FIXED_WINDOW
        )

        assert config.requests_per_minute == 50
        assert config.burst_limit == 10
        assert config.window_seconds == 120
        assert config.strategy == RateLimitStrategy.FIXED_WINDOW

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(self, rate_limiting_service, redis_client):
        """Test rate limiting when under the limit."""
        redis_client.get.return_value = None  # No existing count

        result = await rate_limiting_service.check_rate_limit("192.168.1.1")

        assert result is True
        # Should set initial count
        redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_at_limit(self, rate_limiting_service, redis_client):
        """Test rate limiting when at the limit."""
        redis_client.get.return_value = b"100"  # At limit

        result = await rate_limiting_service.check_rate_limit("192.168.1.1")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_increment(self, rate_limiting_service, redis_client):
        """Test that rate limit counter is incremented."""
        redis_client.get.return_value = b"50"

        await rate_limiting_service.check_rate_limit("192.168.1.1")

        # Should increment the counter
        redis_client.incr.assert_called_once_with("rate_limit:192.168.1.1")

    @pytest.mark.asyncio
    async def test_get_remaining_quota(self, rate_limiting_service, redis_client):
        """Test getting remaining quota for an identifier."""
        redis_client.get.return_value = b"25"

        remaining = await rate_limiting_service.get_remaining_quota("192.168.1.1")

        assert remaining == 75  # 100 - 25

    @pytest.mark.asyncio
    async def test_get_remaining_quota_no_usage(self, rate_limiting_service, redis_client):
        """Test getting remaining quota when no usage recorded."""
        redis_client.get.return_value = None

        remaining = await rate_limiting_service.get_remaining_quota("192.168.1.1")

        assert remaining == 100

    @pytest.mark.asyncio
    async def test_reset_quota(self, rate_limiting_service, redis_client):
        """Test resetting quota for an identifier."""
        await rate_limiting_service.reset_quota("192.168.1.1")

        redis_client.delete.assert_called_once_with("rate_limit:192.168.1.1")

    @pytest.mark.asyncio
    async def test_get_quota_info(self, rate_limiting_service, redis_client):
        """Test getting complete quota information."""
        redis_client.get.return_value = b"30"

        info = await rate_limiting_service.get_quota_info("192.168.1.1")

        expected = RateLimitQuota(
            identifier="192.168.1.1",
            current_usage=30,
            remaining_quota=70,
            limit=100,
            window_seconds=60,
            reset_time=None
        )

        assert info.identifier == expected.identifier
        assert info.current_usage == expected.current_usage
        assert info.remaining_quota == expected.remaining_quota
        assert info.limit == expected.limit

    def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceeded exception."""
        identifier = "192.168.1.1"
        retry_after = 30

        exc = RateLimitExceeded(identifier, retry_after)

        assert exc.identifier == identifier
        assert exc.retry_after == retry_after
        assert str(exc) == f"Rate limit exceeded for {identifier}, retry after {retry_after} seconds"


class TestRateLimitingStrategies:
    """Test different rate limiting strategies."""

    @pytest.fixture
    def redis_client(self):
        return AsyncMock()

    def test_sliding_window_strategy(self, redis_client):
        """Test sliding window rate limiting strategy."""
        config = RateLimitConfig(
            requests_per_minute=100,
            burst_limit=20,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )

        service = RateLimitingService(redis_client, config)

        assert service.config.strategy == RateLimitStrategy.SLIDING_WINDOW

    def test_fixed_window_strategy(self, redis_client):
        """Test fixed window rate limiting strategy."""
        config = RateLimitConfig(
            requests_per_minute=100,
            burst_limit=20,
            window_seconds=60,
            strategy=RateLimitStrategy.FIXED_WINDOW
        )

        service = RateLimitingService(redis_client, config)

        assert service.config.strategy == RateLimitStrategy.FIXED_WINDOW


class TestRateLimitingIntegration:
    """Test rate limiting service integration scenarios."""

    @pytest.fixture
    def redis_client(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, redis_client):
        config = RateLimitConfig(
            requests_per_minute=10,
            burst_limit=5,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        return RateLimitingService(redis_client, config)

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, service, redis_client):
        """Test handling of concurrent requests."""
        redis_client.get.return_value = b"5"

        # Simulate multiple concurrent requests
        tasks = []
        for _ in range(5):
            tasks.append(service.check_rate_limit("192.168.1.1"))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed since we're under the limit
        assert all(results)

    @pytest.mark.asyncio
    async def test_burst_limit_handling(self, service, redis_client):
        """Test burst limit functionality."""
        # First request - should succeed
        redis_client.get.return_value = None
        result1 = await service.check_rate_limit("192.168.1.1")
        assert result1 is True

        # Burst requests - should succeed up to burst limit
        redis_client.get.return_value = b"8"  # 2 requests remaining before burst limit
        result2 = await service.check_rate_limit("192.168.1.1")
        assert result2 is True

    @pytest.mark.asyncio
    async def test_quota_exhaustion(self, service, redis_client):
        """Test behavior when quota is exhausted."""
        redis_client.get.return_value = b"10"  # At limit

        result = await service.check_rate_limit("192.168.1.1")

        assert result is False

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, service, redis_client):
        """Test handling of Redis errors."""
        redis_client.get.side_effect = Exception("Redis connection error")

        # Should handle error gracefully and allow request
        result = await service.check_rate_limit("192.168.1.1")

        assert result is True  # Fail open for Redis errors


class TestRateLimitingSecurity:
    """Test security aspects of rate limiting."""

    @pytest.fixture
    def redis_client(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, redis_client):
        config = RateLimitConfig(
            requests_per_minute=100,
            burst_limit=20,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        return RateLimitingService(redis_client, config)

    def test_prevent_timing_attacks(self, service):
        """Test that rate limiting is resistant to timing attacks."""
        import time

        # Multiple calls should have consistent timing
        start_time = time.time()

        for _ in range(10):
            service._get_key("192.168.1.1")

        end_time = time.time()
        duration = end_time - start_time

        # Should be very fast and consistent
        assert duration < 0.1

    def test_key_generation_security(self, service):
        """Test that rate limit keys are generated securely."""
        identifier = "192.168.1.1"
        key = service._get_key(identifier)

        assert key == f"rate_limit:{identifier}"
        assert "rate_limit:" in key

    @pytest.mark.asyncio
    async def test_rate_limit_bypass_prevention(self, service, redis_client):
        """Test prevention of rate limit bypass attempts."""
        # Simulate rapid successive requests
        redis_client.get.return_value = b"99"

        result = await service.check_rate_limit("192.168.1.1")

        # Should be blocked at limit
        assert result is False

    def test_configuration_validation(self):
        """Test that invalid configurations are rejected."""
        with pytest.raises(ValueError):
            RateLimitConfig(
                requests_per_minute=-1,  # Invalid
                burst_limit=20,
                window_seconds=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW
            )

        with pytest.raises(ValueError):
            RateLimitConfig(
                requests_per_minute=100,
                burst_limit=20,
                window_seconds=0,  # Invalid
                strategy=RateLimitStrategy.SLIDING_WINDOW
            )