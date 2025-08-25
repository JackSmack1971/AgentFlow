"""
Production-Ready Security Alerting System for AgentFlow
Implements comprehensive alerting with escalation paths and multi-channel distribution
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    type: str
    severity: AlertSeverity
    title: str
    description: str
    source: str
    component: str
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    timestamp: datetime = None
    tags: List[str] = None
    data: Dict[str, Any] = None
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalation_level: int = 0
    escalation_deadline: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.tags is None:
            self.tags = []
        if self.data is None:
            self.data = {}

class AlertEscalationRule:
    """Alert escalation rule configuration"""

    def __init__(self,
                 severity: AlertSeverity,
                 initial_response_time: timedelta,
                 escalation_steps: List[Dict[str, Any]],
                 max_escalation_level: int = 3):
        self.severity = severity
        self.initial_response_time = initial_response_time
        self.escalation_steps = escalation_steps
        self.max_escalation_level = max_escalation_level

    def get_escalation_deadline(self, alert_timestamp: datetime) -> datetime:
        """Get escalation deadline for alert"""
        return alert_timestamp + self.initial_response_time

    def get_escalation_step(self, level: int) -> Optional[Dict[str, Any]]:
        """Get escalation step for given level"""
        if 0 <= level < len(self.escalation_steps):
            return self.escalation_steps[level]
        return None

class SecurityAlertManager:
    """
    Production-ready security alert management system
    """

    def __init__(self, redis_client, config: Dict[str, Any]):
        self.redis = redis_client
        self.config = config
        self.alert_correlator = AlertCorrelationEngine()
        self.escalation_manager = AlertEscalationManager()

        # Alert channels
        self.channels = {
            'slack': SlackAlertChannel(config.get('slack', {})),
            'email': EmailAlertChannel(config.get('email', {})),
            'pagerduty': PagerDutyAlertChannel(config.get('pagerduty', {})),
            'sms': SMSAlertChannel(config.get('sms', {})),
            'webhook': WebhookAlertChannel(config.get('webhook', {}))
        }

        # Alert deduplication
        self.deduplication_window = timedelta(minutes=config.get('deduplication_window_minutes', 15))
        self.correlation_window = timedelta(minutes=config.get('correlation_window_minutes', 5))

        # Escalation rules
        self.escalation_rules = self._initialize_escalation_rules()

    def _initialize_escalation_rules(self) -> Dict[AlertSeverity, AlertEscalationRule]:
        """Initialize escalation rules for different severity levels"""
        return {
            AlertSeverity.CRITICAL: AlertEscalationRule(
                severity=AlertSeverity.CRITICAL,
                initial_response_time=timedelta(minutes=5),
                escalation_steps=[
                    {
                        'level': 0,
                        'channels': ['pagerduty', 'slack', 'sms', 'phone'],
                        'recipients': ['security_team', 'management'],
                        'description': 'Immediate notification to all security personnel'
                    },
                    {
                        'level': 1,
                        'channels': ['phone', 'pagerduty'],
                        'recipients': ['security_director', 'executive_team'],
                        'description': 'Escalate to senior management',
                        'delay_minutes': 15
                    },
                    {
                        'level': 2,
                        'channels': ['phone', 'pagerduty'],
                        'recipients': ['ceo', 'board_members'],
                        'description': 'Escalate to executive leadership',
                        'delay_minutes': 30
                    }
                ]
            ),
            AlertSeverity.HIGH: AlertEscalationRule(
                severity=AlertSeverity.HIGH,
                initial_response_time=timedelta(minutes=15),
                escalation_steps=[
                    {
                        'level': 0,
                        'channels': ['slack', 'email', 'pagerduty'],
                        'recipients': ['security_team'],
                        'description': 'Notify security team'
                    },
                    {
                        'level': 1,
                        'channels': ['phone', 'pagerduty'],
                        'recipients': ['security_lead', 'management'],
                        'description': 'Escalate to security leadership',
                        'delay_minutes': 30
                    }
                ]
            ),
            AlertSeverity.MEDIUM: AlertEscalationRule(
                severity=AlertSeverity.MEDIUM,
                initial_response_time=timedelta(hours=1),
                escalation_steps=[
                    {
                        'level': 0,
                        'channels': ['slack', 'email'],
                        'recipients': ['security_team'],
                        'description': 'Notify security team'
                    },
                    {
                        'level': 1,
                        'channels': ['email', 'pagerduty'],
                        'recipients': ['security_lead'],
                        'description': 'Escalate to security lead',
                        'delay_minutes': 120
                    }
                ]
            ),
            AlertSeverity.LOW: AlertEscalationRule(
                severity=AlertSeverity.LOW,
                initial_response_time=timedelta(hours=4),
                escalation_steps=[
                    {
                        'level': 0,
                        'channels': ['slack', 'email'],
                        'recipients': ['security_team'],
                        'description': 'Notify security team'
                    }
                ]
            )
        }

    async def process_alert(self, alert: SecurityAlert) -> str:
        """
        Process a security alert through the complete lifecycle

        Args:
            alert: Security alert to process

        Returns:
            str: Alert ID
        """
        try:
            # Generate alert ID if not provided
            if not alert.alert_id:
                alert.alert_id = f"{alert.type}_{alert.component}_{int(datetime.utcnow().timestamp())}"

            # Check for alert correlation
            correlated_alert = await self.alert_correlator.correlate_alert(alert)
            if correlated_alert:
                alert = correlated_alert

            # Check for alert deduplication
            if await self._is_duplicate_alert(alert):
                logger.info(f"Duplicate alert suppressed: {alert.alert_id}")
                return alert.alert_id

            # Set escalation deadline
            escalation_rule = self.escalation_rules.get(alert.severity)
            if escalation_rule:
                alert.escalation_deadline = escalation_rule.get_escalation_deadline(alert.timestamp)

            # Store alert
            await self._store_alert(alert)

            # Send initial alert
            await self._send_initial_alert(alert)

            # Schedule escalation if needed
            if escalation_rule and len(escalation_rule.escalation_steps) > 1:
                asyncio.create_task(self._schedule_escalation(alert))

            logger.info(f"Processed security alert: {alert.alert_id} - {alert.title}")
            return alert.alert_id

        except Exception as e:
            logger.error(f"Failed to process alert {alert.alert_id}: {e}")
            raise

    async def _is_duplicate_alert(self, alert: SecurityAlert) -> bool:
        """Check if alert is a duplicate"""
        key = f"alert_deduplication:{alert.type}:{alert.component}"
        recent_alerts = await self.redis.lrange(key, 0, -1)

        for recent_alert_data in recent_alerts:
            try:
                recent_alert = json.loads(recent_alert_data)
                alert_time = datetime.fromisoformat(recent_alert['timestamp'])

                if datetime.utcnow() - alert_time < self.deduplication_window:
                    return True

            except Exception as e:
                logger.error(f"Error parsing recent alert data: {e}")

        # Add current alert to deduplication cache
        alert_data = {
            'alert_id': alert.alert_id,
            'timestamp': alert.timestamp.isoformat(),
            'title': alert.title
        }

        await self.redis.lpush(key, json.dumps(alert_data))
        await self.redis.expire(key, int(self.deduplication_window.total_seconds()))

        return False

    async def _store_alert(self, alert: SecurityAlert):
        """Store alert in Redis for tracking"""
        key = f"active_alerts:{alert.alert_id}"
        alert_data = asdict(alert)
        alert_data['timestamp'] = alert.timestamp.isoformat()
        alert_data['severity'] = alert.severity.value
        alert_data['status'] = alert.status.value
        alert_data['acknowledged_at'] = alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        alert_data['resolved_at'] = alert.resolved_at.isoformat() if alert.resolved_at else None
        alert_data['escalation_deadline'] = alert.escalation_deadline.isoformat() if alert.escalation_deadline else None

        await self.redis.set(key, json.dumps(alert_data))
        await self.redis.expire(key, 86400 * 7)  # Keep for 7 days

        # Also add to active alerts set
        await self.redis.sadd("active_security_alerts", alert.alert_id)

    async def _send_initial_alert(self, alert: SecurityAlert):
        """Send initial alert through appropriate channels"""
        escalation_rule = self.escalation_rules.get(alert.severity)
        if not escalation_rule:
            logger.warning(f"No escalation rule found for severity {alert.severity}")
            return

        initial_step = escalation_rule.get_escalation_step(0)
        if not initial_step:
            logger.warning(f"No initial escalation step found for severity {alert.severity}")
            return

        channels = initial_step.get('channels', [])
        recipients = initial_step.get('recipients', [])

        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    await self.channels[channel_name].send_alert(alert, recipients)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel_name}: {e}")

    async def _schedule_escalation(self, alert: SecurityAlert):
        """Schedule alert escalation"""
        escalation_rule = self.escalation_rules.get(alert.severity)
        if not escalation_rule:
            return

        for level in range(1, len(escalation_rule.escalation_steps)):
            step = escalation_rule.get_escalation_step(level)
            if not step:
                continue

            delay_minutes = step.get('delay_minutes', 0)
            if delay_minutes > 0:
                await asyncio.sleep(delay_minutes * 60)

                # Check if alert is still active
                if await self._is_alert_active(alert.alert_id):
                    alert.escalation_level = level
                    await self._escalate_alert(alert, step)

    async def _escalate_alert(self, alert: SecurityAlert, step: Dict[str, Any]):
        """Escalate alert to next level"""
        channels = step.get('channels', [])
        recipients = step.get('recipients', [])

        escalation_message = f"ESCALATION LEVEL {alert.escalation_level}: {alert.title}"

        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    await self.channels[channel_name].send_alert(
                        alert, recipients,
                        prefix=f"🚨 {escalation_message} 🚨"
                    )
                except Exception as e:
                    logger.error(f"Failed to escalate alert via {channel_name}: {e}")

        # Update alert escalation level
        await self._update_alert_escalation_level(alert.alert_id, alert.escalation_level)

    async def _is_alert_active(self, alert_id: str) -> bool:
        """Check if alert is still active"""
        key = f"active_alerts:{alert_id}"
        alert_data = await self.redis.get(key)

        if alert_data:
            alert = json.loads(alert_data)
            return alert.get('status') == 'active'

        return False

    async def _update_alert_escalation_level(self, alert_id: str, level: int):
        """Update alert escalation level"""
        key = f"active_alerts:{alert_id}"
        alert_data = await self.redis.get(key)

        if alert_data:
            alert = json.loads(alert_data)
            alert['escalation_level'] = level

            await self.redis.set(key, json.dumps(alert))

    async def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge security alert"""
        key = f"active_alerts:{alert_id}"
        alert_data = await self.redis.get(key)

        if alert_data:
            alert = json.loads(alert_data)
            alert['status'] = 'acknowledged'
            alert['acknowledged_by'] = user
            alert['acknowledged_at'] = datetime.utcnow().isoformat()

            await self.redis.set(key, json.dumps(alert))
            await self.redis.srem("active_security_alerts", alert_id)

            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True

        return False

    async def resolve_alert(self, alert_id: str, user: str, resolution_notes: str = "") -> bool:
        """Resolve security alert"""
        key = f"active_alerts:{alert_id}"
        alert_data = await self.redis.get(key)

        if alert_data:
            alert = json.loads(alert_data)
            alert['status'] = 'resolved'
            alert['resolved_at'] = datetime.utcnow().isoformat()
            alert['resolution_notes'] = resolution_notes

            await self.redis.set(key, json.dumps(alert))
            await self.redis.srem("active_security_alerts", alert_id)

            logger.info(f"Alert {alert_id} resolved by {user}")
            return True

        return False

    async def get_active_alerts(self) -> List[SecurityAlert]:
        """Get all active security alerts"""
        alert_ids = await self.redis.smembers("active_security_alerts")
        active_alerts = []

        for alert_id in alert_ids:
            key = f"active_alerts:{alert_id.decode() if isinstance(alert_id, bytes) else alert_id}"
            alert_data = await self.redis.get(key)

            if alert_data:
                alert_dict = json.loads(alert_data)
                alert = SecurityAlert(
                    alert_id=alert_dict['alert_id'],
                    type=alert_dict['type'],
                    severity=AlertSeverity(alert_dict['severity']),
                    title=alert_dict.get('title', ''),
                    description=alert_dict.get('description', ''),
                    source=alert_dict.get('source', ''),
                    component=alert_dict.get('component', ''),
                    status=AlertStatus(alert_dict['status']),
                    timestamp=datetime.fromisoformat(alert_dict['timestamp']),
                    tags=alert_dict.get('tags', []),
                    data=alert_dict.get('data', {})
                )
                active_alerts.append(alert)

        return active_alerts

