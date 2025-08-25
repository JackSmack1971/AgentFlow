"""
Security Monitoring Configuration for AgentFlow
Central configuration for all security monitoring components
"""

import os
from typing import Dict, List, Any

# Security Monitoring Configuration
SECURITY_MONITORING_CONFIG = {
    'redis': {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0)),
        'password': os.getenv('REDIS_PASSWORD', None),
        'key_prefix': 'agentflow:security:'
    },

    'alerting': {
        'slack': {
            'webhook_url': os.getenv('SLACK_SECURITY_WEBHOOK_URL'),
            'channels': {
                'critical': '#security-critical',
                'high': '#security-incidents',
                'medium': '#security-monitoring',
                'low': '#security-logs'
            },
            'username': 'AgentFlow Security Alert System',
            'icon_emoji': ':warning:'
        },
        'email': {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.company.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_address': os.getenv('SECURITY_FROM_EMAIL', 'security@company.com'),
            'recipients': {
                'security_team': ['security-team@company.com'],
                'security_lead': ['security-lead@company.com'],
                'management': ['security-management@company.com']
            }
        },
        'pagerduty': {
            'api_key': os.getenv('PAGERDUTY_API_KEY'),
            'service_id': os.getenv('PAGERDUTY_SERVICE_ID'),
            'escalation_policy_id': os.getenv('PAGERDUTY_ESCALATION_POLICY_ID')
        },
        'sms': {
            'provider': os.getenv('SMS_PROVIDER', 'twilio'),
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'from_number': os.getenv('TWILIO_FROM_NUMBER'),
            'recipients': {
                'security_oncall': [os.getenv('SECURITY_ONCALL_PHONE')],
                'security_lead': [os.getenv('SECURITY_LEAD_PHONE')]
            }
        },
        'webhook': {
            'url': os.getenv('SECURITY_WEBHOOK_URL'),
            'headers': {
                'Authorization': f"Bearer {os.getenv('SECURITY_WEBHOOK_TOKEN', '')}",
                'Content-Type': 'application/json'
            }
        }
    },

    'error_budget': {
        'monthly_reset_day': 1,
        'budgets': {
            'authentication_success_rate': {
                'target': 0.9995,  # 99.95%
                'monthly_budget_minutes': 21.56,
                'warning_threshold': 0.75,
                'critical_threshold': 0.9
            },
            'token_validation_latency': {
                'target': 0.1,  # 100ms - hard limit
                'monthly_budget_minutes': 0,
                'warning_threshold': 1.0,
                'critical_threshold': 1.0
            },
            'threat_detection_time': {
                'target': 30.0,  # 30 seconds - hard limit
                'monthly_budget_minutes': 0,
                'warning_threshold': 1.0,
                'critical_threshold': 1.0
            },
            'injection_prevention': {
                'target': 1.0,  # 100% - zero tolerance
                'monthly_budget_count': 0,
                'warning_threshold': 1.0,
                'critical_threshold': 1.0
            },
            'rate_limiting_effectiveness': {
                'target': 0.999,
                'monthly_budget_minutes': 43.2,
                'warning_threshold': 0.75,
                'critical_threshold': 0.9
            },
            'file_validation_accuracy': {
                'target': 0.9995,
                'monthly_budget_minutes': 21.56,
                'warning_threshold': 0.75,
                'critical_threshold': 0.9
            },
            'security_event_ingestion': {
                'target': 0.9999,
                'monthly_budget_minutes': 4.32,
                'warning_threshold': 0.75,
                'critical_threshold': 0.9
            }
        }
    },

    'dashboards': {
        'grafana': {
            'url': os.getenv('GRAFANA_URL', 'http://localhost:3000'),
            'api_key': os.getenv('GRAFANA_API_KEY'),
            'folder_id': os.getenv('GRAFANA_SECURITY_FOLDER_ID'),
            'datasources': {
                'prometheus': os.getenv('PROMETHEUS_DATASOURCE_UID'),
                'loki': os.getenv('LOKI_DATASOURCE_UID')
            }
        },
        'refresh_intervals': {
            'real_time': '10s',
            'operational': '30s',
            'analytical': '1m',
            'executive': '5m'
        }
    },

    'metrics': {
        'prometheus': {
            'pushgateway_url': os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091'),
            'job_name': 'agentflow_security'
        },
        'collection_interval': 15,  # seconds
        'retention_days': 90
    },

    'logging': {
        'security_log_file': '/var/log/agentflow/security.log',
        'max_file_size': 100 * 1024 * 1024,  # 100MB
        'backup_count': 10,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'log_levels': {
            'security_events': 'INFO',
            'alerts': 'WARNING',
            'incidents': 'ERROR'
        }
    },

    'incident_response': {
        'playbooks_path': '/opt/agentflow/playbooks',
        'evidence_storage_path': '/var/agentflow/security/evidence',
        'forensic_tools': [
            'tcpdump',
            'wireshark',
            'volatility',
            'autopsy'
        ],
        'communication_templates': {
            'customer_notification': 'templates/customer_breach_notification.txt',
            'regulatory_report': 'templates/regulatory_breach_report.txt',
            'internal_update': 'templates/internal_incident_update.txt'
        }
    },

    'threat_intelligence': {
        'feeds': [
            {
                'name': 'AlienVault OTX',
                'url': 'https://otx.alienvault.com/api/v1/indicators/export',
                'api_key': os.getenv('ALIENVAULT_API_KEY'),
                'update_interval_hours': 6
            },
            {
                'name': 'MISP',
                'url': os.getenv('MISP_URL'),
                'api_key': os.getenv('MISP_API_KEY'),
                'update_interval_hours': 12
            }
        ],
        'local_cache_path': '/var/agentflow/security/threat_intel',
        'cache_expiry_days': 7
    },

    'compliance': {
        'standards': ['NIST', 'ISO27001', 'GDPR', 'SOX', 'PCI-DSS'],
        'audit_log_retention_days': 365 * 7,  # 7 years
        'evidence_retention_days': 365 * 3,  # 3 years
        'reporting_schedule': {
            'monthly_compliance_report': '1st of month',
            'quarterly_audit': '1st of quarter',
            'annual_assessment': 'January 1st'
        }
    },

    'automation': {
        'daily_security_check': {
            'enabled': True,
            'schedule': '02:00',  # 2 AM daily
            'timeout_minutes': 30
        },
        'weekly_security_review': {
            'enabled': True,
            'schedule': 'sunday 03:00',  # Sunday 3 AM
            'timeout_minutes': 120
        },
        'monthly_compliance_check': {
            'enabled': True,
            'schedule': '1st 04:00',  # 1st of month 4 AM
            'timeout_minutes': 240
        }
    },

    'integrations': {
        'siem': {
            'enabled': os.getenv('SIEM_ENABLED', 'false').lower() == 'true',
            'type': os.getenv('SIEM_TYPE', 'splunk'),
            'host': os.getenv('SIEM_HOST'),
            'port': int(os.getenv('SIEM_PORT', 8088)),
            'token': os.getenv('SIEM_TOKEN'),
            'index': os.getenv('SIEM_INDEX', 'agentflow_security')
        },
        'soar': {
            'enabled': os.getenv('SOAR_ENABLED', 'false').lower() == 'true',
            'type': os.getenv('SOAR_TYPE', 'demisto'),
            'url': os.getenv('SOAR_URL'),
            'api_key': os.getenv('SOAR_API_KEY'),
            'incident_webhook': os.getenv('SOAR_INCIDENT_WEBHOOK')
        },
        'edr': {
            'enabled': os.getenv('EDR_ENABLED', 'false').lower() == 'true',
            'type': os.getenv('EDR_TYPE', 'crowdstrike'),
            'url': os.getenv('EDR_URL'),
            'client_id': os.getenv('EDR_CLIENT_ID'),
            'client_secret': os.getenv('EDR_CLIENT_SECRET')
        }
    }
}

