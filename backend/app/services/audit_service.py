"""
Audit logging service for SentinelSOC.

Creates standardized audit records for user-management actions.
Never stores passwords, hashes, tokens, or secrets in audit details.
"""

from typing import Any, Optional
import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


# Fields that must NEVER appear in audit log details
_SENSITIVE_KEYS = {"password", "password_hash", "access_token", "token", "secret", "jwt"}


def _sanitize_details(details: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Remove any sensitive fields from audit details."""
    if not details:
        return details
    return {k: v for k, v in details.items() if k.lower() not in _SENSITIVE_KEYS}


def create_audit_log(
    db: Session,
    *,
    actor_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: str,
    request: Optional[Request] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """
    Create an audit log record within the current transaction.

    The caller is responsible for committing the transaction — this ensures
    the audit record and the associated mutation are committed atomically.
    """
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

    audit = AuditLog(
        user_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=ip_address,
        user_agent=user_agent,
        details=_sanitize_details(details),
    )
    db.add(audit)
    return audit
