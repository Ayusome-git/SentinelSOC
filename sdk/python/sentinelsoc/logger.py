import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class SentinelLogger:
    def __init__(self, api_key: str, endpoint: str = "http://localhost:8000"):
        self.api_key = api_key
        # Strip trailing slash
        self.endpoint = endpoint.rstrip("/")
        self.events_url = f"{self.endpoint}/api/v1/events"
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})

    def log(
        self,
        event_type: str,
        severity: str,
        source_ip: str,
        message: str,
        timestamp: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        http_method: Optional[str] = None,
        request_path: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> bool:
        """
        Log a security event to SentinelSOC.
        """
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
            
        payload = {
            "event_type": event_type,
            "severity": severity,
            "source_ip": source_ip,
            "message": message,
            "timestamp": timestamp,
        }
        
        # Add optional fields if provided
        if user_id: payload["user_id"] = user_id
        if username: payload["username"] = username
        if session_id: payload["session_id"] = session_id
        if request_id: payload["request_id"] = request_id
        if http_method: payload["http_method"] = http_method
        if request_path: payload["request_path"] = request_path
        if user_agent: payload["user_agent"] = user_agent
        if metadata: payload["metadata"] = metadata

        for attempt in range(max_retries):
            try:
                response = self.session.post(self.events_url, json=payload, timeout=5)
                if response.status_code == 201:
                    return True
                elif response.status_code == 409:
                    # Duplicate
                    return True
                elif response.status_code in (401, 422):
                    # Bad request or auth, don't retry
                    print(f"SentinelSOC logging failed: {response.status_code} - {response.text}")
                    return False
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"SentinelSOC logging failed after {max_retries} attempts: {e}")
                    return False
                time.sleep(0.5 * (2 ** attempt)) # Exponential backoff
        
        return False
