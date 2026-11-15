from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.redis import close_redis, ping_redis, ensure_stream_group

logger = logging.getLogger(__name__)
from app.api.v1.endpoints import (
    health,
    auth,
    users,
    applications,
    events,
    dashboard,
    rules,
    correlations,
    alerts,
    incidents,
    ml,
    threat_intel,
    response_actions,
    response_capabilities,
    response_policies,
    notifications,
    reports,
)

tags_metadata = [
    {"name": "auth", "description": "Authentication operations (JWT)."},
    {"name": "users", "description": "User management operations."},
    {"name": "applications", "description": "Manage external applications and their API Keys."},
    {"name": "events", "description": "Event ingestion pipeline. Applications push events here."},
    {"name": "dashboard", "description": "Aggregated statistics for the SOC dashboard."},
    {"name": "rules", "description": "Configure deterministic detection thresholds."},
    {"name": "alerts", "description": "View and manage threshold breaches."},
    {"name": "correlations", "description": "View correlated attack chains."},
    {"name": "incidents", "description": "Workspace for managing escalated threats."},
    {"name": "ml", "description": "Unsupervised machine learning anomalies."},
    {"name": "threat_intelligence", "description": "Indicator enrichment details."},
    {"name": "response_actions", "description": "Safe human-in-the-loop response framework."},
    {"name": "notifications", "description": "Internal and email notification dispatch."},
    {"name": "reports", "description": "Generate and export compliance reports."},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting SentinelSOC API...")
    is_redis_up = await ping_redis()
    if is_redis_up:
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")
        try:
            await ensure_stream_group(settings.REDIS_STREAM_NAME, settings.REDIS_CONSUMER_GROUP)
        except Exception as exc:
            logger.warning(f"Could not initialize Redis stream/group: {exc}")
    else:
        logger.warning(f"Redis is not reachable at {settings.REDIS_URL}. Running in standalone mode.")
    yield
    # Shutdown
    logger.info("Shutting down SentinelSOC API...")
    await close_redis()

app = FastAPI(
    title="SentinelSOC API",
    version="1.0.0",
    description="AI-powered, application-agnostic Security Operations Center (SOC) platform API.",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' http://localhost:* ws://localhost:* wss://localhost:*;"
    # Enable HSTS only in production (don't break local HTTP development)
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# ---------------------------------------------------------------------------
# CORS — explicit methods and headers (no wildcards with credentials)
# ---------------------------------------------------------------------------
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
from app.api.v1.endpoints import dashboard
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
from app.api.v1.endpoints import rules
app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])
from app.api.v1.endpoints import correlations
app.include_router(correlations.router, prefix="/api/v1/correlations", tags=["correlations"])
from app.api.v1.endpoints import alerts
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
from app.api.v1.endpoints import incidents
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
from app.api.v1.endpoints import ml
app.include_router(ml.router, prefix="/api/v1/ml", tags=["ml"])
from app.api.v1.endpoints import threat_intel
app.include_router(threat_intel.router, prefix="/api/v1/threat-intelligence", tags=["threat_intelligence"])
app.include_router(response_actions.router, prefix="/api/v1/response-actions", tags=["response_actions"])
app.include_router(response_capabilities.router, prefix="/api/v1/response-capabilities", tags=["response_capabilities"])
app.include_router(response_policies.router, prefix="/api/v1/response-policies", tags=["response_policies"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
def root():
    return {
        "message": "Welcome to SentinelSOC API",
        "version": "1.0.0"
    }
