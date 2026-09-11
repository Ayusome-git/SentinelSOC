import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Meaningful name for the API key")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")

class ApiKeyStatusUpdate(BaseModel):
    is_active: bool

class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    created_by: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class ApiKeyCreateResponse(ApiKeyResponse):
    api_key: str = Field(..., description="The raw secret key. This will only be returned once.")
