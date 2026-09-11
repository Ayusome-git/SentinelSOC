import pytest
import uuid
import json
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.models.application import Application, AppEnvironment, AppStatus
from app.models.audit_log import AuditLog
from app.core.security import hash_password, create_access_token

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

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

def _get_token(user):
    return create_access_token(user.id)

def _auth_header(user):
    return {"Authorization": f"Bearer {_get_token(user)}"}

def _create_application(db, *, name="Test App", slug="test-app", owner_id: uuid.UUID):
    app_record = Application(
        name=name,
        slug=slug,
        description="A test application",
        environment=AppEnvironment.DEVELOPMENT.value,
        status=AppStatus.ACTIVE.value,
        owner_id=owner_id
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)
    return app_record


# ===========================================================================
# Application CRUD and RBAC Tests
# ===========================================================================

class TestApplicationRBAC:
    def test_admin_can_list_applications(self, db_session):
        admin, _ = _create_user(db_session, email="admin@soc.com", role=UserRole.ADMIN)
        resp = client.get("/api/v1/applications", headers=_auth_header(admin))
        assert resp.status_code == 200

    def test_analyst_can_list_applications(self, db_session):
        analyst, _ = _create_user(db_session, email="analyst@soc.com", role=UserRole.ANALYST)
        resp = client.get("/api/v1/applications", headers=_auth_header(analyst))
        assert resp.status_code == 200

    def test_viewer_can_list_applications(self, db_session):
        viewer, _ = _create_user(db_session, email="viewer@soc.com", role=UserRole.VIEWER)
        resp = client.get("/api/v1/applications", headers=_auth_header(viewer))
        assert resp.status_code == 200

    def test_admin_can_create_application(self, db_session):
        admin, _ = _create_user(db_session, email="admin2@soc.com", role=UserRole.ADMIN)
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(admin),
            json={
                "name": "New App",
                "slug": "new-app",
                "environment": "DEVELOPMENT",
                "owner_id": str(admin.id)
            },
        )
        assert resp.status_code == 201

    def test_analyst_cannot_create_application(self, db_session):
        analyst, _ = _create_user(db_session, email="analyst2@soc.com", role=UserRole.ANALYST)
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(analyst),
            json={
                "name": "New App",
                "slug": "new-app",
                "environment": "DEVELOPMENT",
                "owner_id": str(analyst.id)
            },
        )
        assert resp.status_code == 403

    def test_viewer_cannot_create_application(self, db_session):
        viewer, _ = _create_user(db_session, email="viewer2@soc.com", role=UserRole.VIEWER)
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(viewer),
            json={
                "name": "New App",
                "slug": "new-app",
                "environment": "DEVELOPMENT",
                "owner_id": str(viewer.id)
            },
        )
        assert resp.status_code == 403

    def test_unauthenticated_returns_401(self, db_session):
        resp = client.get("/api/v1/applications")
        assert resp.status_code == 401


# ===========================================================================
# Application Validation Tests
# ===========================================================================

class TestApplicationValidation:
    def test_create_application_duplicate_slug(self, db_session):
        admin, _ = _create_user(db_session, email="admin@dup.com", role=UserRole.ADMIN)
        _create_application(db_session, name="App 1", slug="app-dup", owner_id=admin.id)
        
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(admin),
            json={
                "name": "App 2",
                "slug": "app-dup",
                "environment": "PRODUCTION",
                "owner_id": str(admin.id)
            },
        )
        assert resp.status_code == 409

    def test_create_application_invalid_slug(self, db_session):
        admin, _ = _create_user(db_session, email="admin@inv.com", role=UserRole.ADMIN)
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(admin),
            json={
                "name": "App",
                "slug": "invalid slug with spaces",
                "environment": "PRODUCTION",
                "owner_id": str(admin.id)
            },
        )
        assert resp.status_code == 422

    def test_create_application_invalid_environment(self, db_session):
        admin, _ = _create_user(db_session, email="admin@env.com", role=UserRole.ADMIN)
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(admin),
            json={
                "name": "App",
                "slug": "valid-slug",
                "environment": "UNKNOWN_ENV",
                "owner_id": str(admin.id)
            },
        )
        assert resp.status_code == 422

    def test_create_application_invalid_owner(self, db_session):
        admin, _ = _create_user(db_session, email="admin@owner.com", role=UserRole.ADMIN)
        fake_uuid = str(uuid.uuid4())
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(admin),
            json={
                "name": "App",
                "slug": "valid-slug",
                "environment": "PRODUCTION",
                "owner_id": fake_uuid
            },
        )
        assert resp.status_code == 422

    def test_create_application_inactive_owner(self, db_session):
        admin, _ = _create_user(db_session, email="admin@iaowner.com", role=UserRole.ADMIN)
        inactive_user, _ = _create_user(db_session, email="inactive@owner.com", is_active=False)
        resp = client.post(
            "/api/v1/applications",
            headers=_auth_header(admin),
            json={
                "name": "App",
                "slug": "valid-slug",
                "environment": "PRODUCTION",
                "owner_id": str(inactive_user.id)
            },
        )
        assert resp.status_code == 422


