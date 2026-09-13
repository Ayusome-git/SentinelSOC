from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.response import ApplicationResponseCapability
from app.schemas.response import (
    ApplicationResponseCapabilityResponse, ApplicationResponseCapabilityCreate, ApplicationResponseCapabilityUpdate
)
from app.models.audit_log import AuditLog

router = APIRouter()

@router.get("", response_model=List[ApplicationResponseCapabilityResponse])
def list_capabilities(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("RESPONSE_READ")),
    application_id: Optional[UUID] = None
):
    query = db.query(ApplicationResponseCapability)
    if application_id:
        query = query.filter(ApplicationResponseCapability.application_id == application_id)
        
    return query.all()

@router.post("", response_model=ApplicationResponseCapabilityResponse)
def create_capability(
    *,
    db: Session = Depends(deps.get_db),
    request: ApplicationResponseCapabilityCreate,
    current_user: User = Depends(deps.require_permission("RESPONSE_MANAGE"))
):
    # Check if exists
    existing = db.query(ApplicationResponseCapability).filter(
        ApplicationResponseCapability.application_id == request.application_id,
        ApplicationResponseCapability.action_type == request.action_type
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Capability already exists for this application and action type")
        
    capability = ApplicationResponseCapability(
        application_id=request.application_id,
        action_type=request.action_type,
        enabled=request.enabled,
        configuration=request.configuration
    )
    
    db.add(capability)
    db.commit()
    db.refresh(capability)
    
    audit = AuditLog(
        user_id=current_user.id,
        action="RESPONSE_CAPABILITY_CREATED",
        resource_type="RESPONSE_CAPABILITY",
        resource_id=str(capability.id),
        details={"action_type": capability.action_type}
    )
    db.add(audit)
    
    return capability

@router.patch("/{id}", response_model=ApplicationResponseCapabilityResponse)
def update_capability(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    request: ApplicationResponseCapabilityUpdate,
    current_user: User = Depends(deps.require_permission("RESPONSE_MANAGE"))
):
    capability = db.query(ApplicationResponseCapability).filter(ApplicationResponseCapability.id == id).first()
    if not capability:
        raise HTTPException(status_code=404, detail="Capability not found")
        
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(capability, field, value)
        
    db.commit()
    db.refresh(capability)
    
    audit = AuditLog(
        user_id=current_user.id,
        action="RESPONSE_CAPABILITY_UPDATED",
        resource_type="RESPONSE_CAPABILITY",
        resource_id=str(capability.id),
        details={"updated_fields": list(update_data.keys())}
    )
    db.add(audit)
    
    return capability
