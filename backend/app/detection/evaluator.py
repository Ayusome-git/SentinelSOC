from datetime import timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.models.detection_rule import DetectionRule

class ThresholdEvaluator:
    @staticmethod
    def evaluate(db: Session, rule: DetectionRule, current_event: SecurityEvent) -> bool:
        """
        Evaluates if the threshold is reached for the given rule and event.
        Returns True if threshold is met, False otherwise.
        """
        group_val = getattr(current_event, rule.group_by, None) if rule.group_by else None
        
        # If the rule requires group_by and the event doesn't have it, skip
        if rule.group_by and group_val is None:
            return False

        window_start = current_event.timestamp - timedelta(seconds=rule.window_seconds)
        
        conditions = [
            SecurityEvent.event_type == rule.event_type,
            SecurityEvent.timestamp >= window_start,
            SecurityEvent.timestamp <= current_event.timestamp,
            SecurityEvent.application_id == current_event.application_id
        ]
        
        if rule.group_by:
            group_attr = getattr(SecurityEvent, rule.group_by)
            conditions.append(group_attr == group_val)
            
        stmt = select(func.count(SecurityEvent.id)).where(and_(*conditions))
        
        count = db.execute(stmt).scalar() or 0
        return count >= rule.threshold