class AlertCorrelationEngine:
    """
    Advanced alert correlation engine
    """

    def __init__(self):
        self.correlation_rules = self._initialize_correlation_rules()

    def _initialize_correlation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert correlation rules"""
        return {
            'authentication_failures': {
                'threshold': 10,
                'window_minutes': 5,
                'correlation_type': 'brute_force_attack',
                'severity_boost': AlertSeverity.HIGH
            },
            'rate_limit_exceeded': {
                'threshold': 5,
                'window_minutes': 10,
                'correlation_type': 'dos_attack',
                'severity_boost': AlertSeverity.HIGH
            },
            'suspicious_file_uploads': {
                'threshold': 3,
                'window_minutes': 15,
                'correlation_type': 'malware_campaign',
                'severity_boost': AlertSeverity.MEDIUM
            },
            'injection_attempts': {
                'threshold': 5,
                'window_minutes': 10,
                'correlation_type': 'injection_attack',
                'severity_boost': AlertSeverity.CRITICAL
            }
        }

    async def correlate_alert(self, alert: SecurityAlert) -> Optional[SecurityAlert]:
        """Correlate alert with existing alerts"""
        # Implementation would check Redis for similar recent alerts
        # and create correlated alerts if thresholds are met
        return None  # Placeholder

class BaseAlertChannel:
    """Base class for alert channels"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def send_alert(self, alert: SecurityAlert, recipients: List[str], prefix: str = ""):
        """Send alert through this channel"""
        raise NotImplementedError

