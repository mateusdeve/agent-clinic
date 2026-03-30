---
phase: 02-auth-multi-tenancy
verified: 2026-03-29T21:30:00Z
status: gaps_found
score: 7/9 must-haves verified
re_verification: false
gaps:
  - truth: "A tenants table exists / users table exists / tenant_id columns on all data tables / RLS enabled with current_tenant_id()"
    status: failed
    reason: "Alembic migrations (001, 002, 003) were committed to a diverged git worktree branch (worktree-agent-af4cec45) and were NEVER merged into main. The files do not exist at agent-service/alembic/ in the main branch."
    artifacts:
      - path: "agent-service/alembic.ini"
        issue: "File does not exist in main branch (only in worktree-agent-af4cec45)"
      - path: "agent-service/alembic/env.py"
        issue: "File does not exist in main branch"
      - path: "agent-service/alembic/versions/001_create_tenants_users.py"
        issue: "File does not exist in main branch"
      - path: "agent-service/alembic/versions/002_add_tenant_id_columns.py"
        issue: "File does not exist in main branch"
      - path: "agent-service/alembic/versions/003_enable_rls_policies.py"
        issue: "File does not exist in main branch"
    missing:
      - "Merge worktree-agent-af4cec45 into main OR cherry-pick commits 285cc3e, a114700, f9a116d into main under agent-service/ path"
      - "Note: the worktree has alembic/ at its root, not under agent-service/ — the path must be corrected to agent-service/alembic/ when merging"
  - truth: "Test stubs still marked xfail — auth tests were not promoted after Plan 02 implemented the endpoints"
    status: partial
    reason: "test_auth.py and test_rbac.py retain @pytest.mark.xfail(reason='Plan 02 not yet executed') even though auth.py and deps.py are fully implemented and operational. This means the tests never validated the running implementation."
    artifacts:
      - path: "agent-service/tests/test_auth.py"
        issue: "All 4 tests still xfail — should have xfail removed after Plan 02 implementation"
      - path: "agent-service/tests/test_rbac.py"
        issue: "All 3 tests still xfail — require_role is implemented but tests not promoted"
    missing:
      - "Remove @pytest.mark.xfail from test_auth.py tests (login, refresh, me)"
      - "Implement (fill in) test_rbac.py stubs: test_require_role_admin_allows_admin, test_require_role_admin_rejects_medico, test_get_current_tenant_extracts_from_jwt"
      - "Once migrations are applied to DB, remove xfail from test_tenant_isolation.py"
human_verification:
  - test: "Login page end-to-end with running servers"
    expected: "Split-layout page loads, invalid credentials show error, valid admin credentials redirect to /home, role-based sidebar shows admin links only for admin, logout redirects to /login, session persists on refresh, /home while unauthenticated redirects to /login"
    why_human: "Requires running FastAPI (with DB migrations applied) + Next.js dev server + AUTH_SECRET configured"
  - test: "Alembic migrations run cleanly against the real database"
    expected: "alembic upgrade head completes without errors, tenants/users tables created, RLS policies active on all 8 tables, existing data preserved"
    why_human: "Requires access to the PostgreSQL database and the migrations must be run from the correct path (currently only in worktree, not in agent-service/)"
---

# Phase 02: Auth + Multi-Tenancy Verification Report

