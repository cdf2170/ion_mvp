# MVP 

P-y API   PSQL     .

  - .

```

# MVP Backend

This repository contains a production oriented FastAPI backend for an identity and device management MVP. The backend exposes versioned REST endpoints under the `/v1` prefix and uses PostgreSQL for persistence. It includes utilities for seeding, migration, and a small administrative surface for maintenance tasks.

## Project overview

- Framework: FastAPI
- Database: PostgreSQL (SQLAlchemy + Alembic)
- Auth: Bearer token 
- API prefix: `/v1`
- Repo entrypoint: `backend/app/main.py` (app factory: `create_app()`)

## Repository layout

- `backend/app/` - application package
  - `main.py` - FastAPI app factory and health/debug endpoints
  - `config.py` - application configuration (imported by `main.py` when present)
  - `schemas.py` - Pydantic data models used by the API
  - `routers/` - API routers (users, devices, apis, policies, history, groups, access, oauth)
  - `db/` - database models and session management
- `alembic/` - migrations
- `seed_db.py` - database seeding helper used by the admin endpoint
- deployment and helper scripts at repo root: `start_backend.sh`, `deploy_railway.sh`, `start_production.sh`, `Dockerfile.bak`, `Procfile` and related docs

## Quick start (local development)

Prerequisites:

- Python 3.11+ (the project uses modern Pydantic patterns)
- PostgreSQL (local or via Docker)
- Recommended: a virtual environment or `venv`/`pipx`

1. Create and activate a virtual environment

  python3 -m venv .venv
  source .venv/bin/activate

2. Install dependencies

  pip install -r requirements.txt

3. Configure environment variables


4. Run database migrations (Alembic)

  alembic upgrade head

5. Start the app (development)

  uvicorn backend.app.main:app --reload --port 8000

If you want to use the included scripts, see `start_backend.sh` and `start_production.sh` for common patterns used in this repository.

## Important endpoints and developer helpers

The app registers multiple routers under the `/v1` prefix. The most relevant endpoints and helpers are:

- `/v1/health` - Health check (includes basic database connectivity check)
- `/v1/readiness` - Readiness probe (returns 503 if DB not reachable)
- `/v1/liveness` - Liveness probe
- `/v1/debug/routes` - Returns the registered routes and import errors for debugging
- `/v1/api-info` - Small machine-friendly summary of important API endpoints and auth

Admin helpers (protected by token dependency in development):

- `POST /v1/admin/seed-database` - Run `seed_db.seed_database()` to populate sample data
- `POST /v1/admin/run-migration` - Attempt to run `run_migration.py` in the deployed container
- `POST /v1/admin/fix-database` - Run a small set of ALTER TABLE statements to add missing columns

API routers (high level)

- `users` - list, detail, scan, merge, password reset, sync, advanced merge
- `devices` - list, detail, update, delete, device summaries and dashboard helpers
- `apis` - manage external API connections (create, test, sync, logs)
- `policies` - manage security policies and summaries
- `history` - configuration and activity history, timeline endpoints
- `groups`, `access`, `oauth` - additional access and OAuth management routers when enabled

For exact route listings, use the debug endpoint: `/v1/debug/routes`.

## Authentication


## Full API routes

This is a complete, code-accurate list of routes registered by the application (no emojis). OAuth endpoints are listed separately since the OAuth router is mounted without the `/v1` prefix.

Top-level (main app)
- GET  /                     — root: basic app status
- GET  /health               — legacy Railway health
- GET  /api/devices          — redirect (301) -> /v1/devices
- GET  /api/health           — alias to health check

Versioned API (prefix: /v1) — probes & helpers
- GET  /v1/health
- GET  /v1/debug/routes
- GET  /v1/readiness
- GET  /v1/liveness
- GET  /v1/cors-debug
- GET  /v1/api-info
- POST /v1/admin/seed-database
- POST /v1/admin/run-migration
- POST /v1/admin/fix-database

OAuth endpoints (mounted at `/oauth`)
- GET  /oauth/.well-known/openid-configuration
- GET  /oauth/authorize
- POST /oauth/callback
- POST /oauth/token
- GET  /oauth/userinfo
- GET  /oauth/jwks
- GET  /oauth/logout
- GET  /oauth/test-users

Users router (`/v1/users`)
- GET  /v1/users
- GET  /v1/users/{cid}
- POST /v1/users/scan/{cid}
- PUT  /v1/users/{cid}
- POST /v1/users/merge
- POST /v1/users/password-reset
- POST /v1/users/sync
- POST /v1/users/advanced-merge
- POST /v1/users/advanced-merge/execute

Devices router (`/v1/devices`)
- GET    /v1/devices
- GET    /v1/devices/{device_id}
- PUT    /v1/devices/{device_id}
- DELETE /v1/devices/{device_id}
- GET    /v1/devices/non-compliant/summary
- GET    /v1/devices/summary/counts
- GET    /v1/devices/summary/by-status
- GET    /v1/devices/summary/compliance
- GET    /v1/devices/summary/by-tag
- GET    /v1/devices/summary/by-vlan
- GET    /v1/devices/summary/recent-activity
- GET    /v1/devices/summary/by-os
- GET    /v1/devices/summary/risk-analysis

API management router (`/v1/apis`)
- GET    /v1/apis
- GET    /v1/apis/{connection_id}
- POST   /v1/apis
- PUT    /v1/apis/{connection_id}
- DELETE /v1/apis/{connection_id}
- POST   /v1/apis/{connection_id}/test
- POST   /v1/apis/{connection_id}/sync
- GET    /v1/apis/{connection_id}/logs
- PUT    /v1/apis/{connection_id}/tags
- GET    /v1/apis/status/summary
- POST   /v1/apis/sync-all
- GET    /v1/apis/orphans
- POST   /v1/apis/improve-device-names
- POST   /v1/apis/fix-misnamed-devices

Policies router (`/v1/policies`)
- GET    /v1/policies
- GET    /v1/policies/{policy_id}
- POST   /v1/policies
- PUT    /v1/policies/{policy_id}
- DELETE /v1/policies/{policy_id}
- POST   /v1/policies/{policy_id}/enable
- POST   /v1/policies/{policy_id}/disable
- GET    /v1/policies/summary/by-type
- GET    /v1/policies/summary/by-severity

History / audit router (`/v1/history`)
- GET  /v1/history/config
- GET  /v1/history/activity
- POST /v1/history/activity
- GET  /v1/history/activity/summary/by-type
- GET  /v1/history/activity/summary/by-risk
- GET  /v1/history/config/summary/recent-changes
- GET  /v1/history/timeline

Groups router (`/v1/groups`)
- GET  /v1/groups
- GET  /v1/groups/{group_name}/members
- GET  /v1/groups/summary/by-type
- GET  /v1/groups/departments
- GET  /v1/groups/user/{cid}/memberships

Access management router (`/v1/access`)
- GET  /v1/access
- GET  /v1/access/audit
- GET  /v1/access/user/{cid}
- GET  /v1/access/user/{cid}/audit
- GET  /v1/access/summary
- GET  /v1/access/compliance/{framework}

Notes:
- Most business endpoints require a Bearer token via the `verify_token` dependency.
- The OAuth router is mounted without the `/v1` prefix.
- For a runtime-accurate dump of registered routes, call the running app's debug endpoint: `/v1/debug/routes`.

If you want, I can generate an `API_REFERENCE.md` with this list formatted as a table and include parameters and response model references.
