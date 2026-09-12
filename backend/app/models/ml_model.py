import uuid
import enum
from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, Float, Boolean, Table, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class MLModelStatus(str, enum.Enum):
    TRAINING = "TRAINING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FAILED = "FAILED"

class MLModel(BaseModel):
    __tablename__ = "ml_models"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. ISOLATION_FOREST
    feature_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Optional because it could be a global model
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    
    status: Mapped[MLModelStatus] = mapped_column(String(50), default=MLModelStatus.TRAINING.value, nullable=False)
    
    trained_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    training_window_start: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    training_window_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    training_sample_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    baseline_statistics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    model_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    application: Mapped[Optional["Application"]] = relationship("Application", back_populates="ml_models")