**Phase Goal:** Users can securely log in with role-based access and every data operation is automatically scoped to the correct clinic
**Verified:** 2026-03-29T21:30:00Z
**Status:** GAPS FOUND
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can log in with email/password on login page (AUTH-01) | ✓ VERIFIED | `login-form.tsx` calls `signIn("credentials")`, FastAPI `/auth/login` queries users table with password verification |
| 2 | User can log out from dashboard (AUTH-02) | ✓ VERIFIED | `logout-button.tsx` calls `signOut({ callbackUrl: "/login" })`, wired in dashboard layout |
| 3 | Session persists across browser refresh (AUTH-03) | ✓ VERIFIED | NextAuth `session: { strategy: "jwt" }` configured; jwt/session callbacks copy role, tenant_id, access_token |
| 4 | Protected routes redirect unauthenticated users to /login (AUTH-05) | ✓ VERIFIED | `proxy.ts` exports `proxy` function (not `middleware`), guards `/home`, `/agenda`, `/pacientes`, `/medicos`, `/whatsapp`, `/dashboard`, `/usuarios` |
| 5 | Admin sees admin-only UI elements others do not (AUTH-06) | ✓ VERIFIED | Dashboard layout conditionally renders "Medicos" and "Usuarios" links only when `role === "admin"`; home/page.tsx shows role-adaptive cards |
| 6 | Login page has split layout (D-05) | ✓ VERIFIED | `login/page.tsx` has `hidden lg:flex w-1/2 bg-green-600` left panel + `w-full lg:w-1/2` right panel with `LoginForm` |
| 7 | tenant_id extracted from JWT automatically, never from request params (TENANT-03) | ✓ VERIFIED | `get_current_tenant` in `deps.py` returns `user["tenant_id"]` from JWT decode; `get_db_for_tenant` executes `SET LOCAL app.tenant_id = %s` |
| 8 | Database has tenants/users tables, tenant_id on all data tables, RLS policies | ✗ FAILED | Alembic migrations (001, 002, 003) exist ONLY in worktree-agent-af4cec45 branch — NOT in `main`. `git show HEAD:agent-service/alembic.ini` returns "fatal: path does not exist in HEAD" |
| 9 | Test stubs promoted after implementation (plan intent) | ✗ FAILED | `test_auth.py` and `test_rbac.py` still carry `@pytest.mark.xfail(reason="Plan 02 not yet executed")` — implementation exists but tests were never activated |

**Score:** 7/9 truths verified

---

## Required Artifacts

### Plan 00 Artifacts (Test Infrastructure)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent-service/pytest.ini` | pytest config with testpaths and markers | ✓ VERIFIED | Contains `testpaths = tests`, markers: auth, rbac, tenant |
| `agent-service/tests/conftest.py` | Shared fixtures: db_conn, fastapi_app, test_client | ✓ VERIFIED | All 5 fixtures present: db_url, db_conn, default_tenant_id, fastapi_app, test_client |
| `agent-service/tests/test_auth.py` | 4 stubs for login, refresh, me | ✓ VERIFIED | 4 xfail stubs present (still xfail — see gaps) |
| `agent-service/tests/test_rbac.py` | 3 stubs for RBAC enforcement | ✓ VERIFIED | 3 xfail stubs present (still xfail — see gaps) |
| `agent-service/tests/test_tenant_isolation.py` | 3 stubs for RLS + isolation | ✓ VERIFIED | 3 xfail stubs present |

### Plan 01 Artifacts (Database Migrations)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent-service/alembic.ini` | Alembic config with empty sqlalchemy.url | ✗ MISSING | Path not tracked in main branch. File only at `.claude/worktrees/agent-af4cec45/alembic.ini` |
| `agent-service/alembic/env.py` | Migration runner reading DATABASE_URL | ✗ MISSING | Only in worktree branch. `git show HEAD:agent-service/alembic/env.py` → fatal |
| `agent-service/alembic/versions/001_create_tenants_users.py` | tenants + users tables | ✗ MISSING | Only in worktree. File content is substantive (verified in worktree) |
| `agent-service/alembic/versions/002_add_tenant_id_columns.py` | tenant_id on 7 data tables + backfill | ✗ MISSING | Only in worktree. File content is substantive (verified in worktree) |
| `agent-service/alembic/versions/003_enable_rls_policies.py` | RLS + current_tenant_id() function | ✗ MISSING | Only in worktree. File content is substantive (verified in worktree) |

