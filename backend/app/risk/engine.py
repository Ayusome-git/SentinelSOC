from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.correlation import Correlation
from app.risk.factors import (
    BaseSeverityFactor,
    AttackTypeFactor,
    FrequencyFactor,
    AuthenticationContextFactor,
    PrivilegeContextFactor,
    CorrelationStrengthFactor,
    ApplicationContextFactor,
    RepeatedActivityFactor,
    MLAnomalyFactor
)

class RiskScoreResult:
    def __init__(self, score: int, level: str, factors: Dict[str, Any]):
        self.score = score
        self.level = level
        self.factors = factors

class RiskScoringEngine:
    @staticmethod
    def get_risk_level(score: int) -> str:
        """Map a numeric risk score (0-100) to a risk level."""
        if score < 25:
            return "LOW"
        elif score < 50:
            return "MODERATE"
        elif score < 75:
            return "HIGH"
        else:
            return "CRITICAL"

    @staticmethod
    def _clamp_score(score: int) -> int:
        return max(0, min(100, score))

    @staticmethod
    def calculate_alert_score(db: Session, alert: Alert) -> RiskScoreResult:
        factors = {}
        total_score = 0
        
        # 1. Base Severity
        base_sev = BaseSeverityFactor.calculate(alert)
        factors["base_severity"] = base_sev
        total_score += base_sev
        
        # 2. Attack Type
        attack_type = AttackTypeFactor.calculate_for_alert(db, alert)
        factors["attack_type"] = attack_type
        total_score += attack_type
        
        # 3. Frequency
        frequency = FrequencyFactor.calculate_for_alert(db, alert)
        factors["frequency"] = frequency
        total_score += frequency
        
        # 4. Authentication Context
        auth_context = AuthenticationContextFactor.calculate_for_alert(db, alert)
        factors["authentication"] = auth_context
        total_score += auth_context
        
        # 5. Privilege Context
        privilege = PrivilegeContextFactor.calculate_for_alert(db, alert)
        factors["privilege"] = privilege
        total_score += privilege
        
        # 6. Correlation Strength
        factors["correlation"] = 0 # Alerts intrinsically have 0 correlation bonus unless part of a sequence
        
        # 7. Application Context
        app_context = ApplicationContextFactor.calculate(alert.application)
        factors["application"] = app_context
        total_score += app_context
        
        # 8. Repeated Activity
        repeated = RepeatedActivityFactor.calculate_for_alert(db, alert)
        factors["repeated_activity"] = repeated
        total_score += repeated

        # 9. ML Anomaly 
        ml_anomaly = MLAnomalyFactor.calculate_for_alert(alert)
        factors["ml_anomaly_strength"] = ml_anomaly
        total_score += ml_anomaly
        
        final_score = RiskScoringEngine._clamp_score(total_score)
        level = RiskScoringEngine.get_risk_level(final_score)
        
        return RiskScoreResult(score=final_score, level=level, factors=factors)

    @staticmethod
    def calculate_correlation_score(db: Session, correlation: Correlation) -> RiskScoreResult:
        factors = {}
        total_score = 0
        
        # 1. Base Severity
        base_sev = BaseSeverityFactor.calculate(correlation)
        factors["base_severity"] = base_sev
        total_score += base_sev
        
        # 2. Attack Type
        attack_type = AttackTypeFactor.calculate_for_correlation(db, correlation)
        factors["attack_type"] = attack_type
        total_score += attack_type
        
        # 3. Frequency
        frequency = FrequencyFactor.calculate_for_correlation(db, correlation)
        factors["frequency"] = frequency
        total_score += frequency
        
        # 4. Authentication Context
        auth_context = AuthenticationContextFactor.calculate_for_correlation(db, correlation)
        factors["authentication"] = auth_context
        total_score += auth_context
        
        # 5. Privilege Context
        privilege = PrivilegeContextFactor.calculate_for_correlation(db, correlation)
        factors["privilege"] = privilege
        total_score += privilege
        
        # 6. Correlation Strength
        corr_strength = CorrelationStrengthFactor.calculate(correlation)
        factors["correlation"] = corr_strength
        total_score += corr_strength
        
        # 7. Application Context
        app_context = ApplicationContextFactor.calculate(correlation.application)
        factors["application"] = app_context
        total_score += app_context
        
        # 8. Repeated Activity
        repeated = RepeatedActivityFactor.calculate_for_correlation(db, correlation)
        factors["repeated_activity"] = repeated
        total_score += repeated
        
        final_score = RiskScoringEngine._clamp_score(total_score)
        level = RiskScoringEngine.get_risk_level(final_score)
        
        return RiskScoreResult(score=final_score, level=level, factors=factors)
