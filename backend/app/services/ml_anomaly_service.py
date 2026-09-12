import os
import uuid
import joblib
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ml_model import MLModel, MLModelStatus
from app.models.alert import Alert, AlertStatus, DetectionSource
from app.services.ml_feature_service import FeatureExtractionService
from app.risk.service import RiskScoringService

class MLDetectionResult:
    def __init__(self, is_anomaly: bool, anomaly_score: int, model_id: str, feature_version: str, feature_values: Dict[str, float], explanation: str):
        self.is_anomaly = is_anomaly
        self.anomaly_score = anomaly_score
        self.model_id = model_id
        self.feature_version = feature_version
        self.feature_values = feature_values
        self.explanation = explanation

class MLAnomalyDetectionService:

    @staticmethod
    def _normalize_score(raw_score: float) -> int:
        """
        Converts Isolation Forest decision_function score to a 0-100 anomaly strength.
        decision_function typically returns negative values for anomalies, positive for normal.
        Lower values = more anomalous.
        Let's map it:
        -0.5 and below -> 100
        0.0 -> 50
        0.5 and above -> 0
        """
        # Map raw_score from [-0.5, 0.5] to [100, 0]
        # score = 50 - (raw_score * 100)
        # Clamped to [0, 100]
        val = 50 - (raw_score * 100)
        return int(max(0, min(100, val)))

    @staticmethod
    def _generate_explanation(features: Dict[str, float], baseline: Dict[str, dict]) -> str:
        """
        Generates deterministic explanation comparing features to baseline.
        """
        explanations = []
        for name, value in features.items():
            base = baseline.get(name, {})
            mean = base.get("mean", 0.0)
            if mean > 0 and value > mean:
                ratio = value / mean
                if ratio >= 2.0:
                    explanations.append(f"{name.replace('_', ' ').title()}: {ratio:.1f}× baseline")
            elif mean == 0 and value > 0:
                explanations.append(f"{name.replace('_', ' ').title()}: {value} (baseline is 0)")
                
        if not explanations:
            return "Multiple features slightly deviated from the baseline."
            
        return "Compared with the learned baseline:\n" + "\n".join(explanations)

    @classmethod
    def evaluate_window(
        cls, 
        db: Session, 
        application_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[MLDetectionResult]:
        """
        Evaluates a specific time window for an application using the active ML model.
        Returns MLDetectionResult if evaluated, None if no model is available.
        """
        if not settings.ML_ENABLED:
            return None

        # 1. Retrieve appropriate model
        model = db.query(MLModel).filter(
            MLModel.application_id == application_id,
            MLModel.status == MLModelStatus.ACTIVE.value,
            MLModel.feature_version == FeatureExtractionService.FEATURE_VERSION
        ).first()
        
        # Fallback to global model
        if not model:
            model = db.query(MLModel).filter(
                MLModel.application_id.is_(None),
                MLModel.status == MLModelStatus.ACTIVE.value,
                MLModel.feature_version == FeatureExtractionService.FEATURE_VERSION
            ).first()
            
        if not model or not model.model_path or not os.path.exists(model.model_path):
            return None # Cold start / No model available
            
        # 2. Load Model
        try:
            clf = joblib.load(model.model_path)
        except Exception as e:
            print(f"Failed to load ML model {model.id}: {e}")
            return None
            
        # 3. Extract Features
        features = FeatureExtractionService.extract_single_window(db, application_id, start_time, end_time)
        vector = FeatureExtractionService.dict_to_vector(features)
        
        # 4. Generate Score
        X = np.array([vector])
        raw_score = clf.decision_function(X)[0] # e.g. -0.2 for anomaly, +0.1 for normal
        
        normalized_score = cls._normalize_score(float(raw_score))
        is_anomaly = normalized_score >= settings.ML_ANOMALY_THRESHOLD
        
        explanation = "No significant anomaly."
        if is_anomaly:
            explanation = cls._generate_explanation(features, model.baseline_statistics or {})
            
        return MLDetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=normalized_score,
            model_id=str(model.id),
            feature_version=model.feature_version,
            feature_values=features,
            explanation=explanation
        )

    @classmethod
    def trigger_detection_for_latest_window(cls, db: Session, application_id: uuid.UUID) -> None:
        """
        Calculates the most recently completed 5-minute window and runs anomaly detection.
        If an anomaly is found, it creates an Alert (handling deduplication).
        """
        if not settings.ML_ENABLED:
            return

        now = datetime.now(timezone.utc)
        now_epoch = int(now.timestamp())
        window_sec = settings.ML_WINDOW_SECONDS
        
        # Current bucket start
        current_bucket = now_epoch - (now_epoch % window_sec)
        
        # We want the MOST RECENTLY COMPLETED bucket
        prev_bucket_start = current_bucket - window_sec
        prev_bucket_end = current_bucket
        
        start_dt = datetime.fromtimestamp(prev_bucket_start, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(prev_bucket_end, tz=timezone.utc)
        
        result = cls.evaluate_window(db, application_id, start_dt, end_dt)
        if not result or not result.is_anomaly:
            return
            
        # 5. Handle Alert Creation and Duplicate Suppression
        # Check if there is already an open/ack ML alert for this app
        existing_alert = db.query(Alert).filter(
            Alert.application_id == application_id,
            Alert.detection_source == DetectionSource.ML.value,
            Alert.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])
        ).first()
        
        if existing_alert:
            # Duplicate suppression: do not create another
            return
            
        desc = f"Machine-learning analysis detected behavior significantly different from the learned baseline.\n\n"
        desc += f"Anomaly Score: {result.anomaly_score} / 100\n\n"
        desc += f"Why was this anomalous?\n{result.explanation}"

        alert = Alert(
            application_id=application_id,
            title="Unusual Application Behavior Detected",
            description=desc,
            severity="HIGH",
            status=AlertStatus.OPEN.value,
            detection_source=DetectionSource.ML.value,
            detected_at=datetime.now(timezone.utc)
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        # 6. Risk Scoring Integration
        RiskScoringService.recalculate_alert(db, alert.id)