**Root cause:** Alembic commits (285cc3e, a114700, f9a116d) were executed in a git worktree at `.claude/worktrees/agent-af4cec45` on branch `worktree-agent-af4cec45`. The branch diverges from main at commit `dd705f4` (before the `agent-service/` directory was created). Those commits placed alembic files at the OLD project root, not under `agent-service/`. The SUMMARY commit (8acc50d) was cherry-picked or merged into main — but the CODE commits were not.

### Plan 02 Artifacts (FastAPI Auth)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent-service/src/api/auth.py` | Login, refresh, me, seed endpoints | ✓ VERIFIED | `router = APIRouter(prefix="/auth")`, 4 endpoints, queries users table with parameterized SQL, PyJWT + pwdlib |
| `agent-service/src/api/deps.py` | get_current_user, get_current_tenant, require_role, get_db_for_tenant | ✓ VERIFIED | All 4 exports present, JWT decode, TENANT-03 compliant, SET LOCAL in get_db_for_tenant |
| `agent-service/src/api/webhook.py` | Auth router mounted + CORS | ✓ VERIFIED | `app.include_router(auth_router)`, CORSMiddleware with allow_credentials=True |

### Plan 03 Artifacts (NextAuth Frontend)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/lib/auth.ts` | NextAuth v5 config with CredentialsProvider | ✓ VERIFIED | Exports handlers, auth, signIn, signOut; fetches FASTAPI_URL/auth/login; jwt/session callbacks copy role, tenant_id, access_token |
| `frontend/src/lib/auth.d.ts` | Type augmentation for role, tenant_id, access_token | ✓ VERIFIED | Augments @auth/core/types User, AdapterUser, next-auth/jwt JWT |
| `frontend/src/app/api/auth/[...nextauth]/route.ts` | NextAuth API route handler | ✓ VERIFIED | Exports GET and POST from handlers |
| `frontend/proxy.ts` | Route protection — unauthenticated redirect to /login | ✓ VERIFIED | `export const proxy = auth(...)`, guards all dashboard paths, no middleware.ts present |
| `frontend/src/app/(auth)/login/page.tsx` | Split-layout login page | ✓ VERIFIED | green-600 left panel, form right panel, renders LoginForm |
| `frontend/src/app/(auth)/login/login-form.tsx` | Client component with react-hook-form + zod | ✓ VERIFIED | "use client", zod schema, signIn("credentials"), router.push("/home") on success, no forgot-password/register links |
| `frontend/src/app/(dashboard)/layout.tsx` | Dashboard shell with auth check + role nav | ✓ VERIFIED | Calls auth(), redirects if !session, admin-only Medicos/Usuarios links, LogoutButton |
| `frontend/src/app/(dashboard)/home/page.tsx` | Role-adaptive home page | ✓ VERIFIED | Reads session.user.role, renders different cards per role; placeholder content is intentional per plan |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `auth.ts` | FastAPI `/auth/login` | CredentialsProvider authorize() fetch | ✓ WIRED | `fetch(\`${process.env.FASTAPI_URL}/auth/login\`)` — real fetch call with JSON body |
| `proxy.ts` | `auth.ts` | `export const proxy = auth(...)` | ✓ WIRED | Pattern `auth.*proxy` confirmed |
| `login-form.tsx` | `auth.ts` | `signIn("credentials", {...})` | ✓ WIRED | signIn with redirect:false, error handling, router.push on success |
| `dashboard/layout.tsx` | `auth.ts` | `await auth()` + `signOut` | ✓ WIRED | Server component calling auth(), LogoutButton calling signOut |
| `auth.py` | users table | psycopg2 SELECT WHERE email | ✓ WIRED | `SELECT id, email, name, hashed_password, role, tenant_id, is_active FROM users WHERE email = %s` |
| `deps.py` | JWT_SECRET_KEY | `jwt.decode(token, SECRET_KEY, ...)` | ✓ WIRED | Pattern `jwt.decode.*SECRET_KEY` confirmed in deps.py line 43 |
| `webhook.py` | `auth.py` | `app.include_router(auth_router)` | ✓ WIRED | Line 41 of webhook.py confirmed |
| `deps.py GET LOCAL` | RLS activation | `SET LOCAL app.tenant_id = %s` | ✓ WIRED | `get_db_for_tenant` line 101 — but DB schema (RLS policies) missing from main |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `login-form.tsx` | result (signIn response) | NextAuth → FastAPI `/auth/login` → users DB table | Conditional — depends on users table existing in DB | ⚠️ HOLLOW — flow is wired but DB schema (users table) not applied to any database from main |
| `dashboard/layout.tsx` | session (role, name) | NextAuth JWT → session callback | Same dependency | ⚠️ HOLLOW — data flow works if DB is migrated |
| `home/page.tsx` | session.user.role | Same JWT chain | Intentional placeholder cards | ✓ FLOWING — role-based rendering works; card content is intentional placeholder |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| auth router importable | `python3 -c "from src.api.auth import router; print(router.prefix)"` | `/auth` | ✓ PASS |
| deps module importable | `python3 -c "from src.api.deps import get_current_user, get_current_tenant, require_role, get_db_for_tenant; print('ok')"` | `deps ok` | ✓ PASS |
| webhook mounts auth router | `grep "include_router" agent-service/src/api/webhook.py` | line 41 found | ✓ PASS |
| next build without TypeScript errors | `npx next build` | 0 errors, routes: /, /home, /login, /api/auth/[...nextauth] | ✓ PASS |
| No middleware.ts (Next.js 16 compat) | `test -f frontend/middleware.ts` | File absent | ✓ PASS |
| proxy.ts exports correct name | `grep "export const proxy" frontend/proxy.ts` | Found | ✓ PASS |
| Alembic migrations in main branch | `git show HEAD:agent-service/alembic.ini` | fatal: path does not exist in HEAD | ✗ FAIL |
| DB login flow (live) | Requires running FastAPI + DB | Cannot test without server | ? SKIP |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| AUTH-01 | 02-00, 02-03 | Login with email and password | ✓ SATISFIED | login-form.tsx + auth.py /login endpoint |
| AUTH-02 | 02-03 | Logout from any page | ✓ SATISFIED | logout-button.tsx with signOut() in dashboard layout |
| AUTH-03 | 02-03 | Session persists across refresh | ✓ SATISFIED | NextAuth JWT strategy + session callback |
| AUTH-04 | 02-00, 02-02 | Three roles: Admin, Recepcionista, Medico | ✓ SATISFIED | users table schema (in worktree) + CHECK constraint in 001 migration; role enforced in deps.py require_role |
| AUTH-05 | 02-03 | Protected routes redirect unauthenticated | ✓ SATISFIED | proxy.ts guards all dashboard paths |
| AUTH-06 | 02-00, 02-02, 02-03 | RBAC — features restricted by role | ✓ SATISFIED | require_role() in deps.py + role-conditional sidebar nav in layout.tsx |
| TENANT-01 | 02-01 | Each clinic's data is fully isolated | ✗ BLOCKED | Migrations with RLS not in main branch. DB schema unverified as applied |
| TENANT-02 | 02-01 | No endpoint returns another clinic's data | ✗ BLOCKED | RLS policies only in worktree — cannot guarantee enforcement |
| TENANT-03 | 02-02 | tenant_id extracted from JWT automatically | ✓ SATISFIED | get_current_tenant() + get_db_for_tenant() in deps.py |
| API-02 | 02-02 | FastAPI implements JWT auth with refresh | ✓ SATISFIED | auth.py has /login (30min access) + /refresh (7d refresh) + /me |
| API-03 | 02-01, 02-02 | FastAPI multi-tenancy middleware with auto-filter | ✓ PARTIAL | get_db_for_tenant does SET LOCAL (code present), but DB RLS policies missing from main |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `agent-service/tests/test_auth.py` | 6, 20, 31, 48 | `@pytest.mark.xfail(reason="Plan 02 not yet executed")` on implemented endpoints | ⚠️ Warning | Tests never validate running auth implementation |
| `agent-service/tests/test_rbac.py` | 5, 12, 19 | `@pytest.mark.xfail` + empty `pass` bodies | ⚠️ Warning | RBAC tests never validate require_role behavior |
| `frontend/src/app/(dashboard)/home/page.tsx` | 17, 24, 31 | "Phase 5", "Phase 3" placeholder content strings | ℹ️ Info | Intentional per plan — not a blocker for auth goals |
| `agent-service/src/api/auth.py` | 257 | `seed` endpoint accepts query params (`email: str, password: str`) not JSON body | ℹ️ Info | SUMMARY shows curl with `-d '{"email":...}'` which would NOT work — needs `SeedRequest(BaseModel)` or the curl must use `?email=...&password=...` |

