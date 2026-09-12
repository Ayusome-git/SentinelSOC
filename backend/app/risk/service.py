import logging
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.correlation import Correlation
from app.risk.engine import RiskScoringEngine

logger = logging.getLogger(__name__)

class RiskScoringService:
    @staticmethod
    def recalculate_alert(db: Session, alert_id: UUID) -> None:
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return
                
            result = RiskScoringEngine.calculate_alert_score(db, alert)
            
            alert.risk_score = result.score
            alert.risk_level = result.level
            alert.risk_factors = result.factors
            
            db.commit()
        except Exception as e:
            logger.error(f"Error recalculating risk for alert {alert_id}: {str(e)}")
            db.rollback()

    @staticmethod
    def recalculate_correlation(db: Session, correlation_id: UUID) -> None:
        try:
            correlation = db.query(Correlation).filter(Correlation.id == correlation_id).first()
            if not correlation:
                return
                
            result = RiskScoringEngine.calculate_correlation_score(db, correlation)
            
            correlation.risk_score = result.score
            correlation.risk_level = result.level
            correlation.risk_factors = result.factors
            
            # If the correlation generated an alert, update its risk score too
            if correlation.alert:
                alert_result = RiskScoringEngine.calculate_alert_score(db, correlation.alert)
                # But wait, the alert's risk score should reflect the correlation's risk score
                # since the alert is just a wrapper for the correlation
                correlation.alert.risk_score = result.score
                correlation.alert.risk_level = result.level
                correlation.alert.risk_factors = result.factors
            
            db.commit()
        except Exception as e:
            logger.error(f"Error recalculating risk for correlation {correlation_id}: {str(e)}")
            db.rollback()
