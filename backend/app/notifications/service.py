import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid

from app.models.notification import (
    Notification, NotificationPreference, NotificationType, 
    NotificationChannel, NotificationStatus
)
from app.models.user import User, UserRole
from app.core.config import settings
from app.notifications.email import get_email_provider, build_email_html
from app.models.audit_log import AuditLog
import threading
import asyncio

logger = logging.getLogger(__name__)

def _send_email_async(to_email: str, title: str, html_content: str, notification_id: uuid.UUID):
    async def _send():
        provider = get_email_provider()
        success = await provider.send_email(to_email, title, html_content)
        # We need a new session to update the notification status
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            notif = db.query(Notification).filter(Notification.id == notification_id).first()
            if notif:
                if success:
                    notif.status = NotificationStatus.SENT
                    notif.sent_at = datetime.now(timezone.utc)
                else:
                    notif.status = NotificationStatus.FAILED
                    notif.failure_reason = "Email provider failed"
            db.commit()
        except Exception as e:
            logger.error(f"Failed to update email notification status: {e}")
        finally:
            db.close()
            
    threading.Thread(target=lambda: asyncio.run(_send()), daemon=True).start()

class NotificationService:
    @staticmethod
    def dispatch_notification(
        db: Session,
        notification_type: NotificationType,
        user_ids: List[uuid.UUID],
        title: str,
        message: str,
        severity: Optional[str] = None,
        risk_score: Optional[int] = None,
        alert_id: Optional[uuid.UUID] = None,
        incident_id: Optional[uuid.UUID] = None,
        response_action_id: Optional[uuid.UUID] = None,
        application_id: Optional[uuid.UUID] = None,
        email_details: Optional[Dict[str, str]] = None,
        link_path: Optional[str] = None
    ):
        """
        Dispatches a notification to a list of users, respecting preferences, deduplication, and rate limiting.
        """
        for user_id in user_ids:
            # 1. Check Preferences
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                continue
                
            in_app_enabled = NotificationService._is_channel_enabled(db, user, notification_type, NotificationChannel.IN_APP)
            email_enabled = NotificationService._is_channel_enabled(db, user, notification_type, NotificationChannel.EMAIL)
            
            if not in_app_enabled and not email_enabled:
                continue
                
            # 2. Check Deduplication
            if NotificationService._is_duplicate(
                db, user_id, notification_type, 
                alert_id, incident_id, response_action_id, risk_score
            ):
                continue
                
            # 3. Create Notification Record (In App)
            if in_app_enabled:
                in_app_notif = Notification(
                    user_id=user_id,
                    application_id=application_id,
                    alert_id=alert_id,
                    incident_id=incident_id,
                    response_action_id=response_action_id,
                    notification_type=notification_type,
                    channel=NotificationChannel.IN_APP,
                    title=title,
                    message=message,
                    severity=severity,
                    risk_score=risk_score,
                    status=NotificationStatus.SENT,
                    sent_at=datetime.now(timezone.utc)
                )
                db.add(in_app_notif)
                
            # 4. Email Dispatch
            if email_enabled:
                # Check rate limit
                if NotificationService._is_rate_limited(db, user_id):
                    # Suppressed due to rate limiting
                    email_notif = Notification(
                        user_id=user_id,
                        application_id=application_id,
                        alert_id=alert_id,
                        incident_id=incident_id,
                        response_action_id=response_action_id,
                        notification_type=notification_type,
                        channel=NotificationChannel.EMAIL,
                        title=title,
                        message=message,
                        status=NotificationStatus.FAILED,
                        failure_reason="Rate limited",
                        sent_at=datetime.now(timezone.utc)
                    )
                    db.add(email_notif)
                    audit = AuditLog(
                        user_id=user_id,
                        action="NOTIFICATION_SUPPRESSED",
                        resource_type="NOTIFICATION",
                        resource_id=str(email_notif.id),
                        details={"reason": "Rate limited"}
                    )
                    db.add(audit)
                else:
                    email_notif = Notification(
                        user_id=user_id,
                        application_id=application_id,
                        alert_id=alert_id,
                        incident_id=incident_id,
                        response_action_id=response_action_id,
                        notification_type=notification_type,
                        channel=NotificationChannel.EMAIL,
                        title=title,
                        message=message,
                        severity=severity,
                        risk_score=risk_score,
                        status=NotificationStatus.PENDING
                    )
                    db.add(email_notif)
                    db.flush() # get ID
                    
                    # Send Email asynchronously in background thread
                    link = f"http://localhost:3000{link_path}" if link_path else None
                    html_content = build_email_html(title, message, email_details or {}, link)
                    
                    _send_email_async(user.email, title, html_content, email_notif.id)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Failed to commit notifications: {e}")
            db.rollback()

    @staticmethod
    def _is_channel_enabled(db: Session, user: User, notif_type: NotificationType, channel: NotificationChannel) -> bool:
        pref = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user.id,
            NotificationPreference.notification_type == notif_type,
            NotificationPreference.channel == channel
        ).first()
        
        if pref:
            return pref.enabled
            
        # Defaults if no explicit preference is set
        if user.role == UserRole.ADMIN:
            return True # Admins get everything by default
            
        if user.role == UserRole.ANALYST:
            # Analysts get important alerts
            return True
            
        if user.role == UserRole.VIEWER:
            if notif_type in (NotificationType.CRITICAL_ALERT, NotificationType.INCIDENT_CREATED):
                return True
            return False
            
        return False

    @staticmethod
    def _is_duplicate(
        db: Session, 
        user_id: uuid.UUID, 
        notif_type: NotificationType, 
        alert_id: Optional[uuid.UUID], 
        incident_id: Optional[uuid.UUID], 
        response_action_id: Optional[uuid.UUID],
        current_risk: Optional[int]
    ) -> bool:
        # Check if there is a notification of the exact same type for the same resource within window
        window_start = datetime.now(timezone.utc) - timedelta(seconds=settings.NOTIFICATION_DEDUP_WINDOW_SECONDS)
        
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.notification_type == notif_type,
            Notification.sent_at >= window_start
        )
        
        if alert_id:
            query = query.filter(Notification.alert_id == alert_id)
        elif incident_id:
            query = query.filter(Notification.incident_id == incident_id)
        elif response_action_id:
            query = query.filter(Notification.response_action_id == response_action_id)
            
        recent = query.order_by(desc(Notification.sent_at)).first()
        
        if not recent:
            return False
            
        # Meaningful escalation check for risk score
        if current_risk is not None and recent.risk_score is not None:
            if current_risk >= 75 and (current_risk - recent.risk_score >= 10):
                # Escalated enough to warrant a new notification
                return False
                
        return True

    @staticmethod
    def _is_rate_limited(db: Session, user_id: uuid.UUID) -> bool:
        window_start = datetime.now(timezone.utc) - timedelta(hours=1)
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.channel == NotificationChannel.EMAIL,
            Notification.sent_at >= window_start,
            Notification.status == NotificationStatus.SENT
        ).count()
        
        return count >= settings.NOTIFICATION_EMAIL_MAX_PER_HOUR
