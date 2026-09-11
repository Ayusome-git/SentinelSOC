from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_
from fastapi import HTTPException
from app.models.security_event import SecurityEvent
from app.models.application import Application
from app.schemas.security_event import EventCreate, EventResponse, EventListResponse, EventAnalyticsResponse, EventTimelinePoint
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.detection.service import DetectionService

def normalize_and_store_event(db: Session, application: Application, event_in: EventCreate) -> str:
    source_ip_str = str(event_in.source_ip)
    
    message_val = event_in.message.strip() if event_in.message else None
    user_id_val = event_in.user_id.strip() if event_in.user_id else None
    username_val = event_in.username.strip() if event_in.username else None
    session_id_val = event_in.session_id.strip() if event_in.session_id else None
    request_id_val = event_in.request_id.strip() if event_in.request_id else None
    http_method_val = event_in.http_method.strip().upper() if event_in.http_method else None
    request_path_val = event_in.request_path.strip() if event_in.request_path else None
    user_agent_val = event_in.user_agent.strip() if event_in.user_agent else None
    
    if request_id_val:
        duplicate = db.query(SecurityEvent).filter(
            SecurityEvent.application_id == application.id,
            SecurityEvent.request_id == request_id_val,
            SecurityEvent.timestamp == event_in.timestamp
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Duplicate event detected")
    else:
        duplicate = db.query(SecurityEvent).filter(
            SecurityEvent.application_id == application.id,
            SecurityEvent.timestamp == event_in.timestamp,
            SecurityEvent.event_type == event_in.event_type.value,
            SecurityEvent.source_ip == source_ip_str
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Duplicate event detected")

    db_event = SecurityEvent(
        application_id=application.id,
        event_type=event_in.event_type.value,
        severity=event_in.severity.value,
        timestamp=event_in.timestamp,
        source_ip=source_ip_str,
        message=message_val,
        user_id=user_id_val,
        username=username_val,
        session_id=session_id_val,
        request_id=request_id_val,
        http_method=http_method_val,
        request_path=request_path_val,
        user_agent=user_agent_val,
        metadata_=event_in.metadata_
    )
    
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    DetectionService.evaluate_event(db, db_event)
    
    return str(db_event.id)

def _build_filter_query(
    db: Session,
    application_id: Optional[UUID] = None,
    event_types: Optional[List[str]] = None,
    severities: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None,
    username: Optional[str] = None,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    search: Optional[str] = None,
    is_analytics: bool = False
):
    if is_analytics:
        query = db.query(SecurityEvent)
    else:
        query = db.query(SecurityEvent, Application.name.label("application_name")).join(
            Application, SecurityEvent.application_id == Application.id
        )

    if application_id:
        query = query.filter(SecurityEvent.application_id == application_id)
    if event_types and len(event_types) > 0:
        query = query.filter(SecurityEvent.event_type.in_(event_types))
    if severities and len(severities) > 0:
        query = query.filter(SecurityEvent.severity.in_(severities))
    if start_date:
        query = query.filter(SecurityEvent.timestamp >= start_date)
    if end_date:
        query = query.filter(SecurityEvent.timestamp <= end_date)
    if source_ip:
        query = query.filter(SecurityEvent.source_ip == source_ip)
    if username:
        query = query.filter(SecurityEvent.username == username)
    if request_path:
        query = query.filter(SecurityEvent.request_path == request_path)
    if request_id:
        query = query.filter(SecurityEvent.request_id == request_id)
    if session_id:
        query = query.filter(SecurityEvent.session_id == session_id)
        
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                SecurityEvent.message.ilike(search_term),
                SecurityEvent.username.ilike(search_term),
                SecurityEvent.source_ip.ilike(search_term),
                SecurityEvent.request_path.ilike(search_term),
                SecurityEvent.request_id.ilike(search_term),
                SecurityEvent.session_id.ilike(search_term),
            )
        )
        
    return query

