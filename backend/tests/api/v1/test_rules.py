import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token

client = TestClient(app)

def _create_user(db, *, email="test@soc.com", role=UserRole.ADMIN, is_active=True, password="SecurePass123"):
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Test User",
        role=role.value,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, password

def _auth_header(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}

def test_create_rule_admin(db_session):
    admin, _ = _create_user(db_session, email="admin@rules.com", role=UserRole.ADMIN)
    response = client.post(
        "/api/v1/rules/",
        headers=_auth_header(admin),
        json={
            "name": "Test Rule",
            "description": "A test rule",
            "rule_type": "THRESHOLD",
            "enabled": True,
            "severity": "HIGH",
            "event_type": "TEST_EVENT",
            "threshold": 3,
            "window_seconds": 60,
            "group_by": "source_ip"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Rule"

def test_create_rule_analyst_forbidden(db_session):
    analyst, _ = _create_user(db_session, email="analyst@rules.com", role=UserRole.ANALYST)
    response = client.post(
        "/api/v1/rules/",
        headers=_auth_header(analyst),
        json={
            "name": "Test Rule",
            "severity": "HIGH",
            "event_type": "TEST_EVENT",
            "threshold": 3,
            "window_seconds": 60,
            "group_by": "source_ip"
        }
    )
    assert response.status_code == 403

def test_list_rules(db_session):
    analyst, _ = _create_user(db_session, email="analyst2@rules.com", role=UserRole.ANALYST)
    response = client.get("/api/v1/rules/", headers=_auth_header(analyst))
    assert response.status_code == 200
    data = response.json()
    assert "items" in data

