from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.correlation_rule import CorrelationRule

class CorrelationEngine:
    @staticmethod
    def get_applicable_rules_for_event(db: Session, event: SecurityEvent) -> List[CorrelationRule]:
        """Fetch enabled correlation rules where the event type matches the last sequence element."""
        # Performance optimization: we fetch all enabled rules for the application and filter in python
        # because sequence is a JSONB array and doing deep json search in postgres for the last element is complex.
        # Since correlation rules are generally few, this is acceptable.
        stmt = select(CorrelationRule).where(
            CorrelationRule.enabled == True,
            or_(
                CorrelationRule.application_id == event.application_id,
                CorrelationRule.application_id.is_(None)
            )
        )
        all_rules = list(db.scalars(stmt).all())
        
        applicable = []
        for rule in all_rules:
            if not rule.sequence:
                continue
            last_item = rule.sequence[-1]
            if last_item.get("type") == "event" and last_item.get("event_type") == event.event_type:
                applicable.append(rule)
                
        return applicable

    @staticmethod
    def get_applicable_rules_for_alert(db: Session, alert: Alert) -> List[CorrelationRule]:
        """Fetch enabled correlation rules where the alert title/rule_id matches the last sequence element."""
        stmt = select(CorrelationRule).where(
            CorrelationRule.enabled == True,
            or_(
                CorrelationRule.application_id == alert.application_id,
                CorrelationRule.application_id.is_(None)
            )
        )
        all_rules = list(db.scalars(stmt).all())
        
        applicable = []
        for rule in all_rules:
            if not rule.sequence:
                continue
            last_item = rule.sequence[-1]
            if last_item.get("type") == "alert" and last_item.get("alert_title") == alert.title:
                applicable.append(rule)
                
        return applicable
