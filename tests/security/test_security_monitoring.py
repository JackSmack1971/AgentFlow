"""Security tests for Security Monitoring service.

Tests cover:
- Security event collection and processing
- Anomaly detection and alerting
- Security metrics and reporting
- Integration with audit logging
- Threat intelligence and pattern recognition
- Real-time security monitoring
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from apps.api.app.services.security_monitoring import (
    SecurityMonitoringService,
    SecurityEvent,
    SecurityAlert,
    SecurityMetrics,
    AlertSeverity,
    EventType,
    MonitoringConfig
)


class TestSecurityMonitoringService:
    """Test the Security Monitoring service."""

    @pytest.fixture
    def redis_client(self):
        """Mock Redis client for testing."""
        return AsyncMock()

    @pytest.fixture
    def monitoring_config(self):
        """Default monitoring configuration for testing."""
        return MonitoringConfig(
            alert_thresholds={
                EventType.SUSPICIOUS_LOGIN: 3,
                EventType.RATE_LIMIT_EXCEEDED: 5,
                EventType.UNAUTHORIZED_ACCESS: 1
            },
            metrics_retention_days=30,
            enable_real_time_alerts=True,
            anomaly_detection_enabled=True
        )

    @pytest.fixture
    def security_monitoring_service(self, redis_client, monitoring_config):
        """Security monitoring service instance for testing."""
        return SecurityMonitoringService(redis_client, monitoring_config)

    def test_security_monitoring_service_initialization(self, redis_client, monitoring_config):
        """Test service initialization with configuration."""
        service = SecurityMonitoringService(redis_client, monitoring_config)

        assert service.redis == redis_client
        assert service.config == monitoring_config
        assert service._alert_handlers == []

    def test_security_event_creation(self):
        """Test security event creation."""
        event = SecurityEvent(
            event_type=EventType.SUSPICIOUS_LOGIN,
            identifier="192.168.1.1",
            details={"attempts": 3, "user_agent": "suspicious-bot"},
            severity=AlertSeverity.MEDIUM,
            timestamp=datetime.utcnow()
        )

        assert event.event_type == EventType.SUSPICIOUS_LOGIN
        assert event.identifier == "192.168.1.1"
        assert event.severity == AlertSeverity.MEDIUM
        assert "attempts" in event.details

    def test_security_alert_creation(self):
        """Test security alert creation."""
        alert = SecurityAlert(
            alert_id="alert-123",
            title="Suspicious Login Attempts",
            description="Multiple failed login attempts detected",
            severity=AlertSeverity.HIGH,
            events=["event-1", "event-2"],
            recommendations=["Block IP temporarily", "Notify security team"],
            created_at=datetime.utcnow()
        )

        assert alert.alert_id == "alert-123"
        assert alert.severity == AlertSeverity.HIGH
        assert len(alert.events) == 2

    @pytest.mark.asyncio
    async def test_record_security_event(self, security_monitoring_service, redis_client):
        """Test recording a security event."""
        event = SecurityEvent(
            event_type=EventType.SUSPICIOUS_LOGIN,
            identifier="192.168.1.1",
            details={"attempts": 3},
            severity=AlertSeverity.LOW
        )

        result = await security_monitoring_service.record_security_event(event)

        assert result is True
        # Should store event in Redis
        redis_client.setex.assert_called()

    @pytest.mark.asyncio
    async def test_get_security_events(self, security_monitoring_service, redis_client):
        """Test retrieving security events."""
        # Mock Redis response
        mock_events = [
            '{"event_type": "SUSPICIOUS_LOGIN", "identifier": "192.168.1.1", "details": {}}',
            '{"event_type": "RATE_LIMIT_EXCEEDED", "identifier": "192.168.1.2", "details": {}}'
        ]
        redis_client.keys.return_value = ["event:1", "event:2"]
        redis_client.mget.return_value = mock_events

        events = await security_monitoring_service.get_security_events(hours=24)

        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_get_security_metrics(self, security_monitoring_service, redis_client):
        """Test retrieving security metrics."""
        # Mock Redis responses
        redis_client.get.side_effect = [
            b"10",  # Total events
            b"5",   # Alerts triggered
            b"2",   # Active alerts
            b"3"    # Critical alerts
        ]

        metrics = await security_monitoring_service.get_security_metrics()

        assert metrics.total_events == 10
        assert metrics.alerts_triggered == 5
        assert metrics.active_alerts == 2
        assert metrics.critical_alerts == 3

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, security_monitoring_service, redis_client):
        """Test anomaly detection."""
        # Mock normal baseline data
        redis_client.get.return_value = b"5"  # Normal event count

        # Test with higher than normal activity
        is_anomaly = await security_monitoring_service._detect_anomaly(
            EventType.SUSPICIOUS_LOGIN,
            "192.168.1.1",
            current_count=15
        )

        assert is_anomaly is True

    @pytest.mark.asyncio
    async def test_trigger_alert(self, security_monitoring_service, redis_client):
        """Test triggering security alerts."""
        events = [
            SecurityEvent(
                event_type=EventType.UNAUTHORIZED_ACCESS,
                identifier="192.168.1.1",
                details={"path": "/admin"},
                severity=AlertSeverity.HIGH
            )
        ]

        alert = await security_monitoring_service._trigger_alert(
            "Unauthorized Access Alert",
            "Unauthorized access attempt detected",
            events,
            AlertSeverity.HIGH
        )

        assert alert.title == "Unauthorized Access Alert"
        assert alert.severity == AlertSeverity.HIGH
        assert len(alert.events) == 1

    def test_add_alert_handler(self, security_monitoring_service):
        """Test adding alert handlers."""
        handler = MagicMock()

        security_monitoring_service.add_alert_handler(handler)

        assert handler in security_monitoring_service._alert_handlers

    @pytest.mark.asyncio
    async def test_process_alert_handlers(self, security_monitoring_service):
        """Test processing alert handlers."""
        handler = AsyncMock()
        security_monitoring_service.add_alert_handler(handler)

        alert = SecurityAlert(
            alert_id="alert-123",
            title="Test Alert",
            description="Test Description",
            severity=AlertSeverity.MEDIUM,
            events=[],
            recommendations=[]
        )

        await security_monitoring_service._process_alert_handlers(alert)

        handler.assert_called_once_with(alert)

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, security_monitoring_service, redis_client):
        """Test cleanup of old security events."""
        redis_client.keys.return_value = ["event:old1", "event:old2"]

        cleaned_count = await security_monitoring_service.cleanup_old_events(days=7)

        # Should delete old keys
        redis_client.delete.assert_called_once_with("event:old1", "event:old2")
        assert cleaned_count == 2


class TestSecurityEventTypes:
    """Test different security event types."""

    def test_event_type_enum(self):
        """Test security event type enumeration."""
        assert EventType.SUSPICIOUS_LOGIN.value == "suspicious_login"
        assert EventType.RATE_LIMIT_EXCEEDED.value == "rate_limit_exceeded"
        assert EventType.UNAUTHORIZED_ACCESS.value == "unauthorized_access"
        assert EventType.SQL_INJECTION.value == "sql_injection"
        assert EventType.XSS_ATTEMPT.value == "xss_attempt"

    def test_alert_severity_enum(self):
        """Test alert severity enumeration."""
        assert AlertSeverity.LOW.value == "low"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestSecurityMetrics:
    """Test security metrics functionality."""

    def test_security_metrics_creation(self):
        """Test security metrics creation."""
        metrics = SecurityMetrics(
            total_events=100,
            alerts_triggered=10,
            active_alerts=5,
            critical_alerts=2,
            events_by_type={"suspicious_login": 50, "rate_limit_exceeded": 30},
            top_attack_sources={"192.168.1.1": 25, "192.168.1.2": 15},
            timestamp=datetime.utcnow()
        )

        assert metrics.total_events == 100
        assert metrics.alerts_triggered == 10
        assert metrics.active_alerts == 5
        assert metrics.critical_alerts == 2
        assert len(metrics.events_by_type) == 2

    def test_security_metrics_calculations(self):
        """Test security metrics calculations."""
        metrics = SecurityMetrics(
            total_events=100,
            alerts_triggered=10,
            active_alerts=5,
            critical_alerts=2,
            events_by_type={"suspicious_login": 60, "rate_limit_exceeded": 40},
            top_attack_sources={"192.168.1.1": 30},
            timestamp=datetime.utcnow()
        )

        # Test alert ratio calculation
        alert_ratio = metrics.alerts_triggered / max(metrics.total_events, 1)
        assert alert_ratio == 0.1

        # Test critical alert ratio
        critical_ratio = metrics.critical_alerts / max(metrics.alerts_triggered, 1)
        assert critical_ratio == 0.2


class TestMonitoringConfiguration:
    """Test monitoring configuration."""

    def test_monitoring_config_creation(self):
        """Test monitoring configuration creation."""
        config = MonitoringConfig(
            alert_thresholds={
                EventType.SUSPICIOUS_LOGIN: 5,
                EventType.RATE_LIMIT_EXCEEDED: 10
            },
            metrics_retention_days=60,
            enable_real_time_alerts=True,
            anomaly_detection_enabled=True
        )

        assert config.alert_thresholds[EventType.SUSPICIOUS_LOGIN] == 5
        assert config.metrics_retention_days == 60
        assert config.enable_real_time_alerts is True
        assert config.anomaly_detection_enabled is True

    def test_monitoring_config_defaults(self):
        """Test monitoring configuration defaults."""
        config = MonitoringConfig()

        assert isinstance(config.alert_thresholds, dict)
        assert config.metrics_retention_days == 30
        assert config.enable_real_time_alerts is True
        assert config.anomaly_detection_enabled is False


class TestSecurityIntegration:
    """Test security monitoring integration scenarios."""

    @pytest.fixture
    def redis_client(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, redis_client):
        config = MonitoringConfig(
            alert_thresholds={EventType.SUSPICIOUS_LOGIN: 3},
            enable_real_time_alerts=True
        )
        return SecurityMonitoringService(redis_client, config)

    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, service, redis_client):
        """Test processing multiple security events concurrently."""
        events = [
            SecurityEvent(
                event_type=EventType.SUSPICIOUS_LOGIN,
                identifier=f"192.168.1.{i}",
                details={"attempts": 3},
                severity=AlertSeverity.MEDIUM
            )
            for i in range(5)
        ]

        # Process events concurrently
        tasks = [service.record_security_event(event) for event in events]
        results = await asyncio.gather(*tasks)

        assert all(results)

    @pytest.mark.asyncio
    async def test_high_frequency_event_handling(self, service, redis_client):
        """Test handling of high-frequency security events."""
        # Simulate high-frequency suspicious activity
        identifier = "192.168.1.100"

        # Record multiple events rapidly
        for i in range(10):
            event = SecurityEvent(
                event_type=EventType.SUSPICIOUS_LOGIN,
                identifier=identifier,
                details={"attempts": i + 1},
                severity=AlertSeverity.HIGH
            )
            await service.record_security_event(event)

        # Should have triggered alerts due to threshold being exceeded
        redis_client.setex.assert_called()

    @pytest.mark.asyncio
    async def test_redis_error_resilience(self, service, redis_client):
        """Test resilience to Redis errors."""
        redis_client.setex.side_effect = Exception("Redis connection error")

        event = SecurityEvent(
            event_type=EventType.SUSPICIOUS_LOGIN,
            identifier="192.168.1.1",
            details={},
            severity=AlertSeverity.LOW
        )

        # Should handle error gracefully
        result = await service.record_security_event(event)

        # Service should continue to function despite Redis errors
        assert result is False  # But doesn't crash

    def test_event_serialization(self, service):
        """Test security event serialization."""
        event = SecurityEvent(
            event_type=EventType.SUSPICIOUS_LOGIN,
            identifier="192.168.1.1",
            details={"attempts": 3, "user_agent": "bot"},
            severity=AlertSeverity.MEDIUM,
            timestamp=datetime.utcnow()
        )

        # Should be able to serialize to dict
        event_dict = event.model_dump()

        assert event_dict["event_type"] == "suspicious_login"
        assert event_dict["identifier"] == "192.168.1.1"
        assert event_dict["details"]["attempts"] == 3