import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.response import ResponseAction, ResponseActionStatus, ApplicationResponseCapability
from app.models.application import Application, AppStatus
from app.response.client import ApplicationResponseClient
from app.response.validation import validate_action_and_target
from app.models.audit_log import AuditLog
from app.notifications.triggers import trigger_response_action_failed

class ResponseExecutionService:
    @staticmethod
    async def execute_action(db: Session, action_id: uuid.UUID, user_id: uuid.UUID) -> ResponseAction:
        """
        Executes a response action if it is in an APPROVED state and the application allows it.
        """
        action = db.query(ResponseAction).filter(ResponseAction.id == action_id).first()
        if not action:
            raise ValueError("Response action not found")
            
        if action.status != ResponseActionStatus.APPROVED:
            raise ValueError(f"Action cannot be executed from state {action.status}")
            
        application = db.query(Application).filter(Application.id == action.application_id).first()
        if not application or application.status != AppStatus.ACTIVE:
            action.status = ResponseActionStatus.FAILED
            action.failure_reason = "Application not found or inactive"
            action.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(action)
            return action
            
        capability = db.query(ApplicationResponseCapability).filter(
            ApplicationResponseCapability.application_id == application.id,
            ApplicationResponseCapability.action_type == action.action_type,
            ApplicationResponseCapability.enabled == True
        ).first()
        
        if not capability:
            action.status = ResponseActionStatus.FAILED
            action.failure_reason = "Application does not support or has disabled this capability"
            action.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(action)
            return action
            
        config = capability.configuration or {}
        webhook_url = config.get("webhook_url")
        secret = config.get("secret")
        
        if not webhook_url or not secret:
            action.status = ResponseActionStatus.FAILED
            action.failure_reason = "Application capability is missing webhook_url or secret configuration"
            action.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(action)
            return action
            
        # Transition to EXECUTING
        action.status = ResponseActionStatus.EXECUTING
        action.executed_at = datetime.now(timezone.utc)
        db.commit()
        
        # Log execution start
        audit = AuditLog(
            user_id=user_id,
            action="RESPONSE_ACTION_EXECUTION_STARTED",
            resource_type="RESPONSE_ACTION",
            resource_id=str(action.id),
            details={"action_type": action.action_type, "target_type": action.target_type}
        )
        db.add(audit)
        
        # Call client
        success, summary, metadata = await ApplicationResponseClient.execute_action(
            webhook_url=webhook_url,
            secret=secret,
            action=action.action_type,
            target_type=action.target_type,
            target_value=action.target_value,
            request_id=str(action.id)
        )
        
        action.completed_at = datetime.now(timezone.utc)
        action.result_summary = summary
        action.metadata_ = metadata
        
        if success:
            action.status = ResponseActionStatus.SUCCEEDED
            audit = AuditLog(
                user_id=user_id,
                action="RESPONSE_ACTION_SUCCEEDED",
                resource_type="RESPONSE_ACTION",
                resource_id=str(action.id),
                details={"summary": summary}
            )
            db.add(audit)
        else:
            action.status = ResponseActionStatus.FAILED
            action.failure_reason = summary
            audit = AuditLog(
                user_id=user_id,
                action="RESPONSE_ACTION_FAILED",
                resource_type="RESPONSE_ACTION",
                resource_id=str(action.id),
                details={"failure_reason": summary}
            )
            db.add(audit)
            
            trigger_response_action_failed(db, action, summary)
            
        db.commit()
        db.refresh(action)
        return action
