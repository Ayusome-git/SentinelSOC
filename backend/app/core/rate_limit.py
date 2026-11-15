import time
import asyncio
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.redis import get_async_redis_client
import logging

logger = logging.getLogger(__name__)

# Fallback in-memory rate limiter using a fixed window.
# Dictionary storing (attempts, reset_time) per IP address and endpoint.
_rate_limits: Dict[str, Tuple[int, float]] = {}
_lock = asyncio.Lock()


async def _in_memory_rate_limit(identifier: str, max_attempts: int, lockout_seconds: int) -> None:
    current_time = time.time()
    async with _lock:
        if identifier in _rate_limits:
            attempts, reset_time = _rate_limits[identifier]
            if current_time > reset_time:
                _rate_limits[identifier] = (1, current_time + lockout_seconds)
            else:
                if attempts >= max_attempts:
                    logger.warning(f"In-memory rate limit exceeded for {identifier}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please try again later."
                    )
                _rate_limits[identifier] = (attempts + 1, reset_time)
        else:
            _rate_limits[identifier] = (1, current_time + lockout_seconds)


async def check_rate_limit(request: Request):
    """
    Dependency to enforce rate limiting on specific endpoints.
    Uses Redis sliding-window with automatic fallback to in-memory limiting.
    Differentiates between auth endpoints and high-volume event ingestion endpoints.
    """
    if not getattr(settings, "AUTH_RATE_LIMIT_ENABLED", False):
        return

    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Distinguish event ingestion from general auth endpoints
    is_event_endpoint = path.startswith("/api/v1/events")
    if is_event_endpoint:
        if not getattr(settings, "EVENT_RATE_LIMIT_ENABLED", True):
            return
        max_attempts = getattr(settings, "EVENT_MAX_REQUESTS_PER_MINUTE", 6000)
        window_seconds = 60
        api_key = request.headers.get("X-API-Key", "")
        key_id = api_key[:12] if api_key else client_ip
        identifier = f"ratelimit:events:{key_id}:{client_ip}"
    else:
        max_attempts = getattr(settings, "AUTH_MAX_ATTEMPTS", 10)
        window_seconds = getattr(settings, "AUTH_LOCKOUT_SECONDS", 300)
        identifier = f"ratelimit:auth:{path}:{client_ip}"

    # Try Redis sliding window first
    try:
        redis_client = get_async_redis_client()
        now = time.time()
        window_start = now - window_seconds

        # Redis Pipeline for atomic sliding-window log
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(identifier, 0, window_start)
        pipe.zadd(identifier, {f"{now}:{time.time_ns()}": now})
        pipe.zcard(identifier)
        pipe.expire(identifier, window_seconds + 5)
        results = await asyncio.wait_for(pipe.execute(), timeout=1.0)

        current_count = results[2]
        if current_count > max_attempts:
            logger.warning(f"Rate limit exceeded for {identifier} ({current_count}/{max_attempts})")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        return
    except HTTPException:
        raise
    except Exception as exc:
        logger.debug(f"Redis rate limiter unavailable ({exc}), falling back to memory.")
        await _in_memory_rate_limit(identifier, max_attempts, window_seconds)
