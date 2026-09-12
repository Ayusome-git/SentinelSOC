from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import timedelta
from typing import Any
from app.models.application import Application
from app.models.alert import Alert
from app.models.correlation import Correlation, correlation_events, correlation_alerts
from app.models.security_event import SecurityEvent

SEVERITY_BASE = {
    "INFO": 10,
    "LOW": 25,
    "MEDIUM": 40,
    "HIGH": 65,
    "CRITICAL": 80,
}

ATTACK_TYPE_WEIGHTS = {
    "Authentication Abuse": 5,
    "Authorization Abuse": 7,
    "API Abuse": 5,
    "Privilege Abuse": 10,
    "Path Traversal": 10,
    "SQL Injection Indicator": 10,
    "XSS Indicator": 10,
    "Credential Stuffing": 8,
    "Password Spray": 8,
    "Brute Force": 7,
    "Brute Force Login": 7,
    "SQL Injection Detected": 10,
}

class BaseSeverityFactor:
    @staticmethod
    def calculate(entity: Any) -> int:
        return SEVERITY_BASE.get(entity.severity.upper(), 0)

class AttackTypeFactor:
    @staticmethod
    def calculate_for_alert(db: Session, alert: Alert) -> int:
        return ATTACK_TYPE_WEIGHTS.get(alert.title, 0)
        
    @staticmethod
    def calculate_for_correlation(db: Session, correlation: Correlation) -> int:
        score = 0
        
        # Check rule name
        for keyword, weight in ATTACK_TYPE_WEIGHTS.items():
            if keyword.lower() in correlation.name.lower():
                score = max(score, weight)
                
        # Also check underlying alerts
        alerts_query = db.query(Alert).join(
            correlation_alerts, correlation_alerts.c.alert_id == Alert.id
        ).filter(correlation_alerts.c.correlation_id == correlation.id).all()
        
        for al in alerts_query:
            score = max(score, ATTACK_TYPE_WEIGHTS.get(al.title, 0))
            
        return score

class FrequencyFactor:
    @staticmethod
    def _calculate_score(count: int) -> int:
        if count <= 1: return 0
        if count <= 4: return 3
        if count <= 9: return 7
        if count <= 19: return 12
        return 15

    @staticmethod
    def calculate_for_alert(db: Session, alert: Alert) -> int:
        # Number of similar alerts in the last 15 mins
        window_start = alert.detected_at - timedelta(minutes=15)
        stmt = select(Alert).where(
            and_(
                Alert.application_id == alert.application_id,
                Alert.title == alert.title,
                Alert.detected_at >= window_start,
                Alert.detected_at <= alert.detected_at
            )
        )
        count = len(db.execute(stmt).scalars().all())
        return FrequencyFactor._calculate_score(count)

    @staticmethod
    def calculate_for_correlation(db: Session, correlation: Correlation) -> int:
        # A simple proxy: total number of underlying events + alerts
        events_count = db.query(correlation_events).filter(correlation_events.c.correlation_id == correlation.id).count()
        alerts_count = db.query(correlation_alerts).filter(correlation_alerts.c.correlation_id == correlation.id).count()
        
        return FrequencyFactor._calculate_score(events_count + alerts_count)

class AuthenticationContextFactor:
    @staticmethod
    def calculate_for_alert(db: Session, alert: Alert) -> int:
        if "login" in alert.title.lower():
            return 2
        return 0

    @staticmethod
    def calculate_for_correlation(db: Session, correlation: Correlation) -> int:
        score = 0
        events_query = db.query(SecurityEvent).join(
            correlation_events, correlation_events.c.security_event_id == SecurityEvent.id
        ).filter(correlation_events.c.correlation_id == correlation.id).all()
        
        event_types = [ev.event_type for ev in events_query]
        
        has_fail = any("FAIL" in et for et in event_types)
        has_success = any("SUCCESS" in et for et in event_types)
        has_brute = "brute" in correlation.name.lower()
        
        if has_brute and has_success:
            return 15
        if has_fail and has_success:
            return 10
        if has_fail or has_success:
            return 5
            
        return score

class PrivilegeContextFactor:
    @staticmethod
    def calculate_for_alert(db: Session, alert: Alert) -> int:
        score = 0
        if alert.security_event:
            if alert.security_event.event_type == "ADMIN_LOGIN":
                score = 5
            elif alert.security_event.event_type == "ADMIN_ACTION":
                score = 10
        return score

    @staticmethod
    def calculate_for_correlation(db: Session, correlation: Correlation) -> int:
        score = 0
        events_query = db.query(SecurityEvent).join(
            correlation_events, correlation_events.c.security_event_id == SecurityEvent.id
        ).filter(correlation_events.c.correlation_id == correlation.id).all()
        
        for ev in events_query:
            if ev.event_type == "ADMIN_LOGIN":
                score = max(score, 5)
            elif ev.event_type == "ADMIN_ACTION":
                score = max(score, 10)
        return score

class CorrelationStrengthFactor:
    @staticmethod
    def calculate(correlation: Correlation) -> int:
        # A correlation result intrinsically implies multiple stages
        # Let's count stages as the number of items in the sequence
        # Actually, we can count total evidence
        events_count = len(correlation.events) if correlation.events else 0
        alerts_count = len(correlation.alerts_evidence) if correlation.alerts_evidence else 0
        total = events_count + alerts_count
        
        if total <= 1: return 0
        if total == 2: return 10
        if total == 3: return 15
        return 20

class ApplicationContextFactor:
    @staticmethod
    def calculate(application: Application) -> int:
        if not application:
            return 0
        env = application.environment.lower() if application.environment else ""
        if env == "production" or env == "prod":
            return 5
        if env == "staging" or env == "stage":
            return 2
        return 0

class RepeatedActivityFactor:
    @staticmethod
    def _calculate_score(count: int) -> int:
        if count <= 1: return 0
        if count == 2: return 5
        if count == 3: return 8
        return 12

    @staticmethod
    def calculate_for_alert(db: Session, alert: Alert) -> int:
        # Repeated alerts for the same user or IP within 30 mins
        window_start = alert.detected_at - timedelta(minutes=30)
        ev = alert.security_event
        if not ev:
            return 0
            
        conds = [
            Alert.application_id == alert.application_id,
            Alert.id != alert.id,
            Alert.detected_at >= window_start,
            Alert.detected_at <= alert.detected_at
        ]
        
        # Need to join SecurityEvent to check user or IP
        stmt = select(Alert).join(SecurityEvent, Alert.security_event_id == SecurityEvent.id).where(and_(*conds))
        
        user_or_ip_conds = []
        if ev.user_id: user_or_ip_conds.append(SecurityEvent.user_id == ev.user_id)
        if ev.source_ip: user_or_ip_conds.append(SecurityEvent.source_ip == ev.source_ip)
        
        if not user_or_ip_conds:
            return 0
            
        stmt = stmt.where(and_(*user_or_ip_conds))
        count = len(db.execute(stmt).scalars().all())
        
        return RepeatedActivityFactor._calculate_score(count + 1)

    @staticmethod
    def calculate_for_correlation(db: Session, correlation: Correlation) -> int:
        # Repeated correlations for same rule & app within 30 mins
        window_start = correlation.last_event_at - timedelta(minutes=30)
        stmt = select(Correlation).where(
            and_(
                Correlation.application_id == correlation.application_id,
                Correlation.rule_id == correlation.rule_id,
                Correlation.last_event_at >= window_start,
                Correlation.last_event_at <= correlation.last_event_at
            )
        )
        count = len(db.execute(stmt).scalars().all())
        return RepeatedActivityFactor._calculate_score(count)
