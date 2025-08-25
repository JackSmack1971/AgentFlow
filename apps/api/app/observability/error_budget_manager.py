"""
Security Error Budget Management System for AgentFlow
Implements comprehensive error budget tracking and alerting for security SLOs
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
from prometheus_client import Gauge, Counter, Histogram

logger = logging.getLogger(__name__)

class BudgetStatus(Enum):
    """Error budget status enumeration"""
    OK = "ok"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    CRITICAL = "critical"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorBudget:
    """Error budget configuration and tracking"""
    slo_name: str
    target: float
    monthly_budget_minutes: Optional[float] = None
    monthly_budget_count: Optional[int] = None
    current_usage: float = 0
    reset_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    warning_threshold: float = 0.75  # 75% of budget
    critical_threshold: float = 0.9   # 90% of budget

    def is_exceeded(self) -> bool:
        """Check if error budget is exceeded"""
        if self.monthly_budget_count is not None:
            return self.current_usage > self.monthly_budget_count
        elif self.monthly_budget_minutes is not None:
            return self.current_usage > self.monthly_budget_minutes
        return False

    def is_warning_level(self) -> bool:
        """Check if budget is at warning level"""
        if self.monthly_budget_count is not None:
            warning_threshold = self.monthly_budget_count * self.warning_threshold
            return self.current_usage > warning_threshold
        elif self.monthly_budget_minutes is not None:
            warning_threshold = self.monthly_budget_minutes * self.warning_threshold
            return self.current_usage > warning_threshold
        return False

    def is_critical_level(self) -> bool:
        """Check if budget is at critical level"""
        if self.monthly_budget_count is not None:
            critical_threshold = self.monthly_budget_count * self.critical_threshold
            return self.current_usage > critical_threshold
        elif self.monthly_budget_minutes is not None:
            critical_threshold = self.monthly_budget_minutes * self.critical_threshold
            return self.current_usage > critical_threshold
        return False

    def get_status(self) -> BudgetStatus:
        """Get current budget status"""
        if self.is_exceeded():
            return BudgetStatus.EXCEEDED
        elif self.is_critical_level():
            return BudgetStatus.CRITICAL
        elif self.is_warning_level():
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.OK

    def get_usage_percentage(self) -> float:
        """Get percentage of budget used"""
        if self.monthly_budget_count is not None and self.monthly_budget_count > 0:
            return (self.current_usage / self.monthly_budget_count) * 100
        elif self.monthly_budget_minutes is not None and self.monthly_budget_minutes > 0:
            return (self.current_usage / self.monthly_budget_minutes) * 100
        return 0.0

    def get_remaining_budget(self) -> float:
        """Get remaining budget"""
        if self.monthly_budget_count is not None:
            return max(0, self.monthly_budget_count - self.current_usage)
        elif self.monthly_budget_minutes is not None:
            return max(0, self.monthly_budget_minutes - self.current_usage)
        return 0.0

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    type: str
    severity: AlertSeverity
    description: str
    slo_name: str
    current_value: float
    threshold_value: float
    budget_usage: float
    budget_limit: float
    timestamp: datetime
    data: Dict[str, Any]

class SecurityErrorBudgetManager:
    """
    Production-ready error budget management system for security SLOs
    """

    def __init__(self, redis_client: redis.Redis, reset_day: int = 1):
        """
        Initialize error budget manager

        Args:
            redis_client: Redis client for persistence
            reset_day: Day of month for budget reset (1-31)
        """
        self.redis = redis_client
        self.reset_day = reset_day
        self.budgets: Dict[str, ErrorBudget] = {}
        self.alert_manager = SecurityAlertManager(redis_client)

        # Prometheus metrics
        self.budget_usage_gauge = Gauge(
            'security_error_budget_usage_percent',
            'Error budget usage percentage',
            ['slo_name']
        )
        self.budget_status_gauge = Gauge(
            'security_error_budget_status',
            'Error budget status (0=OK, 1=WARNING, 2=CRITICAL, 3=EXCEEDED)',
            ['slo_name']
        )
        self.budget_alerts_counter = Counter(
            'security_budget_alerts_total',
            'Total number of error budget alerts',
            ['severity', 'slo_name']
        )

        # Initialize budgets
        self._initialize_budgets()

    def _initialize_budgets(self):
        """Initialize error budgets for all security SLOs"""
        self.budgets = {
            'authentication_success_rate': ErrorBudget(
                slo_name='authentication_success_rate',
                target=0.9995,  # 99.95%
                monthly_budget_minutes=21.56,
                warning_threshold=0.75,
                critical_threshold=0.9
            ),
            'token_validation_latency': ErrorBudget(
                slo_name='token_validation_latency',
                target=0.1,  # 100ms - hard limit
                monthly_budget_minutes=0,
                warning_threshold=1.0,
                critical_threshold=1.0
            ),
            'threat_detection_time': ErrorBudget(
                slo_name='threat_detection_time',
                target=30.0,  # 30 seconds - hard limit
                monthly_budget_minutes=0,
                warning_threshold=1.0,
                critical_threshold=1.0
            ),
            'injection_prevention': ErrorBudget(
                slo_name='injection_prevention',
                target=1.0,  # 100% - zero tolerance
                monthly_budget_count=0,
                warning_threshold=1.0,
                critical_threshold=1.0
            ),
            'rate_limiting_effectiveness': ErrorBudget(
                slo_name='rate_limiting_effectiveness',
                target=0.999,
                monthly_budget_minutes=43.2,
                warning_threshold=0.75,
                critical_threshold=0.9
            ),
            'file_validation_accuracy': ErrorBudget(
                slo_name='file_validation_accuracy',
                target=0.9995,
                monthly_budget_minutes=21.56,
                warning_threshold=0.75,
                critical_threshold=0.9
            ),
            'security_event_ingestion': ErrorBudget(
                slo_name='security_event_ingestion',
                target=0.9999,
                monthly_budget_minutes=4.32,
                warning_threshold=0.75,
                critical_threshold=0.9
            )
        }

    async def track_error_budget_usage(self, slo_name: str, error_count: int = 1, error_duration: float = 0):
        """
        Track error budget usage for specific SLO

        Args:
            slo_name: Name of the SLO
            error_count: Number of errors (for count-based budgets)
            error_duration: Duration of error in minutes (for time-based budgets)
        """
        if slo_name not in self.budgets:
            logger.warning(f"Unknown SLO: {slo_name}")
            return

        budget = self.budgets[slo_name]

        # Update usage based on budget type
        if budget.monthly_budget_count is not None:
            budget.current_usage += error_count
        elif budget.monthly_budget_minutes is not None:
            budget.current_usage += error_duration

        budget.last_updated = datetime.utcnow()

        # Check if we need to reset budget (monthly)
        await self._check_budget_reset(budget)

        # Update Prometheus metrics
        self.budget_usage_gauge.labels(slo_name=slo_name).set(budget.get_usage_percentage())
        self.budget_status_gauge.labels(slo_name=slo_name).set(budget.get_status().value)

        # Check for alerts
        await self._check_budget_alerts(budget)

        # Persist budget state
        await self._persist_budget_state(budget)

    async def _check_budget_reset(self, budget: ErrorBudget):
        """Check if budget needs to be reset"""
        now = datetime.utcnow()

        # Reset on the specified day of each month
        if (budget.reset_date is None or
            now.day >= self.reset_day and
            (budget.reset_date.month < now.month or budget.reset_date.year < now.year)):

            logger.info(f"Resetting error budget for {budget.slo_name}")
            budget.current_usage = 0
            budget.reset_date = now.replace(day=self.reset_day, hour=0, minute=0, second=0, microsecond=0)

    async def _check_budget_alerts(self, budget: ErrorBudget):
        """Check if budget requires alerts"""
        status = budget.get_status()

        if status == BudgetStatus.WARNING:
            await self._create_budget_warning_alert(budget)
        elif status == BudgetStatus.CRITICAL:
            await self._create_budget_critical_alert(budget)
        elif status == BudgetStatus.EXCEEDED:
            await self._create_budget_exceeded_alert(budget)

    async def _create_budget_warning_alert(self, budget: ErrorBudget):
        """Create warning alert for budget usage"""
        alert = SecurityAlert(
            alert_id=f"budget_warning_{budget.slo_name}_{datetime.utcnow().timestamp()}",
            type='error_budget_warning',
            severity=AlertSeverity.MEDIUM,
            description=f"Error budget at {budget.get_usage_percentage():.1f}% for {budget.slo_name}",
            slo_name=budget.slo_name,
            current_value=budget.get_usage_percentage(),
            threshold_value=budget.warning_threshold * 100,
            budget_usage=budget.current_usage,
            budget_limit=budget.monthly_budget_count or budget.monthly_budget_minutes or 0,
            timestamp=datetime.utcnow(),
            data={
                'budget_type': 'count' if budget.monthly_budget_count else 'time',
                'warning_threshold': budget.warning_threshold,
                'remaining_budget': budget.get_remaining_budget()
            }
        )

        await self.alert_manager.process_alert(alert)
        self.budget_alerts_counter.labels(severity='warning', slo_name=budget.slo_name).inc()

    async def _create_budget_critical_alert(self, budget: ErrorBudget):
        """Create critical alert for budget usage"""
        alert = SecurityAlert(
            alert_id=f"budget_critical_{budget.slo_name}_{datetime.utcnow().timestamp()}",
            type='error_budget_critical',
            severity=AlertSeverity.HIGH,
            description=f"Error budget at {budget.get_usage_percentage():.1f}% for {budget.slo_name}",
            slo_name=budget.slo_name,
            current_value=budget.get_usage_percentage(),
            threshold_value=budget.critical_threshold * 100,
            budget_usage=budget.current_usage,
            budget_limit=budget.monthly_budget_count or budget.monthly_budget_minutes or 0,
            timestamp=datetime.utcnow(),
            data={
                'budget_type': 'count' if budget.monthly_budget_count else 'time',
                'critical_threshold': budget.critical_threshold,
                'remaining_budget': budget.get_remaining_budget()
            }
        )

        await self.alert_manager.process_alert(alert)
        self.budget_alerts_counter.labels(severity='critical', slo_name=budget.slo_name).inc()

    async def _create_budget_exceeded_alert(self, budget: ErrorBudget):
        """Create exceeded alert for budget usage"""
        alert = SecurityAlert(
            alert_id=f"budget_exceeded_{budget.slo_name}_{datetime.utcnow().timestamp()}",
            type='error_budget_exceeded',
            severity=AlertSeverity.CRITICAL,
            description=f"Error budget exceeded for {budget.slo_name}: {budget.current_usage} > {budget.monthly_budget_count or budget.monthly_budget_minutes}",
            slo_name=budget.slo_name,
            current_value=budget.get_usage_percentage(),
            threshold_value=100.0,
            budget_usage=budget.current_usage,
            budget_limit=budget.monthly_budget_count or budget.monthly_budget_minutes or 0,
            timestamp=datetime.utcnow(),
            data={
                'budget_type': 'count' if budget.monthly_budget_count else 'time',
                'over_budget_by': budget.current_usage - (budget.monthly_budget_count or budget.monthly_budget_minutes or 0)
            }
        )

        await self.alert_manager.process_alert(alert)
        self.budget_alerts_counter.labels(severity='exceeded', slo_name=budget.slo_name).inc()

    async def _persist_budget_state(self, budget: ErrorBudget):
        """Persist budget state to Redis"""
        key = f"security_budget:{budget.slo_name}"
        budget_data = asdict(budget)
        budget_data['reset_date'] = budget.reset_date.isoformat() if budget.reset_date else None
        budget_data['last_updated'] = budget.last_updated.isoformat() if budget.last_updated else None

        await self.redis.set(key, json.dumps(budget_data))

    async def load_budget_states(self):
        """Load budget states from Redis"""
        for slo_name in self.budgets.keys():
            key = f"security_budget:{slo_name}"
            data = await self.redis.get(key)

            if data:
                try:
                    budget_data = json.loads(data)
                    budget = self.budgets[slo_name]

                    budget.current_usage = budget_data.get('current_usage', 0)
                    budget.reset_date = datetime.fromisoformat(budget_data['reset_date']) if budget_data.get('reset_date') else None
                    budget.last_updated = datetime.fromisoformat(budget_data['last_updated']) if budget_data.get('last_updated') else None

                except Exception as e:
                    logger.error(f"Failed to load budget state for {slo_name}: {e}")

    def get_budget_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current status of all error budgets"""
        return {
            slo_name: {
                'current_usage': budget.current_usage,
                'budget_limit': budget.monthly_budget_count or budget.monthly_budget_minutes,
                'usage_percentage': budget.get_usage_percentage(),
                'remaining_budget': budget.get_remaining_budget(),
                'status': budget.get_status().value,
                'is_warning': budget.is_warning_level(),
                'is_critical': budget.is_critical_level(),
                'is_exceeded': budget.is_exceeded(),
                'last_updated': budget.last_updated.isoformat() if budget.last_updated else None
            }
            for slo_name, budget in self.budgets.items()
        }

    async def reset_budget(self, slo_name: str) -> bool:
        """Manually reset budget for specific SLO"""
        if slo_name not in self.budgets:
            return False

        budget = self.budgets[slo_name]
        budget.current_usage = 0
        budget.reset_date = datetime.utcnow()
        budget.last_updated = datetime.utcnow()

        await self._persist_budget_state(budget)
        logger.info(f"Manually reset error budget for {slo_name}")

        return True

    async def update_budget_configuration(self, slo_name: str, updates: Dict[str, Any]) -> bool:
        """Update budget configuration"""
        if slo_name not in self.budgets:
            return False

        budget = self.budgets[slo_name]

        # Update allowed fields
        for field, value in updates.items():
            if hasattr(budget, field):
                setattr(budget, field, value)

        budget.last_updated = datetime.utcnow()
        await self._persist_budget_state(budget)

        logger.info(f"Updated budget configuration for {slo_name}: {updates}")
        return True

