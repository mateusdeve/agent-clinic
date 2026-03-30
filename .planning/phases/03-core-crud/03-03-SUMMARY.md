---
phase: 03-core-crud
plan: "03"
subsystem: backend-crud-api
tags: [fastapi, doctors, users, rbac, schedules, blocked-slots, pwdlib, pagination]
dependency_graph:
  requires: [03-01, 03-02, 02-auth-multi-tenancy]
  provides: [doctors-api, users-api, api-01-complete]
  affects: [03-04, 03-05, 03-06, 03-07]
tech_stack:
  added: []
  patterns: ["DELETE+INSERT atomic schedule replace", "pwdlib Argon2 password hashing", "self-modification prevention guard", "psycopg2.IntegrityError duplicate email handler", "dia_semana/hora_inicio/hora_fim bot schema compatibility"]
key_files:
  created:
    - agent-service/src/api/doctors.py
    - agent-service/src/api/users.py
  modified:
    - agent-service/src/api/webhook.py
decisions:
  - "Use existing bot schema column names (dia_semana, hora_inicio, hora_fim) in doctor_schedules — migration 004 only added tenant_id, did not rename columns; API Pydantic models use new names (day_of_week, start_time, end_time) and map to DB columns"
  - "Admin self-protection: PATCH /role and PATCH /status prevent admin from modifying own account — compare user_id param against current_user['user_id']"
  - "Password reset is admin-managed only in Phase 3 — self-service email flow deferred to v2 per plan Open Question 2"
metrics:
  duration: "4 minutes"
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 03 Plan 03: Doctors + Users API Routers Summary

**One-liner:** FastAPI doctors router (8 endpoints, DOC-01 to DOC-03 + AGENDA-06) and users router (5 endpoints, USER-01 to USER-05) with Argon2 password hashing, admin self-protection guards, and all 4 CRUD routers mounted completing API-01.

## What Was Built

### Task 1: Doctors API Router

**`agent-service/src/api/doctors.py`** — APIRouter at `/api/doctors`:

- **GET /** — Paginated list with optional `search` param (case-insensitive nome OR especialidade LIKE). Returns PaginatedResponse. DOC-01. Accessible by admin/recepcionista/medico.
- **POST /** — Creates doctor with nome, especialidade, crm, optional user_id. Uses `current_setting('app.tenant_id')::uuid` for tenant insertion. Returns 201. DOC-02.
- **PUT /{doctor_id}** — Dynamic SET clause (only non-None fields). Returns 404 if not found. DOC-02.
- **GET /{doctor_id}/schedules** — Reads `dia_semana`, `hora_inicio`, `hora_fim` from existing bot schema. Returns as `day_of_week`, `start_time`, `end_time` in response. DOC-03.
- **PUT /{doctor_id}/schedules** — Atomic DELETE + INSERT for weekly grid replacement. Verifies doctor exists first. Returns updated slot list. DOC-03.
- **GET /{doctor_id}/blocked-slots** — Lists blocked time slots ordered by date/time. AGENDA-06. Accessible by admin/recepcionista.
- **POST /{doctor_id}/blocked-slots** — Creates blocked slot with optional start_time, end_time, reason. Returns 201. AGENDA-06.
- **DELETE /blocked-slots/{slot_id}** — Removes blocked slot. Returns 404 if not found. AGENDA-06.

All write endpoints: `Depends(require_role("admin"))`. All read endpoints: `Depends(require_role("admin", "recepcionista"))` or `("admin", "recepcionista", "medico")`.

### Task 2: Users API Router + Router Mounting

**`agent-service/src/api/users.py`** — APIRouter at `/api/users`:

- **GET /** — Paginated user list. Returns PaginatedResponse with UserOut items. USER-01. Admin only.
- **POST /** — Creates user with email, name, password, role. Hashes password with `PasswordHash.recommended()` (Argon2). Catches `psycopg2.IntegrityError` for duplicate email → 409. Returns 201. USER-02.
- **PATCH /{user_id}/role** — Changes user role. Validates role is in {admin, recepcionista, medico}. Prevents admin from changing own role. Returns 404 if not found. USER-03.
- **PATCH /{user_id}/status** — Activates/deactivates user. Prevents admin from deactivating own account. Returns 404 if not found. USER-04.
- **POST /{user_id}/reset-password** — Admin-managed password reset. Hashes new password with pwdlib. Returns 404 if not found. USER-05.

All endpoints: `Depends(require_role("admin"))`.

**`agent-service/src/api/webhook.py`** — Added imports and `app.include_router()` calls for doctors_router and users_router. All 4 CRUD routers now mounted (patients, appointments, doctors, users) — API-01 complete.

## Verification Results

- `python -c "from src.api.doctors import router; ..."`: PASS — 8 routes
- `python -c "from src.api.users import router; ..."`: PASS — 5 routes
- All 4 CRUD routers import without error: PASS
- webhook.py includes all 4 routers: PASS (verified via grep)
- Users router uses pwdlib PasswordHash.recommended(): PASS
- Admin self-protection logic in PATCH /role and PATCH /status: PASS (line 182, 231)
- POST / catches psycopg2.IntegrityError for duplicate email: PASS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Issue] Installed pwdlib[argon2] in venv**
- **Found during:** Task 2 verification
- **Issue:** `PasswordHash.recommended()` requires argon2 which was not installed in the venv (same issue as Plan 02).
- **Fix:** `pip install "pwdlib[argon2]"` — restored argon2 support.
- **Files modified:** None (venv packages only)

### Schema Compatibility

The plan specified `day_of_week`, `start_time`, `end_time` as doctor_schedules column names. The existing bot table uses `dia_semana`, `hora_inicio`, `hora_fim` (confirmed from `src/tools/doctors.py`). Migration 004 only added `tenant_id` and did not rename these columns.

Fix: Used the existing bot column names in all SQL queries while keeping `day_of_week`, `start_time`, `end_time` as the Pydantic model and API response field names. This is transparent to API consumers.

## Known Stubs

None. Both routers have real SQL queries targeting real database tables. All endpoints are fully wired with proper error handling, role enforcement, and tenant isolation.

## Commits

- `3556d91`: feat(03-03): doctors API router — list, create, edit, schedules, blocked-slots
- `e146f97`: feat(03-03): users API router + mount all 4 CRUD routers in webhook

## Self-Check: PASSED

- agent-service/src/api/doctors.py: FOUND
- agent-service/src/api/users.py: FOUND
- .planning/phases/03-core-crud/03-03-SUMMARY.md: FOUND
- Commit 3556d91: FOUND
- Commit e146f97: FOUND
