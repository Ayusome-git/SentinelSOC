from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from app.models.security_event import SecurityEvent, EventSeverity
from app.models.application import Application, AppStatus, AppEnvironment
from app.schemas.dashboard import DashboardOverviewResponse, TimeRange, ApplicationActivity, RecentEvent

def get_dashboard_overview(db: Session, start_date: datetime, end_date: datetime) -> DashboardOverviewResponse:
    # Basic filters
    base_query = db.query(SecurityEvent).filter(
        SecurityEvent.timestamp >= start_date,
        SecurityEvent.timestamp <= end_date
    )

    # 1. KPIs (Total, Critical, High)
    # Using a single query with conditional counts for performance
    kpi_row = base_query.with_entities(
        func.count(SecurityEvent.id).label("total"),
        func.sum(case((SecurityEvent.severity == EventSeverity.CRITICAL.value, 1), else_=0)).label("critical"),
        func.sum(case((SecurityEvent.severity == EventSeverity.HIGH.value, 1), else_=0)).label("high")
    ).first()

    total_events = kpi_row.total or 0
    critical_events = int(kpi_row.critical or 0)
    high_events = int(kpi_row.high or 0)

    # 2. Events per Hour
    duration_hours = (end_date - start_date).total_seconds() / 3600.0
    events_per_hour = total_events / duration_hours if duration_hours > 0 else 0.0

    # 3. Active Applications (current state)
    active_applications = db.query(Application).filter(Application.status == AppStatus.ACTIVE.value).count()

    # 4. Severity Distribution
    sev_rows = base_query.with_entities(
        SecurityEvent.severity, func.count(SecurityEvent.id)
    ).group_by(SecurityEvent.severity).all()
    severity_distribution = {sev: cnt for sev, cnt in sev_rows}

    # 5. Event Type Distribution
    type_rows = base_query.with_entities(
        SecurityEvent.event_type, func.count(SecurityEvent.id)
    ).group_by(SecurityEvent.event_type).order_by(desc(func.count(SecurityEvent.id))).limit(10).all()
    event_type_distribution = {et: cnt for et, cnt in type_rows}

    # 6. Application Status & Environment Distribution (current state)
    app_status_rows = db.query(Application.status, func.count(Application.id)).group_by(Application.status).all()
    application_status = {st: cnt for st, cnt in app_status_rows}

    app_env_rows = db.query(Application.environment, func.count(Application.id)).group_by(Application.environment).all()
    environment_distribution = {env: cnt for env, cnt in app_env_rows}

    # 7. Application Activity & Production Events
    # Join with Application
    app_join_query = base_query.join(Application, SecurityEvent.application_id == Application.id)
    
    app_activity_rows = app_join_query.with_entities(
        Application.id, Application.name, func.count(SecurityEvent.id)
    ).group_by(Application.id, Application.name).order_by(desc(func.count(SecurityEvent.id))).limit(10).all()
    
    application_activity = [
        ApplicationActivity(application_id=str(row[0]), application_name=row[1], event_count=row[2])
        for row in app_activity_rows
    ]

    production_events = app_join_query.filter(
        Application.environment == AppEnvironment.PRODUCTION.value
    ).count()

    # 8. Event Timeline
    # Determine bucketing
    if duration_hours <= 24:
        trunc = "hour"
    elif duration_hours <= 24 * 7:
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
        timeline_rows = base_query.with_entities(
            func.strftime(fmt, SecurityEvent.timestamp).label("ts"), 
            func.count(SecurityEvent.id)
        ).group_by("ts").order_by("ts").all()
    else:
        timeline_rows = base_query.with_entities(
            func.date_trunc(trunc, SecurityEvent.timestamp).label("ts"), 
            func.count(SecurityEvent.id)
        ).group_by("ts").order_by("ts").all()

    timeline = []
    for ts, cnt in timeline_rows:
        if ts:
            if isinstance(ts, str):
                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            elif ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            timeline.append({"timestamp": ts.isoformat(), "count": cnt})

    # 9. Recent Events
    recent_event_records = app_join_query.with_entities(
        SecurityEvent.id, SecurityEvent.timestamp, SecurityEvent.severity, 
        SecurityEvent.event_type, Application.name.label("application_name"), 
        SecurityEvent.username, SecurityEvent.user_id, SecurityEvent.source_ip
    ).order_by(desc(SecurityEvent.timestamp)).limit(10).all()
    
    recent_events = []
    for r in recent_event_records:
        uname = r.username or r.user_id
        recent_events.append(
            RecentEvent(
                id=str(r.id),
                timestamp=r.timestamp,
                severity=r.severity,
                event_type=r.event_type,
                application_name=r.application_name,
                username=uname,
                source_ip=r.source_ip
            )
        )

    # 10. Latest Event Timestamp
    latest = base_query.with_entities(SecurityEvent.timestamp).order_by(desc(SecurityEvent.timestamp)).first()
    latest_event_timestamp = latest[0] if latest else None

    return DashboardOverviewResponse(
        time_range=TimeRange(start=start_date, end=end_date),
        total_events=total_events,
        critical_events=critical_events,
        high_events=high_events,
        active_applications=active_applications,
        events_per_hour=round(events_per_hour, 2),
        severity_distribution=severity_distribution,
        event_type_distribution=event_type_distribution,
        application_activity=application_activity,
        application_status=application_status,
        environment_distribution=environment_distribution,
        production_events=production_events,
        event_timeline=timeline,
        latest_event_timestamp=latest_event_timestamp,
        recent_events=recent_events
    )
