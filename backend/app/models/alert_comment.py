import uuid
from typing import Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class AlertComment(BaseModel):
    __tablename__ = "alert_comments"

    alert_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment: Mapped[str] = mapped_column(String(4000), nullable=False)

    # Relationships
    alert: Mapped["Alert"] = relationship("Alert", back_populates="comments")
    user: Mapped["User"] = relationship("User")
