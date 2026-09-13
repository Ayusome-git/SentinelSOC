from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, Request

from app.models.incident import Incident, IncidentStatus
from app.models.incident_comment import IncidentComment
from app.models.user import User
from app.services.audit_service import create_audit_log
from app.core.permissions import has_permission, Permission
from app.notifications.triggers import trigger_incident_assigned, trigger_incident_escalated

class IncidentWorkflowService:
    @staticmethod
    def _enforce_transition(incident: Incident, new_status: IncidentStatus):
        valid_transitions = {
            IncidentStatus.OPEN.value: [
                IncidentStatus.INVESTIGATING, 
                IncidentStatus.CONTAINED, 
                IncidentStatus.RESOLVED
            ],
            IncidentStatus.INVESTIGATING.value: [
                IncidentStatus.CONTAINED, 
                IncidentStatus.RESOLVED
            ],
            IncidentStatus.CONTAINED.value: [
                IncidentStatus.RESOLVED
            ],
            IncidentStatus.RESOLVED.value: [
                IncidentStatus.CLOSED
            ],
            IncidentStatus.CLOSED.value: [] # Terminal
        }
        
        current = incident.status if isinstance(incident.status, str) else incident.status.value

        allowed = valid_transitions.get(current, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=409, 
                detail=f"Invalid transition from {current} to {new_status.value}"
            )

    @staticmethod
    def change_status(db: Session, incident: Incident, new_status: IncidentStatus, actor: User, request: Optional[Request] = None):
        current_status = incident.status if isinstance(incident.status, str) else incident.status.value
        if current_status == new_status.value:
            return incident
            
        IncidentWorkflowService._enforce_transition(incident, new_status)
        
        old_status = current_status
        incident.status = new_status.value
        
        # Update timestamps
        now = datetime.now(timezone.utc)
        if new_status == IncidentStatus.CONTAINED:
            if not incident.contained_at:
                incident.contained_at = now
        elif new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = now
        elif new_status == IncidentStatus.CLOSED:
            incident.closed_at = now
        
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action="INCIDENT_STATUS_CHANGED",
            resource_type="Incident",
            resource_id=str(incident.id),
            request=request,
            details={
                "old_status": old_status,
                "new_status": new_status.value
            }
        )
        
        # We also want to trigger INCIDENT_ESCALATED if it's escalated in severity (not status)
        # But this function only changes status. If we change severity, it's done elsewhere.
        
        return incident

    @staticmethod
    def assign(db: Session, incident: Incident, assignee_id: Optional[uuid.UUID], actor: User, request: Optional[Request] = None):
        old_assignee = str(incident.assigned_to) if incident.assigned_to else None
        
        if assignee_id:
            # Validate assignee
            assignee = db.query(User).filter(User.id == assignee_id).first()
            if not assignee:
                raise HTTPException(status_code=404, detail="Assignee not found")
            if not assignee.is_active:
                raise HTTPException(status_code=400, detail="Cannot assign to inactive user")
            if not has_permission(assignee.role, Permission.INCIDENTS_READ):
                raise HTTPException(status_code=400, detail="Assignee does not have permission to read incidents")

            incident.assigned_to = assignee_id
            action = "INCIDENT_ASSIGNED"
        else:
            incident.assigned_to = None
            action = "INCIDENT_UNASSIGNED"
            
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action=action,
            resource_type="Incident",
            resource_id=str(incident.id),
            request=request,
            details={
                "old_assignee": old_assignee,
                "new_assignee": str(assignee_id) if assignee_id else None
            }
        )
        
        if assignee_id:
            trigger_incident_assigned(db, incident, assignee_id)
            
        return incident

    @staticmethod
    def add_comment(db: Session, incident: Incident, comment_text: str, actor: User, request: Optional[Request] = None) -> IncidentComment:
        if not comment_text or not comment_text.strip():
            raise HTTPException(status_code=400, detail="Comment cannot be empty")
        
        if len(comment_text) > 5000:
            raise HTTPException(status_code=400, detail="Comment exceeds maximum length of 5000 characters")

        comment = IncidentComment(
            incident_id=incident.id,
            user_id=actor.id,
            comment=comment_text.strip()
        )
        db.add(comment)
        
        create_audit_log(
            db=db,
            actor_id=actor.id,
            action="INCIDENT_COMMENT_ADDED",
            resource_type="Incident",
            resource_id=str(incident.id),
            request=request
        )
        
        return comment
