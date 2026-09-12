from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from app.models.security_event import SecurityEvent

class FeatureExtractionService:
    FEATURE_VERSION = "v1"
    
    # Define exact feature order for deterministic vector creation
    FEATURE_NAMES = [
        "event_count",
        "login_failed_count",
        "login_success_count",
        "api_request_count",
        "api_error_count",
        "admin_action_count",
        "suspicious_request_count",
        "unique_source_ips",
        "unique_users",
        "unique_request_paths",
        "error_ratio",
        "failed_login_ratio",
        "admin_action_ratio"
    ]

    @classmethod
    def get_feature_windows(
        cls, 
        db: Session, 
        application_id: uuid.UUID, 
        start_time: datetime, 
        end_time: datetime, 
        window_seconds: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Groups events into time windows and calculates feature vectors.
        Returns a list of dictionaries with window timestamps and extracted features.
        """
        # This could be highly optimized with PostgreSQL time_bucket or group by window.
        # But for DB agnosticism and simplicity in SQLAlchemy without specific dialect extensions,
        # we will fetch all events and group them in memory, or do simple groupings.
        # Since this might be large, we yield/group by integer intervals.
        
        # Calculate epoch bounds
        start_epoch = int(start_time.timestamp())
        end_epoch = int(end_time.timestamp())
        
        # To avoid loading everything into memory, we group by SQL expressions
        # SQLite doesn't support complex date_trunc natively without plugins, but Postgres does.
        # However, the prompt asks for PostgeSQL aggregation if possible.
        
        # We will use Postgres FLOOR(EXTRACT(EPOCH FROM timestamp) / window_seconds)
        # For simplicity and robust DB support, let's query raw events ordered by timestamp.
        
        events = db.query(SecurityEvent).filter(
            SecurityEvent.application_id == application_id,
            SecurityEvent.timestamp >= start_time,
            SecurityEvent.timestamp < end_time
        ).order_by(SecurityEvent.timestamp.asc()).all()
        
        windows = {}
        
        # Build empty windows to ensure continuous timeline or just populate sparse ones?
        # The prompt says: "Zero-event windows: Use safe defaults. error_ratio=0 when zero events."
        # If we only emit windows that have events, Isolation Forest might miss the fact that "0 events" is normal.
        # Let's populate the time range with empty windows first.
        current_ts = start_epoch
        while current_ts < end_epoch:
            windows[current_ts] = {
                "events": []
            }
            current_ts += window_seconds
            
        for event in events:
            ev_ts = int(event.timestamp.timestamp())
            window_bucket = ev_ts - (ev_ts % window_seconds)
            if window_bucket in windows:
                windows[window_bucket]["events"].append(event)
                
        # Extract features for each window
        feature_windows = []
        for bucket, data in windows.items():
            features = cls._extract_features_for_window(data["events"])
            
            # Format window timestamp
            window_start = datetime.fromtimestamp(bucket)
            window_end = datetime.fromtimestamp(bucket + window_seconds)
            
            feature_windows.append({
                "window_start": window_start,
                "window_end": window_end,
                "features": features
            })
            
        return feature_windows

    @classmethod
    def extract_single_window(cls, db: Session, application_id: uuid.UUID, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """
        Extracts features for exactly one specific window.
        """
        events = db.query(SecurityEvent).filter(
            SecurityEvent.application_id == application_id,
            SecurityEvent.timestamp >= start_time,
            SecurityEvent.timestamp < end_time
        ).all()
        
        return cls._extract_features_for_window(events)

    @classmethod
    def _extract_features_for_window(cls, events: List[SecurityEvent]) -> Dict[str, float]:
        """
        Calculates raw numerical features from a list of events.
        """
        event_count = len(events)
        login_failed_count = 0
        login_success_count = 0
        api_request_count = 0
        api_error_count = 0
        admin_action_count = 0
        suspicious_request_count = 0
        
        unique_ips = set()
        unique_users = set()
        unique_paths = set()
        
        for event in events:
            ev_type = event.event_type
            
            if ev_type == "LOGIN_FAILED":
                login_failed_count += 1
            elif ev_type == "LOGIN_SUCCESS":
                login_success_count += 1
            elif ev_type == "API_REQUEST":
                api_request_count += 1
            elif ev_type == "API_ERROR":
                api_error_count += 1
            elif ev_type == "ADMIN_ACTION":
                admin_action_count += 1
            elif ev_type == "SUSPICIOUS_REQUEST":
                suspicious_request_count += 1
                
            if event.source_ip:
                unique_ips.add(event.source_ip)
            
            if event.details:
                username = event.details.get("username")
                if username:
                    unique_users.add(username)
                path = event.details.get("request_path")
                if path:
                    unique_paths.add(path)
                    
        # Ratios (safe division)
        error_ratio = api_error_count / event_count if event_count > 0 else 0.0
        
        total_logins = login_success_count + login_failed_count
        failed_login_ratio = login_failed_count / total_logins if total_logins > 0 else 0.0
        
        admin_action_ratio = admin_action_count / event_count if event_count > 0 else 0.0

        return {
            "event_count": float(event_count),
            "login_failed_count": float(login_failed_count),
            "login_success_count": float(login_success_count),
            "api_request_count": float(api_request_count),
            "api_error_count": float(api_error_count),
            "admin_action_count": float(admin_action_count),
            "suspicious_request_count": float(suspicious_request_count),
            "unique_source_ips": float(len(unique_ips)),
            "unique_users": float(len(unique_users)),
            "unique_request_paths": float(len(unique_paths)),
            "error_ratio": float(error_ratio),
            "failed_login_ratio": float(failed_login_ratio),
            "admin_action_ratio": float(admin_action_ratio)
        }

    @classmethod
    def dict_to_vector(cls, features: Dict[str, float]) -> List[float]:
        """
        Converts a feature dictionary into an ordered list matching FEATURE_NAMES.
        """
        return [features.get(name, 0.0) for name in cls.FEATURE_NAMES]
