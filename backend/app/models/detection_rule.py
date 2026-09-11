import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class DetectionRule(BaseModel):
    __tablename__ = "detection_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), default="THRESHOLD", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    threshold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    window_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    group_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mitre_technique: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pattern: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    distinct_field: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    application: Mapped[Optional["Application"]] = relationship("Application")
    creator: Mapped[Optional["User"]] = relationship("User")
