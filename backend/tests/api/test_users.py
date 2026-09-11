"""
Comprehensive tests for user management API and RBAC.

Tests cover:
- Authentication (active, inactive, nonexistent users)
- RBAC enforcement (all roles × key permissions)
- User management CRUD (create, update, role change, status change)
- Security (no password hash leaks, immediate role/status enforcement)
- Last-admin safeguards (prevent lockout)
- Audit logging (records created, no secrets stored)
"""

import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
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


# ===========================================================================
# Authentication Tests
# ===========================================================================

class TestAuthentication:
    def test_active_user_can_authenticate(self, db_session):
        user, pw = _create_user(db_session, email="active@soc.com")
        resp = client.post("/api/v1/auth/login", json={"email": "active@soc.com", "password": pw})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_inactive_user_cannot_authenticate(self, db_session):
        _create_user(db_session, email="inactive@soc.com", is_active=False)
        resp = client.post("/api/v1/auth/login", json={"email": "inactive@soc.com", "password": "SecurePass123"})
        assert resp.status_code == 400

    def test_nonexistent_user_generic_failure(self, db_session):
        resp = client.post("/api/v1/auth/login", json={"email": "nobody@soc.com", "password": "anything"})
        assert resp.status_code == 400

    def test_jwt_auth_works(self, db_session):
        user, _ = _create_user(db_session, email="jwt@soc.com")
        resp = client.get("/api/v1/auth/me", headers=_auth_header(user))
        assert resp.status_code == 200
        assert resp.json()["email"] == "jwt@soc.com"

    def test_inactive_user_cannot_access_protected_api(self, db_session):
        user, _ = _create_user(db_session, email="inact@soc.com", is_active=False)
        resp = client.get("/api/v1/auth/me", headers=_auth_header(user))
        assert resp.status_code == 401


# ===========================================================================
# RBAC Permission Tests
# ===========================================================================

class TestRBAC:
    """Test role-based access control across key endpoints."""

    def test_admin_can_list_users(self, db_session):
        admin, _ = _create_user(db_session, email="admin@soc.com", role=UserRole.ADMIN)
        resp = client.get("/api/v1/users", headers=_auth_header(admin))
        assert resp.status_code == 200

    def test_analyst_cannot_list_users(self, db_session):
        analyst, _ = _create_user(db_session, email="analyst@soc.com", role=UserRole.ANALYST)
        resp = client.get("/api/v1/users", headers=_auth_header(analyst))
        assert resp.status_code == 403

    def test_viewer_cannot_list_users(self, db_session):
        viewer, _ = _create_user(db_session, email="viewer@soc.com", role=UserRole.VIEWER)
        resp = client.get("/api/v1/users", headers=_auth_header(viewer))
        assert resp.status_code == 403

    def test_admin_users_manage_allowed(self, db_session):
        admin, _ = _create_user(db_session, email="admin2@soc.com", role=UserRole.ADMIN)
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "new@soc.com", "password": "Str0ngPass!", "full_name": "New User", "role": "ANALYST"},
        )
        assert resp.status_code == 201

    def test_analyst_users_manage_denied(self, db_session):
        analyst, _ = _create_user(db_session, email="analyst3@soc.com", role=UserRole.ANALYST)
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(analyst),
            json={"email": "new2@soc.com", "password": "Str0ngPass!", "full_name": "Denied", "role": "VIEWER"},
        )
        assert resp.status_code == 403

    def test_viewer_users_manage_denied(self, db_session):
        viewer, _ = _create_user(db_session, email="viewer3@soc.com", role=UserRole.VIEWER)
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(viewer),
            json={"email": "new3@soc.com", "password": "Str0ngPass!", "full_name": "Denied", "role": "VIEWER"},
        )
        assert resp.status_code == 403

    def test_unauthenticated_returns_401(self, db_session):
        resp = client.get("/api/v1/users")
        assert resp.status_code == 401


# ===========================================================================
# User Management CRUD Tests
# ===========================================================================

