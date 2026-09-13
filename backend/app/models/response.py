import uuid
import enum
from typing import Optional, Dict, Any, List
from sqlalchemy import String, ForeignKey, Boolean, Integer, DateTime, JSON, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import BaseModel

class ResponseActionStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ApplicationResponseCapability(BaseModel):
    __tablename__ = "application_response_capabilities"

    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    configuration: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    application: Mapped["Application"] = relationship("Application", back_populates="response_capabilities")

class ResponseAction(BaseModel):
    __tablename__ = "response_actions"

    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ResponseActionStatus] = mapped_column(String(50), default=ResponseActionStatus.PENDING_APPROVAL.value, nullable=False, index=True)
    
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    incident: Mapped[Optional["Incident"]] = relationship("Incident", back_populates="response_actions")
    alert: Mapped[Optional["Alert"]] = relationship("Alert")
    application: Mapped["Application"] = relationship("Application", back_populates="response_actions")
    requester: Mapped["User"] = relationship("User", foreign_keys=[requested_by])
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by])

class ResponsePolicy(BaseModel):
    __tablename__ = "response_policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    minimum_severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    minimum_risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    require_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    application: Mapped["Application"] = relationship("Application")
    creator: Mapped["User"] = relationship("User")
