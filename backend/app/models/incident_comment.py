import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class IncidentComment(BaseModel):
    __tablename__ = "incident_comments"

    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    comment: Mapped[str] = mapped_column(String(5000), nullable=False)

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="comments")
    author: Mapped["User"] = relationship("User")
