from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from uuid import UUID

class ThreatIntelLookupRequest(BaseModel):
    indicator: str = Field(..., description="The indicator value (e.g. 192.168.1.1)")
    indicator_type: str = Field(..., description="The type of the indicator (e.g. IP_ADDRESS, DOMAIN, HASH_SHA256)")

class ThreatIntelIndicatorBase(BaseModel):
    indicator: str
    indicator_type: str
    source: str
    malicious: bool
    confidence: int
    reputation: Optional[str] = None
    categories: Optional[List[str]] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    reference: Optional[str] = None

class ThreatIntelIndicatorResponse(ThreatIntelIndicatorBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ThreatIntelListResponse(BaseModel):
    items: List[ThreatIntelIndicatorResponse]
    total: int
    page: int
    page_size: int

class ThreatIntelLookupResponse(BaseModel):
    found: bool
    indicator: str
    indicator_type: str
    malicious: bool
    confidence: int
    reputation: Optional[str] = None
    categories: Optional[List[str]] = None
    source: str
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    reference: Optional[str] = None
