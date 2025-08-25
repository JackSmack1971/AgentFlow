# Test Environment Access Guide

## Document Information
- **Version**: 1.0
- **Date**: 2025-08-24
- **Classification**: CONFIDENTIAL
- **Document Status**: ACTIVE

## 1. Environment Overview

### 1.1 Testing Environments

**Primary Production Environment:**
- **API Endpoint:** `https://api.agentflow.com`
- **Web Application:** `https://app.agentflow.com`
- **Purpose:** Primary testing environment for external penetration testing

**Development Environment (Optional):**
- **API Endpoint:** `https://dev-api.agentflow.com`
- **Web Application:** `https://dev-app.agentflow.com`
- **Purpose:** Development testing and validation

### 1.2 Environment Specifications

**Production Environment:**
- **Platform:** Kubernetes cluster on AWS EKS
- **Region:** us-east-1
- **Load Balancer:** Application Load Balancer with WAF
- **CDN:** CloudFront with security headers
- **Database:** PostgreSQL with encryption at rest
- **Cache:** Redis cluster with TLS encryption

**Security Controls:**
- Web Application Firewall (AWS WAF)
- DDoS Protection (AWS Shield)
- Rate Limiting (Custom implementation)
- Security Monitoring (24/7)
- Automated Backups

## 2. Access Credentials and Authentication

### 2.1 Test Account Credentials

**Basic User Account:**
- **Username:** test_user_basic@agentflow.com
- **Password:** [Provided via secure channel]
- **Role:** Basic user with limited permissions
- **Permissions:**
  - Login to web application
  - Access basic RAG functionality
  - View user profile
  - Limited API access

**Administrator Account:**
- **Username:** test_user_admin@agentflow.com
- **Password:** [Provided via secure channel]
- **Role:** Administrator with elevated permissions
- **Permissions:**
  - Full system access
  - User management
  - System configuration
  - Administrative API access

**API Access:**
- **API Key:** [Provided via secure channel]
- **Secret:** [Provided via secure channel]
- **Scopes:** Full API access for testing
- **Rate Limit:** 1000 requests per minute

### 2.2 VPN Access (If Required)

**VPN Configuration:**
- **VPN Type:** OpenVPN
- **Server:** vpn.agentflow.com
- **Port:** 1194 (UDP)
- **Authentication:** Certificate-based
- **Network:** 10.0.100.0/24 (Testing network)

**VPN Client Setup:**
```bash
# Download OpenVPN configuration
wget https://vpn.agentflow.com/config/test-external.ovpn

# Install OpenVPN client
sudo apt-get install openvpn

# Connect to VPN
sudo openvpn --config test-external.ovpn
```

### 2.3 Multi-Factor Authentication

**MFA Setup:**
- **Type:** TOTP (Time-based One-Time Password)
- **App:** Google Authenticator, Authy, or similar
- **Backup Codes:** Provided for emergency access

**MFA Process:**
1. Enter username and password
2. Enter TOTP code from authenticator app
3. Access granted for 8 hours

## 3. API Endpoints and Testing Scope

### 3.1 Authentication Endpoints

**Core Authentication:**
```
POST /auth/login
POST /auth/logout
POST /auth/refresh
POST /auth/register
POST /auth/forgot-password
POST /auth/reset-password
```

**JWT Token Management:**
```
POST /auth/verify-token
POST /auth/revoke-token
GET  /auth/user-info
```

**OTP Management:**
```
POST /auth/enable-otp
POST /auth/verify-otp
POST /auth/disable-otp
```

### 3.2 RAG (Retrieval-Augmented Generation) Endpoints

**Core RAG Functionality:**
```
POST /rag/query
POST /rag/upload-document
GET  /rag/documents
DELETE /rag/documents/{id}
POST /rag/create-collection
GET  /rag/collections
```

**Advanced RAG Features:**
```
POST /rag/batch-query
POST /rag/semantic-search
GET  /rag/search-history
POST /rag/feedback
```

### 3.3 User Management Endpoints

**User Operations:**
```
GET    /users/profile
PUT    /users/profile
POST   /users/change-password
DELETE /users/account
```

**Administrative Operations:**
```
GET    /admin/users
POST   /admin/users
PUT    /admin/users/{id}
DELETE /admin/users/{id}
GET    /admin/roles
POST   /admin/roles
```

### 3.4 System Endpoints

**Health Checks:**
```
GET /health
GET /health/detailed
GET /metrics
```

**Configuration:**
```
GET  /config
POST /config/update
```

## 4. Testing Constraints and Limitations

### 4.1 Rate Limiting

**API Rate Limits:**
- **Per User:** 100 requests per minute
- **Per IP:** 1000 requests per minute
- **Global:** 10,000 requests per minute

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

