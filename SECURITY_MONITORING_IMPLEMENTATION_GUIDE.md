# Security Monitoring Implementation Guide for AgentFlow

## Document Information
- **Version**: 1.0
- **Date**: 2025-08-24
- **Author**: SPARC SRE Engineer
- **Purpose**: Complete implementation guide for production security monitoring

## Executive Summary

This implementation guide provides comprehensive instructions for deploying and managing the production-ready security monitoring framework for AgentFlow. The framework includes SLI/SLO definitions, error budget management, advanced alerting, security dashboards, and incident response playbooks.

## Architecture Overview

The security monitoring framework consists of the following components:

1. **Error Budget Management** (`error_budget_manager.py`)
   - Tracks error budgets for all security SLOs
   - Manages budget consumption and alerts
   - Provides budget status and reporting

2. **Security Alerting System** (`security_alerting.py`)
   - Multi-channel alert distribution
   - Alert correlation and deduplication
   - Escalation path management

3. **Security Dashboards** (`security_dashboards.py`)
   - Grafana dashboard configurations
   - Real-time and analytical views
   - Executive and operational dashboards

4. **Incident Response Playbooks** (`security_playbooks.py`)
   - Automated and manual response procedures
   - Incident lifecycle management
   - Evidence collection and documentation

5. **Central Configuration** (`security_monitoring_config.py`)
   - Unified configuration management
   - Environment-specific settings
   - Integration configurations

## Prerequisites

### System Requirements
- **Redis**: For caching, state management, and persistence
- **Prometheus**: For metrics collection and alerting
- **Grafana**: For dashboard visualization
- **Python 3.8+**: For running the monitoring components
- **SMTP Server**: For email alerting
- **Slack Workspace**: For team notifications

### Environment Variables
```bash
# Redis Configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=your_redis_password

# Alerting Configuration
export SLACK_SECURITY_WEBHOOK_URL=https://hooks.slack.com/services/...
export SMTP_SERVER=smtp.company.com
export SMTP_PORT=587
export SMTP_USERNAME=security@company.com
export SMTP_PASSWORD=your_smtp_password
export SECURITY_FROM_EMAIL=security@company.com

# PagerDuty Configuration (Optional)
export PAGERDUTY_API_KEY=your_pagerduty_api_key
export PAGERDUTY_SERVICE_ID=your_service_id

# SMS Configuration (Optional)
export TWILIO_ACCOUNT_SID=your_twilio_sid
export TWILIO_AUTH_TOKEN=your_twilio_token
export TWILIO_FROM_NUMBER=+1234567890
export SECURITY_ONCALL_PHONE=+1234567890

# Grafana Configuration (Optional)
export GRAFANA_URL=http://localhost:3000
export GRAFANA_API_KEY=your_grafana_api_key
export PROMETHEUS_DATASOURCE_UID=prometheus_uid

# SIEM Integration (Optional)
export SIEM_ENABLED=true
export SIEM_TYPE=splunk
export SIEM_HOST=splunk.company.com
export SIEM_PORT=8088
export SIEM_TOKEN=your_siem_token
```

## Installation and Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install redis aiohttp prometheus_client smtplib
pip install fastapi uvicorn  # If not already installed

# Install additional dependencies for integrations
pip install slack-sdk requests twilio  # For Slack, PagerDuty, SMS
```

### 2. Initialize Security Monitoring

```python
# apps/api/app/main.py or equivalent
from app.observability.error_budget_manager import initialize_error_budget_manager
from app.observability.security_alerting import initialize_alert_manager
from app.observability.security_dashboards import initialize_dashboards_manager
from app.incident_response.security_playbooks import initialize_incident_manager

# Initialize components
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Initialize all security monitoring components
error_budget_manager = await initialize_error_budget_manager(redis_client)
alert_manager = await initialize_alert_manager(redis_client, config)
dashboards_manager = await initialize_dashboards_manager(redis_client)
incident_manager = await initialize_incident_manager(redis_client, config)
```

### 3. Configure Prometheus Metrics

Add the following to your Prometheus configuration:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agentflow_security'
    static_configs:
      - targets: ['localhost:8000']  # Your FastAPI app
    metrics_path: '/metrics'
    scrape_interval: 15s

# Alerting rules
rule_files:
  - 'security_alerts.yml'
```

Create security alerting rules:

