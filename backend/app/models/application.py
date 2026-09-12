import uuid
import enum
from typing import List, Optional
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class AppEnvironment(str, enum.Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

class AppStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class Application(BaseModel):
    __tablename__ = "applications"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    environment: Mapped[AppEnvironment] = mapped_column(String(50), default=AppEnvironment.DEVELOPMENT.value, nullable=False)
    status: Mapped[AppStatus] = mapped_column(String(50), default=AppStatus.ACTIVE.value, nullable=False)
    
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="applications")
    api_keys: Mapped[List["ApplicationApiKey"]] = relationship("ApplicationApiKey", back_populates="application")
    events: Mapped[List["SecurityEvent"]] = relationship("SecurityEvent", back_populates="application")
    alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="application")
    correlations: Mapped[List["Correlation"]] = relationship("Correlation", back_populates="application")
    incidents: Mapped[List["Incident"]] = relationship("Incident", back_populates="application")
