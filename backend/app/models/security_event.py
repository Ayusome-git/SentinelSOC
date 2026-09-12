import uuid
import enum
from typing import List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, Integer, Table, Column, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class EventSeverity(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

incident_events = Table(
    "incident_events",
    BaseModel.metadata,
    Column("incident_id", ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True),
    Column("security_event_id", ForeignKey("security_events.id", ondelete="CASCADE"), primary_key=True),
    Column("sequence_position", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False),
)

class SecurityEvent(BaseModel):
    __tablename__ = "security_events"

    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[EventSeverity] = mapped_column(String(50), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), index=True, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    
    http_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    request_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="events")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="security_event")
    incidents: Mapped[List["Incident"]] = relationship("Incident", secondary=incident_events, back_populates="events")

    # Composite Indexes
    __table_args__ = (
        Index("ix_security_events_app_timestamp", "application_id", "timestamp"),
        Index("ix_security_events_ip_timestamp", "source_ip", "timestamp"),
        Index("ix_security_events_type_timestamp", "event_type", "timestamp"),
        Index("ix_security_events_sev_timestamp", "severity", "timestamp"),
    )
