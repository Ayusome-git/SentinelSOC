from app.db.base import Base, BaseModel
from app.models.user import User, UserRole
from app.models.application import Application, AppEnvironment, AppStatus
from app.models.application_api_key import ApplicationApiKey
from app.models.security_event import SecurityEvent, EventSeverity
from app.models.alert import Alert, AlertStatus, incident_alerts
from app.models.alert_comment import AlertComment
from app.models.incident import Incident, IncidentStatus
from app.models.incident_comment import IncidentComment
from app.models.incident_evidence import IncidentEvidence, EvidenceType
from app.models.ml_model import MLModel, MLModelStatus
from app.models.incident_sequence import IncidentSequence
from app.models.audit_log import AuditLog
from app.models.detection_rule import DetectionRule
from app.models.correlation_rule import CorrelationRule
from app.models.correlation import Correlation, CorrelationStatus, correlation_events, correlation_alerts

# Import all models here so Alembic can discover them
__all__ = [
    "Base",
    "BaseModel",
    "User",
    "UserRole",
    "Application",
    "AppEnvironment",
    "AppStatus",
    "ApplicationApiKey",
    "SecurityEvent",
    "EventSeverity",
    "Alert",
    "AlertStatus",
    "incident_alerts",
    "Incident",
    "IncidentStatus",
    "IncidentSequence",
    "IncidentComment",
    "IncidentEvidence",
    "EvidenceType",
    "AlertComment",
    "AuditLog",
    "DetectionRule",
    "CorrelationRule",
    "Correlation",
    "CorrelationStatus",
    "correlation_events",
    "correlation_alerts"
]
