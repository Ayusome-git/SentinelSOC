from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.correlation import CorrelationStatus
from app.schemas.security_event import EventResponse

class CorrelationRuleBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    rule_type: str = Field(default="SEQUENCE", max_length=50)
    enabled: bool = True
    severity: str = Field(..., max_length=50)
    time_window_seconds: int = Field(..., gt=0)
    sequence: List[Dict[str, Any]]
    relationships: List[str]
    application_id: Optional[UUID] = None

class CorrelationRuleCreate(CorrelationRuleBase):
    pass

class CorrelationRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    enabled: Optional[bool] = None
    severity: Optional[str] = Field(None, max_length=50)
    time_window_seconds: Optional[int] = Field(None, gt=0)
    sequence: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[List[str]] = None
    application_id: Optional[UUID] = None

class CorrelationRuleStatusUpdate(BaseModel):
    enabled: bool

class CorrelationRuleResponse(CorrelationRuleBase):
    id: UUID
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True

class CorrelationRuleListResponse(BaseModel):
    items: List[CorrelationRuleResponse]
    total: int
    page: int
    page_size: int

class CorrelationBase(BaseModel):
    name: str
    description: Optional[str]
    severity: str
    status: str
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    risk_factors: Optional[Dict[str, Any]] = None
    rule_id: Optional[UUID]
    application_id: UUID
    first_event_at: datetime
    last_event_at: datetime
    created_at: datetime

class CorrelationStatusUpdate(BaseModel):
    status: CorrelationStatus

class CorrelationEvidence(BaseModel):
    id: UUID
    type: str # "EVENT" or "ALERT"
    timestamp: datetime
    data: Any # EventResponse or AlertResponse
    sequence_position: int

class CorrelationResponse(CorrelationBase):
    id: UUID
    generated_alert_id: Optional[UUID] = None
    rule: Optional[CorrelationRuleResponse] = None
    evidence: Optional[List[CorrelationEvidence]] = None
    
    class Config:
        from_attributes = True

class CorrelationListResponse(BaseModel):
    items: List[CorrelationResponse]
    total: int
    page: int
    page_size: int
