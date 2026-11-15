# SentinelSOC

SentinelSOC is a high-performance, application-agnostic Security Operations Center (SOC) designed to centralize event logging, automate threat detection, and provide a unified investigation workspace for security analysts.

## Features
- **Centralized Event Ingestion**: A robust REST API for ingesting normalized security events from any external application.
- **Application Isolation**: Strict Multi-Tenant isolation using scoped API Keys and RBAC.
- **Rule-Based Threat Detection**: Deterministic evaluation of events against threshold-based rules (e.g., Brute Force, Impossible Travel, API Spikes).
- **Automated Event Correlation**: Asynchronous background workers stitch together distinct events into cohesive attack chains.
- **Deterministic Risk Scoring**: Explainable `0-100` scoring engine prioritizing critical threats.
- **ML Anomaly Detection**: Unsupervised `Isolation Forest` models detect statistical deviations from normal baselines.
- **Threat Intelligence**: Out-of-the-box IP indicator enrichment via integrations with AlienVault and VirusTotal.
- **Controlled Response Actions**: Human-in-the-loop approval workflows for executing containment actions (e.g., IP Blocks, User Lockouts) back onto the originating application.
- **Reporting & Notifications**: Automated email notifications and PDF/CSV security posture reporting.

## Architecture
SentinelSOC separates concerns cleanly across three primary layers:
1. **Frontend (Next.js)**: A high-performance, Tailwind-styled, responsive dashboard for analysts and administrators.
2. **Backend (FastAPI)**: A high-concurrency Python engine handling ingestion validation, asynchronous correlation tasks, ML training, and API logic.
3. **Database (PostgreSQL)**: The relational source-of-truth storing all events, rules, ML states, and incident histories.

*For detailed architectural diagrams and data flows, see the `/docs` folder.*

## Technology Stack
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui.
- **Backend**: Python 3.13, FastAPI, SQLAlchemy (asyncio), Pydantic, scikit-learn.
- **Infrastructure**: Docker, NGINX, PostgreSQL 15.

## Project Structure
```
SentinelSOC/
├── backend/            # FastAPI application and ML services
├── frontend/           # Next.js React application
├── docker/             # Container configurations (NGINX)
├── docs/               # Architecture, Academic, and Deployment documentation
├── docker-compose.yml  # Local development stack
└── .env.example        # Environment variable definitions
```

## Quick Start (Development)
Ensure Docker and Docker Compose are installed on your machine.

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Update SECRET_KEY and POSTGRES_PASSWORD in .env
   ```
2. **Start the Stack:**
   ```bash
   docker compose up -d
   ```
3. **Run Initial Database Migrations:**
   ```bash
   docker exec -it sentinelsoc_backend_dev alembic upgrade head
   ```
4. **Create First Administrator:**
   ```bash
   docker exec -it sentinelsoc_backend_dev python -m app.scripts.create_admin
   ```
5. **Access the Dashboard:**
   Navigate to `http://localhost:3000` and login with your new admin credentials.

## Demo
SentinelSOC includes a safe, deterministic synthetic attack generator designed for academic presentations and product demonstrations. It generates realistic brute-force and privilege escalation chains without targeting external systems.

Please read `docs/demo/runbook.md` for complete demonstration instructions.

## API Documentation
Once the backend is running, the interactive Swagger OpenAPI documentation is available at:
- `http://localhost:8000/docs`

## Production Deployment
SentinelSOC is containerized for immediate production deployment using `docker-compose.prod.yml`. 
For strict security guidelines, HTTPS termination, and backup strategies, refer to `docs/deployment/production.md`.

## Security
This project enforces:
- Argon2id Password Hashing.
- JWT Authentication (Short-lived tokens).
- IDOR / BOLA tenant isolation.
- Internal rate-limiting and payload size caps.
- Strict SSRF protections on Threat Intelligence integrations.

## Project Status
**Phase 26 Complete - Real-World Attack Simulation and SOC Validation completed. Ready for final deployment and academic defense.
