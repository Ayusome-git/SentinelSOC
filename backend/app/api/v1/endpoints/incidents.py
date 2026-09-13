import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.user import User
from app.models.incident import Incident, IncidentStatus
from app.models.incident_comment import IncidentComment
from app.api.deps import get_current_user, require_permission
from app.core.permissions import Permission
from app.schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentStatusUpdate, IncidentAssigneeUpdate,
    IncidentResponse, IncidentListResponse, IncidentSummaryResponse,
    IncidentAlertsLink, IncidentEventsLink, IncidentCommentCreate, IncidentCommentResponse,
    TimelineResponse, EntitiesResponse, IncidentEvidenceCreate, IncidentEvidenceResponse
)
from app.services.incident_service import IncidentService
from app.services.incident_workflow_service import IncidentWorkflowService
from app.notifications.triggers import trigger_incident_escalated

router = APIRouter()

@router.get("/summary", response_model=IncidentSummaryResponse)
def get_incident_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ))
):
    query = deps.filter_query_by_app_access(db.query(Incident), Incident, current_user)
    
    total = query.count()
    status_counts = db.query(Incident.status, func.count(Incident.id)).group_by(Incident.status).all()
    status_dict = {s: c for s, c in status_counts}
    
    open_count = status_dict.get(IncidentStatus.OPEN.value, 0)
    investigating = status_dict.get(IncidentStatus.INVESTIGATING.value, 0)
    contained = status_dict.get(IncidentStatus.CONTAINED.value, 0)
    resolved = status_dict.get(IncidentStatus.RESOLVED.value, 0)
    closed = status_dict.get(IncidentStatus.CLOSED.value, 0)
    
    critical = query.filter(Incident.severity == "CRITICAL").count()
    high = query.filter(Incident.severity == "HIGH").count()
    unassigned = query.filter(Incident.assigned_to == None).count()
    
    avg_risk_row = db.query(func.avg(Incident.risk_score)).filter(Incident.risk_score != None).first()
    avg_risk = float(avg_risk_row[0]) if avg_risk_row and avg_risk_row[0] is not None else 0.0

    return {
        "total": total,
        "open": open_count,
        "investigating": investigating,
        "contained": contained,
        "resolved": resolved,
        "closed": closed,
        "critical": critical,
        "high": high,
        "unassigned": unassigned,
        "average_risk_score": round(avg_risk, 1)
    }

@router.get("", response_model=IncidentListResponse)
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ)),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    risk_level: Optional[str] = None, # Optional if we map it
    application_id: Optional[uuid.UUID] = None,
    assigned_to: Optional[uuid.UUID] = None,
    search: Optional[str] = None
):
    query = deps.filter_query_by_app_access(db.query(Incident), Incident, current_user)
    
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if application_id:
        query = query.filter(Incident.application_id == application_id)
    if assigned_to:
        query = query.filter(Incident.assigned_to == assigned_to)
    if search:
        query = query.filter(
            (Incident.title.ilike(f"%{search}%")) | 
            (Incident.description.ilike(f"%{search}%")) |
            (Incident.incident_number.ilike(f"%{search}%"))
        )
        
    total = query.count()
    incidents = query.order_by(Incident.risk_score.desc(), Incident.detected_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "items": incidents,
        "total": total,
        "page": page,
        "size": size
    }