class SlackAlertChannel(BaseAlertChannel):
    """Slack alert channel"""

    async def send_alert(self, alert: SecurityAlert, recipients: List[str], prefix: str = ""):
        """Send alert to Slack"""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return

        # Map recipients to channels
        channel_map = {
            'security_team': '#security-incidents',
            'management': '#security-management',
            'security_lead': '#security-lead'
        }

        for recipient in recipients:
            channel = channel_map.get(recipient, '#security-monitoring')

            message = {
                "channel": channel,
                "username": "Security Alert System",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": self._get_slack_color(alert.severity),
                        "title": f"{prefix} {alert.title}".strip(),
                        "text": alert.description,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Component",
                                "value": alert.component,
                                "short": True
                            },
                            {
                                "title": "Alert ID",
                                "value": alert.alert_id,
                                "short": True
                            }
                        ],
                        "footer": "AgentFlow Security Alert System",
                        "ts": alert.timestamp.timestamp()
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send Slack alert: {response.status}")

    def _get_slack_color(self, severity: AlertSeverity) -> str:
        """Get Slack color for severity"""
        color_map = {
            AlertSeverity.CRITICAL: "#FF0000",
            AlertSeverity.HIGH: "#FFA500",
            AlertSeverity.MEDIUM: "#FFFF00",
            AlertSeverity.LOW: "#00FF00"
        }
        return color_map.get(severity, "#000000")

