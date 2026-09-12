from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.correlation_rule import CorrelationRule
import logging

logger = logging.getLogger(__name__)

class EvaluatorResult:
    def __init__(self, matched: bool, evidence_items: List[Any] = None):
        self.matched = matched
        self.evidence_items = evidence_items or []

class SequenceEvaluator:
    @staticmethod
    def evaluate(db: Session, rule: CorrelationRule, anchor_item: Any) -> EvaluatorResult:
        """
        anchor_item is the event/alert that triggered the evaluation.
        It corresponds to the LAST item in the rule.sequence.
        We must search backwards in time to find the preceding items.
        """
        if not rule.sequence or len(rule.sequence) < 2:
            return EvaluatorResult(matched=False)
            
        time_window = timedelta(seconds=rule.time_window_seconds)
        
        # anchor_timestamp is the time of the latest event/alert
        anchor_timestamp = anchor_item.timestamp if isinstance(anchor_item, SecurityEvent) else anchor_item.detected_at
        window_start = anchor_timestamp - time_window
        
        # We will build a list of evidence backwards
        evidence_chain = [anchor_item]
        
        # We process the sequence in reverse, starting from the second to last item
        current_time_bound = anchor_timestamp
        
        # Keep track of relationship constraints from the anchor item
        constraints = {}
        for rel in rule.relationships:
            if rel == "SAME_APPLICATION":
                constraints["application_id"] = anchor_item.application_id
            elif rel == "SAME_SOURCE_IP":
                val = getattr(anchor_item, "source_ip", None) if isinstance(anchor_item, SecurityEvent) else getattr(anchor_item.security_event, "source_ip", None) if anchor_item.security_event else None
                if val: constraints["source_ip"] = val
            elif rel == "SAME_USER" or rel == "SAME_USER_ID":
                val = getattr(anchor_item, "user_id", None) if isinstance(anchor_item, SecurityEvent) else getattr(anchor_item.security_event, "user_id", None) if anchor_item.security_event else None
                if val: constraints["user_id"] = val
            elif rel == "SAME_USERNAME":
                val = getattr(anchor_item, "username", None) if isinstance(anchor_item, SecurityEvent) else getattr(anchor_item.security_event, "username", None) if anchor_item.security_event else None
                if val: constraints["username"] = val
            elif rel == "SAME_SESSION":
                val = getattr(anchor_item, "session_id", None) if isinstance(anchor_item, SecurityEvent) else getattr(anchor_item.security_event, "session_id", None) if anchor_item.security_event else None
                if val: constraints["session_id"] = val

        # If a rule requires SAME_SOURCE_IP but the anchor doesn't have it, it cannot match
        if "SAME_SOURCE_IP" in rule.relationships and "source_ip" not in constraints:
            return EvaluatorResult(matched=False)
        if ("SAME_USER" in rule.relationships or "SAME_USER_ID" in rule.relationships) and "user_id" not in constraints:
            return EvaluatorResult(matched=False)
            
        sequence_to_find = rule.sequence[:-1]
        
        # Iterate backwards
        for seq_item in reversed(sequence_to_find):
            matched_item = SequenceEvaluator._find_preceding_item(
                db, seq_item, window_start, current_time_bound, constraints
            )
            
            if not matched_item:
                return EvaluatorResult(matched=False)
                
            evidence_chain.insert(0, matched_item)
            # Update the time bound so the next preceding item must occur before this matched item
            current_time_bound = matched_item.timestamp if isinstance(matched_item, SecurityEvent) else matched_item.detected_at
            
        return EvaluatorResult(matched=True, evidence_items=evidence_chain)
        
    @staticmethod
    def _find_preceding_item(db: Session, seq_item: dict, window_start: datetime, time_bound: datetime, constraints: dict) -> Any:
        item_type = seq_item.get("type")
        
        if item_type == "event":
            event_type = seq_item.get("event_type")
            conds = [
                SecurityEvent.event_type == event_type,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.timestamp <= time_bound
            ]
            if "application_id" in constraints:
                conds.append(SecurityEvent.application_id == constraints["application_id"])
            if "source_ip" in constraints:
                conds.append(SecurityEvent.source_ip == constraints["source_ip"])
            if "user_id" in constraints:
                conds.append(SecurityEvent.user_id == constraints["user_id"])
            if "username" in constraints:
                conds.append(SecurityEvent.username == constraints["username"])
            if "session_id" in constraints:
                conds.append(SecurityEvent.session_id == constraints["session_id"])
                
            stmt = select(SecurityEvent).where(and_(*conds)).order_by(desc(SecurityEvent.timestamp)).limit(1)
            return db.execute(stmt).scalars().first()
            
        elif item_type == "alert":
            alert_title = seq_item.get("alert_title")
            conds = [
                Alert.title == alert_title,
                Alert.detected_at >= window_start,
                Alert.detected_at <= time_bound
            ]
            if "application_id" in constraints:
                conds.append(Alert.application_id == constraints["application_id"])
                
            # For alerts, relationship fields (like source_ip) might need joins.
            # To keep it performant, if we require source_ip constraint on an Alert, we join SecurityEvent
            needs_join = False
            join_conds = []
            if "source_ip" in constraints:
                needs_join = True
                join_conds.append(SecurityEvent.source_ip == constraints["source_ip"])
            if "user_id" in constraints:
                needs_join = True
                join_conds.append(SecurityEvent.user_id == constraints["user_id"])
            if "username" in constraints:
                needs_join = True
                join_conds.append(SecurityEvent.username == constraints["username"])
            if "session_id" in constraints:
                needs_join = True
                join_conds.append(SecurityEvent.session_id == constraints["session_id"])
                
            if needs_join:
                stmt = select(Alert).join(SecurityEvent, Alert.security_event_id == SecurityEvent.id).where(and_(*conds, *join_conds)).order_by(desc(Alert.detected_at)).limit(1)
            else:
                stmt = select(Alert).where(and_(*conds)).order_by(desc(Alert.detected_at)).limit(1)
                
            return db.execute(stmt).scalars().first()
            
        return None