class TestUserManagement:
    def test_create_user_success(self, db_session):
        admin, _ = _create_user(db_session, email="admin@crud.com")
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "created@crud.com", "password": "Password123", "full_name": "Created User", "role": "ANALYST"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "created@crud.com"
        assert data["role"] == "ANALYST"
        assert data["is_active"] is True
        assert "password_hash" not in data

    def test_create_user_duplicate_email(self, db_session):
        admin, _ = _create_user(db_session, email="admin@dup.com")
        _create_user(db_session, email="dup@dup.com", role=UserRole.VIEWER)
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "dup@dup.com", "password": "Password123", "full_name": "Dup", "role": "VIEWER"},
        )
        assert resp.status_code == 409

    def test_create_user_invalid_role(self, db_session):
        admin, _ = _create_user(db_session, email="admin@inv.com")
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "bad@inv.com", "password": "Password123", "full_name": "Bad", "role": "SUPERADMIN"},
        )
        assert resp.status_code == 422

    def test_create_user_weak_password(self, db_session):
        admin, _ = _create_user(db_session, email="admin@weak.com")
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "weak@weak.com", "password": "short", "full_name": "Weak", "role": "VIEWER"},
        )
        assert resp.status_code == 422

    def test_get_user(self, db_session):
        admin, _ = _create_user(db_session, email="admin@get.com")
        target, _ = _create_user(db_session, email="target@get.com", role=UserRole.ANALYST)
        resp = client.get(f"/api/v1/users/{target.id}", headers=_auth_header(admin))
        assert resp.status_code == 200
        assert resp.json()["email"] == "target@get.com"
        assert "password_hash" not in resp.json()

    def test_update_user(self, db_session):
        admin, _ = _create_user(db_session, email="admin@upd.com")
        target, _ = _create_user(db_session, email="target@upd.com", role=UserRole.VIEWER)
        resp = client.patch(
            f"/api/v1/users/{target.id}",
            headers=_auth_header(admin),
            json={"full_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    def test_change_role(self, db_session):
        admin, _ = _create_user(db_session, email="admin@role.com")
        target, _ = _create_user(db_session, email="target@role.com", role=UserRole.VIEWER)
        resp = client.patch(
            f"/api/v1/users/{target.id}/role",
            headers=_auth_header(admin),
            json={"role": "ANALYST"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "ANALYST"

    def test_unauthorized_role_change_analyst(self, db_session):
        _create_user(db_session, email="admin@urc.com", role=UserRole.ADMIN)
        analyst, _ = _create_user(db_session, email="analyst@urc.com", role=UserRole.ANALYST)
        target, _ = _create_user(db_session, email="target@urc.com", role=UserRole.VIEWER)
        resp = client.patch(
            f"/api/v1/users/{target.id}/role",
            headers=_auth_header(analyst),
            json={"role": "ADMIN"},
        )
        assert resp.status_code == 403

    def test_activate_deactivate_user(self, db_session):
        admin, _ = _create_user(db_session, email="admin@status.com")
        target, _ = _create_user(db_session, email="target@status.com", role=UserRole.VIEWER)

        # Deactivate
        resp = client.patch(
            f"/api/v1/users/{target.id}/status",
            headers=_auth_header(admin),
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Verify deactivated user cannot access APIs
        resp2 = client.get("/api/v1/auth/me", headers=_auth_header(target))
        assert resp2.status_code == 401

        # Reactivate
        resp3 = client.patch(
            f"/api/v1/users/{target.id}/status",
            headers=_auth_header(admin),
            json={"is_active": True},
        )
        assert resp3.status_code == 200
        assert resp3.json()["is_active"] is True

    def test_pagination(self, db_session):
        admin, _ = _create_user(db_session, email="admin@page.com")
        for i in range(5):
            _create_user(db_session, email=f"user{i}@page.com", role=UserRole.VIEWER)

        resp = client.get("/api/v1/users?page=1&page_size=3", headers=_auth_header(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["total"] == 6  # admin + 5 users


# ===========================================================================
# Last-Admin Safeguard Tests
# ===========================================================================

class TestLastAdminSafeguard:
    def test_cannot_deactivate_last_admin(self, db_session):
        admin, _ = _create_user(db_session, email="sole@admin.com", role=UserRole.ADMIN)
        resp = client.patch(
            f"/api/v1/users/{admin.id}/status",
            headers=_auth_header(admin),
            json={"is_active": False},
        )
        assert resp.status_code == 409
        assert "last active administrator" in resp.json()["detail"].lower()

    def test_cannot_demote_last_admin(self, db_session):
        admin, _ = _create_user(db_session, email="sole2@admin.com", role=UserRole.ADMIN)
        resp = client.patch(
            f"/api/v1/users/{admin.id}/role",
            headers=_auth_header(admin),
            json={"role": "ANALYST"},
        )
        assert resp.status_code == 409
        assert "last active administrator" in resp.json()["detail"].lower()

    def test_can_demote_admin_if_another_exists(self, db_session):
        admin1, _ = _create_user(db_session, email="admin1@safe.com", role=UserRole.ADMIN)
        admin2, _ = _create_user(db_session, email="admin2@safe.com", role=UserRole.ADMIN)
        resp = client.patch(
            f"/api/v1/users/{admin2.id}/role",
            headers=_auth_header(admin1),
            json={"role": "ANALYST"},
        )
        assert resp.status_code == 200


# ===========================================================================
# Security Tests
# ===========================================================================

class TestSecurity:
    def test_password_hash_never_in_response_list(self, db_session):
        admin, _ = _create_user(db_session, email="admin@sec1.com")
        resp = client.get("/api/v1/users", headers=_auth_header(admin))
        assert resp.status_code == 200
        text = resp.text
        assert "password_hash" not in text

    def test_password_hash_never_in_response_detail(self, db_session):
        admin, _ = _create_user(db_session, email="admin@sec2.com")
        resp = client.get(f"/api/v1/users/{admin.id}", headers=_auth_header(admin))
        assert resp.status_code == 200
        assert "password_hash" not in resp.text

    def test_password_hash_never_in_create_response(self, db_session):
        admin, _ = _create_user(db_session, email="admin@sec3.com")
        resp = client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "new@sec3.com", "password": "Password123", "full_name": "New", "role": "VIEWER"},
        )
        assert resp.status_code == 201
        assert "password_hash" not in resp.text

    def test_audit_log_no_secrets(self, db_session):
        admin, _ = _create_user(db_session, email="admin@sec4.com")
        client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "audited@sec4.com", "password": "Password123", "full_name": "Audited", "role": "VIEWER"},
        )
        # Check audit log
        logs = db_session.query(AuditLog).filter(AuditLog.action == "USER_CREATED").all()
        for log in logs:
            if log.details:
                details_str = json.dumps(log.details) if isinstance(log.details, dict) else str(log.details)
                assert "Password123" not in details_str

    def test_changed_role_takes_effect_immediately(self, db_session):
        """Changing a user's role in the DB must take effect on the NEXT API call (no JWT caching)."""
        admin, _ = _create_user(db_session, email="admin@imm.com", role=UserRole.ADMIN)
        target, _ = _create_user(db_session, email="target@imm.com", role=UserRole.ADMIN)

        # Target can currently list users (ADMIN)
        resp = client.get("/api/v1/users", headers=_auth_header(target))
        assert resp.status_code == 200

        # Demote target to VIEWER
        client.patch(
            f"/api/v1/users/{target.id}/role",
            headers=_auth_header(admin),
            json={"role": "VIEWER"},
        )

        # Same token, but role changed → should now be 403
        resp2 = client.get("/api/v1/users", headers=_auth_header(target))
        assert resp2.status_code == 403

    def test_deactivated_user_loses_api_access(self, db_session):
        admin, _ = _create_user(db_session, email="admin@deact.com", role=UserRole.ADMIN)
        target, _ = _create_user(db_session, email="target@deact.com", role=UserRole.ANALYST)

        # Target can access protected APIs
        resp = client.get("/api/v1/auth/me", headers=_auth_header(target))
        assert resp.status_code == 200

        # Deactivate target
        client.patch(
            f"/api/v1/users/{target.id}/status",
            headers=_auth_header(admin),
            json={"is_active": False},
        )

        # Same token, but user deactivated → should now be 401
        resp2 = client.get("/api/v1/auth/me", headers=_auth_header(target))
        assert resp2.status_code == 401

    def test_security_headers_present(self, db_session):
        resp = client.get("/api/v1/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("Referrer-Policy") == "no-referrer"


# ===========================================================================
# Audit Logging Tests
# ===========================================================================

class TestAuditLogging:
    def test_create_user_creates_audit_log(self, db_session):
        admin, _ = _create_user(db_session, email="admin@audit1.com")
        client.post(
            "/api/v1/users",
            headers=_auth_header(admin),
            json={"email": "new@audit1.com", "password": "Password123", "full_name": "Audit Test", "role": "ANALYST"},
        )
        logs = db_session.query(AuditLog).filter(AuditLog.action == "USER_CREATED").all()
        assert len(logs) >= 1

    def test_role_change_creates_audit_log(self, db_session):
        admin, _ = _create_user(db_session, email="admin@audit2.com")
        target, _ = _create_user(db_session, email="target@audit2.com", role=UserRole.VIEWER)
        client.patch(
            f"/api/v1/users/{target.id}/role",
            headers=_auth_header(admin),
            json={"role": "ANALYST"},
        )
        logs = db_session.query(AuditLog).filter(AuditLog.action == "USER_ROLE_CHANGED").all()
        assert len(logs) >= 1

    def test_deactivation_creates_audit_log(self, db_session):
        admin, _ = _create_user(db_session, email="admin@audit3.com")
        target, _ = _create_user(db_session, email="target@audit3.com", role=UserRole.VIEWER)
        client.patch(
            f"/api/v1/users/{target.id}/status",
            headers=_auth_header(admin),
            json={"is_active": False},
        )
        logs = db_session.query(AuditLog).filter(AuditLog.action == "USER_DEACTIVATED").all()
        assert len(logs) >= 1

    def test_activation_creates_audit_log(self, db_session):
        admin, _ = _create_user(db_session, email="admin@audit4.com")
        target, _ = _create_user(db_session, email="target@audit4.com", role=UserRole.VIEWER, is_active=False)
        client.patch(
            f"/api/v1/users/{target.id}/status",
            headers=_auth_header(admin),
            json={"is_active": True},
        )
        logs = db_session.query(AuditLog).filter(AuditLog.action == "USER_ACTIVATED").all()
        assert len(logs) >= 1
