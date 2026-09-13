from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, and_
import uuid

from app.models.security_event import SecurityEvent
from app.models.alert import Alert, AlertStatus
from app.models.incident import Incident, IncidentStatus
from app.models.application import Application
from app.models.response import ResponseAction, ResponseActionStatus
from app.models.detection_rule import DetectionRule
from app.schemas.report import (
    ReportFilters, SecurityOverviewReport, SecurityOverviewSummary, SecurityOverviewTrend, TrendPoint,
    AlertSummaryReport, AlertSummaryMetrics, AlertSummaryBreakdowns,
    IncidentSummaryReport, IncidentSummaryMetrics, IncidentSummaryBreakdowns,
    AttackActivityReport, AttackCategory,
    ApplicationSecurityReport, ApplicationSecurityMetrics,
    RiskAnalysisReport, RiskMetrics, RiskDistribution,
    ResponseActionReport, ResponseActionMetrics, ResponseActionBreakdowns,
    EventActivityReport, EventMetrics, EventBreakdowns
)
from app.services.report_query_service import ReportQueryService

class ReportService:
    @staticmethod
    def _parse_ts(ts) -> datetime:
        if isinstance(ts, str):
            try:
                return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except ValueError:
                # SQLite week might be YYYY-WW
                return datetime.strptime(ts + "-1", "%Y-%W-%w").replace(tzinfo=timezone.utc)
        if hasattr(ts, 'tzinfo') and ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts

    @staticmethod
    def get_security_overview(db: Session, filters: ReportFilters) -> SecurityOverviewReport:
        # Event stats
        event_query = db.query(
            func.count(SecurityEvent.id),
            func.sum(case((SecurityEvent.severity == 'CRITICAL', 1), else_=0)),
            func.sum(case((SecurityEvent.severity == 'HIGH', 1), else_=0)),
            func.sum(case((SecurityEvent.severity == 'MEDIUM', 1), else_=0)),
            func.sum(case((SecurityEvent.severity == 'LOW', 1), else_=0))
        ).filter(ReportQueryService.build_event_filters(filters)).first()
        
        # Alert stats
        alert_query = db.query(
            func.count(Alert.id),
            func.sum(case((Alert.status == AlertStatus.OPEN.value, 1), else_=0)),
            func.sum(case((Alert.severity == 'CRITICAL', 1), else_=0)),
            func.sum(case((Alert.risk_score >= 75, 1), else_=0)),
            func.avg(Alert.risk_score),
            func.max(Alert.risk_score)
        ).filter(ReportQueryService.build_alert_filters(filters)).first()
        
        # Incident stats
        incident_query = db.query(
            func.count(Incident.id),
            func.sum(case((Incident.status == IncidentStatus.OPEN.value, 1), else_=0)),
            func.sum(case((Incident.severity == 'CRITICAL', 1), else_=0)),
            func.sum(case((Incident.status == IncidentStatus.RESOLVED.value, 1), else_=0))
        ).filter(ReportQueryService.build_incident_filters(filters)).first()
        
        # Response Action stats
        action_query = db.query(
            func.count(ResponseAction.id),
            func.sum(case((ResponseAction.status == ResponseActionStatus.SUCCEEDED.value, 1), else_=0)),
            func.sum(case((ResponseAction.status == ResponseActionStatus.FAILED.value, 1), else_=0))
        ).filter(ReportQueryService.build_action_filters(filters)).first()
        
        summary = SecurityOverviewSummary(
            total_events=event_query[0] or 0,
            critical_events=event_query[1] or 0,
            high_events=event_query[2] or 0,
            medium_events=event_query[3] or 0,
            low_events=event_query[4] or 0,
            
            total_alerts=alert_query[0] or 0,
            open_alerts=alert_query[1] or 0,
            critical_alerts=alert_query[2] or 0,
            high_risk_alerts=alert_query[3] or 0,
            average_alert_risk=float(alert_query[4]) if alert_query[4] is not None else None,
            max_alert_risk=float(alert_query[5]) if alert_query[5] is not None else None,
            
            total_incidents=incident_query[0] or 0,
            open_incidents=incident_query[1] or 0,
            critical_incidents=incident_query[2] or 0,
            resolved_incidents=incident_query[3] or 0,
            
            total_response_actions=action_query[0] or 0,
            successful_response_actions=action_query[1] or 0,
            failed_response_actions=action_query[2] or 0,
        )
        
        trends = SecurityOverviewTrend(
            events=[TrendPoint(timestamp=ReportService._parse_ts(p['timestamp']), count=p['count']) for p in ReportQueryService.get_event_trend(db, filters)],
            alerts=[TrendPoint(timestamp=ReportService._parse_ts(p['timestamp']), count=p['count']) for p in ReportQueryService.get_alert_trend(db, filters)],
            incidents=[TrendPoint(timestamp=ReportService._parse_ts(p['timestamp']), count=p['count']) for p in ReportQueryService.get_incident_trend(db, filters)]
        )
        
        return SecurityOverviewReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            summary=summary,
            trends=trends
        )

    @staticmethod
    def get_alert_summary(db: Session, filters: ReportFilters) -> AlertSummaryReport:
        base_query = db.query(Alert).filter(ReportQueryService.build_alert_filters(filters))
        
        agg = db.query(
            func.count(Alert.id),
            func.sum(case((Alert.status == AlertStatus.OPEN.value, 1), else_=0)),
            func.sum(case((Alert.status == AlertStatus.ACKNOWLEDGED.value, 1), else_=0)),
            func.sum(case((Alert.status == AlertStatus.RESOLVED.value, 1), else_=0)),
            func.sum(case((Alert.status == AlertStatus.FALSE_POSITIVE.value, 1), else_=0)),
            func.sum(case((Alert.severity == 'CRITICAL', 1), else_=0)),
            func.sum(case((Alert.severity == 'HIGH', 1), else_=0)),
            func.sum(case((Alert.severity == 'MEDIUM', 1), else_=0)),
            func.sum(case((Alert.severity == 'LOW', 1), else_=0)),
            func.avg(Alert.risk_score),
            func.max(Alert.risk_score),
            func.sum(case((Alert.assigned_to == None, 1), else_=0)),
            func.sum(case((Alert.assigned_to != None, 1), else_=0))
        ).filter(ReportQueryService.build_alert_filters(filters)).first()
        
        summary = AlertSummaryMetrics(
            total=agg[0] or 0,
            open=agg[1] or 0,
            acknowledged=agg[2] or 0,
            resolved=agg[3] or 0,
            false_positives=agg[4] or 0,
            critical=agg[5] or 0,
            high=agg[6] or 0,
            medium=agg[7] or 0,
            low=agg[8] or 0,
            avg_risk=float(agg[9]) if agg[9] is not None else None,
            max_risk=float(agg[10]) if agg[10] is not None else None,
            unassigned=agg[11] or 0,
            assigned=agg[12] or 0
        )
        
        sev_counts = dict(db.query(Alert.severity, func.count(Alert.id)).filter(ReportQueryService.build_alert_filters(filters)).group_by(Alert.severity).all())
        stat_counts = dict(db.query(Alert.status, func.count(Alert.id)).filter(ReportQueryService.build_alert_filters(filters)).group_by(Alert.status).all())
        
        # By rule
        rule_query = db.query(DetectionRule.name, func.count(Alert.id)).join(
            Alert, Alert.rule_id == DetectionRule.id
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by(DetectionRule.name).order_by(desc(func.count(Alert.id))).limit(10).all()
        rule_counts = {r[0]: r[1] for r in rule_query}
        
        # By application
        app_query = db.query(Application.name, func.count(Alert.id)).join(
            Alert, Alert.application_id == Application.id
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by(Application.name).order_by(desc(func.count(Alert.id))).limit(10).all()
        app_counts = {a[0]: a[1] for a in app_query}

        breakdowns = AlertSummaryBreakdowns(
            by_severity=sev_counts,
            by_status=stat_counts,
            by_rule=rule_counts,
            by_application=app_counts
        )

        return AlertSummaryReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            summary=summary,
            breakdowns=breakdowns
        )

    @staticmethod
    def get_incident_summary(db: Session, filters: ReportFilters) -> IncidentSummaryReport:
        agg = db.query(
            func.count(Incident.id),
            func.sum(case((Incident.status == IncidentStatus.OPEN.value, 1), else_=0)),
            func.sum(case((Incident.status == IncidentStatus.INVESTIGATING.value, 1), else_=0)),
            func.sum(case((Incident.status == IncidentStatus.CONTAINED.value, 1), else_=0)),
            func.sum(case((Incident.status == IncidentStatus.RESOLVED.value, 1), else_=0)),
            func.sum(case((Incident.status == IncidentStatus.CLOSED.value, 1), else_=0)),
            func.sum(case((Incident.severity == 'CRITICAL', 1), else_=0)),
            func.sum(case((Incident.severity == 'HIGH', 1), else_=0)),
            func.sum(case((Incident.severity == 'MEDIUM', 1), else_=0)),
            func.sum(case((Incident.severity == 'LOW', 1), else_=0)),
            func.avg(Incident.risk_score),
            func.max(Incident.risk_score)
        ).filter(ReportQueryService.build_incident_filters(filters)).first()
        
        summary = IncidentSummaryMetrics(
            total=agg[0] or 0,
            open=agg[1] or 0,
            investigating=agg[2] or 0,
            contained=agg[3] or 0,
            resolved=agg[4] or 0,
            closed=agg[5] or 0,
            critical=agg[6] or 0,
            high=agg[7] or 0,
            medium=agg[8] or 0,
            low=agg[9] or 0,
            avg_risk=float(agg[10]) if agg[10] is not None else None,
            max_risk=float(agg[11]) if agg[11] is not None else None
        )
        
        sev_counts = dict(db.query(Incident.severity, func.count(Incident.id)).filter(ReportQueryService.build_incident_filters(filters)).group_by(Incident.severity).all())
        stat_counts = dict(db.query(Incident.status, func.count(Incident.id)).filter(ReportQueryService.build_incident_filters(filters)).group_by(Incident.status).all())
        
        app_query = db.query(Application.name, func.count(Incident.id)).join(
            Incident, Incident.application_id == Application.id
        ).filter(ReportQueryService.build_incident_filters(filters)).group_by(Application.name).order_by(desc(func.count(Incident.id))).limit(10).all()
        app_counts = {a[0]: a[1] for a in app_query}
        
        breakdowns = IncidentSummaryBreakdowns(
            by_severity=sev_counts,
            by_status=stat_counts,
            by_application=app_counts
        )
        
        trends = [TrendPoint(timestamp=ReportService._parse_ts(p['timestamp']), count=p['count']) for p in ReportQueryService.get_incident_trend(db, filters)]
        
        return IncidentSummaryReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            summary=summary,
            breakdowns=breakdowns,
            trends=trends
        )

    @staticmethod
    def get_attack_activity(db: Session, filters: ReportFilters) -> AttackActivityReport:
        # We group by DetectionRule category
        rows = db.query(
            DetectionRule.category,
            func.count(Alert.id),
            func.sum(case((Alert.severity == 'CRITICAL', 1), else_=0)),
            func.sum(case((Alert.risk_score >= 75, 1), else_=0)),
            func.avg(Alert.risk_score)
        ).join(
            Alert, Alert.rule_id == DetectionRule.id
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by(DetectionRule.category).all()
        
        categories = []
        for r in rows:
            cat = r[0] or "Other"
            categories.append(AttackCategory(
                category=cat,
                detection_count=r[1],
                alert_count=r[1],
                critical_count=r[2],
                high_risk_count=r[3],
                incident_count=0, # Hard to accurately map alert->incident count in a simple query, omit or proxy
                avg_risk=float(r[4]) if r[4] is not None else None
            ))
            
        top_rules = []
        rule_rows = db.query(
            DetectionRule.name,
            func.count(Alert.id)
        ).join(
            Alert, Alert.rule_id == DetectionRule.id
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by(DetectionRule.name).order_by(desc(func.count(Alert.id))).limit(10).all()
        
        for r in rule_rows:
            top_rules.append({"rule_name": r[0], "alert_count": r[1]})
            
        return AttackActivityReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            categories=categories,
            top_rules=top_rules
        )

    @staticmethod
    def get_application_security(db: Session, filters: ReportFilters) -> ApplicationSecurityReport:
        app_query = db.query(Application)
        if filters.application_id:
            app_query = app_query.filter(Application.id == filters.application_id)
            
        apps = app_query.all()
        app_metrics = []
        
        # We do N queries if N is small, or do group_bys
        # For safety, let's do group_bys and map
        
        # Events
        event_counts = dict(db.query(SecurityEvent.application_id, func.count(SecurityEvent.id)).filter(ReportQueryService.build_event_filters(filters)).group_by(SecurityEvent.application_id).all())
        last_events = dict(db.query(SecurityEvent.application_id, func.max(SecurityEvent.timestamp)).filter(ReportQueryService.build_event_filters(filters)).group_by(SecurityEvent.application_id).all())
        
        # Alerts
        alert_agg = db.query(
            Alert.application_id, 
            func.count(Alert.id),
            func.sum(case((Alert.severity == 'CRITICAL', 1), else_=0)),
            func.avg(Alert.risk_score),
            func.max(Alert.risk_score),
            func.max(Alert.detected_at)
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by(Alert.application_id).all()
        
        alert_data = {a[0]: {"count": a[1], "critical": a[2], "avg_risk": a[3], "max_risk": a[4], "last": a[5]} for a in alert_agg}
        
        # Incidents
        inc_agg = db.query(
            Incident.application_id,
            func.count(Incident.id),
            func.sum(case((Incident.severity == 'CRITICAL', 1), else_=0)),
            func.max(Incident.detected_at)
        ).filter(ReportQueryService.build_incident_filters(filters)).group_by(Incident.application_id).all()
        
        inc_data = {i[0]: {"count": i[1], "critical": i[2], "last": i[3]} for i in inc_agg}
        
        for app in apps:
            a_data = alert_data.get(app.id, {})
            i_data = inc_data.get(app.id, {})
            
            # Skip apps with absolutely no activity if we want, but better to show them as 0 if they matched the filter
            if not filters.application_id and event_counts.get(app.id, 0) == 0 and a_data.get("count", 0) == 0:
                continue
                
            app_metrics.append(ApplicationSecurityMetrics(
                application_id=app.id,
                name=app.name,
                environment=app.environment,
                status=app.status,
                events=event_counts.get(app.id, 0),
                alerts=a_data.get("count", 0),
                critical_alerts=a_data.get("critical", 0),
                incidents=i_data.get("count", 0),
                critical_incidents=i_data.get("critical", 0),
                avg_risk=float(a_data.get("avg_risk")) if a_data.get("avg_risk") is not None else None,
                max_risk=float(a_data.get("max_risk")) if a_data.get("max_risk") is not None else None,
                last_event_at=ReportService._parse_ts(last_events.get(app.id)) if last_events.get(app.id) else None,
                last_alert_at=ReportService._parse_ts(a_data.get("last")) if a_data.get("last") else None,
                last_incident_at=ReportService._parse_ts(i_data.get("last")) if i_data.get("last") else None
            ))
            
        # Sort by alerts desc
        app_metrics.sort(key=lambda x: x.alerts, reverse=True)
            
        return ApplicationSecurityReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            applications=app_metrics
        )

    @staticmethod
    def get_risk_analysis(db: Session, filters: ReportFilters) -> RiskAnalysisReport:
        a_agg = db.query(
            func.avg(Alert.risk_score),
            func.max(Alert.risk_score)
        ).filter(ReportQueryService.build_alert_filters(filters)).first()
        
        i_agg = db.query(
            func.avg(Incident.risk_score),
            func.max(Incident.risk_score)
        ).filter(ReportQueryService.build_incident_filters(filters)).first()
        
        metrics = RiskMetrics(
            avg_alert_risk=float(a_agg[0]) if a_agg[0] is not None else None,
            max_alert_risk=float(a_agg[1]) if a_agg[1] is not None else None,
            avg_incident_risk=float(i_agg[0]) if i_agg[0] is not None else None,
            max_incident_risk=float(i_agg[1]) if i_agg[1] is not None else None
        )
        
        # Distribution
        d_agg = db.query(
            func.sum(case((Alert.risk_score < 25, 1), else_=0)),
            func.sum(case((and_(Alert.risk_score >= 25, Alert.risk_score < 50), 1), else_=0)),
            func.sum(case((and_(Alert.risk_score >= 50, Alert.risk_score < 75), 1), else_=0)),
            func.sum(case((Alert.risk_score >= 75, 1), else_=0))
        ).filter(ReportQueryService.build_alert_filters(filters)).first()
        
        distribution = RiskDistribution(
            low=d_agg[0] or 0,
            moderate=d_agg[1] or 0,
            high=d_agg[2] or 0,
            critical=d_agg[3] or 0
        )
        
        # Risk by Application
        app_risk = db.query(Application.name, func.avg(Alert.risk_score)).join(
            Alert, Alert.application_id == Application.id
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by(Application.name).all()
        risk_by_app = {r[0]: float(r[1]) if r[1] is not None else 0 for r in app_risk}
        
        # Risk by Rule
        rule_risk = db.query(DetectionRule.name, func.avg(Alert.risk_score)).join(
            Alert, Alert.rule_id == DetectionRule.id
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by(DetectionRule.name).all()
        risk_by_rule = {r[0]: float(r[1]) if r[1] is not None else 0 for r in rule_risk}
        
        # Top High Risk Alerts
        top_alerts = db.query(Alert).filter(
            ReportQueryService.build_alert_filters(filters),
            Alert.risk_score != None
        ).order_by(desc(Alert.risk_score)).limit(5).all()
        top_alerts_list = [{"id": str(a.id), "title": a.title, "risk_score": a.risk_score} for a in top_alerts]
        
        # Top High Risk Incidents
        top_incidents = db.query(Incident).filter(
            ReportQueryService.build_incident_filters(filters),
            Incident.risk_score != None
        ).order_by(desc(Incident.risk_score)).limit(5).all()
        top_inc_list = [{"id": str(i.id), "title": i.title, "risk_score": i.risk_score} for i in top_incidents]
        
        # Trend
        bucket = ReportQueryService.determine_bucket(filters.start_date, filters.end_date)
        trunc_expr = ReportQueryService.get_date_trunc_expr(db, Alert.detected_at, bucket)
        
        rows = db.query(
            trunc_expr.label('ts'),
            func.avg(Alert.risk_score)
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by('ts').order_by('ts').all()
        
        trends = [{"timestamp": ReportService._parse_ts(r[0]), "count": int(r[1] or 0)} for r in rows if r[0]]
        
        return RiskAnalysisReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            metrics=metrics,
            distribution=distribution,
            risk_by_application=risk_by_app,
            risk_by_rule=risk_by_rule,
            top_high_risk_alerts=top_alerts_list,
            top_high_risk_incidents=top_inc_list,
            trends=[TrendPoint(**t) for t in trends]
        )

    @staticmethod
    def get_response_action_summary(db: Session, filters: ReportFilters) -> ResponseActionReport:
        agg = db.query(
            func.count(ResponseAction.id),
            func.sum(case((ResponseAction.status == ResponseActionStatus.PENDING_APPROVAL.value, 1), else_=0)),
            func.sum(case((ResponseAction.status == ResponseActionStatus.APPROVED.value, 1), else_=0)),
            func.sum(case((ResponseAction.status == ResponseActionStatus.EXECUTING.value, 1), else_=0)),
            func.sum(case((ResponseAction.status == ResponseActionStatus.SUCCEEDED.value, 1), else_=0)),
            func.sum(case((ResponseAction.status == ResponseActionStatus.FAILED.value, 1), else_=0)),
            func.sum(case((ResponseAction.status == ResponseActionStatus.CANCELLED.value, 1), else_=0)),
            func.sum(case((ResponseAction.status == ResponseActionStatus.REJECTED.value, 1), else_=0))
        ).filter(ReportQueryService.build_action_filters(filters)).first()
        
        total = agg[0] or 0
        succeeded = agg[4] or 0
        failed = agg[5] or 0
        
        success_rate = (succeeded / total * 100) if total > 0 else None
        failure_rate = (failed / total * 100) if total > 0 else None
        
        summary = ResponseActionMetrics(
            total=total,
            pending=agg[1] or 0,
            approved=agg[2] or 0,
            executing=agg[3] or 0,
            succeeded=succeeded,
            failed=failed,
            cancelled=agg[6] or 0,
            rejected=agg[7] or 0,
            success_rate=success_rate,
            failure_rate=failure_rate
        )
        
        # Breakdowns
        type_counts = dict(db.query(ResponseAction.action_type, func.count(ResponseAction.id)).filter(ReportQueryService.build_action_filters(filters)).group_by(ResponseAction.action_type).all())
        stat_counts = dict(db.query(ResponseAction.status, func.count(ResponseAction.id)).filter(ReportQueryService.build_action_filters(filters)).group_by(ResponseAction.status).all())
        
        app_query = db.query(Application.name, func.count(ResponseAction.id)).join(
            ResponseAction, ResponseAction.application_id == Application.id
        ).filter(ReportQueryService.build_action_filters(filters)).group_by(Application.name).all()
        app_counts = {a[0]: a[1] for a in app_query}
        
        breakdowns = ResponseActionBreakdowns(
            by_type=type_counts,
            by_application=app_counts,
            by_status=stat_counts
        )
        
        return ResponseActionReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            summary=summary,
            breakdowns=breakdowns
        )

    @staticmethod
    def get_event_activity(db: Session, filters: ReportFilters) -> EventActivityReport:
        agg = db.query(
            func.count(SecurityEvent.id),
            func.sum(case((SecurityEvent.event_type == 'LOGIN_FAILED', 1), else_=0)),
            func.sum(case((SecurityEvent.event_type == 'LOGIN_SUCCESS', 1), else_=0)),
            func.sum(case((SecurityEvent.event_type == 'PERMISSION_DENIED', 1), else_=0)),
            func.sum(case((SecurityEvent.event_type == 'API_ERROR', 1), else_=0)),
            func.sum(case((SecurityEvent.event_type == 'SUSPICIOUS_REQUEST', 1), else_=0)),
            func.sum(case((SecurityEvent.event_type == 'ADMIN_ACTION', 1), else_=0))
        ).filter(ReportQueryService.build_event_filters(filters)).first()
        
        summary = EventMetrics(
            total=agg[0] or 0,
            login_failures=agg[1] or 0,
            login_successes=agg[2] or 0,
            permission_denied=agg[3] or 0,
            api_errors=agg[4] or 0,
            suspicious_requests=agg[5] or 0,
            admin_actions=agg[6] or 0
        )
        
        sev_counts = dict(db.query(SecurityEvent.severity, func.count(SecurityEvent.id)).filter(ReportQueryService.build_event_filters(filters)).group_by(SecurityEvent.severity).all())
        type_counts = dict(db.query(SecurityEvent.event_type, func.count(SecurityEvent.id)).filter(ReportQueryService.build_event_filters(filters)).group_by(SecurityEvent.event_type).all())
        
        app_query = db.query(Application.name, func.count(SecurityEvent.id)).join(
            SecurityEvent, SecurityEvent.application_id == Application.id
        ).filter(ReportQueryService.build_event_filters(filters)).group_by(Application.name).all()
        app_counts = {a[0]: a[1] for a in app_query}
        
        breakdowns = EventBreakdowns(
            by_severity=sev_counts,
            by_type=type_counts,
            by_application=app_counts
        )
        
        trends = [TrendPoint(timestamp=ReportService._parse_ts(p['timestamp']), count=p['count']) for p in ReportQueryService.get_event_trend(db, filters)]
        
        return EventActivityReport(
            from_date=filters.start_date,
            to_date=filters.end_date,
            generated_at=datetime.now(timezone.utc),
            filters=filters.model_dump(mode="json"),
            summary=summary,
            breakdowns=breakdowns,
            trends=trends
        )
