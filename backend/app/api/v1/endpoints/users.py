"""
User management API endpoints.

All endpoints require USERS_READ or USERS_MANAGE permissions.
Authorization is enforced via the require_permission dependency which
loads the current user's role from the database on every request.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission, CurrentUser
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.user import (
    UserCreateByAdmin,
    UserUpdate,
    UserRoleUpdate,
    UserStatusUpdate,
    UserResponse,
    PaginatedUsersResponse,
)
from app.services import user_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedUsersResponse,
    dependencies=[Depends(require_permission(Permission.USERS_READ))],
    summary="List SOC users",
    description="Retrieve a paginated list of SOC users. Requires USERS_READ permission.",
    responses={401: {"description": "Not authenticated"}, 403: {"description": "Insufficient permissions"}},
)
def list_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search by email or name"),
):
    users, total = user_service.list_users(db, page=page, page_size=page_size, search=search)
    return PaginatedUsersResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permission(Permission.USERS_READ))],
    summary="Get a SOC user",
    description="Retrieve a single user by ID. Requires USERS_READ permission.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "User not found"},
    },
)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    user = user_service.get_user(db, user_id)
    return UserResponse.model_validate(user)


@router.post(
    "",
    response_model=UserResponse,
    status_code=201,
    summary="Create a SOC user",
    description="Create a new user. Only ADMIN. No public registration.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        409: {"description": "Email already exists"},
        422: {"description": "Validation error"},
    },
)
def create_user(
    data: UserCreateByAdmin,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    user = user_service.create_user(db, data=data, actor=current_user, request=request)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a SOC user's profile",
    description="Update safe user fields (full_name, email). Requires USERS_MANAGE.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "User not found"},
        409: {"description": "Email already exists"},
    },
)
def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    user = user_service.update_user(db, user_id=user_id, data=data, actor=current_user, request=request)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Change a user's role",
    description="Change the role of a user. Only ADMIN. Prevents last-admin demotion.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "User not found"},
        409: {"description": "Cannot demote the last active administrator"},
        422: {"description": "Invalid role"},
    },
)
def change_user_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    user = user_service.change_role(db, user_id=user_id, data=data, actor=current_user, request=request)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or deactivate a user",
    description="Toggle user active status. Only ADMIN. Prevents last-admin deactivation.",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "User not found"},
        409: {"description": "Cannot deactivate the last active administrator"},
    },
)
def change_user_status(
    user_id: uuid.UUID,
    data: UserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
):
    user = user_service.change_status(db, user_id=user_id, data=data, actor=current_user, request=request)
    return UserResponse.model_validate(user)
