import logging
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.models.security_event import SecurityEvent
from app.models.alert import Alert, AlertStatus
from app.models.detection_rule import DetectionRule
from app.detection.engine import DetectionEngine
from app.detection.evaluator import ThresholdEvaluator, PatternEvaluator, SequenceEvaluator
from app.detection.types import DetectionResult

logger = logging.getLogger(__name__)

class DetectionService:
    @staticmethod
    def evaluate_event(db: Session, event: SecurityEvent) -> None:
        try:
            rules = DetectionEngine.get_applicable_rules(db, event)
            for rule in rules:
                result = None
                if rule.rule_type == "THRESHOLD":
                    result = ThresholdEvaluator.evaluate(db, rule, event)
                elif rule.rule_type == "PATTERN":
                    result = PatternEvaluator.evaluate(db, rule, event)
                elif rule.rule_type == "SEQUENCE":
                    result = SequenceEvaluator.evaluate(db, rule, event)
                
                if result and result.matched:
                    DetectionService._generate_alert(db, result)
        except Exception as e:
            logger.error(f"Error during detection evaluation for event {event.id}: {str(e)}")

    @staticmethod
    def _generate_alert(db: Session, result: DetectionResult) -> None:
        stmt = select(Alert).where(
            and_(
                Alert.rule_id == result.rule_id,
                Alert.application_id == result.application_id,
                Alert.title == result.title,
                Alert.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])
            )
        )
        existing_alert = db.execute(stmt).scalars().first()
        if existing_alert:
            return # Suppress duplicate
            
        new_alert = Alert(
            application_id=result.application_id,
            security_event_id=result.event_id,
            title=result.title,
            description=result.description,
            severity=result.severity,
            status=AlertStatus.OPEN.value,
            rule_id=result.rule_id,
            detected_at=result.detected_at
        )
        db.add(new_alert)
        db.commit()
