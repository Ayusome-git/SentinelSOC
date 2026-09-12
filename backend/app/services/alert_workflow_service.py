from datetime import datetime, timezone
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, Request

from app.models.alert import Alert, AlertStatus
from app.models.alert_comment import AlertComment
from app.models.user import User, UserRole
from app.services.audit_service import create_audit_log
from app.core.permissions import has_permission, Permission

class AlertWorkflowService:
    
    @staticmethod
    def _enforce_transition(alert: Alert, new_status: AlertStatus):
        valid_transitions = {
            AlertStatus.OPEN.value: [AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE],
            AlertStatus.ACKNOWLEDGED.value: [AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE],
            AlertStatus.RESOLVED.value: [], # Terminal
            AlertStatus.FALSE_POSITIVE.value: [], # Terminal
        }
        
        current = alert.status if isinstance(alert.status, str) else alert.status.value

        allowed = valid_transitions.get(current, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=409, 
                detail=f"Invalid transition from {current} to {new_status.value}"
            )

    @staticmethod
    def acknowledge(db: Session, alert: Alert, actor: User, request: Optional[Request] = None):
        current_status = alert.status if isinstance(alert.status, str) else alert.status.value
        if current_status == AlertStatus.ACKNOWLEDGED.value:
            return alert
            
        AlertWorkflowService._enforce_transition(alert, AlertStatus.ACKNOWLEDGED)
        
        old_status = current_status
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_at = datetime.now(timezone.utc)
        
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action="ALERT_ACKNOWLEDGED",
            resource_type="Alert",
            resource_id=str(alert.id),
            request=request,
            details={
                "old_status": old_status,
                "new_status": AlertStatus.ACKNOWLEDGED.value
            }
        )
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def resolve(db: Session, alert: Alert, actor: User, request: Optional[Request] = None):
        current_status = alert.status if isinstance(alert.status, str) else alert.status.value
        if current_status == AlertStatus.RESOLVED.value:
            return alert
            
        AlertWorkflowService._enforce_transition(alert, AlertStatus.RESOLVED)
        
        old_status = current_status
        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_at = datetime.now(timezone.utc)
        
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action="ALERT_RESOLVED",
            resource_type="Alert",
            resource_id=str(alert.id),
            request=request,
            details={
                "old_status": old_status,
                "new_status": AlertStatus.RESOLVED.value
            }
        )
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def mark_false_positive(db: Session, alert: Alert, actor: User, request: Optional[Request] = None):
        current_status = alert.status if isinstance(alert.status, str) else alert.status.value
        if current_status == AlertStatus.FALSE_POSITIVE.value:
            return alert
            
        AlertWorkflowService._enforce_transition(alert, AlertStatus.FALSE_POSITIVE)
        
        old_status = current_status
        alert.status = AlertStatus.FALSE_POSITIVE.value
        alert.resolved_at = datetime.now(timezone.utc) # Also mark as resolved time
        
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action="ALERT_MARKED_FALSE_POSITIVE",
            resource_type="Alert",
            resource_id=str(alert.id),
            request=request,
            details={
                "old_status": old_status,
                "new_status": AlertStatus.FALSE_POSITIVE.value
            }
        )
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def assign(db: Session, alert: Alert, assignee_id: Optional[uuid.UUID], actor: User, request: Optional[Request] = None):
        old_assignee = str(alert.assigned_to) if alert.assigned_to else None
        
        if assignee_id:
            # Validate assignee
            assignee = db.query(User).filter(User.id == assignee_id).first()
            if not assignee:
                raise HTTPException(status_code=404, detail="Assignee not found")
            if not assignee.is_active:
                raise HTTPException(status_code=400, detail="Cannot assign to inactive user")
            if not has_permission(assignee.role, Permission.ALERTS_MANAGE):
                # Optionally enforce this, though analysts could just be VIEWERS if that was allowed? 
                # Requirements: "valid SOC user" - typically they need ALERTS_READ at minimum. Let's ensure ALERTS_READ.
                if not has_permission(assignee.role, Permission.ALERTS_READ):
                    raise HTTPException(status_code=400, detail="Assignee does not have permission to read alerts")

            alert.assigned_to = assignee_id
            action = "ALERT_ASSIGNED"
        else:
            alert.assigned_to = None
            action = "ALERT_UNASSIGNED"
            
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action=action,
            resource_type="Alert",
            resource_id=str(alert.id),
            request=request,
            details={
                "old_assignee": old_assignee,
                "new_assignee": str(assignee_id) if assignee_id else None
            }
        )
        return alert

    @staticmethod
    def add_comment(db: Session, alert: Alert, comment_text: str, actor: User, request: Optional[Request] = None) -> AlertComment:
        comment = AlertComment(
            alert_id=alert.id,
            user_id=actor.id,
            comment=comment_text
        )
        db.add(comment)
        
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action="ALERT_COMMENT_ADDED",
            resource_type="Alert",
            resource_id=str(alert.id),
            request=request
        )
        
        return comment
