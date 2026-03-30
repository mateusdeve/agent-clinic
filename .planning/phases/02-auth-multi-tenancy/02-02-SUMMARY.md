---
phase: 02-auth-multi-tenancy
plan: 02
subsystem: auth
tags: [jwt, pyjwt, pwdlib, argon2, fastapi, rbac, multi-tenancy, cors]

# Dependency graph
requires:
  - phase: 02-auth-multi-tenancy
    plan: 01
    provides: "tenants and users tables with UUID PKs, hashed_password, role CHECK constraint"
provides:
  - FastAPI auth router at /auth with login, refresh, me, seed endpoints
  - get_current_user dependency — decodes Bearer token, extracts user_id/tenant_id/role
  - get_current_tenant dependency — extracts tenant_id from JWT (never from request params)
  - require_role(*roles) dependency factory — raises 403 on unauthorized role
  - get_db_for_tenant dependency — psycopg2 connection with SET LOCAL app.tenant_id for RLS
  - CORS middleware configured for Next.js frontend on FRONTEND_URL env var
  - Auth router mounted on existing FastAPI app
affects:
  - 02-auth-multi-tenancy plan 03 (NextAuth frontend integration — calls POST /auth/login)
  - 02-auth-multi-tenancy plan 04 (any protected API endpoints)
  - All future API endpoints that need authentication or tenant isolation

# Tech tracking
tech-stack:
  added:
    - PyJWT==2.12.1 (JWT encode/decode, FastAPI official docs recommendation)
    - pwdlib[argon2]==0.2.1 (Argon2 password hashing, FastAPI official docs recommendation)
    - python-multipart==0.0.20 (form data parsing for OAuth2PasswordBearer)
  patterns:
    - OAuth2PasswordBearer(tokenUrl="/auth/login") for Bearer token extraction
    - Two-token architecture: access token (30 min) with sub/tenant_id/role + refresh token (7 days) with sub/type=refresh
    - require_role as a dependency factory (not a decorator) — returns inner function for FastAPI Depends()
    - SET LOCAL app.tenant_id in get_db_for_tenant for per-request RLS activation
    - _get_db() contextmanager pattern consistent with existing psycopg2 usage in codebase

key-files:
  created:
    - agent-service/src/api/auth.py
    - agent-service/src/api/deps.py
  modified:
    - agent-service/src/api/webhook.py
    - agent-service/requirements.txt

key-decisions:
  - "GET /auth/me uses late import of get_current_user to avoid circular imports (auth.py imports deps.py which would need to import auth.py for the oauth2_scheme)"
  - "require_role returns a closure (not async) — synchronous dependencies work fine in FastAPI for this pattern"
  - "CORS allow_origins reads FRONTEND_URL env var with fallback to http://localhost:3000 — no hardcoded production origins"
  - "get_db_for_tenant uses SET LOCAL (not SET) — transaction-scoped so value resets automatically, safer under connection pooling"

patterns-established:
  - "Auth pattern: OAuth2PasswordBearer + jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) in get_current_user"
  - "RBAC pattern: Depends(require_role('admin')) on any protected endpoint"
  - "Tenant isolation pattern: Depends(get_db_for_tenant) auto-sets RLS context before any query"

requirements-completed: [API-02, TENANT-01, TENANT-02, TENANT-03, AUTH-04, AUTH-06]

# Metrics
duration: 10min
completed: 2026-03-30
---

# Phase 2 Plan 2: FastAPI JWT Auth Endpoints + Dependencies Summary

**FastAPI auth router (login/refresh/me/seed) with PyJWT + Argon2, plus get_current_user/get_current_tenant/require_role/get_db_for_tenant dependencies and CORS for Next.js frontend**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-30T00:09:55Z
- **Completed:** 2026-03-30T00:20:00Z
- **Tasks:** 2
- **Files modified:** 2 created, 2 modified

## Accomplishments

- Created `agent-service/src/api/auth.py` with 4 endpoints: POST /auth/login (email+password → access_token+refresh_token with user_id/email/name/role/tenant_id), POST /auth/refresh (refresh token → new access_token), GET /auth/me (returns current user info), POST /auth/seed (dev-only admin user creation guarded by ENVIRONMENT != "production")
- Created `agent-service/src/api/deps.py` with get_current_user (JWT decode), get_current_tenant (tenant_id from JWT per TENANT-03), require_role factory (403 on unauthorized per D-07), and get_db_for_tenant (psycopg2 conn + SET LOCAL for RLS per API-03)
- Updated `agent-service/src/api/webhook.py` to mount auth_router and add CORSMiddleware with allow_credentials=True for NextAuth session forwarding — all existing webhook endpoints unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Install backend auth dependencies and create auth endpoints** - `55f523f` (feat)
2. **Task 2: Create auth dependencies and mount router on FastAPI app** - `903252e` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `agent-service/src/api/auth.py` - Auth router with login, refresh, me, seed endpoints using PyJWT + pwdlib
- `agent-service/src/api/deps.py` - FastAPI dependency functions for auth, tenant, role, and DB isolation
- `agent-service/src/api/webhook.py` - Added auth router mounting and CORS middleware
- `agent-service/requirements.txt` - Added PyJWT==2.12.1, pwdlib[argon2]==0.2.1, python-multipart==0.0.20

## Decisions Made

- Used late import in GET /auth/me (`from src.api.deps import get_current_user`) to avoid circular imports — auth.py and deps.py would otherwise create a circular dependency since both need each other
- `require_role` implemented as a synchronous dependency factory (not async) — FastAPI supports sync dependencies; the inner `_check_role` function is the actual dependency returned
- CORS `allow_origins` reads from `FRONTEND_URL` environment variable with localhost:3000 fallback, avoiding hardcoded production values
- `get_db_for_tenant` uses `SET LOCAL` rather than `SET` — transaction-scoped setting is reverted automatically at transaction end, which is safer if connections are reused (connection pooling)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- `python3 -c "from src.api.auth import router"` initially failed because psycopg2, python-dotenv, and fastapi were not installed in the system Python 3.9 path (project normally uses a venv). Resolved by running `python3 -m pip install` for each missing dependency. This is a local environment issue, not a code issue.

## User Setup Required

`JWT_SECRET_KEY` environment variable must be added to `agent-service/.env`:

```bash
# Generate with:
python3 -c "import secrets; print(secrets.token_hex(32))"
# Add to agent-service/.env:
JWT_SECRET_KEY=<generated-value>
```

Also add `FRONTEND_URL` to `agent-service/.env` if the frontend runs on a different port:
```bash
FRONTEND_URL=http://localhost:3000
```

## Next Phase Readiness

- FastAPI auth layer is complete — NextAuth CredentialsProvider (plan 02-03) can now call `POST /auth/login` with email+password and receive a JWT to store in the session
- Any protected API endpoint can use `Depends(get_current_user)`, `Depends(require_role('admin'))`, or `Depends(get_db_for_tenant)` to enforce auth, RBAC, and tenant isolation automatically
- The seed endpoint (`POST /auth/seed`) can be used to create a test admin user before building the NextAuth login page

## Self-Check: PASSED

All files verified present on disk. Both task commits (55f523f, 903252e) confirmed in git log.

---
*Phase: 02-auth-multi-tenancy*
*Completed: 2026-03-30*
