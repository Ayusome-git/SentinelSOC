# SentinelSOC Detection Matrix

This matrix documents the implemented, deterministic detection rules inside the SentinelSOC detection engine.

| Rule Name | Category | Event Type(s) | Threshold | Window | Grouping | Severity | Purpose / Scenario |
|-----------|----------|--------------|-----------|--------|----------|----------|-------------------|
| **Brute Force Login** | Authentication | `LOGIN_FAILED` | 5 | 5 mins | `source_ip` | HIGH | Detects an attacker attempting to guess passwords by rapidly submitting failed login requests from a single IP address. |
| **Distributed Brute Force** | Authentication | `LOGIN_FAILED` | 15 | 5 mins | `user` | CRITICAL | Detects a botnet attempting to brute-force a specific user account across multiple IP addresses. |
| **API Rate Limit Exceeded** | Abuse | `RATE_LIMIT` | 10 | 1 min | `source_ip` | MEDIUM | Detects potential denial of service (DoS) attempts or aggressive scraping bots. |
| **Suspicious Admin Activity** | Privilege | `ADMIN_ACTION` | 5 | 10 mins | `user` | HIGH | Detects anomalous bulk actions by an administrator, which may indicate account compromise or insider threat. |
| **Multiple Authorization Failures** | Access Control | `AUTH_FAILED` | 5 | 5 mins | `user` | MEDIUM | Detects an authenticated user probing for unauthorized access to restricted endpoints (e.g., IDOR/BOLA attempts). |
| **Suspicious Request Pattern** | Web Attack | `SUSPICIOUS_REQUEST` | 3 | 5 mins | `source_ip` | HIGH | Detects explicit attack payloads (like SQLi or XSS signatures) targeting application routes. |
| **Multiple Password Resets** | Account Takeover | `PASSWORD_RESET` | 3 | 15 mins | `user` | HIGH | Detects attackers attempting to bypass authentication through aggressive password reset workflows. |
| **Impossible Travel** | Authentication | `LOGIN_SUCCESS` | 2 | 4 hours | `user` | HIGH | Detects successful logins for a single user originating from vastly differing geographic regions (currently simulated via distinct IP subnets). |

> [!NOTE]
> These rules form the foundational **deterministic** detection layer. Machine Learning anomaly detection acts as an independent, secondary layer.
