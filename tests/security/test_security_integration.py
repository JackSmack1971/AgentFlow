"""Integration tests for security components.

Tests cover:
- Integration between rate limiting and security monitoring
- End-to-end security workflows
- Security component interaction
- Comprehensive security validation
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from apps.api.app.services.rate_limiting_service import (
    RateLimitingService,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitExceeded
)
from apps.api.app.services.security_monitoring import (
    SecurityMonitoringService,
    SecurityEvent,
    SecurityAlert,
    AlertSeverity,
    EventType,
    MonitoringConfig
)
from apps.api.app.utils.encryption import EncryptionManager


class TestSecurityComponentsIntegration:
    """Test integration between security components."""

    @pytest.fixture
    def redis_client(self):
        """Mock Redis client for testing."""
        return AsyncMock()

    @pytest.fixture
    def rate_limiting_service(self, redis_client):
        """Rate limiting service for testing."""
        config = RateLimitConfig(
            requests_per_minute=10,
            burst_limit=5,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        return RateLimitingService(redis_client, config)

    @pytest.fixture
    def security_monitoring_service(self, redis_client):
        """Security monitoring service for testing."""
        config = MonitoringConfig(
            alert_thresholds={EventType.RATE_LIMIT_EXCEEDED: 3},
            enable_real_time_alerts=True
        )
        return SecurityMonitoringService(redis_client, config)

    @pytest.fixture
    def encryption_manager(self):
        """Encryption manager for testing."""
        return EncryptionManager("test_key_32_chars_12345678901234567890")

    @pytest.mark.asyncio
    async def test_rate_limiting_triggers_security_monitoring(
        self,
        rate_limiting_service,
        security_monitoring_service,
        redis_client
    ):
        """Test that rate limiting violations trigger security monitoring."""
        # Mock Redis responses for rate limiting
        redis_client.get.return_value = None  # First call - no existing count
        redis_client.incr.return_value = 11  # Exceeds limit

        # Mock security event recording
        security_monitoring_service.record_security_event = AsyncMock(return_value=True)

        # Try to make requests that will exceed rate limit
        for i in range(12):  # Exceed the limit of 10
            try:
                await rate_limiting_service.check_rate_limit("192.168.1.1")
            except RateLimitExceeded:
                # Record security event when rate limit is exceeded
                event = SecurityEvent(
                    event_type=EventType.RATE_LIMIT_EXCEEDED,
                    identifier="192.168.1.1",
                    details={"attempt": i + 1, "limit": 10},
                    severity=AlertSeverity.MEDIUM
                )
                await security_monitoring_service.record_security_event(event)
                break

        # Verify security event was recorded
        security_monitoring_service.record_security_event.assert_called()

    @pytest.mark.asyncio
    async def test_encryption_integration_with_security_events(
        self,
        security_monitoring_service,
        encryption_manager
    ):
        """Test encryption integration with security event data."""
        # Create sensitive event data
        sensitive_data = {
            "user_id": "12345",
            "ip_address": "192.168.1.100",
            "session_token": "secret_session_token_123",
            "attempted_action": "admin_login"
        }

        # Encrypt sensitive data
        encrypted_data = encryption_manager.encrypt(str(sensitive_data))

        # Create security event with encrypted data
        event = SecurityEvent(
            event_type=EventType.SUSPICIOUS_LOGIN,
            identifier="192.168.1.100",
            details={"encrypted_info": encrypted_data},
            severity=AlertSeverity.HIGH
        )

        # Verify event can be created with encrypted data
        assert event.details["encrypted_info"] == encrypted_data

        # Verify encrypted data is different from original
        assert event.details["encrypted_info"] != str(sensitive_data)

        # Verify we can decrypt the data back
        decrypted_data = encryption_manager.decrypt(encrypted_data)
        assert decrypted_data == str(sensitive_data)

    @pytest.mark.asyncio
    async def test_comprehensive_security_workflow(
        self,
        rate_limiting_service,
        security_monitoring_service,
        encryption_manager,
        redis_client
    ):
        """Test comprehensive security workflow with all components."""
        # Step 1: Normal request - should succeed
        redis_client.get.return_value = None
        redis_client.incr.return_value = 1

        result = await rate_limiting_service.check_rate_limit("192.168.1.1")
        assert result is True

        # Step 2: Multiple rapid requests to trigger rate limiting
        redis_client.get.return_value = b"9"  # Near limit
        redis_client.incr.return_value = 10

        for i in range(5):
            try:
                await rate_limiting_service.check_rate_limit("192.168.1.1")
            except RateLimitExceeded:
                # Step 3: Record security event
                event = SecurityEvent(
                    event_type=EventType.RATE_LIMIT_EXCEEDED,
                    identifier="192.168.1.1",
                    details={"violation_count": i + 1},
                    severity=AlertSeverity.MEDIUM
                )

                # Step 4: Encrypt sensitive event data
                sensitive_info = {"ip": "192.168.1.1", "violation_time": datetime.utcnow().isoformat()}
                encrypted_info = encryption_manager.encrypt(str(sensitive_info))
                event.details["encrypted_sensitive_info"] = encrypted_info

                await security_monitoring_service.record_security_event(event)
                break

        # Step 5: Verify security monitoring captured the event
        events = await security_monitoring_service.get_security_events(hours=1)
        rate_limit_events = [e for e in events if e.event_type == EventType.RATE_LIMIT_EXCEEDED]

        assert len(rate_limit_events) > 0

        # Step 6: Verify encrypted data can be decrypted
        for event in rate_limit_events:
            if "encrypted_sensitive_info" in event.details:
                encrypted_info = event.details["encrypted_sensitive_info"]
                decrypted_info = encryption_manager.decrypt(encrypted_info)
                assert "192.168.1.1" in decrypted_info

    @pytest.mark.asyncio
    async def test_security_metrics_aggregation(
        self,
        security_monitoring_service,
        redis_client
    ):
        """Test security metrics aggregation across components."""
        # Mock Redis metrics data
        redis_client.get.side_effect = [
            b"50",  # total_events
            b"5",   # alerts_triggered
            b"3",   # active_alerts
            b"1"    # critical_alerts
        ]
        redis_client.keys.return_value = ["security:events:type:suspicious_login"]
        redis_client.mget.return_value = [b"25"]

        # Get security metrics
        metrics = await security_monitoring_service.get_security_metrics()

        assert metrics.total_events == 50
        assert metrics.alerts_triggered == 5
        assert metrics.active_alerts == 3
        assert metrics.critical_alerts == 1

    @pytest.mark.asyncio
    async def test_concurrent_security_operations(
        self,
        rate_limiting_service,
        security_monitoring_service,
        redis_client
    ):
        """Test concurrent security operations."""
        # Mock Redis for concurrent operations
        redis_client.get.return_value = None
        redis_client.incr.return_value = 1

        async def security_operation(identifier: str):
            """Simulate a security operation."""
            # Check rate limit
            result = await rate_limiting_service.check_rate_limit(identifier)

            # Record security event
            if result:
                event = SecurityEvent(
                    event_type=EventType.SUSPICIOUS_LOGIN,
                    identifier=identifier,
                    details={"operation": "test"},
                    severity=AlertSeverity.LOW
                )
                await security_monitoring_service.record_security_event(event)

            return result

        # Run concurrent operations
        identifiers = [f"192.168.1.{i}" for i in range(10)]
        tasks = [security_operation(identifier) for identifier in identifiers]
        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(results)

    @pytest.mark.asyncio
    async def test_security_error_handling_and_resilience(
        self,
        rate_limiting_service,
        security_monitoring_service,
        redis_client
    ):
        """Test error handling and resilience of security components."""
        # Simulate Redis failure
        redis_client.get.side_effect = Exception("Redis connection error")

        # Rate limiting should fail open
        result = await rate_limiting_service.check_rate_limit("192.168.1.1")
        assert result is True  # Should allow request despite Redis error

        # Security monitoring should handle errors gracefully
        event = SecurityEvent(
            event_type=EventType.SUSPICIOUS_LOGIN,
            identifier="192.168.1.1",
            details={"error_test": True},
            severity=AlertSeverity.LOW
        )

        result = await security_monitoring_service.record_security_event(event)
        # Should return False but not crash
        assert result is False

    def test_encryption_security_boundaries(self, encryption_manager):
        """Test encryption component security boundaries."""
        # Test with various data sizes
        test_cases = [
            "small_data",
            "A" * 1000,  # 1KB
            "A" * 1000000,  # 1MB
        ]

        for test_data in test_cases:
            # Encrypt
            encrypted = encryption_manager.encrypt(test_data)
            assert encrypted != test_data
            assert len(encrypted) > 0

            # Decrypt
            decrypted = encryption_manager.decrypt(encrypted)
            assert decrypted == test_data

    @pytest.mark.asyncio
    async def test_security_component_lifecycle(
        self,
        rate_limiting_service,
        security_monitoring_service
    ):
        """Test complete lifecycle of security components."""
        identifier = "192.168.1.100"

        # 1. Check rate limit quota
        remaining = await rate_limiting_service.get_remaining_quota(identifier)
        assert remaining == 100  # Full quota initially

        # 2. Get security metrics
        metrics = await security_monitoring_service.get_security_metrics()
        initial_events = metrics.total_events

        # 3. Record security event
        event = SecurityEvent(
            event_type=EventType.SUSPICIOUS_LOGIN,
            identifier=identifier,
            details={"lifecycle_test": True},
            severity=AlertSeverity.LOW
        )
        await security_monitoring_service.record_security_event(event)

        # 4. Verify event was recorded
        updated_metrics = await security_monitoring_service.get_security_metrics()
        assert updated_metrics.total_events >= initial_events

        # 5. Get quota info
        quota_info = await rate_limiting_service.get_quota_info(identifier)
        assert quota_info.limit == 100
        assert quota_info.remaining_quota == 100  # No usage yet

    @pytest.mark.asyncio
    async def test_security_alert_integration(self, security_monitoring_service, redis_client):
        """Test security alert integration and handling."""
        # Mock alert handler
        alert_handler = AsyncMock()
        security_monitoring_service.add_alert_handler(alert_handler)

        # Create multiple events to trigger alert
        for i in range(5):  # Exceed threshold of 3
            event = SecurityEvent(
                event_type=EventType.SUSPICIOUS_LOGIN,
                identifier="192.168.1.1",
                details={"attempt": i + 1},
                severity=AlertSeverity.HIGH
            )
            await security_monitoring_service.record_security_event(event)

        # Verify alert handler was called
        alert_handler.assert_called()

        # Verify alert was created
        alert = alert_handler.call_args[0][0]
        assert alert.severity == AlertSeverity.HIGH
        assert len(alert.events) > 0


class TestSecurityCompliance:
    """Test security compliance and standards."""

    @pytest.fixture
    def encryption_manager(self):
        """Encryption manager for compliance testing."""
        return EncryptionManager("test_key_32_chars_12345678901234567890")

    def test_encryption_compliance(self, encryption_manager):
        """Test encryption compliance with security standards."""
        # Test key strength
        test_data = "Compliance test data"

        # Encrypt multiple times - should produce different ciphertexts
        encrypted_results = set()
        for _ in range(10):
            encrypted = encryption_manager.encrypt(test_data)
            encrypted_results.add(encrypted)

        # Should have multiple different ciphertexts due to IV
        assert len(encrypted_results) > 1

        # All should decrypt to original
        for encrypted in encrypted_results:
            decrypted = encryption_manager.decrypt(encrypted)
            assert decrypted == test_data

    def test_rate_limiting_compliance(self):
        """Test rate limiting compliance with security best practices."""
        config = RateLimitConfig(
            requests_per_minute=100,
            burst_limit=20,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )

        # Verify reasonable limits
        assert config.requests_per_minute > 0
        assert config.burst_limit >= 0
        assert config.window_seconds > 0

        # Burst should be reasonable compared to main limit
        assert config.burst_limit <= config.requests_per_minute

    def test_security_monitoring_compliance(self):
        """Test security monitoring compliance."""
        config = MonitoringConfig(
            alert_thresholds={
                EventType.SUSPICIOUS_LOGIN: 3,
                EventType.RATE_LIMIT_EXCEEDED: 5
            },
            metrics_retention_days=30,
            enable_real_time_alerts=True
        )

        # Verify reasonable thresholds
        for threshold in config.alert_thresholds.values():
            assert threshold > 0

        # Verify reasonable retention period
        assert 7 <= config.metrics_retention_days <= 365


class TestSecurityPerformance:
    """Test security component performance."""

    @pytest.fixture
    def redis_client(self):
        """Mock Redis client for performance testing."""
        return AsyncMock()

    @pytest.fixture
    def rate_limiting_service(self, redis_client):
        """Rate limiting service for performance testing."""
        config = RateLimitConfig(
            requests_per_minute=1000,  # High limit for performance
            burst_limit=100,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        return RateLimitingService(redis_client, config)

    def test_rate_limiting_performance(self, rate_limiting_service, redis_client):
        """Test rate limiting performance under load."""
        import time

        redis_client.get.return_value = None
        redis_client.incr.return_value = 1

        # Test many rapid calls
        start_time = time.time()

        for _ in range(100):
            # Should complete quickly
            result = asyncio.run(rate_limiting_service.check_rate_limit("192.168.1.1"))
            assert result is True

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (less than 1 second)
        assert duration < 1.0

    def test_encryption_performance(self, encryption_manager):
        """Test encryption performance."""
        import time

        test_data = "A" * 1000  # 1KB data

        start_time = time.time()

        for _ in range(100):
            encrypted = encryption_manager.encrypt(test_data)
            decrypted = encryption_manager.decrypt(encrypted)
            assert decrypted == test_data

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time
        assert duration < 2.0

    @pytest.mark.asyncio
    async def test_concurrent_security_operations_performance(
        self,
        rate_limiting_service,
        redis_client
    ):
        """Test performance of concurrent security operations."""
        import time

        redis_client.get.return_value = None
        redis_client.incr.return_value = 1

        async def quick_check():
            return await rate_limiting_service.check_rate_limit("192.168.1.1")

        start_time = time.time()

        # Run many concurrent operations
        tasks = [quick_check() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # All should succeed
        assert all(results)

        # Should complete quickly
        assert duration < 1.0