import asyncio
import uuid
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.security_event import EventCreate, EventType, EventSeverity
from app.services.event_queue_service import (
    serialize_event,
    deserialize_stream_payload,
    enqueue_event_async,
    enqueue_batch_async
)
from app.workers.event_worker import EventStreamWorker


def test_serialize_deserialize_roundtrip():
    app_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    event_in = EventCreate(
        event_type=EventType.LOGIN_FAILED,
        severity=EventSeverity.HIGH,
        timestamp=now,
        source_ip="192.168.1.50",
        message="Failed login attempt",
        username="admin",
        user_id="usr_123",
        metadata={"ip_reputation": "suspicious", "attempts": 3}
    )

    eid_str, payload = serialize_event(app_id, event_in)
    assert eid_str is not None
    assert payload["event_type"] == "LOGIN_FAILED"
    assert payload["source_ip"] == "192.168.1.50"
    assert "attempts" in payload["metadata"]

    deserialized = deserialize_stream_payload(payload)
    assert deserialized["id"] == uuid.UUID(eid_str)
    assert deserialized["application_id"] == app_id
    assert deserialized["event_type"] == "LOGIN_FAILED"
    assert deserialized["source_ip"] == "192.168.1.50"
    assert deserialized["metadata_"]["attempts"] == 3


def test_enqueue_event_async():
    async def run():
        mock_redis = AsyncMock()
        mock_redis.xadd.return_value = "1700000000000-0"

        with patch("app.services.event_queue_service.get_async_redis_client", return_value=mock_redis):
            msg_id = await enqueue_event_async({"id": "test-123", "message": "test"})
            assert msg_id == "1700000000000-0"
            mock_redis.xadd.assert_awaited_once()

    asyncio.run(run())


def test_enqueue_batch_async():
    async def run():
        mock_redis = MagicMock()
        mock_pipe = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipe

        with patch("app.services.event_queue_service.get_async_redis_client", return_value=mock_redis):
            payloads = [{"id": f"event-{i}"} for i in range(5)]
            count = await enqueue_batch_async(payloads)
            assert count == 5
            assert mock_pipe.xadd.call_count == 5
            mock_pipe.execute.assert_awaited_once()

    asyncio.run(run())


def test_worker_process_batch_persists_and_evaluates():
    async def run():
        worker = EventStreamWorker(consumer_name="test_worker")
        mock_db = MagicMock()

        app_id = str(uuid.uuid4())
        msg1_id = "1700000000001-0"
        payload1 = {
            "id": str(uuid.uuid4()),
            "application_id": app_id,
            "event_type": "LOGIN_FAILED",
            "severity": "MEDIUM",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "10.0.0.1",
            "message": "Bad password"
        }

        raw_messages = [(msg1_id, payload1)]

        with patch("app.workers.event_worker.DetectionService.evaluate_event") as mock_detect, \
             patch("app.workers.event_worker.CorrelationService.evaluate_event") as mock_correlate, \
             patch("app.workers.event_worker.ThreatIntelEnrichmentService.enrich_event_alerts"), \
             patch("app.workers.event_worker.MLAnomalyDetectionService.trigger_detection_for_latest_window"):
            
            ack_ids = await worker.process_batch(mock_db, raw_messages)
            assert ack_ids == [msg1_id]
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_detect.assert_called_once()
            mock_correlate.assert_called_once()

    asyncio.run(run())


def test_worker_handles_poison_pill_to_dlq():
    async def run():
        worker = EventStreamWorker(consumer_name="dlq_worker")
        mock_db = MagicMock()
        mock_redis = AsyncMock()

        poison_id = "1700000000002-0"
        # Missing required application_id causes exception
        poison_payload = {"id": "malformed", "data": "corrupt"}
        raw_messages = [(poison_id, poison_payload)]

        with patch("app.workers.event_worker.get_async_redis_client", return_value=mock_redis):
            ack_ids = await worker.process_batch(mock_db, raw_messages)
            # Poison pill should be acknowledged from main stream and sent to DLQ
            assert ack_ids == [poison_id]
            mock_redis.xadd.assert_awaited_once()
            dlq_args = mock_redis.xadd.call_args[0]
            assert "dlq" in dlq_args[0]

    asyncio.run(run())


def test_batch_endpoint_queues_events():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models.application import Application, AppStatus
    from app.api import deps

    client = TestClient(app)
    mock_app = MagicMock(spec=Application)
    mock_app.id = uuid.uuid4()
    mock_app.status = AppStatus.ACTIVE.value

    app.dependency_overrides[deps.get_application_from_api_key] = lambda: mock_app

    try:
        now_str = datetime.now(timezone.utc).isoformat()
        batch_payload = {
            "events": [
                {
                    "event_type": "LOGIN_SUCCESS",
                    "severity": "INFO",
                    "timestamp": now_str,
                    "source_ip": "10.0.0.1",
                    "message": "User logged in"
                },
                {
                    "event_type": "LOGIN_FAILED",
                    "severity": "HIGH",
                    "timestamp": now_str,
                    "source_ip": "10.0.0.2",
                    "message": "Bad password"
                }
            ]
        }

        with patch("app.api.v1.endpoints.events.enqueue_batch_async", return_value=2) as mock_enqueue:
            resp = client.post("/api/v1/events/batch", json=batch_payload, headers={"X-API-Key": "test_key"})
            assert resp.status_code == 201
            data = resp.json()
            assert data["queued"] == 2
            assert data["status"] == "accepted"
            assert len(data["event_ids"]) == 2
            mock_enqueue.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(deps.get_application_from_api_key, None)

