from pydantic import BaseModel, Field, IPvAnyAddress, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from app.models.security_event import EventSeverity

class EventType(str, Enum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ADMIN_LOGIN = "ADMIN_LOGIN"
    ADMIN_ACTION = "ADMIN_ACTION"
    API_REQUEST = "API_REQUEST"
    API_ERROR = "API_ERROR"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SUSPICIOUS_REQUEST = "SUSPICIOUS_REQUEST"

class EventCreate(BaseModel):
    event_type: EventType
    severity: EventSeverity
    timestamp: datetime
    source_ip: IPvAnyAddress
    message: str = Field(..., max_length=2000)

    user_id: Optional[str] = Field(None, max_length=255)
    username: Optional[str] = Field(None, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    request_id: Optional[str] = Field(None, max_length=255)
    http_method: Optional[str] = Field(None, max_length=10)
    request_path: Optional[str] = Field(None, max_length=1000)
    user_agent: Optional[str] = Field(None, max_length=1000)
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")

    model_config = ConfigDict(populate_by_name=True)

class EventResponse(BaseModel):
    id: UUID
    application_id: UUID
    application_name: str
    event_type: str
    severity: str
    timestamp: datetime
    
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    http_method: Optional[str] = None
    request_path: Optional[str] = None
    user_agent: Optional[str] = None
    
    message: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, validation_alias="metadata_", serialization_alias="metadata")
    
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class EventListResponse(BaseModel):
    total: int
    items: List[EventResponse]
    page: int
    page_size: int

class EventTimelinePoint(BaseModel):
    timestamp: datetime
    count: int

class EventAnalyticsResponse(BaseModel):
    total: int
    severity_counts: Dict[str, int]
    event_type_counts: Dict[str, int]
    application_counts: Dict[str, int]
    source_ip_counts: Dict[str, int]
    timeline: List[EventTimelinePoint]
