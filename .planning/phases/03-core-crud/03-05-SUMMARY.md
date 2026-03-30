---
phase: 03-core-crud
plan: "05"
subsystem: frontend-patients
tags: [patients, datatable, slide-over, react-hook-form, zod, tabs, whatsapp-timeline]
dependency_graph:
  requires: [03-01, 03-02]
  provides: [patients-list-page, patients-profile-page, appointment-history-component, whatsapp-timeline-component]
  affects: []
tech_stack:
  added: []
  patterns: ["buildPatientColumns factory with action callbacks", "debounced search with useDebounce hook", "chat bubble timeline (user=green-right, bot=white-left)", "cancellable useEffect data fetch pattern"]
key_files:
  created:
    - frontend/src/app/(dashboard)/pacientes/page.tsx
    - frontend/src/app/(dashboard)/pacientes/columns.tsx
    - frontend/src/app/(dashboard)/pacientes/patient-form.tsx
    - frontend/src/app/(dashboard)/pacientes/[id]/page.tsx
    - frontend/src/components/dashboard/patient/AppointmentHistory.tsx
    - frontend/src/components/dashboard/patient/WhatsAppTimeline.tsx
  modified: []
decisions:
  - "buildPatientColumns factory pattern: columns.tsx exports a function (not array) to allow action callbacks (onEdit, router.push) without prop drilling through DataTable"
  - "ActionCell as separate component: hooks (useRouter) require a component context — extracted from column defs to avoid invalid hook call"
  - "Debounce threshold: 2-char minimum + 300ms delay before search fires — prevents 1-char queries hitting API"
  - "AppointmentHistory uses simple table (not DataTable): appointment history per patient is bounded data, no pagination needed"
  - "WhatsApp bubbles: user=bg-green-500 text-white rounded-2xl rounded-br-sm, bot=bg-white border rounded-2xl rounded-bl-sm — matches D-10 and landing page chat card"
  - "Cancellable fetch pattern: cancelled flag in useEffect cleanup prevents state updates on unmounted components"
metrics:
  duration: "12 minutes"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_created: 6
  files_modified: 0
---

# Phase 03 Plan 05: Patient Management Pages Summary

**One-liner:** Patient list at /pacientes with DataTable, debounced search, and react-hook-form+zod slide-over CRUD; patient profile at /pacientes/[id] with info header and tabbed appointment history (StatusBadge) and WhatsApp chat bubble timeline.

## What Was Built

### Task 1: Patient List Page

**`frontend/src/app/(dashboard)/pacientes/columns.tsx`** — ColumnDef factory:
- `buildPatientColumns(callbacks)` returns 5 columns: nome (bold), phone (monospace), data_nascimento (date-fns format or "-"), total_consultas (tabular-nums), actions
- `ActionCell` component uses `useRouter()` for "Ver Perfil" nav and `callbacks.onEdit` for slide-over open
- Action pattern: separate component allows hook usage (useRouter) within column cell

**`frontend/src/app/(dashboard)/pacientes/patient-form.tsx`** — react-hook-form + zod form:
- Zod schema: nome (min 2, max 120), phone (regex `/^\d{10,11}$/`), data_nascimento (optional date input), notas (optional textarea)
- Pre-fills from `patient` prop for edit mode; empty defaults for create
- Submit button: "Cadastrar" (create) or "Salvar" (edit) — with spinner during submission
- All labels in pt-BR

**`frontend/src/app/(dashboard)/pacientes/page.tsx`** — main list page:
- `useDebounce(value, 300)` custom hook — fires search after 300ms, minimum 2 chars
- `apiFetch<PaginatedResponse<Patient>>("/api/patients?search=...&page=...&per_page=20")`
- Resets pageIndex to 0 on search change (separate useEffect)
- "Novo Paciente" button (Plus icon) opens SlideOver with null patient
- Row "Editar" opens SlideOver with patient pre-loaded
- Row "Ver Perfil" navigates to /pacientes/{id}
- POST /api/patients for create, PUT /api/patients/{id} for edit

### Task 2: Patient Profile Page

**`frontend/src/components/dashboard/patient/AppointmentHistory.tsx`**:
- Fetches `apiFetch<Appointment[]>("/api/patients/${patientId}/appointments")` on mount
- Simple HTML table (no DataTable — bounded data): Data, Horario, Medico, Especialidade, Status columns
- Status column uses `StatusBadge` component with all 4 live statuses
- Loading: 3 skeleton rows with 5 cells each (animate-pulse)
- Empty state: "Nenhuma consulta registrada"

**`frontend/src/components/dashboard/patient/WhatsAppTimeline.tsx`**:
- Fetches `apiFetch<ConversationMessage[]>("/api/patients/${patientId}/conversations")` on mount
- Chat background: `flex flex-col gap-3 p-4 bg-gray-50 rounded-lg`
- User messages (role="user"): `justify-end` + `bg-green-500 text-white rounded-2xl rounded-br-sm`
- Bot messages (role="assistant"): `justify-start` + `bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-bl-sm shadow-sm`
- Timestamp per bubble: `format(parseISO(created_at), "HH:mm")` in 10px opacity text
- Loading: 3 skeleton bubbles alternating left/right
- Empty state: "Nenhuma conversa registrada"

**`frontend/src/app/(dashboard)/pacientes/[id]/page.tsx`**:
- `useParams<{ id: string }>()` to read patient ID
- Fetches `apiFetch<Patient>("/api/patients/${id}")` on mount
- Patient header: nome in `font-serif text-2xl`, Phone icon + phone, Calendar icon + data_nascimento, total_consultas count, notas in bg-gray-50 block
- Back button: ArrowLeft icon → `router.push("/pacientes")`
- Tabs (shadcn): defaultValue="consultas", triggers styled with `data-[state=active]:bg-green-600 data-[state=active]:text-white`
- "Consultas" tab renders AppointmentHistory; "Conversas WhatsApp" tab renders WhatsAppTimeline

## Verification Results

- `npx tsc --noEmit` Task 1: PASS (zero errors)
- `npx tsc --noEmit` Task 2: PASS (zero errors)
- Patient list page at /pacientes: PASS (file exists with DataTable + search)
- Patient profile page at /pacientes/[id]: PASS (file exists with two tabs)
- WhatsApp timeline uses green bubbles for user, white for bot: PASS (verified in source)
- columns.tsx defines 5 columns: PASS (nome, phone, data_nascimento, total_consultas, actions)
- patient-form.tsx uses react-hook-form + zod with 4 fields: PASS

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All components fetch from live API endpoints:
- `/api/patients` — wired via apiFetch
- `/api/patients/{id}` — wired via apiFetch
- `/api/patients/{id}/appointments` — wired via apiFetch
- `/api/patients/{id}/conversations` — wired via apiFetch

No placeholder data flows to any rendered UI.

## Commits

- `5a2e22c`: feat(03-05): patient list page — DataTable with search, create/edit slide-over forms
- `c2d678b`: feat(03-05): patient profile page — tabbed appointment history and WhatsApp timeline

## Self-Check: PASSED
