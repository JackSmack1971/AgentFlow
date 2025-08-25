"""
Security Monitoring Dashboards for AgentFlow
Production-ready dashboard configurations for security monitoring and visualization
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis

class DashboardType(Enum):
    """Dashboard types"""
    REAL_TIME = "real_time"
    ANALYTICS = "analytics"
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"

class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class DashboardPanel:
    """Dashboard panel configuration"""
    panel_id: str
    title: str
    type: str  # 'graph', 'stat', 'table', 'heatmap'
    targets: List[Dict[str, Any]]
    grid_pos: Dict[str, int]
    options: Dict[str, Any] = None
    field_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.options is None:
            self.options = {}
        if self.field_config is None:
            self.field_config = {}

@dataclass
class Dashboard:
    """Dashboard configuration"""
    dashboard_id: str
    title: str
    description: str
    type: DashboardType
    tags: List[str]
    panels: List[DashboardPanel]
    time_range: str = "now-1h"
    refresh_interval: str = "30s"
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class SecurityDashboardsManager:
    """
    Production-ready security dashboards manager
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.dashboards = {}
        self._initialize_dashboards()

    def _initialize_dashboards(self):
        """Initialize all security dashboards"""
        self.dashboards = {
            'security_operations_center': self._create_soc_dashboard(),
            'authentication_monitoring': self._create_auth_dashboard(),
            'threat_detection': self._create_threat_dashboard(),
            'error_budget_monitoring': self._create_error_budget_dashboard(),
            'executive_security_summary': self._create_executive_dashboard(),
            'incident_response_tracker': self._create_incident_dashboard()
        }

    def _create_soc_dashboard(self) -> Dashboard:
        """Create Security Operations Center dashboard"""
        panels = [
            DashboardPanel(
                panel_id="threat_level",
                title="Current Threat Level",
                type="stat",
                targets=[{
                    "expr": "security_threat_level",
                    "legendFormat": "Threat Level"
                }],
                grid_pos={"x": 0, "y": 0, "w": 6, "h": 3},
                options={
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "horizontal",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "auto"
                },
                field_config={
                    "defaults": {
                        "color": {
                            "mode": "thresholds"
                        },
                        "mappings": [
                            {
                                "options": {
                                    "0": {"text": "LOW", "color": "green"},
                                    "1": {"text": "MEDIUM", "color": "orange"},
                                    "2": {"text": "HIGH", "color": "red"},
                                    "3": {"text": "CRITICAL", "color": "dark-red"}
                                },
                                "type": "value"
                            }
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "orange", "value": 1},
                                {"color": "red", "value": 2},
                                {"color": "dark-red", "value": 3}
                            ]
                        }
                    }
                }
            ),
            DashboardPanel(
                panel_id="active_alerts",
                title="Active Security Alerts",
                type="stat",
                targets=[{
                    "expr": "security_alerts_active",
                    "legendFormat": "Active Alerts"
                }],
                grid_pos={"x": 6, "y": 0, "w": 6, "h": 3},
                options={
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "horizontal",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "auto"
                }
            ),
            DashboardPanel(
                panel_id="authentication_failures",
                title="Authentication Failures (5min)",
                type="graph",
                targets=[{
                    "expr": "rate(jwt_validation_failed_total[5m])",
                    "legendFormat": "Auth Failures"
                }],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 6},
                options={
                    "alertThreshold": True
                }
            ),
            DashboardPanel(
                panel_id="rate_limiting_activity",
                title="Rate Limiting Activity",
                type="graph",
                targets=[
                    {
                        "expr": "rate(rate_limited_requests_total[5m])",
                        "legendFormat": "Rate Limited"
                    },
                    {
                        "expr": "rate(abusive_requests_detected_total[5m])",
                        "legendFormat": "Abusive Requests"
                    }
                ],
                grid_pos={"x": 0, "y": 3, "w": 12, "h": 6}
            ),
            DashboardPanel(
                panel_id="security_events_timeline",
                title="Security Events Timeline",
                type="graph",
                targets=[
                    {
                        "expr": "rate(security_events_total[5m])",
                        "legendFormat": "Total Events"
                    },
                    {
                        "expr": "rate(malicious_activities_detected_total[5m])",
                        "legendFormat": "Malicious Activities"
                    },
                    {
                        "expr": "rate(threats_detected_total[5m])",
                        "legendFormat": "Threats Detected"
                    }
                ],
                grid_pos={"x": 12, "y": 6, "w": 12, "h": 8}
            ),
            DashboardPanel(
                panel_id="top_attack_sources",
                title="Top Attack Sources",
                type="table",
                targets=[{
                    "expr": "topk(10, rate(suspicious_requests_by_ip[1h]))",
                    "legendFormat": "{{ source_ip }}"
                }],
                grid_pos={"x": 0, "y": 9, "w": 12, "h": 8}
            ),
            DashboardPanel(
                panel_id="error_budget_status",
                title="Error Budget Status",
                type="table",
                targets=[{
                    "expr": "security_error_budget_usage_percent",
                    "legendFormat": "{{ slo_name }}"
                }],
                grid_pos={"x": 12, "y": 14, "w": 12, "h": 8}
            )
        ]

        return Dashboard(
            dashboard_id="security_operations_center",
            title="Security Operations Center",
            description="Real-time security monitoring and operations dashboard",
            type=DashboardType.REAL_TIME,
            tags=["security", "soc", "monitoring"],
            panels=panels,
            refresh_interval="10s"
        )

    def _create_auth_dashboard(self) -> Dashboard:
        """Create authentication monitoring dashboard"""
        panels = [
            DashboardPanel(
                panel_id="auth_success_rate",
                title="Authentication Success Rate",
                type="stat",
                targets=[{
                    "expr": "rate(jwt_validation_total[5m]) / rate(jwt_validation_total[5m]) * 100",
                    "legendFormat": "Success Rate %"
                }],
                grid_pos={"x": 0, "y": 0, "w": 6, "h": 3}
            ),
            DashboardPanel(
                panel_id="token_validation_latency",
                title="Token Validation Latency",
                type="graph",
                targets=[{
                    "expr": "histogram_quantile(0.95, rate(jwt_validation_duration_bucket[5m]))",
                    "legendFormat": "P95 Latency"
                }],
                grid_pos={"x": 6, "y": 0, "w": 9, "h": 6}
            ),
            DashboardPanel(
                panel_id="failed_logins_by_ip",
                title="Failed Logins by IP",
                type="table",
                targets=[{
                    "expr": "rate(authentication_failures_by_ip[1h])",
                    "legendFormat": "{{ source_ip }}"
                }],
                grid_pos={"x": 15, "y": 0, "w": 9, "h": 8}
            ),
            DashboardPanel(
                panel_id="session_hijacking_attempts",
                title="Session Hijacking Attempts",
                type="graph",
                targets=[{
                    "expr": "rate(session_hijacking_attempts_total[5m])",
                    "legendFormat": "Hijacking Attempts"
                }],
                grid_pos={"x": 0, "y": 3, "w": 12, "h": 6}
            ),
            DashboardPanel(
                panel_id="geographic_auth_anomalies",
                title="Geographic Authentication Anomalies",
                type="heatmap",
                targets=[{
                    "expr": "rate(geographic_auth_anomalies[1h])",
                    "legendFormat": "{{ country }}"
                }],
                grid_pos={"x": 0, "y": 9, "w": 12, "h": 8}
            )
        ]

        return Dashboard(
            dashboard_id="authentication_monitoring",
            title="Authentication Security Monitoring",
            description="Comprehensive authentication security monitoring",
            type=DashboardType.OPERATIONAL,
            tags=["authentication", "security", "jwt"],
            panels=panels
        )

    def _create_threat_dashboard(self) -> Dashboard:
        """Create threat detection dashboard"""
        panels = [
            DashboardPanel(
                panel_id="threat_detection_rate",
                title="Threat Detection Rate",
                type="stat",
                targets=[{
                    "expr": "rate(threats_detected_total[1h])",
                    "legendFormat": "Threats/Hour"
                }],
                grid_pos={"x": 0, "y": 0, "w": 6, "h": 3}
            ),
            DashboardPanel(
                panel_id="threat_types",
                title="Threat Types Distribution",
                type="piechart",
                targets=[{
                    "expr": "sum(rate(threats_detected_total[1h])) by (threat_type)",
                    "legendFormat": "{{ threat_type }}"
                }],
                grid_pos={"x": 6, "y": 0, "w": 9, "h": 6}
            ),
            DashboardPanel(
                panel_id="injection_attempts",
                title="Injection Attempts by Type",
                type="graph",
                targets=[
                    {
                        "expr": "rate(prompt_injection_attempts_total[5m])",
                        "legendFormat": "Prompt Injection"
                    },
                    {
                        "expr": "rate(sql_injection_attempts_total[5m])",
                        "legendFormat": "SQL Injection"
                    },
                    {
                        "expr": "rate(xss_attempts_total[5m])",
                        "legendFormat": "XSS Attempts"
                    }
                ],
                grid_pos={"x": 15, "y": 0, "w": 9, "h": 6}
            ),
            DashboardPanel(
                panel_id="malicious_file_uploads",
                title="Malicious File Uploads",
                type="graph",
                targets=[{
                    "expr": "rate(malicious_file_uploads_total[1h])",
                    "legendFormat": "Malicious Files"
                }],
                grid_pos={"x": 0, "y": 3, "w": 12, "h": 6}
            ),
            DashboardPanel(
                panel_id="attack_source_geography",
                title="Attack Source Geography",
                type="geomap",
                targets=[{
                    "expr": "rate(attacks_by_country[1h])",
                    "legendFormat": "{{ country }}"
                }],
                grid_pos={"x": 0, "y": 9, "w": 12, "h": 8}
            )
        ]

        return Dashboard(
            dashboard_id="threat_detection",
            title="Threat Detection & Response",
            description="Advanced threat detection and analysis dashboard",
            type=DashboardType.ANALYTICS,
            tags=["threats", "detection", "security"],
            panels=panels
        )

    def _create_error_budget_dashboard(self) -> Dashboard:
        """Create error budget monitoring dashboard"""
        panels = [
            DashboardPanel(
                panel_id="budget_usage_overview",
                title="Error Budget Usage Overview",
                type="bargauge",
                targets=[{
                    "expr": "security_error_budget_usage_percent",
                    "legendFormat": "{{ slo_name }}"
                }],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 8},
                options={
                    "orientation": "horizontal",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "showUnfilled": True
                },
                field_config={
                    "defaults": {
                        "color": {
                            "mode": "thresholds"
                        },
                        "mappings": [],
                        "max": 100,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "orange", "value": 75},
                                {"color": "red", "value": 90},
                                {"color": "dark-red", "value": 100}
                            ]
                        },
                        "unit": "percent"
                    }
                }
            ),
            DashboardPanel(
                panel_id="budget_remaining",
                title="Remaining Error Budget",
                type="table",
                targets=[{
                    "expr": "security_error_budget_remaining",
                    "legendFormat": "{{ slo_name }}"
                }],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 8}
            ),
            DashboardPanel(
                panel_id="budget_burn_rate",
                title="Error Budget Burn Rate",
                type="graph",
                targets=[{
                    "expr": "rate(security_error_budget_usage[1h])",
                    "legendFormat": "{{ slo_name }}"
                }],
                grid_pos={"x": 0, "y": 8, "w": 12, "h": 8}
            ),
            DashboardPanel(
                panel_id="budget_alerts",
                title="Error Budget Alerts",
                type="stat",
                targets=[{
                    "expr": "security_budget_alerts_total",
                    "legendFormat": "Budget Alerts"
                }],
                grid_pos={"x": 12, "y": 8, "w": 6, "h": 4}
            ),
            DashboardPanel(
                panel_id="budget_status",
                title="Budget Status",
                type="stat",
                targets=[{
                    "expr": "security_error_budget_status",
                    "legendFormat": "{{ slo_name }}"
                }],
                grid_pos={"x": 18, "y": 8, "w": 6, "h": 4}
            )
        ]

        return Dashboard(
            dashboard_id="error_budget_monitoring",
            title="Error Budget Monitoring",
            description="Monitor error budget consumption across all security SLOs",
            type=DashboardType.OPERATIONAL,
            tags=["error_budget", "slo", "reliability"],
            panels=panels
        )

    def _create_executive_dashboard(self) -> Dashboard:
        """Create executive security summary dashboard"""
        panels = [
            DashboardPanel(
                panel_id="security_health_score",
                title="Security Health Score",
                type="stat",
                targets=[{
                    "expr": "security_health_score",
                    "legendFormat": "Health Score"
                }],
                grid_pos={"x": 0, "y": 0, "w": 6, "h": 4},
                options={
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "horizontal",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "auto"
                },
                field_config={
                    "defaults": {
                        "color": {
                            "mode": "thresholds"
                        },
                        "mappings": [],
                        "max": 100,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "dark-red", "value": None},
                                {"color": "red", "value": 50},
                                {"color": "orange", "value": 75},
                                {"color": "green", "value": 90}
                            ]
                        },
                        "unit": "percent"
                    }
                }
            ),
            DashboardPanel(
                panel_id="active_incidents",
                title="Active Security Incidents",
                type="stat",
                targets=[{
                    "expr": "security_incidents_active",
                    "legendFormat": "Active Incidents"
                }],
                grid_pos={"x": 6, "y": 0, "w": 6, "h": 4}
            ),
            DashboardPanel(
                panel_id="mttr_trend",
                title="Mean Time to Resolution (MTTR)",
                type="graph",
                targets=[{
                    "expr": "security_incident_mttr",
                    "legendFormat": "MTTR (minutes)"
                }],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 6}
            ),
            DashboardPanel(
                panel_id="slo_compliance",
                title="SLO Compliance Overview",
                type="bargauge",
                targets=[{
                    "expr": "(1 - security_error_budget_usage_percent / 100) * 100",
                    "legendFormat": "{{ slo_name }}"
                }],
                grid_pos={"x": 0, "y": 4, "w": 12, "h": 8}
            ),
            DashboardPanel(
                panel_id="security_investments",
                title="Security Investment ROI",
                type="table",
                targets=[{
                    "expr": "security_investment_roi",
                    "legendFormat": "Investment"
                }],
                grid_pos={"x": 12, "y": 6, "w": 12, "h": 8}
            )
        ]

        return Dashboard(
            dashboard_id="executive_security_summary",
            title="Executive Security Summary",
            description="High-level security metrics for executive review",
            type=DashboardType.EXECUTIVE,
            tags=["executive", "summary", "security"],
            panels=panels,
            refresh_interval="5m"
        )

    def _create_incident_dashboard(self) -> Dashboard:
        """Create incident response tracker dashboard"""
        panels = [
            DashboardPanel(
                panel_id="incident_status",
                title="Incident Response Status",
                type="stat",
                targets=[{
                    "expr": "incident_response_status",
                    "legendFormat": "Status"
                }],
                grid_pos={"x": 0, "y": 0, "w": 6, "h": 3}
            ),
            DashboardPanel(
                panel_id="active_incidents_table",
                title="Active Incidents",
                type="table",
                targets=[{
                    "expr": "active_security_incidents",
                    "legendFormat": "Incidents"
                }],
                grid_pos={"x": 6, "y": 0, "w": 18, "h": 8}
            ),
            DashboardPanel(
                panel_id="incident_response_time",
                title="Incident Response Times",
                type="graph",
                targets=[{
                    "expr": "security_incident_response_time",
                    "legendFormat": "Response Time"
                }],
                grid_pos={"x": 0, "y": 3, "w": 12, "h": 6}
            ),
            DashboardPanel(
                panel_id="incident_categories",
                title="Incidents by Category",
                type="piechart",
                targets=[{
                    "expr": "sum(security_incidents_total) by (category)",
                    "legendFormat": "{{ category }}"
                }],
                grid_pos={"x": 12, "y": 8, "w": 12, "h": 8}
            )
        ]

        return Dashboard(
            dashboard_id="incident_response_tracker",
            title="Incident Response Tracker",
            description="Track and manage security incident response activities",
            type=DashboardType.OPERATIONAL,
            tags=["incidents", "response", "tracking"],
            panels=panels
        )

    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID"""
        return self.dashboards.get(dashboard_id)

    async def get_all_dashboards(self) -> Dict[str, Dashboard]:
        """Get all dashboards"""
        return self.dashboards

    async def get_dashboards_by_type(self, dashboard_type: DashboardType) -> List[Dashboard]:
        """Get dashboards by type"""
        return [db for db in self.dashboards.values() if db.type == dashboard_type]

    async def get_dashboards_by_tag(self, tag: str) -> List[Dashboard]:
        """Get dashboards by tag"""
        return [db for db in self.dashboards.values() if tag in db.tags]

    async def export_dashboard(self, dashboard_id: str) -> Optional[str]:
        """Export dashboard as JSON"""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None

        dashboard_dict = {
            'dashboard_id': dashboard.dashboard_id,
            'title': dashboard.title,
            'description': dashboard.description,
            'type': dashboard.type.value,
            'tags': dashboard.tags,
            'time_range': dashboard.time_range,
            'refresh_interval': dashboard.refresh_interval,
            'panels': [
                {
                    'panel_id': panel.panel_id,
                    'title': panel.title,
                    'type': panel.type,
                    'targets': panel.targets,
                    'grid_pos': panel.grid_pos,
                    'options': panel.options,
                    'field_config': panel.field_config
                }
                for panel in dashboard.panels
            ],
            'created_at': dashboard.created_at.isoformat(),
            'updated_at': dashboard.updated_at.isoformat()
        }

        return json.dumps(dashboard_dict, indent=2)

    async def save_dashboard_state(self, dashboard_id: str, state: Dict[str, Any]):
        """Save dashboard state to Redis"""
        key = f"dashboard_state:{dashboard_id}"
        await self.redis.set(key, json.dumps(state))

    async def load_dashboard_state(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Load dashboard state from Redis"""
        key = f"dashboard_state:{dashboard_id}"
        state = await self.redis.get(key)
        return json.loads(state) if state else None

# Global dashboards manager instance
dashboards_manager: Optional[SecurityDashboardsManager] = None

async def initialize_dashboards_manager(redis_client: redis.Redis) -> SecurityDashboardsManager:
    """Initialize global dashboards manager"""
    global dashboards_manager

    if dashboards_manager is None:
        dashboards_manager = SecurityDashboardsManager(redis_client)
        logger.info("Security Dashboards Manager initialized")

    return dashboards_manager

async def get_dashboards_manager() -> SecurityDashboardsManager:
    """Get global dashboards manager instance"""
    if dashboards_manager is None:
        raise RuntimeError("Dashboards manager not initialized")
    return dashboards_manager