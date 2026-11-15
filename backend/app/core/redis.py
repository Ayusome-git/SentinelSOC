import asyncio
import logging
from typing import AsyncGenerator, Generator, Optional
import redis
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Async pool and client
_async_pool: Optional[aioredis.ConnectionPool] = None
_async_client: Optional[aioredis.Redis] = None

# Sync pool and client (for sync endpoints / services)
_sync_pool: Optional[redis.ConnectionPool] = None
_sync_client: Optional[redis.Redis] = None


def get_async_redis_client() -> aioredis.Redis:
    """
    Returns a singleton async Redis client instance.
    Initializes the pool if not already created.
    """
    global _async_pool, _async_client
    if _async_client is None:
        _async_pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            decode_responses=True
        )
        _async_client = aioredis.Redis(connection_pool=_async_pool)
    return _async_client


def get_sync_redis_client() -> redis.Redis:
    """
    Returns a singleton synchronous Redis client instance.
    Initializes the pool if not already created.
    """
    global _sync_pool, _sync_client
    if _sync_client is None:
        _sync_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            decode_responses=True
        )
        _sync_client = redis.Redis(connection_pool=_sync_pool)
    return _sync_client


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency that yields an async Redis client.
    """
    client = get_async_redis_client()
    try:
        yield client
    finally:
        pass


def get_sync_redis() -> Generator[redis.Redis, None, None]:
    """
    FastAPI dependency that yields a synchronous Redis client.
    """
    client = get_sync_redis_client()
    try:
        yield client
    finally:
        pass


async def ping_redis(timeout: float = 1.0) -> bool:
    """
    Checks if Redis is reachable via async ping within timeout.
    Returns True if healthy, False otherwise.
    """
    try:
        client = get_async_redis_client()
        return bool(await asyncio.wait_for(client.ping(), timeout=timeout))
    except Exception as exc:
        logger.warning(f"Redis ping failed: {exc}")
        return False


def ping_redis_sync() -> bool:
    """
    Checks if Redis is reachable via synchronous ping.
    Returns True if healthy, False otherwise.
    """
    try:
        client = get_sync_redis_client()
        return bool(client.ping())
    except Exception as exc:
        logger.warning(f"Redis sync ping failed: {exc}")
        return False


async def ensure_stream_group(
    stream_name: str,
    group_name: str,
    client: Optional[aioredis.Redis] = None
) -> None:
    """
    Ensures that a Redis Stream and its Consumer Group exist.
    Creates the stream (mkstream=True) and group starting at the latest ID ($).
    If the group already exists (BUSYGROUP), ignores the error.
    """
    r = client or get_async_redis_client()
    try:
        await r.xgroup_create(name=stream_name, groupname=group_name, id="$", mkstream=True)
        logger.info(f"Created consumer group '{group_name}' on stream '{stream_name}'")
    except Exception as exc:
        if "BUSYGROUP" in str(exc):
            logger.debug(f"Consumer group '{group_name}' already exists on '{stream_name}'")
        else:
            logger.error(f"Failed to create stream consumer group '{group_name}' on '{stream_name}': {exc}")
            raise


async def close_redis() -> None:
    """
    Closes async and sync connection pools during application shutdown.
    """
    global _async_client, _async_pool, _sync_client, _sync_pool

    if _async_client is not None:
        try:
            await _async_client.aclose()
        except Exception as exc:
            logger.warning(f"Error closing async Redis client: {exc}")
        _async_client = None

    if _async_pool is not None:
        try:
            await _async_pool.disconnect()
        except Exception as exc:
            logger.warning(f"Error disconnecting async Redis pool: {exc}")
        _async_pool = None

    if _sync_client is not None:
        try:
            _sync_client.close()
        except Exception as exc:
            logger.warning(f"Error closing sync Redis client: {exc}")
        _sync_client = None

    if _sync_pool is not None:
        try:
            _sync_pool.disconnect()
        except Exception as exc:
            logger.warning(f"Error disconnecting sync Redis pool: {exc}")
        _sync_pool = None

    logger.info("Redis connection pools closed successfully.")
