import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models.user import User
from app.models.notification import Notification, NotificationPreference, NotificationStatus
from app.schemas.notification import (
    NotificationResponse, NotificationListResponse, 
    NotificationPreferenceResponse, NotificationPreferenceUpdate
)

router = APIRouter()

@router.get("", response_model=NotificationListResponse)
def get_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("NOTIFICATIONS_READ")),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    is_read: Optional[bool] = None
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if is_read is not None:
        if is_read:
            query = query.filter(Notification.status == NotificationStatus.READ)
        else:
            query = query.filter(Notification.status != NotificationStatus.READ)
        
    total = query.count()
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status != NotificationStatus.READ
    ).count()
    
    items = query.order_by(desc(Notification.created_at)).offset((page - 1) * size).limit(size).all()
    
    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count,
        page=page,
        size=size
    )

@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("NOTIFICATIONS_READ"))
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if notif.status != NotificationStatus.READ:
        notif.status = NotificationStatus.READ
        notif.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notif)
        
    return notif

@router.post("/read-all", response_model=dict)
def mark_all_read(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("NOTIFICATIONS_READ"))
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status != NotificationStatus.READ
    ).update({
        "status": NotificationStatus.READ.value,
        "read_at": datetime.now(timezone.utc)
    })
    
    db.commit()
    return {"status": "success"}

@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    prefs = db.query(NotificationPreference).filter(NotificationPreference.user_id == current_user.id).first()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs

@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    prefs_update: NotificationPreferenceUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    prefs = db.query(NotificationPreference).filter(NotificationPreference.user_id == current_user.id).first()
    if not prefs:
        prefs = NotificationPreference(user_id=current_user.id)
        db.add(prefs)
    
    update_data = prefs_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prefs, key, value)
        
    prefs.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(prefs)
    return prefs
