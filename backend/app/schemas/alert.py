from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.alert import AlertStatus

class AlertBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str
    status: AlertStatus = AlertStatus.OPEN
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    rule_id: Optional[uuid.UUID] = None

class AlertCreate(AlertBase):
    application_id: uuid.UUID
    security_event_id: Optional[uuid.UUID] = None
    detected_at: datetime

class AlertAssigneeUpdate(BaseModel):
    assigned_to: Optional[uuid.UUID]

class AlertResponse(AlertBase):
    id: uuid.UUID
    application_id: uuid.UUID
    security_event_id: Optional[uuid.UUID] = None
    detected_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int

class AlertCommentCreate(BaseModel):
    comment: str

class AlertCommentResponse(BaseModel):
    id: uuid.UUID
    alert_id: uuid.UUID
    user_id: uuid.UUID
    comment: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertSummary(BaseModel):
    total: int
    open: int
    acknowledged: int
    resolved: int
    false_positive: int
    critical: int
    high: int
    unassigned: int
    average_risk_score: float

class BulkActionRequest(BaseModel):
    alert_ids: list[uuid.UUID]
    action: str # ACKNOWLEDGE, ASSIGN, RESOLVE, FALSE_POSITIVE
    assigned_to: Optional[uuid.UUID] = None
