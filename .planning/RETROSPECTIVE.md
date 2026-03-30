# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-30
**Phases:** 6 | **Plans:** 25 | **Tasks:** 50

### What Was Built
- Full-stack SaaS clinic management platform (Next.js 16 + FastAPI)
- Multi-tenant auth with PostgreSQL RLS, JWT/RBAC, NextAuth v5
- Landing page, dashboard with KPIs/charts, CRUD for all entities
- Real-time WhatsApp inbox with Socket.IO and human takeover controls
- Message templates with live preview and bulk campaign dispatch
- Mobile responsive layout, error boundaries, loading skeletons

### What Worked
- Wave-based plan execution: parallel independent work, sequential dependencies
- xfail test stubs written before implementation (Phase 2) — guided development and flagged real gaps
- Custom calendar with date-fns instead of FullCalendar — full design control, no heavy dependency
- proxy.ts route protection pattern for Next.js 16 — clean auth boundary
- Factory pattern for DataTable columns (buildPatientColumns, buildTemplateColumns) — reusable across pages
- FOR UPDATE SKIP LOCKED for campaign dispatch — concurrent-safe without complex locking
- CSS-only responsive breakpoints (max-[900px]:) — no JS media query listeners needed

### What Was Inefficient
- Some SUMMARY.md files had empty one-liner fields — extraction tooling didn't catch all formats
- Phase 5 and 6 progress table in ROADMAP.md fell out of sync with actual plan checkboxes
- shadcn CLI failed in Phase 1 (required manual setup) but worked fine in Phase 3 — inconsistent tooling behavior

### Patterns Established
- Tailwind 4 CSS-first design tokens via @theme block (no tailwind.config.ts)
- React Server Components by default, "use client" only when needed (hooks, events)
- ErrorAlert as server-compatible presentational component (no "use client")
- loading.tsx files as Server Components for route transition skeletons
- unstable_retry (not reset) for Next.js 16.2.x error boundaries
- COALESCE for backward-compatible column access (bot legacy + new schema)
- Module-level Socket.IO singleton shared across routers

### Key Lessons
1. RLS policies must be applied to production database during deployment — writing migrations alone doesn't enable them
2. NextAuth v5 beta has Session type limitations — use local ExtendedUser cast for jwt callback
3. Zod v4 changed enum API — 'as const' instead of required_error
4. python-socketio cors_allowed_origins=[] prevents duplicate CORS headers when co-hosted with FastAPI CORSMiddleware
5. Next.js route groups with page.tsx at / cause build conflicts — use sub-paths (/login, /home) instead

### Cost Observations
- Model mix: ~70% opus, ~20% sonnet, ~10% haiku (estimated)
- Sessions: ~20+ across 7 days
- Notable: 25 plans in 7 days — high velocity enabled by clear phase dependencies and parallel plan execution

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 6 | 25 | Initial milestone — established GSD workflow patterns |

### Cumulative Quality

| Milestone | Tests | Known Issues | Zero-Dep Additions |
|-----------|-------|--------------|-------------------|
| v1.0 | 10 (3 auth + 3 RBAC + 3 tenant + 1 connection) | 2 RLS tests fail (infra gap) | 0 |

### Top Lessons (Verified Across Milestones)

1. Write test stubs (xfail) before implementation to guide development and surface real gaps
2. CSS-first responsive design (Tailwind breakpoints) avoids JS complexity
3. Infrastructure deployment steps must be documented alongside migration code