**Rate Limit Response:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limit": 100,
  "remaining": 0
}
```

### 4.2 Account Lockout

**Lockout Policy:**
- **Failed Attempts:** 5 attempts within 15 minutes
- **Lockout Duration:** 15 minutes
- **Reset:** Automatic after lockout period

**Lockout Response:**
```json
{
  "error": "Account locked due to multiple failed attempts",
  "retry_after": 900,
  "unlock_time": "2025-08-24T23:15:00Z"
}
```

### 4.3 Data Protection

**Test Data Only:**
- Use only provided test accounts
- Do not create real user accounts
- Do not upload sensitive documents
- Do not test with real user data

**Data Sanitization:**
- All test data will be cleaned up after testing
- No persistent data should remain
- Database will be reset after testing completion

## 5. Security Monitoring and Alerting

### 5.1 Security Events Monitored

**Authentication Events:**
- Failed login attempts
- Account lockouts
- Suspicious login patterns
- Token revocation events

**API Security Events:**
- Rate limit violations
- SQL injection attempts
- XSS attack attempts
- Directory traversal attempts

**System Security Events:**
- High CPU/memory usage
- Unusual traffic patterns
- File upload anomalies
- Configuration changes

### 5.2 Alert Thresholds

**Critical Alerts (Immediate Notification):**
- Successful authentication bypass
- Data exfiltration
- Service disruption
- Critical vulnerability exploitation

**High Alerts (Within 4 hours):**
- Multiple failed login attempts
- Rate limit violations
- Suspicious API usage
- Configuration changes

**Medium Alerts (Daily Review):**
- Unusual traffic patterns
- Performance degradation
- Security control failures

### 5.3 Monitoring Dashboards

**Real-time Monitoring:**
- Security events dashboard: `https://monitoring.agentflow.com/security`
- API performance dashboard: `https://monitoring.agentflow.com/api`
- Authentication dashboard: `https://monitoring.agentflow.com/auth`

**Access Credentials:**
- Username: test_monitoring@agentflow.com
- Password: [Provided via secure channel]

## 6. Testing Tools and Resources

### 6.1 Approved Testing Tools

**Web Application Testing:**
- Burp Suite Professional
- OWASP ZAP
- Postman
- curl/wget

**API Testing:**
- Postman
- Insomnia
- REST Client extensions
- Custom Python scripts

**Network Testing:**
- Nmap
- Wireshark
- tcpdump
- netcat

### 6.2 Custom Testing Scripts

**Authentication Testing:**
```python
# JWT Token Testing Script
import requests
import jwt

# Test JWT token manipulation
def test_jwt_token_manipulation():
    # Implementation provided in testing scripts
    pass
```

**Rate Limiting Testing:**
```python
# Rate Limiting Bypass Testing
import requests
import time

def test_rate_limiting_bypass():
    # Implementation provided in testing scripts
    pass
```

### 6.3 Testing Libraries

**Python Libraries:**
```python
pip install requests
pip install jwt
pip install cryptography
pip install pyotp
pip install faker
```

**Node.js Libraries:**
```javascript
npm install axios
npm install jsonwebtoken
npm install crypto-js
npm install speakeasy
```

## 7. Emergency Procedures

### 7.1 Emergency Stop

**Emergency Contact:**
- **Phone:** +1 (555) 123-4567
- **Email:** security-emergency@agentflow.com
- **Slack:** #security-emergency

**Emergency Stop Procedure:**
1. Call emergency phone number
2. State: "EMERGENCY STOP - PENETRATION TESTING"
3. Provide your name and organization
4. Explain the emergency situation
5. Wait for confirmation

### 7.2 Service Disruption

**If Service is Disrupted:**
1. Stop all testing activities immediately
2. Notify emergency contact
3. Document the incident
4. Wait for service restoration
5. Resume testing only after approval

**Service Restoration:**
- Automatic monitoring will detect service restoration
- Testing can resume after notification
- Additional safeguards may be implemented

### 7.3 Data Breach Response

**If Data Exposure is Suspected:**
1. Stop all testing immediately
2. Notify emergency contact
3. Preserve evidence
4. Do not delete or modify any data
5. Wait for forensic investigation

## 8. Documentation and Reporting

### 8.1 Testing Documentation

**Required Documentation:**
- Daily testing logs
- Vulnerability findings
- Proof of concept code
- Screenshots and network captures
- Tool output and scan results

**Documentation Standards:**
- Timestamp all activities
- Document all findings with evidence
- Include affected endpoints and parameters
- Provide step-by-step reproduction steps

### 8.2 Report Templates

