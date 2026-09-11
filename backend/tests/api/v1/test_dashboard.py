import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

from app.main import app
from app.models.user import UserRole
from app.core.config import settings
from tests.api.v1.test_applications import _create_user, _auth_header, _create_application

client = TestClient(app)

def test_dashboard_overview_unauthorized(db_session):
    resp = client.get(f"{settings.API_V1_STR}/dashboard/overview")
    assert resp.status_code == 401

def test_dashboard_overview_success(db_session):
    admin, _ = _create_user(db_session, email="dash@events.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Dash App", slug="dash-app", owner_id=admin.id)
    
    # Generate API key
    key_resp = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "Dash Key"}
    )
    api_key = key_resp.json()["api_key"]
    
    # Ingest some events
    for _ in range(3):
        client.post(
            f"{settings.API_V1_STR}/events",
            headers={"X-API-Key": api_key},
            json={
                "event_type": "LOGIN_FAILED",
                "severity": "HIGH",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_ip": "1.1.1.1",
                "message": "Fail"
            }
        )
        
    client.post(
        f"{settings.API_V1_STR}/events",
        headers={"X-API-Key": api_key},
        json={
            "event_type": "LOGIN_SUCCESS",
            "severity": "INFO",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "1.1.1.1",
            "message": "Success"
        }
    )
    
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=24)
    start_str = start.isoformat().replace("+", "%2B")
    end_str = end.isoformat().replace("+", "%2B")
    
    resp = client.get(
        f"{settings.API_V1_STR}/dashboard/overview?start_date={start_str}&end_date={end_str}", 
        headers=_auth_header(admin)
    )
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["total_events"] >= 4
    assert data["high_events"] >= 3
    assert data["active_applications"] >= 1
    assert "LOGIN_FAILED" in data["event_type_distribution"]
    assert "HIGH" in data["severity_distribution"]
    assert len(data["recent_events"]) >= 4
    
    recent_event = data["recent_events"][0]
    assert recent_event["application_name"] == "Dash App"

def test_dashboard_90_days_limit(db_session):
    admin, _ = _create_user(db_session, email="dash_limit@events.com", role=UserRole.ADMIN)
    
    start = datetime.now(timezone.utc) - timedelta(days=100)
    end = datetime.now(timezone.utc)
    start_str = start.isoformat().replace("+", "%2B")
    end_str = end.isoformat().replace("+", "%2B")
    
    resp = client.get(
        f"{settings.API_V1_STR}/dashboard/overview?start_date={start_str}&end_date={end_str}", 
        headers=_auth_header(admin)
    )
    assert resp.status_code == 400
    assert "90 days" in resp.json()["detail"]
