# Security Configuration Guide

## Quick Start

### 1. Environment Setup

Create a `.env` file with the following security settings:

```bash
# Required Security Settings
SECRET_KEY=your-super-secure-jwt-secret-key-here
FERNET_KEY=your-fernet-encryption-key-here
REDIS_URL=redis://localhost:6379

# Security Configuration
ENVIRONMENT=production
SECURITY_RATE_LIMIT_PER_MINUTE=100
SECURITY_PENETRATION_ATTEMPTS_THRESHOLD=5
SECURITY_BAN_DURATION_MINUTES=60
SECURITY_LOG_FILE=logs/security.log

# Development Whitelist (remove in production)
SECURITY_DEV_IP_WHITELIST=["127.0.0.1", "::1"]
```

### 2. Generate Secure Keys

#### JWT Secret Key
```bash
# Generate a secure JWT secret (256 bits)
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Fernet Encryption Key
```bash
# Generate a Fernet key for encryption
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Redis Setup

Ensure Redis is running and accessible:

```bash
# Start Redis (if using Docker)
docker run -d -p 6379:6379 redis:alpine

# Test Redis connection
redis-cli ping
```

## Configuration Options

### Rate Limiting Configuration

```python
# apps/api/app/core/security_config.py
rate_limiting = RateLimitConfig(
    requests_per_minute=100,        # Requests per minute per IP
    burst_limit=10,                # Burst capacity
    window_seconds=60,             # Rate limit window
    strategy="sliding_window",     # sliding_window or fixed_window
    enable_redis=True,             # Use Redis for distributed limiting
    whitelist_ips=["127.0.0.1"]    # IPs to whitelist
)
```

### Security Monitoring Configuration

```python
# apps/api/app/core/security_config.py
monitoring = SecurityMonitoringConfig(
    enable_real_time_alerts=True,
    enable_anomaly_detection=False,
    metrics_retention_days=30,
    alert_thresholds={
        "rate_limit_exceeded": 5,
        "unauthorized_access": 3,
        "suspicious_login": 3,
        "sql_injection": 1,
        "xss_attempt": 3,
        "brute_force": 5,
        "dos_attack": 10
    }
)
```

### JWT Configuration

```python
# apps/api/app/core/security_config.py
jwt = JWTConfig(
    access_token_ttl_minutes=15,
    refresh_token_ttl_minutes=1440,  # 24 hours
    algorithm="HS256",
    enable_jti=True,
    enable_session_tracking=True,
    max_tokens_per_user=10
)
```

### OTP Configuration

```python
# apps/api/app/core/security_config.py
otp = OTPConfig(
    length=6,
    ttl_minutes=10,
    max_attempts=3,
    lockout_minutes=15
)
```

## Production Deployment

### 1. Security Headers

The application automatically includes security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

### 2. HTTPS Configuration

Ensure HTTPS is configured:

```nginx
# Nginx configuration example
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

### 3. Monitoring Setup

Configure monitoring and alerting:

```bash
# Set up log rotation
cat > /etc/logrotate.d/agentflow << EOF
/var/log/agentflow/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
EOF

# Configure monitoring alerts (example with Prometheus)
# Add security metrics to your monitoring stack
```

### 4. Backup and Recovery

```bash
# Backup encryption keys (secure location)
# Example: Store in a secure key vault
export FERNET_KEY=$(cat /secure/location/fernet_key.txt)
export SECRET_KEY=$(cat /secure/location/jwt_secret.txt)
```

## Security Testing

### 1. Configuration Validation

```python
# Test security configuration
from apps.api.app.core.security_config import get_security_config_manager
from apps.api.core.settings import get_settings

settings = get_settings()
config_manager = get_security_config_manager(settings)

# Validate configuration
issues = config_manager.validate_config()
if issues:
    print("Configuration issues:", issues)
else:
    print("Configuration is valid")