```yaml
# security_alerts.yml
groups:
  - name: security_alerts
    rules:
      - alert: AuthenticationFailureSpike
        expr: rate(jwt_validation_failed_total[5m]) > 50
        for: 5m
        labels:
          severity: high
        annotations:
          summary: "High rate of authentication failures"
          description: "More than 50 authentication failures in 5 minutes"

      - alert: RateLimitExceeded
        expr: rate(rate_limited_requests_total[5m]) > 1000
        for: 5m
        labels:
          severity: medium
        annotations:
          summary: "Rate limiting threshold exceeded"
          description: "More than 1000 requests rate limited in 5 minutes"
```

### 4. Set Up Grafana Dashboards

1. **Import Dashboard Templates**

```python
# Import dashboards programmatically
import json
from app.observability.security_dashboards import get_dashboards_manager

dashboards_manager = get_dashboards_manager()

# Export dashboard JSON for Grafana import
soc_dashboard = await dashboards_manager.get_dashboard('security_operations_center')
dashboard_json = await dashboards_manager.export_dashboard('security_operations_center')

# Save to file for manual import
with open('security_operations_center.json', 'w') as f:
    f.write(dashboard_json)
```

2. **Configure Data Sources**

Ensure the following data sources are configured in Grafana:
- **Prometheus**: For metrics data
- **Loki**: For log aggregation (optional)
- **PostgreSQL/MySQL**: For incident data (optional)

### 5. Configure Alert Webhooks

Set up webhooks in your monitoring system to trigger security alerts:

```python
# Webhook endpoint for receiving alerts
@app.post("/webhooks/security-alert")
async def security_alert_webhook(alert_data: dict):
    """Receive alerts from monitoring systems"""
    from app.observability.security_alerting import get_alert_manager

    alert_manager = get_alert_manager()

    # Create security alert from webhook data
    alert = SecurityAlert(
        type=alert_data.get('alertname', 'external_alert'),
        severity=AlertSeverity(alert_data.get('severity', 'medium')),
        title=alert_data.get('summary', 'External Alert'),
        description=alert_data.get('description', ''),
        source='prometheus',
        component=alert_data.get('job', 'unknown'),
        data=alert_data
    )

    # Process the alert
    alert_id = await alert_manager.process_alert(alert)

    return {"alert_id": alert_id, "status": "processed"}
```

## Security Monitoring Operations

### Daily Operations

#### Morning Security Check
```bash
# Run daily security check
python scripts/security/daily_security_check.py

# Check results
tail -f /var/log/agentflow/security.log
```

#### Dashboard Review
1. **Security Operations Center Dashboard**
   - Check current threat level
   - Review active alerts
   - Monitor authentication failure rates
   - Check rate limiting activity

2. **Error Budget Dashboard**
   - Review budget consumption
   - Check for budget warnings
   - Monitor burn rate trends

3. **Authentication Dashboard**
   - Review success rates
   - Check for geographic anomalies
   - Monitor session security

### Weekly Operations

#### Security Metrics Review
```python
# Generate weekly security report
python scripts/security/weekly_security_report.py

# Review alert effectiveness
python scripts/security/analyze_alert_effectiveness.py
```

#### Threat Intelligence Update
```python
# Update threat intelligence feeds
python scripts/security/update_threat_intel.py

# Review new indicators
python scripts/security/review_threat_indicators.py
```

### Monthly Operations

#### Error Budget Analysis
```python
# Analyze error budget consumption
python scripts/security/analyze_error_budgets.py

# Generate budget reports
python scripts/security/generate_budget_reports.py
```

#### Compliance Review
```python
# Run compliance checks
python scripts/security/compliance_check.py

# Generate compliance report
python scripts/security/compliance_report.py
```

## Incident Response Procedures

### 1. Incident Detection and Triage

#### Automated Detection
The system automatically detects security incidents through:
- **Prometheus Alerting Rules**: Pre-configured alert thresholds
- **Error Budget Monitoring**: SLO violation detection
- **Security Event Correlation**: Pattern-based detection

#### Manual Detection
Security team members can create incidents manually:

```python
from app.incident_response.security_playbooks import create_authentication_breach_incident

# Create incident for authentication breach
incident = await create_authentication_breach_incident(
    affected_users=25,
    breach_source="password_spraying"
)

# Execute automated response
actions = await incident_manager.execute_incident_response(incident)
```

### 2. Incident Response Workflow

#### Phase 1: Identification (0-30 minutes)
```python
# Update incident status
await incident_manager.update_incident_status(
    incident_id=incident.incident_id,
    status=IncidentStatus.INVESTIGATING,
    user="security_analyst",
    notes="Confirmed authentication breach pattern"
)

# Add evidence
await incident_manager.add_incident_evidence(
    incident_id=incident.incident_id,
    evidence_type="log_analysis",
    location="/var/log/auth.log",
    description="Authentication failure logs showing password spraying",
    collected_by="security_analyst"
)
```

