---
phase: 03-core-crud
plan: "06"
subsystem: frontend-admin-pages
tags: [react, tanstack-table, react-hook-form, zod, schedule-grid, role-management, password-reset]
dependency_graph:
  requires: [03-01, 03-03]
  provides: [medicos-page, usuarios-page, schedule-grid-editor, DOC-01, DOC-02, DOC-03, USER-01, USER-02, USER-03, USER-04, USER-05]
  affects: [03-07]
tech_stack:
  added: []
  patterns: ["react-hook-form + zod form validation", "drag-select schedule grid with mouse events", "inline toggle switch with self-modification guard", "admin-managed password reset dialog"]
key_files:
  created:
    - frontend/src/app/(dashboard)/medicos/columns.tsx
    - frontend/src/app/(dashboard)/medicos/doctor-form.tsx
    - frontend/src/app/(dashboard)/medicos/schedule-grid.tsx
    - frontend/src/app/(dashboard)/medicos/page.tsx
    - frontend/src/app/(dashboard)/usuarios/columns.tsx
    - frontend/src/app/(dashboard)/usuarios/user-form.tsx
    - frontend/src/app/(dashboard)/usuarios/page.tsx
  modified: []
decisions:
  - "schedule-grid uses DAY_INDICES mapping [1,2,3,4,5,6,0] for Mon-Sun display order, converting from API day_of_week (0=Sunday) to visual grid column index"
  - "doctor-form renders both Select dropdown and free-text Input for especialidade — dropdown for common specialties, text input overwrites for arbitrary values"
  - "user-form split into CreateForm and EditForm sub-components to isolate zod schemas and avoid conditional form field complexity"
  - "zod enum uses 'as const' not required_error — zod v4 removed required_error from enum overload signature"
  - "schedule-grid builds consecutive time ranges from active cells via addThirtyMinutes chaining for atomic PUT slots payload"
  - "current user self-deactivation prevention in columns.tsx via currentUserId prop from useSession() comparison"
metrics:
  duration: "4 minutes"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_created: 7
  files_modified: 0
---

# Phase 03 Plan 06: Doctors + Users Admin Pages Summary

**One-liner:** Doctor management page at /medicos (list, create/edit slide-over, drag-select weekly availability grid) and user management page at /usuarios (list, create/edit slide-over, inline status toggle with self-protection, admin password reset dialog).

## What Was Built

### Task 1: Doctor Management Page

**`frontend/src/app/(dashboard)/medicos/columns.tsx`** — `ColumnDef<Doctor>[]` with columns: nome (Medico), especialidade, crm, and actions (Editar + Horarios buttons). DOC-01.

**`frontend/src/app/(dashboard)/medicos/doctor-form.tsx`** — react-hook-form + zod. Fields: nome (required), especialidade (Select dropdown with 10 common specialties + free-text fallback Input), crm (required), user_id (optional Select populated with active medico-role users for AGENDA-07 linkage). Supports both create ("Cadastrar") and edit ("Salvar") modes. DOC-02.

**`frontend/src/app/(dashboard)/medicos/schedule-grid.tsx`** — Weekly availability grid editor. DOC-03.
- 7-column layout (Seg-Dom) x 26 rows (07:00-19:30, 30-min slots)
- On mount: fetches existing schedules from `/api/doctors/{id}/schedules`, builds active cell Set
- Click to toggle individual cells; click-drag to select/deselect multiple cells
- Active cells: `bg-green-100 border-green-400`; Inactive: `bg-white border-gray-100`
- "Salvar Horarios" → `buildScheduleSlots()` merges consecutive active cells into time ranges → PUT `/api/doctors/{id}/schedules` with `{ slots: [...] }`
- Skeleton grid while loading; error/success inline messages

**`frontend/src/app/(dashboard)/medicos/page.tsx`** — Page with DataTable + two SlideOvers:
- Primary SlideOver (max-w-md): DoctorForm for create/edit
- Secondary inline panel (max-w-2xl): ScheduleGrid for availability editing
- Fetches doctors with pagination; fetches medico-role users for form linkage
- POST to create, PUT to update; refetches on success

### Task 2: User Management Page

**`frontend/src/app/(dashboard)/usuarios/columns.tsx`** — `ColumnDef<SystemUser>[]` with columns: name, email, role (colored badge: admin=purple, recepcionista=blue, medico=green), is_active (status badge + toggle switch), actions (Editar + Redefinir Senha). Toggle switch disabled if `user.id === currentUserId` (self-deactivation prevention). USER-01, USER-04.

**`frontend/src/app/(dashboard)/usuarios/user-form.tsx`** — Two zod schemas and two sub-components:
- `CreateForm`: name, email, password (min 6), role select — "Criar Usuario". USER-02.
- `EditForm`: name/email read-only display, role select editable — "Salvar". USER-03.
- zod `enum` uses `as const` (zod v4 removed `required_error` from enum overload)

**`frontend/src/app/(dashboard)/usuarios/page.tsx`** — Full user management page. USER-01 through USER-05:
- DataTable with pagination; SlideOver for create/edit
- Status toggle opens Dialog: "Desativar usuario X?" / "Reativar usuario X?" confirmation. USER-04.
- Password reset opens Dialog: new password input → POST `/api/users/{id}/reset-password`. Success/error inline message. USER-05.
- `currentUserId` from `useSession()` passed to columns for self-protection guard.

## Verification Results

- `npx tsc --noEmit`: PASS (zero errors after zod enum fix)
- Doctor page columns (nome, especialidade, crm, actions): PASS
- Schedule grid 7-column layout with time slots: PASS
- User form create mode (with password) and edit mode (role only): PASS
- Status toggle with self-deactivation guard: PASS
- Password reset dialog flow: PASS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] zod enum required_error removed in zod v4**
- **Found during:** Task 2 TypeScript compilation
- **Issue:** `z.enum(["admin", "recepcionista", "medico"], { required_error: "..." })` fails in zod v4 — `required_error` removed from enum's params overload
- **Fix:** Replaced `{ required_error: "..." }` with `as const` assertion: `z.enum(["admin", "recepcionista", "medico"] as const)`
- **Files modified:** `frontend/src/app/(dashboard)/usuarios/user-form.tsx`
- **Commit:** 6869e73

## Known Stubs

None. Both pages call real API endpoints (`/api/doctors`, `/api/users`, `/api/doctors/{id}/schedules`, `/api/users/{id}/reset-password`, etc.) wired in Plan 03. All form submissions, pagination, and status changes make real API calls.

## Commits

- `c21df38`: feat(03-06): doctor management page — list, create/edit form, availability schedule grid
- `6869e73`: feat(03-06): user management page — list, create, role change, status toggle, password reset

## Self-Check: PASSED
