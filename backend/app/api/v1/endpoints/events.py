from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.api import deps
from app.schemas.security_event import EventCreate, EventListResponse, EventAnalyticsResponse
from app.services.event_service import normalize_and_store_event, list_events, get_event_analytics
from app.models.application import Application
from app.models.user import User

router = APIRouter()

@router.post("", status_code=status.HTTP_201_CREATED)
def ingest_event(
    *,
    db: Session = Depends(deps.get_db),
    application: Application = Depends(deps.get_application_from_api_key),
    event_in: EventCreate
):
    """
    Ingest a security event from an external application.
    Must be authenticated with an X-API-Key header.
    """
    event_id = normalize_and_store_event(db=db, application=application, event_in=event_in)
    return {"event_id": event_id, "status": "accepted"}

@router.get("", response_model=EventListResponse)
def get_events(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("EVENTS_READ")),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    application_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None,
    username: Optional[str] = None,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_dir: str = Query("newest", regex="^(newest|oldest)$")
):
    """
    List security events. Requires EVENTS_READ permission.
    """
    event_types = event_type.split(",") if event_type else None
    severities = severity.split(",") if severity else None

    return list_events(
        db=db,
        page=page,
        page_size=page_size,
        application_id=application_id,
        event_types=event_types,
        severities=severities,
        start_date=start_date,
        end_date=end_date,
        source_ip=source_ip,
        username=username,
        request_path=request_path,
        request_id=request_id,
        session_id=session_id,
        search=search,
        sort_dir=sort_dir
    )

@router.get("/analytics", response_model=EventAnalyticsResponse)
def get_events_analytics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("EVENTS_READ")),
    application_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None,
    username: Optional[str] = None,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get event analytics. Requires EVENTS_READ permission.
    """
    event_types = event_type.split(",") if event_type else None
    severities = severity.split(",") if severity else None

    return get_event_analytics(
        db=db,
        application_id=application_id,
        event_types=event_types,
        severities=severities,
        start_date=start_date,
        end_date=end_date,
        source_ip=source_ip,
        username=username,
        request_path=request_path,
        request_id=request_id,
        session_id=session_id,
        search=search
    )