#### Phase 2: Containment (30-120 minutes)
```python
# Update to contained status
await incident_manager.update_incident_status(
    incident_id=incident.incident_id,
    status=IncidentStatus.CONTAINED,
    user="security_team",
    notes="Blocked malicious IPs and reset affected passwords"
)

# Get manual response steps
playbook_steps = await incident_manager.get_incident_playbook_steps(incident.incident_id)
```

#### Phase 3: Eradication (2-24 hours)
```python
# Update to eradicated status
await incident_manager.update_incident_status(
    incident_id=incident.incident_id,
    status=IncidentStatus.ERADICATED,
    user="security_lead",
    notes="Identified and patched vulnerability in authentication system"
)
```

#### Phase 4: Recovery (4-48 hours)
```python
# Update to recovering status
await incident_manager.update_incident_status(
    incident_id=incident.incident_id,
    status=IncidentStatus.RECOVERING,
    user="platform_team",
    notes="Restoring authentication services with enhanced security"
)
```

#### Phase 5: Post-Incident (1-4 weeks)
```python
# Close incident with final documentation
await incident_manager.close_incident(
    incident_id=incident.incident_id,
    resolution_summary="Successfully contained and resolved authentication breach",
    lessons_learned=[
        "Implement stronger password policies",
        "Add geo-fencing for authentication",
        "Improve monitoring for password spraying patterns"
    ],
    prevention_recommendations=[
        "Deploy multi-factor authentication",
        "Implement account lockout policies",
        "Add behavioral analytics for authentication"
    ],
    closed_by="security_lead"
)
```

## Alert Management

### Creating Custom Alerts

```python
from app.observability.security_alerting import create_authentication_failure_alert

# Create alert for authentication failures
alert = await create_authentication_failure_alert(
    failures=75,
    time_window=5
)

# Process the alert
alert_id = await alert_manager.process_alert(alert)
```

### Managing Alert Escalation

```python
# Acknowledge alert
acknowledged = await alert_manager.acknowledge_alert(
    alert_id=alert_id,
    user="security_engineer"
)

# Resolve alert
resolved = await alert_manager.resolve_alert(
    alert_id=alert_id,
    user="security_engineer",
    resolution_notes="Blocked malicious IP addresses and reset passwords"
)
```

### Alert Correlation

The system automatically correlates related alerts:

```python
# Check for correlated alerts
correlated = await alert_manager.alert_correlator.correlate_alert(alert)

if correlated:
    # Handle correlated alert with higher severity
    escalated_alert = correlated
    await alert_manager.process_alert(escalated_alert)
```

## Error Budget Management

### Monitoring Budget Consumption

```python
from app.observability.error_budget_manager import get_error_budget_manager

# Get budget status
budget_manager = get_error_budget_manager()
budget_status = budget_manager.get_budget_status()

# Check specific SLO
auth_budget = budget_status.get('authentication_success_rate', {})
if auth_budget.get('is_warning'):
    print(f"Warning: Auth budget at {auth_budget['usage_percentage']:.1f}%")
```

### Manual Budget Management

```python
# Reset budget manually
await budget_manager.reset_budget('authentication_success_rate')

# Update budget configuration
await budget_manager.update_budget_configuration(
    'authentication_success_rate',
    {
        'warning_threshold': 0.8,
        'critical_threshold': 0.95
    }
)
```

### Budget Reporting

```python
# Generate budget report
budget_report = {
    'timestamp': datetime.utcnow().isoformat(),
    'budgets': budget_status,
    'recommendations': []
}

for slo_name, budget in budget_status.items():
    if budget['is_exceeded']:
        budget_report['recommendations'].append({
            'slo': slo_name,
            'issue': 'Budget exceeded',
            'action': 'Immediate reliability improvement required'
        })
    elif budget['is_warning']:
        budget_report['recommendations'].append({
            'slo': slo_name,
            'issue': 'Budget warning',
            'action': 'Consider optimization or budget increase'
        })
```

## Dashboard Management

### Creating Custom Dashboards

```python
from app.observability.security_dashboards import Dashboard, DashboardPanel

# Create custom dashboard
custom_dashboard = Dashboard(
    dashboard_id="custom_security_view",
    title="Custom Security View",
    description="Specialized security monitoring view",
    type=DashboardType.OPERATIONAL,
    tags=["custom", "security"],
    panels=[
        DashboardPanel(
            panel_id="custom_metric",
            title="Custom Security Metric",
            type="graph",
            targets=[{
                "expr": "rate(custom_security_metric_total[5m])",
                "legendFormat": "Custom Metric"
            }],
            grid_pos={"x": 0, "y": 0, "w": 12, "h": 8}
        )
    ]
)

# Save dashboard state
await dashboards_manager.save_dashboard_state(
    "custom_security_view",
    {"last_updated": datetime.utcnow().isoformat()}
)
```

