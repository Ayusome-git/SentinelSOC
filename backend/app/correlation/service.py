import logging
import hashlib
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.models.security_event import SecurityEvent
from app.models.alert import Alert, AlertStatus
from app.models.correlation_rule import CorrelationRule
from app.models.correlation import Correlation, CorrelationStatus, correlation_events, correlation_alerts
from app.correlation.engine import CorrelationEngine
from app.correlation.evaluator import SequenceEvaluator

logger = logging.getLogger(__name__)

class CorrelationService:
    @staticmethod
    def evaluate_event(db: Session, event: SecurityEvent) -> None:
        try:
            rules = CorrelationEngine.get_applicable_rules_for_event(db, event)
            for rule in rules:
                if rule.rule_type == "SEQUENCE":
                    result = SequenceEvaluator.evaluate(db, rule, event)
                    if result.matched:
                        CorrelationService._create_correlation(db, rule, event.application_id, result.evidence_items)
        except Exception as e:
            logger.error(f"Error during correlation evaluation for event {event.id}: {str(e)}")

    @staticmethod
    def evaluate_alert(db: Session, alert: Alert) -> None:
        try:
            rules = CorrelationEngine.get_applicable_rules_for_alert(db, alert)
            for rule in rules:
                if rule.rule_type == "SEQUENCE":
                    result = SequenceEvaluator.evaluate(db, rule, alert)
                    if result.matched:
                        CorrelationService._create_correlation(db, rule, alert.application_id, result.evidence_items)
        except Exception as e:
            logger.error(f"Error during correlation evaluation for alert {alert.id}: {str(e)}")

    @staticmethod
    def _create_correlation(db: Session, rule: CorrelationRule, application_id: Any, evidence_items: list[Any]) -> None:
        # Determine deterministic hash to prevent duplicates
        # Hash combines rule id, application id, and the IDs of all evidence items
        hash_input = f"{rule.id}:{application_id}"
        
        first_event_at = None
        last_event_at = None
        
        for idx, item in enumerate(evidence_items):
            if isinstance(item, SecurityEvent):
                hash_input += f":event_{item.id}"
                ts = item.timestamp
            else:
                hash_input += f":alert_{item.id}"
                ts = item.detected_at
                
            if first_event_at is None or ts < first_event_at:
                first_event_at = ts
            if last_event_at is None or ts > last_event_at:
                last_event_at = ts
                
        unique_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        # Check for duplicate
        existing = db.execute(select(Correlation).where(Correlation.unique_hash == unique_hash)).scalars().first()
        if existing:
            return
            
        correlation = Correlation(
            name=rule.name,
            description=f"Correlated attack sequence detected based on rule '{rule.name}'.",
            severity=rule.severity,
            status=CorrelationStatus.DETECTED.value,
            rule_id=rule.id,
            application_id=application_id,
            first_event_at=first_event_at,
            last_event_at=last_event_at,
            unique_hash=unique_hash
        )
        
        db.add(correlation)
        db.flush() # flush to get correlation.id
        
        # Associate evidence
        for idx, item in enumerate(evidence_items):
            if isinstance(item, SecurityEvent):
                db.execute(
                    correlation_events.insert().values(
                        correlation_id=correlation.id,
                        security_event_id=item.id,
                        sequence_position=idx
                    )
                )
            elif isinstance(item, Alert):
                db.execute(
                    correlation_alerts.insert().values(
                        correlation_id=correlation.id,
                        alert_id=item.id,
                        sequence_position=idx
                    )
                )
                
        # Generate higher-level Alert referencing this correlation
        alert_desc = f"A correlation rule '{rule.name}' detected an attack sequence involving {len(evidence_items)} steps."
        
        new_alert = Alert(
            application_id=application_id,
            title=rule.name,
            description=alert_desc,
            severity=rule.severity,
            status=AlertStatus.OPEN.value,
            correlation_id=correlation.id,
            detected_at=last_event_at
        )
        db.add(new_alert)
        
        db.commit()
        db.refresh(correlation)
        
        # Calculate risk score for correlation (and its alert)
        from app.risk.service import RiskScoringService
        RiskScoringService.recalculate_correlation(db, correlation.id)
