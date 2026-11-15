import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Tuple, List, Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session

from app.models.application_api_key import ApplicationApiKey
from app.models.application import Application, AppStatus
from app.schemas.application_api_key import ApiKeyCreate, ApiKeyStatusUpdate
from app.core.api_key import generate_api_key, extract_key_prefix, verify_api_key
from app.services.audit_service import create_audit_log
from app.core.redis import get_sync_redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_API_KEYS_PER_APP = 20

def create_api_key(
    db: Session,
    *,
    application_id: uuid.UUID,
    data: ApiKeyCreate,
    actor_id: uuid.UUID,
    request: Request
) -> Tuple[ApplicationApiKey, str]:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Enforce limit
    active_keys_count = db.query(ApplicationApiKey).filter(
        ApplicationApiKey.application_id == application_id,
        ApplicationApiKey.is_active == True
    ).count()

    if active_keys_count >= MAX_API_KEYS_PER_APP:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Maximum number of active API keys ({MAX_API_KEYS_PER_APP}) reached for this application."
        )

    if data.expires_at and data.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Expiration date must be in the future."
        )

    raw_api_key, key_prefix, key_hash = generate_api_key(application.environment)

    db_obj = ApplicationApiKey(
        application_id=application_id,
        name=data.name.strip(),
        key_prefix=key_prefix,
        key_hash=key_hash,
        expires_at=data.expires_at,
        is_active=True,
        created_by=actor_id
    )

    db.add(db_obj)
    db.flush()

    create_audit_log(
        db=db,
        actor_id=actor_id,
        action="API_KEY_CREATED",
        resource_type="API_KEY",
        resource_id=str(db_obj.id),
        request=request,
        details={"name": db_obj.name, "application_id": str(application_id), "key_prefix": key_prefix}
    )

    db.commit()
    db.refresh(db_obj)

    return db_obj, raw_api_key


def list_api_keys(
    db: Session,
    *,
    application_id: uuid.UUID
) -> List[ApplicationApiKey]:
    return db.query(ApplicationApiKey).filter(ApplicationApiKey.application_id == application_id).order_by(ApplicationApiKey.created_at.desc()).all()


def invalidate_application_api_key_cache(application_id: uuid.UUID | str) -> None:
    """
    Invalidates cached API keys associated with an application in Redis.
    """
    try:
        r = get_sync_redis_client()
        set_key = f"app:apikeys:{str(application_id)}"
        cached_keys = r.smembers(set_key)
        if cached_keys:
            for k in cached_keys:
                r.delete(k)
            r.delete(set_key)
            logger.debug(f"Invalidated {len(cached_keys)} cached API keys for app {application_id}")
    except Exception as exc:
        logger.debug(f"Error invalidating API key cache for app {application_id}: {exc}")


def revoke_api_key(
    db: Session,
    *,
    application_id: uuid.UUID,
    key_id: uuid.UUID,
    data: ApiKeyStatusUpdate,
    actor_id: uuid.UUID,
    request: Request
) -> ApplicationApiKey:
    db_obj = db.query(ApplicationApiKey).filter(
        ApplicationApiKey.id == key_id,
        ApplicationApiKey.application_id == application_id
    ).first()

    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    if db_obj.is_active == data.is_active:
        return db_obj

    db_obj.is_active = data.is_active

    # Invalidate cache so revoked key cannot authenticate from cache
    invalidate_application_api_key_cache(application_id)

    action = "API_KEY_REVOKED" if not data.is_active else "API_KEY_REACTIVATED"
    
    create_audit_log(
        db=db,
        actor_id=actor_id,
        action=action,
        resource_type="API_KEY",
        resource_id=str(db_obj.id),
        request=request,
        details={"application_id": str(application_id), "is_active": data.is_active}
    )

    db.commit()
    db.refresh(db_obj)
    return db_obj


def authenticate_api_key(db: Session, raw_api_key: str) -> Application:
    """
    Validates an API key and returns the associated application.
    Checks Redis cache first to bypass expensive Argon2id hash verification.
    Raises 401 Unauthorized for any failure.
    """
    invalid_cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or inactive API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )

    prefix = extract_key_prefix(raw_api_key)
    if not prefix:
        raise invalid_cred_exception

    # Compute fast SHA-256 fingerprint for Redis caching
    key_digest = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
    cache_key = f"apikey:cache:{prefix}:{key_digest}"
    redis_client = None

    try:
        redis_client = get_sync_redis_client()
        cached_app_id = redis_client.get(cache_key)
        if cached_app_id:
            # Fast Path: Validated key cached! Fetch active application by ID
            app_uuid = uuid.UUID(cached_app_id)
            application = db.query(Application).filter(Application.id == app_uuid).first()
            if application and application.status == AppStatus.ACTIVE.value:
                return application
            else:
                # Application was deactivated, delete invalid cache entry
                redis_client.delete(cache_key)
    except Exception as exc:
        logger.debug(f"Redis API key cache lookup failed ({exc}), falling back to database.")

    # Cache Miss / Slow Path: Query candidate keys and run Argon2id
    candidates = db.query(ApplicationApiKey).filter(
        ApplicationApiKey.key_prefix == prefix
    ).all()

    valid_key: Optional[ApplicationApiKey] = None
    for candidate in candidates:
        if verify_api_key(raw_api_key, candidate.key_hash):
            valid_key = candidate
            break

    if not valid_key:
        raise invalid_cred_exception

    if not valid_key.is_active:
        raise invalid_cred_exception

    if valid_key.expires_at and valid_key.expires_at < datetime.now(timezone.utc):
        raise invalid_cred_exception

    application = valid_key.application
    if not application:
        raise invalid_cred_exception

    if application.status != AppStatus.ACTIVE.value:
        raise invalid_cred_exception

    # Cache successful validation in Redis
    if redis_client:
        try:
            ttl = getattr(settings, "API_KEY_CACHE_TTL_SECONDS", 300)
            redis_client.set(cache_key, str(application.id), ex=ttl)
            # Track key under application set for invalidation on revocation
            set_key = f"app:apikeys:{str(application.id)}"
            redis_client.sadd(set_key, cache_key)
            redis_client.expire(set_key, ttl + 60)
        except Exception as exc:
            logger.debug(f"Redis API key cache write failed: {exc}")

    # Update last_used_at with throttle to avoid excessive DB writes
    now = datetime.now(timezone.utc)
    last_used = valid_key.last_used_at
    if last_used and last_used.tzinfo is None:
        last_used = last_used.replace(tzinfo=timezone.utc)

    if not last_used or (now - last_used).total_seconds() > 60:
        valid_key.last_used_at = now
        db.commit()

    return application
