import re
from typing import List, Tuple, Set
from app.models.security_event import SecurityEvent

class IndicatorExtractionService:
    # Basic indicator patterns
    IPV4_REGEX = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    SHA256_REGEX = re.compile(r'\b[A-Fa-f0-9]{64}\b')

    @classmethod
    def extract_from_event(cls, event: SecurityEvent) -> List[Tuple[str, str]]:
        """
        Safely extract indicators from a SecurityEvent.
        Returns a list of tuples: (indicator, indicator_type)
        """
        indicators: Set[Tuple[str, str]] = set()

        # 1. Source IP is a direct indicator
        if event.source_ip:
            if cls.IPV4_REGEX.match(event.source_ip):
                indicators.add((event.source_ip, "IP_ADDRESS"))

        # 2. Extract from request_path (e.g. searching for hashes or domains)
        # For safety and speed, we will only extract clear SHA256 hashes from paths
        if event.request_path:
            for match in cls.SHA256_REGEX.findall(event.request_path):
                indicators.add((match, "HASH_SHA256"))
        
        # 3. Extract from message if present
        if event.message:
            # Avoid overly broad regex; specifically look for IPs and Hashes for now
            for ip in cls.IPV4_REGEX.findall(event.message):
                # Don't add local/private IPs (naive check for demo)
                if not ip.startswith(("10.", "192.168.", "127.", "172.")):
                    indicators.add((ip, "IP_ADDRESS"))
            
            for h in cls.SHA256_REGEX.findall(event.message):
                indicators.add((h, "HASH_SHA256"))

        return list(indicators)
