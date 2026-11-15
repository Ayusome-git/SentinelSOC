import json
import logging
import uuid
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from uuid import UUID

from app.core.config import settings
from app.core.redis import get_async_redis_client, get_sync_redis_client
from app.schemas.security_event import EventCreate

logger = logging.getLogger(__name__)


def serialize_event(
    application_id: UUID,
    event_in: EventCreate,
    event_id: Optional[UUID] = None
) -> Tuple[str, Dict[str, str]]:
    """
    Serializes an EventCreate schema into a flat string-only dictionary
    suitable for Redis Streams (XADD).
    Returns (event_id_str, payload_dict).
    """
    eid = event_id or uuid.uuid4()
    eid_str = str(eid)

    metadata_str = ""
    if event_in.metadata_:
        try:
            metadata_str = json.dumps(event_in.metadata_)
        except Exception:
            metadata_str = "{}"

    payload = {
        "id": eid_str,
        "application_id": str(application_id),
        "event_type": event_in.event_type.value,
        "severity": event_in.severity.value,
        "timestamp": event_in.timestamp.isoformat(),
        "source_ip": str(event_in.source_ip),
        "message": (event_in.message or "").strip(),
        "user_id": (event_in.user_id or "").strip(),
        "username": (event_in.username or "").strip(),
        "session_id": (event_in.session_id or "").strip(),
        "request_id": (event_in.request_id or "").strip(),
        "http_method": (event_in.http_method or "").strip().upper(),
        "request_path": (event_in.request_path or "").strip(),
        "user_agent": (event_in.user_agent or "").strip(),
        "metadata": metadata_str,
    }
    return eid_str, payload


def deserialize_stream_payload(payload: Dict[str, str]) -> Dict[str, Any]:
    """
    Deserializes a Redis Stream message dictionary back into typed fields
    ready for database model insertion.
    """
    raw_metadata = payload.get("metadata", "")
    metadata_obj = None
    if raw_metadata:
        try:
            metadata_obj = json.loads(raw_metadata)
        except Exception:
            metadata_obj = None

    ts_str = payload.get("timestamp")
    try:
        timestamp_dt = datetime.fromisoformat(ts_str) if ts_str else datetime.now(timezone.utc)
    except Exception:
        timestamp_dt = datetime.now(timezone.utc)

    return {
        "id": uuid.UUID(payload["id"]) if "id" in payload else uuid.uuid4(),
        "application_id": uuid.UUID(payload["application_id"]),
        "event_type": payload.get("event_type", "API_REQUEST"),
        "severity": payload.get("severity", "LOW"),
        "timestamp": timestamp_dt,
        "source_ip": payload.get("source_ip", "0.0.0.0"),
        "message": payload.get("message") or None,
        "user_id": payload.get("user_id") or None,
        "username": payload.get("username") or None,
        "session_id": payload.get("session_id") or None,
        "request_id": payload.get("request_id") or None,
        "http_method": payload.get("http_method") or None,
        "request_path": payload.get("request_path") or None,
        "user_agent": payload.get("user_agent") or None,
        "metadata_": metadata_obj,
    }


async def enqueue_event_async(payload: Dict[str, str]) -> str:
    """
    Publishes a single event payload to the Redis Stream.
    Returns the Redis Stream Message ID.
    """
    redis_client = get_async_redis_client()
    stream_name = getattr(settings, "REDIS_STREAM_NAME", "sentinelsoc:events:stream")
    stream_id = await redis_client.xadd(stream_name, payload)
    return str(stream_id)


async def enqueue_batch_async(payloads: List[Dict[str, str]]) -> int:
    """
    Pipelined publish of multiple events to the Redis Stream.
    Returns the number of queued events.
    """
    if not payloads:
        return 0
    redis_client = get_async_redis_client()
    stream_name = getattr(settings, "REDIS_STREAM_NAME", "sentinelsoc:events:stream")
    pipe = redis_client.pipeline()
    for p in payloads:
        pipe.xadd(stream_name, p)
    await pipe.execute()
    return len(payloads)
