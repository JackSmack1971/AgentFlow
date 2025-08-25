"""Security Monitoring service for comprehensive threat detection and alerting.

This module provides advanced security monitoring with:
- Real-time security event collection and analysis
- Anomaly detection and threat intelligence
- Automated alerting and incident response
- Security metrics and reporting
- Integration with existing security components
- Configurable monitoring policies
"""

from __future__ import annotations

import asyncio
import json
import secrets
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, asdict

from redis.asyncio import Redis


class EventType(Enum):
    """Security event types for monitoring."""
    SUSPICIOUS_LOGIN = "suspicious_login"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    BRUTE_FORCE = "brute_force"
    SESSION_HIJACKING = "session_hijacking"
    DATA_BREACH = "data_breach"
    MALWARE_DETECTED = "malware_detected"
    DOS_ATTACK = "dos_attack"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_type: EventType
    identifier: str  # IP address, user ID, etc.
    details: Dict[str, Any]
    severity: AlertSeverity = AlertSeverity.MEDIUM
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def model_dump(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "identifier": self.identifier,
            "details": self.details,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class SecurityAlert:
    """Security alert data structure."""
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    events: List[str]  # Event IDs
    recommendations: List[str]
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        """Set creation timestamp if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SecurityMetrics:
    """Security metrics data structure."""
    total_events: int = 0
    alerts_triggered: int = 0
    active_alerts: int = 0
    critical_alerts: int = 0
    events_by_type: Dict[str, int] = None
    top_attack_sources: Dict[str, int] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Initialize optional fields."""
        if self.events_by_type is None:
            self.events_by_type = {}
        if self.top_attack_sources is None:
            self.top_attack_sources = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class MonitoringConfig:
    """Configuration for security monitoring."""
    alert_thresholds: Dict[EventType, int] = None
    metrics_retention_days: int = 30
    enable_real_time_alerts: bool = True
    anomaly_detection_enabled: bool = False

    def __post_init__(self):
        """Initialize default thresholds."""
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                EventType.SUSPICIOUS_LOGIN: 3,
                EventType.RATE_LIMIT_EXCEEDED: 5,
                EventType.UNAUTHORIZED_ACCESS: 1,
                EventType.SQL_INJECTION: 1,
                EventType.XSS_ATTEMPT: 3,
                EventType.BRUTE_FORCE: 5,
                EventType.DOS_ATTACK: 10
            }


