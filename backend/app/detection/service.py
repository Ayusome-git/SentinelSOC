import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.models.security_event import SecurityEvent
from app.models.alert import Alert, AlertStatus
from app.models.detection_rule import DetectionRule
from app.detection.engine import DetectionEngine
from app.detection.evaluator import ThresholdEvaluator

logger = logging.getLogger(__name__)

class DetectionService:
    @staticmethod
    def evaluate_event(db: Session, event: SecurityEvent) -> None:
        try:
            rules = DetectionEngine.get_applicable_rules(db, event)
            for rule in rules:
                is_triggered = False
                if rule.rule_type == "THRESHOLD":
                    is_triggered = ThresholdEvaluator.evaluate(db, rule, event)
                
                if is_triggered:
                    DetectionService._generate_alert(db, rule, event)
        except Exception as e:
            logger.error(f"Error during detection evaluation for event {event.id}: {str(e)}")

    @staticmethod
    def _generate_alert(db: Session, rule: DetectionRule, event: SecurityEvent) -> None:
        group_val = getattr(event, rule.group_by, None) if rule.group_by else None
        
        alert_title = rule.name
        if group_val:
            alert_title = f"{rule.name} ({rule.group_by}: {group_val})"
            
        stmt = select(Alert).where(
            and_(
                Alert.rule_id == rule.id,
                Alert.application_id == event.application_id,
                Alert.title == alert_title,
                Alert.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])
            )
        )
        existing_alert = db.execute(stmt).scalars().first()
        if existing_alert:
            return # Suppress duplicate
            
        new_alert = Alert(
            application_id=event.application_id,
            security_event_id=event.id,
            title=alert_title,
            description=f"Rule '{rule.name}' triggered.\n{rule.description or ''}",
            severity=rule.severity,
            status=AlertStatus.OPEN.value,
            rule_id=rule.id,
            detected_at=event.timestamp
        )
        db.add(new_alert)
        db.commit()
