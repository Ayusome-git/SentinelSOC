import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class DetectionRuleBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    rule_type: str = Field(default="THRESHOLD", max_length=50)
    enabled: bool = Field(default=True)
    severity: str = Field(..., max_length=50)
    event_type: str = Field(..., max_length=100)
    threshold: Optional[int] = Field(None, ge=1)
    window_seconds: Optional[int] = Field(None, gt=0)
    group_by: Optional[str] = Field(None, max_length=100)
    
    category: Optional[str] = Field(None, max_length=100)
    mitre_technique: Optional[str] = Field(None, max_length=50)
    pattern: Optional[str] = Field(None, max_length=2000)
    distinct_field: Optional[str] = Field(None, max_length=100)
    
    application_id: Optional[uuid.UUID] = None

class DetectionRuleCreate(DetectionRuleBase):
    pass

class DetectionRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    enabled: Optional[bool] = None
    severity: Optional[str] = Field(None, max_length=50)
    threshold: Optional[int] = Field(None, ge=1)
    window_seconds: Optional[int] = Field(None, gt=0)
    group_by: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    mitre_technique: Optional[str] = Field(None, max_length=50)
    pattern: Optional[str] = Field(None, max_length=2000)
    distinct_field: Optional[str] = Field(None, max_length=100)

class DetectionRuleStatusUpdate(BaseModel):
    enabled: bool

class DetectionRuleResponse(DetectionRuleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class DetectionRuleListResponse(BaseModel):
    items: List[DetectionRuleResponse]
    total: int
    page: int
    size: int
