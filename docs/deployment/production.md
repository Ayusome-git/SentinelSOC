# Production Deployment Guide

This guide details the procedure for deploying SentinelSOC in a production environment using Docker Compose.

## Prerequisites

1. A server with Docker and Docker Compose installed.
2. At least 4GB of RAM (8GB+ recommended for ML and Postgres caching).
3. (Optional but recommended) A valid Domain Name and SSL certificates.

## First Deployment Workflow

### 1. Configure the Environment
Copy the example environment file and secure it:
```bash
cp .env.example .env.prod
```
> [!CAUTION]
> **Generate a strong secret key:**
> `openssl rand -hex 32`
> Replace the `SECRET_KEY` value in `.env.prod`.

Set the following variables in `.env.prod`:
- `ENVIRONMENT=production`
- `POSTGRES_PASSWORD` (use a strong random password)
- `DATABASE_URL` (update with the new password)
- `NEXT_PUBLIC_API_URL` (set to your public NGINX domain, e.g. `https://soc.example.com/api/v1`)
- `BACKEND_CORS_ORIGINS` (e.g. `["https://soc.example.com"]`)

### 2. Configure HTTPS (Highly Recommended)
Place your fullchain and private key on the host machine. Open `docker-compose.prod.yml` and uncomment the NGINX certificate mounts:
```yaml
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt/live/soc.example.com/fullchain.pem:/etc/nginx/certs/fullchain.pem:ro
      - /etc/letsencrypt/live/soc.example.com/privkey.pem:/etc/nginx/certs/privkey.pem:ro
```
You will also need to update `docker/nginx/nginx.conf` to handle `ssl_certificate` directives on port 443.

### 3. Build and Start
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```
> [!TIP]
> Use `docker compose -f docker-compose.prod.yml logs -f` to monitor the startup process.

### 4. Run Database Migrations
> [!WARNING]
> Migrations do not run automatically to prevent race conditions across multiple worker nodes in a scaled environment.
Run Alembic migrations manually once the backend container is running:
```bash
docker exec -it sentinelsoc_backend_prod alembic upgrade head
```

### 5. Create Initial Administrator
Create your first administrator account to access the platform:
```bash
docker exec -it sentinelsoc_backend_prod python -m app.scripts.create_admin
```
Follow the prompts to configure the admin email and password.

## Safe Update Strategy

When a new version of SentinelSOC is released:

1. **Backup Database** (See `backup.md`).
2. Pull new code: `git pull origin main`
3. Build new images: `docker compose -f docker-compose.prod.yml build`
4. Review Alembic migrations: Check release notes for breaking database changes.
5. Deploy and restart: `docker compose -f docker-compose.prod.yml up -d`
6. Run migrations: `docker exec -it sentinelsoc_backend_prod alembic upgrade head`

## Security Checklist

- [ ] PostgreSQL port `5432` is NOT exposed in `docker-compose.prod.yml`.
- [ ] Backend debugging is disabled (`ENVIRONMENT=production`).
- [ ] `SECRET_KEY` is cryptographically random.
- [ ] CORS is explicitly locked down to your frontend origin.
- [ ] `AUTO_RESPONSE_ENABLED` is `False` unless explicitly understood and tested.
- [ ] NGINX security headers are active.
