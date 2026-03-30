---
phase: 02-auth-multi-tenancy
plan: "00"
subsystem: testing
tags: [pytest, psycopg2, fastapi, xfail, test-infrastructure]

requires: []
provides:
  - pytest.ini configured with testpaths and custom markers (auth, rbac, tenant)
  - conftest.py with shared fixtures: db_conn, default_tenant_id, fastapi_app, test_client
  - test_auth.py with 4 xfail stubs for login, refresh, and /me endpoints
  - test_rbac.py with 3 xfail stubs for role enforcement and tenant JWT extraction
  - test_tenant_isolation.py with 3 xfail stubs for RLS and cross-clinic isolation
affects: [02-01, 02-02, 02-03]

tech-stack:
  added: []
  patterns:
    - xfail-first test stubs — all new tests start as @pytest.mark.xfail before implementation
    - transaction-rollback test isolation — db_conn fixture rolls back after each test, no separate test DB
    - session-scoped db_url — DATABASE_URL checked once per session, skip if not set

key-files:
  created:
    - agent-service/pytest.ini
    - agent-service/tests/__init__.py
    - agent-service/tests/conftest.py
    - agent-service/tests/test_auth.py
    - agent-service/tests/test_rbac.py
    - agent-service/tests/test_tenant_isolation.py
  modified: []

key-decisions:
  - "Use @pytest.mark.xfail instead of @pytest.mark.skip so xpassed tests are visible signals when implementation is complete"
  - "Use dev database with transaction rollback rather than separate test database — simpler setup, consistent with existing codebase pattern"
  - "fastapi_app fixture skips gracefully if app is not importable — ensures conftest works before auth router exists"

patterns-established:
  - "xfail-first: Plan 00 stubs all tests as xfail, subsequent plans remove xfail as they implement"
  - "db_conn rolls back: every DB test gets a clean slate without needing a test DB"

requirements-completed: [AUTH-01, AUTH-02, AUTH-04, AUTH-06, TENANT-01, TENANT-02, TENANT-03]

duration: 3min
completed: 2026-03-29
---

# Phase 02 Plan 00: Test Infrastructure Summary

**pytest infrastructure with xfail stubs for auth (4), RBAC (3), and tenant isolation (3) tests — suite is green before implementation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-30T00:03:29Z
- **Completed:** 2026-03-30T00:05:52Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- pytest.ini configured with `testpaths = tests` and custom markers (auth, rbac, tenant)
- conftest.py providing 4 shared fixtures: `db_url`, `db_conn`, `default_tenant_id`, `fastapi_app`, `test_client`
- 10 test stubs across 3 files, all marked `@pytest.mark.xfail` so suite exits 0 before implementation
- Fixtures skip gracefully when DATABASE_URL is not set or FastAPI app is not yet importable

## Task Commits

1. **Task 1: Create pytest config and shared test fixtures** - `411a83b` (chore)
2. **Task 2: Create test stub files for auth, RBAC, and tenant isolation** - `599fca9` (test)

**Plan metadata:** `8499add` (docs: complete test infrastructure plan)

## Files Created/Modified

- `agent-service/pytest.ini` - pytest configuration: testpaths, markers, python_files/functions patterns
- `agent-service/tests/__init__.py` - empty package init for test discovery
- `agent-service/tests/conftest.py` - shared fixtures: db_url, db_conn, default_tenant_id, fastapi_app, test_client
- `agent-service/tests/test_auth.py` - 4 xfail stubs: login valid, login invalid, refresh token, /me endpoint
- `agent-service/tests/test_rbac.py` - 3 xfail stubs: require_role allows admin, rejects medico, tenant from JWT
- `agent-service/tests/test_tenant_isolation.py` - 3 xfail stubs: RLS policies exist, cross-clinic isolation, SET LOCAL

## Decisions Made

- Used `@pytest.mark.xfail` instead of `@pytest.mark.skip` — xpassed tests signal when implementation is complete without changing exit code
- Transaction rollback on `db_conn` instead of separate test database — matches existing codebase pattern, no extra infrastructure needed
- `fastapi_app` fixture uses try/except to skip gracefully if app can't be imported (e.g., missing dependencies before auth router is added)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The agent-service `.venv` shebang points to `/Users/mateuspires/Dev/agent-clinic/.venv/bin/python3.12` (the original root venv location) which no longer exists. Verification used the Frameworks Python path with explicit site-packages. This is a pre-existing environment issue not caused by this plan — logged to deferred-items.

## Next Phase Readiness

- Test infrastructure is ready for Plans 01-03 to fill in implementations
- Plan 01 (DB migrations + RLS) should flip xfail on `test_rls_policies_exist` and `test_tenant_isolation_across_clinics`
- Plan 02 (auth endpoints) should flip xfail on all test_auth.py and test_rbac.py stubs
- Broken `.venv` shebang should be fixed before running tests in CI — suggest recreating venv from requirements.txt

## Self-Check: PASSED

- FOUND: agent-service/pytest.ini
- FOUND: agent-service/tests/__init__.py
- FOUND: agent-service/tests/conftest.py
- FOUND: agent-service/tests/test_auth.py
- FOUND: agent-service/tests/test_rbac.py
- FOUND: agent-service/tests/test_tenant_isolation.py
- FOUND: .planning/phases/02-auth-multi-tenancy/02-00-SUMMARY.md
- FOUND commit: 411a83b (chore: pytest config and fixtures)
- FOUND commit: 599fca9 (test: xfail stub files)
- FOUND commit: 8499add (docs: plan metadata)

---
*Phase: 02-auth-multi-tenancy*
*Completed: 2026-03-29*
