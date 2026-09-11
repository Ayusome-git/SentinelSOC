import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.core.security import hash_password

client = TestClient(app)

def test_login_success(db_session):
    # Setup test user
    email = "testauth@sentinelsoc.com"
    password = "SecurePassword123"
    
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Test Auth User",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # Test login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        print(f"FAILED RESPONSE: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure_wrong_password(db_session):
    email = "testfail@sentinelsoc.com"
    user = User(
        email=email,
        password_hash=hash_password("correctpassword"),
        role=UserRole.ANALYST.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"

def test_login_failure_nonexistent_user(db_session):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@sentinelsoc.com", "password": "password"}
    )
    assert response.status_code == 400

def test_get_current_user_unauthorized():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_get_current_user_success(db_session):
    email = "me@sentinelsoc.com"
    password = "mepassword"
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Me User",
        role=UserRole.VIEWER.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    # Login to get token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    token = login_resp.json()["access_token"]

    # Fetch me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "Me User"
    assert data["role"] == "VIEWER"
    assert "password_hash" not in data
