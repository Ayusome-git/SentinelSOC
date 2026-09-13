import uuid
import logging
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.response import ResponseAction
from app.models.notification import NotificationType
from app.notifications.service import NotificationService

logger = logging.getLogger(__name__)

def _get_eligible_users(db: Session, permission_required: str = "NOTIFICATIONS_READ") -> list[uuid.UUID]:
    # In a real app we'd join with a roles/permissions table if it was in DB,
    # but here roles are mapped to permissions in code.
    # We just fetch active users who have ADMIN or ANALYST roles (which have NOTIFICATIONS_READ)
    # Actually VIEWER has NOTIFICATIONS_READ too in this system.
    users = db.query(User).filter(User.is_active == True).all()
    
    # We use a simple logic: Admin and Analyst get ALERTS, INCIDENTS, ML, TI
    # Viewers get basic things if configured. We can just send to ADMIN and ANALYST by default for these high severity alerts.
    return [u.id for u in users if u.role in (UserRole.ADMIN, UserRole.ANALYST)]

def trigger_alert_notification(db: Session, alert: Alert):
    try:
        # Check if it warrants a notification
        if alert.risk_score >= 75 or alert.severity == "CRITICAL":
            notif_type = NotificationType.CRITICAL_ALERT if alert.severity == "CRITICAL" else NotificationType.HIGH_RISK_ALERT
            
            title = f"{'Critical' if notif_type == NotificationType.CRITICAL_ALERT else 'High Risk'} security alert detected."
            msg = f"Alert: {alert.title}"
            
            email_details = {
                "Alert": alert.title,
                "Application": alert.application.name if alert.application else "Unknown",
                "Risk": f"{alert.risk_score}/100" if alert.risk_score else "N/A",
                "Severity": alert.severity,
                "Detected Time": alert.detected_at.strftime("%Y-%m-%d %H:%M:%S UTC") if alert.detected_at else "Unknown"
            }
            
            user_ids = _get_eligible_users(db)
            
            NotificationService.dispatch_notification(
                db=db,
                notification_type=notif_type,
                user_ids=user_ids,
                title=title,
                message=msg,
                severity=alert.severity,
                risk_score=alert.risk_score,
                alert_id=alert.id,
                application_id=alert.application_id,
                email_details=email_details,
                link_path=f"/alerts/{alert.id}"
            )
    except Exception as e:
        logger.error(f"Failed to trigger alert notification: {e}")

def trigger_incident_created(db: Session, incident: Incident):
    try:
        user_ids = _get_eligible_users(db)
        title = "New Security Incident Created"
        msg = f"Incident {incident.incident_number}: {incident.title}"
        email_details = {
            "Incident Number": incident.incident_number,
            "Title": incident.title,
            "Severity": incident.severity,
            "Risk Score": f"{incident.risk_score}/100" if incident.risk_score else "N/A"
        }
        
        NotificationService.dispatch_notification(
            db=db,
            notification_type=NotificationType.INCIDENT_CREATED,
            user_ids=user_ids,
            title=title,
            message=msg,
            severity=incident.severity,
            risk_score=incident.risk_score,
            incident_id=incident.id,
            email_details=email_details,
            link_path=f"/incidents/{incident.id}"
        )
    except Exception as e:
        logger.error(f"Failed to trigger incident created notification: {e}")

def trigger_incident_assigned(db: Session, incident: Incident, assignee_id: uuid.UUID):
    try:
        title = "Incident Assigned to You"
        msg = f"Incident {incident.incident_number} has been assigned to you."
        email_details = {
            "Incident Number": incident.incident_number,
            "Title": incident.title,
            "Severity": incident.severity
        }
        
        NotificationService.dispatch_notification(
            db=db,
            notification_type=NotificationType.INCIDENT_ASSIGNED,
            user_ids=[assignee_id],
            title=title,
            message=msg,
            severity=incident.severity,
            risk_score=incident.risk_score,
            incident_id=incident.id,
            email_details=email_details,
            link_path=f"/incidents/{incident.id}"
        )
    except Exception as e:
        logger.error(f"Failed to trigger incident assigned notification: {e}")

