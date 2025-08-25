# Security Implementation Guide

## Overview

This document provides comprehensive information about the security implementations in AgentFlow, including configuration, usage, and best practices for the security components.

## Security Components

### 1. Enhanced Rate Limiting Service

**Location**: `apps/api/app/services/rate_limiting_service.py`

**Features**:
- Multiple rate limiting strategies (sliding window, fixed window)
- Burst handling and quota management
- Distributed rate limiting with Redis
- Configurable policies and security integration
- Comprehensive error handling and fail-open behavior

**Configuration**:
```python
from apps.api.app.services.rate_limiting_service import RateLimitingService, RateLimitConfig, RateLimitStrategy

# Create rate limiter configuration
config = RateLimitConfig(
    requests_per_minute=100,
    burst_limit=10,
    strategy=RateLimitStrategy.SLIDING_WINDOW
)

# Initialize service
rate_limiter = RateLimitingService(redis_client, config)

# Check rate limit
try:
    await rate_limiter.check_rate_limit(client_ip)
    # Request allowed
except RateLimitExceeded as e:
    # Handle rate limit exceeded
    print(f"Rate limited: retry after {e.retry_after} seconds")
```

### 2. Data Encryption Component

**Location**: `apps/api/app/utils/encryption.py`

**Features**:
- Fernet symmetric encryption
- OTP secret encryption/decryption
- Key generation and management
- Encryption key rotation
- Thread-safe global encryption manager

**Usage**:
```python
from apps.api.app.utils.encryption import get_encryption_manager

# Get encryption manager
encryption = get_encryption_manager()

# Encrypt sensitive data
encrypted_data = encryption.encrypt("sensitive information")

# Decrypt data
decrypted_data = encryption.decrypt(encrypted_data)

# Generate new encryption key
new_key = encryption.generate_key()
```

### 3. Security Monitoring Service

**Location**: `apps/api/app/services/security_monitoring.py`

**Features**:
- Real-time security event collection and analysis
- Automated threat detection and alerting
- Security metrics and reporting
- Anomaly detection capabilities
- Integration with existing security infrastructure

**Usage**:
```python
from apps.api.app.services.security_monitoring import get_security_monitoring_service, SecurityEvent, EventType

# Get monitoring service
monitor = get_security_monitoring_service()

# Record security event
await monitor.record_security_event(
    SecurityEvent(
        event_type=EventType.SUSPICIOUS_LOGIN,
        identifier="192.168.1.100",
        details={"attempts": 3, "user_agent": "suspicious-agent"},
        severity=AlertSeverity.MEDIUM
    )
)

# Get security metrics
metrics = await monitor.get_security_metrics()
```

### 4. OTP Service

**Location**: `apps/api/app/services/otp_service.py`

**Features**:
- Secure OTP generation and verification
- Encrypted storage of OTP secrets
- Configurable OTP length and TTL
- Automatic cleanup of expired OTPs

**Usage**:
```python
from apps.api.app.services.otp_service import get_otp_service

# Get OTP service
otp_service = get_otp_service()

# Generate and store OTP
otp = await otp_service.generate_and_store_otp("user@example.com")

# Verify OTP
is_valid = await otp_service.verify_otp("user@example.com", user_input)
```

## Security Configuration

### Unified Configuration System

**Location**: `apps/api/app/core/security_config.py`

The unified security configuration system provides centralized management of all security settings:

```python
from apps.api.app.core.security_config import get_security_config

# Get security configuration
config = get_security_config()

# Access component configurations
rate_limit_config = config.rate_limiting
encryption_config = config.encryption
monitoring_config = config.monitoring
jwt_config = config.jwt
otp_config = config.otp
```

### Environment Variables

Set the following environment variables for production:

```bash
# Encryption
export FERNET_KEY="your-secure-fernet-key-here"

# JWT
export SECRET_KEY="your-secure-jwt-secret-key"

# Redis (for distributed features)
export REDIS_URL="redis://localhost:6379"

# Security Settings
export ENVIRONMENT="production"
export SECURITY_RATE_LIMIT_PER_MINUTE="100"
export SECURITY_PENETRATION_ATTEMPTS_THRESHOLD="5"
export SECURITY_BAN_DURATION_MINUTES="60"
```

### Configuration Validation

The system includes built-in configuration validation:

```python
from apps.api.app.core.security_config import get_security_config_manager
from apps.api.core.settings import get_settings

# Validate configuration
settings = get_settings()
config_manager = get_security_config_manager(settings)
issues = config_manager.validate_config()

if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"- {issue}")
```

