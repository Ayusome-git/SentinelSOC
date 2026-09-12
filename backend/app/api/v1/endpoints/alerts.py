from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.models.alert import Alert, AlertStatus
from app.models.alert_comment import AlertComment
from app.schemas.alert import (
    AlertResponse, AlertListResponse, AlertCommentCreate, 
    AlertCommentResponse, AlertSummary, BulkActionRequest,
    AlertAssigneeUpdate
)
from app.core.permissions import Permission, has_permission
from app.services.alert_workflow_service import AlertWorkflowService

router = APIRouter()

@router.get("/summary", response_model=AlertSummary)
def get_alert_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_READ)),
):
    query = db.query(Alert)
    total = query.count()
    
    status_counts = db.query(Alert.status, func.count(Alert.id)).group_by(Alert.status).all()
    status_dict = {status: count for status, count in status_counts}
    
    risk_counts = db.query(Alert.risk_level, func.count(Alert.id)).filter(Alert.risk_level.is_not(None)).group_by(Alert.risk_level).all()
    risk_dict = {level: count for level, count in risk_counts}
    
    unassigned_count = db.query(Alert).filter(Alert.assigned_to.is_(None)).count()
    
    avg_score = db.query(func.avg(Alert.risk_score)).filter(Alert.risk_score.is_not(None)).scalar()
    
    return AlertSummary(
        total=total,
        open=status_dict.get(AlertStatus.OPEN.value, 0),
        acknowledged=status_dict.get(AlertStatus.ACKNOWLEDGED.value, 0),
        resolved=status_dict.get(AlertStatus.RESOLVED.value, 0),
        false_positive=status_dict.get(AlertStatus.FALSE_POSITIVE.value, 0),
        critical=risk_dict.get("CRITICAL", 0),
        high=risk_dict.get("HIGH", 0),
        unassigned=unassigned_count,
        average_risk_score=float(avg_score or 0.0)
    )

@router.get("", response_model=AlertListResponse)
def list_alerts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_READ)),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    risk_level: Optional[str] = None,
    min_risk_score: Optional[int] = None,
    max_risk_score: Optional[int] = None,
    application_id: Optional[UUID] = None,
    rule_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    unassigned: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = Query("detected_at", regex="^(detected_at|risk_score|severity)$"),
    sort_dir: str = Query("desc", regex="^(asc|desc)$")
):
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if risk_level:
        query = query.filter(Alert.risk_level == risk_level)
    if min_risk_score is not None:
        query = query.filter(Alert.risk_score >= min_risk_score)
    if max_risk_score is not None:
        query = query.filter(Alert.risk_score <= max_risk_score)
    if application_id:
        query = query.filter(Alert.application_id == application_id)
    if rule_id:
        query = query.filter(Alert.rule_id == rule_id)
    if assigned_to:
        query = query.filter(Alert.assigned_to == assigned_to)
    if unassigned is True:
        query = query.filter(Alert.assigned_to.is_(None))
    if start_time:
        query = query.filter(Alert.detected_at >= start_time)
    if end_time:
        query = query.filter(Alert.detected_at <= end_time)
    if search:
        query = query.filter(
            or_(
                Alert.title.ilike(f"%{search}%"),
                Alert.description.ilike(f"%{search}%")
            )
        )
        
    total = query.count()
    
    # Sorting
    sort_col = getattr(Alert, sort_by)
    if sort_dir == "desc":
        sort_col = desc(sort_col)
    else:
        sort_col = asc(sort_col)
        
    # Always add tiebreaker
    if sort_by != "detected_at":
        query = query.order_by(sort_col, desc(Alert.detected_at))
    else:
        query = query.order_by(sort_col)
    
    alerts = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return AlertListResponse(
        items=alerts,
        total=total,
        page=page,
        page_size=page_size
    )

@router.post("/bulk-action")
def bulk_action_alerts(
    request: BulkActionRequest,
    req: Request,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_MANAGE)),
):
    if len(request.alert_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 alerts can be processed at once")
        
    alerts = db.query(Alert).filter(Alert.id.in_(request.alert_ids)).all()
    
    processed = 0
    for alert in alerts:
        try:
            if request.action == "ACKNOWLEDGE":
                AlertWorkflowService.acknowledge(db, alert, current_user, req)
            elif request.action == "RESOLVE":
                AlertWorkflowService.resolve(db, alert, current_user, req)
            elif request.action == "FALSE_POSITIVE":
                AlertWorkflowService.mark_false_positive(db, alert, current_user, req)
            elif request.action == "ASSIGN":
                AlertWorkflowService.assign(db, alert, request.assigned_to, current_user, req)
            processed += 1
        except HTTPException:
            # Skip invalid transitions in bulk operations silently or accumulate errors. We'll skip silently for now.
            pass
            
    db.commit()
    return {"message": f"Successfully processed {processed} alerts"}

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_READ)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return alert

@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    req: Request,
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_MANAGE)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert = AlertWorkflowService.acknowledge(db, alert, current_user, req)
    db.commit()
    return alert

@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    req: Request,
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_MANAGE)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert = AlertWorkflowService.resolve(db, alert, current_user, req)
    db.commit()
    return alert

@router.post("/{alert_id}/false-positive", response_model=AlertResponse)
def false_positive_alert(
    req: Request,
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_MANAGE)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert = AlertWorkflowService.mark_false_positive(db, alert, current_user, req)
    db.commit()
    return alert

@router.patch("/{alert_id}/assignee", response_model=AlertResponse)
def assign_alert(
    update_data: AlertAssigneeUpdate,
    req: Request,
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_MANAGE)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert = AlertWorkflowService.assign(db, alert, update_data.assigned_to, current_user, req)
    db.commit()
    return alert

@router.get("/{alert_id}/comments", response_model=List[AlertCommentResponse])
def get_alert_comments(
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_READ)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return alert.comments

@router.post("/{alert_id}/comments", response_model=AlertCommentResponse)
def add_alert_comment(
    req: Request,
    comment_data: AlertCommentCreate,
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_MANAGE)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    comment = AlertWorkflowService.add_comment(db, alert, comment_data.comment, current_user, req)
    db.commit()
    db.refresh(comment)
    return comment

@router.get("/{alert_id}/risk")
def get_alert_risk(
    alert_id: UUID = Path(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission(Permission.ALERTS_READ)),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return {
        "score": alert.risk_score,
        "risk_level": alert.risk_level,
        "factors": alert.risk_factors,
        "calculated_at": alert.updated_at
    }
