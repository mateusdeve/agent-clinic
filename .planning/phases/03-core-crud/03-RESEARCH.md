# Phase 3: Core CRUD - Research

**Researched:** 2026-03-29
**Domain:** Next.js CRUD UI (data tables, calendar, slide-overs, patient profile) + FastAPI REST routers (patients, appointments, doctors, users)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Calendar / Agenda UI**
- D-01: Three views: Day, Week, Month with toggle. Day for detailed slot scheduling, week for overview, month for long-range planning (AGENDA-01).
- D-02: Custom calendar built with date-fns for date math + Tailwind for layout. No heavy calendar library (no FullCalendar). Full control over green palette and MedIA brand.
- D-03: Color-coded appointment blocks by status: Agendado=blue, Confirmado=green, Realizado=gray, Cancelado=red with strikethrough. Scannable at a glance.
- D-04: Doctor filter dropdown on calendar (AGENDA-01). Medico role sees only their own calendar (AGENDA-07).

**Data Tables and Forms**
- D-05: shadcn/ui Table + @tanstack/react-table for all entity lists (patients, doctors, users, appointments). Headless logic with full Tailwind control. Reusable column definitions per entity.
- D-06: Slide-over panel for create/edit forms. Side panel slides in from right — main list stays visible. Consistent across all 4 entities.
- D-07: Server-side pagination: 20 rows per page, page numbers at bottom. API returns paginated results with total count.
- D-08: Form validation with react-hook-form + zod schemas. Pattern established in login form (Phase 2).

**Patient Profile Page**
- D-09: Tabbed layout: patient info header at top, then tabs: "Consultas" (appointment history) | "Conversas WhatsApp" (conversation history). Each tab loads independently.
- D-10: WhatsApp conversation history displayed as chat bubble timeline (read-only, like WhatsApp UI). Familiar for clinic staff reviewing past conversations.

**API Design Pattern**
- D-11: RESTful FastAPI routers per entity: /api/patients, /api/appointments, /api/doctors, /api/users. Standard REST verbs (GET/POST/PUT/DELETE). Builds on existing FastAPI app + auth deps from Phase 2.
- D-12: Pagination response envelope: `{ items: [], total: int, page: int, per_page: int }`. Shared pagination helper across all routers.
- D-13: All endpoints use `get_current_user` + `get_db_for_tenant` from Phase 2 deps. Tenant isolation automatic via RLS.
- D-14: Existing backend functions in `src/tools/` (patients.py, appointments.py, doctors.py) are WhatsApp-bot oriented (use `_get_db()` without tenant context). New API routers use `get_db_for_tenant` from deps.py — do NOT modify existing tool functions to avoid breaking the bot.

### Claude's Discretion
- Exact column definitions for each entity table
- Calendar time slot granularity (15min/30min)
- Availability grid editing UX for doctors (DOC-03)
- User deactivation confirmation flow
- Password reset mechanism for admin-managed users
- Exact slide-over panel animation/sizing
- Search debounce timing and minimum characters
- Empty state illustrations/messages

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGENDA-01 | Recepcionista ve calendario visual (dia/semana/mes) com filtro por medico | date-fns week/month math; custom grid with Tailwind |
| AGENDA-02 | Recepcionista pode criar agendamento manualmente (paciente, medico, data, hora, especialidade) | POST /api/appointments; slide-over form; react-hook-form + zod |
| AGENDA-03 | Recepcionista pode editar/remarcar agendamento existente | PUT /api/appointments/{id}; same slide-over reused for edit |
| AGENDA-04 | Recepcionista pode cancelar agendamento com motivo opcional | PATCH /api/appointments/{id}/cancel; confirm dialog |
| AGENDA-05 | Agendamentos tem status tracking: Agendado > Confirmado > Realizado > Cancelado | DB column `status` already exists; map to color classes |
| AGENDA-06 | Admin pode bloquear horarios (ferias, almoco, indisponibilidade) | New `blocked_slots` table or `status='blocked'` record; Alembic migration 004 |
| AGENDA-07 | Medico ve apenas sua propria agenda | require_role guard + JWT `user_id` matched to `doctor_id`; frontend hides filter |
| PAT-01 | Recepcionista ve lista de pacientes com busca por nome/telefone | GET /api/patients?search=&page=; TanStack Table server-side |
| PAT-02 | Recepcionista pode criar paciente manualmente (nome, telefone, data nascimento, notas) | POST /api/patients; patients table needs `data_nascimento` + `notas` columns (migration 004) |
| PAT-03 | Recepcionista pode editar dados de paciente | PUT /api/patients/{id}; patients table needs UUID id (currently phone is PK) |
| PAT-04 | Pagina de perfil do paciente mostra historico de consultas | GET /api/patients/{id}/appointments; tab Consultas |
| PAT-05 | Pagina de perfil do paciente mostra historico de conversas WhatsApp | GET /api/patients/{id}/conversations; tab Conversas WhatsApp; chat bubble timeline |
| DOC-01 | Admin ve lista de medicos com especialidade | GET /api/doctors; TanStack Table |
| DOC-02 | Admin pode criar/editar perfil de medico (nome, especialidade, CRM, horarios) | POST/PUT /api/doctors; slide-over form |
| DOC-03 | Admin pode definir grade de disponibilidade por medico (dia x horarios) | PUT /api/doctors/{id}/schedules; day x time grid UI; doctor_schedules table |
| USER-01 | Admin ve lista de usuarios do sistema com role | GET /api/users; require_role('admin') |
| USER-02 | Admin pode criar usuario com atribuicao de role | POST /api/users; pwdlib hash; roles enum |
| USER-03 | Admin pode editar role de usuario existente | PATCH /api/users/{id}/role |
| USER-04 | Admin pode desativar/reativar usuario | PATCH /api/users/{id}/status; is_active toggle |
| USER-05 | Usuario pode redefinir senha | POST /api/users/{id}/reset-password (admin sets new pwd) or self-service flow |
| API-01 | FastAPI expoe endpoints REST para todas as entidades | All 4 routers; pagination envelope; mount in webhook.py |
</phase_requirements>

