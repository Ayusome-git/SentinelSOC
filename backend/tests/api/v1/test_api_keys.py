import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import UserRole
from app.models.application import Application, AppEnvironment, AppStatus
from app.models.application_api_key import ApplicationApiKey
from tests.api.v1.test_applications import _create_user, _auth_header, _create_application
from app.core.config import settings

client = TestClient(app)

def test_admin_can_create_api_key(db_session):
    admin, _ = _create_user(db_session, email="admin@api1.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Test App", slug="test-app-keys", owner_id=admin.id)
    
    response = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "Test Key"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "api_key" in data
    assert data["api_key"].startswith("ssk_dev_")
    assert "name" in data
    assert data["name"] == "Test Key"
    assert data["is_active"] is True
    
    db_key = db_session.query(ApplicationApiKey).filter(ApplicationApiKey.id == uuid.UUID(data["id"])).first()
    assert db_key is not None
    assert db_key.key_hash != data["api_key"]
    assert db_key.key_prefix == data["key_prefix"]

def test_analyst_cannot_create_api_key(db_session):
    admin, _ = _create_user(db_session, email="admin@api2.com", role=UserRole.ADMIN)
    analyst, _ = _create_user(db_session, email="analyst@api2.com", role=UserRole.ANALYST)
    app_obj = _create_application(db_session, name="Test App", slug="test-app-keys2", owner_id=admin.id)

    response = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(analyst),
        json={"name": "Test Key Analyst"}
    )
    assert response.status_code == 403

def test_viewer_cannot_create_api_key(db_session):
    admin, _ = _create_user(db_session, email="admin@api3.com", role=UserRole.ADMIN)
    viewer, _ = _create_user(db_session, email="viewer@api3.com", role=UserRole.VIEWER)
    app_obj = _create_application(db_session, name="Test App", slug="test-app-keys3", owner_id=admin.id)

    response = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(viewer),
        json={"name": "Test Key Viewer"}
    )
    assert response.status_code == 403

def test_api_key_authentication(db_session):
    admin, _ = _create_user(db_session, email="admin@api4.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Test App", slug="test-app-keys4", owner_id=admin.id)

    response = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "Auth Test Key"}
    )
    assert response.status_code == 201
    raw_key = response.json()["api_key"]

    from app.api import deps
    from fastapi import APIRouter, Depends
    from app.main import app as main_app
    
    router = APIRouter()
    @router.get("/test-auth")
    def test_auth(application: Application = Depends(deps.get_application_from_api_key)):
        return {"app_id": str(application.id)}
    
    # Check if already added to avoid errors if this test runs multiple times
    if not any(hasattr(route, "path") and route.path == "/test-auth" for route in main_app.router.routes):
        main_app.include_router(router)
    
    auth_response = client.get("/test-auth", headers={"X-API-Key": raw_key})
    assert auth_response.status_code == 200
    assert auth_response.json()["app_id"] == str(app_obj.id)
    
    auth_response = client.get("/test-auth", headers={"X-API-Key": raw_key + "invalid"})
    assert auth_response.status_code == 401
    
    key_id = response.json()["id"]
    client.patch(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys/{key_id}/status",
        headers=_auth_header(admin),
        json={"is_active": False}
    )
    
    auth_response = client.get("/test-auth", headers={"X-API-Key": raw_key})
    assert auth_response.status_code == 401

def test_list_api_keys_hides_raw_secret(db_session):
    admin, _ = _create_user(db_session, email="admin@api5.com", role=UserRole.ADMIN)
    app_obj = _create_application(db_session, name="Test App", slug="test-app-keys5", owner_id=admin.id)

    response = client.post(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin),
        json={"name": "List Test Key"}
    )
    assert response.status_code == 201
    
    list_response = client.get(
        f"{settings.API_V1_STR}/applications/{app_obj.id}/api-keys",
        headers=_auth_header(admin)
    )
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data) > 0
    assert "api_key" not in data[0]
    assert "key_hash" not in data[0]
    assert "key_prefix" in data[0]