# Alert Thresholds Configuration
ALERT_THRESHOLDS = {
    # Authentication Alerts
    'authentication_failure_spike': {
        'condition': 'auth_failures > 50 AND time_window = 5min',
        'severity': 'high',
        'cool_down': '10min',
        'channels': ['slack', 'email'],
        'auto_actions': ['enable_enhanced_monitoring']
    },
    'token_validation_failure_rate': {
        'condition': 'token_validation_failure_rate > 0.1 AND time_window = 5min',
        'severity': 'high',
        'cool_down': '15min',
        'channels': ['slack', 'email', 'pagerduty'],
        'auto_actions': ['isolate_auth_service']
    },
    'suspicious_geographic_login': {
        'condition': 'geographic_anomaly_detected = true',
        'severity': 'medium',
        'cool_down': '30min',
        'channels': ['slack'],
        'auto_actions': ['log_suspicious_activity']
    },

    # Injection Prevention Alerts
    'prompt_injection_spike': {
        'condition': 'prompt_injection_attempts > 10 AND time_window = 10min',
        'severity': 'high',
        'cool_down': '15min',
        'channels': ['slack', 'email'],
        'auto_actions': ['update_security_patterns']
    },
    'sql_injection_attempt': {
        'condition': 'sql_injection_detected = true',
        'severity': 'critical',
        'cool_down': '5min',
        'channels': ['pagerduty', 'slack', 'sms'],
        'auto_actions': ['block_attack_source', 'isolate_affected_systems']
    },
    'xss_attempt_detected': {
        'condition': 'xss_attempts > 5 AND time_window = 10min',
        'severity': 'high',
        'cool_down': '15min',
        'channels': ['slack', 'email'],
        'auto_actions': ['update_input_validation']
    },

    # Rate Limiting Alerts
    'rate_limit_exceeded': {
        'condition': 'rate_limited_requests > 1000 AND time_window = 5min',
        'severity': 'medium',
        'cool_down': '30min',
        'channels': ['slack'],
        'auto_actions': ['analyze_traffic_pattern']
    },
    'dos_attack_pattern': {
        'condition': 'dos_pattern_detected = true',
        'severity': 'high',
        'cool_down': '10min',
        'channels': ['slack', 'email', 'pagerduty'],
        'auto_actions': ['enable_dos_protection', 'block_attack_sources']
    },
    'legitimate_traffic_blocked': {
        'condition': 'legitimate_requests_blocked > 10 AND time_window = 5min',
        'severity': 'medium',
        'cool_down': '15min',
        'channels': ['slack'],
        'auto_actions': ['adjust_rate_limits']
    },

    # File Security Alerts
    'malicious_file_detected': {
        'condition': 'malicious_files > 5 AND time_window = 15min',
        'severity': 'high',
        'cool_down': '30min',
        'channels': ['slack', 'email'],
        'auto_actions': ['quarantine_files', 'update_file_signatures']
    },
    'file_validation_failure': {
        'condition': 'file_validation_errors > 10 AND time_window = 10min',
        'severity': 'medium',
        'cool_down': '20min',
        'channels': ['slack'],
        'auto_actions': ['analyze_validation_failures']
    },

    # Error Budget Alerts
    'error_budget_warning': {
        'condition': 'error_budget_usage_percent > 75',
        'severity': 'medium',
        'cool_down': '1h',
        'channels': ['slack', 'email'],
        'auto_actions': ['create_budget_review_ticket']
    },
    'error_budget_critical': {
        'condition': 'error_budget_usage_percent > 90',
        'severity': 'high',
        'cool_down': '30min',
        'channels': ['slack', 'email', 'pagerduty'],
        'auto_actions': ['create_urgent_budget_review', 'notify_management']
    },
    'error_budget_exceeded': {
        'condition': 'error_budget_usage_percent > 100',
        'severity': 'critical',
        'cool_down': '15min',
        'channels': ['pagerduty', 'slack', 'sms', 'phone'],
        'auto_actions': ['trigger_slo_violation_process', 'notify_executive_team']
    },

    # Monitoring System Alerts
    'security_event_ingestion_failure': {
        'condition': 'event_ingestion_success_rate < 0.999 AND time_window = 5min',
        'severity': 'high',
        'cool_down': '10min',
        'channels': ['slack', 'email'],
        'auto_actions': ['check_ingestion_pipeline', 'restart_failed_services']
    },
    'high_false_positive_rate': {
        'condition': 'false_positive_rate > 0.1 AND time_window = 15min',
        'severity': 'medium',
        'cool_down': '30min',
        'channels': ['slack'],
        'auto_actions': ['review_alert_rules', 'update_detection_logic']
    }
}

