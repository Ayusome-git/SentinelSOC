import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.redis import (
    get_async_redis_client,
    get_sync_redis_client,
    ping_redis,
    ping_redis_sync,
    ensure_stream_group,
    close_redis,
)


def test_redis_clients_created():
    async_client = get_async_redis_client()
    assert async_client is not None

    sync_client = get_sync_redis_client()
    assert sync_client is not None


def test_ping_redis_offline_returns_false():
    # When Redis is not reachable at localhost:6379, ping_redis should return False without crashing
    result = asyncio.run(ping_redis(timeout=0.2))
    assert result is False


def test_ping_redis_sync_offline_returns_false():
    result = ping_redis_sync()
    assert result is False


def test_ensure_stream_group_handles_busygroup():
    async def run():
        mock_client = AsyncMock()
        # Simulate Redis BUSYGROUP error (group already exists)
        mock_client.xgroup_create.side_effect = Exception("BUSYGROUP Consumer Group name already exists")
        
        # Should not raise exception
        await ensure_stream_group("test_stream", "test_group", client=mock_client)
        mock_client.xgroup_create.assert_awaited_once_with(
            name="test_stream",
            groupname="test_group",
            id="$",
            mkstream=True
        )

    asyncio.run(run())


def test_ensure_stream_group_raises_other_errors():
    async def run():
        mock_client = AsyncMock()
        mock_client.xgroup_create.side_effect = Exception("WRONGTYPE Operation against a key holding the wrong kind of value")
        
        with pytest.raises(Exception, match="WRONGTYPE"):
            await ensure_stream_group("test_stream", "test_group", client=mock_client)

    asyncio.run(run())


def test_close_redis_cleans_up():
    async def run():
        # Ensure clients exist
        get_async_redis_client()
        get_sync_redis_client()

        # Close should execute without exception
        await close_redis()

    asyncio.run(run())


def test_rate_limit_sliding_window_exceeded():
    from unittest.mock import MagicMock
    from fastapi import Request, HTTPException
    from app.core.rate_limit import check_rate_limit
    from app.core.config import settings

    async def run():
        mock_redis = MagicMock()
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        # Simulate pipeline results: [zremrangebyscore_res, zadd_res, count, expire_res]
        # count is 15 which exceeds AUTH_MAX_ATTEMPTS (10)
        async def mock_execute():
            return [0, 1, 15, True]
        mock_pipe.execute = mock_execute

        mock_request = MagicMock(spec=Request)
        mock_request.client.host = "192.168.1.100"
        mock_request.url.path = "/api/v1/auth/login"
        mock_request.headers = {}

        with patch("app.core.rate_limit.get_async_redis_client", return_value=mock_redis):
            with patch.object(settings, "AUTH_RATE_LIMIT_ENABLED", True):
                with pytest.raises(HTTPException) as exc_info:
                    await check_rate_limit(mock_request)
                assert exc_info.value.status_code == 429

    asyncio.run(run())


def test_api_key_cache_hit():
    import uuid
    from unittest.mock import MagicMock
    from app.services.api_key_service import authenticate_api_key
    from app.models.application import Application, AppStatus

    mock_db = MagicMock()
    app_id = uuid.uuid4()
    mock_app = MagicMock(spec=Application)
    mock_app.id = app_id
    mock_app.status = AppStatus.ACTIVE.value

    # DB query returns the active application
    mock_db.query.return_value.filter.return_value.first.return_value = mock_app

    mock_redis = MagicMock()
    mock_redis.get.return_value = str(app_id)

    with patch("app.services.api_key_service.get_sync_redis_client", return_value=mock_redis):
        app = authenticate_api_key(mock_db, "ssk_dev_abcd1234567890abcdef1234567890ab")
        assert app == mock_app
        # Verify Redis get was called
        mock_redis.get.assert_called_once()
        # Verify DB candidate query was bypassed!
        assert mock_db.query.return_value.filter.return_value.all.call_count == 0

