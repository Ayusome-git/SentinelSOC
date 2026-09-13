# SentinelSOC Security Hardening

This document summarizes the security hardening measures implemented in SentinelSOC.

## 1. Authentication & Brute-Force Protection
- **In-Memory Rate Limiting**: An API rate limiter has been applied to sensitive endpoints (e.g., `POST /api/v1/auth/login`) using an in-memory token bucket. It allows 10 attempts per IP per 5 minutes by default (`AUTH_MAX_ATTEMPTS`, `AUTH_LOCKOUT_SECONDS`).
- **Generic Errors**: Login failures provide generic messages ("Invalid email or password") regardless of whether the user exists, preventing user enumeration.
- **Audit Logging**: Successful and failed logins, as well as logouts, generate explicit audit logs.
- **Password Policy**: New and updated passwords require a strict minimum length of 12 characters.

## 2. Authorization & Tenant Isolation
- **IDOR Protection**: The `deps.check_app_access` and `deps.filter_query_by_app_access` dependencies ensure that users (Analyst/Viewer) can only interact with alerts, incidents, events, and correlations for applications they explicitly own. Requests for unauthorized tenant data return `403 Forbidden` or `404 Not Found`.

## 3. Event Ingestion Hardening
- **Payload Bounding**: The `POST /api/v1/events` endpoint restricts maximum payload sizes via `MAX_EVENT_PAYLOAD_BYTES` to prevent memory/DoD exhaustion.
- **JSONB Hardening**: Metadata nested depth is restricted to 5 levels, max 50 keys, and a maximum string length of 4096 to prevent pathological database queries and JSON parsing crashes.
- **Rate Limiting**: Event ingestion is rate-limited.

## 4. API Keys & Applications
- API keys are securely hashed using constant-time hashing before storage. Raw keys are never stored and are only provided once upon generation.
- Application context is strictly tied to the verified API key and cannot be spoofed by the client.

## 5. Defense-in-Depth & Reporting
- **Security Headers**: Strict security headers have been added, including a tight `Content-Security-Policy` and `Strict-Transport-Security`.
- **CSV Injection Prevention**: Export functions actively sanitize `=` `+` `-` and `@` prefixes with single quotes (`'`) to prevent CSV formula injection in spreadsheet applications.
- **Response Action Safety**: Idempotent response validation ensures actions cannot be executed twice, executed without approval, or modified during execution. Auto-response is explicitly disabled by default.

## 6. Secrets Management
- All sensitive configurations (Database URL, Secret Key, API Keys, etc.) are strictly loaded via `pydantic-settings` from environment variables. No secrets are hardcoded in the codebase.

## 7. Dependency Auditing
- **Backend**: Audited via `pip-audit`. Known vulnerabilities found only in the `pip` package manager itself (development dependency, no runtime impact).
- **Frontend**: Audited via `npm audit`. Discovered vulnerabilities in `next` and `postcss`. An upgrade would require breaking changes (`next@16.x`). To prevent breaking the frontend, these vulnerabilities have been documented as accepted risks in the current runtime environment, pending a major framework upgrade.