## Security Middleware

### Enhanced Security Middleware

**Location**: `apps/api/app/middleware/security.py`

The security middleware integrates all security components:

```python
# The middleware automatically:
# 1. Checks rate limits using enhanced rate limiting service
# 2. Monitors for suspicious patterns
# 3. Logs security events to monitoring service
# 4. Applies security headers
# 5. Handles IP banning for security violations
```

### Integration Points

The security middleware integrates with:
- **Rate Limiting Service**: Prevents abuse and DoS attacks
- **Security Monitoring Service**: Records and analyzes security events
- **Encryption Service**: Encrypts sensitive data in logs
- **Logging System**: Provides unified security event logging

## Security Endpoints

### Health Check Endpoint

```
GET /security/health
```

Returns the overall health status of security components:

```json
{
  "status": "healthy",
  "timestamp": "2025-08-24T21:11:28.802Z",
  "services": {
    "encryption": {"configured": true, "key_available": true},
    "rate_limiting": {"configured": true, "redis_available": true},
    "monitoring": {"configured": true, "alerts_enabled": true},
    "jwt": {"configured": true, "secure_algorithm": true},
    "otp": {"configured": true, "secure_length": true}
  },
  "issues": [],
  "recommendations": []
}
```

### Configuration Endpoint

```
GET /security/config
```

Returns current security configuration (admin access recommended).

### Metrics Endpoint

```
GET /security/metrics
```

Returns security monitoring metrics:

```json
{
  "total_events": 150,
  "alerts_triggered": 3,
  "active_alerts": 1,
  "critical_alerts": 0,
  "events_by_type": {
    "rate_limit_exceeded": 45,
    "suspicious_login": 12,
    "sql_injection": 2
  },
  "top_attack_sources": {
    "192.168.1.100": 25,
    "10.0.0.50": 15
  }
}
```

## Security Best Practices

### 1. Environment Configuration

- **Development**: Use relaxed settings for development productivity
- **Staging**: Mirror production settings for testing
- **Production**: Use strict security settings and monitoring

### 2. Key Management

- Store encryption keys securely (environment variables, key vaults)
- Rotate encryption keys regularly (recommended: 90 days)
- Use different keys for different environments
- Never commit keys to version control

### 3. Monitoring and Alerting

- Enable real-time alerts in production
- Set up alert notifications (email, Slack, etc.)
- Monitor security metrics regularly
- Review security logs for suspicious patterns

### 4. Rate Limiting

- Set appropriate rate limits based on API usage patterns
- Use burst capacity for legitimate traffic spikes
- Monitor rate limiting effectiveness
- Adjust limits based on traffic analysis

### 5. Incident Response

- Have an incident response plan
- Know how to investigate security events
- Set up automated responses for critical alerts
- Regularly test incident response procedures

## Troubleshooting

### Common Issues

1. **Rate Limiting Not Working**
   - Check Redis connectivity
   - Verify rate limiting configuration
   - Ensure middleware is properly configured

2. **Encryption Errors**
   - Verify FERNET_KEY environment variable
   - Check key format (should be base64)
   - Ensure key is not expired

3. **Security Events Not Logging**
   - Check logging configuration
   - Verify security monitoring service initialization
   - Ensure proper permissions for log files

4. **High False Positive Alerts**
   - Adjust alert thresholds
   - Review suspicious pattern detection rules
   - Fine-tune security monitoring configuration

### Debug Mode

Enable debug logging for security components:

```python
import logging
logging.getLogger("security").setLevel(logging.DEBUG)
```

## Security Standards Compliance

The implementation follows these security standards:

- **NIST CSF (Cybersecurity Framework)**
- **ISO 27001 Information Security**
- **OWASP Security Guidelines**
- **JWT Best Current Practices (RFC 8725)**

## Performance Considerations

- **Rate Limiting**: Minimal performance impact, Redis-based for scalability
- **Encryption**: Efficient Fernet encryption, minimal overhead
- **Monitoring**: Asynchronous event processing, non-blocking
- **Logging**: Structured logging with minimal performance impact

## Future Enhancements

- Integration with external security information and event management (SIEM) systems
- Advanced anomaly detection using machine learning
- Automated threat intelligence feeds
- Enhanced encryption options (asymmetric encryption, key rotation)
- Security dashboard and reporting features