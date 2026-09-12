from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class TimeRange(BaseModel):
    start: datetime
    end: datetime

class ApplicationActivity(BaseModel):
    application_id: str
    application_name: str
    event_count: int

class RecentEvent(BaseModel):
    id: str
    timestamp: datetime
    severity: str
    event_type: str
    application_name: str
    username: Optional[str]
    source_ip: Optional[str]

class DashboardOverviewResponse(BaseModel):
    time_range: TimeRange
    total_events: int
    critical_events: int
    high_events: int
    active_applications: int
    events_per_hour: float
    severity_distribution: Dict[str, int]
    event_type_distribution: Dict[str, int]
    application_activity: List[ApplicationActivity]
    application_status: Dict[str, int]
    environment_distribution: Dict[str, int]
    production_events: int
    risk_summary: Optional[Dict[str, int]] = None
    event_timeline: List[Dict[str, int | str]]  # Format: [{"timestamp": "...", "count": 0}]
    latest_event_timestamp: Optional[datetime]
    recent_events: List[RecentEvent]
