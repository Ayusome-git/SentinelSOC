from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.alert import Alert
from app.schemas.alert import AlertResponse, AlertListResponse
from app.core.permissions import Permission

router = APIRouter()

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
        
    total = query.count()
    
    alerts = query.order_by(desc(Alert.detected_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return AlertListResponse(
        items=alerts,
        total=total,
        page=page,
        page_size=page_size
    )

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
