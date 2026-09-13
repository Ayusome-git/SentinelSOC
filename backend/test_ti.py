import asyncio
import os
import sys

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.threat_intel.extractor import IndicatorExtractionService
from app.models.security_event import SecurityEvent
from app.threat_intel.client import ti_client

async def main():
    print("--- Testing Indicator Extraction ---")
    event = SecurityEvent(
        source_ip="203.0.113.10",
        request_path="/download/a3b1c5d7e8f0a3b1c5d7e8f0a3b1c5d7e8f0a3b1c5d7e8f0a3b1c5d7e8f0a3b1",
        message="Suspicious connection from 198.51.100.42 to our server."
    )
    
    indicators = IndicatorExtractionService.extract_from_event(event)
    print(f"Extracted {len(indicators)} indicators:")
    for ind, itype in indicators:
        print(f" - {itype}: {ind}")

    print("\n--- Testing TI Provider (Mock) ---")
    import app.core.config
    app.core.config.settings.TI_ENABLED = True
    app.core.config.settings.TI_PROVIDER = "mock"

    for ind, itype in indicators:
        print(f"Looking up {ind} ({itype})...")
        result = await ti_client.lookup(ind, itype)
        print(f"  Found: {result.found}, Malicious: {result.malicious}, Confidence: {result.confidence}, Source: {result.source}")
        
    print("\nLooking up a known malicious indicator ('malicious_domain.com')...")
    result = await ti_client.lookup("malicious_domain.com", "DOMAIN")
    print(f"  Found: {result.found}, Malicious: {result.malicious}, Confidence: {result.confidence}")

if __name__ == "__main__":
    asyncio.run(main())
