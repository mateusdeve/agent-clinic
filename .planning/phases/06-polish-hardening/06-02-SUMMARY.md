---
phase: 06-polish-hardening
plan: 02
subsystem: ui
tags: [nextjs, error-boundary, loading-skeleton, tailwind, react]

requires:
  - phase: 05-dashboard-campaigns
    provides: DashboardClient component and dashboard page structure

provides:
  - global-error.tsx root-level error boundary with branded recovery page
  - dashboard error.tsx segment error boundary with retry UI
  - ErrorAlert reusable inline error banner component
  - (dashboard)/loading.tsx generic route transition skeleton
  - (dashboard)/home/loading.tsx KPI-grid-shaped home page skeleton
  - DashboardClient updated to use ErrorAlert for API failures

affects:
  - phase-06-polish-hardening remaining plans (responsive, tenant isolation)

tech-stack:
  added: []
  patterns:
    - "unstable_retry in Next.js 16.2.x error boundaries instead of reset"
    - "Server Component loading.tsx files for route transition skeletons"
    - "Presentational ErrorAlert component importable in both server and client components"

key-files:
  created:
    - frontend/src/app/global-error.tsx
    - frontend/src/app/(dashboard)/error.tsx
    - frontend/src/app/(dashboard)/loading.tsx
    - frontend/src/app/(dashboard)/home/loading.tsx
    - frontend/src/components/dashboard/ErrorAlert.tsx
  modified:
    - frontend/src/components/dashboard/DashboardClient.tsx

key-decisions:
  - "Use unstable_retry (not reset) in error boundary props — Next.js 16.2.x breaking change"
  - "ErrorAlert is NOT use client — pure presentational for server and client import"
  - "loading.tsx files are Server Components — no use client directive needed"

patterns-established:
  - "Error boundaries: global-error.tsx requires full html/body shell; segment error.tsx does not"
  - "Loading skeletons use animate-pulse with gray-100 background matching page layout structure"

requirements-completed:
  - SC-2
  - SC-4

duration: 10min
completed: 2026-03-30
---

# Phase 06 Plan 02: Error Boundaries and Loading States Summary

**Next.js error boundaries (global + segment) with unstable_retry, reusable ErrorAlert component, and route-transition loading skeletons for dashboard**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-30T16:30:00Z
- **Completed:** 2026-03-30T16:40:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Root layout errors now render a branded recovery page with "Tentar novamente" button instead of blank white screen
- Dashboard segment errors render AlertCircle error UI with retry, logged to console
- Route transitions between dashboard pages show animate-pulse skeleton loading states
- Home page shows KPI-grid-shaped skeleton (5-card grid + 2-column charts + consultas block)
- DashboardClient API failures now use standardized ErrorAlert inline banner

## Task Commits

1. **Task 1: Error boundaries and ErrorAlert** - `5e25008` (feat)
2. **Task 2: Loading skeleton files** - `55c8f0f` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified
- `frontend/src/app/global-error.tsx` - Root-level error boundary with html/body shell and unstable_retry
- `frontend/src/app/(dashboard)/error.tsx` - Dashboard segment error boundary with AlertCircle and retry button
- `frontend/src/components/dashboard/ErrorAlert.tsx` - Reusable inline error banner (border-red-200, AlertCircle)
- `frontend/src/app/(dashboard)/loading.tsx` - Generic page transition skeleton (header + 5 row skeleton)
- `frontend/src/app/(dashboard)/home/loading.tsx` - Home page skeleton matching KPI grid + charts layout
- `frontend/src/components/dashboard/DashboardClient.tsx` - Updated error state to use ErrorAlert

## Decisions Made
- Used `unstable_retry` (not `reset`) in both error boundary files — Next.js 16.2.x uses this prop name per the AGENTS.md warning about breaking changes
- ErrorAlert has no `'use client'` directive — pure presentational component importable by both server and client components
- Loading skeleton files are Server Components — Next.js wraps page.tsx in Suspense automatically for route transitions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Error boundary infrastructure is complete for all dashboard routes
- ErrorAlert component available for use in any future client components that fetch data
- Loading skeletons ready for all dashboard route transitions
- Ready for remaining Phase 06 plans (responsive layout, tenant isolation tests)

---
*Phase: 06-polish-hardening*
*Completed: 2026-03-30*