### Dashboard Export/Import

```python
# Export dashboard for backup
dashboard_json = await dashboards_manager.export_dashboard('security_operations_center')

# Import dashboard from JSON
import json
dashboard_data = json.loads(dashboard_json)
# Import logic would go here
```

## Maintenance and Troubleshooting

### System Health Checks

```bash
# Check Redis connectivity
redis-cli ping

# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=up

# Check Grafana health
curl http://localhost:3000/api/health

# Check application health
curl http://localhost:8000/health
```

### Log Analysis

```bash
# Security event logs
tail -f /var/log/agentflow/security.log

# Application logs
tail -f /var/log/agentflow/application.log

# Alert logs
tail -f /var/log/agentflow/alerts.log
```

### Performance Optimization

#### Redis Optimization
```python
# Monitor Redis memory usage
redis-cli info memory

# Set appropriate memory limits
redis-cli config set maxmemory 2gb
redis-cli config set maxmemory-policy allkeys-lru
```

#### Prometheus Optimization
```yaml
# prometheus.yml optimizations
global:
  scrape_interval: 15s  # Balance between freshness and performance
  evaluation_interval: 15s

# Use remote write for long-term storage
remote_write:
  - url: "http://remote-storage:9201/write"
```

#### Alert Optimization
```python
# Reduce alert noise by adjusting thresholds
ALERT_THRESHOLDS['authentication_failure_spike']['condition'] = 'auth_failures > 100 AND time_window = 5min'

# Increase cool-down periods
ALERT_THRESHOLDS['rate_limit_exceeded']['cool_down'] = '1h'
```

## Compliance and Audit

### Audit Logging

All security monitoring activities are logged:

```python
# Security audit log entries
audit_logger.info({
    'event': 'alert_acknowledged',
    'alert_id': alert_id,
    'user': user,
    'timestamp': datetime.utcnow().isoformat(),
    'ip_address': client_ip
})
```

### Compliance Reporting

```python
# Generate compliance reports
from scripts.security.compliance_report import generate_compliance_report

# Monthly compliance report
report = generate_compliance_report(
    start_date=datetime.utcnow() - timedelta(days=30),
    end_date=datetime.utcnow(),
    standards=['NIST', 'ISO27001', 'GDPR']
)

# Export report
with open('compliance_report.json', 'w') as f:
    json.dump(report, f, indent=2)
```

## Integration Examples

### SIEM Integration

```python
# Send security events to SIEM
import json
from datetime import datetime

def send_to_siem(event_data: dict):
    """Send security event to SIEM system"""
    siem_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'agentflow_security_monitoring',
        'event_type': event_data.get('type'),
        'severity': event_data.get('severity'),
        'data': event_data
    }

    # Send to SIEM (implementation depends on SIEM type)
    if config.get('siem_enabled'):
        # Splunk HEC example
        headers = {
            'Authorization': f'Bearer {config["siem_token"]}',
            'Content-Type': 'application/json'
        }

        payload = {
            'event': siem_event,
            'index': config.get('siem_index', 'agentflow_security'),
            'sourcetype': 'agentflow_security'
        }

        # Send via HTTP
        # response = requests.post(f"{config['siem_host']}:{config['siem_port']}/services/collector", json=payload, headers=headers)
```

### SOAR Integration

```python
# Create incident in SOAR system
def create_soar_incident(incident_data: dict):
    """Create incident in SOAR system"""
    if not config.get('soar_enabled'):
        return

    soar_payload = {
        'name': incident_data.get('title'),
        'description': incident_data.get('description'),
        'severity': incident_data.get('severity'),
        'type': 'security_incident',
        'data': incident_data
    }

    headers = {
        'Authorization': f'Bearer {config["soar_api_key"]}',
        'Content-Type': 'application/json'
    }

    # Create incident via SOAR API
    # response = requests.post(f"{config['soar_url']}/api/incidents", json=soar_payload, headers=headers)
```

## Best Practices

### 1. Alert Tuning
- **Start Conservative**: Begin with higher thresholds and reduce gradually
- **Monitor False Positives**: Regularly review and tune alert rules
- **Use Alert Correlation**: Reduce noise by correlating related alerts
- **Set Appropriate Escalation**: Ensure alerts reach the right people at the right time

