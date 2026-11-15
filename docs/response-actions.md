# Response Actions & Security Architecture

SentinelSOC provides a controlled response framework, allowing analysts to isolate threats directly on the integrated applications. Because automated response can inadvertently cause severe denial of service, SentinelSOC enforces a strict **Human-in-the-Loop** approval architecture.

## Supported Safe Actions
Applications explicitly register their supported response capabilities during onboarding. SentinelSOC only supports predefined, safe enumerations:
- `BLOCK_SOURCE_IP`: Instructs the application to reject traffic from a specific IP.
- `LOCK_USER`: Instructs the application to freeze a user account.
- `REVOKE_SESSION`: Immediately terminates an active user session.
- `RATE_LIMIT_SOURCE`: Throttles requests from a specific IP or User.
- `DISABLE_API_ACCESS`: Revokes an application-level API token.

> [!CAUTION]
> Arbitrary remote code execution, arbitrary SQL execution, or arbitrary webhook triggers are explicitly disallowed by the framework to prevent SentinelSOC from being used as an attack vector.

## The Response Lifecycle

### 1. Analyst Request
An Analyst identifies a threat (e.g., a Brute Force incident) and initiates a Response Action (e.g., Block IP). The action is recorded in the database in a `PENDING_APPROVAL` state.

### 2. Admin Approval
An Administrator reviews the pending action. They can either:
- **Approve**: Transitioning the state to `EXECUTING`.
- **Reject**: Terminating the workflow.

> [!NOTE]
> `AUTO_RESPONSE_ENABLED` is `false` by default. If explicitly configured to `true` via `.env`, specific high-confidence rules can bypass the Administrator approval step. This is not recommended for most deployments.

### 3. Execution & Validation
SentinelSOC attempts to execute the action via the registered application's designated webhook or API endpoint. 
- The system enforces a strict timeout (`RESPONSE_ACTION_TIMEOUT_SECONDS`).
- Idempotency keys are used to ensure actions are not duplicated during network retries.

### 4. Audit Logging
Every state transition (Request, Approval, Execution, Success, Failure) is durably recorded in the SentinelSOC database, mapped to the requesting Analyst and approving Administrator.
