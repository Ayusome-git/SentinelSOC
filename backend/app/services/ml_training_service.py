import os
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sklearn.ensemble import IsolationForest
import numpy as np
import joblib

from app.core.config import settings
from app.models.ml_model import MLModel, MLModelStatus
from app.models.audit_log import AuditLog
from app.services.ml_feature_service import FeatureExtractionService

class MLTrainingService:

    @staticmethod
    def _ensure_model_directory():
        if not os.path.exists(settings.ML_MODEL_DIRECTORY):
            os.makedirs(settings.ML_MODEL_DIRECTORY)

    @staticmethod
    def train_model(
        db: Session, 
        application_id: Optional[uuid.UUID], 
        training_days: int, 
        user_id: Optional[uuid.UUID] = None
    ) -> MLModel:
        """
        Trains an Isolation Forest model for the given application (or globally)
        over the specified historical window.
        """
        cls = MLTrainingService
        cls._ensure_model_directory()
        
        # 1. Determine Training Window
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=training_days)
        
        model_name = f"IForest_{'Global' if not application_id else str(application_id)[:8]}_{end_time.strftime('%Y%m%d%H%M')}"
        
        # Create DB record in TRAINING status
        db_model = MLModel(
            name=model_name,
            model_type="ISOLATION_FOREST",
            feature_version=FeatureExtractionService.FEATURE_VERSION,
            application_id=application_id,
            status=MLModelStatus.TRAINING.value,
            training_window_start=start_time,
            training_window_end=end_time,
            parameters={
                "n_estimators": settings.ML_N_ESTIMATORS,
                "random_state": settings.ML_RANDOM_STATE,
                "contamination": "auto",
                "window_seconds": settings.ML_WINDOW_SECONDS
            }
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        # Audit Log Start
        if user_id:
            audit = AuditLog(
                user_id=user_id,
                application_id=application_id,
                action="ML_MODEL_TRAINING_STARTED",
                resource_type="ML_MODEL",
                resource_id=str(db_model.id),
                details={"training_days": training_days}
            )
            db.add(audit)
            db.commit()

        try:
            # 2. Extract Features
            windows = FeatureExtractionService.get_feature_windows(
                db=db,
                application_id=application_id,
                start_time=start_time,
                end_time=end_time,
                window_seconds=settings.ML_WINDOW_SECONDS
            )
            
            # 3. Check Minimum Samples
            if len(windows) < settings.ML_MIN_TRAINING_SAMPLES:
                raise ValueError(f"Insufficient training data. Found {len(windows)} windows, require {settings.ML_MIN_TRAINING_SAMPLES}.")

            # Prepare data
            X_train = []
            features_list = []
            for w in windows:
                vec = FeatureExtractionService.dict_to_vector(w["features"])
                X_train.append(vec)
                features_list.append(w["features"])
                
            X_np = np.array(X_train)
            
            # 4. Calculate Baseline Statistics
            baseline_stats = {}
            for i, feat_name in enumerate(FeatureExtractionService.FEATURE_NAMES):
                col = X_np[:, i]
                baseline_stats[feat_name] = {
                    "mean": float(np.mean(col)),
                    "std": float(np.std(col)),
                    "min": float(np.min(col)),
                    "max": float(np.max(col))
                }

            # 5. Train Model
            clf = IsolationForest(
                n_estimators=settings.ML_N_ESTIMATORS,
                contamination="auto",
                random_state=settings.ML_RANDOM_STATE
            )
            clf.fit(X_np)
            
            # 6. Save Model to Disk
            model_filename = f"{db_model.id}.joblib"
            model_path = os.path.join(settings.ML_MODEL_DIRECTORY, model_filename)
            joblib.dump(clf, model_path)
            
            # 7. Update Metadata and Activate
            db_model.status = MLModelStatus.ACTIVE.value
            db_model.trained_at = datetime.now(timezone.utc)
            db_model.training_sample_count = len(windows)
            db_model.baseline_statistics = baseline_stats
            db_model.model_path = model_path
            
            # Deactivate previous active models for this scope
            old_models = db.query(MLModel).filter(
                MLModel.application_id == application_id,
                MLModel.feature_version == FeatureExtractionService.FEATURE_VERSION,
                MLModel.status == MLModelStatus.ACTIVE.value,
                MLModel.id != db_model.id
            ).all()
            for old_m in old_models:
                old_m.status = MLModelStatus.INACTIVE.value
                
            db.commit()
            db.refresh(db_model)
            
            # Audit Log Success
            if user_id:
                audit = AuditLog(
                    user_id=user_id,
                    application_id=application_id,
                    action="ML_MODEL_TRAINED",
                    resource_type="ML_MODEL",
                    resource_id=str(db_model.id),
                    details={"samples": len(windows)}
                )
                db.add(audit)
                db.commit()
                
            return db_model

        except Exception as e:
            # Handle Failure
            db.rollback()
            db_model.status = MLModelStatus.FAILED.value
            
            # Try to save error reason in parameters or audit log
            db_model.parameters = {**(db_model.parameters or {}), "error": str(e)}
            db.add(db_model)
            db.commit()
            
            if user_id:
                audit = AuditLog(
                    user_id=user_id,
                    application_id=application_id,
                    action="ML_MODEL_TRAINING_FAILED",
                    resource_type="ML_MODEL",
                    resource_id=str(db_model.id),
                    details={"error": str(e)}
                )
                db.add(audit)
                db.commit()
            
            # We don't raise here, we just return the failed model record
            return db_model
