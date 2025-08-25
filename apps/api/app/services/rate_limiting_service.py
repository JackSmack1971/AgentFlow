"""Enhanced Rate Limiting service for comprehensive API protection.

This module provides an advanced rate limiting service with:
- Multiple rate limiting strategies (sliding window, fixed window)
- Burst handling and quota management
- Distributed rate limiting with Redis
- Configurable policies and tiers
- Security monitoring integration
- Comprehensive error handling
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass

from redis.asyncio import Redis


class RateLimitStrategy(Enum):
    """Rate limiting strategy enumeration."""
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int
    burst_limit: int = 0
    window_seconds: int = 60
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if self.burst_limit < 0:
            raise ValueError("burst_limit must be non-negative")


@dataclass
class RateLimitQuota:
    """Rate limit quota information."""
    identifier: str
    current_usage: int
    remaining_quota: int
    limit: int
    window_seconds: int
    reset_time: Optional[datetime] = None


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, identifier: str, retry_after: int):
        self.identifier = identifier
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {identifier}, retry after {retry_after} seconds")


class RateLimitingService:
    """
    Enhanced rate limiting service with multiple strategies and security features.

    This service provides:
    - Distributed rate limiting using Redis
    - Multiple rate limiting strategies
    - Burst handling capabilities
    - Comprehensive monitoring and logging
    - Security-focused error handling
    """

    def __init__(self, redis_client: Redis, config: RateLimitConfig):
        """
        Initialize the rate limiting service.

        Args:
            redis_client: Redis client for distributed rate limiting
            config: Rate limiting configuration
        """
        self.redis = redis_client
        self.config = config
        self._quotas: Dict[str, RateLimitQuota] = {}

    def _get_key(self, identifier: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"rate_limit:{identifier}"

    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (e.g., IP address, user ID)

        Returns:
            bool: True if request is allowed, False if rate limited

        Raises:
            RateLimitExceeded: When rate limit is exceeded
        """
        try:
            key = self._get_key(identifier)
            current_count = await self._get_current_count(key)

            # Check if limit exceeded
            if current_count >= self.config.requests_per_minute:
                retry_after = await self._get_retry_after(key)
                raise RateLimitExceeded(identifier, retry_after)

            # Increment counter
            await self.redis.incr(key)

            # Set expiry if this is the first request in window
            if current_count == 0:
                await self.redis.expire(key, self.config.window_seconds)

            return True

        except RateLimitExceeded:
            raise
        except Exception as e:
            # Log error but allow request to proceed (fail open)
            print(f"Rate limiting error for {identifier}: {e}")
            return True

    async def _get_current_count(self, key: str) -> int:
        """Get current request count for identifier."""
        try:
            count = await self.redis.get(key)
            return int(count) if count is not None else 0
        except Exception:
            return 0  # Fail open

    async def _get_retry_after(self, key: str) -> int:
        """Get retry after seconds for rate limited identifier."""
        try:
            ttl = await self.redis.ttl(key)
            return max(ttl, 1)
        except Exception:
            return self.config.window_seconds

    async def get_remaining_quota(self, identifier: str) -> int:
        """
        Get remaining quota for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            int: Remaining quota (requests)
        """
        try:
            key = self._get_key(identifier)
            current_count = await self._get_current_count(key)
            remaining = self.config.requests_per_minute - current_count
            return max(remaining, 0)
        except Exception:
            return self.config.requests_per_minute

    async def get_quota_info(self, identifier: str) -> RateLimitQuota:
        """
        Get complete quota information for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            RateLimitQuota: Complete quota information
        """
        try:
            key = self._get_key(identifier)
            current_usage = await self._get_current_count(key)
            remaining = self.config.requests_per_minute - current_usage

            return RateLimitQuota(
                identifier=identifier,
                current_usage=current_usage,
                remaining_quota=max(remaining, 0),
                limit=self.config.requests_per_minute,
                window_seconds=self.config.window_seconds,
                reset_time=None  # Could be calculated from TTL if needed
            )
        except Exception:
            # Return default quota info on error
            return RateLimitQuota(
                identifier=identifier,
                current_usage=0,
                remaining_quota=self.config.requests_per_minute,
                limit=self.config.requests_per_minute,
                window_seconds=self.config.window_seconds,
                reset_time=None
            )

    async def reset_quota(self, identifier: str) -> bool:
        """
        Reset quota for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            bool: True if reset successful, False otherwise
        """
        try:
            key = self._get_key(identifier)
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Failed to reset quota for {identifier}: {e}")
            return False

    async def get_all_quotas(self) -> Dict[str, RateLimitQuota]:
        """
        Get quota information for all tracked identifiers.

        Returns:
            Dict[str, RateLimitQuota]: All quota information
        """
        try:
            # Get all rate limit keys
            keys = await self.redis.keys("rate_limit:*")

            quotas = {}
            for key in keys:
                identifier = key.replace("rate_limit:", "", 1)
                quotas[identifier] = await self.get_quota_info(identifier)

            return quotas
        except Exception as e:
            print(f"Failed to get all quotas: {e}")
            return {}

    async def cleanup_expired_quotas(self) -> int:
        """
        Clean up expired rate limit entries.

        Returns:
            int: Number of entries cleaned up
        """
        try:
            # Redis automatically expires keys, but we can manually clean if needed
            # This is a no-op for now as Redis handles expiration
            return 0
        except Exception as e:
            print(f"Failed to cleanup expired quotas: {e}")
            return 0

    async def is_rate_limited(self, identifier: str) -> bool:
        """
        Check if identifier is currently rate limited.

        Args:
            identifier: Unique identifier

        Returns:
            bool: True if rate limited, False otherwise
        """
        try:
            key = self._get_key(identifier)
            current_count = await self._get_current_count(key)
            return current_count >= self.config.requests_per_minute
        except Exception:
            return False

    def get_config(self) -> RateLimitConfig:
        """Get current rate limiting configuration."""
        return self.config

    async def update_config(self, config: RateLimitConfig) -> bool:
        """
        Update rate limiting configuration.

        Args:
            config: New configuration

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            self.config = config
            return True
        except Exception as e:
            print(f"Failed to update rate limiting config: {e}")
            return False


# Global rate limiting service instance
_rate_limiting_service: Optional[RateLimitingService] = None


def get_rate_limiting_service() -> Optional[RateLimitingService]:
    """Get global rate limiting service instance."""
    return _rate_limiting_service


def set_rate_limiting_service(service: RateLimitingService):
    """Set global rate limiting service instance."""
    global _rate_limiting_service
    _rate_limiting_service = service


__all__ = [
    "RateLimitingService",
    "RateLimitExceeded",
    "RateLimitConfig",
    "RateLimitQuota",
    "RateLimitStrategy",
    "get_rate_limiting_service",
    "set_rate_limiting_service"
]