"""
FastAPI dependencies for authentication and authorization.

Authorization flow:
  JWT → User ID → Load user from DB → Check is_active → Determine role → Resolve permissions → Authorize

The JWT only identifies the user. Role and permissions are always loaded from the database,
ensuring that role changes and deactivation take effect immediately.
"""

from typing import Generator, Annotated, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import uuid
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.permissions import Permission, has_permission
from app.db.session import SessionLocal
from app.models.user import User, UserRole

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(db: SessionDep, token: TokenDep) -> User:
    """
    Decode JWT, load user from database, and verify they are active.

    Returns 401 for all authentication failures (missing/invalid token,
    user not found, inactive user). Never reveals which check failed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise credentials_exception
        if payload.get("type") != "access":
            raise credentials_exception
    except (InvalidTokenError, ValidationError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(permission: Permission) -> Callable:
    """
    Factory that returns a FastAPI dependency enforcing a specific permission.

    Usage:
        @router.get("/users", dependencies=[Depends(require_permission(Permission.USERS_READ))])

    The dependency loads the current user's role from the database (via get_current_user)
    and checks it against the centralized permission matrix. Returns 403 if insufficient.
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
            detail="Missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return authenticate_api_key(db=db, raw_api_key=api_key)