```

### 2. Health Check

```bash
# Check security system health
curl http://localhost:8000/security/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "encryption": {"configured": true, "key_available": true},
    "rate_limiting": {"configured": true, "redis_available": true},
    "monitoring": {"configured": true, "alerts_enabled": true},
    "jwt": {"configured": true, "secure_algorithm": true},
    "otp": {"configured": true, "secure_length": true}
  }
}
```

### 3. Security Testing Commands

```bash
# Test rate limiting
for i in {1..150}; do
  curl -s http://localhost:8000/health > /dev/null &
done

# Test suspicious patterns
curl "http://localhost:8000/api/endpoint?input=../../../etc/passwd"

# Check security logs
tail -f logs/security.log
```

## Troubleshooting

### Common Issues

1. **Rate Limiting Not Working**
   ```bash
   # Check Redis connectivity
   redis-cli ping

   # Check rate limiter status
   curl http://localhost:8000/security/rate-limit/status
   ```

2. **Encryption Errors**
   ```bash
   # Verify encryption key
   python -c "import os; print('FERNET_KEY set:', bool(os.getenv('FERNET_KEY')))"

   # Test encryption service
   curl http://localhost:8000/security/encryption/status
   ```

3. **Security Events Not Logging**
   ```bash
   # Check log file permissions
   ls -la logs/

   # Check logging configuration
   curl http://localhost:8000/security/config | jq .logging
   ```

### Log Analysis

```bash
# Search for security events
grep "SECURITY_VIOLATION" logs/security.log

# Count events by type
grep "event_type" logs/security.log | sort | uniq -c

# Monitor real-time security events
tail -f logs/security.log | grep --line-buffered "security"
```

## Performance Tuning

### Rate Limiting Optimization

```python
# Adjust based on your traffic patterns
rate_limiting = RateLimitConfig(
    requests_per_minute=1000,  # Increase for high-traffic APIs
    burst_limit=50,           # Allow larger bursts
    strategy="sliding_window" # Better for variable traffic
)
```

### Redis Optimization

```bash
# Redis configuration for security features
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

### Monitoring Performance

```python
# Reduce metrics retention for better performance
monitoring = SecurityMonitoringConfig(
    metrics_retention_days=7,  # Shorter retention
    enable_anomaly_detection=False  # Disable if not needed
)
```

## Compliance Checklists

### NIST CSF Compliance

- [ ] **Identify**: Security monitoring and logging implemented
- [ ] **Protect**: Encryption and access controls in place
- [ ] **Detect**: Threat detection and alerting configured
- [ ] **Respond**: Incident response procedures documented
- [ ] **Recover**: Backup and recovery procedures in place

### GDPR Compliance

- [ ] Data encryption implemented
- [ ] Access logging enabled
- [ ] Data minimization practices followed
- [ ] Breach notification procedures in place

### SOC 2 Compliance

- [ ] Security policies documented
- [ ] Access controls implemented
- [ ] Monitoring and alerting configured
- [ ] Audit logging enabled
- [ ] Incident response procedures documented

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review security logs for suspicious patterns
   - Check security metrics and alerts
   - Monitor rate limiting effectiveness

2. **Monthly**
   - Rotate encryption keys
   - Review and update alert thresholds
   - Test security incident response procedures

3. **Quarterly**
   - Security configuration review
   - Update security dependencies
   - Review and update security documentation

### Key Rotation

```python
# Rotate encryption keys
from apps.api.app.utils.encryption import EncryptionManager

# Generate new key
new_key = EncryptionManager.generate_key()

# Update environment variable
# IMPORTANT: Deploy new key to all instances before updating
os.environ['FERNET_KEY'] = new_key

# Update configuration
config_manager.update_config(encryption={'key_env_var': 'FERNET_KEY'})
```

## Support

For security-related issues or questions:

1. Check the security logs: `logs/security.log`
2. Review security metrics: `GET /security/metrics`
3. Validate configuration: `GET /security/validate`
4. Check system health: `GET /security/health`

For urgent security issues, contact the security team immediately.