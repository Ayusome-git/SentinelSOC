# SentinelSOC Data Flow

This document details the complete lifecycle of a security event as it moves through the SentinelSOC pipeline. 

## 1. Event Generation
An external application (e.g., a web service, firewall, or IAM provider) detects an actionable activity such as a failed login, an administrative action, or a rate-limit breach. The application formats this into a JSON payload.

## 2. Authentication & Ingestion
The external application calls the SentinelSOC API `POST /api/v1/events` endpoint, authenticating via a scoped **API Key** placed in the Authorization header. SentinelSOC validates the token, identifying which registered Application the event belongs to.

## 3. Validation & Normalization
SentinelSOC validates the incoming payload against strict Pydantic schemas. The event is normalized into a standard structure, ensuring critical fields like `timestamp`, `event_type`, `severity`, and `source_ip` exist and are correctly formatted.

## 4. Persistence
The raw event is written to the PostgreSQL database for historical retention and audit logging.

## 5. Detection Evaluation
The **Detection Engine** immediately evaluates the new event against active, enabled Rules. It checks for thresholds within specified time windows (e.g., *Has this Source IP triggered 5 failed logins in the last 5 minutes?*).

## 6. Alert Creation
If a detection threshold is met, the engine generates an **Alert**. The alert aggregates the original triggering events and tags the associated detection rule.

## 7. Correlation Analysis
The asynchronous **Correlation Engine** continuously scans active alerts. If it detects related patterns (e.g., a Brute Force Alert followed closely by a Successful Login event from the same IP), it links the activities to establish an attack chain.

## 8. Risk Calculation
The deterministic **Risk Scoring Engine** evaluates the new Alert or Correlation. It calculates a score from 0–100 based on severity, frequency, attack type, and contextual relevance. 

## 9. Incident Escalation
If the calculated Risk Score crosses the CRITICAL threshold (or if highly correlated alerts are detected), the system automatically escalates the issue by creating an **Incident**. This Incident becomes the central workspace for investigation.

## 10. Enrichment (Background)
- **Threat Intelligence**: If TI is enabled, the system looks up extracted indicators (like IPs) against providers (e.g., AlienVault). A positive match dynamically increases the risk score.
- **Machine Learning**: If sufficient data exists, the Isolation Forest model evaluates the event baseline, flagging severe statistical anomalies for analyst review.

## 11. Notification
The system dispatches internal notifications (and emails, if SMTP is enabled) to analysts and administrators based on their configured severity preferences.

## 12. Investigation & Response
An analyst reviews the Incident timeline. They identify the threat and initiate a **Response Action** (e.g., Lock User Account).

## 13. Approval & Execution
Because `AUTO_RESPONSE_ENABLED` is `false` by default, the action enters a `PENDING_APPROVAL` state. An Administrator reviews the request. Upon approval, SentinelSOC executes the integration webhook or script to isolate the threat on the external application.

## 14. Reporting
Finally, the lifecycle concludes when Security Reports are generated, aggregating the week's events, alerts, and incident metrics for compliance and managerial review.
