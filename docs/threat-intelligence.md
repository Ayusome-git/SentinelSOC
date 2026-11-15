# Threat Intelligence

SentinelSOC abstracts Threat Intelligence (TI) lookups to enrich raw security events with known malicious indicators (e.g., matching a Source IP against a known botnet list).

## Supported Indicators
Currently, SentinelSOC supports extraction and lookup of **IPv4 / IPv6 addresses**. 

> [!WARNING]
> **Data Privacy & Security**: Passwords, authentication tokens, API keys, and session cookies are explicitly ignored and **never** transmitted to external Threat Intelligence providers.

## Provider Abstraction
The system uses a factory pattern to integrate with different TI providers.
- **Mock Provider**: Used for development and demonstrations. Returns deterministic synthetic results without making network calls.
- **AlienVault OTX / VirusTotal**: (Configurable via `.env` plugins) Used in production environments with valid API keys.

## Architecture Flow
1. **Extraction**: During event ingestion, an asynchronous task scans the payload for valid IP addresses.
2. **Caching (TTL)**: The system first checks the local PostgreSQL caching layer to see if the IP was queried recently (e.g., within the last 1 hour). This prevents rate-limiting by the external TI provider.
3. **Lookup**: If a cache miss occurs, the provider executes a network call to the external TI API.
4. **Enrichment**: The resulting data (match boolean, reputation score, provider name) is persisted to the database and linked to the event.

## Failure Isolation
Network calls to external providers are inherently brittle. SentinelSOC implements:
- Strict timeouts (`TI_TIMEOUT_SECONDS`).
- Try/Catch isolation.
If a TI provider is unavailable, the event is silently logged as un-enriched, and the main ingestion pipeline continues without disruption or data loss.

## SSRF Protections
SentinelSOC strictly prevents Server-Side Request Forgery (SSRF) when interacting with external APIs. All HTTP clients are restricted to explicitly whitelisted domains defined within the TI Provider implementations. External inputs cannot manipulate the target URL of the lookup.
