from __future__ import annotations

import re
import sys
from contextvars import ContextVar
from typing import Any, cast

from loguru import logger
from loguru._logger import Logger

request_id_ctx_var: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

SECRET_PATTERN = re.compile(r"[A-Za-z0-9]{32,}")

# Security monitoring integration
_security_monitor = None


def _redact(record: dict[str, Any]) -> dict[str, Any]:
    """Redact potential secrets from log records."""
    record["message"] = SECRET_PATTERN.sub("***", record["message"])
    return record


def setup_logging(level: str = "INFO") -> None:
    """Configure JSON structured logging.

    Args:
        level: Minimum log level.
    """
    logger.remove()
    logger.add(
        sys.stdout,
        serialize=True,
        level=level,
        filter=cast(Any, _redact),
    )


def logger_with_request_id() -> Logger:
    """Return a logger bound with the current request ID if available."""
    request_id = request_id_ctx_var.get()
    bound = logger.bind(request_id=request_id) if request_id else logger
    return cast(Logger, bound)


def set_security_monitor(monitor) -> None:
    """Set the security monitoring service for integration."""
    global _security_monitor
    _security_monitor = monitor


def get_security_logger() -> Logger:
    """Get a security-specific logger with monitoring integration."""
    security_logger = logger.bind(logger_name="security")

    class SecurityLogger:
        """Enhanced security logger with monitoring integration."""

        def info(self, message: str, **kwargs) -> None:
            """Log security info with monitoring."""
            security_logger.info(message, **kwargs)

        def warning(self, message: str, **kwargs) -> None:
            """Log security warning with monitoring."""
            security_logger.warning(message, **kwargs)

        def error(self, message: str, **kwargs) -> None:
            """Log security error with monitoring."""
            security_logger.error(message, **kwargs)

        def critical(self, message: str, **kwargs) -> None:
            """Log security critical event with monitoring."""
            security_logger.critical(message, **kwargs)

        async def log_security_event(self, event_type: str, identifier: str,
                                  details: dict = None, severity: str = "medium") -> None:
            """Log security event with monitoring service integration."""
            if details is None:
                details = {}

            # Log to standard logger
            log_data = {
                "event_type": event_type,
                "identifier": identifier,
                "details": details,
                "severity": severity
            }
            security_logger.info(f"Security event: {event_type}", **log_data)

            # Send to security monitoring service if available
            if _security_monitor:
                try:
                    from ..services.security_monitoring import (
                        SecurityEvent, EventType, AlertSeverity
                    )

                    # Map event type
                    event_type_mapping = {
                        "rate_limit_exceeded": EventType.RATE_LIMIT_EXCEEDED,
                        "unauthorized_access": EventType.UNAUTHORIZED_ACCESS,
                        "suspicious_login": EventType.SUSPICIOUS_LOGIN,
                        "sql_injection": EventType.SQL_INJECTION,
                        "xss_attempt": EventType.XSS_ATTEMPT,
                        "brute_force": EventType.BRUTE_FORCE,
                        "data_breach": EventType.DATA_BREACH,
                        "malware_detected": EventType.MALWARE_DETECTED,
                        "dos_attack": EventType.DOS_ATTACK
                    }

                    # Map severity
                    severity_mapping = {
                        "low": AlertSeverity.LOW,
                        "medium": AlertSeverity.MEDIUM,
                        "high": AlertSeverity.HIGH,
                        "critical": AlertSeverity.CRITICAL
                    }

                    mapped_event_type = event_type_mapping.get(event_type, EventType.SUSPICIOUS_LOGIN)
                    mapped_severity = severity_mapping.get(severity.lower(), AlertSeverity.MEDIUM)

                    security_event = SecurityEvent(
                        event_type=mapped_event_type,
                        identifier=identifier,
                        details=details,
                        severity=mapped_severity
                    )

                    await _security_monitor.record_security_event(security_event)

                except Exception as e:
                    security_logger.error(f"Failed to record security event in monitoring service: {e}")

    return SecurityLogger()
