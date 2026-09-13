from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ThreatIntelResult:
    found: bool
    indicator: str
    indicator_type: str
    malicious: bool = False
    confidence: int = 0
    reputation: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    source: str = "unknown"
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    reference: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

class ThreatIntelligenceProvider(ABC):
    """
    Base class for all external threat intelligence providers.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the TI provider."""
        pass

    @abstractmethod
    async def lookup_ip(self, ip: str) -> ThreatIntelResult:
        pass

    @abstractmethod
    async def lookup_domain(self, domain: str) -> ThreatIntelResult:
        pass

    @abstractmethod
    async def lookup_url(self, url: str) -> ThreatIntelResult:
        pass

    @abstractmethod
    async def lookup_hash_sha256(self, hash_value: str) -> ThreatIntelResult:
        pass
