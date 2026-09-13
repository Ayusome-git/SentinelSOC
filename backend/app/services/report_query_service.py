from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, desc

from app.models.security_event import SecurityEvent
from app.models.alert import Alert, AlertStatus
from app.models.incident import Incident, IncidentStatus
from app.models.application import Application
from app.models.response import ResponseAction, ResponseActionStatus
from app.models.detection_rule import DetectionRule
from app.schemas.report import ReportFilters

class ReportQueryService:
    @staticmethod
    def get_date_trunc_expr(db: Session, field, bucket: str):
        """Helper to get date truncation based on dialect"""
        if db.bind.dialect.name == "sqlite":
            if bucket == "minute":
                return func.strftime("%Y-%m-%d %H:%M:00", field)
            elif bucket == "hour":
                return func.strftime("%Y-%m-%d %H:00:00", field)
            elif bucket == "day":
                return func.strftime("%Y-%m-%d 00:00:00", field)
            elif bucket == "week":
                # Basic approximation for sqlite week
                return func.strftime("%Y-%W", field)
            else:
                return func.strftime("%Y-%m-%d %H:00:00", field)
        else:
            return func.date_trunc(bucket, field)

    @staticmethod
    def determine_bucket(start_date: datetime, end_date: datetime) -> str:
        diff_hours = (end_date - start_date).total_seconds() / 3600
        if diff_hours <= 1:
            return "minute"
        elif diff_hours <= 24:
            return "hour"
        elif diff_hours <= 24 * 30:
            return "day"
        else:
            return "week"

    @staticmethod
    def build_event_filters(filters: ReportFilters):
        conditions = [
            SecurityEvent.timestamp >= filters.start_date,
            SecurityEvent.timestamp <= filters.end_date
        ]
        if filters.application_id:
            conditions.append(SecurityEvent.application_id == filters.application_id)
        if filters.severity:
            conditions.append(SecurityEvent.severity == filters.severity)
        return and_(*conditions)
        
    @staticmethod
    def build_alert_filters(filters: ReportFilters):
        conditions = [
            Alert.detected_at >= filters.start_date,
            Alert.detected_at <= filters.end_date
        ]
        if filters.application_id:
            conditions.append(Alert.application_id == filters.application_id)
        if filters.severity:
            conditions.append(Alert.severity == filters.severity)
        return and_(*conditions)

    @staticmethod
    def build_incident_filters(filters: ReportFilters):
        conditions = [
            Incident.detected_at >= filters.start_date,
            Incident.detected_at <= filters.end_date
        ]
        if filters.application_id:
            conditions.append(Incident.application_id == filters.application_id)
        if filters.severity:
            conditions.append(Incident.severity == filters.severity)
        return and_(*conditions)

    @staticmethod
    def build_action_filters(filters: ReportFilters):
        conditions = [
            ResponseAction.created_at >= filters.start_date,
            ResponseAction.created_at <= filters.end_date
        ]
        if filters.application_id:
            conditions.append(ResponseAction.application_id == filters.application_id)
        # Severity doesn't directly map to response action
        return and_(*conditions)

    @staticmethod
    def get_event_trend(db: Session, filters: ReportFilters) -> List[Dict[str, Any]]:
        bucket = ReportQueryService.determine_bucket(filters.start_date, filters.end_date)
        trunc_expr = ReportQueryService.get_date_trunc_expr(db, SecurityEvent.timestamp, bucket)
        
        rows = db.query(
            trunc_expr.label('ts'),
            func.count(SecurityEvent.id)
        ).filter(ReportQueryService.build_event_filters(filters)).group_by('ts').order_by('ts').all()
        
        return [{"timestamp": r[0], "count": r[1]} for r in rows if r[0]]

    @staticmethod
    def get_alert_trend(db: Session, filters: ReportFilters) -> List[Dict[str, Any]]:
        bucket = ReportQueryService.determine_bucket(filters.start_date, filters.end_date)
        trunc_expr = ReportQueryService.get_date_trunc_expr(db, Alert.detected_at, bucket)
        
        rows = db.query(
            trunc_expr.label('ts'),
            func.count(Alert.id)
        ).filter(ReportQueryService.build_alert_filters(filters)).group_by('ts').order_by('ts').all()
        
        return [{"timestamp": r[0], "count": r[1]} for r in rows if r[0]]

    @staticmethod
    def get_incident_trend(db: Session, filters: ReportFilters) -> List[Dict[str, Any]]:
        bucket = ReportQueryService.determine_bucket(filters.start_date, filters.end_date)
        trunc_expr = ReportQueryService.get_date_trunc_expr(db, Incident.detected_at, bucket)
        
        rows = db.query(
            trunc_expr.label('ts'),
            func.count(Incident.id)
        ).filter(ReportQueryService.build_incident_filters(filters)).group_by('ts').order_by('ts').all()
        
        return [{"timestamp": r[0], "count": r[1]} for r in rows if r[0]]
