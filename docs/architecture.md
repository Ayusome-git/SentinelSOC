# SentinelSOC Architecture

SentinelSOC is a centralized Security Operations Center (SOC) platform designed to ingest, process, correlate, and respond to security events from any external application. It is strictly application-agnostic, providing security teams with a unified interface to investigate threats across the entire organization.

## System Architecture

```mermaid
flowchart TD
    ExternalApp([External Web App\nReact / Node / etc.])
    
    subgraph SentinelSOC
        API[SentinelSOC API]
        
        subgraph Pipeline [Event Pipeline]
            Ingestion[Event Ingestion & Normalization]
            Detection[Detection Engine\n(Rule-Based)]
            Correlation[Correlation Engine]
            Risk[Risk Scoring Engine]
            IncidentMgr[Incident Management]
        end
        
        subgraph Enrichment
            ML[ML Anomaly Detection]
            TI[Threat Intelligence]
        end
        
        subgraph Actions
            Response[Response Actions]
            Notifications[Notifications & SMTP]
            Reports[Reporting]
        end
        
        DB[(PostgreSQL)]
        
        API --> Ingestion
        Ingestion --> Detection
        Detection --> Correlation
        Correlation --> Risk
        Risk --> IncidentMgr
        
        Detection -.-> ML
        Correlation -.-> TI
        
        IncidentMgr --> Response
        IncidentMgr --> Notifications
        
        Pipeline <--> DB
        Enrichment <--> DB
        Actions <--> DB
    end
    
    ExternalApp -- "API Key Auth" --> API
```

## Core Components

### 1. Application Isolation & Authentication
SentinelSOC identifies origin applications using scoped **API Keys**. The backend enforces strict RBAC (Role-Based Access Control) ensuring that:
- External applications can only ingest events, not read them.
- Analysts can only view data.
- Admins can manage the platform.

### 2. Event Flow & Normalization
Events are ingested via the `/api/v1/events` endpoint. SentinelSOC normalizes timestamps, source IPs, and severities into a standard taxonomy, allowing it to process events from firewalls, web apps, and endpoints uniformly.

### 3. Detection Engine
The Detection Engine evaluates normalized events against a set of threshold-based rules (e.g., "5 failed logins within 5 minutes grouped by source IP"). If a threshold is crossed, an **Alert** is generated.

### 4. Correlation Engine
The Correlation Engine runs asynchronously to identify relationships between disparate Alerts and Events over time (e.g., "Brute Force" followed by "Successful Admin Login"). This pieces together the attack chain.

### 5. Risk Scoring
Every Alert and Incident is passed through a deterministic 0–100 risk scoring engine that factors in event severity, frequency, threat intelligence matches, and application criticality.

### 6. Incident Management
Highly correlated alerts or critical risk scores result in the creation of an **Incident**. Incidents provide a unified workspace timeline for analysts to investigate the attack chain.

### 7. Enrichment (ML & TI)
- **Machine Learning**: An Isolation Forest model identifies anomalous behavior based on historical baselines (e.g., unexpected API spikes).
- **Threat Intelligence**: A TI provider abstraction resolves Source IPs against known malicious databases, caching the results to prevent rate-limiting and latency.

### 8. Response Model
SentinelSOC operates on a **Human-In-The-Loop** response model:
1. Analyst requests an action (e.g., Block IP).
2. Action is pending until an Admin approves.
3. Action executes safely, with idempotency guarantees.

### 9. Docker Deployment
The system is fully containerized, relying on a Next.js (Standalone) frontend, a FastAPI (Uvicorn) backend, and a PostgreSQL database, shielded by an NGINX reverse proxy.