---

## Human Verification Required

### 1. Database Migration Applied

**Test:** Run `alembic upgrade head` from the correct directory with the migrations merged to main under `agent-service/alembic/`
**Expected:** All 3 migrations complete without errors. `\dt` in psql shows `tenants`, `users` tables. `SELECT * FROM pg_policies` shows `tenant_isolation_*` policies on 8 tables.
**Why human:** Requires a running PostgreSQL database and the migration files must first be moved to main.

### 2. Login + Role-Based UI End-to-End

**Test:** Start FastAPI (`uvicorn src.api.webhook:app --reload`), run seed endpoint, start Next.js (`npm run dev`), visit http://localhost:3000/home, login as admin, verify sidebar shows Medicos/Usuarios, logout, verify redirect
**Expected:** All 10 steps from 02-03-PLAN Task 4 pass
**Why human:** Requires two running services + seeded database + AUTH_SECRET and JWT_SECRET_KEY configured in .env files

### 3. Tenant Isolation Enforcement

**Test:** Seed two clinics (two different tenant_ids), login as user from clinic A, verify API endpoints return only clinic A data
**Expected:** Data from clinic B never appears in any response
**Why human:** Requires DB migrations applied + RLS policies enforced + two-tenant test data

---

## Gaps Summary

**Two gaps block the phase goal from being fully achieved:**

