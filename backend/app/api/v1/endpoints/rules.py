import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.api import deps
from app.models.user import User
from app.models.detection_rule import DetectionRule
from app.schemas.detection_rule import (
    DetectionRuleCreate,
    DetectionRuleUpdate,
    DetectionRuleStatusUpdate,
    DetectionRuleResponse,
    DetectionRuleListResponse
)
from app.core.permissions import Permission, has_permission
from app.services.audit_service import create_audit_log

router = APIRouter()

@router.get("/", response_model=DetectionRuleListResponse)
def list_rules(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str = None
) -> Any:
    if not has_permission(current_user.role, Permission.RULES_READ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    query = db.query(DetectionRule)
    if search:
        query = query.filter(
            or_(
                DetectionRule.name.ilike(f"%{search}%"),
                DetectionRule.event_type.ilike(f"%{search}%")
            )
        )
    
    total = query.count()
    query = query.order_by(desc(DetectionRule.created_at))
    rules = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return DetectionRuleListResponse(
        items=rules,
        total=total,
        page=page,
        size=page_size
    )

@router.get("/{rule_id}", response_model=DetectionRuleResponse)
def get_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if not has_permission(current_user.role, Permission.RULES_READ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        
    return rule

@router.post("/", response_model=DetectionRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_in: DetectionRuleCreate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if not has_permission(current_user.role, Permission.RULES_MANAGE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    rule = DetectionRule(
        name=rule_in.name,
        description=rule_in.description,
        rule_type=rule_in.rule_type,
        enabled=rule_in.enabled,
        severity=rule_in.severity,
        event_type=rule_in.event_type,
        threshold=rule_in.threshold,
        window_seconds=rule_in.window_seconds,
        group_by=rule_in.group_by,
        application_id=rule_in.application_id,
        created_by=current_user.id
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="RULE_CREATE",
        resource_type="RULE",
        resource_id=str(rule.id),
        details={"name": rule.name}
    )
    
    return rule

@router.patch("/{rule_id}", response_model=DetectionRuleResponse)
def update_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: uuid.UUID,
    rule_in: DetectionRuleUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if not has_permission(current_user.role, Permission.RULES_MANAGE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        
    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
        
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    create_audit_log(
        db=db,
        actor_id=current_user.id,
        action="RULE_UPDATE",
        resource_type="RULE",
        resource_id=str(rule.id),
        details={"updated_fields": list(update_data.keys())}
    )
    
    return rule

@router.patch("/{rule_id}/status", response_model=DetectionRuleResponse)
def update_rule_status(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: uuid.UUID,
    status_in: DetectionRuleStatusUpdate,
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    if not has_permission(current_user.role, Permission.RULES_MANAGE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    rule = db.query(DetectionRule).filter(DetectionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        
    rule.enabled = status_in.enabled
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    audit_action(
        db=db,
        actor_id=current_user.id,
        action="RULE_STATUS_UPDATE",
        resource_type="RULE",
        resource_id=str(rule.id),
        details={"enabled": rule.enabled}
    )
    
    return rule
