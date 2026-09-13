import uuid
import enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, Table, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel, Base

class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"

class DetectionSource(str, enum.Enum):
    RULE = "RULE"
    ML = "ML"
    CORRELATION = "CORRELATION"
    MANUAL = "MANUAL"

# Association table for incidents <-> alerts
incident_alerts = Table(
    "incident_alerts",
    Base.metadata,
    Column("incident_id", ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True),
    Column("alert_id", ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True),
)

class Alert(BaseModel):
    __tablename__ = "alerts"

    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    security_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("security_events.id", ondelete="SET NULL"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. INFO, LOW, MEDIUM, HIGH, CRITICAL
    status: Mapped[AlertStatus] = mapped_column(String(50), default=AlertStatus.OPEN.value, nullable=False)
    detection_source: Mapped[DetectionSource] = mapped_column(String(50), default=DetectionSource.RULE.value, nullable=False)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # LOW, MODERATE, HIGH, CRITICAL
    risk_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True) # Future use
    correlation_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("correlations.id", ondelete="SET NULL"), nullable=True)
    
    detected_at: Mapped[datetime] = mapped_column(nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="alerts")
    security_event: Mapped[Optional["SecurityEvent"]] = relationship("SecurityEvent", back_populates="alerts")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_alerts")
    incidents: Mapped[List["Incident"]] = relationship("Incident", secondary=incident_alerts, back_populates="alerts")
    correlation: Mapped[Optional["Correlation"]] = relationship("Correlation", back_populates="alert", foreign_keys=[correlation_id])
    comments: Mapped[List["AlertComment"]] = relationship("AlertComment", back_populates="alert", cascade="all, delete-orphan", order_by="asc(AlertComment.created_at)")
    threat_intel_indicators: Mapped[List["AlertThreatIntel"]] = relationship("AlertThreatIntel", back_populates="alert", cascade="all, delete-orphan")
