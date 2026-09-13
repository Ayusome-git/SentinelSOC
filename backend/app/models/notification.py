import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import enum
from sqlalchemy import String, ForeignKey, Boolean, DateTime, Integer, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class NotificationType(str, enum.Enum):
    CRITICAL_ALERT = "CRITICAL_ALERT"
    HIGH_RISK_ALERT = "HIGH_RISK_ALERT"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_ASSIGNED = "INCIDENT_ASSIGNED"
    INCIDENT_ESCALATED = "INCIDENT_ESCALATED"
    RESPONSE_ACTION_FAILED = "RESPONSE_ACTION_FAILED"
    ML_ANOMALY_DETECTED = "ML_ANOMALY_DETECTED"
    THREAT_INTELLIGENCE_MATCH = "THREAT_INTELLIGENCE_MATCH"

class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    READ = "READ"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=True)
    alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True, index=True)
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    response_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("response_actions.id", ondelete="CASCADE"), nullable=True, index=True)
    
    notification_type: Mapped[NotificationType] = mapped_column(String(50), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    status: Mapped[NotificationStatus] = mapped_column(String(50), default=NotificationStatus.PENDING.value, nullable=False, index=True)
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    @property
    def is_read(self) -> bool:
        return self.status == NotificationStatus.READ
    application: Mapped[Optional["Application"]] = relationship("Application")

    __table_args__ = (
        Index("ix_notification_type_user", "notification_type", "user_id"),
    )

class NotificationPreference(BaseModel):
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type: Mapped[NotificationType] = mapped_column(String(50), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(String(20), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="notification_preferences")

    __table_args__ = (
        UniqueConstraint("user_id", "notification_type", "channel", name="uq_user_type_channel"),
    )
