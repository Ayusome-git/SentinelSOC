import uuid
import enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(String(50), default=UserRole.VIEWER.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="owner", cascade="all, delete-orphan")
    assigned_alerts: Mapped[List["Alert"]] = relationship("Alert", back_populates="assignee")
    assigned_incidents: Mapped[List["Incident"]] = relationship("Incident", back_populates="assignee")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    notification_preferences: Mapped[List["NotificationPreference"]] = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan")
