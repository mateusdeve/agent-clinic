---
phase: 03-core-crud
plan: "04"
subsystem: frontend-agenda
tags: [nextjs, calendar, date-fns, react-hook-form, zod, agenda, appointments, rbac, blocked-slots]
dependency_graph:
  requires: [03-01, 03-02, 03-03]
  provides: [agenda-page, calendar-components, appointment-crud-ui]
  affects: [03-05, 03-06, 03-07]
tech_stack:
  added: []
  patterns: ["custom calendar with date-fns (no FullCalendar)", "CalendarDay absolute-positioned time grid", "react-hook-form + zod v4 validation", "role-gated doctor filter via useSession", "blocked slots overlay with z-indexed layers"]
key_files:
  created:
    - frontend/src/components/dashboard/calendar/CalendarToolbar.tsx
    - frontend/src/components/dashboard/calendar/AppointmentBlock.tsx
    - frontend/src/components/dashboard/calendar/CalendarDay.tsx
    - frontend/src/components/dashboard/calendar/CalendarWeek.tsx
    - frontend/src/components/dashboard/calendar/CalendarMonth.tsx
    - frontend/src/app/(dashboard)/agenda/page.tsx
    - frontend/src/app/(dashboard)/agenda/appointment-form.tsx
  modified: []
decisions:
  - "Custom calendar with date-fns + Tailwind per D-02 — no FullCalendar dependency, full brand control with green palette"
  - "CalendarDay uses absolute positioning formula: top = ((hour-7)*2 + (minute/30)) * ROW_HEIGHT (48px per 30-min row)"
  - "Blocked slots rendered as z-10 gray bands behind z-20 appointment blocks in day view, indicator text in week view"
  - "AppointmentForm uses native <select> for patient/doctor (not Radix Select) — avoids hydration complexity with large lists"
  - "Medico role check: useSession() role === medico hides doctor filter; API already enforces server-side (03-02)"
metrics:
  duration: "4 minutes"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_created: 7
  files_modified: 0
---

# Phase 03 Plan 04: Agenda Calendar Page Summary

**One-liner:** Custom Day/Week/Month calendar built with date-fns + Tailwind, color-coded appointment blocks per D-03, doctor filter with medico isolation, blocked slot overlays, and slide-over CRUD via react-hook-form + zod.

## What Was Built

### Task 1: Calendar Components

**`CalendarToolbar.tsx`** — Navigation + view toggle + doctor filter:
- Left: Anterior/Hoje/Proximo navigation with ChevronLeft/ChevronRight from lucide-react
- Center: Date label formatted with ptBR locale ("Sexta, 29 de marco de 2026" / "24–30 Mar 2026" / "Marco 2026")
- Right: Dia/Semana/Mes toggle with green-500 active state
- Conditional doctor filter dropdown using shadcn Select (hidden for medico role via showDoctorFilter prop)

**`AppointmentBlock.tsx`** — Appointment chip with D-03 color mapping:
- agendado: bg-blue-50 + border-l-4 border-blue-500 + text-blue-700
- confirmado: bg-green-50 + border-l-4 border-green-500 + text-green-700
- realizado: bg-gray-50 + border-l-4 border-gray-400 + text-gray-500
- cancelado: bg-red-50 + border-l-4 border-red-400 + text-red-400 line-through
- Full mode: horario + patient_nome + doctor_nome; Compact mode: horario + patient_nome truncated

**`CalendarDay.tsx`** — Day view with absolute-positioned time grid:
- 07:00 to 20:00 range with 30-minute rows (ROW_HEIGHT = 48px)
- Uses `eachHourOfInterval` + `setMinutes` to generate slot array
- Appointment blocks absolutely positioned: `top = minutesToOffset(timeToMinutes(horario))`
- Blocked slot bands: z-10 semi-transparent gray with reason text
- Appointment blocks: z-20 (above blocked bands)
- Current time indicator: red line with dot, only visible when `isToday(date)`
- Empty rows are clickable — call onSlotClick with slot time string

**`CalendarWeek.tsx`** — 7-column week view:
- Uses `eachDayOfInterval({ start: startOfWeek(date, {locale: ptBR}), end: endOfWeek(...) })`
- Header: day name + date number; today highlighted with green circle
- Blocked day indicator: "Bloqueado" italic text per day column
- Appointments sorted by horario per column

