# AgentFlow Security Middleware

This document describes the comprehensive security middleware implemented for the AgentFlow API using fastapi-guard.

## Overview

The security middleware provides enterprise-grade protection with the following features:

- **Rate Limiting**: 100 requests per minute per IP address
- **Penetration Detection**: Auto-ban after 5 suspicious attempts
- **Redis Integration**: Distributed security state management
- **IP Whitelisting**: Development environment IP bypass
- **Security Logging**: Dedicated security event logging
- **Security Headers**: Automatic security headers injection

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Security Configuration
ENVIRONMENT=dev  # dev, staging, or prod
SECURITY_RATE_LIMIT_PER_MINUTE=100
SECURITY_PENETRATION_ATTEMPTS_THRESHOLD=5
SECURITY_BAN_DURATION_MINUTES=60
SECURITY_DEV_IP_WHITELIST=127.0.0.1,::1,192.168.0.0/16
SECURITY_LOG_FILE=logs/security.log
```

### Settings

The security middleware reads configuration from `apps/api/app/core/settings.py`:

```python
# Security Configuration
environment: str = Field(default="dev", description="Environment: dev, staging, or prod")
security_rate_limit_per_minute: int = Field(default=100, description="Requests per minute per IP")
security_penetration_attempts_threshold: int = Field(default=5, description="Failed attempts before ban")
security_ban_duration_minutes: int = Field(default=60, description="Ban duration in minutes")
security_dev_ip_whitelist: list[str] = Field(
    default=["127.0.0.1", "::1", "192.168.0.0/16"],
    description="IP whitelist for development environment"
)
security_log_file: str = Field(default="logs/security.log", description="Security events log file")
```

## Features

### 1. Rate Limiting

- **Limit**: 100 requests per minute per IP
- **Response**: HTTP 429 with `Retry-After` header
- **Storage**: Redis-based distributed counters

### 2. Penetration Detection

**Detected Patterns:**
- Directory traversal (`../../../etc/passwd`)
- SQL injection (`UNION SELECT`, `DROP TABLE`, etc.)
- XSS attempts (`<script>`, `javascript:`, etc.)
- HTTP method tunneling (`TRACE`, `CONNECT` with `*`)
- Large query strings (>1000 characters)
- Header injection attempts

**Response:**
- Auto-ban after 5 suspicious attempts
- 1-hour ban duration (configurable)
- 403 Forbidden response for banned IPs

### 3. IP Whitelisting

- **Development**: IPs in whitelist bypass all security checks
- **Production**: No whitelist, strict security enforcement
- **Configuration**: Comma-separated IPs/CIDR ranges

### 4. Security Logging

- **Location**: `logs/security.log`
- **Format**: Structured logging with IP, User-Agent, and event details
- **Events**:
  - `SECURITY_VIOLATION`: Rate limit or ban events
  - `SUSPICIOUS_ACTIVITY`: Detected attack patterns
  - `IP_BANNED`: IP address banned
  - `REQUEST_ALLOWED`: Successful requests (audit trail)

### 5. Redis Integration

**Security Keys:**
- `security:rate_limit:{ip}`: Rate limit counters (1-minute TTL)
- `security:ban:{ip}`: Banned IP addresses (configurable TTL)
- `security:failed_attempts:{ip}`: Failed attempt counters (1-hour TTL)

## Installation

1. **Install fastapi-guard**:
   ```bash
   pip install fastapi-guard==3.0.2
   ```

2. **Update dependencies** (already done):
   - Added `fastapi-guard==3.0.2` to `pyproject.toml`

3. **Configure environment**:
   - Set `ENVIRONMENT` variable
   - Configure Redis connection via `REDIS_URL`

## Usage

The security middleware is automatically integrated into `apps/api/app/main.py`:

```python
from .middleware.security import SecurityMiddleware

# Add security middleware first for comprehensive protection
app.add_middleware(SecurityMiddleware, settings=settings)
```

## Testing

### Automated Testing

Run the comprehensive security test suite:

```bash
# Test all security features
python scripts/test_security_middleware.py

# Expected output:
# ✅ All security middleware tests PASSED!
```

### Manual Testing

#### Test Rate Limiting

```bash
# Make 101 requests to trigger rate limiting
for i in {1..101}; do curl -s http://localhost:8000/health; done

# Check Redis for rate limit data
python scripts/check_redis_security.py
```

#### Test Penetration Detection

```bash
# Try malicious requests
curl "http://localhost:8000/../../../etc/passwd"
curl "http://localhost:8000/api/users<script>alert(1)</script>"
curl "http://localhost:8000/api/'; DROP TABLE users; --"

# Check if IP is banned
python scripts/check_redis_security.py
```

#### Test Redis Integration

```bash
# Check security keys in Redis
redis-cli KEYS "security:*"

# Clear security data (for testing)
python scripts/check_redis_security.py clear
```

### Security Log Monitoring

```bash
# Monitor security logs in real-time
tail -f logs/security.log

# Example log entry:
# 2024-01-15 10:30:45,123 - security - WARNING - Security event: SUSPICIOUS_ACTIVITY - IP: 192.168.1.100 - User-Agent: curl/7.68.0 - {'patterns': ['directory_traversal'], 'path': '/../../../etc/passwd', 'method': 'GET'}
```

## Security Headers

The middleware automatically adds security headers to all responses:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis is running
   - Check `REDIS_URL` in environment variables
   - Verify network connectivity

2. **Security Logs Not Created**
   - Check write permissions on `logs/` directory
   - Verify `SECURITY_LOG_FILE` path is correct

3. **IP Not Banned After Malicious Requests**
   - Check if IP is in development whitelist
   - Verify `ENVIRONMENT` is set to `prod` for strict mode
   - Check Redis connectivity

4. **Rate Limiting Not Working**
   - Verify Redis is accessible
   - Check `SECURITY_RATE_LIMIT_PER_MINUTE` setting
   - Ensure middleware is added to the app

### Debug Mode

Enable debug logging for security middleware:

```python
import logging
logging.getLogger("security").setLevel(logging.DEBUG)
```

## Production Deployment

### Security Checklist

- [ ] Set `ENVIRONMENT=prod`
- [ ] Remove development IP whitelist
- [ ] Configure production Redis instance
- [ ] Set up log rotation for `logs/security.log`
- [ ] Monitor security logs with alerting
- [ ] Regular security testing and penetration testing
- [ ] Keep fastapi-guard updated

### Monitoring

Monitor these metrics:

- Security violation events
- Banned IP addresses
- Rate limiting triggers
- Failed attempt patterns
- Redis security key counts

### Incident Response

1. **Security Violation Detected**:
   - Check security logs for details
   - Identify attack patterns
   - Review banned IPs
   - Update security rules if needed

2. **Distributed Attack**:
   - Check Redis for attack patterns across instances
   - Consider temporary rate limit increases
   - Implement additional firewall rules

## API Endpoints

The security middleware affects all API endpoints. Here are some endpoints you can use for testing:

- `GET /health` - Health check (good for rate limiting tests)
- `GET /docs` - API documentation
- `GET /openapi.json` - OpenAPI specification

## Contributing

When modifying security middleware:

1. Run all security tests
2. Update documentation
3. Test in all environments (dev, staging, prod)
4. Monitor performance impact
5. Review security implications

## License

This security implementation is part of the AgentFlow project.