class SecurityAlertManager:
    """
    Security alert management and distribution system
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.alert_channels = {
            AlertSeverity.CRITICAL: ['pagerduty', 'slack_critical', 'sms', 'phone'],
            AlertSeverity.HIGH: ['slack_high', 'email_lead', 'pagerduty'],
            AlertSeverity.MEDIUM: ['slack_general', 'email_team'],
            AlertSeverity.LOW: ['slack_logs', 'email_team']
        }

        # Alert deduplication
        self.alert_deduplication_window = timedelta(minutes=15)
        self.processed_alerts_key = "processed_security_alerts"

    async def process_alert(self, alert: SecurityAlert):
        """Process and distribute security alert"""
        # Check for duplicate alerts
        if await self._is_duplicate_alert(alert):
            logger.info(f"Duplicate alert suppressed: {alert.alert_id}")
            return

        # Mark alert as processed
        await self._mark_alert_processed(alert)

        # Distribute alert through appropriate channels
        await self._distribute_alert(alert)

        # Store alert for historical analysis
        await self._store_alert(alert)

        logger.info(f"Processed security alert: {alert.alert_id} - {alert.description}")

    async def _is_duplicate_alert(self, alert: SecurityAlert) -> bool:
        """Check if alert is a duplicate within deduplication window"""
        key = f"{self.processed_alerts_key}:{alert.type}:{alert.slo_name}"
        recent_alerts = await self.redis.lrange(key, 0, -1)

        for recent_alert_data in recent_alerts:
            try:
                recent_alert = json.loads(recent_alert_data)
                alert_time = datetime.fromisoformat(recent_alert['timestamp'])

                if datetime.utcnow() - alert_time < self.alert_deduplication_window:
                    return True

            except Exception as e:
                logger.error(f"Error parsing recent alert data: {e}")

        return False

    async def _mark_alert_processed(self, alert: SecurityAlert):
        """Mark alert as processed for deduplication"""
        key = f"{self.processed_alerts_key}:{alert.type}:{alert.slo_name}"
        alert_data = {
            'alert_id': alert.alert_id,
            'timestamp': alert.timestamp.isoformat(),
            'description': alert.description
        }

        await self.redis.lpush(key, json.dumps(alert_data))
        await self.redis.expire(key, int(self.alert_deduplication_window.total_seconds()))

    async def _distribute_alert(self, alert: SecurityAlert):
        """Distribute alert through configured channels"""
        channels = self.alert_channels.get(alert.severity, ['slack_general'])

        for channel in channels:
            try:
                if channel == 'pagerduty':
                    await self._send_pagerduty_alert(alert)
                elif channel == 'slack_critical':
                    await self._send_slack_alert(alert, '#security-critical')
                elif channel == 'slack_high':
                    await self._send_slack_alert(alert, '#security-incidents')
                elif channel == 'slack_general':
                    await self._send_slack_alert(alert, '#security-monitoring')
                elif channel == 'slack_logs':
                    await self._send_slack_alert(alert, '#security-logs')
                elif channel == 'sms':
                    await self._send_sms_alert(alert)
                elif channel == 'phone':
                    await self._send_phone_alert(alert)
                elif channel == 'email_lead':
                    await self._send_email_alert(alert, 'security-lead@company.com')
                elif channel == 'email_team':
                    await self._send_email_alert(alert, 'security-team@company.com')

            except Exception as e:
                logger.error(f"Failed to send alert to {channel}: {e}")

    async def _send_pagerduty_alert(self, alert: SecurityAlert):
        """Send alert to PagerDuty"""
        # Implementation would integrate with PagerDuty API
        logger.info(f"PagerDuty alert: {alert.description}")

    async def _send_slack_alert(self, alert: SecurityAlert, channel: str):
        """Send alert to Slack channel"""
        # Implementation would integrate with Slack API
        logger.info(f"Slack alert to {channel}: {alert.description}")

    async def _send_sms_alert(self, alert: SecurityAlert):
        """Send SMS alert"""
        # Implementation would integrate with SMS service
        logger.info(f"SMS alert: {alert.description}")

    async def _send_phone_alert(self, alert: SecurityAlert):
        """Send phone alert"""
        # Implementation would integrate with phone service
        logger.info(f"Phone alert: {alert.description}")

    async def _send_email_alert(self, alert: SecurityAlert, recipient: str):
        """Send email alert"""
        # Implementation would integrate with email service
        logger.info(f"Email alert to {recipient}: {alert.description}")

    async def _store_alert(self, alert: SecurityAlert):
        """Store alert for historical analysis"""
        key = f"security_alerts:{alert.timestamp.strftime('%Y-%m-%d')}"
        alert_data = asdict(alert)
        alert_data['timestamp'] = alert.timestamp.isoformat()
        alert_data['severity'] = alert.severity.value

        await self.redis.lpush(key, json.dumps(alert_data))
        await self.redis.expire(key, 86400 * 30)  # Keep for 30 days

# Global error budget manager instance
error_budget_manager: Optional[SecurityErrorBudgetManager] = None

async def initialize_error_budget_manager(redis_client: redis.Redis) -> SecurityErrorBudgetManager:
    """Initialize global error budget manager"""
    global error_budget_manager

    if error_budget_manager is None:
        error_budget_manager = SecurityErrorBudgetManager(redis_client)
        await error_budget_manager.load_budget_states()
        logger.info("Security Error Budget Manager initialized")

    return error_budget_manager

async def get_error_budget_manager() -> SecurityErrorBudgetManager:
    """Get global error budget manager instance"""
    if error_budget_manager is None:
        raise RuntimeError("Error budget manager not initialized")
    return error_budget_manager

# Convenience functions for tracking common security errors
async def track_authentication_failure():
    """Track authentication failure for error budget"""
    manager = await get_error_budget_manager()
    await manager.track_error_budget_usage('authentication_success_rate')

async def track_token_validation_error():
    """Track token validation error for error budget"""
    manager = await get_error_budget_manager()
    await manager.track_error_budget_usage('token_validation_latency', error_duration=0.1)  # 100ms

async def track_injection_attempt():
    """Track injection attempt for error budget"""
    manager = await get_error_budget_manager()
    await manager.track_error_budget_usage('injection_prevention')

async def track_rate_limiting_failure():
    """Track rate limiting failure for error budget"""
    manager = await get_error_budget_manager()
    await manager.track_error_budget_usage('rate_limiting_effectiveness')

async def track_file_validation_error():
    """Track file validation error for error budget"""
    manager = await get_error_budget_manager()
    await manager.track_error_budget_usage('file_validation_accuracy')

async def track_event_ingestion_failure():
    """Track security event ingestion failure for error budget"""
    manager = await get_error_budget_manager()
    await manager.track_error_budget_usage('security_event_ingestion')