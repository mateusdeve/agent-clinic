---
phase: 02-auth-multi-tenancy
plan: 01
subsystem: database
tags: [alembic, postgresql, rls, multi-tenancy, migrations, uuid]

# Dependency graph
requires: []
provides:
  - Alembic initialized with DATABASE_URL env config and NullPool
  - tenants table with UUID PK, slug, is_active, and default Clinica Padrao row
  - users table with email UNIQUE, hashed_password, role CHECK (admin/recepcionista/medico), tenant_id FK
  - tenant_id UUID column on all 7 data tables (patients, appointments, doctors, conversations, conversation_summaries, knowledge_chunks, follow_ups)
  - Backfill of all existing rows to default tenant 00000000-0000-0000-0000-000000000001
  - current_tenant_id() PostgreSQL function reading app.tenant_id session variable
  - RLS enabled on all 7 data tables + users (8 total) with tenant_isolation_* policies
  - BYPASSRLS granted to current DB user for WhatsApp bot compatibility
affects:
  - 02-auth-multi-tenancy (plans 02, 03, 04 — FastAPI auth, NextAuth frontend)
  - All future phases that touch database queries

# Tech tracking
tech-stack:
  added:
    - alembic 1.16.5 (was in requirements.txt, now initialized and configured)
  patterns:
    - Raw SQL migrations via op.execute() — no SQLAlchemy ORM models
    - Alembic env.py reads DATABASE_URL from os.getenv() + load_dotenv()
    - Migration chain: 001 (base) -> 002 -> 003 (head)
    - Per-table RLS isolation policy pattern: tenant_isolation_{table}
    - BYPASSRLS for service/bot users, RLS enforced for web API users

key-files:
  created:
    - alembic.ini
    - alembic/env.py
    - alembic/script.py.mako
    - alembic/versions/001_create_tenants_users.py
    - alembic/versions/002_add_tenant_id_columns.py
    - alembic/versions/003_enable_rls_policies.py
  modified: []

key-decisions:
  - "All migrations use op.execute() with raw SQL — project has no SQLAlchemy ORM models (psycopg2 only)"
  - "Default tenant UUID 00000000-0000-0000-0000-000000000001 hardcoded for deterministic backfill"
  - "BYPASSRLS granted to current DB user so Sofia/Carla bot pipeline continues working without tenant context"
  - "current_tenant_id() uses NULLIF to return NULL when app.tenant_id not set, preventing accidental cross-tenant leakage"

patterns-established:
  - "Migration pattern: ADD COLUMN nullable -> UPDATE backfill -> SET NOT NULL -> ADD FK -> CREATE INDEX (zero data loss)"
  - "RLS pattern: ENABLE ROW LEVEL SECURITY + CREATE POLICY ... USING (tenant_id = current_tenant_id())"
  - "Session variable pattern: SET LOCAL app.tenant_id = '...' before queries in web API (implemented in plan 02-03)"

requirements-completed: [TENANT-01, TENANT-02, API-03]

# Metrics
duration: 15min
completed: 2026-03-30
---

# Phase 2 Plan 1: Alembic Init + Multi-Tenancy DB Migrations Summary

**Alembic initialized with 3-migration chain: tenants/users tables, tenant_id columns on all 7 data tables with backfill, and PostgreSQL RLS policies with current_tenant_id() session function**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-30T00:10:00Z
- **Completed:** 2026-03-30T00:25:00Z
- **Tasks:** 3
- **Files modified:** 6 created

## Accomplishments

- Initialized Alembic in agent-service with env.py reading DATABASE_URL from environment, NullPool, and load_dotenv() for .env support
- Created migration chain 001->002->003: tenants + users tables with default tenant row, tenant_id columns on all 7 existing data tables (patients, appointments, doctors, conversations, conversation_summaries, knowledge_chunks, follow_ups) with deterministic backfill, FK constraints, and indexes
- Enabled PostgreSQL Row-Level Security on all 8 tables (7 data + users) with current_tenant_id() function reading app.tenant_id session variable; BYPASSRLS granted to current DB user so WhatsApp bot pipeline continues working unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Initialize Alembic and create migration infrastructure** - `285cc3e` (chore)
2. **Task 2: Create migration 001 — tenants and users tables** - `a114700` (feat)
3. **Task 3: Create migrations 002 (tenant_id columns) and 003 (RLS policies)** - `f9a116d` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `alembic.ini` - Alembic config with empty sqlalchemy.url (env.py reads DATABASE_URL)
- `alembic/env.py` - Migration runner with os.getenv('DATABASE_URL'), NullPool, load_dotenv()
- `alembic/script.py.mako` - Standard Alembic migration template
- `alembic/versions/001_create_tenants_users.py` - Creates tenants table + default row + users table with role CHECK constraint
- `alembic/versions/002_add_tenant_id_columns.py` - Adds tenant_id to 7 data tables with backfill, FK, and index per table
- `alembic/versions/003_enable_rls_policies.py` - Creates current_tenant_id() function, enables RLS on 8 tables, grants BYPASSRLS

## Decisions Made

- Used raw SQL via `op.execute()` throughout — no SQLAlchemy ORM models exist in the project; autogenerate would not work
- Hardcoded default tenant UUID `00000000-0000-0000-0000-000000000001` for deterministic, idempotent backfill
- BYPASSRLS granted to `current_user` (the DB user running migrations) — in v1 single-user setup this is acceptable; production with separate web API and bot users would restrict BYPASSRLS to bot user only
- `current_tenant_id()` returns NULL (not error) when `app.tenant_id` is not set, via `NULLIF(..., '')` — this means unset context returns no rows rather than all rows (fail-closed security)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Alembic shebang in agent-service/.venv pointed to a missing venv path (`/Users/.../Dev/agent-clinic/.venv/bin/python3.12`). Resolved by using `python -m alembic` instead of calling the alembic binary directly. Not a blocker.

## User Setup Required

None — no external service configuration required for this plan. To apply migrations, run:
```
cd agent-service && python -m alembic upgrade head
```

## Next Phase Readiness

- Database foundation for multi-tenancy is complete — tenants, users, and isolation policies are ready
- Plan 02-02 can build FastAPI JWT auth endpoints using the users table
- Plan 02-03 can implement the FastAPI middleware that calls `SET LOCAL app.tenant_id = '...'` before each request
- The WhatsApp bot (Sofia/Carla) will continue working after `alembic upgrade head` because the DB user has BYPASSRLS

---
*Phase: 02-auth-multi-tenancy*
*Completed: 2026-03-30*
