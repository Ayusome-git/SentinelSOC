from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.application import AppEnvironment, AppStatus


class ApplicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Name of the application")
    description: Optional[str] = Field(None, max_length=1000)
    environment: AppEnvironment = Field(default=AppEnvironment.DEVELOPMENT)


class ApplicationCreate(ApplicationBase):
    slug: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe unique identifier (lowercase, alphanumeric, hyphens)"
    )
    owner_id: uuid.UUID


class ApplicationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    environment: Optional[AppEnvironment] = None
    owner_id: Optional[uuid.UUID] = None


class ApplicationStatusUpdate(BaseModel):
    status: AppStatus


class ApplicationResponse(ApplicationBase):
    id: uuid.UUID
    slug: str
    status: AppStatus
    owner_id: uuid.UUID
    owner_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    page: int
    page_size: int
    total: int
