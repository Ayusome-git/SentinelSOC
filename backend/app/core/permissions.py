"""
Centralized Permission System for SentinelSOC.

Defines all permissions as an enum and maps roles to their granted permissions.
This is the single source of truth for authorization decisions.
"""

import enum
from typing import Set

from app.models.user import UserRole


class Permission(str, enum.Enum):
    """All permissions available in SentinelSOC."""

    # User management
    USERS_READ = "USERS_READ"
    USERS_MANAGE = "USERS_MANAGE"

    # Application management
    APPLICATIONS_READ = "APPLICATIONS_READ"
    APPLICATIONS_MANAGE = "APPLICATIONS_MANAGE"

    # Security events
    EVENTS_READ = "EVENTS_READ"

    # Alerts
    ALERTS_READ = "ALERTS_READ"
    ALERTS_MANAGE = "ALERTS_MANAGE"

    # Incidents
    INCIDENTS_READ = "INCIDENTS_READ"
    INCIDENTS_MANAGE = "INCIDENTS_MANAGE"

    # Settings
    SETTINGS_READ = "SETTINGS_READ"
    SETTINGS_MANAGE = "SETTINGS_MANAGE"

    # Detection Rules
    RULES_READ = "RULES_READ"
    RULES_MANAGE = "RULES_MANAGE"

    # Correlations
    CORRELATIONS_READ = "CORRELATIONS_READ"
    CORRELATIONS_MANAGE = "CORRELATIONS_MANAGE"

    # ML
    ML_READ = "ML_READ"
    ML_MANAGE = "ML_MANAGE"

    # Threat Intelligence
    THREAT_INTEL_READ = "THREAT_INTEL_READ"
    THREAT_INTEL_MANAGE = "THREAT_INTEL_MANAGE"

    # Automated Response & Actions
    RESPONSE_READ = "RESPONSE_READ"
    RESPONSE_REQUEST = "RESPONSE_REQUEST"
    RESPONSE_APPROVE = "RESPONSE_APPROVE"
    RESPONSE_MANAGE = "RESPONSE_MANAGE"

    # Notifications
    NOTIFICATIONS_READ = "NOTIFICATIONS_READ"
    NOTIFICATIONS_MANAGE = "NOTIFICATIONS_MANAGE"


# Centralized role → permissions mapping.
# This is the authoritative matrix — extend it as new permissions are added.
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        Permission.USERS_READ,
        Permission.USERS_MANAGE,
        Permission.APPLICATIONS_READ,
        Permission.APPLICATIONS_MANAGE,
        Permission.EVENTS_READ,
        Permission.ALERTS_READ,
        Permission.ALERTS_MANAGE,
        Permission.INCIDENTS_READ,
        Permission.INCIDENTS_MANAGE,
        Permission.SETTINGS_READ,
        Permission.SETTINGS_MANAGE,
        Permission.RULES_READ,
        Permission.RULES_MANAGE,
        Permission.CORRELATIONS_READ,
        Permission.CORRELATIONS_MANAGE,
        Permission.ML_READ,
        Permission.ML_MANAGE,
        Permission.THREAT_INTEL_READ,
        Permission.THREAT_INTEL_MANAGE,
        Permission.RESPONSE_READ,
        Permission.RESPONSE_REQUEST,
        Permission.RESPONSE_APPROVE,
        Permission.RESPONSE_MANAGE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_MANAGE,
    },
    UserRole.ANALYST: {
        Permission.APPLICATIONS_READ,
        Permission.EVENTS_READ,
        Permission.ALERTS_READ,
        Permission.ALERTS_MANAGE,
        Permission.INCIDENTS_READ,
        Permission.INCIDENTS_MANAGE,
        Permission.SETTINGS_READ,
        Permission.RULES_READ,
        Permission.CORRELATIONS_READ,
        Permission.CORRELATIONS_MANAGE,
        Permission.ML_READ,
        Permission.THREAT_INTEL_READ,
        Permission.THREAT_INTEL_MANAGE,
        Permission.RESPONSE_READ,
        Permission.RESPONSE_REQUEST,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_MANAGE,
    },
    UserRole.VIEWER: {
        Permission.APPLICATIONS_READ,
        Permission.EVENTS_READ,
        Permission.ALERTS_READ,
        Permission.INCIDENTS_READ,
        Permission.SETTINGS_READ,
        Permission.CORRELATIONS_READ,
        Permission.RESPONSE_READ,
        Permission.NOTIFICATIONS_READ,
    },
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return permission in role_perms


def get_permissions(role: UserRole) -> Set[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, set())
