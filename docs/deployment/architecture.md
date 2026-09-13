# SentinelSOC Deployment Architecture

SentinelSOC uses a robust, scalable containerized architecture utilizing Docker and Docker Compose. This ensures environment consistency across development, testing, and production.

## Production Container Layout

```mermaid
flowchart TD
    Client([Client / Browser])
    
    subgraph Docker Network [SentinelSOC Production Network]
        NGINX[NGINX Reverse Proxy\n:80 / :443]
        Frontend[Next.js Frontend\n(Standalone)]
        Backend[FastAPI Backend\n(Uvicorn Workers)]
        Postgres[(PostgreSQL 15)]
        
        NGINX -->|/| Frontend
        NGINX -->|/api/| Backend
        Backend <--> Postgres
    end
    
    Client <-->|HTTPS| NGINX
```

### Components

1. **NGINX Reverse Proxy (`nginx`)**:
   - Acts as the single entry point.
   - Handles SSL/TLS termination (when configured).
   - Routes `/` traffic to the Frontend container.
   - Routes `/api/` traffic to the Backend container.
   - Enforces rate limits, body size limits, and security headers.

2. **Next.js Frontend (`frontend`)**:
   - Compiled as a standalone Node.js application for reduced image size.
   - Only accessible internally via the NGINX reverse proxy.
   - Connects to the backend via the `NEXT_PUBLIC_API_URL` which goes through NGINX.

3. **FastAPI Backend (`backend`)**:
   - Python 3.13 slim container.
   - Runs `uvicorn` with multiple workers (configurable).
   - Only accessible internally via NGINX.
   - Contains ML models mapped to a persistent volume.

4. **PostgreSQL (`postgres`)**:
   - Official PostgreSQL 15 alpine image.
   - Houses all operational, relational, and event data.
   - Strictly internal network (no exposed ports in production).
   - Data stored in a persistent Docker volume (`postgres_data_prod`).

### Persistent Storage

In a production environment, the following data must be persisted across container restarts:
- **`postgres_data_prod`**: The relational database volume containing all application state, security events, users, incidents, and RBAC configurations.
- **`ml_models_data_prod`**: The local filesystem directory where Scikit-Learn models are cached and stored after training runs.

### Health Checks and Dependencies

Startup sequence and reliability are guaranteed via Docker Healthchecks:
- `backend` waits for `postgres` to become fully ready (`pg_isready`).
- `frontend` waits for `backend`.
- `nginx` waits for both `frontend` and `backend`, and performs its own loopback healthcheck (`/health`).
