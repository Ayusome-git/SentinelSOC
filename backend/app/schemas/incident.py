from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any, Dict
from enum import Enum
from datetime import datetime
import uuid
from app.models.incident import IncidentStatus

class IncidentBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str

class IncidentCreate(IncidentBase):
    application_id: uuid.UUID
    alert_ids: Optional[List[uuid.UUID]] = None
    event_ids: Optional[List[uuid.UUID]] = None

class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None

class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus

class IncidentAssigneeUpdate(BaseModel):
    assigned_to: Optional[uuid.UUID] = None

class IncidentAlertsLink(BaseModel):
    alert_ids: List[uuid.UUID]

class IncidentEventsLink(BaseModel):
    event_ids: List[uuid.UUID]

class IncidentCommentCreate(BaseModel):
    comment: str

class IncidentCommentResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    user_id: uuid.UUID
    comment: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IncidentResponse(IncidentBase):
    id: uuid.UUID
    incident_number: str
    status: IncidentStatus
    risk_score: Optional[int] = None
    application_id: uuid.UUID
    correlation_id: Optional[uuid.UUID] = None
    assigned_to: Optional[uuid.UUID] = None
    
    detected_at: datetime
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IncidentListResponse(BaseModel):
    items: List[IncidentResponse]
    total: int
    page: int
    size: int

class IncidentSummaryResponse(BaseModel):
    total: int
    open: int
    investigating: int
    contained: int
    resolved: int
    closed: int
    critical: int
    high: int
    unassigned: int
    average_risk_score: float

# --- Phase 16 Schemas ---

class TimelineEntryType(str, Enum):
    SECURITY_EVENT = "SECURITY_EVENT"
    ALERT = "ALERT"
    CORRELATION = "CORRELATION"
    INCIDENT_ACTIVITY = "INCIDENT_ACTIVITY"
    COMMENT = "COMMENT"

class TimelineEntry(BaseModel):
    id: uuid.UUID
    entry_type: TimelineEntryType
    occurred_at: datetime
    title: str
    description: Optional[str] = None
    severity: Optional[str] = None
    risk_score: Optional[int] = None
    
    # Optional foreign IDs depending on type
    security_event_id: Optional[uuid.UUID] = None
    alert_id: Optional[uuid.UUID] = None
    correlation_id: Optional[uuid.UUID] = None
    
    # Entity info
    source_ip: Optional[str] = None
    username: Optional[str] = None
    
    metadata_fields: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class TimelineResponse(BaseModel):
    items: List[TimelineEntry]
    total: int
    
class EntityCount(BaseModel):
    value: str
    event_count: int

class EntitiesResponse(BaseModel):
    source_ips: List[EntityCount] = []
    users: List[EntityCount] = []
    request_paths: List[EntityCount] = []
    sessions: List[EntityCount] = []

class IncidentEvidenceCreate(BaseModel):
    evidence_type: str # SECURITY_EVENT, ALERT, CORRELATION
    evidence_id: uuid.UUID

class IncidentEvidenceResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    evidence_type: str
    evidence_id: uuid.UUID
    added_by: Optional[uuid.UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
