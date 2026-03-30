---
phase: 03-core-crud
plan: "02"
subsystem: backend-crud-api
tags: [fastapi, patients, appointments, rbac, rls, pagination, medico-isolation]
dependency_graph:
  requires: [03-01, 02-auth-multi-tenancy]
  provides: [patients-api, appointments-api]
  affects: [03-03, 03-04, 03-05, 03-06, 03-07]
tech_stack:
  added: []
  patterns: ["RLS tenant isolation via get_db_for_tenant", "require_role RBAC dependency factory", "PaginatedResponse envelope", "medico isolation via doctors.user_id lookup", "dynamic SET clause for partial updates"]
key_files:
  created:
    - agent-service/src/api/patients.py
    - agent-service/src/api/appointments.py
  modified:
    - agent-service/src/api/webhook.py
    - agent-service/alembic/versions/004_crud_schema_additions.py
decisions:
  - "Appointments table column names: used COALESCE(appointment_date, data_agendamento) in read queries for backward compat with bot legacy columns"
  - "Migration 004 extended with appointments CRUD columns (data_agendamento, horario_agendamento, patient_id, motivo_cancelamento) — all via idempotent IF NOT EXISTS DDL"
  - "Medico with no linked doctor record returns empty results instead of 403 — safer than exposing error that reveals DB state"
metrics:
  duration: "5 minutes"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_created: 2
  files_modified: 2
---

# Phase 03 Plan 02: Patients + Appointments API Routers Summary

**One-liner:** FastAPI patients router (6 endpoints, PAT-01 to PAT-05) and appointments router (5 endpoints, AGENDA-02 to AGENDA-07) with full RLS tenant isolation, role-based access control, pagination envelope, and medico-only doctor_id enforcement.

## What Was Built

### Task 1: Patients API Router

**`agent-service/src/api/patients.py`** — APIRouter at `/api/patients`:

- **GET /** — Paginated list with optional `search` param (case-insensitive nome OR phone LIKE). Returns `PaginatedResponse` with `PatientOut` items. PAT-01.
- **POST /** — Creates patient with explicit `current_setting('app.tenant_id')::uuid` tenant insertion. Returns 201 with `PatientOut`. PAT-02.
- **GET /{patient_id}** — Single patient with subquery for `total_consultas`. Returns 404 if not found.
- **PUT /{patient_id}** — Dynamic SET clause (only non-None fields updated). Fetches `total_consultas` in a second query after UPDATE. Returns 404 if no row. PAT-03.
- **GET /{patient_id}/appointments** — LEFT JOIN with doctors for nome/especialidade. Uses `COALESCE(appointment_date, data_agendamento)` for bot legacy column compat. PAT-04.
- **GET /{patient_id}/conversations** — First looks up patient phone, then queries `conversations WHERE session_id LIKE %phone%`. Returns `ConversationMessage` list. PAT-05.

All endpoints: `Depends(require_role("admin", "recepcionista"))` + `Depends(get_db_for_tenant)`.

### Task 2: Appointments API Router + Router Mounting

**`agent-service/src/api/appointments.py`** — APIRouter at `/api/appointments`:

- **GET /** — Paginated list with filters: `doctor_id`, `date_from`, `date_to`, `status`. AGENDA-07: If `current_user["role"] == "medico"`, looks up `SELECT id FROM doctors WHERE user_id = %s` and overrides doctor_id. Returns empty if no linked doctor. JOIN with patients and doctors for names.
- **POST /** — Creates with `status='agendado'` and `current_setting('app.tenant_id')::uuid`. AGENDA-02, AGENDA-05.
- **PUT /{appointment_id}** — Dynamic SET clause (doctor_id, data_agendamento, horario_agendamento, especialidade). Returns 404 if no row. AGENDA-03.
- **PATCH /{appointment_id}/cancel** — `UPDATE ... SET status='cancelado', motivo_cancelamento=%s WHERE ... AND status != 'cancelado'`. Returns 404 if already cancelled or not found. AGENDA-04.
- **PATCH /{appointment_id}/status** — Validates against `ALLOWED_STATUSES` set. Returns 400 for invalid status. AGENDA-05.

**`agent-service/src/api/webhook.py`** — Added imports and `app.include_router()` calls for both routers after auth_router.

**`agent-service/alembic/versions/004_crud_schema_additions.py`** — Extended with 4 new appointments columns (see Deviations).

## Verification Results

- `python -c "from src.api.patients import router; ..."`: PASS — 6 routes
- `python -c "from src.api.appointments import router; ..."`: PASS — 5 routes
- Both routers mounted in webhook.py: PASS (verified via grep)
- Medico isolation logic in GET /: PASS (role == "medico" branch present)
- PATCH /cancel sets status='cancelado': PASS
- POST / sets status='agendado': PASS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Extended migration 004 with CRUD appointment columns**
- **Found during:** Task 2 — creating the appointments router
- **Issue:** The plan's create endpoint inserts into `data_agendamento`, `horario_agendamento`, `patient_id`, and `motivo_cancelamento` columns which did not exist in the appointments table. Migration 004 only modified the status CHECK constraint.
- **Fix:** Added 4 idempotent `ALTER TABLE appointments ADD COLUMN IF NOT EXISTS` blocks to migration 004 (with DO $$ IF NOT EXISTS patterns matching the existing migration style). Also added downgrade blocks for all 4 new columns.
- **Files modified:** `agent-service/alembic/versions/004_crud_schema_additions.py`
- **Commit:** 24dcd91

**2. [Rule 3 - Blocking Issue] Installed missing PyJWT and pwdlib packages in venv**
- **Found during:** Task 1 verification
- **Issue:** The plan's verification command uses the venv at `agent-service/.venv` which lacked PyJWT and pwdlib (listed in requirements.txt but not installed).
- **Fix:** `python -m pip install PyJWT==2.12.1 pwdlib` — restored environment to match requirements.txt.
- **Files modified:** None (venv packages only)

### Read-Query Backward Compatibility

The plan said to "read src/tools/appointments.py to confirm exact column names". The old bot table uses `appointment_date` and `appointment_time`. The CRUD panel introduces `data_agendamento` and `horario_agendamento`. The read queries (GET / and GET /{patient_id}/appointments) use `COALESCE(appointment_date, data_agendamento)` to support both old bot-created rows and new CRUD-created rows.

## Known Stubs

None. Both routers have real SQL queries targeting real database tables. All endpoints are fully wired with proper error handling, role enforcement, and tenant isolation.

## Commits

- `6a26667`: feat(03-02): patients API router — list/search, create, edit, appointment history, conversation history
- `24dcd91`: feat(03-02): appointments API router + mount both routers in webhook

## Self-Check: PASSED

- agent-service/src/api/patients.py: FOUND
- agent-service/src/api/appointments.py: FOUND
- .planning/phases/03-core-crud/03-02-SUMMARY.md: FOUND
- Commit 6a26667: FOUND
- Commit 24dcd91: FOUND
