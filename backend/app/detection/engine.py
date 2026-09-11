from typing import List
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.models.detection_rule import DetectionRule

class DetectionEngine:
    @staticmethod
    def get_applicable_rules(db: Session, event: SecurityEvent) -> List[DetectionRule]:
        """Fetch enabled rules matching event type and application."""
        stmt = select(DetectionRule).where(
            DetectionRule.enabled == True,
            DetectionRule.event_type == event.event_type,
            or_(
                DetectionRule.application_id == event.application_id,
                DetectionRule.application_id.is_(None)
            )
        )
        return list(db.scalars(stmt).all())
