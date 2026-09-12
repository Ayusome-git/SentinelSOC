import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class CorrelationRule(BaseModel):
    __tablename__ = "correlation_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(50), default="SEQUENCE", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    time_window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # JSON array defining the ordered sequence of events/alerts
    # Example: [{"type": "event", "event_type": "LOGIN_FAILED"}, {"type": "alert", "alert_title": "Brute Force"}]
    sequence: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    
    # JSON array defining relationship constraints
    # Example: ["SAME_SOURCE_IP", "SAME_APPLICATION"]
    relationships: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    application: Mapped[Optional["Application"]] = relationship("Application")
    creator: Mapped[Optional["User"]] = relationship("User")
