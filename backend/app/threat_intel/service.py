import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta, timezone
from typing import List

from app.core.config import settings
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.models.threat_intel import ThreatIntelCache, ThreatIntelIndicator, AlertThreatIntel
from app.threat_intel.client import ti_client
from app.threat_intel.extractor import IndicatorExtractionService
from app.threat_intel.provider import ThreatIntelResult
from app.notifications.triggers import trigger_ti_match

logger = logging.getLogger(__name__)

class ThreatIntelEnrichmentService:
    @staticmethod
    async def enrich_event_alerts(db: Session, event_id: str):
        if not settings.TI_ENABLED:
            return

        # Find all alerts associated with this event
        alerts = db.query(Alert).filter(Alert.security_event_id == event_id).all()
        for alert in alerts:
            await ThreatIntelEnrichmentService.enrich_alert(db, alert.id)

    @staticmethod
    async def enrich_alert(db: Session, alert_id: str):
        if not settings.TI_ENABLED:
            return

        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return

        indicators_to_check = set()

        if alert.security_event_id:
            event = db.query(SecurityEvent).filter(SecurityEvent.id == alert.security_event_id).first()
            if event:
                extracted = IndicatorExtractionService.extract_from_event(event)
                for ind in extracted:
                    indicators_to_check.add(ind)

        # Truncate lookups to prevent unbounded API calls
        indicators_to_check = list(indicators_to_check)[:settings.TI_MAX_LOOKUPS_PER_EVENT]

        new_ti_indicators = []
        for indicator, indicator_type in indicators_to_check:
            # 1. Check persistent indicators (already normalized)
            # We want to re-check if it's very old, but for simplicity, we check cache.
            now = datetime.now(timezone.utc)
            
            # Check cache
            cache_entry = db.query(ThreatIntelCache).filter(
                ThreatIntelCache.indicator == indicator,
                ThreatIntelCache.indicator_type == indicator_type,
                ThreatIntelCache.expires_at > now
            ).first()

            result = None
            if cache_entry:
                result = ThreatIntelResult(**cache_entry.result)
            else:
                # Cache miss, lookup provider
                result = await ti_client.lookup(indicator, indicator_type)
                if result.source not in ("ERROR", "UNAVAILABLE"):
                    # Save to cache
                    new_cache = ThreatIntelCache(
                        indicator=indicator,
                        indicator_type=indicator_type,
                        provider=result.source,
                        result=result.__dict__,
                        expires_at=now + timedelta(seconds=settings.TI_CACHE_TTL_SECONDS)
                    )
                    
                    # Overwrite existing cache if needed (handled simply by deleting old)
                    db.query(ThreatIntelCache).filter(
                        ThreatIntelCache.indicator == indicator,
                        ThreatIntelCache.indicator_type == indicator_type
                    ).delete()
                    
                    db.add(new_cache)
                    db.commit()

            # 2. Store normalized indicator if found (or NO_MATCH, but we only store real indicators to not pollute)
            # Actually, we should store even NO_MATCH to explicitly show it was checked?
            # The prompt says: "ThreatIntelIndicator... fields: malicious... confidence".
            # Let's store all results to link them to the alert.
            
            # Upsert ThreatIntelIndicator
            ti_record = db.query(ThreatIntelIndicator).filter(
                ThreatIntelIndicator.indicator == indicator,
                ThreatIntelIndicator.indicator_type == indicator_type
            ).first()

            if not ti_record:
                ti_record = ThreatIntelIndicator(
                    indicator=indicator,
                    indicator_type=indicator_type,
                    source=result.source,
                    malicious=result.malicious,
                    confidence=result.confidence,
                    reputation=result.reputation,
                    categories=result.categories,
                    first_seen_at=now,
                    last_seen_at=now
                )
                db.add(ti_record)
                db.commit()
                db.refresh(ti_record)
            else:
                ti_record.malicious = result.malicious
                ti_record.confidence = result.confidence
                ti_record.reputation = result.reputation
                ti_record.categories = result.categories
                ti_record.last_seen_at = now
                ti_record.source = result.source
                db.commit()
            
            new_ti_indicators.append(ti_record)

        # Link to alert
        for ti_ind in new_ti_indicators:
            link_exists = db.query(AlertThreatIntel).filter(
                AlertThreatIntel.alert_id == alert.id,
                AlertThreatIntel.threat_intel_indicator_id == ti_ind.id
            ).first()
            if not link_exists:
                db.add(AlertThreatIntel(alert_id=alert.id, threat_intel_indicator_id=ti_ind.id))
                
            # Trigger notification if malicious match is found
            if ti_ind.malicious:
                trigger_ti_match(db, alert, ti_ind.indicator, ti_ind.indicator_type, ti_ind.source)
        
        db.commit()

        # Re-score alert
        if new_ti_indicators:
            from app.risk.engine import RiskScoringEngine
            RiskScoringEngine.recalculate_alert_risk(db, alert.id)

    @staticmethod
    async def manual_lookup(db: Session, indicator: str, indicator_type: str) -> ThreatIntelResult:
        now = datetime.now(timezone.utc)
        
        # Check cache
        cache_entry = db.query(ThreatIntelCache).filter(
            ThreatIntelCache.indicator == indicator,
            ThreatIntelCache.indicator_type == indicator_type,
            ThreatIntelCache.expires_at > now
        ).first()

        if cache_entry:
            return ThreatIntelResult(**cache_entry.result)

        result = await ti_client.lookup(indicator, indicator_type)
        if result.source not in ("ERROR", "UNAVAILABLE"):
            new_cache = ThreatIntelCache(
                indicator=indicator,
                indicator_type=indicator_type,
                provider=result.source,
                result=result.__dict__,
                expires_at=now + timedelta(seconds=settings.TI_CACHE_TTL_SECONDS)
            )
            
            db.query(ThreatIntelCache).filter(
                ThreatIntelCache.indicator == indicator,
                ThreatIntelCache.indicator_type == indicator_type
            ).delete()
            
            db.add(new_cache)
            db.commit()

        return result