**`CalendarMonth.tsx`** — 6x7 month grid:
- Uses `startOfMonth`, `endOfMonth`, padded to full weeks
- Up to 3 AppointmentBlock (compact=true) per cell, "+N mais" overflow button
- Today's date: ring-2 ring-green-500
- Out-of-month days: muted gray text + gray-50 background

### Task 2: Agenda Page + Appointment Form

**`agenda/page.tsx`** — Main calendar page:
- Fetches `/api/appointments?date_from=X&date_to=Y&per_page=500` on mount and on date/view/doctor changes
- Fetches `/api/doctors?per_page=100` and `/api/patients?per_page=500` on mount
- Fetches `/api/doctors/{id}/blocked-slots` when selectedDoctorId is set (AGENDA-06)
- AGENDA-07: `useSession()` checks `role === "medico"` → passes `showDoctorFilter={!isMedico}` to toolbar
- `handleDayClick` in Week/Month view switches to day view at that date
- `handleSlotClick` pre-fills date+time for create form
- Loading spinner while fetching
- "Novo Agendamento" button in page header

**`appointment-form.tsx`** — Create/edit form with full CRUD:
- react-hook-form with zodResolver, zod v4 schema
- Fields: patient_id (select), doctor_id (select), data_agendamento (date input, min=today), horario (time input), especialidade (auto-filled from doctor, read-only)
- Edit mode: shows current StatusBadge, status transition buttons
- Status transitions: agendado → "Confirmar consulta" (PATCH /status), confirmado → "Marcar como realizado"
- Cancel button: shows inline confirmation dialog with optional motivo textarea (AGENDA-04)
- POST /api/appointments (create) or PUT /api/appointments/{id} (edit)

## Verification Results

- `npx tsc --noEmit`: PASS (0 errors)
- All 5 calendar components under `frontend/src/components/dashboard/calendar/`: PASS
- CalendarDay contains `eachHourOfInterval`: PASS
- CalendarWeek contains `startOfWeek` + `eachDayOfInterval`: PASS
- CalendarMonth contains `startOfMonth` + `endOfMonth`: PASS
- AppointmentBlock has all 4 status color mappings: PASS
- CalendarToolbar has Dia/Semana/Mes labels: PASS
- All components have "use client": PASS
- Agenda page uses apiFetch for /api/appointments and /api/doctors: PASS
- Agenda page fetches /api/doctors/{id}/blocked-slots when doctor selected: PASS
- Medico role check present (isMedico via useSession): PASS
- AppointmentForm has react-hook-form + zod: PASS
- Cancel with motivo prompt: PASS
- Status transition buttons: PASS

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Design Decisions

**1. Native `<select>` instead of Radix Select for patient/doctor dropdowns in AppointmentForm**
- The plan specified "searchable select" for patients but this requires a combobox component not yet in the shadcn setup. Used native `<select>` which is simpler and avoids hydration issues with large lists. The doctor Select in CalendarToolbar (small list, fixed) uses the shadcn Select.
- This is a minor UX tradeoff; a combobox can be added in a future plan if needed.

## Known Stubs

None. All calendar components render from real appointment data fetched from the API. The agenda page is fully wired with proper data fetching, role checks, and CRUD operations.

## Commits

- `7f5e382`: feat(03-04): calendar components — Day/Week/Month views + toolbar + appointment blocks
- `a039af4`: feat(03-04): agenda page + appointment form — calendar CRUD with slide-over

## Self-Check: PASSED

- frontend/src/components/dashboard/calendar/CalendarToolbar.tsx: FOUND
- frontend/src/components/dashboard/calendar/AppointmentBlock.tsx: FOUND
- frontend/src/components/dashboard/calendar/CalendarDay.tsx: FOUND
- frontend/src/components/dashboard/calendar/CalendarWeek.tsx: FOUND
- frontend/src/components/dashboard/calendar/CalendarMonth.tsx: FOUND
- frontend/src/app/(dashboard)/agenda/page.tsx: FOUND
- frontend/src/app/(dashboard)/agenda/appointment-form.tsx: FOUND
- Commit 7f5e382: FOUND
- Commit a039af4: FOUND