def list_events(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    application_id: Optional[UUID] = None,
    event_types: Optional[List[str]] = None,
    severities: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None,
    username: Optional[str] = None,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_dir: str = "newest"
) -> EventListResponse:
    
    # 90 days protection
    if start_date and end_date:
        if (end_date - start_date).days > 90:
            raise HTTPException(status_code=400, detail="Time range cannot exceed 90 days")

    query = _build_filter_query(
        db, application_id, event_types, severities, start_date, end_date,
        source_ip, username, request_path, request_id, session_id, search
    )

    total = query.count()
    
    if sort_dir == "oldest":
        query = query.order_by(asc(SecurityEvent.timestamp))
    else:
        query = query.order_by(desc(SecurityEvent.timestamp))
    
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = []
    for event, app_name in records:
        resp_data = {k: getattr(event, k) for k in event.__mapper__.columns.keys()}
        resp_data["application_name"] = app_name
        resp = EventResponse.model_validate(resp_data)
        items.append(resp)

    return EventListResponse(
        total=total,
        items=items,
        page=page,
        page_size=page_size
    )

def get_event_analytics(
    db: Session,
    application_id: Optional[UUID] = None,
    event_types: Optional[List[str]] = None,
    severities: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    source_ip: Optional[str] = None,
    username: Optional[str] = None,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    search: Optional[str] = None,
) -> EventAnalyticsResponse:

    # Limit to 90 days logic
    if not end_date:
        end_date = datetime.now(timezone.utc)
    if not start_date:
        start_date = end_date - timedelta(days=1)
        
    if (end_date - start_date).days > 90:
        raise HTTPException(status_code=400, detail="Time range cannot exceed 90 days")

    query = _build_filter_query(
        db, application_id, event_types, severities, start_date, end_date,
        source_ip, username, request_path, request_id, session_id, search,
        is_analytics=True
    )
    
    total = query.count()
    
    # Aggregations
    severity_counts = {}
    sev_rows = query.with_entities(SecurityEvent.severity, func.count(SecurityEvent.id)).group_by(SecurityEvent.severity).all()
    for sev, cnt in sev_rows:
        severity_counts[sev] = cnt
        
    event_type_counts = {}
    type_rows = query.with_entities(SecurityEvent.event_type, func.count(SecurityEvent.id)).group_by(SecurityEvent.event_type).order_by(desc(func.count(SecurityEvent.id))).limit(10).all()
    for et, cnt in type_rows:
        event_type_counts[et] = cnt
        
    source_ip_counts = {}
    ip_rows = query.with_entities(SecurityEvent.source_ip, func.count(SecurityEvent.id)).group_by(SecurityEvent.source_ip).order_by(desc(func.count(SecurityEvent.id))).limit(10).all()
    for ip, cnt in ip_rows:
        if ip:
            source_ip_counts[ip] = cnt
            
    # For applications, we need a join
    app_query = _build_filter_query(
        db, application_id, event_types, severities, start_date, end_date,
        source_ip, username, request_path, request_id, session_id, search,
        is_analytics=False
    )
    application_counts = {}
    app_rows = app_query.with_entities(Application.name, func.count(SecurityEvent.id)).group_by(Application.name).order_by(desc(func.count(SecurityEvent.id))).limit(10).all()
    for an, cnt in app_rows:
        application_counts[an] = cnt
        
    # Timeline
    # Determine bucketing based on range
    diff_hours = (end_date - start_date).total_seconds() / 3600
    if diff_hours <= 24:
        trunc = "hour"
    elif diff_hours <= 24 * 7:
        trunc = "day"
    else:
        trunc = "week"
        
    if db.bind.dialect.name == "sqlite":
        if trunc == "hour":
            fmt = "%Y-%m-%d %H:00:00"
        elif trunc == "day":
            fmt = "%Y-%m-%d 00:00:00"
        else:
            fmt = "%Y-%m-01 00:00:00"
        timeline_rows = query.with_entities(func.strftime(fmt, SecurityEvent.timestamp).label("ts"), func.count(SecurityEvent.id)).group_by("ts").order_by("ts").all()
    else:
        timeline_rows = query.with_entities(func.date_trunc(trunc, SecurityEvent.timestamp).label("ts"), func.count(SecurityEvent.id)).group_by("ts").order_by("ts").all()
        
    timeline = []
    for ts, cnt in timeline_rows:
        if ts:
            if isinstance(ts, str):
                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            elif ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            timeline.append(EventTimelinePoint(timestamp=ts, count=cnt))

    return EventAnalyticsResponse(
        total=total,
        severity_counts=severity_counts,
        event_type_counts=event_type_counts,
        application_counts=application_counts,
        source_ip_counts=source_ip_counts,
        timeline=timeline
    )