# SLI Definitions
SLI_DEFINITIONS = {
    'authentication_success_rate': {
        'description': 'Percentage of successful authentication attempts',
        'query': 'rate(jwt_validation_total[5m]) / rate(jwt_validation_total[5m]) * 100',
        'target': 99.95,
        'error_budget': '21.56 minutes/month'
    },
    'token_validation_latency_p95': {
        'description': '95th percentile token validation latency',
        'query': 'histogram_quantile(0.95, rate(jwt_validation_duration_bucket[5m]))',
        'target': 100,  # milliseconds
        'error_budget': 'hard limit'
    },
    'threat_detection_time': {
        'description': 'Average time to detect security threats',
        'query': 'avg(threat_detection_time)',
        'target': 30,  # seconds
        'error_budget': 'hard limit'
    },
    'injection_prevention_accuracy': {
        'description': 'Accuracy of injection attack prevention',
        'query': '(blocked_injection_attempts / total_injection_attempts) * 100',
        'target': 100.0,
        'error_budget': 'zero tolerance'
    },
    'rate_limiting_effectiveness': {
        'description': 'Effectiveness of rate limiting in preventing abuse',
        'query': '(rate_limited_abusive_requests / total_abusive_requests) * 100',
        'target': 99.9,
        'error_budget': '43.2 minutes/month'
    },
    'file_validation_accuracy': {
        'description': 'Accuracy of malicious file detection',
        'query': '(detected_malicious_files / total_malicious_files) * 100',
        'target': 99.95,
        'error_budget': '21.56 minutes/month'
    },
    'security_event_ingestion_success': {
        'description': 'Success rate of security event ingestion',
        'query': '(successful_event_ingestion / total_event_ingestion) * 100',
        'target': 99.99,
        'error_budget': '4.32 minutes/month'
    }
}

