from pydantic import BaseModel
import uuid
from typing import Optional
from datetime import datetime

class DetectionResult(BaseModel):
    rule_id: uuid.UUID
    event_id: uuid.UUID
    application_id: uuid.UUID
    severity: str
    title: str
    description: str
    detected_at: datetime
    matched: bool = True
