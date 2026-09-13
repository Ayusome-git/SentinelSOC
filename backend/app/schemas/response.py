from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from app.models.response import ResponseActionStatus

class ApplicationResponseCapabilityBase(BaseModel):
    action_type: str
    enabled: bool = True
    configuration: Optional[Dict[str, Any]] = None

class ApplicationResponseCapabilityCreate(ApplicationResponseCapabilityBase):
    application_id: uuid.UUID

class ApplicationResponseCapabilityUpdate(BaseModel):
    enabled: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None

class ApplicationResponseCapabilityResponse(ApplicationResponseCapabilityBase):
    id: uuid.UUID
    application_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResponseActionBase(BaseModel):
    action_type: str
    target_type: str
    target_value: str

class ResponseActionCreate(ResponseActionBase):
    incident_id: Optional[uuid.UUID] = None
    alert_id: Optional[uuid.UUID] = None
    application_id: uuid.UUID

class ResponseActionResponse(ResponseActionBase):
    id: uuid.UUID
    incident_id: Optional[uuid.UUID] = None
    alert_id: Optional[uuid.UUID] = None
    application_id: uuid.UUID
    status: ResponseActionStatus
    requested_by: uuid.UUID
    approved_by: Optional[uuid.UUID] = None
    requested_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    result_summary: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ResponseActionListResponse(BaseModel):
    items: List[ResponseActionResponse]
    total: int
    page: int
    page_size: int

class ResponseRejectRequest(BaseModel):
    reason: str = Field(..., description="Reason for rejection")

class ResponsePolicyBase(BaseModel):
    name: str
    enabled: bool = False
    action_type: str
    minimum_severity: Optional[str] = None
    minimum_risk_score: Optional[int] = None
    require_approval: bool = True

class ResponsePolicyCreate(ResponsePolicyBase):
    application_id: uuid.UUID

class ResponsePolicyUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    action_type: Optional[str] = None
    minimum_severity: Optional[str] = None
    minimum_risk_score: Optional[int] = None
    require_approval: Optional[bool] = None

class ResponsePolicyResponse(ResponsePolicyBase):
    id: uuid.UUID
    application_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResponsePolicyListResponse(BaseModel):
    items: List[ResponsePolicyResponse]
    total: int
    page: int
    page_size: int