class SecurityMonitoringService:
    """
    Comprehensive security monitoring service.

    This service provides:
    - Real-time security event collection and analysis
    - Automated threat detection and alerting
    - Security metrics collection and reporting
    - Anomaly detection capabilities
    - Integration with existing security infrastructure
    """

    def __init__(self, redis_client: Redis, config: MonitoringConfig):
        """
        Initialize the security monitoring service.

        Args:
            redis_client: Redis client for distributed monitoring
            config: Monitoring configuration
        """
        self.redis = redis_client
        self.config = config
        self._alert_handlers: List[Callable[[SecurityAlert], Awaitable[None]]] = []

    async def record_security_event(self, event: SecurityEvent) -> bool:
        """
        Record a security event for monitoring and analysis.

        Args:
            event: Security event to record

        Returns:
            bool: True if recorded successfully, False otherwise
        """
        try:
            # Generate unique event ID
            event_id = f"event:{secrets.token_hex(16)}"

            # Store event in Redis
            event_data = json.dumps(event.model_dump())
            await self.redis.setex(
                f"security:event:{event_id}",
                self.config.metrics_retention_days * 24 * 3600,  # Convert days to seconds
                event_data
            )

            # Update event counters
            await self._increment_event_counter(event.event_type, event.identifier)

            # Check for alert conditions
            if self.config.enable_real_time_alerts:
                await self._check_alert_conditions(event)

            return True

        except Exception as e:
            print(f"Failed to record security event: {e}")
            return False

    async def _increment_event_counter(self, event_type: EventType, identifier: str):
        """Increment counters for event type and identifier."""
        try:
            # Increment total event counter
            await self.redis.incr("security:metrics:total_events")

            # Increment event type counter
            await self.redis.incr(f"security:events:type:{event_type.value}")

            # Increment identifier counter
            await self.redis.incr(f"security:events:identifier:{identifier}")

            # Set expiry for identifier counter (24 hours)
            await self.redis.expire(f"security:events:identifier:{identifier}", 86400)

        except Exception as e:
            print(f"Failed to increment event counter: {e}")

    async def _check_alert_conditions(self, event: SecurityEvent):
        """Check if event triggers any alerts."""
        try:
            threshold = self.config.alert_thresholds.get(event.event_type, 0)
            if threshold <= 0:
                return

            # Get current count for this event type and identifier
            current_count = await self._get_event_count(event.event_type, event.identifier)

            if current_count >= threshold:
                await self._trigger_alert_for_event(event, current_count)

        except Exception as e:
            print(f"Failed to check alert conditions: {e}")

    async def _get_event_count(self, event_type: EventType, identifier: str) -> int:
        """Get current event count for type and identifier."""
        try:
            key = f"security:events:identifier:{identifier}"
            count = await self.redis.get(key)
            return int(count) if count else 0
        except Exception:
            return 0

    async def _trigger_alert_for_event(self, event: SecurityEvent, current_count: int):
        """Trigger alert for security event."""
        try:
            alert_title = f"Security Alert: {event.event_type.value.replace('_', ' ').title()}"
            alert_description = (
                f"Threshold exceeded for {event.event_type.value}. "
                f"Current count: {current_count}"
            )

            recommendations = self._generate_recommendations(event.event_type, current_count)

            alert = await self._trigger_alert(
                alert_title,
                alert_description,
                [event],
                event.severity
            )

            # Process alert handlers
            await self._process_alert_handlers(alert)

        except Exception as e:
            print(f"Failed to trigger alert: {e}")

    def _generate_recommendations(self, event_type: EventType, count: int) -> List[str]:
        """Generate recommendations based on event type and severity."""
        recommendations = []

        if event_type == EventType.SUSPICIOUS_LOGIN:
            recommendations.extend([
                "Review login attempt patterns",
                "Consider temporary IP blocking",
                "Enable additional authentication factors"
            ])
        elif event_type == EventType.RATE_LIMIT_EXCEEDED:
            recommendations.extend([
                "Increase rate limit thresholds",
                "Implement progressive delays",
                "Monitor for DDoS patterns"
            ])
        elif event_type == EventType.UNAUTHORIZED_ACCESS:
            recommendations.extend([
                "Review access control policies",
                "Audit user permissions",
                "Implement additional authorization checks"
            ])
        elif event_type in [EventType.SQL_INJECTION, EventType.XSS_ATTEMPT]:
            recommendations.extend([
                "Review input validation",
                "Implement WAF rules",
                "Conduct security assessment"
            ])

        return recommendations

    async def _trigger_alert(
        self,
        title: str,
        description: str,
        events: List[SecurityEvent],
        severity: AlertSeverity
    ) -> SecurityAlert:
        """Create and store security alert."""
        try:
            alert_id = f"alert:{secrets.token_hex(8)}"

            alert = SecurityAlert(
                alert_id=alert_id,
                title=title,
                description=description,
                severity=severity,
                events=[f"event:{secrets.token_hex(8)}" for _ in events],
                recommendations=self._generate_recommendations(events[0].event_type, len(events))
            )

            # Store alert in Redis
            alert_data = json.dumps(asdict(alert))
            await self.redis.setex(
                f"security:alert:{alert_id}",
                7 * 24 * 3600,  # 7 days
                alert_data
            )

            # Update alert counters
            await self.redis.incr("security:metrics:alerts_triggered")
            await self.redis.incr("security:metrics:active_alerts")

            if severity == AlertSeverity.CRITICAL:
                await self.redis.incr("security:metrics:critical_alerts")

            return alert

        except Exception as e:
            print(f"Failed to create alert: {e}")
            raise

    async def get_security_events(
        self,
        hours: int = 24,
        event_type: Optional[EventType] = None,
        identifier: Optional[str] = None
    ) -> List[SecurityEvent]:
        """
        Retrieve security events with optional filtering.

        Args:
            hours: Number of hours to look back
            event_type: Filter by event type
            identifier: Filter by identifier

        Returns:
            List[SecurityEvent]: Matching security events
        """
        try:
            # Get event keys from Redis
            pattern = "security:event:*"
            event_keys = await self.redis.keys(pattern)

            events = []
            for key in event_keys:
                event_data = await self.redis.get(key)
                if event_data:
                    event_dict = json.loads(event_data)
                    event = SecurityEvent(
                        event_type=EventType(event_dict["event_type"]),
                        identifier=event_dict["identifier"],
                        details=event_dict["details"],
                        severity=AlertSeverity(event_dict["severity"]),
                        timestamp=datetime.fromisoformat(event_dict["timestamp"])
                    )

                    # Apply filters
                    if event_type and event.event_type != event_type:
                        continue
                    if identifier and event.identifier != identifier:
                        continue

                    # Check time window
                    if event.timestamp and event.timestamp > datetime.utcnow() - timedelta(hours=hours):
                        events.append(event)

            return events

        except Exception as e:
            print(f"Failed to retrieve security events: {e}")
            return []

    async def get_security_metrics(self) -> SecurityMetrics:
        """
        Get current security metrics.

        Returns:
            SecurityMetrics: Current security metrics
        """
        try:
            # Get basic metrics
            total_events = await self.redis.get("security:metrics:total_events")
            alerts_triggered = await self.redis.get("security:metrics:alerts_triggered")
            active_alerts = await self.redis.get("security:metrics:active_alerts")
            critical_alerts = await self.redis.get("security:metrics:critical_alerts")

            # Get events by type
            event_type_keys = await self.redis.keys("security:events:type:*")
            events_by_type = {}
            for key in event_type_keys:
                event_type = key.replace("security:events:type:", "")
                count = await self.redis.get(key)
                events_by_type[event_type] = int(count) if count else 0

            # Get top attack sources
            identifier_keys = await self.redis.keys("security:events:identifier:*")
            top_attack_sources = {}
            for key in identifier_keys:
                identifier = key.replace("security:events:identifier:", "")
                count = await self.redis.get(key)
                top_attack_sources[identifier] = int(count) if count else 0

            return SecurityMetrics(
                total_events=int(total_events) if total_events else 0,
                alerts_triggered=int(alerts_triggered) if alerts_triggered else 0,
                active_alerts=int(active_alerts) if active_alerts else 0,
                critical_alerts=int(critical_alerts) if critical_alerts else 0,
                events_by_type=events_by_type,
                top_attack_sources=dict(sorted(
                    top_attack_sources.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10])  # Top 10 sources
            )

        except Exception as e:
            print(f"Failed to retrieve security metrics: {e}")
            return SecurityMetrics()

    async def _detect_anomaly(
        self,
        event_type: EventType,
        identifier: str,
        current_count: int
    ) -> bool:
        """
        Detect anomalies in security event patterns.

        Args:
            event_type: Type of security event
            identifier: Event identifier
            current_count: Current event count

        Returns:
            bool: True if anomaly detected, False otherwise
        """
        if not self.config.anomaly_detection_enabled:
            return False

        try:
            # Get baseline count (simplified - could be more sophisticated)
            baseline_key = f"security:baseline:{event_type.value}:{identifier}"
            baseline = await self.redis.get(baseline_key)

            if baseline is None:
                # Set initial baseline
                await self.redis.setex(baseline_key, 86400, current_count)
                return False

            baseline_count = int(baseline)

            # Simple anomaly detection: current count > 3x baseline
            if current_count > baseline_count * 3:
                return True

            return False

        except Exception as e:
            print(f"Failed to detect anomaly: {e}")
            return False

    def add_alert_handler(self, handler: Callable[[SecurityAlert], Awaitable[None]]):
        """
        Add alert handler for processing security alerts.

        Args:
            handler: Async function to handle alerts
        """
        self._alert_handlers.append(handler)

    async def _process_alert_handlers(self, alert: SecurityAlert):
        """Process all registered alert handlers."""
        try:
            tasks = [handler(alert) for handler in self._alert_handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"Failed to process alert handlers: {e}")

    async def cleanup_old_events(self, days: int = 30) -> int:
        """
        Clean up old security events.

        Args:
            days: Remove events older than this many days

        Returns:
            int: Number of events cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            event_keys = await self.redis.keys("security:event:*")

            cleaned_count = 0
            for key in event_keys:
                event_data = await self.redis.get(key)
                if event_data:
                    event_dict = json.loads(event_data)
                    event_time = datetime.fromisoformat(event_dict["timestamp"])

                    if event_time < cutoff_time:
                        await self.redis.delete(key)
                        cleaned_count += 1

            return cleaned_count

        except Exception as e:
            print(f"Failed to cleanup old events: {e}")
            return 0

    async def resolve_alert(self, alert_id: str) -> bool:
        """
        Mark an alert as resolved.

        Args:
            alert_id: Alert ID to resolve

        Returns:
            bool: True if resolved successfully, False otherwise
        """
        try:
            alert_key = f"security:alert:{alert_id}"
            alert_data = await self.redis.get(alert_key)

            if alert_data:
                alert_dict = json.loads(alert_data)
                alert_dict["resolved_at"] = datetime.utcnow().isoformat()

                # Update alert data
                await self.redis.setex(
                    alert_key,
                    7 * 24 * 3600,  # 7 days
                    json.dumps(alert_dict)
                )

                # Decrement active alerts counter
                await self.redis.decr("security:metrics:active_alerts")

                return True

            return False

        except Exception as e:
            print(f"Failed to resolve alert {alert_id}: {e}")
            return False


# Global security monitoring service instance
_security_monitoring_service: Optional[SecurityMonitoringService] = None


def get_security_monitoring_service() -> Optional[SecurityMonitoringService]:
    """Get global security monitoring service instance."""
    return _security_monitoring_service


def set_security_monitoring_service(service: SecurityMonitoringService):
    """Set global security monitoring service instance."""
    global _security_monitoring_service
    _security_monitoring_service = service


__all__ = [
    "SecurityMonitoringService",
    "SecurityEvent",
    "SecurityAlert",
    "SecurityMetrics",
    "AlertSeverity",
    "EventType",
    "MonitoringConfig",
    "get_security_monitoring_service",
    "set_security_monitoring_service"
]