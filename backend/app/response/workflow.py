import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.response import ResponseAction, ResponseActionStatus
from app.models.audit_log import AuditLog
from app.core.config import settings

class ResponseWorkflowService:
    @staticmethod
    def approve_action(db: Session, action_id: uuid.UUID, user_id: uuid.UUID) -> ResponseAction:
        action = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
        if not action:
            raise ValueError("Response action not found")
            
        if action.status != ResponseActionStatus.PENDING_APPROVAL:
            raise ValueError(f"Action cannot be approved from state {action.status}")
            
        action.status = ResponseActionStatus.APPROVED
        action.approved_by = user_id
        action.approved_at = datetime.now(timezone.utc)
        
        audit = AuditLog(
            user_id=user_id,
            action="RESPONSE_ACTION_APPROVED",
            resource_type="RESPONSE_ACTION",
            resource_id=str(action.id),
            details={"action_type": action.action_type}
        )
        db.add(audit)
        
        db.commit()
        db.refresh(action)
        return action
        
    @staticmethod
    def reject_action(db: Session, action_id: uuid.UUID, user_id: uuid.UUID, reason: str) -> ResponseAction:
        action = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
        if not action:
            raise ValueError("Response action not found")
            
        if action.status != ResponseActionStatus.PENDING_APPROVAL:
            raise ValueError(f"Action cannot be rejected from state {action.status}")
            
        action.status = ResponseActionStatus.REJECTED
        action.completed_at = datetime.now(timezone.utc)
        action.result_summary = f"Rejected: {reason}"
        
        audit = AuditLog(
            user_id=user_id,
            action="RESPONSE_ACTION_REJECTED",
            resource_type="RESPONSE_ACTION",
            resource_id=str(action.id),
            details={"action_type": action.action_type, "reason": reason}
        )
        db.add(audit)
        
        db.commit()
        db.refresh(action)
        return action
        
    @staticmethod
    def cancel_action(db: Session, action_id: uuid.UUID, user_id: uuid.UUID) -> ResponseAction:
        action = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
        if not action:
            raise ValueError("Response action not found")
            
        if action.status not in (ResponseActionStatus.PENDING_APPROVAL, ResponseActionStatus.APPROVED):
            raise ValueError(f"Action cannot be cancelled from state {action.status}")
            
        action.status = ResponseActionStatus.CANCELLED
        action.completed_at = datetime.now(timezone.utc)
        action.result_summary = "Cancelled by user"
        
        audit = AuditLog(
            user_id=user_id,
            action="RESPONSE_ACTION_CANCELLED",
            resource_type="RESPONSE_ACTION",
            resource_id=str(action.id),
            details={"action_type": action.action_type}
        )
        db.add(audit)
        
        db.commit()
        db.refresh(action)
        return action
