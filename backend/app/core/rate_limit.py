import time
import asyncio
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Basic in-memory rate limiter using a fixed window.
# Dictionary storing (attempts, reset_time) per IP address and endpoint.
_rate_limits: Dict[str, Tuple[int, float]] = {}
_lock = asyncio.Lock()

async def check_rate_limit(request: Request):
    """
    Dependency to enforce rate limiting on specific endpoints.
    Uses AUTH_RATE_LIMIT_ENABLED, AUTH_MAX_ATTEMPTS, AUTH_LOCKOUT_SECONDS from settings.
    """
    if not getattr(settings, "AUTH_RATE_LIMIT_ENABLED", False):
        return
        
    client_ip = request.client.host if request.client else "unknown"
    # Basic identifier: endpoint path + IP
    identifier = f"{request.url.path}:{client_ip}"
    
    max_attempts = getattr(settings, "AUTH_MAX_ATTEMPTS", 10)
    lockout_seconds = getattr(settings, "AUTH_LOCKOUT_SECONDS", 300)
    
    current_time = time.time()
    
    async with _lock:
        if identifier in _rate_limits:
            attempts, reset_time = _rate_limits[identifier]
            
            if current_time > reset_time:
                # Window expired, reset
                _rate_limits[identifier] = (1, current_time + lockout_seconds)
            else:
                if attempts >= max_attempts:
                    logger.warning(f"Rate limit exceeded for {identifier}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please try again later."
                    )
                _rate_limits[identifier] = (attempts + 1, reset_time)
        else:
            # First attempt
            _rate_limits[identifier] = (1, current_time + lockout_seconds)

