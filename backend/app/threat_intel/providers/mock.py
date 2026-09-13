from app.threat_intel.provider import ThreatIntelligenceProvider, ThreatIntelResult
from datetime import datetime
import asyncio

class MockThreatIntelligenceProvider(ThreatIntelligenceProvider):
    @property
    def name(self) -> str:
        return "mock"

    async def _mock_lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        # Simulate network latency
        await asyncio.sleep(0.5)

        # Hardcoded demonstration indicators
        if indicator == "203.0.113.10":
            return ThreatIntelResult(
                found=True,
                indicator=indicator,
                indicator_type=indicator_type,
                malicious=True,
                confidence=87,
                reputation="malicious",
                categories=["Credential Abuse", "Brute Force"],
                source=self.name,
                last_seen_at=datetime.utcnow()
            )
        elif indicator == "198.51.100.42":
            return ThreatIntelResult(
                found=True,
                indicator=indicator,
                indicator_type=indicator_type,
                malicious=False,
                confidence=0,
                reputation="benign",
                categories=[],
                source=self.name,
                last_seen_at=datetime.utcnow()
            )
        elif "malicious" in indicator.lower():
            return ThreatIntelResult(
                found=True,
                indicator=indicator,
                indicator_type=indicator_type,
                malicious=True,
                confidence=95,
                reputation="malicious",
                categories=["Malware", "C2"],
                source=self.name,
                last_seen_at=datetime.utcnow()
            )
        
        # Default empty result
        return ThreatIntelResult(
            found=False,
            indicator=indicator,
            indicator_type=indicator_type,
            source=self.name
        )

    async def lookup_ip(self, ip: str) -> ThreatIntelResult:
        return await self._mock_lookup(ip, "IP_ADDRESS")

    async def lookup_domain(self, domain: str) -> ThreatIntelResult:
        return await self._mock_lookup(domain, "DOMAIN")

    async def lookup_url(self, url: str) -> ThreatIntelResult:
        return await self._mock_lookup(url, "URL")

    async def lookup_hash_sha256(self, hash_value: str) -> ThreatIntelResult:
        return await self._mock_lookup(hash_value, "HASH_SHA256")
