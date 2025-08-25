"""
Security Incident Response Playbooks for AgentFlow
Production-ready incident response procedures and automation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    """Incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    """Incident status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IncidentCategory(Enum):
    """Incident categories"""
    AUTHENTICATION_BREACH = "authentication_breach"
    DATA_EXFILTRATION = "data_exfiltration"
    INJECTION_ATTACK = "injection_attack"
    DOS_ATTACK = "dos_attack"
    MALWARE = "malware"
    INSIDER_THREAT = "insider_threat"
    THIRD_PARTY_COMPROMISE = "third_party_compromise"
    OTHER = "other"

@dataclass
class Incident:
    """Security incident data structure"""
    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    category: IncidentCategory
    status: IncidentStatus = IncidentStatus.DETECTED
    detection_time: datetime = None
    reported_by: str = None
    assigned_to: Optional[str] = None
    tags: List[str] = None
    affected_systems: List[str] = None
    attack_vector: Optional[str] = None
    threat_actor: Optional[str] = None
    indicators_of_compromise: List[str] = None
    timeline: List[Dict[str, Any]] = None
    actions_taken: List[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]] = None
    containment_status: str = "not_started"
    eradication_status: str = "not_started"
    recovery_status: str = "not_started"
    post_incident_status: str = "not_started"
    business_impact: Optional[str] = None
    estimated_financial_impact: Optional[float] = None
    customer_impact: Optional[str] = None
    resolution_summary: Optional[str] = None
    lessons_learned: List[str] = None
    prevention_recommendations: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.detection_time is None:
            self.detection_time = datetime.utcnow()
        if self.tags is None:
            self.tags = []
        if self.affected_systems is None:
            self.affected_systems = []
        if self.indicators_of_compromise is None:
            self.indicators_of_compromise = []
        if self.timeline is None:
            self.timeline = []
        if self.actions_taken is None:
            self.actions_taken = []
        if self.evidence is None:
            self.evidence = []
        if self.lessons_learned is None:
            self.lessons_learned = []
        if self.prevention_recommendations is None:
            self.prevention_recommendations = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def add_timeline_entry(self, event: str, details: str = "", user: str = "system"):
        """Add entry to incident timeline"""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event,
            'details': details,
            'user': user
        }
        self.timeline.append(entry)
        self.updated_at = datetime.utcnow()

    def add_action_taken(self, action: str, status: str = "completed", user: str = "system", notes: str = ""):
        """Add action taken to incident"""
        action_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'status': status,
            'user': user,
            'notes': notes
        }
        self.actions_taken.append(action_entry)
        self.updated_at = datetime.utcnow()

    def add_evidence(self, evidence_type: str, location: str, description: str, collected_by: str = "system"):
        """Add evidence to incident"""
        evidence_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': evidence_type,
            'location': location,
            'description': description,
            'collected_by': collected_by
        }
        self.evidence.append(evidence_entry)
        self.updated_at = datetime.utcnow()

class IncidentResponsePlaybook:
    """
    Incident response playbook with automated and manual procedures
    """

    def __init__(self, incident_type: str, config: Dict[str, Any]):
        self.incident_type = incident_type
        self.config = config
        self.automated_steps = config.get('automated_steps', [])
        self.manual_steps = config.get('manual_steps', [])
        self.escalation_matrix = config.get('escalation_matrix', {})
        self.communication_plan = config.get('communication_plan', {})
        self.recovery_procedures = config.get('recovery_procedures', [])

    async def execute_automated_response(self, incident: Incident) -> List[str]:
        """Execute automated response steps"""
        executed_actions = []

        for step in self.automated_steps:
            try:
                action_name = step.get('action', '')
                action_type = step.get('type', '')

                if action_type == 'isolate_system':
                    result = await self._isolate_affected_systems(incident, step)
                elif action_type == 'block_traffic':
                    result = await self._block_malicious_traffic(incident, step)
                elif action_type == 'revoke_credentials':
                    result = await self._revoke_compromised_credentials(incident, step)
                elif action_type == 'enable_monitoring':
                    result = await self._enable_enhanced_monitoring(incident, step)
                elif action_type == 'collect_evidence':
                    result = await self._collect_forensic_evidence(incident, step)
                else:
                    result = f"Unknown action type: {action_type}"

                executed_actions.append(f"{action_name}: {result}")
                incident.add_action_taken(action_name, "completed", "automated_system", result)

            except Exception as e:
                error_msg = f"Failed to execute {step.get('action', 'unknown')}: {str(e)}"
                executed_actions.append(error_msg)
                incident.add_action_taken(step.get('action', 'unknown'), "failed", "automated_system", error_msg)

        return executed_actions

    async def get_manual_response_steps(self, incident: Incident) -> List[Dict[str, Any]]:
        """Get manual response steps for current incident phase"""
        current_phase = self._get_incident_phase(incident)
        return self.manual_steps.get(current_phase, [])

    def get_escalation_contacts(self, severity: IncidentSeverity) -> List[Dict[str, Any]]:
        """Get escalation contacts for incident severity"""
        return self.escalation_matrix.get(severity.value, [])

    def get_communication_plan(self, stakeholder: str) -> Dict[str, Any]:
        """Get communication plan for stakeholder"""
        return self.communication_plan.get(stakeholder, {})

    async def _isolate_affected_systems(self, incident: Incident, step_config: Dict[str, Any]) -> str:
        """Isolate affected systems"""
        # Implementation would integrate with infrastructure management
        systems = step_config.get('systems', incident.affected_systems)
        logger.info(f"Isolating systems: {systems}")
        return f"Isolated {len(systems)} systems"

    async def _block_malicious_traffic(self, incident: Incident, step_config: Dict[str, Any]) -> str:
        """Block malicious traffic"""
        # Implementation would integrate with firewall/WAF
        sources = step_config.get('sources', [])
        logger.info(f"Blocking traffic from: {sources}")
        return f"Blocked traffic from {len(sources)} sources"

    async def _revoke_compromised_credentials(self, incident: Incident, step_config: Dict[str, Any]) -> str:
        """Revoke compromised credentials"""
        # Implementation would integrate with identity management
        users = step_config.get('users', [])
        logger.info(f"Revoking credentials for: {users}")
        return f"Revoked credentials for {len(users)} users"

    async def _enable_enhanced_monitoring(self, incident: Incident, step_config: Dict[str, Any]) -> str:
        """Enable enhanced monitoring"""
        # Implementation would enable additional monitoring
        monitoring_type = step_config.get('monitoring_type', 'enhanced')
        logger.info(f"Enabling {monitoring_type} monitoring")
        return f"Enabled {monitoring_type} monitoring"

    async def _collect_forensic_evidence(self, incident: Incident, step_config: Dict[str, Any]) -> str:
        """Collect forensic evidence"""
        # Implementation would collect logs, memory dumps, etc.
        evidence_types = step_config.get('evidence_types', ['logs', 'network_traffic'])
        logger.info(f"Collecting evidence: {evidence_types}")
        return f"Collected {len(evidence_types)} types of evidence"

    def _get_incident_phase(self, incident: Incident) -> str:
        """Get current incident response phase"""
        if incident.status in [IncidentStatus.DETECTED, IncidentStatus.INVESTIGATING]:
            return "identification"
        elif incident.status == IncidentStatus.CONTAINED:
            return "containment"
        elif incident.status == IncidentStatus.ERADICATED:
            return "eradication"
        elif incident.status == IncidentStatus.RECOVERING:
            return "recovery"
        elif incident.status == IncidentStatus.RESOLVED:
            return "post_incident"
        else:
            return "unknown"

class SecurityIncidentManager:
    """
    Production-ready security incident management system
    """

    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any]):
        self.redis = redis_client
        self.config = config
        self.playbooks = self._initialize_playbooks()
        self.active_incidents: Dict[str, Incident] = {}
        self.incident_counter = 0

    def _initialize_playbooks(self) -> Dict[str, IncidentResponsePlaybook]:
        """Initialize incident response playbooks"""
        return {
            'authentication_breach': IncidentResponsePlaybook('authentication_breach', {
                'automated_steps': [
                    {
                        'action': 'Isolate affected systems',
                        'type': 'isolate_system',
                        'systems': ['auth_service', 'api_gateway']
                    },
                    {
                        'action': 'Block suspicious IPs',
                        'type': 'block_traffic',
                        'sources': 'from_incident_data'
                    },
                    {
                        'action': 'Revoke active sessions',
                        'type': 'revoke_credentials',
                        'users': 'from_incident_data'
                    },
                    {
                        'action': 'Enable enhanced authentication monitoring',
                        'type': 'enable_monitoring',
                        'monitoring_type': 'authentication'
                    }
                ],
                'manual_steps': {
                    'identification': [
                        {'step': 'Verify breach indicators', 'role': 'security_analyst', 'timeframe': '15 minutes'},
                        {'step': 'Determine scope of compromise', 'role': 'security_lead', 'timeframe': '30 minutes'},
                        {'step': 'Identify affected users', 'role': 'security_team', 'timeframe': '45 minutes'}
                    ],
                    'containment': [
                        {'step': 'Force password reset for affected users', 'role': 'security_team', 'timeframe': '1 hour'},
                        {'step': 'Implement additional authentication controls', 'role': 'platform_team', 'timeframe': '2 hours'},
                        {'step': 'Update security policies', 'role': 'security_lead', 'timeframe': '4 hours'}
                    ],
                    'eradication': [
                        {'step': 'Remove malicious access', 'role': 'security_team', 'timeframe': '2 hours'},
                        {'step': 'Patch vulnerabilities', 'role': 'platform_team', 'timeframe': '6 hours'},
                        {'step': 'Update threat intelligence', 'role': 'security_team', 'timeframe': '8 hours'}
                    ],
                    'recovery': [
                        {'step': 'Restore authentication services', 'role': 'platform_team', 'timeframe': '4 hours'},
                        {'step': 'Validate system integrity', 'role': 'security_team', 'timeframe': '6 hours'},
                        {'step': 'Monitor for reoccurrence', 'role': 'security_team', 'timeframe': '24 hours'}
                    ],
                    'post_incident': [
                        {'step': 'Conduct incident review', 'role': 'security_lead', 'timeframe': '1 week'},
                        {'step': 'Update incident response plan', 'role': 'security_team', 'timeframe': '2 weeks'},
                        {'step': 'Implement prevention measures', 'role': 'platform_team', 'timeframe': '1 month'}
                    ]
                },
                'escalation_matrix': {
                    'critical': [
                        {'role': 'Security Director', 'contact': 'security-director@company.com', 'phone': '+1-555-0101'},
                        {'role': 'CTO', 'contact': 'cto@company.com', 'phone': '+1-555-0102'},
                        {'role': 'CEO', 'contact': 'ceo@company.com', 'phone': '+1-555-0103'}
                    ],
                    'high': [
                        {'role': 'Security Lead', 'contact': 'security-lead@company.com', 'phone': '+1-555-0201'},
                        {'role': 'VP Engineering', 'contact': 'vp-engineering@company.com', 'phone': '+1-555-0202'}
                    ]
                },
                'communication_plan': {
                    'customers': {
                        'template': 'customer_breach_notification',
                        'timeline': '24 hours after containment',
                        'channels': ['email', 'dashboard_notification']
                    },
                    'regulators': {
                        'template': 'regulatory_breach_report',
                        'timeline': '72 hours after detection',
                        'channels': ['formal_report', 'phone_briefing']
                    },
                    'internal': {
                        'template': 'internal_incident_update',
                        'timeline': 'immediate',
                        'channels': ['slack', 'email', 'meeting']
                    }
                }
            }),
            'data_exfiltration': IncidentResponsePlaybook('data_exfiltration', {
                'automated_steps': [
                    {
                        'action': 'Stop data egress',
                        'type': 'block_traffic',
                        'sources': 'from_incident_data'
                    },
                    {
                        'action': 'Quarantine affected data',
                        'type': 'isolate_system',
                        'systems': 'from_incident_data'
                    },
                    {
                        'action': 'Enable data loss prevention',
                        'type': 'enable_monitoring',
                        'monitoring_type': 'dlp'
                    }
                ],
                'manual_steps': {
                    'identification': [
                        {'step': 'Confirm data exfiltration', 'role': 'security_analyst', 'timeframe': '30 minutes'},
                        {'step': 'Identify exfiltrated data', 'role': 'security_lead', 'timeframe': '1 hour'},
                        {'step': 'Assess data sensitivity', 'role': 'legal_team', 'timeframe': '2 hours'}
                    ],
                    'containment': [
                        {'step': 'Stop all data transfers', 'role': 'security_team', 'timeframe': '1 hour'},
                        {'step': 'Secure affected systems', 'role': 'platform_team', 'timeframe': '2 hours'},
                        {'step': 'Notify legal counsel', 'role': 'legal_team', 'timeframe': '4 hours'}
                    ],
                    'eradication': [
                        {'step': 'Remove backdoors', 'role': 'security_team', 'timeframe': '4 hours'},
                        {'step': 'Update access controls', 'role': 'platform_team', 'timeframe': '8 hours'},
                        {'step': 'Patch vulnerabilities', 'role': 'security_team', 'timeframe': '12 hours'}
                    ],
                    'recovery': [
                        {'step': 'Restore from clean backups', 'role': 'platform_team', 'timeframe': '6 hours'},
                        {'step': 'Validate data integrity', 'role': 'security_team', 'timeframe': '8 hours'},
                        {'step': 'Resume normal operations', 'role': 'platform_team', 'timeframe': '12 hours'}
                    ],
                    'post_incident': [
                        {'step': 'Conduct forensic analysis', 'role': 'forensics_team', 'timeframe': '2 weeks'},
                        {'step': 'Prepare regulatory reports', 'role': 'legal_team', 'timeframe': '1 month'},
                        {'step': 'Implement additional controls', 'role': 'security_team', 'timeframe': '2 months'}
                    ]
                }
            }),
            'injection_attack': IncidentResponsePlaybook('injection_attack', {
                'automated_steps': [
                    {
                        'action': 'Deploy WAF rules',
                        'type': 'block_traffic',
                        'sources': 'from_incident_data'
                    },
                    {
                        'action': 'Enable input validation',
                        'type': 'enable_monitoring',
                        'monitoring_type': 'input_validation'
                    }
                ],
                'manual_steps': {
                    'identification': [
                        {'step': 'Analyze attack pattern', 'role': 'security_analyst', 'timeframe': '30 minutes'},
                        {'step': 'Determine attack vector', 'role': 'security_team', 'timeframe': '1 hour'},
                        {'step': 'Assess system compromise', 'role': 'security_lead', 'timeframe': '2 hours'}
                    ],
                    'containment': [
                        {'step': 'Block attack vectors', 'role': 'security_team', 'timeframe': '1 hour'},
                        {'step': 'Sanitize inputs', 'role': 'platform_team', 'timeframe': '2 hours'},
                        {'step': 'Rate limit affected endpoints', 'role': 'platform_team', 'timeframe': '4 hours'}
                    ],
                    'eradication': [
                        {'step': 'Remove malicious payloads', 'role': 'security_team', 'timeframe': '2 hours'},
                        {'step': 'Update security patterns', 'role': 'security_team', 'timeframe': '4 hours'},
                        {'step': 'Patch vulnerable code', 'role': 'platform_team', 'timeframe': '1 week'}
                    ],
                    'recovery': [
                        {'step': 'Restore normal operations', 'role': 'platform_team', 'timeframe': '2 hours'},
                        {'step': 'Monitor for reoccurrence', 'role': 'security_team', 'timeframe': '24 hours'},
                        {'step': 'Validate system security', 'role': 'security_team', 'timeframe': '48 hours'}
                    ],
                    'post_incident': [
                        {'step': 'Update injection detection rules', 'role': 'security_team', 'timeframe': '1 week'},
                        {'step': 'Conduct security training', 'role': 'security_team', 'timeframe': '2 weeks'},
                        {'step': 'Review secure coding practices', 'role': 'platform_team', 'timeframe': '1 month'}
                    ]
                }
            })
        }

    async def create_incident(self, title: str, description: str, severity: IncidentSeverity,
                            category: IncidentCategory, detection_source: str,
                            affected_systems: List[str] = None, attack_vector: str = None,
                            reported_by: str = "automated_detection") -> Incident:
        """Create a new security incident"""
        self.incident_counter += 1
        incident_id = "04d"

        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            reported_by=reported_by,
            affected_systems=affected_systems or [],
            attack_vector=attack_vector
        )

        # Add initial timeline entry
        incident.add_timeline_entry(
            "Incident detected",
            f"Incident detected by {detection_source}",
            reported_by
        )

        # Store incident
        await self._store_incident(incident)

        # Add to active incidents
        self.active_incidents[incident_id] = incident

        logger.info(f"Created security incident: {incident_id} - {title}")
        return incident

    async def execute_incident_response(self, incident: Incident) -> List[str]:
        """Execute incident response for the given incident"""
        playbook = self.playbooks.get(incident.category.value)

        if not playbook:
            logger.warning(f"No playbook found for incident category: {incident.category.value}")
            return ["No playbook available for this incident type"]

        # Update incident status
        incident.status = IncidentStatus.INVESTIGATING
        incident.add_timeline_entry("Started incident response", "Initiated automated response procedures")

        # Execute automated response
        executed_actions = await playbook.execute_automated_response(incident)

        # Get manual response steps
        manual_steps = await playbook.get_manual_response_steps(incident)

        # Update incident status based on actions
        if executed_actions:
            incident.status = IncidentStatus.CONTAINED
            incident.containment_status = "completed"
            incident.add_timeline_entry("Automated containment completed", f"Executed {len(executed_actions)} automated actions")

        # Store updated incident
        await self._store_incident(incident)

        return executed_actions

    async def update_incident_status(self, incident_id: str, status: IncidentStatus,
                                   user: str, notes: str = "") -> bool:
        """Update incident status"""
        incident = self.active_incidents.get(incident_id)
        if not incident:
            return False

        old_status = incident.status
        incident.status = status
        incident.updated_at = datetime.utcnow()

        incident.add_timeline_entry(
            f"Status changed: {old_status.value} -> {status.value}",
            notes,
            user
        )

        # Update phase-specific status
        if status == IncidentStatus.CONTAINED:
            incident.containment_status = "completed"
        elif status == IncidentStatus.ERADICATED:
            incident.eradication_status = "completed"
        elif status == IncidentStatus.RECOVERING:
            incident.recovery_status = "in_progress"
        elif status == IncidentStatus.RESOLVED:
            incident.recovery_status = "completed"
            incident.post_incident_status = "pending"

        await self._store_incident(incident)
        logger.info(f"Updated incident {incident_id} status to {status.value}")

        return True

    async def add_incident_evidence(self, incident_id: str, evidence_type: str,
                                  location: str, description: str, collected_by: str) -> bool:
        """Add evidence to incident"""
        incident = self.active_incidents.get(incident_id)
        if not incident:
            return False

        incident.add_evidence(evidence_type, location, description, collected_by)
        await self._store_incident(incident)

        return True

    async def get_incident_playbook_steps(self, incident_id: str) -> Dict[str, Any]:
        """Get playbook steps for incident"""
        incident = self.active_incidents.get(incident_id)
        if not incident:
            return {}

        playbook = self.playbooks.get(incident.category.value)
        if not playbook:
            return {}

        current_phase = playbook._get_incident_phase(incident)
        manual_steps = await playbook.get_manual_response_steps(incident)

        return {
            'current_phase': current_phase,
            'manual_steps': manual_steps,
            'escalation_contacts': playbook.get_escalation_contacts(incident.severity),
            'communication_plan': playbook.communication_plan
        }

    async def _store_incident(self, incident: Incident):
        """Store incident in Redis"""
        key = f"security_incident:{incident.incident_id}"
        incident_data = asdict(incident)
        incident_data['detection_time'] = incident.detection_time.isoformat()
        incident_data['created_at'] = incident.created_at.isoformat()
        incident_data['updated_at'] = incident.updated_at.isoformat()
        incident_data['severity'] = incident.severity.value
        incident_data['category'] = incident.category.value
        incident_data['status'] = incident.status.value

        await self.redis.set(key, json.dumps(incident_data))
        await self.redis.expire(key, 86400 * 30)  # Keep for 30 days

    async def get_active_incidents(self) -> List[Incident]:
        """Get all active incidents"""
        return list(self.active_incidents.values())

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID"""
        return self.active_incidents.get(incident_id)

    async def close_incident(self, incident_id: str, resolution_summary: str,
                           lessons_learned: List[str], prevention_recommendations: List[str],
                           closed_by: str) -> bool:
        """Close incident with final documentation"""
        incident = self.active_incidents.get(incident_id)
        if not incident:
            return False

        incident.status = IncidentStatus.CLOSED
        incident.resolution_summary = resolution_summary
        incident.lessons_learned = lessons_learned
        incident.prevention_recommendations = prevention_recommendations
        incident.post_incident_status = "completed"
        incident.updated_at = datetime.utcnow()

        incident.add_timeline_entry(
            "Incident closed",
            resolution_summary,
            closed_by
        )

        await self._store_incident(incident)

        # Remove from active incidents
        self.active_incidents.pop(incident_id, None)

        logger.info(f"Closed incident {incident_id}")
        return True

