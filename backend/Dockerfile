FROM python:3.13-slim as requirements-stage

WORKDIR /tmp

# Install only required dependencies for psycopg2 and other build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r requirements.txt

FROM python:3.13-slim as production-stage

WORKDIR /app

# Install runtime dependencies for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy built wheels from requirements-stage
COPY --from=requirements-stage /tmp/wheels /tmp/wheels
COPY --from=requirements-stage /tmp/requirements.txt /tmp/requirements.txt

# Install dependencies from wheels
RUN pip install --no-cache-dir /tmp/wheels/* && \
    rm -rf /tmp/wheels /tmp/requirements.txt

# Create a non-root user
RUN useradd -m -d /app -s /bin/bash sentinelsoc && \
    chown -R sentinelsoc:sentinelsoc /app

USER sentinelsoc

# Copy application code
COPY --chown=sentinelsoc:sentinelsoc . /app/

# Expose backend port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1

# Run Uvicorn worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
