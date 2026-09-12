import uuid
import enum
from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class EvidenceType(str, enum.Enum):
    SECURITY_EVENT = "SECURITY_EVENT"
    ALERT = "ALERT"
    CORRELATION = "CORRELATION"

class IncidentEvidence(BaseModel):
    __tablename__ = "incident_evidence"

    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type: Mapped[EvidenceType] = mapped_column(String(50), nullable=False)
    
    # The ID of the SecurityEvent, Alert, or Correlation
    evidence_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    
    added_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="evidence")
    user: Mapped[Optional["User"]] = relationship("User")
