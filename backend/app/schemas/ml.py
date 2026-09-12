from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class MLModelBase(BaseModel):
    name: str
    model_type: str
    feature_version: str
    application_id: Optional[UUID] = None
    status: str
    training_sample_count: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None

class MLModelResponse(MLModelBase):
    id: UUID
    trained_at: Optional[datetime] = None
    training_window_start: Optional[datetime] = None
    training_window_end: Optional[datetime] = None
    baseline_statistics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MLTrainRequest(BaseModel):
    application_id: Optional[UUID] = None
    training_days: int = 7