@router.post("", response_model=IncidentResponse)
def create_incident(
    incident_in: IncidentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = IncidentService.create_incident_manual(
        db=db,
        title=incident_in.title,
        description=incident_in.description,
        severity=incident_in.severity,
        application_id=incident_in.application_id,
        actor=current_user,
        alert_ids=incident_in.alert_ids,
        event_ids=incident_in.event_ids,
        request=request
    )
    return incident

@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: uuid.UUID,
    incident_in: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    old_severity = incident.severity
        
    if incident_in.title is not None:
        incident.title = incident_in.title
    if incident_in.description is not None:
        incident.description = incident_in.description
    if incident_in.severity is not None:
        incident.severity = incident_in.severity
        
    db.commit()
    db.refresh(incident)
    
    # Trigger escalation if severity changed
    if incident_in.severity is not None and incident_in.severity != old_severity:
        # Check if it was actually an escalation (e.g. going up in severity). For simplicity, any change could be a trigger,
        # but let's just trigger it.
        trigger_incident_escalated(db, incident)
        
    return incident

@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: uuid.UUID,
    status_update: IncidentStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    IncidentWorkflowService.change_status(db, incident, status_update.status, current_user, request)
    db.commit()
    db.refresh(incident)
    return incident

@router.patch("/{incident_id}/assignee", response_model=IncidentResponse)
def assign_incident(
    incident_id: uuid.UUID,
    assign_update: IncidentAssigneeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    IncidentWorkflowService.assign(db, incident, assign_update.assigned_to, current_user, request)
    db.commit()
    db.refresh(incident)
    return incident

@router.post("/{incident_id}/alerts", response_model=IncidentResponse)
def add_alerts_to_incident(
    incident_id: uuid.UUID,
    link_data: IncidentAlertsLink,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    IncidentService.add_alerts(db, incident, link_data.alert_ids, current_user, request)
    return incident

@router.post("/{incident_id}/events", response_model=IncidentResponse)
def add_events_to_incident(
    incident_id: uuid.UUID,
    link_data: IncidentEventsLink,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    IncidentService.add_events(db, incident, link_data.event_ids, current_user, request)
    return incident

@router.get("/{incident_id}/comments", response_model=List[IncidentCommentResponse])
def get_incident_comments(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    return db.query(IncidentComment).filter(IncidentComment.incident_id == incident_id).order_by(IncidentComment.created_at.asc()).all()

@router.post("/{incident_id}/comments", response_model=IncidentCommentResponse)
def add_incident_comment(
    incident_id: uuid.UUID,
    comment_data: IncidentCommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    comment = IncidentWorkflowService.add_comment(db, incident, comment_data.comment, current_user, request)
    db.commit()
    db.refresh(comment)
    return comment

@router.get("/{incident_id}/timeline", response_model=TimelineResponse)
def get_incident_timeline(
    incident_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    types: Optional[str] = Query(None, description="Comma-separated list of types"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    entry_types = types.split(",") if types else None
    
    from app.services.investigation_service import InvestigationService
    items = InvestigationService.get_timeline(db, incident, limit, offset, entry_types, search)
    
    return {
        "items": items,
        "total": len(items) # Note: For pagination, real total might be more complex, returning loaded count
    }

@router.get("/{incident_id}/entities", response_model=EntitiesResponse)
def get_incident_entities(
    incident_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    from app.services.investigation_service import InvestigationService
    return InvestigationService.get_entities(db, incident)

from app.schemas.security_event import EventResponse
@router.get("/{incident_id}/related-events", response_model=List[EventResponse])
def get_incident_related_events(
    incident_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    time_window: int = Query(30, description="Minutes around incident"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    from app.services.investigation_service import InvestigationService
    events = InvestigationService.get_related_events(db, incident, time_window, limit)
    
    # Map to EventResponse manually because schemas are slightly different
    result = []
    for ev in events:
        result.append(EventResponse(
            id=ev.id,
            application_id=ev.application_id,
            application_name=ev.application.name if ev.application else "",
            event_type=ev.event_type,
            severity=ev.severity,
            timestamp=ev.timestamp,
            source_ip=ev.source_ip,
            user_id=ev.details.get("user_id") if ev.details else None,
            username=ev.details.get("username") if ev.details else None,
            session_id=ev.details.get("session_id") if ev.details else None,
            request_id=ev.details.get("request_id") if ev.details else None,
            http_method=ev.details.get("http_method") if ev.details else None,
            request_path=ev.details.get("request_path") if ev.details else None,
            user_agent=ev.details.get("user_agent") if ev.details else None,
            message=ev.title or ev.description
        ))
    return result

@router.post("/{incident_id}/evidence", response_model=IncidentEvidenceResponse)
def pin_evidence(
    incident_id: uuid.UUID,
    evidence_in: IncidentEvidenceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    from app.services.investigation_service import InvestigationService
    from app.services.incident_workflow_service import IncidentWorkflowService
    
    evidence = InvestigationService.pin_evidence(
        db, incident_id, evidence_in.evidence_type, evidence_in.evidence_id, current_user.id
    )
    
    IncidentWorkflowService._log_audit(
        db, current_user, "INCIDENT_EVIDENCE_PINNED", incident.id,
        {"evidence_type": evidence_in.evidence_type, "evidence_id": str(evidence_in.evidence_id)}, request
    )
    
    db.commit()
    db.refresh(evidence)
    return evidence

@router.delete("/{incident_id}/evidence/{evidence_type}/{evidence_id}", status_code=204)
def unpin_evidence(
    incident_id: uuid.UUID,
    evidence_type: str,
    evidence_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_MANAGE))
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        deps.check_app_access(current_user, incident.application_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    from app.services.investigation_service import InvestigationService
    from app.services.incident_workflow_service import IncidentWorkflowService
    
    InvestigationService.unpin_evidence(db, incident_id, evidence_type, evidence_id)
    
    IncidentWorkflowService._log_audit(
        db, current_user, "INCIDENT_EVIDENCE_UNPINNED", incident.id,
        {"evidence_type": evidence_type, "evidence_id": str(evidence_id)}, request
    )
    
    db.commit()
    return None
