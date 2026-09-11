from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid
from app.models.incident import IncidentStatus

class IncidentBase(BaseModel):
    incident_number: str
    title: str
    description: Optional[str] = None
    severity: str
    status: IncidentStatus = IncidentStatus.OPEN
    risk_score: Optional[int] = None

class IncidentCreate(IncidentBase):
    application_id: uuid.UUID
    detected_at: datetime

class IncidentResponse(IncidentBase):
    id: uuid.UUID
    application_id: uuid.UUID
    assigned_to: Optional[uuid.UUID] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
