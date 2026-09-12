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
    IncidentAlertsLink, IncidentEventsLink, IncidentCommentCreate, IncidentCommentResponse
)
from app.services.incident_service import IncidentService
from app.services.incident_workflow_service import IncidentWorkflowService

router = APIRouter()

@router.get("/summary", response_model=IncidentSummaryResponse)
def get_incident_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.INCIDENTS_READ))
):
    query = db.query(Incident)
    
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
    query = db.query(Incident)
    
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
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident_in.title is not None:
        incident.title = incident_in.title
    if incident_in.description is not None:
        incident.description = incident_in.description
    if incident_in.severity is not None:
        incident.severity = incident_in.severity
        
    db.commit()
    db.refresh(incident)
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
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    comment = IncidentWorkflowService.add_comment(db, incident, comment_data.comment, current_user, request)
    db.commit()
    db.refresh(comment)
    return comment
