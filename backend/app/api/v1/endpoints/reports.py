from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.core.config import settings
from app.schemas.report import (
    ReportFilters, SecurityOverviewReport, AlertSummaryReport,
    IncidentSummaryReport, AttackActivityReport, ApplicationSecurityReport,
    RiskAnalysisReport, ResponseActionReport, EventActivityReport
)
from app.services.report_service import ReportService
from app.services.report_export_service import ReportExportService
from app.services.audit_service import create_audit_log

router = APIRouter()

def validate_date_range(start_date: datetime, end_date: datetime):
    if end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date cannot be before start_date")
    
    diff_days = (end_date - start_date).days
    if diff_days > settings.REPORT_MAX_RANGE_DAYS:
        raise HTTPException(status_code=422, detail=f"Date range exceeds maximum allowed ({settings.REPORT_MAX_RANGE_DAYS} days)")

def get_report_filters(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    application_id: Optional[UUID] = None,
    severity: Optional[str] = None
) -> ReportFilters:
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
        
    validate_date_range(start_date, end_date)
    return ReportFilters(
        start_date=start_date,
        end_date=end_date,
        application_id=application_id,
        severity=severity
    )

@router.get("/security-overview", response_model=SecurityOverviewReport)
def get_security_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_security_overview(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "SECURITY_OVERVIEW", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report

@router.get("/security-overview/export")
def export_security_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    filters: ReportFilters = Depends(get_report_filters),
    format: str = Query("pdf", pattern="^(pdf|csv)$")
):
    deps.check_app_access(current_user, filters.application_id)
    report = ReportService.get_security_overview(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_EXPORTED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "SECURITY_OVERVIEW", "format": format, "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    if format == "pdf":
        pdf_bytes = ReportExportService.generate_security_overview_pdf(report)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=security_overview.pdf"})
    else:
        # Simple CSV format for overview
        data = [{"Metric": "Total Events", "Value": report.summary.total_events}, {"Metric": "Active Alerts", "Value": report.summary.open_alerts}]
        csv_str = ReportExportService.generate_csv(data)
        return Response(content=csv_str, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=security_overview.csv"})

@router.get("/alerts", response_model=AlertSummaryReport)
def get_alert_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("ALERTS_READ")),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_alert_summary(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "ALERT_SUMMARY", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report

@router.get("/incidents", response_model=IncidentSummaryReport)
def get_incident_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("INCIDENTS_READ")),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_incident_summary(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "INCIDENT_SUMMARY", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report

@router.get("/attacks", response_model=AttackActivityReport)
def get_attack_activity(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("ALERTS_READ")),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_attack_activity(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "ATTACK_ACTIVITY", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report

@router.get("/applications", response_model=ApplicationSecurityReport)
def get_application_security(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_application_security(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "APPLICATION_SECURITY", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report

@router.get("/risk", response_model=RiskAnalysisReport)
def get_risk_analysis(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_risk_analysis(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "RISK_ANALYSIS", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report

@router.get("/response-actions", response_model=ResponseActionReport)
def get_response_actions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_response_action_summary(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "RESPONSE_ACTIONS", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report

@router.get("/events", response_model=EventActivityReport)
def get_event_activity(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("EVENTS_READ")),
    filters: ReportFilters = Depends(get_report_filters)
):
    deps.check_app_access(current_user, filters.application_id)
    
    report = ReportService.get_event_activity(db, filters)
    
    create_audit_log(
        db=db,
        action="REPORT_GENERATED",
        actor_id=current_user.id,
        resource_type="REPORT",
        resource_id="N/A",
        details={"report_type": "EVENT_ACTIVITY", "filters": filters.model_dump(mode="json")}
    )
    db.commit()
    
    return report
