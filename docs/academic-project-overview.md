# SentinelSOC — AI-Powered Mini Security Operations Center

## 1. Problem Statement
Modern web applications, especially those built on decentralized architectures, generate massive amounts of log data. However, these logs are often fragmented, difficult to analyze, and lack security context. Development teams struggle to detect and respond to active threats (like brute-force attacks or privilege escalation) in real-time because they lack a centralized, application-agnostic Security Operations Center (SOC) platform.

## 2. Proposed Solution
SentinelSOC is a centralized, application-agnostic Security Operations Center platform. It provides a standardized API for any external application to ingest security events. SentinelSOC normalizes these events, evaluates them against deterministic detection rules, correlates related attacks, calculates risk scores, and optionally enriches the data using Machine Learning and external Threat Intelligence.

## 3. Objectives
- **Centralized Ingestion**: Provide a secure, API-driven pipeline for security event ingestion.
- **Application-Independent Monitoring**: Isolate applications via RBAC and API Keys, allowing multiple distinct apps to use the same SOC.
- **Rule-Based Threat Detection**: Implement deterministic thresholds to identify attacks.
- **Event Correlation**: Automatically link disparate events into cohesive attack chains.
- **Explainable Risk Scoring**: Calculate a deterministic 0–100 risk score.
- **ML Anomaly Detection**: Utilize Isolation Forests to detect baseline deviations.
- **Incident Management**: Provide a workspace for analysts to investigate threats.
- **Controlled Response**: Implement a human-in-the-loop approval workflow for isolating threats (e.g., blocking IPs).

## 4. System Architecture
SentinelSOC is composed of three main layers:
1. **Frontend**: A Next.js standalone application optimized for high-performance dashboarding.
2. **Backend**: A FastAPI Python application providing high-concurrency event ingestion, detection, and asynchronous correlation.
3. **Database**: A PostgreSQL relational database storing normalized events, rules, configurations, and state.

## 5. Technologies Used
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Recharts.
- **Backend**: Python 3.13, FastAPI, Pydantic, SQLAlchemy, Alembic.
- **Database**: PostgreSQL 15.
- **Infrastructure**: Docker, Docker Compose, NGINX.
- **Security**: JWT Authentication, Argon2id Password Hashing, RBAC, API Keys.
- **Machine Learning**: scikit-learn (Isolation Forest).

## 6. Security Features
- Strict Tenant Isolation (BOLA/IDOR protection).
- Deterministic, scoped API Key Authentication for applications.
- JWT-based Analyst and Administrator Authentication.
- In-memory rate limiting and payload size restrictions.

## 7. Limitations
- **Scaling**: Currently relies on a single PostgreSQL instance. Extreme event volumes (e.g., millions per minute) would require a distributed message queue (like Kafka) and an indexing engine (like Elasticsearch).
- **Machine Learning Cold Start**: The ML models require significant historical data to establish a baseline before providing value.

## 8. Future Work
- **Richer Detection DSL**: Implement a Domain Specific Language (DSL) to allow analysts to write highly complex custom detection rules.
- **SIEM Integrations**: Add webhook forwarding to push aggregated incidents into enterprise SIEMs (like Splunk or Sentinel).
- **Advanced Behavioral Analytics**: Expand ML capabilities beyond Isolation Forests to include recurrent neural networks for sequence prediction.
