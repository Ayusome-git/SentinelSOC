import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel
from enum import Enum

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONTAINED = "CONTAINED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Incident(BaseModel):
    __tablename__ = "incidents"

    incident_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[IncidentStatus] = mapped_column(String(50), default=IncidentStatus.OPEN.value, nullable=False)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    correlation_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("correlations.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    detected_at: Mapped[datetime] = mapped_column(nullable=False)
    contained_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="incidents")
    correlation: Mapped[Optional["Correlation"]] = relationship("Correlation", back_populates="incidents")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_incidents")
    alerts: Mapped[List["Alert"]] = relationship("Alert", secondary="incident_alerts", back_populates="incidents")
    events: Mapped[List["SecurityEvent"]] = relationship("SecurityEvent", secondary="incident_events", back_populates="incidents")
    comments: Mapped[List["IncidentComment"]] = relationship("IncidentComment", back_populates="incident", cascade="all, delete-orphan", order_by="asc(IncidentComment.created_at)")
    evidence: Mapped[List["IncidentEvidence"]] = relationship("IncidentEvidence", back_populates="incident", cascade="all, delete-orphan", order_by="asc(IncidentEvidence.created_at)")