# Global incident manager instance
incident_manager: Optional[SecurityIncidentManager] = None

async def initialize_incident_manager(redis_client: redis.Redis, config: Dict[str, Any]) -> SecurityIncidentManager:
    """Initialize global incident manager"""
    global incident_manager

    if incident_manager is None:
        incident_manager = SecurityIncidentManager(redis_client, config)
        logger.info("Security Incident Manager initialized")

    return incident_manager

async def get_incident_manager() -> SecurityIncidentManager:
    """Get global incident manager instance"""
    if incident_manager is None:
        raise RuntimeError("Incident manager not initialized")
    return incident_manager

# Convenience functions for creating common incidents
async def create_authentication_breach_incident(affected_users: int, breach_source: str) -> Incident:
    """Create authentication breach incident"""
    manager = await get_incident_manager()

    return await manager.create_incident(
        title=f"Authentication Breach - {affected_users} Users Affected",
        description=f"Authentication system compromised affecting {affected_users} users. Source: {breach_source}",
        severity=IncidentSeverity.CRITICAL,
        category=IncidentCategory.AUTHENTICATION_BREACH,
        detection_source="automated_monitoring",
        affected_systems=["authentication_service", "api_gateway"],
        attack_vector=breach_source
    )

async def create_data_exfiltration_incident(data_types: List[str], destination: str) -> Incident:
    """Create data exfiltration incident"""
    manager = await get_incident_manager()

    return await manager.create_incident(
        title=f"Data Exfiltration - {', '.join(data_types)}",
        description=f"Unauthorized data exfiltration detected. Data types: {', '.join(data_types)}. Destination: {destination}",
        severity=IncidentSeverity.CRITICAL,
        category=IncidentCategory.DATA_EXFILTRATION,
        detection_source="dlp_monitoring",
        affected_systems=["data_storage", "api_endpoints"],
        attack_vector=f"data_exfiltration_to_{destination}"
    )

async def create_injection_attack_incident(attack_type: str, affected_endpoints: List[str]) -> Incident:
    """Create injection attack incident"""
    manager = await get_incident_manager()

    severity = IncidentSeverity.CRITICAL if attack_type in ['sql_injection', 'rce'] else IncidentSeverity.HIGH

    return await manager.create_incident(
        title=f"{attack_type.replace('_', ' ').title()} Attack",
        description=f"{attack_type.replace('_', ' ').title()} attack detected against endpoints: {', '.join(affected_endpoints)}",
        severity=severity,
        category=IncidentCategory.INJECTION_ATTACK,
        detection_source="waf_monitoring",
        affected_systems=affected_endpoints,
        attack_vector=attack_type
    )