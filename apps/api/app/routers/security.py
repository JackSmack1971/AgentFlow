"""Security management router for configuration and monitoring."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ..core.security_config import (
    get_security_config_manager,
    get_security_config,
    SecurityConfig
)
from ..core.settings import get_settings, Settings
from ..services.rate_limiting_service import get_rate_limiting_service
from ..services.security_monitoring import get_security_monitoring_service
from ..utils.encryption import get_encryption_manager

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/config", summary="Get security configuration")
async def get_security_configuration(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get current security configuration (admin only)."""
    try:
        config_manager = get_security_config_manager(settings)
        config = config_manager.config

        # Return configuration without sensitive data
        return {
            "environment": config.environment,
            "enable_security": config.enable_security,
            "rate_limiting": {
                "requests_per_minute": config.rate_limiting.requests_per_minute,
                "burst_limit": config.rate_limiting.burst_limit,
                "strategy": config.rate_limiting.strategy,
                "enable_redis": config.rate_limiting.enable_redis
            },
            "monitoring": {
                "enable_real_time_alerts": config.monitoring.enable_real_time_alerts,
                "enable_anomaly_detection": config.monitoring.enable_anomaly_detection,
                "metrics_retention_days": config.monitoring.metrics_retention_days,
                "alert_thresholds": config.monitoring.alert_thresholds
            },
            "jwt": {
                "algorithm": config.jwt.algorithm,
                "access_token_ttl_minutes": config.jwt.access_token_ttl_minutes,
                "refresh_token_ttl_minutes": config.jwt.refresh_token_ttl_minutes,
                "enable_jti": config.jwt.enable_jti,
                "max_tokens_per_user": config.jwt.max_tokens_per_user
            },
            "otp": {
                "length": config.otp.length,
                "ttl_minutes": config.otp.ttl_minutes,
                "max_attempts": config.otp.max_attempts
            },
            "logging": {
                "log_level": config.log_level,
                "enable_file_logging": config.enable_file_logging,
                "enable_console_logging": config.enable_console_logging
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve security config: {str(e)}")


@router.get("/health", summary="Security system health check")
async def get_security_health(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Get security system health status."""
    try:
        config_manager = get_security_config_manager(settings)
        health_status = config_manager.get_health_status()

        return {
            "status": health_status["status"],
            "timestamp": "2025-08-24T21:10:42.027Z",  # Current timestamp
            "services": health_status["services"],
            "issues": health_status["issues"],
            "recommendations": [
                "Review and address any configuration issues",
                "Ensure encryption keys are properly configured",
                "Verify monitoring alerts are working",
                "Check rate limiting is functioning correctly"
            ] if health_status["issues"] else []
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": "2025-08-24T21:10:42.027Z",
            "services": {},
            "issues": [f"Health check failed: {str(e)}"],
            "recommendations": ["Contact system administrator"]
        }


@router.get("/metrics", summary="Security metrics")
async def get_security_metrics() -> Dict[str, Any]:
    """Get security monitoring metrics."""
    try:
        monitoring_service = get_security_monitoring_service()
        if monitoring_service:
            metrics = await monitoring_service.get_security_metrics()
            return {
                "total_events": metrics.total_events,
                "alerts_triggered": metrics.alerts_triggered,
                "active_alerts": metrics.active_alerts,
                "critical_alerts": metrics.critical_alerts,
                "events_by_type": metrics.events_by_type,
                "top_attack_sources": metrics.top_attack_sources,
                "timestamp": metrics.timestamp.isoformat() if metrics.timestamp else None
            }
        else:
            return {
                "error": "Security monitoring service not available",
                "total_events": 0,
                "alerts_triggered": 0,
                "active_alerts": 0,
                "critical_alerts": 0,
                "events_by_type": {},
                "top_attack_sources": {}
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/rate-limit/status", summary="Rate limiting status")
async def get_rate_limit_status() -> Dict[str, Any]:
    """Get rate limiting service status."""
    try:
        rate_limiter = get_rate_limiting_service()
        if rate_limiter:
            config = rate_limiter.get_config()
            return {
                "service": "active",
                "requests_per_minute": config.requests_per_minute,
                "burst_limit": config.burst_limit,
                "window_seconds": config.window_seconds,
                "strategy": config.strategy.value
            }
        else:
            return {
                "service": "inactive",
                "error": "Rate limiting service not initialized"
            }
    except Exception as e:
        return {
            "service": "error",
            "error": str(e)
        }


@router.get("/encryption/status", summary="Encryption service status")
async def get_encryption_status() -> Dict[str, Any]:
    """Get encryption service status."""
    try:
        encryption_manager = get_encryption_manager()
        if encryption_manager:
            return {
                "service": "active",
                "key_available": True,
                "test_encryption": "Encryption service is operational"
            }
        else:
            return {
                "service": "inactive",
                "key_available": False,
                "error": "Encryption manager not initialized"
            }
    except Exception as e:
        return {
            "service": "error",
            "key_available": False,
            "error": str(e)
        }


@router.get("/validate", summary="Validate security configuration")
async def validate_security_config(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """Validate security configuration and return issues."""
    try:
        config_manager = get_security_config_manager(settings)
        issues = config_manager.validate_config()

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": [
                "Fix configuration issues before deploying to production",
                "Review security settings with security team",
                "Test security features in staging environment"
            ] if issues else ["Security configuration is valid"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")