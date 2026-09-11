"""
Unit tests for the centralized permission system.
"""
import pytest
from app.core.permissions import Permission, has_permission, get_permissions, ROLE_PERMISSIONS
from app.models.user import UserRole


class TestPermissionMatrix:
    """Verify the role → permission mapping is correct."""

    def test_admin_has_all_permissions(self):
        for perm in Permission:
            assert has_permission(UserRole.ADMIN, perm), f"ADMIN should have {perm}"

    def test_analyst_has_read_permissions(self):
        assert has_permission(UserRole.ANALYST, Permission.APPLICATIONS_READ)
        assert has_permission(UserRole.ANALYST, Permission.EVENTS_READ)
        assert has_permission(UserRole.ANALYST, Permission.ALERTS_READ)
        assert has_permission(UserRole.ANALYST, Permission.INCIDENTS_READ)
        assert has_permission(UserRole.ANALYST, Permission.SETTINGS_READ)

    def test_analyst_has_manage_permissions(self):
        assert has_permission(UserRole.ANALYST, Permission.ALERTS_MANAGE)
        assert has_permission(UserRole.ANALYST, Permission.INCIDENTS_MANAGE)

    def test_analyst_lacks_admin_permissions(self):
        assert not has_permission(UserRole.ANALYST, Permission.USERS_READ)
        assert not has_permission(UserRole.ANALYST, Permission.USERS_MANAGE)
        assert not has_permission(UserRole.ANALYST, Permission.APPLICATIONS_MANAGE)
        assert not has_permission(UserRole.ANALYST, Permission.SETTINGS_MANAGE)

    def test_viewer_has_read_only(self):
        assert has_permission(UserRole.VIEWER, Permission.APPLICATIONS_READ)
        assert has_permission(UserRole.VIEWER, Permission.EVENTS_READ)
        assert has_permission(UserRole.VIEWER, Permission.ALERTS_READ)
        assert has_permission(UserRole.VIEWER, Permission.INCIDENTS_READ)
        assert has_permission(UserRole.VIEWER, Permission.SETTINGS_READ)

    def test_viewer_lacks_all_manage_permissions(self):
        assert not has_permission(UserRole.VIEWER, Permission.USERS_READ)
        assert not has_permission(UserRole.VIEWER, Permission.USERS_MANAGE)
        assert not has_permission(UserRole.VIEWER, Permission.APPLICATIONS_MANAGE)
        assert not has_permission(UserRole.VIEWER, Permission.ALERTS_MANAGE)
        assert not has_permission(UserRole.VIEWER, Permission.INCIDENTS_MANAGE)
        assert not has_permission(UserRole.VIEWER, Permission.SETTINGS_MANAGE)

    def test_get_permissions_returns_set(self):
        perms = get_permissions(UserRole.ADMIN)
        assert isinstance(perms, set)
        assert len(perms) == len(Permission)

    def test_unknown_role_returns_empty(self):
        assert get_permissions("NONEXISTENT") == set()
        assert not has_permission("NONEXISTENT", Permission.EVENTS_READ)

    def test_all_roles_are_covered(self):
        for role in UserRole:
            assert role in ROLE_PERMISSIONS, f"Role {role} has no permissions mapping"
