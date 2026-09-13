from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
from app.db.base import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class ThreatIntelCache(BaseModel):
    __tablename__ = "threat_intel_cache"

    indicator: Mapped[str] = mapped_column(String, nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    result: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("indicator", "indicator_type", "provider", name="uix_ti_cache_indicator_provider"),
    )

class ThreatIntelIndicator(BaseModel):
    __tablename__ = "threat_intel_indicators"

    indicator: Mapped[str] = mapped_column(String, nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    malicious: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    reputation: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    alerts: Mapped[List["AlertThreatIntel"]] = relationship("AlertThreatIntel", back_populates="threat_intel_indicator")

class AlertThreatIntel(BaseModel):
    __tablename__ = "alert_threat_intel"

    alert_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    threat_intel_indicator_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("threat_intel_indicators.id", ondelete="CASCADE"), nullable=False, index=True)

    alert: Mapped["Alert"] = relationship("Alert", back_populates="threat_intel_indicators")
    threat_intel_indicator: Mapped["ThreatIntelIndicator"] = relationship("ThreatIntelIndicator", back_populates="alerts")

    __table_args__ = (
        UniqueConstraint("alert_id", "threat_intel_indicator_id", name="uix_alert_ti_indicator"),
    )
