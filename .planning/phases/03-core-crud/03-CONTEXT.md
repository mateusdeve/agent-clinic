# Phase 3: Core CRUD - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Full CRUD management for patients, doctors, appointments/agenda, and system users through the web interface. Receptionists manage day-to-day operations (scheduling, patient lookup), Admins manage doctors and users, Medicos see only their own agenda. All data is tenant-scoped via Phase 2 RLS.

</domain>

<decisions>
## Implementation Decisions

### Calendar / Agenda UI
- **D-01:** Three views: Day, Week, Month with toggle. Day for detailed slot scheduling, week for overview, month for long-range planning (AGENDA-01).
- **D-02:** Custom calendar built with date-fns for date math + Tailwind for layout. No heavy calendar library (no FullCalendar). Full control over green palette and MedIA brand.
- **D-03:** Color-coded appointment blocks by status: Agendado=blue, Confirmado=green, Realizado=gray, Cancelado=red with strikethrough. Scannable at a glance.
- **D-04:** Doctor filter dropdown on calendar (AGENDA-01). Medico role sees only their own calendar (AGENDA-07).

### Data Tables and Forms
- **D-05:** shadcn/ui Table + @tanstack/react-table for all entity lists (patients, doctors, users, appointments). Headless logic with full Tailwind control. Reusable column definitions per entity.
- **D-06:** Slide-over panel for create/edit forms. Side panel slides in from right — main list stays visible. Consistent across all 4 entities.
- **D-07:** Server-side pagination: 20 rows per page, page numbers at bottom. API returns paginated results with total count.
- **D-08:** Form validation with react-hook-form + zod schemas. Pattern established in login form (Phase 2).

### Patient Profile Page
- **D-09:** Tabbed layout: patient info header at top, then tabs: "Consultas" (appointment history) | "Conversas WhatsApp" (conversation history). Each tab loads independently.
- **D-10:** WhatsApp conversation history displayed as chat bubble timeline (read-only, like WhatsApp UI). Familiar for clinic staff reviewing past conversations.

### API Design Pattern
- **D-11:** RESTful FastAPI routers per entity: /api/patients, /api/appointments, /api/doctors, /api/users. Standard REST verbs (GET/POST/PUT/DELETE). Builds on existing FastAPI app + auth deps from Phase 2.
- **D-12:** Pagination response envelope: `{ items: [], total: int, page: int, per_page: int }`. Shared pagination helper across all routers.
- **D-13:** All endpoints use `get_current_user` + `get_db_for_tenant` from Phase 2 deps. Tenant isolation automatic via RLS.
- **D-14:** Existing backend functions in `src/tools/` (patients.py, appointments.py, doctors.py) are WhatsApp-bot oriented (use `_get_db()` without tenant context). New API routers use `get_db_for_tenant` from deps.py — do NOT modify existing tool functions to avoid breaking the bot.

### Claude's Discretion
- Exact column definitions for each entity table
- Calendar time slot granularity (15min/30min)
- Availability grid editing UX for doctors (DOC-03)
- User deactivation confirmation flow
- Password reset mechanism for admin-managed users
- Exact slide-over panel animation/sizing
- Search debounce timing and minimum characters
- Empty state illustrations/messages

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backend patterns
- `agent-service/src/tools/patients.py` — Existing patient CRUD (WhatsApp bot). Shows `_get_db()` + raw psycopg2 pattern. New API must NOT reuse these functions (they lack tenant context).
- `agent-service/src/tools/appointments.py` — Existing appointment CRUD. Shows SQL query patterns for the appointments table.
- `agent-service/src/tools/doctors.py` — Existing doctor queries. Shows table schema hints.
- `agent-service/src/api/auth.py` — FastAPI auth router from Phase 2. Pattern for new CRUD routers.
- `agent-service/src/api/deps.py` — `get_current_user`, `get_current_tenant`, `require_role`, `get_db_for_tenant`. All new endpoints MUST use these.

### Database schema
- `agent-service/alembic/versions/001_create_tenants_users.py` — tenants + users table schema
- `agent-service/alembic/versions/002_add_tenant_id_columns.py` — tenant_id on all data tables
- `agent-service/alembic/versions/003_enable_rls_policies.py` — RLS policies

### Frontend foundation
- `frontend/src/app/(dashboard)/layout.tsx` — Dashboard shell with role-based sidebar from Phase 2
- `frontend/src/app/globals.css` — Tailwind 4 design tokens
- `frontend/src/lib/auth.ts` — NextAuth config, session types

### Requirements
- `.planning/REQUIREMENTS.md` — AGENDA-01 through AGENDA-07, PAT-01 through PAT-05, DOC-01 through DOC-03, USER-01 through USER-05, API-01

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- shadcn/ui Button component — use for all form actions
- `cn()` utility — class merging
- react-hook-form + zod — pattern from login form (Phase 2)
- FastAPI auth deps — `get_current_user`, `require_role`, `get_db_for_tenant`
- Dashboard layout with sidebar nav — already has route links for Agenda, Pacientes, Medicos, Usuarios

### Established Patterns
- Raw psycopg2 with `_get_db()` context manager (bot) / `get_db_for_tenant` (new API)
- Module-scoped loggers with `[module]` prefix
- FastAPI routers mounted on main app via `app.include_router()`
- Alembic for migrations (initialized in Phase 2)
- NextAuth session with role/tenant_id claims

### Integration Points
- Dashboard sidebar already has navigation links — CRUD pages slot into `(dashboard)/` route group
- FastAPI app in webhook.py — new CRUD routers mount here alongside auth router
- PostgreSQL tables with tenant_id + RLS — all queries auto-scoped
- API endpoints consumed by Next.js server actions or client-side fetch

</code_context>

<specifics>
## Specific Ideas

- Calendar should feel clean and minimal (MedIA brand) — not like Google Calendar or Outlook
- Chat bubble timeline for WhatsApp history should visually match the hero chat card from landing page
- Slide-over panels should use the same green accent for headers/actions

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-core-crud*
*Context gathered: 2026-03-30*
