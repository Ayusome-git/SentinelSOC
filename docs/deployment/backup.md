# Backup and Restore Strategy

This document outlines the procedures for backing up and restoring SentinelSOC's critical data components.

## What Needs Backing Up

SentinelSOC is primarily stateless at the application layer, with two notable exceptions:
1. **PostgreSQL Database**: Contains all configurations, users, incidents, alerts, events, and ML models logic.
2. **ML Models Directory**: If local filesystem persistence is used, compiled `.pkl` files reside here.

## 1. Backing Up PostgreSQL

PostgreSQL is the absolute source of truth. You should back it up regularly.

### Taking a Backup

Use `pg_dump` via the running Postgres container:

```bash
docker exec -t sentinelsoc_postgres_prod pg_dumpall -c -U sentinelsoc > sentinelsoc_backup_$(date +%Y%m%d).sql
```
*Note: Replace `sentinelsoc` with your `POSTGRES_USER`.*

> [!TIP]
> **Automate this process:** Setup a `cron` job on the host machine to execute this command nightly and move the `.sql` artifact to an off-site S3 bucket or cold storage.

### Restoring a Backup

If a disaster recovery scenario occurs, restore using the following procedure:

1. Copy the backup file to the host running the database.
2. Start the fresh Postgres container (without starting the backend to avoid conflicts):
   ```bash
   docker compose -f docker-compose.prod.yml up -d postgres
   ```
3. Pipe the SQL dump into the running container:
   ```bash
   cat sentinelsoc_backup_20260913.sql | docker exec -i sentinelsoc_postgres_prod psql -U sentinelsoc
   ```
4. Start the rest of the stack:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

## 2. Backing up ML Models

If the ML subsystem has generated heavy serialized models, back up the volume data.

```bash
# Example backup using a temporary alpine container to tar the volume
docker run --rm \
  --volumes-from sentinelsoc_backend_prod \
  -v $(pwd):/backup \
  alpine tar cvf /backup/ml_models_$(date +%Y%m%d).tar /app/ml_models
```

> [!NOTE]
> If ML models are lost, they can be entirely retrained from historical database events. The loss of models will result in temporary CPU overhead during retraining, but no absolute data loss.

## Secure Storage

- **NEVER** expose backups over the public internet via NGINX.
- **NEVER** commit `.sql` files or `.env` files into Git.
- Ensure backups are encrypted at rest on the storage medium.