# Monitoring Dashboard Templates
DASHBOARD_TEMPLATES = {
    'security_operations_center': {
        'title': 'Security Operations Center',
        'description': 'Real-time security monitoring and operations',
        'panels': [
            {'id': 'threat_level', 'title': 'Current Threat Level', 'type': 'stat'},
            {'id': 'active_alerts', 'title': 'Active Security Alerts', 'type': 'stat'},
            {'id': 'auth_failures', 'title': 'Authentication Failures (5min)', 'type': 'graph'},
            {'id': 'rate_limiting', 'title': 'Rate Limiting Activity', 'type': 'graph'},
            {'id': 'security_events', 'title': 'Security Events Timeline', 'type': 'graph'},
            {'id': 'top_attack_sources', 'title': 'Top Attack Sources', 'type': 'table'},
            {'id': 'error_budget_status', 'title': 'Error Budget Status', 'type': 'table'}
        ],
        'refresh_interval': '10s',
        'time_range': 'now-1h'
    },
    'authentication_monitoring': {
        'title': 'Authentication Security Monitoring',
        'description': 'Comprehensive authentication security monitoring',
        'panels': [
            {'id': 'auth_success_rate', 'title': 'Authentication Success Rate', 'type': 'stat'},
            {'id': 'token_validation_latency', 'title': 'Token Validation Latency', 'type': 'graph'},
            {'id': 'failed_logins_by_ip', 'title': 'Failed Logins by IP', 'type': 'table'},
            {'id': 'session_hijacking', 'title': 'Session Hijacking Attempts', 'type': 'graph'},
            {'id': 'geographic_anomalies', 'title': 'Geographic Anomalies', 'type': 'heatmap'}
        ],
        'refresh_interval': '30s',
        'time_range': 'now-6h'
    },
    'error_budget_monitoring': {
        'title': 'Error Budget Monitoring',
        'description': 'Monitor error budget consumption across security SLOs',
        'panels': [
            {'id': 'budget_usage_overview', 'title': 'Error Budget Usage Overview', 'type': 'bargauge'},
            {'id': 'budget_remaining', 'title': 'Remaining Error Budget', 'type': 'table'},
            {'id': 'budget_burn_rate', 'title': 'Error Budget Burn Rate', 'type': 'graph'},
            {'id': 'budget_alerts', 'title': 'Error Budget Alerts', 'type': 'stat'},
            {'id': 'budget_status', 'title': 'Budget Status', 'type': 'stat'}
        ],
        'refresh_interval': '1m',
        'time_range': 'now-24h'
    },
    'executive_security_summary': {
        'title': 'Executive Security Summary',
        'description': 'High-level security metrics for executive review',
        'panels': [
            {'id': 'security_health_score', 'title': 'Security Health Score', 'type': 'stat'},
            {'id': 'active_incidents', 'title': 'Active Security Incidents', 'type': 'stat'},
            {'id': 'mttr_trend', 'title': 'Mean Time to Resolution', 'type': 'graph'},
            {'id': 'slo_compliance', 'title': 'SLO Compliance Overview', 'type': 'bargauge'},
            {'id': 'security_investments', 'title': 'Security Investment ROI', 'type': 'table'}
        ],
        'refresh_interval': '5m',
        'time_range': 'now-30d'
    }
}

def get_security_config() -> Dict[str, Any]:
    """Get the complete security monitoring configuration"""
    return SECURITY_MONITORING_CONFIG

def get_alert_thresholds() -> Dict[str, Any]:
    """Get alert thresholds configuration"""
    return ALERT_THRESHOLDS

def get_sli_definitions() -> Dict[str, Any]:
    """Get SLI definitions"""
    return SLI_DEFINITIONS

def get_dashboard_templates() -> Dict[str, Any]:
    """Get dashboard templates"""
    return DASHBOARD_TEMPLATES

def validate_configuration() -> List[str]:
    """Validate security monitoring configuration"""
    errors = []

    # Check required environment variables
    required_vars = [
        'REDIS_HOST',
        'SLACK_SECURITY_WEBHOOK_URL',
        'SMTP_USERNAME',
        'SMTP_PASSWORD'
    ]

    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")

    # Check configuration consistency
    if SECURITY_MONITORING_CONFIG['error_budget']['monthly_reset_day'] not in range(1, 29):
        errors.append("Monthly reset day must be between 1 and 28")

    # Validate alert thresholds
    for alert_name, config in ALERT_THRESHOLDS.items():
        if 'condition' not in config:
            errors.append(f"Alert {alert_name} missing condition")
        if 'severity' not in config:
            errors.append(f"Alert {alert_name} missing severity")
        if config.get('severity') not in ['low', 'medium', 'high', 'critical']:
            errors.append(f"Alert {alert_name} has invalid severity")

    return errors