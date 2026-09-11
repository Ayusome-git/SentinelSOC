import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import UserRole
from app.models.security_event import SecurityEvent
from tests.api.v1.test_applications import _create_user, _auth_header, _create_application
from app.core.config import settings
from datetime import datetime, timezone, timedelta

client = TestClient(app)

def test_ingest_event_success(db_session):
    admin, _ = _create_user(db_session, email="admin@events.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Test App", slug="events-app", owner_id=admin.id)
    
    # Generate API key
    key_resp = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "Ingestion Key"}
    )
    api_key = key_resp.json()["api_key"]
    
    # Ingest Event
    event_payload = {
        "event_type": "LOGIN_FAILED",
        "severity": "MEDIUM",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": "192.168.1.100",
        "message": "Failed login attempt",
        "metadata": {"reason": "bad_password"}
    }
    
    resp = client.post(
        f"{settings.API_V1_STR}/events",
        headers={"X-API-Key": api_key},
        json=event_payload
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "event_id" in data
    assert data["status"] == "accepted"
    
    # Verify in DB
    import uuid
    event_in_db = db_session.query(SecurityEvent).filter(SecurityEvent.id == uuid.UUID(data["event_id"])).first()
    assert event_in_db is not None
    assert event_in_db.event_type == "LOGIN_FAILED"
    assert event_in_db.metadata_ == {"reason": "bad_password"}

def test_ingest_event_unauthorized(db_session):
    event_payload = {
        "event_type": "LOGIN_FAILED",
        "severity": "MEDIUM",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": "192.168.1.100",
        "message": "Failed login attempt"
    }
    
    resp = client.post(
        f"{settings.API_V1_STR}/events",
        headers={"X-API-Key": "invalid_key"},
        json=event_payload
    )
    assert resp.status_code == 401

def test_ingest_duplicate_event(db_session):
    admin, _ = _create_user(db_session, email="admin@dup.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Test App", slug="dup-app", owner_id=admin.id)
    
    key_resp = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "Dup Key"}
    )
    api_key = key_resp.json()["api_key"]
    
    event_payload = {
        "event_type": "LOGIN_SUCCESS",
        "severity": "INFO",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": "10.0.0.1",
        "request_id": "req-12345",
        "message": "Login success"
    }
    
    resp1 = client.post(f"{settings.API_V1_STR}/events", headers={"X-API-Key": api_key}, json=event_payload)
    assert resp1.status_code == 201
    
    resp2 = client.post(f"{settings.API_V1_STR}/events", headers={"X-API-Key": api_key}, json=event_payload)
    assert resp2.status_code == 409

def test_list_events(db_session):
    admin, _ = _create_user(db_session, email="admin@list.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Test App", slug="list-app", owner_id=admin.id)
    
    key_resp = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "List Key"}
    )
    api_key = key_resp.json()["api_key"]
    
    client.post(
        f"{settings.API_V1_STR}/events",
        headers={"X-API-Key": api_key},
        json={
            "event_type": "LOGIN_SUCCESS",
            "severity": "INFO",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "10.0.0.1",
            "message": "Event 1"
        }
    )
    
    resp = client.get(f"{settings.API_V1_STR}/events", headers=_auth_header(admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(e["event_type"] == "LOGIN_SUCCESS" for e in data["items"])
    
def test_list_events_advanced_filters(db_session):
    admin, _ = _create_user(db_session, email="admin@filter.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Filter App", slug="filter-app", owner_id=admin.id)
    
    key_resp = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "Filter Key"}
    )
    api_key = key_resp.json()["api_key"]
    
    resp_ingest = client.post(
        f"{settings.API_V1_STR}/events",
        headers={"X-API-Key": api_key},
        json={
            "event_type": "SUSPICIOUS_REQUEST",
            "severity": "CRITICAL",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "10.0.0.2",
            "message": "Filter this event",
            "username": "hacker",
            "request_path": "/admin/panel"
        }
    )
    assert resp_ingest.status_code == 201
    
    # Test search by username
    resp = client.get(f"{settings.API_V1_STR}/events?search=hacker", headers=_auth_header(admin))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    
    # Test array filters
    resp = client.get(f"{settings.API_V1_STR}/events?severity=CRITICAL,HIGH", headers=_auth_header(admin))
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
    
def test_events_analytics(db_session):
    admin, _ = _create_user(db_session, email="admin@analytics.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Analytics App", slug="analytics-app", owner_id=admin.id)
    
    key_resp = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "Analytics Key"}
    )
    api_key = key_resp.json()["api_key"]
    
    # Ingest 2 events
    client.post(
        f"{settings.API_V1_STR}/events",
        headers={"X-API-Key": api_key},
        json={
            "event_type": "LOGIN_FAILED",
            "severity": "MEDIUM",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "10.0.0.5",
            "message": "Fail 1"
        }
    )
    client.post(
        f"{settings.API_V1_STR}/events",
        headers={"X-API-Key": api_key},
        json={
            "event_type": "LOGIN_FAILED",
            "severity": "HIGH",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "10.0.0.5",
            "message": "Fail 2",
            "request_id": "some-id"
        }
    )
    
    resp = client.get(f"{settings.API_V1_STR}/events/analytics?application_id={app_obj.id}", headers=_auth_header(admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["severity_counts"]["MEDIUM"] == 1
    assert data["severity_counts"]["HIGH"] == 1
    assert data["event_type_counts"]["LOGIN_FAILED"] == 2
    assert "Analytics App" in data["application_counts"]
    assert data["source_ip_counts"]["10.0.0.5"] == 2
    assert len(data["timeline"]) > 0

def test_90_days_limit(db_session):
    admin, _ = _create_user(db_session, email="admin@90days.com", role=UserRole.ADMIN)
    
    start = datetime.now(timezone.utc) - timedelta(days=100)
    end = datetime.now(timezone.utc)
    
    start_str = start.isoformat().replace("+", "%2B")
    end_str = end.isoformat().replace("+", "%2B")
    
    resp = client.get(f"{settings.API_V1_STR}/events?start_date={start_str}&end_date={end_str}", headers=_auth_header(admin))
    assert resp.status_code == 400
    assert "90 days" in resp.json()["detail"]