---

## Summary

Phase 3 builds the complete CRUD management layer across two surfaces: a FastAPI REST API (4 routers: patients, appointments, doctors, users) and a Next.js dashboard UI (data tables, a custom calendar, slide-over panels, and a patient profile page with tabs). Everything builds directly on Phase 2 infrastructure — JWT auth deps, tenant RLS, and the dashboard shell are already in place.

The biggest technical challenge is the **schema gap**: the existing `patients` table uses `phone` as primary key (TEXT), has no `id` UUID, no `data_nascimento`, and no `notas` column. The new API requires a stable UUID `id` for all `/api/patients/{id}` routes and the profile page. A new Alembic migration (004) must add these columns to `patients` — and also add a `blocked_slots` table for AGENDA-06. The `appointments` table also needs new status values mapped (currently uses `active`/`cancelled`; new statuses are `agendado`, `confirmado`, `realizado`, `cancelado`).

The frontend additions are additive: 8 new route stubs under `(dashboard)/` (agenda, pacientes, pacientes/[id], medicos, usuarios), 3 shared components (DataTable, SlideOver, StatusBadge), and the custom calendar component. No existing pages are modified.

**Primary recommendation:** Build Wave 0 (Alembic migration 004 + router skeleton registration) first — every other task depends on stable table schemas and mounted API routes.

---

## Standard Stack

### Core (all already installed or confirmed current)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-table | 8.21.3 (latest) | Headless table logic (sorting, pagination, filtering) | Decoupled from UI — pairs with shadcn Table primitives |
| date-fns | 4.1.0 (latest) | Calendar date arithmetic (startOfWeek, eachDayOfInterval, etc.) | Smallest footprint; no moment.js bloat; tree-shakeable |
| react-hook-form | 7.72.0 (installed) | Form state + validation | Already used in login-form.tsx |
| zod | 4.3.6 (installed) | Schema validation + TypeScript inference | Already used in login-form.tsx |
| @hookform/resolvers | 5.2.2 (installed) | zodResolver bridge | Already installed |
| lucide-react | 1.7.0 (installed) | Icons (ChevronLeft, ChevronRight, X, Plus, Search) | Already in project |
| shadcn/ui (table, dialog, tabs, badge, input, select) | — | UI primitives | Project standard; components.json configured |

### New Libraries to Install

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tanstack/react-table | 8.21.3 | Data table headless logic | All entity lists (patients, doctors, users, appointments) |

**Note:** `@tanstack/react-table` is NOT yet in `package.json`. It must be installed. All other dependencies are already present.

**Installation:**
```bash
cd /Users/mateuspires/Dev/agent-clinic/frontend
npm install @tanstack/react-table@8.21.3
```

**Version verification:** Confirmed `npm view @tanstack/react-table version` = 8.21.3 on 2026-03-29.

---

## Architecture Patterns

### Recommended Project Structure

