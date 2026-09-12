import uuid
import enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Table, Column, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel, Base

class CorrelationStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"

correlation_events = Table(
    "correlation_events",
    Base.metadata,
    Column("correlation_id", ForeignKey("correlations.id", ondelete="CASCADE"), primary_key=True),
    Column("security_event_id", ForeignKey("security_events.id", ondelete="CASCADE"), primary_key=True),
    Column("sequence_position", Integer, nullable=False)
)

correlation_alerts = Table(
    "correlation_alerts",
    Base.metadata,
    Column("correlation_id", ForeignKey("correlations.id", ondelete="CASCADE"), primary_key=True),
    Column("alert_id", ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True),
    Column("sequence_position", Integer, nullable=False)
)

class Correlation(BaseModel):
    __tablename__ = "correlations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[CorrelationStatus] = mapped_column(String(50), default=CorrelationStatus.DETECTED.value, nullable=False)
    
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    risk_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("correlation_rules.id", ondelete="SET NULL"), nullable=True)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    
    first_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    unique_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Relationships
    rule: Mapped[Optional["CorrelationRule"]] = relationship("CorrelationRule")
    application: Mapped["Application"] = relationship("Application", back_populates="correlations")
    events: Mapped[List["SecurityEvent"]] = relationship("SecurityEvent", secondary=correlation_events)
    alerts_evidence: Mapped[List["Alert"]] = relationship("Alert", secondary=correlation_alerts, foreign_keys=[correlation_alerts.c.correlation_id, correlation_alerts.c.alert_id])
    
    # Generated alert
    alert: Mapped[Optional["Alert"]] = relationship("Alert", back_populates="correlation", foreign_keys="[Alert.correlation_id]")
    incidents: Mapped[List["Incident"]] = relationship("Incident", back_populates="correlation")

    @property
    def generated_alert_id(self):
        return self.alert.id if self.alert else None
