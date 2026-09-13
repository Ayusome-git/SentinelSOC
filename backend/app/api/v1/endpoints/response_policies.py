from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.response import ResponsePolicy
from app.schemas.response import (
    ResponsePolicyResponse, ResponsePolicyCreate, ResponsePolicyUpdate, ResponsePolicyListResponse
)
from app.models.audit_log import AuditLog

router = APIRouter()

@router.get("", response_model=ResponsePolicyListResponse)
def list_policies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("RESPONSE_READ")),
    application_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    query = db.query(ResponsePolicy)
    if application_id:
        query = query.filter(ResponsePolicy.application_id == application_id)
        
    total = query.count()
    items = query.order_by(desc(ResponsePolicy.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.post("", response_model=ResponsePolicyResponse)
def create_policy(
    *,
    db: Session = Depends(deps.get_db),
    request: ResponsePolicyCreate,
    current_user: User = Depends(deps.require_permission("RESPONSE_MANAGE"))
):
    policy = ResponsePolicy(
        name=request.name,
        enabled=request.enabled,
        application_id=request.application_id,
        action_type=request.action_type,
        minimum_severity=request.minimum_severity,
        minimum_risk_score=request.minimum_risk_score,
        require_approval=request.require_approval,
        created_by=current_user.id
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    audit = AuditLog(
        user_id=current_user.id,
        action="RESPONSE_POLICY_CREATED",
        resource_type="RESPONSE_POLICY",
        resource_id=str(policy.id),
        details={"name": policy.name}
    )
    db.add(audit)
    
    return policy

@router.patch("/{id}", response_model=ResponsePolicyResponse)
def update_policy(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    request: ResponsePolicyUpdate,
    current_user: User = Depends(deps.require_permission("RESPONSE_MANAGE"))
):
    policy = db.query(ResponsePolicy).filter(ResponsePolicy.id == id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
        
    db.commit()
    db.refresh(policy)
    
    audit = AuditLog(
        user_id=current_user.id,
        action="RESPONSE_POLICY_UPDATED",
        resource_type="RESPONSE_POLICY",
        resource_id=str(policy.id),
        details={"updated_fields": list(update_data.keys())}
    )
    db.add(audit)
    
    return policy