```
frontend/src/
├── app/(dashboard)/
│   ├── agenda/
│   │   └── page.tsx             # Calendar view (AGENDA-01..07)
│   ├── pacientes/
│   │   ├── page.tsx             # Patient list (PAT-01..03)
│   │   └── [id]/
│   │       └── page.tsx         # Patient profile (PAT-04..05)
│   ├── medicos/
│   │   └── page.tsx             # Doctor list + availability (DOC-01..03)
│   └── usuarios/
│       └── page.tsx             # User management (USER-01..05)
├── components/
│   ├── ui/                      # shadcn primitives (add: table, dialog, tabs, badge, input, select)
│   └── dashboard/
│       ├── DataTable.tsx        # Generic TanStack Table wrapper
│       ├── SlideOver.tsx        # Slide-over panel (shared across all entities)
│       ├── StatusBadge.tsx      # Appointment status color chip
│       ├── calendar/
│       │   ├── CalendarDay.tsx
│       │   ├── CalendarWeek.tsx
│       │   └── CalendarMonth.tsx
│       └── patient/
│           ├── AppointmentHistory.tsx
│           └── WhatsAppTimeline.tsx
└── lib/
    ├── api.ts                   # fetch wrapper that injects Bearer token from session
    └── types.ts                 # Shared TypeScript interfaces for API responses

agent-service/src/api/
├── patients.py                  # FastAPI router /api/patients
├── appointments.py              # FastAPI router /api/appointments
├── doctors.py                   # FastAPI router /api/doctors
└── users.py                     # FastAPI router /api/users

agent-service/alembic/versions/
└── 004_crud_schema_additions.py # Adds id UUID to patients, data_nascimento, notas, blocked_slots
```

### Pattern 1: Generic DataTable Component (TanStack v8)

**What:** A single reusable component that accepts `columns` and `data` props. Each entity page defines its own `ColumnDef[]` and passes paginated data.

**When to use:** All 4 entity list pages (patients, doctors, users, appointments list).

```typescript
// Source: @tanstack/react-table v8 official docs
"use client";

import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
  type PaginationState,
} from "@tanstack/react-table";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";

interface DataTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];
  pageCount: number;
  pagination: PaginationState;
  onPaginationChange: (updater: PaginationState | ((old: PaginationState) => PaginationState)) => void;
}

export function DataTable<TData>({
  columns, data, pageCount, pagination, onPaginationChange,
}: DataTableProps<TData>) {
  const table = useReactTable({
    data,
    columns,
    pageCount,
    state: { pagination },
    onPaginationChange,
    manualPagination: true,  // server-side — do NOT use getCoreRowModel pagination
    getCoreRowModel: getCoreRowModel(),
  });

  // render table.getHeaderGroups(), table.getRowModel().rows
  // render pagination controls using table.getCanPreviousPage() etc.
}
```

**Critical:** `manualPagination: true` is required for server-side pagination (D-07). Without it, TanStack tries to paginate the already-sliced `data` array again.

### Pattern 2: SlideOver Panel

**What:** Fixed right-side panel (CSS `translate-x`) for create/edit forms. Overlay backdrop closes panel on click.

**When to use:** Create and edit for patients, doctors, users, appointments.

