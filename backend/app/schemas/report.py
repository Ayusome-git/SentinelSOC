from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class ReportFilters(BaseModel):
    start_date: datetime
    end_date: datetime
    application_id: Optional[UUID] = None
    severity: Optional[str] = None
    
# Reusable base for report responses
class BaseReportResponse(BaseModel):
    from_date: datetime
    to_date: datetime
    generated_at: datetime
    filters: Dict[str, Any]

class TrendPoint(BaseModel):
    timestamp: datetime
    count: int

# Security Overview Report
class SecurityOverviewSummary(BaseModel):
    total_events: int
    critical_events: int
    high_events: int
    medium_events: int
    low_events: int
    total_alerts: int
    open_alerts: int
    critical_alerts: int
    high_risk_alerts: int
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    resolved_incidents: int
    average_alert_risk: Optional[float]
    max_alert_risk: Optional[float]
    total_response_actions: int
    successful_response_actions: int
    failed_response_actions: int

class SecurityOverviewTrend(BaseModel):
    events: List[TrendPoint]
    alerts: List[TrendPoint]
    incidents: List[TrendPoint]

class SecurityOverviewReport(BaseReportResponse):
    summary: SecurityOverviewSummary
    trends: SecurityOverviewTrend
    comparison: Optional[Dict[str, Any]] = None

# Alert Summary Report
class AlertSummaryMetrics(BaseModel):
    total: int
    open: int
    acknowledged: int
    resolved: int
    false_positives: int
    critical: int
    high: int
    medium: int
    low: int
    avg_risk: Optional[float]
    max_risk: Optional[float]
    unassigned: int
    assigned: int
    
class AlertSummaryBreakdowns(BaseModel):
    by_severity: Dict[str, int]
    by_rule: Dict[str, int]
    by_application: Dict[str, int]
    by_status: Dict[str, int]

class AlertSummaryReport(BaseReportResponse):
    summary: AlertSummaryMetrics
    breakdowns: AlertSummaryBreakdowns
    comparison: Optional[Dict[str, Any]] = None

# Incident Summary Report
class IncidentSummaryMetrics(BaseModel):
    total: int
    open: int
    investigating: int
    contained: int
    resolved: int
    closed: int
    critical: int
    high: int
    medium: int
    low: int
    avg_risk: Optional[float]
    max_risk: Optional[float]

class IncidentSummaryBreakdowns(BaseModel):
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    by_application: Dict[str, int]

class IncidentSummaryReport(BaseReportResponse):
    summary: IncidentSummaryMetrics
    breakdowns: IncidentSummaryBreakdowns
    trends: List[TrendPoint]
    comparison: Optional[Dict[str, Any]] = None

# Attack Activity Report
class AttackCategory(BaseModel):
    category: str
    detection_count: int
    alert_count: int
    critical_count: int
    high_risk_count: int
    incident_count: int
    avg_risk: Optional[float]

class AttackActivityReport(BaseReportResponse):
    categories: List[AttackCategory]
    top_rules: List[Dict[str, Any]]
    
# Application Security Report
class ApplicationSecurityMetrics(BaseModel):
    application_id: UUID
    name: str
    environment: str
    status: str
    events: int
    alerts: int
    critical_alerts: int
    incidents: int
    critical_incidents: int
    avg_risk: Optional[float]
    max_risk: Optional[float]
    last_event_at: Optional[datetime]
    last_alert_at: Optional[datetime]
    last_incident_at: Optional[datetime]

class ApplicationSecurityReport(BaseReportResponse):
    applications: List[ApplicationSecurityMetrics]

# Risk Analysis Report
class RiskMetrics(BaseModel):
    avg_alert_risk: Optional[float]
    avg_incident_risk: Optional[float]
    max_alert_risk: Optional[float]
    max_incident_risk: Optional[float]

class RiskDistribution(BaseModel):
    low: int
    moderate: int
    high: int
    critical: int

class RiskAnalysisReport(BaseReportResponse):
    metrics: RiskMetrics
    distribution: RiskDistribution
    risk_by_application: Dict[str, float]
    risk_by_rule: Dict[str, float]
    top_high_risk_alerts: List[Dict[str, Any]]
    top_high_risk_incidents: List[Dict[str, Any]]
    trends: List[TrendPoint]
    
# Response Action Summary Report
class ResponseActionMetrics(BaseModel):
    total: int
    pending: int
    approved: int
    executing: int
    succeeded: int
    failed: int
    cancelled: int
    rejected: int
    success_rate: Optional[float]
    failure_rate: Optional[float]

class ResponseActionBreakdowns(BaseModel):
    by_type: Dict[str, int]
    by_application: Dict[str, int]
    by_status: Dict[str, int]

class ResponseActionReport(BaseReportResponse):
    summary: ResponseActionMetrics
    breakdowns: ResponseActionBreakdowns

# Event Activity Report
class EventMetrics(BaseModel):
    total: int
    login_failures: int
    login_successes: int
    permission_denied: int
    api_errors: int
    suspicious_requests: int
    admin_actions: int

class EventBreakdowns(BaseModel):
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    by_application: Dict[str, int]

class EventActivityReport(BaseReportResponse):
    summary: EventMetrics
    breakdowns: EventBreakdowns
    trends: List[TrendPoint]
