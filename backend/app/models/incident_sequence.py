import uuid
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class IncidentSequence(Base):
    __tablename__ = "incident_sequences"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="INCIDENT")
    last_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
