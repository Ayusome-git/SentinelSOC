from sqlalchemy.orm import Session
from app.models.response import ResponsePolicy, ResponseAction, ResponseActionStatus
from app.models.incident import Incident
from app.models.audit_log import AuditLog
from app.core.config import settings
import uuid
from datetime import datetime, timezone

class ResponsePolicyEngine:
    @staticmethod
    def evaluate_policies_for_incident(db: Session, incident: Incident) -> None:
        """
        Evaluates automation policies for an incident. If auto-response is disabled globally, does nothing.
        If a policy matches, creates a ResponseAction.
        """
        if not settings.AUTO_RESPONSE_ENABLED:
            return
            
        policies = db.query(ResponsePolicy).filter(
            ResponsePolicy.enabled == True,
            ResponsePolicy.application_id == incident.application_id
        ).all()
        
        for policy in policies:
            # Check conditions
            if policy.minimum_severity:
                # Assuming severity ordering: LOW < MEDIUM < HIGH < CRITICAL
                severities = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
                inc_sev = severities.get(incident.severity.upper(), 0)
                pol_sev = severities.get(policy.minimum_severity.upper(), 0)
                if inc_sev < pol_sev:
                    continue
                    
            if policy.minimum_risk_score is not None:
                inc_risk = incident.risk_score or 0
                if inc_risk < policy.minimum_risk_score:
                    continue
                    
            # A valid policy match is found. We would ideally need to extract the target dynamically
            # For automation, this requires complex context extraction (e.g. knowing the attacker IP).
            # We will generate a pending action if we can reliably extract the target type from the incident evidence.
            # To avoid arbitrary unvalidated targets, the simplest robust mechanism is to iterate over incident events
            # or alerts to find matching target types.
            
            # Since automatic target extraction is tricky, we will defer automated payload execution to a 
            # more sophisticated entity extractor, but for now we create a recommendation hook.
            
            # In a full implementation, we'd extract target_value from incident.alerts -> events
            pass
            