### 2. Error Budget Management
- **Monitor Regularly**: Check budget consumption daily
- **Plan for Budget Exhaustion**: Have action plans for when budgets are exceeded
- **Balance Reliability and Features**: Use error budgets to guide development priorities
- **Communicate Budget Status**: Keep stakeholders informed about budget health

### 3. Incident Response
- **Practice Regularly**: Conduct incident response drills quarterly
- **Keep Playbooks Updated**: Review and update playbooks after each incident
- **Document Everything**: Maintain detailed incident documentation
- **Learn and Improve**: Implement lessons learned from each incident

### 4. Dashboard Management
- **Keep Dashboards Focused**: Each dashboard should have a specific purpose
- **Use Consistent Metrics**: Standardize metric definitions across dashboards
- **Regular Review**: Update dashboards based on changing needs
- **Performance Monitoring**: Ensure dashboards don't impact system performance

## Troubleshooting Guide

### Common Issues

#### 1. High False Positive Rate
**Symptoms**: Too many alerts, security team alert fatigue
**Solutions**:
- Review and adjust alert thresholds
- Implement better alert correlation
- Use machine learning for anomaly detection
- Add more specific conditions to alert rules

#### 2. Error Budget Exceeded
**Symptoms**: Frequent SLO violations, error budget alerts
**Solutions**:
- Analyze root causes of errors
- Implement reliability improvements
- Consider increasing error budgets if appropriate
- Review service architecture for improvements

#### 3. Alert Delivery Failures
**Symptoms**: Alerts not reaching intended recipients
**Solutions**:
- Check webhook URLs and authentication
- Verify email server configuration
- Test SMS and phone integrations
- Review alert routing rules

#### 4. Dashboard Performance Issues
**Symptoms**: Slow dashboard loading, timeout errors
**Solutions**:
- Optimize Prometheus queries
- Reduce dashboard refresh rates
- Implement dashboard caching
- Use summary metrics for historical data

#### 5. Incident Response Delays
**Symptoms**: Slow incident response times, missed SLAs
**Solutions**:
- Review and optimize incident playbooks
- Improve alert triage processes
- Enhance team training and readiness
- Automate more response actions

### Debug Commands

```bash
# Check Redis connectivity and data
redis-cli --scan --pattern "security:*"

# Check Prometheus metrics
curl "http://localhost:9090/api/v1/query?query=security_alerts_active"

# Check application logs
tail -f /var/log/agentflow/security.log | grep ERROR

# Check alert system status
curl "http://localhost:8000/security/alerts/status"

# Check error budget status
curl "http://localhost:8000/security/budgets/status"

# Check incident status
curl "http://localhost:8000/security/incidents/active"
```

## Security Considerations

### 1. Data Protection
- All security monitoring data should be encrypted at rest
- Use TLS for all external communications
- Implement proper access controls for monitoring data
- Regularly rotate credentials and API keys

### 2. Access Control
- Implement role-based access to monitoring systems
- Use strong authentication for all monitoring interfaces
- Regularly review and audit access permissions
- Implement session management for monitoring consoles

### 3. Secure Configuration
- Store sensitive configuration in secure vaults
- Use environment variables for secrets
- Implement configuration validation
- Regular security scanning of monitoring components

### 4. Incident Response Security
- Secure incident response communication channels
- Implement secure evidence collection procedures
- Protect incident data with appropriate classification
- Implement secure incident data retention policies

## Conclusion

This implementation guide provides a comprehensive foundation for deploying and managing production-ready security monitoring for AgentFlow. The framework includes all necessary components for effective security operations, from basic monitoring to advanced incident response.

### Key Benefits
- **Comprehensive Coverage**: All security components monitored with appropriate SLIs/SLOs
- **Production Ready**: Designed for high availability and performance
- **Scalable**: Can handle enterprise-level security monitoring requirements
- **Automated**: Extensive automation reduces manual effort and errors
- **Integrated**: Works seamlessly with existing DevOps and security tooling

### Next Steps
1. **Deploy Core Components**: Start with error budget management and basic alerting
2. **Configure Dashboards**: Set up essential security dashboards
3. **Train Team**: Ensure security team is familiar with tools and procedures
4. **Tune and Optimize**: Continuously improve based on operational experience
5. **Expand Coverage**: Add additional security monitoring as needed

### Support and Resources
- **Documentation**: Comprehensive documentation in the implementation files
- **Playbooks**: Detailed incident response playbooks for common scenarios
- **Configuration**: Extensive configuration options for different environments
- **Integration**: Support for major security and monitoring platforms

The security monitoring framework is designed to evolve with your security needs, providing a solid foundation that can be extended and customized as your security posture matures.