**Vulnerability Report Template:**
```markdown
# Vulnerability Report

## Vulnerability Details
- **Title:** [Vulnerability Title]
- **Severity:** [Critical/High/Medium/Low]
- **CVSS Score:** [Score]
- **Affected Endpoint:** [URL/Endpoint]
- **Parameter:** [Affected Parameter]

## Description
[Detailed description of the vulnerability]

## Proof of Concept
[Step-by-step reproduction steps]

## Impact
[Potential impact and consequences]

## Remediation
[Recommended remediation steps]

## References
[External references and standards]
```

### 8.3 Evidence Collection

**Evidence Types:**
- Screenshots of successful exploitation
- Network traffic captures (PCAP files)
- Application logs
- Database query results
- File system access proof

**Evidence Storage:**
- Encrypt all evidence files
- Use secure file transfer methods
- Maintain chain of custody
- Document evidence collection process

## 9. Communication Channels

### 9.1 Primary Communication

**Email:**
- General: security-testing@agentflow.com
- Emergency: security-emergency@agentflow.com
- Technical: security-tech@agentflow.com

**Phone:**
- Emergency: +1 (555) 123-4567
- Technical Support: +1 (555) 123-4568

**Slack:**
- General: #external-pentest
- Emergency: #security-emergency
- Technical: #security-tech

### 9.2 Communication Schedule

**Daily Communication:**
- Progress updates by 17:00 UTC
- Critical finding notifications (immediate)
- Emergency notifications (immediate)

**Weekly Communication:**
- Monday 10:00 UTC: Weekly status meeting
- Friday 15:00 UTC: End-of-week summary

**Meeting Information:**
- **Video Conference:** Zoom link provided
- **Meeting ID:** [Provided via secure channel]
- **Password:** [Provided via secure channel]

## 10. Support Resources

### 10.1 Technical Support

**Support Hours:**
- Monday - Friday: 09:00 - 18:00 UTC
- Emergency: 24/7

**Support Contacts:**
- **Project Manager:** Sarah Chen - sarah.chen@agentflow.com
- **Technical Lead:** Michael Rodriguez - michael.rodriguez@agentflow.com
- **Security Lead:** Dr. Emily Watson - emily.watson@agentflow.com

### 10.2 Documentation Resources

**API Documentation:**
- Swagger UI: `https://api.agentflow.com/docs`
- OpenAPI Spec: `https://api.agentflow.com/openapi.json`
- Authentication Guide: `https://docs.agentflow.com/auth`

**Security Documentation:**
- Security Architecture: `https://docs.agentflow.com/security/architecture`
- API Security: `https://docs.agentflow.com/security/api`
- Authentication Security: `https://docs.agentflow.com/security/auth`

### 10.3 Testing Resources

**Test Scripts Repository:**
- GitHub: `https://github.com/agentflow/security-testing`
- Access: Provided via secure channel
- Credentials: [Provided via secure channel]

**Testing Tools:**
- Burp Suite configurations
- Custom testing scripts
- Automated test suites

## 11. Environment Cleanup

### 11.1 Post-Testing Cleanup

**Account Cleanup:**
- All test accounts will be disabled
- Passwords will be changed
- API keys will be revoked
- Session data will be cleared

**Data Cleanup:**
- All test data will be removed
- Database will be reset to clean state
- File uploads will be deleted
- Cache data will be cleared

**Log Cleanup:**
- Testing-related logs will be archived
- Security events will be preserved
- Audit trails will be maintained

### 11.2 Final Verification

**Cleanup Verification:**
- Security team will verify all cleanup activities
- Independent audit of environment state
- Confirmation of no residual test data
- Validation of security control restoration

## 12. Appendix

### 12.1 Glossary

**Terms and Definitions:**
- **RAG:** Retrieval-Augmented Generation
- **JWT:** JSON Web Token
- **OTP:** One-Time Password
- **MFA:** Multi-Factor Authentication
- **API:** Application Programming Interface
- **WAF:** Web Application Firewall
- **DDoS:** Distributed Denial of Service

### 12.2 Acronyms

**Common Acronyms:**
- **OSCP:** Offensive Security Certified Professional
- **OWASP:** Open Web Application Security Project
- **NIST:** National Institute of Standards and Technology
- **CVSS:** Common Vulnerability Scoring System
- **SLA:** Service Level Agreement
- **VPN:** Virtual Private Network

### 12.3 Contact Information

**AgentFlow Security Team:**
- **Security Director:** Dr. Emily Watson
  - Email: emily.watson@agentflow.com
  - Phone: +1 (555) 123-4567

- **Security Architect:** Michael Rodriguez
  - Email: michael.rodriguez@agentflow.com
  - Phone: +1 (555) 123-4568

- **Security Engineer:** Sarah Chen
  - Email: sarah.chen@agentflow.com
  - Phone: +1 (555) 123-4569

---

**Document Classification: CONFIDENTIAL**
**Distribution: Limited to authorized testing personnel**
**Effective Date: 2025-08-24**
**Review Date: 2025-09-24**