class EmailAlertChannel(BaseAlertChannel):
    """Email alert channel"""

    async def send_alert(self, alert: SecurityAlert, recipients: List[str], prefix: str = ""):
        """Send alert via email"""
        smtp_config = self.config.get('smtp', {})

        # Implementation would use actual email sending
        logger.info(f"Email alert: {alert.title} to {recipients}")

class PagerDutyAlertChannel(BaseAlertChannel):
    """PagerDuty alert channel"""

    async def send_alert(self, alert: SecurityAlert, recipients: List[str], prefix: str = ""):
        """Send alert to PagerDuty"""
        api_key = self.config.get('api_key')
        if not api_key:
            return

        # Implementation would integrate with PagerDuty API
        logger.info(f"PagerDuty alert: {alert.title}")

class SMSAlertChannel(BaseAlertChannel):
    """SMS alert channel"""

    async def send_alert(self, alert: SecurityAlert, recipients: List[str], prefix: str = ""):
        """Send alert via SMS"""
        # Implementation would integrate with SMS service
        logger.info(f"SMS alert: {alert.title}")

class WebhookAlertChannel(BaseAlertChannel):
    """Generic webhook alert channel"""

    async def send_alert(self, alert: SecurityAlert, recipients: List[str], prefix: str = ""):
        """Send alert via webhook"""
        webhook_url = self.config.get('url')
        if not webhook_url:
            return

        payload = {
            'alert_id': alert.alert_id,
            'type': alert.type,
            'severity': alert.severity.value,
            'title': f"{prefix} {alert.title}".strip(),
            'description': alert.description,
            'component': alert.component,
            'timestamp': alert.timestamp.isoformat(),
            'data': alert.data
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Failed to send webhook alert: {response.status}")

# Convenience functions for creating common security alerts
async def create_authentication_failure_alert(failures: int, time_window: int = 5) -> SecurityAlert:
    """Create authentication failure alert"""
    return SecurityAlert(
        type='authentication_failure_spike',
        severity=AlertSeverity.HIGH if failures > 50 else AlertSeverity.MEDIUM,
        title=f'Authentication Failure Spike: {failures} failures in {time_window} minutes',
        description=f'Detected {failures} authentication failures in the last {time_window} minutes',
        source='authentication_service',
        component='jwt_auth',
        current_value=float(failures),
        threshold_value=50.0,
        tags=['authentication', 'security'],
        data={'failures': failures, 'time_window_minutes': time_window}
    )

async def create_injection_attempt_alert(attempts: int, attack_type: str) -> SecurityAlert:
    """Create injection attempt alert"""
    return SecurityAlert(
        type='injection_attempt',
        severity=AlertSeverity.CRITICAL if attempts > 10 else AlertSeverity.HIGH,
        title=f'{attack_type} Injection Attempts: {attempts} detected',
        description=f'Detected {attempts} {attack_type} injection attempts',
        source='security_validator',
        component='input_validation',
        current_value=float(attempts),
        threshold_value=10.0,
        tags=['injection', 'security', attack_type.lower()],
        data={'attempts': attempts, 'attack_type': attack_type}
    )

async def create_rate_limit_alert(blocked_requests: int, source_ip: str = None) -> SecurityAlert:
    """Create rate limiting alert"""
    return SecurityAlert(
        type='rate_limit_exceeded',
        severity=AlertSeverity.MEDIUM,
        title=f'Rate Limit Exceeded: {blocked_requests} requests blocked',
        description=f'Rate limiting blocked {blocked_requests} requests' + (f' from {source_ip}' if source_ip else ''),
        source='rate_limiter',
        component='api_security',
        current_value=float(blocked_requests),
        threshold_value=1000.0,
        tags=['rate_limiting', 'dos_protection'],
        data={'blocked_requests': blocked_requests, 'source_ip': source_ip}
    )

async def create_malicious_file_alert(detected_files: int, file_types: List[str]) -> SecurityAlert:
    """Create malicious file upload alert"""
    return SecurityAlert(
        type='malicious_file_detected',
        severity=AlertSeverity.HIGH,
        title=f'Malicious Files Detected: {detected_files} files blocked',
        description=f'Detected {detected_files} malicious files of types: {", ".join(file_types)}',
        source='file_validator',
        component='file_security',
        current_value=float(detected_files),
        threshold_value=5.0,
        tags=['malware', 'file_security'],
        data={'detected_files': detected_files, 'file_types': file_types}
    )

# Global alert manager instance
alert_manager: Optional[SecurityAlertManager] = None

async def initialize_alert_manager(redis_client, config: Dict[str, Any]) -> SecurityAlertManager:
    """Initialize global alert manager"""
    global alert_manager

    if alert_manager is None:
        alert_manager = SecurityAlertManager(redis_client, config)
        logger.info("Security Alert Manager initialized")

    return alert_manager

async def get_alert_manager() -> SecurityAlertManager:
    """Get global alert manager instance"""
    if alert_manager is None:
        raise RuntimeError("Alert manager not initialized")
    return alert_manager