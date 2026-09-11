import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.core.permissions import Permission
from app.models.application import AppEnvironment, AppStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatusUpdate,
    ApplicationResponse,
    ApplicationListResponse
)
from app.schemas.application_api_key import (
    ApiKeyCreate,
    ApiKeyStatusUpdate,
    ApiKeyResponse,
    ApiKeyCreateResponse
)
from app.services import application_service, api_key_service

router = APIRouter()


@router.get("", response_model=ApplicationListResponse, dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_READ))])
def list_applications(
    *,
    db: Session = Depends(deps.get_db),
    environment: AppEnvironment | None = None,
    status: AppStatus | None = None,
    page: int = 1,
    page_size: int = 20
) -> Any:
    """
    Retrieve applications.
    Requires APPLICATIONS_READ permission.
    """
    # Enforce reasonable limits
    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)

    applications, total = application_service.list_applications(
        db=db,
        environment=environment,
        status=status,
        page=page,
        page_size=page_size
    )

    items = []
    for app in applications:
        # Pydantic schema expects owner_name which is derived from owner relationship
        owner_name = app.owner.full_name if app.owner else "Unknown"
        # We manually construct or let Pydantic extract it via from_attributes if we enrich the dict
        # We can just let Pydantic handle it by adding owner_name attribute to a dummy obj, but it's simpler to use a dict
        app_dict = {
            "id": app.id,
            "name": app.name,
            "slug": app.slug,
            "description": app.description,
            "environment": app.environment,
            "status": app.status,
            "owner_id": app.owner_id,
            "owner_name": owner_name,
            "created_at": app.created_at,
            "updated_at": app.updated_at
        }
        items.append(app_dict)

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total
    }


@router.get("/{application_id}", response_model=ApplicationResponse, dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_READ))])
def get_application(
    *,
    db: Session = Depends(deps.get_db),
    application_id: uuid.UUID
) -> Any:
    """
    Get application by ID.
    Requires APPLICATIONS_READ permission.
    """
    app = application_service.get_application(db=db, application_id=application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    owner_name = app.owner.full_name if app.owner else "Unknown"
    return {
        "id": app.id,
        "name": app.name,
        "slug": app.slug,
        "description": app.description,
        "environment": app.environment,
        "status": app.status,
        "owner_id": app.owner_id,
        "owner_name": owner_name,
        "created_at": app.created_at,
        "updated_at": app.updated_at
    }


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_MANAGE))])
def create_application(
    *,
    db: Session = Depends(deps.get_db),
    application_in: ApplicationCreate,
    current_user: User = Depends(deps.get_current_user),
    request: Request
) -> Any:
    """
    Create a new application.
    Requires APPLICATIONS_MANAGE permission.
    """
    app = application_service.create_application(
        db=db,
        data=application_in,
        actor_id=current_user.id,
        request=request
    )
    
    owner_name = app.owner.full_name if app.owner else "Unknown"
    return {
        "id": app.id,
        "name": app.name,
        "slug": app.slug,
        "description": app.description,
        "environment": app.environment,
        "status": app.status,
        "owner_id": app.owner_id,
        "owner_name": owner_name,
        "created_at": app.created_at,
        "updated_at": app.updated_at
    }


@router.patch("/{application_id}", response_model=ApplicationResponse, dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_MANAGE))])
def update_application(
    *,
    db: Session = Depends(deps.get_db),
    application_id: uuid.UUID,
    application_in: ApplicationUpdate,
    current_user: User = Depends(deps.get_current_user),
    request: Request
) -> Any:
    """
    Update application details.
    Requires APPLICATIONS_MANAGE permission.
    """
    app = application_service.get_application(db=db, application_id=application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    app = application_service.update_application(
        db=db,
        db_obj=app,
        data=application_in,
        actor_id=current_user.id,
        request=request
    )
    
    owner_name = app.owner.full_name if app.owner else "Unknown"
    return {
        "id": app.id,
        "name": app.name,
        "slug": app.slug,
        "description": app.description,
        "environment": app.environment,
        "status": app.status,
        "owner_id": app.owner_id,
        "owner_name": owner_name,
        "created_at": app.created_at,
        "updated_at": app.updated_at
    }


@router.patch("/{application_id}/status", response_model=ApplicationResponse, dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_MANAGE))])
def change_application_status(
    *,
    db: Session = Depends(deps.get_db),
    application_id: uuid.UUID,
    status_in: ApplicationStatusUpdate,
    current_user: User = Depends(deps.get_current_user),
    request: Request
) -> Any:
    """
    Change application status.
    Requires APPLICATIONS_MANAGE permission.
    """
    app = application_service.get_application(db=db, application_id=application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    app = application_service.change_application_status(
        db=db,
        db_obj=app,
        data=status_in,
        actor_id=current_user.id,
        request=request
    )
    
    owner_name = app.owner.full_name if app.owner else "Unknown"
    return {
        "id": app.id,
        "name": app.name,
        "slug": app.slug,
        "description": app.description,
        "environment": app.environment,
        "status": app.status,
        "owner_id": app.owner_id,
        "owner_name": owner_name,
        "created_at": app.created_at,
        "updated_at": app.updated_at
    }


@router.post("/{application_id}/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_MANAGE))])
def create_api_key(
    *,
    db: Session = Depends(deps.get_db),
    application_id: uuid.UUID,
    data: ApiKeyCreate,
    current_user: User = Depends(deps.get_current_user),
    request: Request
) -> Any:
    """
    Create a new API key for the application.
    Requires APPLICATIONS_MANAGE permission.
    """
    db_obj, raw_api_key = api_key_service.create_api_key(
        db=db,
        application_id=application_id,
        data=data,
        actor_id=current_user.id,
        request=request
    )
    
    return {
        "id": db_obj.id,
        "name": db_obj.name,
        "key_prefix": db_obj.key_prefix,
        "last_used_at": db_obj.last_used_at,
        "expires_at": db_obj.expires_at,
        "is_active": db_obj.is_active,
        "created_at": db_obj.created_at,
        "created_by": db_obj.created_by,
        "api_key": raw_api_key
    }


@router.get("/{application_id}/api-keys", response_model=list[ApiKeyResponse], dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_READ))])
def list_api_keys(
    *,
    db: Session = Depends(deps.get_db),
    application_id: uuid.UUID
) -> Any:
    """
    List API keys for an application.
    Requires APPLICATIONS_READ permission.
    """
    return api_key_service.list_api_keys(db=db, application_id=application_id)


@router.patch("/{application_id}/api-keys/{key_id}/status", response_model=ApiKeyResponse, dependencies=[Depends(deps.require_permission(Permission.APPLICATIONS_MANAGE))])
def revoke_api_key(
    *,
    db: Session = Depends(deps.get_db),
    application_id: uuid.UUID,
    key_id: uuid.UUID,
    data: ApiKeyStatusUpdate,
    current_user: User = Depends(deps.get_current_user),
    request: Request
) -> Any:
    """
    Revoke or reactivate an API key.
    Requires APPLICATIONS_MANAGE permission.
    """
    return api_key_service.revoke_api_key(
        db=db,
        application_id=application_id,
        key_id=key_id,
        data=data,
        actor_id=current_user.id,
        request=request
    )
