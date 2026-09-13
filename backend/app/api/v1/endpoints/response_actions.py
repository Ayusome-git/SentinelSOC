from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from app.api import deps
from app.core.rate_limit import check_rate_limit
from app.models.user import User
from app.models.incident import Incident
from app.models.application import Application, AppStatus
from app.models.response import ResponseAction, ResponseActionStatus
from app.schemas.response import (
    ResponseActionResponse, ResponseActionListResponse, 
    ResponseActionCreate, ResponseRejectRequest
)
from app.response.validation import validate_action_and_target
from app.response.workflow import ResponseWorkflowService
from app.response.execution import ResponseExecutionService
from app.models.audit_log import AuditLog

router = APIRouter()

@router.get("", response_model=ResponseActionListResponse)
def list_response_actions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("RESPONSE_READ")),
    incident_id: Optional[UUID] = None,
    application_id: Optional[UUID] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    query = deps.filter_query_by_app_access(db.query(ResponseAction), ResponseAction, current_user)
    
    if incident_id:
        query = query.filter(ResponseAction.incident_id == incident_id)
    if application_id:
        query = query.filter(ResponseAction.application_id == application_id)
    if status:
        query = query.filter(ResponseAction.status == status)
        
    total = query.count()
    items = query.order_by(desc(ResponseAction.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("", response_model=ResponseActionResponse)
def create_response_action(
    *,
    db: Session = Depends(deps.get_db),
    request: ResponseActionCreate,
    current_user: User = Depends(deps.require_permission("RESPONSE_REQUEST"))
):
    if not validate_action_and_target(request.action_type, request.target_type, request.target_value):
        raise HTTPException(status_code=400, detail="Invalid action type, target type, or target value")
        
    app_entity = db.query(Application).filter(Application.id == request.application_id).first()
    if not app_entity or app_entity.status != AppStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Application is not active or doesn't exist")
        
    if request.incident_id:
        incident = db.query(Incident).filter(Incident.id == request.incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        if incident.application_id != request.application_id:
            raise HTTPException(status_code=400, detail="Incident does not belong to the specified application")

    action = ResponseAction(
        incident_id=request.incident_id,
        alert_id=request.alert_id,
        application_id=request.application_id,
        action_type=request.action_type,
        target_type=request.target_type,
        target_value=request.target_value,
        status=ResponseActionStatus.PENDING_APPROVAL,
        requested_by=current_user.id,
        requested_at=datetime.now(timezone.utc)
    )
    
    db.add(action)
    db.commit()
    db.refresh(action)
    
    audit = AuditLog(
        user_id=current_user.id,
        action="RESPONSE_ACTION_REQUESTED",
        resource_type="RESPONSE_ACTION",
        resource_id=str(action.id),
        details={"action_type": action.action_type, "target_type": action.target_type}
    )
    db.add(audit)
    
    return action

@router.post("/{id}/approve", response_model=ResponseActionResponse)
def approve_response_action(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: User = Depends(deps.require_permission("RESPONSE_APPROVE"))
):
    try:
        return ResponseWorkflowService.approve_action(db, id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/reject", response_model=ResponseActionResponse)
def reject_response_action(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    request: ResponseRejectRequest,
    current_user: User = Depends(deps.require_permission("RESPONSE_APPROVE"))
):
    try:
        return ResponseWorkflowService.reject_action(db, id, current_user.id, request.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/cancel", response_model=ResponseActionResponse)
def cancel_response_action(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: User = Depends(deps.require_permission("RESPONSE_REQUEST"))
):
    try:
        return ResponseWorkflowService.cancel_action(db, id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/execute", response_model=ResponseActionResponse, dependencies=[Depends(check_rate_limit)])
async def execute_response_action(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: User = Depends(deps.require_permission("RESPONSE_APPROVE"))
):
    try:
        return await ResponseExecutionService.execute_action(db, id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
