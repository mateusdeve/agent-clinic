---
phase: 05-dashboard-campaigns
plan: 02
subsystem: ui
tags: [recharts, dashboard, kpi, charts, next.js, typescript]

# Dependency graph
requires:
  - phase: 05-dashboard-campaigns
    provides: Phase 5 context, dashboard API endpoints (plan 01)
provides:
  - Dashboard /home page with 5 KPI cards, proximas consultas table, and admin-only charts
  - KpiCard, ProximasConsultas, TrendChart, EspecialidadeChart reusable components
  - DashboardClient use-client component fetching /api/dashboard/stats and /api/dashboard/charts
  - Medico redirect from /home to /agenda
  - Templates and Campanhas sidebar links for admin role
  - Dashboard TypeScript types: DashboardStats, ProximaConsulta, DashboardCharts, TrendDataPoint, EspecialidadeDataPoint
  - Phase 5 types: MessageTemplate, Campaign, CampaignDetail, CampaignRecipient, SegmentPreview
affects: [05-03, 05-04, 05-05]

# Tech tracking
tech-stack:
  added: [recharts]
  patterns:
    - Server Component passes role to use-client DashboardClient (no data fetching in layout)
    - Recharts components always get "use client" directive to prevent SSR crash
    - Admin-only charts rendered conditionally via {role === "admin" && charts && ...} (not display:none)
    - KpiCard is pure presentational RSC — no hooks, no "use client"

key-files:
  created:
    - frontend/src/components/dashboard/KpiCard.tsx
    - frontend/src/components/dashboard/ProximasConsultas.tsx
    - frontend/src/components/dashboard/TrendChart.tsx
    - frontend/src/components/dashboard/EspecialidadeChart.tsx
    - frontend/src/components/dashboard/DashboardClient.tsx
  modified:
    - frontend/src/lib/types.ts
    - frontend/src/app/(dashboard)/home/page.tsx
    - frontend/src/app/(dashboard)/layout.tsx
    - frontend/package.json

key-decisions:
  - "KpiCard is RSC (no use client) — pure presentational with icon + label + value"
  - "DashboardClient fetches both stats and charts on mount; charts fetch is admin-only"
  - "ProximasConsultas uses plain HTML table (not DataTable) — no pagination needed for max 20 rows"
  - "Recharts LineChart and BarChart each have use client directive per SSR pitfall rule"

patterns-established:
  - "Dashboard KPI pattern: Server Component (auth/role) -> Client Component (data fetch + render)"
  - "Admin-only chart visibility: conditional render, not CSS display:none"

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-04]

# Metrics
duration: 15min
completed: 2026-03-30
---

# Phase 5 Plan 02: Dashboard Frontend Summary

**Operational dashboard at /home with 5 KPI cards, proximas consultas table, and admin-only Recharts charts — plus medico redirect and sidebar nav updates for Templates/Campanhas**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-30T14:15:00Z
- **Completed:** 2026-03-30T14:30:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Replaced /home placeholder with full operational dashboard (KPIs, appointments table, charts)
- Installed recharts and created 4 new chart/KPI components, all with correct client/server boundaries
- Added Templates and Campanhas sidebar nav links for admin role
- Medico visiting /home is now redirected to /agenda per D-04

## Task Commits

Each task was committed atomically:

1. **Task 1: Install recharts + create dashboard types + KPI/chart components** - `bc257aa` (feat)
2. **Task 2: Dashboard /home page rewrite + sidebar navigation updates** - `d44d68d` (feat)

## Files Created/Modified
- `frontend/package.json` - Added recharts dependency
- `frontend/src/lib/types.ts` - Added DashboardStats, ProximaConsulta, DashboardCharts, TrendDataPoint, EspecialidadeDataPoint, MessageTemplate, Campaign, CampaignDetail, CampaignRecipient, SegmentPreview
- `frontend/src/components/dashboard/KpiCard.tsx` - Reusable KPI card with icon, label, value (RSC)
- `frontend/src/components/dashboard/ProximasConsultas.tsx` - Today's appointments table with StatusBadge
- `frontend/src/components/dashboard/TrendChart.tsx` - Recharts LineChart (7-day trend) with use client
- `frontend/src/components/dashboard/EspecialidadeChart.tsx` - Recharts BarChart (by specialty) with use client
- `frontend/src/components/dashboard/DashboardClient.tsx` - Client component fetching stats/charts + rendering full dashboard layout
- `frontend/src/app/(dashboard)/home/page.tsx` - Server Component: auth check, medico redirect, renders DashboardClient
- `frontend/src/app/(dashboard)/layout.tsx` - Added Templates and Campanhas admin-only sidebar links

## Decisions Made
- KpiCard kept as RSC (no use client) since it's purely presentational with no hooks
- ProximasConsultas uses a simple HTML table (not DataTable) — max 20 rows, no pagination needed
- Recharts components always get "use client" to prevent SSR crash (recharts uses window/document)
- Admin-only charts use conditional rendering (not display:none) to prevent unnecessary fetches

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - Next.js build passed without TypeScript errors on first attempt.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dashboard frontend complete. /home page fully operational for admin and recepcionista.
- Medico role correctly redirected to /agenda.
- All Phase 5 TypeScript types defined (MessageTemplate, Campaign, CampaignRecipient) — ready for plans 03-05.
- Sidebar navigation ready with Templates and Campanhas placeholders for plan 03/04 page implementations.

---
*Phase: 05-dashboard-campaigns*
*Completed: 2026-03-30*
