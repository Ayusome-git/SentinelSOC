import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc

from app.models.incident import Incident
from app.models.security_event import SecurityEvent
from app.models.alert import Alert, incident_alerts
from app.models.correlation import Correlation
from app.models.incident_comment import IncidentComment
from app.models.audit_log import AuditLog
from app.models.incident_evidence import IncidentEvidence, EvidenceType
from app.schemas.incident import TimelineEntry, TimelineEntryType, EntitiesResponse, EntityCount

class InvestigationService:

    @staticmethod
    def get_timeline(
        db: Session, 
        incident: Incident, 
        limit: int = 100, 
        offset: int = 0,
        entry_types: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[TimelineEntry]:
        """
        Builds a unified chronological timeline for the investigation workspace.
        Collects Security Events, Alerts, Correlations, Comments, and Audit Logs.
        """
        entries: List[TimelineEntry] = []
        
        # 1. Gather Security Events (via incident_events)
        if not entry_types or TimelineEntryType.SECURITY_EVENT.value in entry_types:
            for event in incident.events:
                # Optional search filter
                if search:
                    search_lower = search.lower()
                    if not (search_lower in (event.title or "").lower() or 
                            search_lower in (event.source_ip or "").lower() or 
                            search_lower in str(event.details or "").lower()):
                        continue
                        
                entries.append(TimelineEntry(
                    id=event.id,
                    entry_type=TimelineEntryType.SECURITY_EVENT,
                    occurred_at=event.timestamp,
                    title=event.title or event.event_type,
                    description=event.description,
                    severity=event.severity,
                    security_event_id=event.id,
                    source_ip=event.source_ip,
                    username=event.details.get("username") if event.details else None,
                    metadata_fields={"app_id": str(event.application_id)}
                ))
                
        # 2. Gather Alerts (via incident_alerts)
        if not entry_types or TimelineEntryType.ALERT.value in entry_types:
            for alert in incident.alerts:
                if search:
                    if search.lower() not in (alert.title or "").lower():
                        continue
                entries.append(TimelineEntry(
                    id=alert.id,
                    entry_type=TimelineEntryType.ALERT,
                    occurred_at=alert.detected_at,
                    title=alert.title,
                    description=alert.description,
                    severity=alert.severity,
                    risk_score=alert.risk_score,
                    alert_id=alert.id
                ))
                
        # 3. Gather Correlation
        if incident.correlation_id and (not entry_types or TimelineEntryType.CORRELATION.value in entry_types):
            correlation = incident.correlation
            if correlation:
                if not search or search.lower() in (correlation.title or "").lower():
                    entries.append(TimelineEntry(
                        id=correlation.id,
                        entry_type=TimelineEntryType.CORRELATION,
                        occurred_at=correlation.detected_at,
                        title=correlation.title,
                        description=correlation.description,
                        severity=correlation.severity,
                        risk_score=correlation.risk_score,
                        correlation_id=correlation.id
                    ))
                    
        # 4. Gather Comments
        if not entry_types or TimelineEntryType.COMMENT.value in entry_types:
            for comment in incident.comments:
                if search and search.lower() not in comment.comment.lower():
                    continue
                entries.append(TimelineEntry(
                    id=comment.id,
                    entry_type=TimelineEntryType.COMMENT,
                    occurred_at=comment.created_at,
                    title=f"Analyst Note by {comment.author.email if comment.author else 'Unknown'}",
                    description=comment.comment
                ))
                
        # 5. Gather Incident Activity from AuditLog
        if not entry_types or TimelineEntryType.INCIDENT_ACTIVITY.value in entry_types:
            # Resource ID is typically string of UUID
            logs = db.query(AuditLog).filter(
                AuditLog.resource_id == str(incident.id)
            ).all()
            for log in logs:
                if search and search.lower() not in log.action.lower():
                    continue
                # Skip evidence pinning noise unless explicitly wanted, or include them as activity
                entries.append(TimelineEntry(
                    id=log.id,
                    entry_type=TimelineEntryType.INCIDENT_ACTIVITY,
                    occurred_at=log.created_at,
                    title=log.action,
                    description=f"Action performed by {log.user.email if log.user else 'System'}",
                    metadata_fields=log.details
                ))
                
        # Sort chronologically
        entries.sort(key=lambda x: (x.occurred_at, x.entry_type))
        
        # Paginate
        return entries[offset:offset+limit]


    @staticmethod
    def get_entities(db: Session, incident: Incident) -> EntitiesResponse:
        """
        Aggregate entity counts (Source IPs, Users, Request Paths) from all events
        related to this incident.
        """
        # Collect all event IDs
        event_ids = [e.id for e in incident.events]
        
        if not event_ids:
            return EntitiesResponse()
            
        # Query events from DB to aggregate
        events = db.query(SecurityEvent).filter(SecurityEvent.id.in_(event_ids)).all()
        
        ip_counts: Dict[str, int] = {}
        user_counts: Dict[str, int] = {}
        path_counts: Dict[str, int] = {}
        session_counts: Dict[str, int] = {}
        
        for ev in events:
            # Source IP
            if ev.source_ip:
                ip_counts[ev.source_ip] = ip_counts.get(ev.source_ip, 0) + 1
            
            # Username and Session from details
            if ev.details:
                username = ev.details.get("username")
                if username:
                    user_counts[username] = user_counts.get(username, 0) + 1
                    
                session = ev.details.get("session_id")
                if session:
                    session_counts[session] = session_counts.get(session, 0) + 1
                    
                path = ev.details.get("request_path")
                if path:
                    path_counts[path] = path_counts.get(path, 0) + 1

        def to_entity_list(counts: Dict[str, int]) -> List[EntityCount]:
            return [EntityCount(value=k, event_count=v) for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)]

        return EntitiesResponse(
            source_ips=to_entity_list(ip_counts),
            users=to_entity_list(user_counts),
            request_paths=to_entity_list(path_counts),
            sessions=to_entity_list(session_counts)
        )

    @staticmethod
    def pin_evidence(
        db: Session, 
        incident_id: uuid.UUID, 
        evidence_type: str, 
        evidence_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> IncidentEvidence:
        existing = db.query(IncidentEvidence).filter(
            IncidentEvidence.incident_id == incident_id,
            IncidentEvidence.evidence_type == evidence_type,
            IncidentEvidence.evidence_id == evidence_id
        ).first()
        
        if existing:
            return existing
            
        evidence = IncidentEvidence(
            incident_id=incident_id,
            evidence_type=EvidenceType(evidence_type),
            evidence_id=evidence_id,
            added_by=user_id
        )
        db.add(evidence)
        return evidence

    @staticmethod
    def unpin_evidence(
        db: Session, 
        incident_id: uuid.UUID, 
        evidence_type: str, 
        evidence_id: uuid.UUID
    ):
        db.query(IncidentEvidence).filter(
            IncidentEvidence.incident_id == incident_id,
            IncidentEvidence.evidence_type == evidence_type,
        ).delete()

    @staticmethod
    def get_related_events(
        db: Session,
        incident: Incident,
        time_window_minutes: int = 30,
        limit: int = 100
    ) -> List[SecurityEvent]:
        # Collect entity values from incident's events
        ips = set()
        users = set()
        sessions = set()
        
        for ev in incident.events:
            if ev.source_ip:
                ips.add(ev.source_ip)
            if ev.details:
                if ev.details.get("username"):
                    users.add(ev.details.get("username"))
                if ev.details.get("session_id"):
                    sessions.add(ev.details.get("session_id"))
                    
        if not ips and not users and not sessions:
            return []
            
        # Build query within time window
        start_time = incident.detected_at - timedelta(minutes=time_window_minutes)
        end_time = incident.detected_at + timedelta(minutes=time_window_minutes)
        
        # Strict application isolation
        query = db.query(SecurityEvent).filter(
            SecurityEvent.application_id == incident.application_id,
            SecurityEvent.timestamp >= start_time,
            SecurityEvent.timestamp <= end_time,
            SecurityEvent.id.not_in([e.id for e in incident.events]) if incident.events else True
        )
        
        # Match any entity
        conditions = []
        if ips:
            conditions.append(SecurityEvent.source_ip.in_(ips))
        if users:
            for u in users:
                conditions.append(SecurityEvent.details['username'].astext == u)
        if sessions:
            for s in sessions:
                conditions.append(SecurityEvent.details['session_id'].astext == s)
                
        if conditions:
            query = query.filter(or_(*conditions))
            
        return query.order_by(SecurityEvent.timestamp.asc()).limit(limit).all()