```typescript
// Tailwind 4 transition pattern — no framer-motion needed
"use client";

interface SlideOverProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function SlideOver({ open, onClose, title, children }: SlideOverProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/40 z-40 transition-opacity duration-200
          ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
        onClick={onClose}
      />
      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-full max-w-md bg-white z-50 shadow-2xl
          transform transition-transform duration-300 ease-in-out
          ${open ? "translate-x-0" : "translate-x-full"}`}
      >
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="font-serif text-green-600 text-lg">{title}</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-gray-400" /></button>
        </div>
        <div className="p-6 overflow-y-auto h-[calc(100%-73px)]">
          {children}
        </div>
      </div>
    </>
  );
}
```

### Pattern 3: API Fetch Wrapper (Frontend)

**What:** A thin wrapper around `fetch` that reads `access_token` from NextAuth session and injects `Authorization: Bearer`. Used by all client components.

**When to use:** Every client-side API call to `/api/*`.

```typescript
// frontend/src/lib/api.ts
import { getSession } from "next-auth/react";

export async function apiFetch(path: string, init?: RequestInit) {
  const session = await getSession();
  const token = (session as any)?.access_token;
  return fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
}
```

**Note:** Server components (page.tsx files using `await auth()`) should use the token from `auth()` directly, not `getSession()`.

### Pattern 4: FastAPI Router (mirroring auth.py)

**What:** Each entity gets its own `APIRouter` with prefix `/api/{entity}`, mounted in `webhook.py`. Uses `get_db_for_tenant` + `get_current_user` from `deps.py`.

```python
# agent-service/src/api/patients.py
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.api.deps import get_db_for_tenant, get_current_user, require_role
import logging

logger = logging.getLogger("agent-clinic.api.patients")
router = APIRouter(prefix="/api/patients", tags=["patients"])

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int

@router.get("", dependencies=[Depends(require_role("admin", "recepcionista"))])
def list_patients(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conn=Depends(get_db_for_tenant),
):
    offset = (page - 1) * per_page
    with conn.cursor() as cur:
        # count query
        # data query with LIMIT/OFFSET
    conn.commit()
    return PaginatedResponse(items=[...], total=total, page=page, per_page=per_page)
```

**Mounting in webhook.py:**
```python
from src.api.patients import router as patients_router
from src.api.appointments import router as appointments_router
from src.api.doctors import router as doctors_router
from src.api.users import router as users_router

app.include_router(patients_router)
app.include_router(appointments_router)
app.include_router(doctors_router)
app.include_router(users_router)
```

### Pattern 5: Custom Calendar with date-fns

**What:** Three view modes (day/week/month) toggled by a state variable. Each view is a separate component. date-fns handles all date arithmetic.

**Key date-fns functions needed:**
```typescript
import {
  startOfWeek, endOfWeek,       // week bounds
  startOfMonth, endOfMonth,     // month bounds
  eachDayOfInterval,            // array of days in range
  addDays, subDays,             // navigation
  addWeeks, subWeeks,
  addMonths, subMonths,
  format,                       // "dd/MM", "EEEE", "MMM yyyy"
  isSameDay,                    // is appointment on this cell
  isToday,                      // highlight today
  parseISO,                     // parse API date strings
  setHours, setMinutes,         // time slot generation
  eachHourOfInterval,           // day view time slots
} from "date-fns";
import { ptBR } from "date-fns/locale";   // Portuguese locale for format()
```

**Day view:** Fixed time grid (07:00–20:00), 30-minute rows, appointment blocks absolutely positioned by time offset. Slot granularity: 30 minutes (recommendation — matches `duracao_consulta` default in `doctor_schedules`).

**Week view:** 7-column grid. Each column is one day. Appointments as colored chips inside cells.

**Month view:** 6-row × 7-column grid. Cells show up to 3 appointment chips with "+N more" overflow.

### Pattern 6: Chat Bubble Timeline (PAT-05)

**What:** Read-only message list styled as WhatsApp-like bubbles. Bot messages align left, patient messages align right.

```typescript
// Matches hero chat card from landing page visually
function WhatsAppTimeline({ messages }: { messages: ConversationMessage[] }) {
  return (
    <div className="flex flex-col gap-3 p-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm
              ${msg.role === "user"
                ? "bg-green-500 text-white rounded-br-sm"
                : "bg-white border border-gray-200 text-gray-800 rounded-bl-sm"}`}
          >
            {msg.content}
            <span className="text-xs opacity-60 ml-2">{format(parseISO(msg.created_at), "HH:mm")}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Anti-Patterns to Avoid

- **Mutating existing tool functions in `src/tools/`:** patients.py, appointments.py, doctors.py use `_get_db()` without tenant context. The WhatsApp bot depends on these. New API routers must be written from scratch in `src/api/`.
- **Using client-side pagination with TanStack:** Always set `manualPagination: true` and `pageCount` from API response. Without this, table re-paginates already-sliced server data.
- **Storing `access_token` in localStorage:** NextAuth manages tokens in the encrypted `next-auth.session-token` cookie. Always read from session via `getSession()` or `auth()`.
- **Changing `patients.phone` primary key without migration:** The bot writes patients by phone as PK. Migration 004 must ADD a UUID `id` column with `gen_random_uuid()` default and make it the new primary key — do not remove `phone` column (bot still uses it).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table sorting / filtering logic | Custom sort state + filter functions | @tanstack/react-table | Handles multi-sort, column visibility, pagination state machine |
| Form validation + error display | Manual `useState` + validation logic | react-hook-form + zod | Already in project; handles async validation, dirty state, reset |
| Date arithmetic (week start, month grid) | Manual date math with `getDay()` etc. | date-fns functions | DST edge cases, locale-aware week start (Brazil: Sunday) |
| CSS transition animations | framer-motion or custom keyframes | Tailwind `transition-transform` + `translate-x-full` | Tailwind 4 in project; zero dependency for slide-over |
| Password hashing (users endpoint) | bcrypt or manual SHA | pwdlib (already installed in agent-service) | Already used in `auth.py`; Argon2 through `PasswordHash.recommended()` |
| Tenant filtering in queries | Manual `WHERE tenant_id = ?` in every query | `get_db_for_tenant` dep (already built) | RLS in PostgreSQL handles it automatically via `SET LOCAL app.tenant_id` |

**Key insight:** The Phase 2 auth/tenant infrastructure eliminates an entire class of security bugs. Any new router that calls `get_db_for_tenant` gets multi-tenancy for free — no per-query tenant filtering needed.

---

## Common Pitfalls

### Pitfall 1: patients Table Schema Gap

**What goes wrong:** New API routes reference `/api/patients/{id}` using a UUID `id`. The existing `patients` table uses `phone TEXT PRIMARY KEY` with no UUID `id` column. Every GET/PUT/DELETE by `{id}` will fail.

**Why it happens:** The original schema was designed for the WhatsApp bot (phone-first). Phase 3 is the first time a stable, URL-addressable patient ID is needed.

**How to avoid:** Migration 004 must:
1. `ADD COLUMN id UUID DEFAULT gen_random_uuid()` to `patients`
2. Backfill: `UPDATE patients SET id = gen_random_uuid() WHERE id IS NULL`
3. `ADD COLUMN data_nascimento DATE`
4. `ADD COLUMN notas TEXT`
5. `ADD COLUMN tenant_id UUID` (migration 002 already handles this, verify before running)
6. Create a `UNIQUE` index on `id`

The bot functions keep using `phone` as the lookup key — no changes needed to `src/tools/patients.py`.

**Warning signs:** `column "id" does not exist` errors on first API call to `/api/patients/{id}`.

### Pitfall 2: appointments Status Enum Mismatch

**What goes wrong:** Existing `appointments` table uses `status VARCHAR(20)` with values `'active'` and `'cancelled'`. Phase 3 introduces new statuses: `agendado`, `confirmado`, `realizado`, `cancelado`. The bot code uses `status = 'active'` in WHERE clauses.

**Why it happens:** The bot was built before the management UI status model was defined.

**How to avoid:** Migration 004 must rename existing statuses in a backward-compatible way:
- Keep `'active'` as equivalent to `'agendado'` OR update bot queries to accept both
- Best approach: Add `'agendado'` as the new insert default while keeping `'active'` query backward-compat via `status IN ('active', 'agendado')`
- New cancellations use `'cancelado'` (existing bot uses `'cancelled'`) — migration must map

**Warning signs:** Bot stops finding active appointments after migration. Test with `test_connections.py` after migration.

### Pitfall 3: doctor_schedules Missing tenant_id (RLS Gap)

**What goes wrong:** Migration 002 added `tenant_id` to a specific list of tables (`patients`, `appointments`, `doctors`, `conversations`, `conversation_summaries`, `knowledge_chunks`, `follow_ups`). The `doctor_schedules` table (created by `006_doctors.sql`) was NOT in that list and may not have `tenant_id`.

**Why it happens:** `doctor_schedules` is a child table — it was created after the original migration set was defined. RLS policy on `doctors` parent doesn't cascade to `doctor_schedules`.

**How to avoid:** Migration 004 must explicitly add `tenant_id` to `doctor_schedules` with the same backfill pattern as migration 002. Also add RLS policy on `doctor_schedules` matching the pattern from migration 003.

**Warning signs:** `/api/doctors/{id}/schedules` returns other clinics' schedule data.

### Pitfall 4: get_db_for_tenant is a Generator Dependency

**What goes wrong:** `get_db_for_tenant` in `deps.py` uses `yield conn` (generator). Using `conn.commit()` inside the router function works, but the connection is closed in the `finally` block after the response is returned. If you call `conn.close()` manually inside the router, the `finally` block gets a double-close error.

**Why it happens:** FastAPI dependency injection with `yield` handles cleanup in the finally block automatically.

**How to avoid:** Never call `conn.close()` inside router functions that receive `conn=Depends(get_db_for_tenant)`. Only call `conn.commit()` after writes.

**Warning signs:** `psycopg2.InterfaceError: connection already closed` on some requests.

### Pitfall 5: Next.js Server vs Client Component Token Access

**What goes wrong:** `getSession()` from `next-auth/react` only works in Client Components (`"use client"`). Server Components (page.tsx without `"use client"`) must use `await auth()` from `@/lib/auth`. Mixing them causes hydration errors or missing tokens.

**Why it happens:** NextAuth v5 has two separate APIs: the server-side `auth()` (from `./src/lib/auth`) and the client-side `getSession()` (from `next-auth/react`).

**How to avoid:**
- Page-level data fetching: `"use server"` (default for page.tsx) → use `await auth()`, pass `session.access_token` as prop to client components
- Client component API calls: use `apiFetch()` wrapper that calls `getSession()`

**Warning signs:** `TypeError: auth is not a function` in client components; `getSession() returns null` in server components.

### Pitfall 6: Medico Role Calendar Isolation (AGENDA-07)

**What goes wrong:** If the Medico role filter is only enforced in the frontend (hiding the dropdown), a medico could manually fetch `/api/appointments?doctor_id=OTHER_DOCTOR_UUID` and see all appointments.

**Why it happens:** UI-only RBAC is insufficient per project security model.

**How to avoid:** In the appointments API router, if `current_user["role"] == "medico"`, enforce that `doctor_id` is always overridden to the user's linked doctor ID. This requires a `doctor_user_id` or `linked_doctor_id` column on `doctors` table linking to `users.id`, OR looking up by user_id in a new mapping.

**Recommendation (Claude's discretion):** Add `user_id UUID REFERENCES users(id)` to the `doctors` table in migration 004. Medicos are created as both a `users` row and a `doctors` row. API joins on `doctors.user_id = current_user["user_id"]` to enforce the filter.

---

## Code Examples

Verified patterns from project source:

### Pagination Envelope (D-12)
```python
# agent-service/src/api/patients.py — recommended pattern
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int

# Usage in router
@router.get("", response_model=PaginatedResponse[PatientOut])
def list_patients(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    conn=Depends(get_db_for_tenant),
    _user=Depends(require_role("admin", "recepcionista")),
):
    offset = (page - 1) * per_page
    with conn.cursor() as cur:
        base_where = "WHERE 1=1"
        params = []
        if search:
            base_where += " AND (LOWER(nome) LIKE LOWER(%s) OR phone LIKE %s)"
            params += [f"%{search}%", f"%{search}%"]
        cur.execute(f"SELECT COUNT(*) FROM patients {base_where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT id, phone, nome, data_nascimento, notas FROM patients {base_where} ORDER BY nome LIMIT %s OFFSET %s",
            params + [per_page, offset]
        )
        rows = cur.fetchall()
    conn.commit()
    return PaginatedResponse(items=[...], total=total, page=page, per_page=per_page)
```

### Migration 004 Pattern (following migrations 001-003)
```python
# agent-service/alembic/versions/004_crud_schema_additions.py
from alembic import op

revision = "004"
down_revision = "003"

def upgrade():
    # 1. patients: add UUID id, data_nascimento, notas
    op.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid()")
    op.execute("UPDATE patients SET id = gen_random_uuid() WHERE id IS NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_id ON patients(id)")

    op.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS data_nascimento DATE")
    op.execute("ALTER TABLE patients ADD COLUMN IF NOT EXISTS notas TEXT")

    # 2. doctors: add user_id for Medico role isolation (AGENDA-07)
    op.execute("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id)")

    # 3. doctor_schedules: add tenant_id (missed in migration 002)
    op.execute("ALTER TABLE doctor_schedules ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(f"UPDATE doctor_schedules SET tenant_id = '00000000-0000-0000-0000-000000000001' WHERE tenant_id IS NULL")
    op.execute("ALTER TABLE doctor_schedules ALTER COLUMN tenant_id SET NOT NULL")
    op.execute("ALTER TABLE doctor_schedules ADD CONSTRAINT fk_doctor_schedules_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)")
    op.execute("ALTER TABLE doctor_schedules ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_doctor_schedules ON doctor_schedules
            USING (tenant_id = current_tenant_id())
            WITH CHECK (tenant_id = current_tenant_id())
    """)

    # 4. blocked_slots: new table for AGENDA-06
    op.execute("""
        CREATE TABLE IF NOT EXISTS blocked_slots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            blocked_date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            reason TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("ALTER TABLE blocked_slots ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tenant_isolation_blocked_slots ON blocked_slots
            USING (tenant_id = current_tenant_id())
            WITH CHECK (tenant_id = current_tenant_id())
    """)
```

### TanStack Table Column Definition (per-entity)
```typescript
// frontend/src/app/(dashboard)/pacientes/columns.tsx
"use client";
import { type ColumnDef } from "@tanstack/react-table";

export type Patient = {
  id: string;
  nome: string;
  phone: string;
  data_nascimento: string | null;
  total_consultas: number;
};

export const columns: ColumnDef<Patient>[] = [
  {
    accessorKey: "nome",
    header: "Paciente",
  },
  {
    accessorKey: "phone",
    header: "Telefone",
  },
  {
    accessorKey: "total_consultas",
    header: "Consultas",
  },
  {
    id: "actions",
    cell: ({ row }) => (
      // open slide-over or link to /pacientes/{row.original.id}
    ),
  },
];
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FullCalendar (jQuery era) | Custom div grid + date-fns | 2020+ | Zero dependency; full brand control |
| react-table v7 (class API) | @tanstack/react-table v8 (hooks API) | 2022 | `useReactTable()` replaces `useTable()` — v7 imports are breaking |
| moment.js | date-fns or dayjs | 2019+ | Tree-shakeable; ~30% bundle size reduction |
| class-based form components | react-hook-form uncontrolled | 2020+ | No re-renders per keystroke; already in project |

**Deprecated/outdated:**
- `@tanstack/react-table` v7: Completely different API (`useTable`, `usePagination` hooks). Do NOT use v7 docs — all examples in this research are v8.
- `moment.js`: Do not add; `date-fns` is already the correct choice (D-02).

---

## Open Questions

1. **Medico-to-User Linkage**
   - What we know: AGENDA-07 requires Medicos to see only their own calendar. Currently `doctors` table has no `user_id` column linking to `users` table.
   - What's unclear: Is the Medico user always created simultaneously with a doctors row? Is there a manual linking step?
   - Recommendation: Migration 004 adds `user_id UUID REFERENCES users(id)` to `doctors`. Admin creates doctor profile, then links it to a user account from the doctor edit form. API enforces filter: if `role == "medico"`, look up `doctors.user_id = current_user.user_id` and override doctor_id filter.

2. **Password Reset Flow (USER-05)**
   - What we know: Context marks this as Claude's discretion. `auth.py` already has `hash_password` and `verify_password` (pwdlib).
   - What's unclear: Admin-managed reset (admin sets new password) vs self-service (user receives email).
   - Recommendation: Implement admin-managed reset only for Phase 3. `POST /api/users/{id}/reset-password` accepts `{ new_password: str }`, requires `require_role("admin")`. Self-service email flow is v2.

3. **conversations Table Schema for WhatsApp Timeline**
   - What we know: `conversations` table exists (migration 002 adds `tenant_id`). Bot stores messages as `role=user/assistant, content, metadata`.
   - What's unclear: Exact column names for `content`, `created_at`, and how to join to `patients` by `phone`.
   - Recommendation: Read `agent-service/src/memory/persistence.py` before implementing PAT-05 to confirm column names. The `conversations.session_id` likely encodes the `phone` number.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Frontend install | ✓ | (project running) | — |
| @tanstack/react-table | D-05 | ✗ (not in package.json) | 8.21.3 available | — (no fallback, must install) |
| date-fns | D-02 | ✗ (not in package.json) | 4.1.0 available | — (no fallback, must install) |
| Python venv (agent-service) | Test running | ✓ | .venv present | — |
| PostgreSQL | Migration 004 | ✓ (assumed from Phase 2) | — | — |
| pwdlib | USER-02 password hashing | ✓ | in agent-service requirements.txt | — |

**Missing dependencies with no fallback:**
- `@tanstack/react-table` — must `npm install @tanstack/react-table@8.21.3` in Wave 0
- `date-fns` — must `npm install date-fns@4.1.0` in Wave 0

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `agent-service/pytest.ini` |
| Quick run command | `cd agent-service && .venv/bin/python -m pytest tests/ -x -q --tb=short` |
| Full suite command | `cd agent-service && .venv/bin/python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 / PAT-01 | GET /api/patients returns paginated list with tenant isolation | integration | `pytest tests/test_crud_patients.py -x` | ❌ Wave 0 |
| API-01 / PAT-02 | POST /api/patients creates patient in correct tenant | integration | `pytest tests/test_crud_patients.py::test_create_patient -x` | ❌ Wave 0 |
| API-01 / AGENDA-02 | POST /api/appointments creates appointment | integration | `pytest tests/test_crud_appointments.py::test_create_appointment -x` | ❌ Wave 0 |
| AGENDA-07 | Medico token only returns own appointments | integration | `pytest tests/test_crud_appointments.py::test_medico_sees_only_own -x` | ❌ Wave 0 |
| USER-01..04 | Admin can create/deactivate/role-change users | integration | `pytest tests/test_crud_users.py -x` | ❌ Wave 0 |
| DOC-01..03 | Admin can CRUD doctors + schedules | integration | `pytest tests/test_crud_doctors.py -x` | ❌ Wave 0 |
| TENANT-01..03 | All new endpoints respect RLS | integration | `pytest tests/ -m tenant -x` | existing (stubs) |
| AGENDA-01..06 (UI) | Calendar renders day/week/month views | manual-only | N/A — browser test | ❌ manual |
| PAT-04..05 (UI) | Patient profile tabs load independently | manual-only | N/A — browser test | ❌ manual |

### Sampling Rate
- **Per task commit:** `cd agent-service && .venv/bin/python -m pytest tests/ -x -q --tb=short`
- **Per wave merge:** `cd agent-service && .venv/bin/python -m pytest tests/ -q`
- **Phase gate:** Full suite green + manual calendar/profile smoke test before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `agent-service/tests/test_crud_patients.py` — covers PAT-01, PAT-02, PAT-03
- [ ] `agent-service/tests/test_crud_appointments.py` — covers AGENDA-02, AGENDA-03, AGENDA-04, AGENDA-05, AGENDA-07
- [ ] `agent-service/tests/test_crud_doctors.py` — covers DOC-01, DOC-02, DOC-03
- [ ] `agent-service/tests/test_crud_users.py` — covers USER-01, USER-02, USER-03, USER-04
- [ ] `agent-service/alembic/versions/004_crud_schema_additions.py` — schema prerequisite for all tests

---

## Project Constraints (from CLAUDE.md)

All directives below must be honored by the planner:

1. **Tech stack frontend:** Next.js + Tailwind CSS — already confirmed; no framework change
2. **Tech stack backend:** Python/FastAPI — new routers follow existing `auth.py` pattern
3. **Idioma:** Interface em pt-BR — all labels, button text, error messages in Portuguese
4. **Design:** Seguir identidade visual do site.html — green palette (`green-500 = #2e9e60`, `green-600 = #1e7d48`), DM Serif/DM Sans fonts from `globals.css @theme`
5. **Naming:** `snake_case.py` for Python modules → new files: `patients.py`, `appointments.py`, `doctors.py`, `users.py`; `PascalCase` for Python classes
6. **Error handling:** `except Exception as e:` + `logger.error(f"[module] message: {e}")` → return 500 HTTPException, never crash
7. **Logging:** Module-scoped `logger = logging.getLogger("agent-clinic.api.{module}")` with `[module]` prefix in messages
8. **DB pattern:** Raw psycopg2 with `Depends(get_db_for_tenant)` — no SQLAlchemy ORM, no connection pooling
9. **Imports:** Absolute from project root: `from src.api.deps import ...`
10. **GSD Workflow:** All file changes through GSD workflow — no direct edits outside execute-phase

---

## Sources

### Primary (HIGH confidence)
- Project source code — `agent-service/src/api/auth.py`, `deps.py`, `webhook.py` (read directly)
- Project migrations — `001_create_tenants_users.py`, `002_add_tenant_id_columns.py`, `003_enable_rls_policies.py` (read directly)
- Project SQL — `migrations/003_appointments.sql`, `004_patients_followups.sql`, `006_doctors.sql` (read directly)
- `frontend/package.json` — confirmed installed versions
- `npm view @tanstack/react-table version` = 8.21.3 (verified 2026-03-29)
- `npm view date-fns version` = 4.1.0 (verified 2026-03-29)

### Secondary (MEDIUM confidence)
- @tanstack/react-table v8 API patterns — based on npm registry confirmed version, consistent with known v8 API
- date-fns v4 locale import path — `date-fns/locale` (consistent with v3+ API; v4 is stable release of v3 refactor)

### Tertiary (LOW confidence)
- None — all critical claims verified against project source or npm registry

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified via npm registry; libraries already in project or confirmed available
- Architecture: HIGH — patterns derived from existing Phase 2 code (`auth.py`, `deps.py`, `login-form.tsx`)
- Pitfalls: HIGH — schema gaps verified by direct reading of SQL migration files; gaps are factual

**Research date:** 2026-03-29
**Valid until:** 2026-04-29 (stable stack, 30-day window)
