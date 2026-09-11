from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
import uuid

class AuditLogBase(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict[str, Any]] = None

class AuditLogCreate(AuditLogBase):
    user_id: uuid.UUID

class AuditLogResponse(AuditLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
