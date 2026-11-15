# SentinelSOC Correlation Matrix

The Correlation Engine asynchronously links distinct events and alerts over time to construct logical attack chains. This context prevents alert fatigue by bundling related activities into a single actionable Incident.

| Correlation Pattern | Sequence / Requirements | Time Window | Resulting Severity | Purpose / Scenario |
|---------------------|------------------------|-------------|--------------------|-------------------|
| **Brute Force → Successful Login** | 1. `Brute Force Login` (Alert)<br>2. `LOGIN_SUCCESS` (Event)<br>*Must share identical User ID or Source IP* | 30 minutes | CRITICAL | Identifies an attacker successfully guessing a password and gaining initial access to the system. |
| **Privilege Escalation Chain** | 1. `LOGIN_SUCCESS`<br>2. `ADMIN_LOGIN`<br>3. `ADMIN_ACTION`<br>*Must share identical Source IP* | 15 minutes | CRITICAL | Identifies a rapid sequence of access escalation leading to immediate administrative abuse. |
| **Compromised Admin Account** | 1. `Brute Force Login` (Alert) OR `LOGIN_SUCCESS`<br>2. `ADMIN_ACTION` (Event)<br>*Must share identical User ID* | 1 hour | CRITICAL | Identifies an attacker pivoting immediately to administrative actions following a login. |
| **Web Attack → API Abuse** | 1. `Suspicious Request Pattern` (Alert)<br>2. `RATE_LIMIT` (Event) OR high API volume<br>*Must share identical Source IP* | 10 minutes | HIGH | Identifies automated exploitation tools aggressively probing for web vulnerabilities (like SQLi or Directory Traversal). |
| **Insider Threat / BOLA Probe** | 1. `Multiple Authorization Failures` (Alert)<br>2. `ADMIN_ACTION` (Event) | 30 minutes | HIGH | Identifies an authenticated user who probed restricted endpoints, failed, and then eventually executed an administrative action (indicating a potential bypass). |

## Correlation Logic
Correlations are evaluated asynchronously via background tasks (`app.workers.correlation_worker`). When a correlation is matched, the engine:
1. Links the participating entities.
2. Creates an `Incident` encompassing all evidence.
3. Automatically triggers a recalculation in the Risk Engine.
