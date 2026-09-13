import asyncio
import logging
from app.threat_intel.provider import ThreatIntelligenceProvider, ThreatIntelResult
from app.threat_intel.providers.mock import MockThreatIntelligenceProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class ThreatIntelProviderClient:
    def __init__(self):
        self.provider: ThreatIntelligenceProvider = self._load_provider()
        
    def _load_provider(self) -> ThreatIntelligenceProvider:
        if settings.TI_PROVIDER.lower() == "mock":
            return MockThreatIntelligenceProvider()
        # TODO: Return AlienVault / actual provider if configured
        logger.warning(f"Provider {settings.TI_PROVIDER} not implemented or misconfigured. Falling back to Mock.")
        return MockThreatIntelligenceProvider()

    async def lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        if not settings.TI_ENABLED:
            return ThreatIntelResult(found=False, indicator=indicator, indicator_type=indicator_type, source="disabled")

        try:
            # Enforce strict timeout from config
            return await asyncio.wait_for(
                self._dispatch_lookup(indicator, indicator_type),
                timeout=settings.TI_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            logger.error(f"TI lookup timed out for {indicator}")
            # Unavailable state simulated with source=UNAVAILABLE
            return ThreatIntelResult(found=False, indicator=indicator, indicator_type=indicator_type, source="UNAVAILABLE")
        except Exception as e:
            logger.error(f"TI provider error for {indicator}: {e}")
            return ThreatIntelResult(found=False, indicator=indicator, indicator_type=indicator_type, source="ERROR")

    async def _dispatch_lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        if indicator_type == "IP_ADDRESS":
            return await self.provider.lookup_ip(indicator)
        elif indicator_type == "DOMAIN":
            return await self.provider.lookup_domain(indicator)
        elif indicator_type == "URL":
            return await self.provider.lookup_url(indicator)
        elif indicator_type == "HASH_SHA256":
            return await self.provider.lookup_hash_sha256(indicator)
        else:
            raise ValueError(f"Unsupported indicator type: {indicator_type}")

ti_client = ThreatIntelProviderClient()