**Gap 1 — Critical: Database migration files not in main branch**

Alembic migrations (001, 002, 003) were written and committed during Plan 01 execution, but to a git worktree branch (`worktree-agent-af4cec45`) that was never merged into main. The files reside at `.claude/worktrees/agent-af4cec45/alembic/` (not under `agent-service/`).

This means:
- The `tenants` and `users` tables only exist if someone manually ran the migrations from the worktree
- RLS policies (the enforcement mechanism for TENANT-01/TENANT-02) are not deployable from main
- Any team member checking out main cannot set up the full system
- The SUMMARY for Plan 01 was committed to main (8acc50d) but its code commits (285cc3e, a114700, f9a116d) were not

Resolution: Cherry-pick the three alembic commits into main, adjusting file paths to be under `agent-service/alembic/` (the worktree committed them at the old project root level, before `agent-service/` was created as a subdirectory on main).

**Gap 2 — Warning: Test stubs never promoted after implementation**

Plan 00 created xfail stubs as scaffolding. Plan 02 implemented the full auth layer. However, the xfail markers were never removed from `test_auth.py` and `test_rbac.py`. This means running `pytest` shows all auth tests as "expected failures" even though the implementation is complete, providing no green signal that the implementation is correct. The RBAC test bodies also remain as `pass`.

Resolution: Remove `@pytest.mark.xfail` from test_auth.py (4 tests), implement the 3 test_rbac.py test bodies against real endpoints.

---

*Verified: 2026-03-29T21:30:00Z*
*Verifier: Claude (gsd-verifier)*
