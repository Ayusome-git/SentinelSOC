"""
User management service for SentinelSOC.

Encapsulates business logic for CRUD operations on SOC users.
All mutations create transactional audit records and include
safeguards against last-admin lockout.
"""

from typing import Optional, Tuple, List
import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreateByAdmin, UserUpdate, UserRoleUpdate, UserStatusUpdate
from app.services.audit_service import create_audit_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_active_admins(db: Session) -> int:
    """Count active users with ADMIN role."""
    return (
        db.query(func.count(User.id))
        .filter(User.role == UserRole.ADMIN.value, User.is_active == True)  # noqa: E712
        .scalar()
    )


def _get_user_or_404(db: Session, user_id: uuid.UUID) -> User:
    """Fetch a user by ID or raise 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------

def list_users(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
) -> Tuple[List[User], int]:
    """Return a paginated list of users with optional search."""
    query = db.query(User)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.email.ilike(like)) | (User.full_name.ilike(like))
        )

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return users, total


def get_user(db: Session, user_id: uuid.UUID) -> User:
    """Get a single user by ID."""
    return _get_user_or_404(db, user_id)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create_user(
    db: Session,
    *,
    data: UserCreateByAdmin,
    actor: User,
    request: Optional[Request] = None,
) -> User:
    """Create a new SOC user (admin-only operation)."""
    # Normalize email
    email = data.email.strip().lower()

    # Check uniqueness
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Validate role
    try:
        UserRole(data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of: {', '.join(r.value for r in UserRole)}",
        )

    new_user = User(
        email=email,
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        role=data.role.value if isinstance(data.role, UserRole) else data.role,
        is_active=True,
    )
    db.add(new_user)
    db.flush()  # Get the ID before audit log

    create_audit_log(
        db,
        actor_id=actor.id,
        action="USER_CREATED",
        resource_type="USER",
        resource_id=str(new_user.id),
        request=request,
        details={"email": email, "role": new_user.role, "full_name": new_user.full_name},
    )

    db.commit()
    db.refresh(new_user)
    return new_user


# ---------------------------------------------------------------------------
# Update profile
# ---------------------------------------------------------------------------

def update_user(
    db: Session,
    *,
    user_id: uuid.UUID,
    data: UserUpdate,
    actor: User,
    request: Optional[Request] = None,
) -> User:
    """Update a user's safe profile fields (full_name, email)."""
    user = _get_user_or_404(db, user_id)
    changes: dict = {}

    if data.full_name is not None:
        old = user.full_name
        user.full_name = data.full_name.strip()
        changes["full_name"] = {"old": old, "new": user.full_name}

    if data.email is not None:
        new_email = data.email.strip().lower()
        # Check uniqueness
        existing = db.query(User).filter(User.email == new_email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )
        old = user.email
        user.email = new_email
        changes["email"] = {"old": old, "new": new_email}

    if changes:
        create_audit_log(
            db,
            actor_id=actor.id,
            action="USER_UPDATED",
            resource_type="USER",
            resource_id=str(user_id),
            request=request,
            details=changes,
        )
        db.commit()
        db.refresh(user)

    return user


# ---------------------------------------------------------------------------
# Change role
# ---------------------------------------------------------------------------

def change_role(
    db: Session,
    *,
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    actor: User,
    request: Optional[Request] = None,
) -> User:
    """Change a user's role with last-admin safeguard."""
    user = _get_user_or_404(db, user_id)

    # Validate role
    try:
        new_role = UserRole(data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of: {', '.join(r.value for r in UserRole)}",
        )

    old_role = user.role

    # No-op if same role
    if old_role == new_role.value:
        return user

    # Prevent demoting the last active admin
    if old_role == UserRole.ADMIN.value and new_role != UserRole.ADMIN:
        if user.is_active and _count_active_admins(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot demote the last active administrator",
            )

    user.role = new_role.value

    create_audit_log(
        db,
        actor_id=actor.id,
        action="USER_ROLE_CHANGED",
        resource_type="USER",
        resource_id=str(user_id),
        request=request,
        details={"old_role": old_role, "new_role": new_role.value},
    )

    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Activate / Deactivate
# ---------------------------------------------------------------------------

def change_status(
    db: Session,
    *,
    user_id: uuid.UUID,
    data: UserStatusUpdate,
    actor: User,
    request: Optional[Request] = None,
) -> User:
    """Activate or deactivate a user with last-admin safeguard."""
    user = _get_user_or_404(db, user_id)

    # No-op if same status
    if user.is_active == data.is_active:
        return user

    # Prevent deactivating the last active admin
    if not data.is_active and user.role == UserRole.ADMIN.value and user.is_active:
        if _count_active_admins(db) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot deactivate the last active administrator",
            )

    user.is_active = data.is_active
    action = "USER_ACTIVATED" if data.is_active else "USER_DEACTIVATED"

    create_audit_log(
        db,
        actor_id=actor.id,
        action=action,
        resource_type="USER",
        resource_id=str(user_id),
        request=request,
        details={"email": user.email, "is_active": data.is_active},
    )

    db.commit()
    db.refresh(user)
    return user
