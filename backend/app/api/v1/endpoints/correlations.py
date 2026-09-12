from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.correlation import Correlation, CorrelationStatus
from app.schemas.correlation import (
    CorrelationResponse,
    CorrelationListResponse,
    CorrelationStatusUpdate,
    CorrelationEvidence
)
from app.core.permissions import Permission

router = APIRouter()

@router.get("", response_model=CorrelationListResponse)
def list_correlations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.CORRELATIONS_READ)),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    risk_level: Optional[str] = None,
    min_risk_score: Optional[int] = None,
    max_risk_score: Optional[int] = None,
    application_id: Optional[UUID] = None,
):
    """
    List correlations with optional filtering.
    """
    query = db.query(Correlation)
    
    if status:
        query = query.filter(Correlation.status == status)
    if severity:
        query = query.filter(Correlation.severity == severity)
    if risk_level:
        query = query.filter(Correlation.risk_level == risk_level)
    if min_risk_score is not None:
        query = query.filter(Correlation.risk_score >= min_risk_score)
    if max_risk_score is not None:
        query = query.filter(Correlation.risk_score <= max_risk_score)
    if application_id:
        query = query.filter(Correlation.application_id == application_id)
        
    total = query.count()
    
    correlations = query.order_by(desc(Correlation.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for corr in correlations:
        resp = CorrelationResponse.model_validate(corr)
        items.append(resp)
        
    return CorrelationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{correlation_id}", response_model=CorrelationResponse)
def get_correlation(
    correlation_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.CORRELATIONS_READ)),
):
    """
    Get a specific correlation and its evidence timeline.
    """
    correlation = db.query(Correlation).filter(Correlation.id == correlation_id).first()
    if not correlation:
        raise HTTPException(status_code=404, detail="Correlation not found")
        
    # We must assemble the evidence from events and alerts.
    # The Association tables do not map automatically as objects unless configured.
    # But we can query the tables directly.
    from app.models.correlation import correlation_events, correlation_alerts
    from app.models.security_event import SecurityEvent
    from app.models.alert import Alert
    from app.schemas.security_event import EventResponse
    from app.schemas.alert import AlertResponse
    
    evidence_list = []
    
    # Get events
    events_query = db.query(correlation_events.c.sequence_position, SecurityEvent).join(
        SecurityEvent, correlation_events.c.security_event_id == SecurityEvent.id
    ).filter(correlation_events.c.correlation_id == correlation_id).all()
    
    for pos, ev in events_query:
        evidence_list.append(CorrelationEvidence(
            id=ev.id,
            type="EVENT",
            timestamp=ev.timestamp,
            data=EventResponse.model_validate(ev),
            sequence_position=pos
        ))
        
    # Get alerts
    alerts_query = db.query(correlation_alerts.c.sequence_position, Alert).join(
        Alert, correlation_alerts.c.alert_id == Alert.id
    ).filter(correlation_alerts.c.correlation_id == correlation_id).all()
    
    for pos, al in alerts_query:
        evidence_list.append(CorrelationEvidence(
            id=al.id,
            type="ALERT",
            timestamp=al.detected_at,
            data=AlertResponse.model_validate(al),
            sequence_position=pos
        ))
        
    evidence_list.sort(key=lambda x: x.sequence_position)
    
    resp = CorrelationResponse.model_validate(correlation)
    resp.evidence = evidence_list
    if correlation.alert:
        resp.generated_alert_id = correlation.alert.id
    
    return resp

@router.patch("/{correlation_id}/status", response_model=CorrelationResponse)
def update_correlation_status(
    status_update: CorrelationStatusUpdate,
    correlation_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.CORRELATIONS_MANAGE)),
):
    """
    Update the status of a correlation.
    """
    correlation = db.query(Correlation).filter(Correlation.id == correlation_id).first()
    if not correlation:
        raise HTTPException(status_code=404, detail="Correlation not found")
        
    correlation.status = status_update.status
    db.commit()
    db.refresh(correlation)
    
    return CorrelationResponse.model_validate(correlation)

@router.post("/{correlation_id}/create-incident", response_model=dict)
def create_incident_from_correlation(
    req: Request,
    correlation_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.INCIDENTS_MANAGE)),
):
    from app.services.incident_service import IncidentService
    correlation = db.query(Correlation).filter(Correlation.id == correlation_id).first()
    if not correlation:
        raise HTTPException(status_code=404, detail="Correlation not found")
        
    incident = IncidentService.create_from_correlation(db, correlation, current_user, req)
    return {"message": "Incident created", "incident_id": str(incident.id), "incident_number": incident.incident_number}
