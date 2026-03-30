---
phase: 03-core-crud
plan: "01"
subsystem: frontend-foundation
tags: [migration, types, api-wrapper, components, shadcn, tanstack-table]
dependency_graph:
  requires: [02-auth-multi-tenancy]
  provides: [crud-schema, shared-types, api-fetch, data-table, slide-over, status-badge]
  affects: [03-02, 03-03, 03-04, 03-05, 03-06, 03-07]
tech_stack:
  added: ["@tanstack/react-table@8.21.3", "date-fns@4.1.0", "shadcn/ui table/badge/tabs/input/select/dialog"]
  patterns: ["manualPagination server-side table", "slide-over panel", "apiFetch Bearer injection", "Alembic raw SQL idempotent DDL"]
key_files:
  created:
    - agent-service/alembic/versions/004_crud_schema_additions.py
    - frontend/src/lib/types.ts
    - frontend/src/lib/api.ts
    - frontend/src/components/ui/table.tsx
    - frontend/src/components/ui/badge.tsx
    - frontend/src/components/ui/tabs.tsx
    - frontend/src/components/ui/input.tsx
    - frontend/src/components/ui/select.tsx
    - frontend/src/components/ui/dialog.tsx
    - frontend/src/components/dashboard/DataTable.tsx
    - frontend/src/components/dashboard/SlideOver.tsx
    - frontend/src/components/dashboard/StatusBadge.tsx
  modified:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/.env.local
decisions:
  - "shadcn CLI (npx shadcn@latest add) succeeded this phase — all 6 primitives created via CLI without manual fallback"
  - "apiFetch accesses session.access_token via unknown cast to match NextAuth v5 beta session shape from auth.ts"
  - "DataTable uses onPaginationChange as React.Dispatch to support functional updater pattern from @tanstack/react-table"
  - "SlideOver backdrop uses pointer-events toggle (not display:none) for smooth opacity transition"
metrics:
  duration: "13 minutes"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_created: 12
  files_modified: 3
---

# Phase 03 Plan 01: Foundation Layer (Schema + Types + Components) Summary

**One-liner:** Alembic migration 004 adds UUID patients.id, doctors.user_id, doctor_schedules RLS, and blocked_slots table; plus @tanstack/react-table DataTable, SlideOver, and StatusBadge components with shared TypeScript interfaces and authenticated apiFetch wrapper.

## What Was Built

### Task 1: Migration 004 + Frontend Deps + Shared Types + API Wrapper

**Migration 004** (`agent-service/alembic/versions/004_crud_schema_additions.py`) with revision chain 003 -> 004:
- `patients`: UUID `id` with backfill + `idx_patients_id`, `data_nascimento DATE`, `notas TEXT`
- `doctors`: `user_id UUID REFERENCES users(id)` for doctor-portal isolation (AGENDA-07)
- `doctor_schedules`: `tenant_id UUID` backfilled from doctors join + NOT NULL + FK + RLS + policy
- `blocked_slots`: New table with RLS — id, doctor_id, tenant_id, blocked_date, start/end time, reason
- `appointments`: Status CHECK constraint extended to include `agendado`, `confirmado`, `realizado`, `cancelado` alongside existing `active`/`cancelled` (backward compat for bot)
- All DDL uses IF NOT EXISTS / DO $$ patterns for idempotency

**Frontend dependencies installed:** `@tanstack/react-table@8.21.3`, `date-fns@4.1.0`

**`frontend/src/lib/types.ts`** exports: `PaginatedResponse<T>`, `Patient`, `Doctor`, `DoctorSchedule`, `Appointment`, `AppointmentStatus`, `SystemUser`, `ConversationMessage`, `BlockedSlot`

**`frontend/src/lib/api.ts`** exports `apiFetch<T>` — injects `Authorization: Bearer {access_token}` from NextAuth session into all API calls, throws `Error(detail)` on non-ok responses

### Task 2: shadcn Primitives + Dashboard Components

**shadcn/ui primitives** via `npx shadcn@latest add`: `table`, `badge`, `tabs`, `input`, `select`, `dialog`

**`DataTable<TData>`** — generic server-side pagination table:
- `useReactTable` with `manualPagination: true` and `getCoreRowModel()`
- Skeleton rows (3x pulse) while `isLoading=true`
- "Nenhum registro encontrado" empty state (pt-BR)
- "Pagina X de Y" with Anterior/Proximo buttons

**`SlideOver`** — slide-from-right panel:
- `translate-x-full` / `translate-x-0` transition (300ms ease-in-out)
- Backdrop with opacity transition (200ms) + pointer-events toggle
- `max-w-md`, green-600 header, Escape key close

**`StatusBadge`** — appointment status chip:
- `agendado` -> blue-100/blue-700
- `confirmado` -> green-100/green-700
- `realizado` -> gray-100/gray-600
- `cancelado` -> red-100/red-700 + `line-through`

## Verification Results

- `npx tsc --noEmit`: PASS (zero errors)
- Migration 004 revision chain (003 -> 004): PASS
- `@tanstack/react-table` and `date-fns` in package.json: PASS
- All 3 dashboard components exported and importable: PASS

## Deviations from Plan

None — plan executed exactly as written. shadcn CLI succeeded (unlike Phase 1 where it needed manual fallback).

## Known Stubs

None. All components are fully wired stubs — DataTable is generic and accepts real data props; StatusBadge maps all 4 live statuses; apiFetch calls the real FastAPI endpoint. No placeholder data flows to any UI.

## Commits

- `365b283`: feat(03-01): migration 004 + shared types + API wrapper + frontend deps
- `261e69c`: feat(03-01): dashboard components — DataTable, SlideOver, StatusBadge + shadcn primitives

## Self-Check: PASSED