def trigger_incident_escalated(db: Session, incident: Incident):
    try:
        user_ids = _get_eligible_users(db)
        title = "Incident Escalated"
        msg = f"Incident {incident.incident_number} has been escalated to {incident.severity}."
        email_details = {
            "Incident Number": incident.incident_number,
            "Title": incident.title,
            "New Severity": incident.severity,
            "Risk Score": f"{incident.risk_score}/100" if incident.risk_score else "N/A"
        }
        
        NotificationService.dispatch_notification(
            db=db,
            notification_type=NotificationType.INCIDENT_ESCALATED,
            user_ids=user_ids,
            title=title,
            message=msg,
            severity=incident.severity,
            risk_score=incident.risk_score,
            incident_id=incident.id,
            email_details=email_details,
            link_path=f"/incidents/{incident.id}"
        )
    except Exception as e:
        logger.error(f"Failed to trigger incident escalated notification: {e}")

def trigger_response_action_failed(db: Session, action: ResponseAction, reason: str):
    try:
        user_ids = _get_eligible_users(db)
        title = "Security response action failed"
        msg = f"Action {action.action_type} failed on target {action.target_type}"
        
        # Safe logging, never include secrets
        email_details = {
            "Action": action.action_type,
            "Target Type": action.target_type,
            "Reason": reason
        }
        
        NotificationService.dispatch_notification(
            db=db,
            notification_type=NotificationType.RESPONSE_ACTION_FAILED,
            user_ids=user_ids,
            title=title,
            message=msg,
            response_action_id=action.id,
            application_id=action.application_id,
            email_details=email_details,
            link_path=f"/response-actions"
        )
    except Exception as e:
        logger.error(f"Failed to trigger response action failed notification: {e}")

def trigger_ml_anomaly(db: Session, alert: Alert):
    try:
        user_ids = _get_eligible_users(db)
        title = "Anomalous activity detected"
        msg = f"ML Anomaly Alert: {alert.title}"
        email_details = {
            "Alert": alert.title,
            "Application": alert.application.name if alert.application else "Unknown",
            "Risk": f"{alert.risk_score}/100" if alert.risk_score else "N/A",
            "Detection Source": "Isolation Forest"
        }
        
        NotificationService.dispatch_notification(
            db=db,
            notification_type=NotificationType.ML_ANOMALY_DETECTED,
            user_ids=user_ids,
            title=title,
            message=msg,
            severity=alert.severity,
            risk_score=alert.risk_score,
            alert_id=alert.id,
            application_id=alert.application_id,
            email_details=email_details,
            link_path=f"/alerts/{alert.id}"
        )
    except Exception as e:
        logger.error(f"Failed to trigger ML anomaly notification: {e}")

def trigger_ti_match(db: Session, alert: Alert, indicator: str, ioc_type: str, provider: str):
    try:
        user_ids = _get_eligible_users(db)
        title = "Threat Intelligence Match Detected"
        msg = f"Match found for {ioc_type} indicator in Alert: {alert.title}"
        email_details = {
            "Indicator": indicator,
            "Type": ioc_type,
            "Source": provider,
            "Associated Alert": alert.title
        }
        
        NotificationService.dispatch_notification(
            db=db,
            notification_type=NotificationType.THREAT_INTELLIGENCE_MATCH,
            user_ids=user_ids,
            title=title,
            message=msg,
            severity=alert.severity,
            risk_score=alert.risk_score,
            alert_id=alert.id,
            application_id=alert.application_id,
            email_details=email_details,
            link_path=f"/alerts/{alert.id}"
        )
    except Exception as e:
        logger.error(f"Failed to trigger TI match notification: {e}")
