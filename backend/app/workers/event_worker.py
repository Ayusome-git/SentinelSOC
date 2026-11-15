import asyncio
import logging
import signal
import sys
import os
import uuid
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import get_async_redis_client, ensure_stream_group, close_redis
from app.db.session import SessionLocal
from app.models.security_event import SecurityEvent
from app.services.event_queue_service import deserialize_stream_payload
from app.detection.service import DetectionService
from app.correlation.service import CorrelationService
from app.services.ml_anomaly_service import MLAnomalyDetectionService
from app.threat_intel.service import ThreatIntelEnrichmentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [EventWorker] %(message)s"
)
logger = logging.getLogger("sentinelsoc.event_worker")

# Global graceful shutdown flag
_shutdown_event = asyncio.Event()


def _handle_signal(sig, frame):
    logger.info(f"Received termination signal ({sig}). Initiating graceful shutdown...")
    _shutdown_event.set()


class EventStreamWorker:
    def __init__(self, consumer_name: str | None = None):
        self.stream_name = getattr(settings, "REDIS_STREAM_NAME", "sentinelsoc:events:stream")
        self.group_name = getattr(settings, "REDIS_CONSUMER_GROUP", "sentinelsoc_consumers")
        self.consumer_name = consumer_name or f"worker_{os.getpid()}_{uuid.uuid4().hex[:6]}"
        self.batch_size = getattr(settings, "WORKER_BATCH_SIZE", 100)
        self.block_ms = getattr(settings, "WORKER_BLOCK_MS", 2000)
        self.dead_letter_stream = f"{self.stream_name}:dlq"

    async def initialize(self) -> None:
        """Ensures the stream and consumer group exist before consuming."""
        logger.info(f"Initializing worker '{self.consumer_name}' for stream '{self.stream_name}'...")
        await ensure_stream_group(self.stream_name, self.group_name)
        logger.info("Stream and consumer group verified.")

    async def process_batch(self, db: Session, raw_messages: List[Tuple[str, Dict[str, str]]]) -> List[str]:
        """
        Processes a batch of raw stream messages:
        1. Deserializes payloads into SecurityEvent models.
        2. Bulk-persists them to PostgreSQL.
        3. Runs Detection and Correlation evaluation.
        4. Triggers background Threat Intel and ML window jobs.
        Returns list of successfully processed message IDs for acknowledgment.
        """
        success_msg_ids: List[str] = []
        events_to_evaluate: List[SecurityEvent] = []
        affected_apps = set()

        for msg_id, payload in raw_messages:
            try:
                event_dict = deserialize_stream_payload(payload)
                db_event = SecurityEvent(**event_dict)
                db.add(db_event)
                events_to_evaluate.append(db_event)
                success_msg_ids.append(msg_id)
                affected_apps.add(db_event.application_id)
            except Exception as exc:
                logger.error(f"Error deserializing event message {msg_id}: {exc}")
                # Send to DLQ so poison pill does not halt stream
                try:
                    r = get_async_redis_client()
                    await r.xadd(self.dead_letter_stream, {**payload, "error": str(exc), "original_id": msg_id})
                    success_msg_ids.append(msg_id) # Ack poisoned message from main stream
                except Exception as dlq_exc:
                    logger.error(f"Failed to write to DLQ for {msg_id}: {dlq_exc}")

        if not events_to_evaluate:
            return success_msg_ids

        # Commit batch to PostgreSQL
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error(f"Database commit error for batch: {exc}. Retrying individually...")
            # Fallback: process individually to isolate any duplicate or faulty row
            success_msg_ids.clear()
            events_to_evaluate.clear()
            for msg_id, payload in raw_messages:
                try:
                    event_dict = deserialize_stream_payload(payload)
                    single_event = SecurityEvent(**event_dict)
                    db.add(single_event)
                    db.commit()
                    events_to_evaluate.append(single_event)
                    success_msg_ids.append(msg_id)
                except Exception as row_exc:
                    db.rollback()
                    logger.warning(f"Failed inserting single event {msg_id}: {row_exc}")
                    # Ack duplicates or dead-letter
                    success_msg_ids.append(msg_id)

        # Run Security Detection & Correlation on successfully persisted events
        for event in events_to_evaluate:
            try:
                DetectionService.evaluate_event(db, event)
            except Exception as exc:
                logger.error(f"Detection evaluation failed for event {event.id}: {exc}")

            try:
                CorrelationService.evaluate_event(db, event)
            except Exception as exc:
                logger.error(f"Correlation evaluation failed for event {event.id}: {exc}")

            # Trigger threat intelligence enrichment for event
            try:
                ThreatIntelEnrichmentService.enrich_event_alerts(db, str(event.id))
            except Exception as exc:
                logger.debug(f"TI enrichment skipped for {event.id}: {exc}")

        # Trigger ML anomaly detection for affected applications
        for app_id in affected_apps:
            try:
                MLAnomalyDetectionService.trigger_detection_for_latest_window(db, app_id)
            except Exception as exc:
                logger.debug(f"ML trigger skipped for app {app_id}: {exc}")

        return success_msg_ids

    async def run(self) -> None:
        """Main consumer loop."""
        await self.initialize()
        redis_client = get_async_redis_client()
        logger.info(f"Worker '{self.consumer_name}' started listening for events...")

        last_claim_time = asyncio.get_event_loop().time()

        while not _shutdown_event.is_set():
            try:
                # 1. Read new events from the stream
                response = await redis_client.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.stream_name: ">"},
                    count=self.batch_size,
                    block=self.block_ms
                )

                if response:
                    for stream, messages in response:
                        if messages:
                            logger.info(f"Processing batch of {len(messages)} events from '{stream}'...")
                            db = SessionLocal()
                            try:
                                ack_ids = await self.process_batch(db, messages)
                                if ack_ids:
                                    await redis_client.xack(self.stream_name, self.group_name, *ack_ids)
                                    logger.info(f"Acknowledged {len(ack_ids)} events.")
                            finally:
                                db.close()

                # 2. Periodic XAUTOCLAIM to reclaim orphaned messages from crashed workers
                current_time = asyncio.get_event_loop().time()
                if current_time - last_claim_time > 30.0:
                    last_claim_time = current_time
                    try:
                        claim_res = await redis_client.xautoclaim(
                            name=self.stream_name,
                            groupname=self.group_name,
                            consumername=self.consumer_name,
                            min_idle_time=60000, # 60s idle
                            count=50
                        )
                        # claim_res returns [next_id, [messages], [deleted_ids]]
                        claimed_messages = claim_res[1] if len(claim_res) > 1 else []
                        if claimed_messages:
                            logger.warning(f"Reclaimed {len(claimed_messages)} orphaned messages from dead workers.")
                            db = SessionLocal()
                            try:
                                ack_ids = await self.process_batch(db, claimed_messages)
                                if ack_ids:
                                    await redis_client.xack(self.stream_name, self.group_name, *ack_ids)
                            finally:
                                db.close()
                    except Exception as claim_exc:
                        logger.debug(f"Autoclaim check: {claim_exc}")

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Worker iteration exception: {exc}")
                await asyncio.sleep(1.0)

        logger.info(f"Worker '{self.consumer_name}' gracefully stopped.")
        await close_redis()


async def main():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    worker = EventStreamWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
