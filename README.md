# SentinelSOC

SentinelSOC is an AI-powered, application-agnostic Security Operations Center (SOC) platform.

## Current Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Project foundation, SOC UI |
| Phase 2 | ✅ Complete | PostgreSQL database architecture and models |
| Phase 3 | ✅ Complete | Secure authentication (Argon2id + JWT) |
| Phase 4 | ✅ Complete | RBAC, authorization, user management, security controls |
| Phase 5 | ✅ Complete | Application registration and management |

## Architecture

```
Developer Web App → SentinelSOC Ingestion API → Event Processing → Detection Engine
    → Correlation Engine → Risk Engine → Alerts/Incidents → SOC Dashboard
```

## Technology Stack

- **Frontend**: Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy
- **Database**: PostgreSQL
- **Auth**: Argon2id password hashing, JWT access tokens
- **Infrastructure**: Docker, Docker Compose

---

## RBAC & Authorization

### Roles

| Role | Description |
|------|-------------|
| **ADMIN** | Full administrative access including user management |
| **ANALYST** | SOC investigation and operational access |
| **VIEWER** | Read-only SOC access |

### Permission Matrix

| Permission | ADMIN | ANALYST | VIEWER |
|------------|:-----:|:-------:|:------:|
| `USERS_READ` | ✅ | ❌ | ❌ |
| `USERS_MANAGE` | ✅ | ❌ | ❌ |
| `APPLICATIONS_READ` | ✅ | ✅ | ✅ |
| `APPLICATIONS_MANAGE` | ✅ | ❌ | ❌ |
| `EVENTS_READ` | ✅ | ✅ | ✅ |
| `ALERTS_READ` | ✅ | ✅ | ✅ |
| `ALERTS_MANAGE` | ✅ | ✅ | ❌ |
| `INCIDENTS_READ` | ✅ | ✅ | ✅ |
| `INCIDENTS_MANAGE` | ✅ | ✅ | ❌ |
| `SETTINGS_READ` | ✅ | ✅ | ✅ |
| `SETTINGS_MANAGE` | ✅ | ❌ | ❌ |

### Authorization Architecture

```
JWT → User ID → Load from DB → Check is_active → Determine role → Resolve permissions → Authorize
```

**Key design decisions:**
- The JWT only identifies the user — it is **never** used as the source of truth for roles/permissions
- Role and active status are always loaded from the database on every request
- Role changes and deactivation take effect **immediately** (no waiting for token expiry)
- Frontend role checks are UX only — the backend is always authoritative

### API Authorization Errors

| HTTP Code | Meaning |
|-----------|---------|
| `401 Unauthorized` | Missing or invalid authentication |
| `403 Forbidden` | Authenticated but insufficient permissions |

---

## User Management API

All user management endpoints require `USERS_READ` or `USERS_MANAGE` permissions (ADMIN only).

**No public registration** — users can only be created by administrators.

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| `GET` | `/api/v1/users` | `USERS_READ` | List users (paginated, searchable) |
| `GET` | `/api/v1/users/{id}` | `USERS_READ` | Get single user |
| `POST` | `/api/v1/users` | `USERS_MANAGE` | Create user |
| `PATCH` | `/api/v1/users/{id}` | `USERS_MANAGE` | Update profile (name, email) |
| `PATCH` | `/api/v1/users/{id}/role` | `USERS_MANAGE` | Change role |
| `PATCH` | `/api/v1/users/{id}/status` | `USERS_MANAGE` | Activate/deactivate |

### Security Safeguards

- **Last-admin protection**: Cannot deactivate or demote the last active ADMIN
- **Audit logging**: All user management actions create audit records
- **No sensitive data in responses**: Password hashes are never returned
- **No sensitive data in audit logs**: Passwords and tokens are never stored

---

## Security Headers

The following security headers are set on all responses:

| Header | Value | Notes |
|--------|-------|-------|
| `X-Content-Type-Options` | `nosniff` | Always |
| `X-Frame-Options` | `DENY` | Always |
| `Referrer-Policy` | `no-referrer` | Always |
| `Strict-Transport-Security` | `max-age=63072000` | Production only |

### CORS

- Explicit allowed origins (no wildcards with credentials)
- Explicit allowed methods: `GET, POST, PUT, PATCH, DELETE, OPTIONS`
- Explicit allowed headers: `Authorization, Content-Type, Accept, Origin, X-Requested-With`

---

## Local Setup

### Environment Variables
```bash
cp .env.example .env
```

### Running with Docker
```bash
docker-compose up -d --build
```

### Running manually

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Creating the First Admin
```bash
cd backend
python -m app.scripts.create_admin
```

This is the **only** way to create the initial administrator. All subsequent users are created through the admin UI or API.

---

## Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

Tests cover:
- Authentication (active, inactive, nonexistent users)
- RBAC (all 3 roles × all permissions)
- User management CRUD
- Last-admin safeguards
- Security (no password leaks, immediate role enforcement, security headers)
- Audit logging

### RBAC Testing Guide

1. **Login as ADMIN** → verify User Management sidebar item visible
2. **Create ANALYST and VIEWER** via User Management
3. **Change roles** → verify role takes effect immediately
4. **Deactivate a user** → verify they lose API access
5. **Login as ANALYST** → verify no User Management, 403 on user management API
6. **Login as VIEWER** → verify read-only, 403 on management APIs

---

## API Documentation

Interactive API docs are available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Directory Structure

```
├── frontend/           # Next.js application
│   ├── app/            # Pages and routes
│   ├── components/     # Reusable components
│   └── lib/            # Auth, permissions, API client
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── api/        # Route handlers
│   │   ├── core/       # Config, security, permissions
│   │   ├── db/         # Database engine and base models
│   │   ├── models/     # SQLAlchemy models
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # Business logic (user, audit)
│   │   └── scripts/    # Admin creation script
│   └── tests/          # Comprehensive test suite
└── docker-compose.yml
```

