# Phase 2: Auth + Multi-Tenancy - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Secure login with role-based access (Admin, Recepcionista, Medico) and automatic clinic-scoped data isolation. Users can log in, stay authenticated across refreshes, and every data operation is automatically scoped to their clinic. No public registration — Admin creates accounts.

</domain>

<decisions>
## Implementation Decisions

### Auth Strategy
- **D-01:** NextAuth.js handles login UI/session on frontend, FastAPI issues its own JWT with tenant_id + role for API calls. Two token layers: NextAuth session cookie + FastAPI access token.
- **D-02:** FastAPI JWT stored in httpOnly secure cookie. Requires CSRF protection on state-changing endpoints.
- **D-03:** Invite-only registration — Admin creates user accounts. No public signup page.
- **D-04:** No password recovery in v1 — Admin resets passwords manually. Avoids email sending infrastructure.

### Login Page Design
- **D-05:** Split layout — left side: illustration with medical/clinic theme on green background. Right side: login form with email + password fields.
- **D-06:** Login page follows MedIA brand identity (green palette, DM fonts) from landing page.

### Role-Based Access (RBAC)
- **D-07:** Role checks on both layers — FastAPI middleware enforces roles on API routes (source of truth), Next.js middleware hides UI elements for UX. Defense in depth.
- **D-08:** Three roles only in v1: Admin, Recepcionista, Medico. No Super Admin — platform management done via database.
- **D-09:** All roles land on Dashboard after login. Dashboard content adapts by role (Medico sees their agenda, Admin sees full KPIs).

### Tenant Isolation
- **D-10:** PostgreSQL Row-Level Security (RLS) — add tenant_id column to all data tables, create RLS policies. DB enforces isolation even if application code misses a WHERE clause.
- **D-11:** Migration via ALTER TABLE ADD tenant_id + backfill existing rows to a default "Clinic 1" tenant, then enable RLS. Zero data loss, existing WhatsApp bot keeps working.
- **D-12:** Use Alembic for database migrations (already in requirements.txt). Set up migration chain for tenant_id columns, RLS policies, users table, and roles.
- **D-13:** tenant_id extracted from JWT automatically (per TENANT-03), never passed as URL/query parameter.

### Claude's Discretion
- Login form error states and validation UX
- Exact CSRF protection mechanism
- JWT token expiration times and refresh strategy
- Alembic directory structure and naming conventions
- RLS policy exact syntax and testing approach
- Left-side illustration choice/style for login page

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backend architecture
- `.planning/codebase/ARCHITECTURE.md` — Layer structure, API patterns, DB access via `_get_db()` context manager
- `.planning/codebase/STACK.md` — Tech stack: FastAPI, psycopg2, Redis, PostgreSQL
- `.planning/codebase/CONVENTIONS.md` — Naming patterns, code style, module design

### Database access patterns
- `agent-service/src/tools/appointments.py` — `_get_db()` pattern with raw psycopg2, parameterized queries
- `agent-service/src/tools/patients.py` — Patient CRUD with raw SQL
- `agent-service/src/api/session.py` — Redis session management pattern

### Frontend foundation
- `frontend/src/app/layout.tsx` — Root layout with DM fonts, pt-BR lang
- `frontend/src/app/globals.css` — Tailwind 4 @theme design tokens (green palette)
- `frontend/src/app/(auth)/login/page.tsx` — Auth route group stub

### Requirements
- `.planning/REQUIREMENTS.md` — AUTH-01 through AUTH-06, TENANT-01 through TENANT-03, API-02, API-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- shadcn/ui Button component (`frontend/src/components/ui/button.tsx`) — use for login form
- `cn()` utility (`frontend/src/lib/utils.ts`) — class merging
- Tailwind 4 design tokens (green palette, DM fonts) — login page must use same tokens
- `(auth)` route group stub already exists at `frontend/src/app/(auth)/`

### Established Patterns
- Backend uses raw psycopg2 with `_get_db()` context manager — no ORM
- All DB queries use parameterized `%s` placeholders
- Module-scoped loggers with `[module]` prefix
- Environment variables loaded via python-dotenv
- Alembic 1.16.5 already in requirements.txt but not initialized

### Integration Points
- FastAPI app in `agent-service/src/api/webhook.py` — new auth routes mount here
- Redis async client for sessions — separate from web auth (WhatsApp sessions)
- PostgreSQL tables (patients, appointments, doctors, conversations, knowledge_chunks) — all need tenant_id column
- Next.js middleware for route protection — intercepts requests before rendering
- `(dashboard)` route group stub exists — auth redirects here after login

</code_context>

<specifics>
## Specific Ideas

- Login page has split layout with illustration (medical/clinic theme) on left, form on right
- All existing data should be preserved during tenant migration (backfill to default clinic)
- The WhatsApp bot (Sofia/Carla pipeline) must continue working after tenant_id migration

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-auth-multi-tenancy*
*Context gathered: 2026-03-29*
