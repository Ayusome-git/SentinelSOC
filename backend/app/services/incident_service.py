from typing import List, Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, Request

from app.models.incident import Incident, IncidentStatus
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.models.correlation import Correlation
from app.models.user import User
from app.services.audit_service import create_audit_log
from app.services.incident_sequence_service import IncidentSequenceService
from app.notifications.triggers import trigger_incident_created

class IncidentService:
    @staticmethod
    def _recalculate_risk(incident: Incident):
        """
        Incident risk = highest relevant correlation risk OR highest linked alert risk.
        Risk level mapping:
        0–24    LOW
        25–49   MODERATE
        50–74   HIGH
        75–100  CRITICAL
        """
        risks = []
        if incident.correlation and incident.correlation.risk_score is not None:
            risks.append(incident.correlation.risk_score)
        
        for alert in incident.alerts:
            if alert.risk_score is not None:
                risks.append(alert.risk_score)
                
        if risks:
            max_risk = max(risks)
            # Clip between 0 and 100
            incident.risk_score = max(0, min(100, max_risk))
        else:
            incident.risk_score = None

    @staticmethod
    def create_incident_manual(
        db: Session, 
        title: str, 
        description: str, 
        severity: str, 
        application_id: uuid.UUID,
        actor: User,
        alert_ids: List[uuid.UUID] = None,
        event_ids: List[uuid.UUID] = None,
        request: Optional[Request] = None
    ) -> Incident:
        
        incident_number = IncidentSequenceService.generate_incident_number(db)
        
        incident = Incident(
            incident_number=incident_number,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN.value,
            application_id=application_id,
            detected_at=datetime.now(timezone.utc)
        )
        
        db.add(incident)
        
        if alert_ids:
            alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
            for alert in alerts:
                if alert.application_id != application_id:
                    raise HTTPException(status_code=400, detail="Cannot link alerts from a different application")
                incident.alerts.append(alert)
                
        if event_ids:
            events = db.query(SecurityEvent).filter(SecurityEvent.id.in_(event_ids)).all()
            for event in events:
                if event.application_id != application_id:
                    raise HTTPException(status_code=400, detail="Cannot link events from a different application")
                incident.events.append(event)
                
        IncidentService._recalculate_risk(incident)
        
        db.commit()
        db.refresh(incident)
        
        create_audit_log(
            db=db,
            actor_id=actor.id if actor else None,
            action="INCIDENT_CREATED",
            resource_type="Incident",
            resource_id=str(incident.id),
            request=request,
            details={"incident_number": incident.incident_number, "manual": True}
        )
        
        trigger_incident_created(db, incident)
        
        return incident

    @staticmethod
    def create_from_alert(db: Session, alert: Alert, actor: User, request: Optional[Request] = None, title: str = None, description: str = None) -> Incident:
        incident_number = IncidentSequenceService.generate_incident_number(db)
        
        incident = Incident(
            incident_number=incident_number,
            title=title or f"Escalated Alert: {alert.title}",
            description=description or alert.description or f"Created from alert {alert.id}",
            severity=alert.severity,
            status=IncidentStatus.OPEN.value,
            application_id=alert.application_id,
            detected_at=datetime.now(timezone.utc)
        )
        
        db.add(incident)
        incident.alerts.append(alert)
        
        IncidentService._recalculate_risk(incident)
        
        db.commit()
        db.refresh(incident)
        
        create_audit_log(
            db=db,
            actor_id=actor.id if actor else None,
            action="INCIDENT_CREATED_FROM_ALERT",
            resource_type="Incident",
            resource_id=str(incident.id),
            request=request,
            details={"incident_number": incident.incident_number, "alert_id": str(alert.id)}
        )
        
        trigger_incident_created(db, incident)
        
        return incident

    @staticmethod
    def create_from_correlation(db: Session, correlation: Correlation, actor: Optional[User], request: Optional[Request] = None, auto: bool = False) -> Incident:
        # Prevent duplicates
        existing = db.query(Incident).filter(Incident.correlation_id == correlation.id).first()
        if existing:
            return existing

        incident_number = IncidentSequenceService.generate_incident_number(db)
        
        incident = Incident(
            incident_number=incident_number,
            title=f"Potential Attack Sequence: {correlation.name}",
            description=correlation.description or "Automatically created from correlation.",
            severity=correlation.severity,
            status=IncidentStatus.OPEN.value,
            application_id=correlation.application_id,
            correlation_id=correlation.id,
            detected_at=datetime.now(timezone.utc)
        )
        
        db.add(incident)
        
        # Link all alerts and events from correlation
        for alert in correlation.alerts_evidence:
            if alert not in incident.alerts:
                incident.alerts.append(alert)
                
        for event in correlation.events:
            if event not in incident.events:
                incident.events.append(event)
                
        IncidentService._recalculate_risk(incident)
        
        db.commit()
        db.refresh(incident)
        
        action = "INCIDENT_CREATED_AUTOMATICALLY" if auto else "INCIDENT_CREATED_FROM_CORRELATION"
        
        create_audit_log(
            db=db,
            actor_id=actor.id if actor else None,
            action=action,
            resource_type="Incident",
            resource_id=str(incident.id),
            request=request,
            details={"incident_number": incident.incident_number, "correlation_id": str(correlation.id)}
        )
        
        trigger_incident_created(db, incident)
        
        return incident

    @staticmethod
    def add_alerts(db: Session, incident: Incident, alert_ids: List[uuid.UUID], actor: User, request: Optional[Request] = None):
        if not alert_ids:
            return incident
            
        alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
        added = 0
        for alert in alerts:
            if alert.application_id != incident.application_id:
                raise HTTPException(status_code=400, detail="Cannot link alerts from a different application")
            if alert not in incident.alerts:
                incident.alerts.append(alert)
                added += 1
                
        if added > 0:
            IncidentService._recalculate_risk(incident)
            db.commit()
            db.refresh(incident)
            
            create_audit_log(
                db=db,
                actor_id=actor.id,
                action="INCIDENT_ALERT_ADDED",
                resource_type="Incident",
                resource_id=str(incident.id),
                request=request,
                details={"added_count": added, "alert_ids": [str(a_id) for a_id in alert_ids]}
            )
        return incident

    @staticmethod
    def add_events(db: Session, incident: Incident, event_ids: List[uuid.UUID], actor: User, request: Optional[Request] = None):
        if not event_ids:
            return incident
            
        events = db.query(SecurityEvent).filter(SecurityEvent.id.in_(event_ids)).all()
        added = 0
        for event in events:
            if event.application_id != incident.application_id:
                raise HTTPException(status_code=400, detail="Cannot link events from a different application")
            if event not in incident.events:
                incident.events.append(event)
                added += 1
                
        if added > 0:
            db.commit()
            db.refresh(incident)
            
            create_audit_log(
                db=db,
                actor_id=actor.id,
                action="INCIDENT_EVENT_ADDED",
                resource_type="Incident",
                resource_id=str(incident.id),
                request=request,
                details={"added_count": added, "event_ids": [str(e_id) for e_id in event_ids]}
            )
        return incident
