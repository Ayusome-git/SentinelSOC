from datetime import timedelta
import re
import urllib.parse
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.models.detection_rule import DetectionRule
from app.detection.types import DetectionResult

class ThresholdEvaluator:
    @staticmethod
    def evaluate(db: Session, rule: DetectionRule, current_event: SecurityEvent) -> DetectionResult | None:
        if not rule.threshold or not rule.window_seconds:
            return None
            
        group_val = getattr(current_event, rule.group_by, None) if rule.group_by else None
        
        # If the rule requires group_by and the event doesn't have it, skip
        if rule.group_by and group_val is None:
            return None

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
            
        if rule.distinct_field:
            distinct_attr = getattr(SecurityEvent, rule.distinct_field)
            stmt = select(func.count(func.distinct(distinct_attr))).where(and_(*conditions))
        else:
            stmt = select(func.count(SecurityEvent.id)).where(and_(*conditions))
        
        count = db.execute(stmt).scalar() or 0
        
        if count >= rule.threshold:
            title = rule.name
            if group_val:
                title = f"{rule.name} ({rule.group_by}: {group_val})"
            desc = f"Rule '{rule.name}' triggered.\n{rule.description or ''}\nDetected {count} events."
            if rule.distinct_field:
                desc += f" (Distinct {rule.distinct_field}s)."
            return DetectionResult(
                rule_id=rule.id,
                event_id=current_event.id,
                application_id=current_event.application_id,
                severity=rule.severity,
                title=title,
                description=desc,
                detected_at=current_event.timestamp
            )
        return None

class PatternEvaluator:
    @staticmethod
    def _decode_defensively(text: str, max_depth: int = 3) -> str:
        if not text:
            return ""
        current = text
        for _ in range(max_depth):
            decoded = urllib.parse.unquote(current)
            if decoded == current:
                break
            current = decoded
        return current

    @staticmethod
    def evaluate(db: Session, rule: DetectionRule, current_event: SecurityEvent) -> DetectionResult | None:
        if not rule.pattern:
            return None

        # Gather target strings
        targets = []
        if current_event.request_path:
            targets.append(current_event.request_path)
        if current_event.message:
            targets.append(current_event.message)
        if current_event.metadata_:
            targets.append(str(current_event.metadata_))

        for target in targets:
            decoded_target = PatternEvaluator._decode_defensively(target)
            if re.search(rule.pattern, decoded_target, re.IGNORECASE):
                title = rule.name
                group_val = getattr(current_event, rule.group_by, None) if rule.group_by else None
                if group_val:
                    title = f"{rule.name} ({rule.group_by}: {group_val})"
                
                desc = f"Rule '{rule.name}' triggered.\n{rule.description or ''}\nPattern matched."
                return DetectionResult(
                    rule_id=rule.id,
                    event_id=current_event.id,
                    application_id=current_event.application_id,
                    severity=rule.severity,
                    title=title,
                    description=desc,
                    detected_at=current_event.timestamp
                )
        return None

class SequenceEvaluator:
    @staticmethod
    def evaluate(db: Session, rule: DetectionRule, current_event: SecurityEvent) -> DetectionResult | None:
        # Example hardcoded logic for Privilege Escalation: ADMIN_ACTION after PERMISSION_DENIED
        if current_event.event_type != "ADMIN_ACTION" or not current_event.user_id:
            return None
            
        if not rule.window_seconds:
            return None

        window_start = current_event.timestamp - timedelta(seconds=rule.window_seconds)
        
        # Look for PERMISSION_DENIED
        stmt = select(SecurityEvent.id).where(
            and_(
                SecurityEvent.event_type == "PERMISSION_DENIED",
                SecurityEvent.user_id == current_event.user_id,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.timestamp < current_event.timestamp,
                SecurityEvent.application_id == current_event.application_id
            )
        ).limit(1)
        
        has_prior_denied = db.execute(stmt).scalar()
        if has_prior_denied:
            title = f"{rule.name} (user_id: {current_event.user_id})"
            desc = f"Rule '{rule.name}' triggered.\n{rule.description or ''}\nADMIN_ACTION observed shortly after PERMISSION_DENIED."
            return DetectionResult(
                rule_id=rule.id,
                event_id=current_event.id,
                application_id=current_event.application_id,
                severity=rule.severity,
                title=title,
                description=desc,
                detected_at=current_event.timestamp
            )
        return None
