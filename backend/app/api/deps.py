"""
FastAPI dependencies for authentication and authorization.

Authorization flow:
  JWT -> User ID -> Load user from DB -> Check is_active -> Determine role -> Resolve permissions -> Authorize

The JWT only identifies the user. Role and permissions are always loaded from the database,
ensuring that role changes and deactivation take effect immediately.
"""

from typing import Generator, Annotated, Callable, Optional, Any, TypeVar, Type
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import uuid
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.orm import Session, Query
from app.core.config import settings
from app.core.security import ALGORITHM
from app.core.permissions import Permission, has_permission
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str | None = None


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]

def get_current_user(db: SessionDep, token: TokenDep) -> User:
    """
    Validate the JWT token and return the current active User.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def require_permission(permission: Permission) -> Callable:
    """
    Factory that returns a FastAPI dependency enforcing a specific permission.
    """
    def _check_permission(current_user: CurrentUser) -> User:
        if not has_permission(UserRole(current_user.role), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check_permission


from fastapi.security import APIKeyHeader
from app.models.application import Application
from app.services.api_key_service import authenticate_api_key

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_application_from_api_key(
    db: SessionDep,
    api_key: str = Depends(api_key_header)
) -> Application:
    """
    Authenticate an application via API key.
    Raises 401 if invalid, expired, revoked, or application is suspended/inactive.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header missing"
        )
        
    application = authenticate_api_key(db, api_key)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API Key"
        )
        
    return application

def check_app_access(current_user: User, application_id: uuid.UUID | str) -> None:
    """
    Verify that the current user has access to the specified application.
    Admins can access everything. Analysts/Viewers can only access apps they own.
    Raises 403 Forbidden if they do not have access.
    """
    if not application_id:
        return
        
    if current_user.role != UserRole.ADMIN:
        if str(application_id) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this application's data."
            )

T = TypeVar("T")

def filter_query_by_app_access(query: Query, model: Type[T], current_user: User) -> Query:
    """
    Filter a SQLAlchemy query to only return records the user is authorized to see.
    Assumes the model has an `application_id` column, unless the model IS Application, 
    in which case it filters by `id`.
    """
    if current_user.role == UserRole.ADMIN:
        return query
        
    if model.__name__ == "Application":
        return query.filter(model.id == current_user.id)
    else:
        return query.filter(model.application_id == current_user.id)
