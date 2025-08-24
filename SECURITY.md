# AgentFlow Security Architecture

## Overview

AgentFlow implements a comprehensive security architecture designed to protect against modern web application threats. This document provides detailed information about the security implementation, controls, and best practices.

## Security Architecture Overview

### Core Security Components

1. **Authentication & Authorization**
   - JWT-based authentication with access and refresh tokens
   - Two-factor authentication (TOTP) for enhanced security
   - Role-based access control (RBAC) for fine-grained permissions
   - Account lockout protection after failed attempts

2. **Data Protection**
   - AES-256 encryption for sensitive data at rest
   - Fernet symmetric encryption for OTP secrets
   - Secure key management with environment-based configuration

3. **Network & Infrastructure Security**
   - Docker container security with non-root users
   - Internal network isolation between services
   - Health checks and service dependencies

4. **Application Security**
   - Comprehensive security middleware with penetration detection
   - Rate limiting and IP banning for abuse protection
   - Security headers and CORS configuration
   - Input validation and output encoding

## Authentication & Authorization

### JWT Token Security

**Access Tokens:**
- Algorithm: HS256 (HMAC-SHA256)
- Expiration: 15 minutes (configurable)
- Includes JTI (JWT ID) for uniqueness
- Stored in Authorization header as Bearer token

**Refresh Tokens:**
- Expiration: 7 days (configurable)
- Blacklist mechanism for token revocation
- One-time use with rotation
- Secure storage in Redis with TTL

**Token Lifecycle:**
1. Client authenticates with email/password/OTP
2. Server issues access and refresh tokens
3. Client uses access token for API calls
4. When access token expires, client uses refresh token
5. Server validates refresh token and issues new tokens
6. Old refresh token is blacklisted

### Two-Factor Authentication (2FA)

**TOTP Implementation:**
- Uses pyotp library for RFC 6238 compliance
- 32-character base32 secret keys
- 6-digit codes with 30-second windows
- Secrets encrypted with Fernet before database storage

**2FA Flow:**
1. User registers with email and password
2. System generates TOTP secret and returns to client
3. Client configures authenticator app
4. Login requires email, password, and current TOTP code
5. System verifies TOTP code against stored secret

### Account Security

**Password Policy:**
- Minimum 12 characters (configurable)
- Requires uppercase and lowercase letters
- Requires at least one number
- Requires at least one special character
- Banned common passwords ("password", "123456", "qwerty")

**Account Lockout:**
- 5 failed login attempts trigger lockout
- 30-minute lockout duration (configurable)
- Automatic reset after successful login
- Failed attempt tracking with timestamps

**Session Management:**
- Last login timestamp tracking
- Concurrent session handling
- Secure logout with token blacklisting

### Role-Based Access Control (RBAC)

**Core Components:**
- Organizations, Roles, Users, Memberships
- Resource-based permissions (agents, memory, etc.)
- Action-based permissions (read, write, delete)

**Permission Model:**
```python
PermissionRequest = {
    user_id: UUID,
    organization_id: UUID,
    resource: str,  # "agents", "memory", etc.
    action: str     # "read", "write", "delete"
}
```

## Data Protection

### Encryption Implementation

**Fernet Encryption:**
- Symmetric encryption using AES-128-CBC + HMAC-SHA256
- 32-byte keys (256-bit security)
- Automatic key derivation with PBKDF2 when needed
- Base64 encoding for storage

**Key Management:**
- FERNET_KEY environment variable
- Automatic key generation for development
- Key validation on startup
- Secure key rotation support

**Encrypted Data:**
- OTP secrets (primary use case)
- Future expansion for other sensitive data
- Encryption/decryption utility functions

### Database Security

**User Model Security:**
- Password hashing with bcrypt
- Encrypted OTP secrets
- Audit timestamps (created_at, updated_at, last_login)
- Soft delete capability
- Account lockout tracking

**Security Fields:**
```sql
-- User table security fields
failed_login_attempts INTEGER DEFAULT 0
account_locked_until TIMESTAMP
last_login TIMESTAMP
deleted_at TIMESTAMP  -- Soft delete
otp_secret VARCHAR(255)  -- Encrypted
```

## Network & Infrastructure Security

### Docker Security

**Container Configuration:**
- Non-root user execution (UID 1000, 999, etc.)
- Minimal base images
- Health checks for all services
- Resource limits and constraints

**Service Isolation:**
- Internal Docker network (not exposed externally)
- Service-to-service communication only
- Database and Redis not directly accessible
- API gateway as single entry point

**Security Headers:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict CORS policy

### Infrastructure Components

**Database (PostgreSQL):**
- Connection pooling with limits
- Prepared statements
- Connection timeouts
- Health monitoring

