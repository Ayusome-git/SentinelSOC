from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models.notification import NotificationType, NotificationStatus

class NotificationPreferenceBase(BaseModel):
    notify_on_critical_alerts: bool
    notify_on_high_risk: bool
    notify_on_incident_assigned: bool
    notify_on_incident_created: bool
    notify_on_incident_escalated: bool
    notify_on_response_failure: bool
    notify_on_ml_anomaly: bool
    notify_on_ti_match: bool
    receive_emails: bool

class NotificationPreferenceUpdate(BaseModel):
    notify_on_critical_alerts: Optional[bool] = None
    notify_on_high_risk: Optional[bool] = None
    notify_on_incident_assigned: Optional[bool] = None
    notify_on_incident_created: Optional[bool] = None
    notify_on_incident_escalated: Optional[bool] = None
    notify_on_response_failure: Optional[bool] = None
    notify_on_ml_anomaly: Optional[bool] = None
    notify_on_ti_match: Optional[bool] = None
    receive_emails: Optional[bool] = None

class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: UUID
    user_id: UUID
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class NotificationBase(BaseModel):
    notification_type: str
    title: str
    message: str
    severity: Optional[str] = None
    risk_score: Optional[int] = None
    link_path: Optional[str] = None
    is_read: bool
    status: str

class NotificationResponse(NotificationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    
    alert_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    response_action_id: Optional[UUID] = None
    application_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    size: int