class TestApplicationOperations:
    def test_get_application(self, db_session):
        admin, _ = _create_user(db_session, email="admin@get.com", role=UserRole.ADMIN)
        app = _create_application(db_session, name="Test App", slug="test-app", owner_id=admin.id)
        
        resp = client.get(f"/api/v1/applications/{app.id}", headers=_auth_header(admin))
        assert resp.status_code == 200
        assert resp.json()["slug"] == "test-app"
        assert resp.json()["owner_name"] == "Test User"

    def test_get_nonexistent_application(self, db_session):
        admin, _ = _create_user(db_session, email="admin@getnon.com", role=UserRole.ADMIN)
        fake_uuid = str(uuid.uuid4())
        resp = client.get(f"/api/v1/applications/{fake_uuid}", headers=_auth_header(admin))
        assert resp.status_code == 404

    def test_update_application(self, db_session):
        admin, _ = _create_user(db_session, email="admin@upd.com", role=UserRole.ADMIN)
        app = _create_application(db_session, name="Test App", slug="test-app", owner_id=admin.id)
        
        resp = client.patch(
            f"/api/v1/applications/{app.id}",
            headers=_auth_header(admin),
            json={"name": "Updated App", "environment": "STAGING"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated App"
        assert resp.json()["environment"] == "STAGING"

    def test_change_application_status(self, db_session):
        admin, _ = _create_user(db_session, email="admin@stat.com", role=UserRole.ADMIN)
        app = _create_application(db_session, name="Test App", slug="test-app", owner_id=admin.id)
        
        resp = client.patch(
            f"/api/v1/applications/{app.id}/status",
            headers=_auth_header(admin),
            json={"status": "SUSPENDED"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "SUSPENDED"

    def test_analyst_cannot_update_application(self, db_session):
        admin, _ = _create_user(db_session, email="admin@stat2.com", role=UserRole.ADMIN)
        analyst, _ = _create_user(db_session, email="analyst@stat.com", role=UserRole.ANALYST)
        app = _create_application(db_session, name="Test App", slug="test-app", owner_id=admin.id)
        
        resp = client.patch(
            f"/api/v1/applications/{app.id}",
            headers=_auth_header(analyst),
            json={"name": "Updated App"},
        )
        assert resp.status_code == 403


class TestAuditLogging:
    def test_create_application_audit(self, db_session):
        admin, _ = _create_user(db_session, email="admin@aud1.com", role=UserRole.ADMIN)
        
        client.post(
            "/api/v1/applications",
            headers=_auth_header(admin),
            json={
                "name": "Audit App",
                "slug": "audit-app",
                "environment": "PRODUCTION",
                "owner_id": str(admin.id)
            },
        )
        
        logs = db_session.query(AuditLog).filter(AuditLog.action == "APPLICATION_CREATED").all()
        assert len(logs) == 1
        assert logs[0].resource_type == "APPLICATION"
        assert logs[0].details["slug"] == "audit-app"
        assert "password" not in json.dumps(logs[0].details)

    def test_update_application_audit(self, db_session):
        admin, _ = _create_user(db_session, email="admin@aud2.com", role=UserRole.ADMIN)
        app = _create_application(db_session, name="Audit App", slug="audit-app2", owner_id=admin.id)
        
        client.patch(
            f"/api/v1/applications/{app.id}",
            headers=_auth_header(admin),
            json={"name": "New Name", "environment": "STAGING"},
        )
        
        logs = db_session.query(AuditLog).filter(AuditLog.action == "APPLICATION_UPDATED").all()
        assert len(logs) == 1
        assert "name" in logs[0].details["changed_fields"]
        assert "environment" in logs[0].details["changed_fields"]

    def test_status_change_application_audit(self, db_session):
        admin, _ = _create_user(db_session, email="admin@aud3.com", role=UserRole.ADMIN)
        app = _create_application(db_session, name="Audit App", slug="audit-app3", owner_id=admin.id)
        
        client.patch(
            f"/api/v1/applications/{app.id}/status",
            headers=_auth_header(admin),
            json={"status": "INACTIVE"},
        )
        
        logs = db_session.query(AuditLog).filter(AuditLog.action == "APPLICATION_STATUS_CHANGED").all()
        assert len(logs) == 1
        assert logs[0].details["new_status"] == "INACTIVE"
        assert logs[0].details["old_status"] == "ACTIVE"