**Cache (Redis):**
- In-memory storage with persistence
- Connection timeouts
- Password protection (configurable)
- Used for session storage and rate limiting

## Application Security Controls

### Security Middleware

**Core Features:**
- Rate limiting (100 requests/minute per IP)
- Penetration detection with pattern matching
- IP banning after suspicious activity
- Security event logging
- Development IP whitelisting

**Attack Detection Patterns:**
- Directory traversal (../, ..)
- SQL injection attempts
- Cross-site scripting (XSS) attempts
- HTTP method tunneling
- Large query strings
- Header injection attempts

**Rate Limiting:**
- Redis-backed distributed rate limiting
- Configurable limits per minute
- Automatic retry-after headers
- Burst capacity handling

**IP Banning:**
- Configurable threshold (3 attempts default)
- Configurable ban duration (5 minutes default)
- Redis-based ban storage
- Automatic cleanup with TTL

### Input Validation & Sanitization

**Request Processing:**
- FastAPI automatic validation
- Pydantic model validation
- Type hints enforcement
- Custom validation decorators

**Security Headers Validation:**
- Content-Type validation
- Content-Length limits
- User-Agent validation
- Origin and Referer checking

## Security Monitoring & Logging

### Security Event Logging

**Event Types:**
- SECURITY_VIOLATION: Rate limit exceeded, banned IPs
- SUSPICIOUS_ACTIVITY: Attack pattern detected
- REQUEST_ALLOWED: Successful security checks
- IP_BANNED: IP address banned
- SECURITY_ERROR: Middleware errors

**Log Format:**
```json
{
  "event_type": "SECURITY_VIOLATION",
  "ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "path": "/api/sensitive",
  "method": "POST",
  "timestamp": 1234567890.123,
  "details": {
    "reason": "rate_limited",
    "retry_after": 60
  }
}
```

### Security Metrics

**Monitoring Points:**
- Authentication success/failure rates
- Rate limiting events
- IP ban frequency
- Suspicious activity patterns
- Account lockouts

## Security Configuration

### Environment Variables

**Critical Security Settings:**
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secure-random-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption Keys
FERNET_KEY=your-base64-encoded-32-byte-key
ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# Security Limits
RATE_LIMIT_PER_MINUTE=100
SECURITY_MAX_FAILED_ATTEMPTS=5
SECURITY_LOCKOUT_DURATION_MINUTES=30

# Password Policy
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true
```

### Production Considerations

**Security Hardening:**
- Disable debug mode
- Use strong random keys
- Configure proper CORS origins
- Set appropriate timeouts
- Enable security headers
- Monitor security logs

## Security Testing

### Test Coverage

**Authentication Tests:**
- JWT token creation and validation
- Token expiration and refresh
- Account lockout mechanisms
- Password policy enforcement
- OTP secret encryption

**Middleware Tests:**
- Rate limiting functionality
- Penetration detection patterns
- IP banning mechanisms
- Security header validation
- Error handling

**Integration Tests:**
- Full authentication flows
- API endpoint security
- Concurrent request handling
- Redis connectivity issues

### Security Test Results

**Current Test Status:**
- ✅ Authentication flows tested
- ✅ Token security validated
- ✅ Encryption mechanisms verified
- ✅ Rate limiting functional
- ✅ Penetration detection working
- ✅ Account security enforced

## Compliance Considerations

### Security Standards

**OWASP Top 10 Coverage:**
- A01:2021 - Broken Access Control → RBAC implementation
- A02:2021 - Cryptographic Failures → Encryption implementation
- A03:2021 - Injection → Input validation and prepared statements
- A05:2021 - Security Misconfiguration → Secure defaults and validation
- A07:2021 - Identification and Authentication Failures → JWT + 2FA

**Data Protection:**
- Sensitive data encryption at rest
- Secure key management
- Access logging and monitoring
- Data minimization principles

## Security Maintenance

### Key Rotation

**Rotation Schedule:**
- JWT secret keys: Every 24 hours (configurable)
- Encryption keys: As needed for security incidents
- Database credentials: Regular rotation
- API keys: Immediate rotation on compromise

### Security Updates

**Dependency Management:**
- Regular security patch updates
- Dependency vulnerability scanning
- Automated security testing
- Security advisory monitoring

## Conclusion

AgentFlow implements a comprehensive security architecture that addresses modern web application security challenges. The multi-layered approach ensures protection against various attack vectors while maintaining usability and performance.

**Key Security Strengths:**
- Strong authentication with 2FA
- Comprehensive data encryption
- Advanced threat detection
- Robust access controls
- Security monitoring and logging
- Secure infrastructure design

**Continuous Improvement:**
- Regular security assessments
- Automated testing and monitoring
- Security patch management
- Threat intelligence integration