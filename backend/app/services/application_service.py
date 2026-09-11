import uuid
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import exc

from fastapi import HTTPException, status, Request
from app.models.application import Application, AppEnvironment, AppStatus
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationStatusUpdate
from app.services.audit_service import create_audit_log


def list_applications(
    db: Session,
    *,
    environment: Optional[AppEnvironment] = None,
    status: Optional[AppStatus] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[list[Application], int]:
    query = db.query(Application)

    if environment:
        query = query.filter(Application.environment == environment.value)
    if status:
        query = query.filter(Application.status == status.value)

    total = query.count()
    offset = (page - 1) * page_size
    applications = query.order_by(Application.created_at.desc()).offset(offset).limit(page_size).all()
    return applications, total


def get_application(db: Session, application_id: uuid.UUID) -> Optional[Application]:
    return db.query(Application).filter(Application.id == application_id).first()


def get_application_by_slug(db: Session, slug: str) -> Optional[Application]:
    return db.query(Application).filter(Application.slug == slug).first()


def create_application(
    db: Session, 
    *, 
    data: ApplicationCreate, 
    actor_id: uuid.UUID,
    request: Request
) -> Application:
    # Validate Slug
    if get_application_by_slug(db, data.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Application with slug '{data.slug}' already exists."
        )

    # Validate Owner
    owner = db.query(User).filter(User.id == data.owner_id).first()
    if not owner or not owner.is_active:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Specified owner does not exist or is inactive."
        )

    db_obj = Application(
        name=data.name.strip(),
        slug=data.slug,
        description=data.description,
        environment=data.environment.value,
        owner_id=data.owner_id,
        status=AppStatus.ACTIVE.value
    )
    db.add(db_obj)
    db.flush()

    create_audit_log(
        db=db,
        actor_id=actor_id,
        action="APPLICATION_CREATED",
        resource_type="APPLICATION",
        resource_id=str(db_obj.id),
        request=request,
        details={"name": db_obj.name, "slug": db_obj.slug, "environment": db_obj.environment}
    )

    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_application(
    db: Session,
    *,
    db_obj: Application,
    data: ApplicationUpdate,
    actor_id: uuid.UUID,
    request: Request
) -> Application:
    update_data = data.model_dump(exclude_unset=True)
    changed_fields = []

    if "owner_id" in update_data and update_data["owner_id"] != db_obj.owner_id:
        owner = db.query(User).filter(User.id == update_data["owner_id"]).first()
        if not owner or not owner.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Specified owner does not exist or is inactive."
            )
        db_obj.owner_id = update_data["owner_id"]
        changed_fields.append("owner_id")

    if "name" in update_data and update_data["name"].strip() != db_obj.name:
        db_obj.name = update_data["name"].strip()
        changed_fields.append("name")

    if "description" in update_data and update_data["description"] != db_obj.description:
        db_obj.description = update_data["description"]
        changed_fields.append("description")

    if "environment" in update_data and update_data["environment"].value != db_obj.environment:
        db_obj.environment = update_data["environment"].value
        changed_fields.append("environment")

    if changed_fields:
        create_audit_log(
            db=db,
            actor_id=actor_id,
            action="APPLICATION_UPDATED",
            resource_type="APPLICATION",
            resource_id=str(db_obj.id),
            request=request,
            details={"changed_fields": changed_fields}
        )

        db.commit()
        db.refresh(db_obj)

    return db_obj


def change_application_status(
    db: Session,
    *,
    db_obj: Application,
    data: ApplicationStatusUpdate,
    actor_id: uuid.UUID,
    request: Request
) -> Application:
    old_status = db_obj.status
    new_status = data.status.value

    if old_status == new_status:
        return db_obj

    db_obj.status = new_status
    
    create_audit_log(
        db=db,
        actor_id=actor_id,
        action="APPLICATION_STATUS_CHANGED",
        resource_type="APPLICATION",
        resource_id=str(db_obj.id),
        request=request,
        details={"old_status": old_status, "new_status": new_status}
    )

    db.commit()
    db.refresh(db_obj)
    return db_obj
