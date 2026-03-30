# Phase 06: Polish + Hardening - Research

**Researched:** 2026-03-30
**Domain:** Responsive CSS, React error boundaries, Next.js loading conventions, PostgreSQL RLS integration testing
**Confidence:** HIGH

## Summary

Phase 6 is a cross-cutting quality layer over a completed five-phase application. All features from Phases 1-5 are implemented; this phase makes them production-ready across four orthogonal concerns: responsive layout, error resilience, loading feedback, and tenant isolation verification.

The frontend runs Next.js 16.2.1 with Tailwind CSS 4 (CSS-first, no `tailwind.config.ts`). The dashboard layout uses `hidden md:flex` for the sidebar — meaning on mobile there is currently no navigation at all. Every page-level client component handles loading and error state inline (e.g. `DashboardClient`, `PacientesPage`), but there are no Next.js `error.tsx` or `loading.tsx` route segment files. Tenant isolation is enforced via PostgreSQL RLS, but the two key integration tests (`test_rls_policies_exist`, `test_tenant_isolation_across_clinics`) are still `xfail` — they require a live DB connection that was skipped in earlier phases.

**Primary recommendation:** Work in four focused streams — (1) responsive: add mobile nav drawer + fix table/calendar overflow at 375px and 768px; (2) error boundaries: add `error.tsx` per route segment + inline API error states; (3) loading: add `loading.tsx` route stubs + skeleton patterns; (4) tenant tests: activate the two xfail RLS integration tests against the real DB.

## Project Constraints (from CLAUDE.md)

- **Frontend stack**: Next.js + Tailwind CSS (no alternatives)
- **Backend stack**: Python/FastAPI — keep as-is
- **Tailwind 4 CSS-first**: All tokens in `globals.css @theme`, no `tailwind.config.ts`
- **Portuguese UI**: All user-facing text in pt-BR
- **Design identity**: Green palette (green-600 primary), DM Serif Display headings, DM Sans body
- **No formatters enforced**: Follow PEP 8 (Python), 4-space indent; TypeScript follows existing code style
- **Error handling pattern (backend)**: catch-all `except Exception as e`, log with module prefix, return safe defaults
- **GSD workflow**: All file changes must go through a GSD command (execute-phase for planned work)
- **No CONTEXT.md for this phase**: No locked decisions; this is a quality/hardening phase with implementation freedom

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.2.1 (installed) | Route-level error.tsx, loading.tsx, unstable_retry | Official file conventions — no additional install needed |
| Tailwind CSS | 4.x (installed) | Responsive utilities (md:, lg: prefixes) | Already in project, CSS-first config |
| React | 19.2.4 (installed) | Error boundaries, Suspense, useState loading patterns | Already in project |
| pytest | 8.4.2 (installed) | Tenant isolation integration tests | Already in project test suite |
| psycopg2 | 2.9.11 (installed) | Direct DB queries for RLS verification | Already used in conftest.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | 1.7.0 (installed) | AlertCircle, Loader2, WifiOff icons for error/loading states | In all error state UI and loading spinners |
| date-fns | 4.1.0 (installed) | Already used; no new dependency | — |

**No new packages required for this phase.** All needed libraries are already installed.

## Architecture Patterns

### Recommended Project Structure Additions
```
frontend/src/app/
├── (dashboard)/
│   ├── error.tsx          # NEW — catches render errors in entire dashboard segment
│   ├── loading.tsx        # NEW — Suspense fallback for dashboard route transitions
│   ├── home/
│   │   └── loading.tsx    # OPTIONAL — skeleton for KPI cards
│   ├── agenda/
│   │   └── error.tsx      # OPTIONAL — agenda-specific error recovery
│   └── whatsapp/
│       └── error.tsx      # OPTIONAL — inbox error boundary
├── global-error.tsx       # NEW — catches root layout errors (must include <html><body>)
└── (landing)/
    └── error.tsx          # OPTIONAL — landing page errors
```

### Pattern 1: Next.js Route Segment Error Boundary (error.tsx)

**What:** A `error.tsx` file co-located with a route segment auto-wraps the segment in a React Error Boundary. Replaces the segment with fallback UI when a render or async error occurs.

**When to use:** Any route that performs data fetching or has complex rendering that can fail at the route level.

**Key constraint:** Must be `'use client'` — error boundaries are always Client Components.

**Next.js 16.2.x specific:** Uses `unstable_retry` prop (not the older `reset`). The `reset` function still exists but `unstable_retry` is preferred as it re-fetches server data.

```tsx
// Source: frontend/node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/error.md
'use client'

import { useEffect } from 'react'
import { AlertCircle } from 'lucide-react'

export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  useEffect(() => {
    console.error('[error-boundary]', error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4 text-gray-600">
      <AlertCircle className="size-10 text-red-400" />
      <p className="text-sm">Ocorreu um erro ao carregar esta pagina.</p>
      <button
        onClick={() => unstable_retry()}
        className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
      >
        Tentar novamente
      </button>
    </div>
  )
}
```

### Pattern 2: Next.js Route Segment Loading State (loading.tsx)

**What:** A `loading.tsx` co-located with a route segment wraps `page.tsx` in a `<Suspense>` boundary. Shows skeleton UI during server-side data loading and route transitions.

**When to use:** Any server component page or route transition where content takes visible time to load.

**Note:** Most dashboard pages are `'use client'` with `useState(isLoading)` — `loading.tsx` applies only to RSC pages and route transitions. For client components, the existing `isLoading` inline patterns should remain; add `loading.tsx` for the route transition skeleton only.

```tsx
// Source: frontend/node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/loading.md
export default function Loading() {
  return (
    <div className="space-y-4 p-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-16 bg-gray-100 rounded-lg animate-pulse" />
      ))}
    </div>
  )
}
```

### Pattern 3: Global Error Boundary (global-error.tsx)

**What:** Catches errors in the root layout. Must include `<html>` and `<body>` tags since it replaces the root layout entirely.

**When to use:** One file at `src/app/global-error.tsx` to prevent blank white screens for root-level failures.

```tsx
// Source: Next.js official docs — global-error
'use client'

export default function GlobalError({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string }
  unstable_retry: () => void
}) {
  return (
    <html lang="pt-BR">
      <body className="flex items-center justify-center min-h-screen bg-off-white">
        <div className="text-center space-y-4 p-8">
          <h2 className="font-serif text-2xl text-gray-800">Algo deu errado</h2>
          <p className="text-sm text-gray-500">
            Por favor, tente novamente ou entre em contato com o suporte.
          </p>
          <button
            onClick={() => unstable_retry()}
            className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
          >
            Tentar novamente
          </button>
        </div>
      </body>
    </html>
  )
}
```

### Pattern 4: Inline API Error State (existing pattern, to standardize)

The existing codebase uses inline error states in client components. `DashboardClient` returns `<p>Nao foi possivel carregar...</p>` on error — but does not use a structured error component. `PacientesPage` renders a red banner div. The pattern to standardize:

```tsx
// Pattern already established in pacientes/page.tsx — extend to all pages
{error && (
  <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 flex items-center gap-2">
    <AlertCircle className="size-4 shrink-0" />
    {error}
  </div>
)}
```

### Pattern 5: Mobile Navigation Drawer

**What:** The dashboard layout has `aside className="hidden md:flex ..."` — mobile gets NO navigation. Need a hamburger + mobile drawer for 375px.

**Approach:** Extend `(dashboard)/layout.tsx` with a `MobileNav` client component. Since layout.tsx is a server component, extract mobile nav as a separate `'use client'` child that uses `useState` for open/closed state.

```tsx
// MobileNav.tsx — 'use client'
// Triggered by hamburger button in header
// Renders a full-width overlay panel with same nav links as desktop sidebar
// Close on link click or outside-click (useEffect + event listener)
```

**Important constraint:** `layout.tsx` is a Server Component. Extract the interactive mobile nav as a `'use client'` component. This is the same pattern used for `LogoutButton`.

### Pattern 6: Table/Calendar Responsive Overflow

**What:** DataTable uses `@tanstack/react-table` with full-width rendering. Calendar (`CalendarDay`, `CalendarWeek`) uses absolute positioning. Both need horizontal scroll containers on small viewports.

**Approach:**
- Wrap DataTable in `<div className="overflow-x-auto -mx-4 px-4">` (negative margin trick to break out of padding, then re-add padding for visual alignment)
- CalendarWeek: already width-constrained by column count; needs `overflow-x-auto` wrapper
- CalendarDay/month: visually simpler, check height on mobile

### Pattern 7: Responsive KPI Grid

**Current:** `grid-cols-2 lg:grid-cols-5` — at 375px this gives 2-column layout which is acceptable. At 768px (tablet), 2-column may look sparse with 5 KPIs. Verify and adjust if needed. Recharts charts need `width="100%"` and `aspect` prop instead of fixed pixel widths.

### Pattern 8: Tenant Isolation Integration Tests (activate xfail stubs)

**What:** `test_rls_policies_exist` and `test_tenant_isolation_across_clinics` in `tests/test_tenant_isolation.py` are marked `xfail` with stub implementations. They need real DB connection (already available via `DATABASE_URL` env var + `db_conn` fixture in `conftest.py`).

**Current status:**
- `test_rls_policies_exist`: xfail — tests that RLS is enabled on 8 tables; the actual RLS migration ran in Phase 2, so this test should pass now
- `test_tenant_isolation_across_clinics`: xfail — sets `app.tenant_id` to a non-existent UUID and verifies `SELECT count(*) FROM patients` returns 0 via RLS; should pass with live DB
- `test_get_db_for_tenant_sets_session_var`: already **XPASS** (passes despite xfail mark) — confirms `get_db_for_tenant` implementation is correct

**Action:** Remove `xfail` decorators, run against live DB. If RLS is active (Phase 2 migration ran), these should green-light immediately.

### Anti-Patterns to Avoid

- **`reset` instead of `unstable_retry`:** Next.js 16.2 error.tsx uses `unstable_retry` — using old `reset` prop will TypeScript-error
- **Error boundary in Server Components:** `error.tsx` must be `'use client'` — attempting RSC will fail at build
- **Mobile nav in Server Component:** layout.tsx is RSC; interactive state must be in a child Client Component
- **`overflow-hidden` on calendar parent without scroll:** Wrapping calendar in overflow-hidden without overflow-x-auto causes content cut-off, not scroll
- **Fixed-pixel Recharts chart widths:** Charts with fixed `width={600}` overflow at 375px; use `width="100%"` with `<ResponsiveContainer>`
- **Recharts in Server Component:** Recharts uses browser APIs; components must have `'use client'` (already done in TrendChart/EspecialidadeChart)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Route-level error boundaries | Custom class ErrorBoundary wrapping every page | Next.js `error.tsx` convention | Auto-integrated with React Suspense tree, handles server errors, free unstable_retry |
| Loading fallback for route transitions | Manual spinner in layout | Next.js `loading.tsx` convention | Auto-wraps page.tsx in Suspense, instant fallback during navigation |
| Responsive table | Custom mobile table | `overflow-x-auto` wrapper on existing DataTable | DataTable already built; just needs scroll container |
| Mobile navigation | Full re-implementation | Extract `MobileNav.tsx` client component from existing layout | Reuse existing link structure, add drawer behavior |

**Key insight:** This phase adds NO new libraries and builds NO new abstractions. It adds Next.js file conventions (`error.tsx`, `loading.tsx`) and Tailwind utility classes to existing components.

## Common Pitfalls

### Pitfall 1: `error.tsx` Does Not Catch Layout Errors
**What goes wrong:** An `error.tsx` in `(dashboard)/` only catches errors in children of that layout — not errors in the layout file itself.
**Why it happens:** React error boundaries cannot catch errors in the same component.
**How to avoid:** Add `global-error.tsx` at `src/app/` for root layout errors. Add separate `error.tsx` per segment for segment-level errors.
**Warning signs:** White blank page with no UI at all — means root layout threw, no boundary caught it.

### Pitfall 2: Mobile Nav State in Server Component
**What goes wrong:** Adding `useState` for hamburger open/closed state directly in `(dashboard)/layout.tsx` causes Next.js build error: "You're importing a component that needs `useState`. It only works in a Client Component."
**Why it happens:** `layout.tsx` is a Server Component — it cannot use React hooks.
**How to avoid:** Extract `MobileNav` as a separate `'use client'` component, import it into layout. Same pattern already used for `LogoutButton` in this project.

### Pitfall 3: xfail Tests Require Live Database
**What goes wrong:** The two tenant isolation xfail stubs will only pass with `DATABASE_URL` pointing to a real PostgreSQL instance with the Phase 2 RLS migrations applied.
**Why it happens:** The conftest fixture `db_conn` skips if `DATABASE_URL` is not set.
**How to avoid:** Run `python3 -m pytest tests/test_tenant_isolation.py -v` locally after removing xfail marks, with valid `DATABASE_URL` in `.env`. Don't mark as passing until the real DB confirms.
**Warning signs:** `SKIPPED (DATABASE_URL not set)` — means env not loaded.

### Pitfall 4: `overflow-x-auto` on Wrong Element
**What goes wrong:** Adding `overflow-x-auto` to the outer page container causes the entire page to scroll horizontally instead of just the table.
**Why it happens:** `overflow-x-auto` must be scoped to the table's direct wrapper, not a parent that contains other content.
**How to avoid:** Wrap only the DataTable render call: `<div className="overflow-x-auto"><DataTable .../></div>`

### Pitfall 5: Recharts `ResponsiveContainer` Height Requirement
**What goes wrong:** `<ResponsiveContainer width="100%" height={300}>` works, but `<ResponsiveContainer width="100%" height="100%">` renders 0px height if the parent has no fixed height.
**Why it happens:** Percentage height requires a parent with explicit height.
**How to avoid:** Always use a fixed pixel value for height in `ResponsiveContainer`: `height={300}` or `height={200}`. The existing `TrendChart` and `EspecialidadeChart` components already use this pattern — verify before changing.

### Pitfall 6: `unstable_retry` vs `reset` in error.tsx
**What goes wrong:** TypeScript error: "Property 'reset' does not exist on type..."
**Why it happens:** Next.js 16.2.0 changed the prop name from `reset` to `unstable_retry`.
**How to avoid:** Use `unstable_retry` as shown in the official docs. Already documented in the version history: `v16.2.0` added `unstable_retry`.

## Code Examples

### Loading Skeleton Component (reusable)
```tsx
// Source: Pattern derived from existing DashboardClient loading state
// Can be placed in src/components/dashboard/LoadingSkeleton.tsx
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      <div className="h-10 bg-gray-100 rounded animate-pulse" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-12 bg-gray-50 rounded animate-pulse" />
      ))}
    </div>
  )
}
```

### Mobile Navigation Drawer (client component)
```tsx
// Source: Pattern extrapolated from existing LogoutButton client component pattern
'use client'
import { useState } from 'react'
import { Menu, X } from 'lucide-react'

interface MobileNavProps {
  role: string
}

export function MobileNav({ role }: MobileNavProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Hamburger button — visible only on mobile */}
      <button
        className="md:hidden p-2 text-gray-600 hover:text-gray-800"
        onClick={() => setOpen(true)}
        aria-label="Abrir menu"
      >
        <Menu className="size-5" />
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Drawer */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform md:hidden ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between p-4 border-b">
          <span className="font-serif text-green-600 text-lg">MedIA</span>
          <button onClick={() => setOpen(false)} aria-label="Fechar menu">
            <X className="size-5 text-gray-500" />
          </button>
        </div>
        <nav className="flex flex-col gap-1 p-4">
          {/* Same links as desktop sidebar */}
        </nav>
      </div>
    </>
  )
}
```

### Tenant Isolation Test (activated)
```python
# Source: agent-service/tests/test_tenant_isolation.py — remove xfail decorators
@pytest.mark.tenant
def test_rls_policies_exist(db_conn):
    """RLS policies are enabled on all data tables (TENANT-01)."""
    cursor = db_conn.cursor()
    tables = ["patients", "appointments", "doctors", "conversations",
              "conversation_summaries", "knowledge_chunks", "follow_ups", "users"]
    for table in tables:
        cursor.execute(
            "SELECT relrowsecurity FROM pg_class WHERE relname = %s",
            (table,)
        )
        row = cursor.fetchone()
        assert row is not None, f"Table {table} not found"
        assert row[0] is True, f"RLS not enabled on {table}"

@pytest.mark.tenant
def test_tenant_isolation_across_clinics(db_conn):
    """Non-matching tenant_id returns zero rows (TENANT-02)."""
    cursor = db_conn.cursor()
    cursor.execute("SET LOCAL app.tenant_id = '00000000-0000-0000-0000-000000000099'")
    cursor.execute("SELECT count(*) FROM patients")
    count = cursor.fetchone()[0]
    assert count == 0, "RLS should filter out rows for non-matching tenant"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `reset` prop in error.tsx | `unstable_retry` prop | Next.js v16.2.0 | Must use new prop name — TypeScript will error on `reset` |
| Separate `@tailwindcss/jit` config | CSS-first `@theme` in globals.css | Tailwind 4.0 | All breakpoints/utilities still work; no behavior change for responsive work |
| Class-based React Error Boundaries | `error.tsx` file convention | Next.js 13+ | File convention is simpler; class-based still works inside components |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.9 | Tenant isolation tests | ✓ | 3.9.6 | — |
| pytest | Test runner | ✓ | 8.4.2 | — |
| psycopg2 | DB connection in tests | ✓ | 2.9.11 | — |
| PostgreSQL (with RLS migrations) | test_rls_policies_exist, test_tenant_isolation | Must verify at runtime | — | Skip with xfail if DB unavailable |
| Node.js | Next.js build | ✓ | (present, next dev works) | — |

**Missing dependencies with no fallback:**
- PostgreSQL with Phase 2 RLS migrations applied — required for 2 tenant isolation tests. If not available in CI, tests must be marked `pytest.mark.skipif` with `DATABASE_URL` check (already handled by `conftest.py` fixture skip logic).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `agent-service/pytest.ini` |
| Quick run command | `cd agent-service && python3 -m pytest tests/test_tenant_isolation.py tests/test_rbac.py -v` |
| Full suite command | `cd agent-service && python3 -m pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map

Phase 6 has no formal requirement IDs (cross-cutting quality layer). Success criteria map to tests:

| Success Criterion | Behavior | Test Type | Automated Command | Status |
|----------|-----------|-------------------|-------------|---------|
| SC-1: responsive 768px + 375px | Dashboard pages usable on tablet/mobile | manual visual | `next dev` + browser devtools | Manual |
| SC-2: error states | Network failures show user-friendly UI | manual + unit | n/a — visual verification | Manual |
| SC-3: tenant isolation | No cross-tenant data leakage | integration | `python3 -m pytest tests/test_tenant_isolation.py -v` | `xfail` → activate |
| SC-4: loading states | Async ops show loading indicators | manual visual | `next dev` + network throttle | Manual |
| RBAC pass | Role restrictions enforced | integration | `python3 -m pytest tests/test_rbac.py -v` | 3 XPASS (already passing) |
| Auth pass | Login/token flow correct | integration | `python3 -m pytest tests/test_auth.py -v` | xfail (need live DB) |

### Sampling Rate
- **Per task commit:** `cd agent-service && python3 -m pytest tests/test_tenant_isolation.py tests/test_rbac.py -v --tb=short`
- **Per wave merge:** `cd agent-service && python3 -m pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green (with xfail-to-pass upgrades for tenant isolation) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `frontend/src/app/(dashboard)/error.tsx` — route segment error boundary
- [ ] `frontend/src/app/global-error.tsx` — root layout error boundary
- [ ] `frontend/src/app/(dashboard)/loading.tsx` — dashboard loading skeleton
- [ ] `frontend/src/components/dashboard/MobileNav.tsx` — mobile navigation drawer client component

*(Existing test infrastructure covers backend test requirements. No new test files needed beyond activating existing xfail stubs.)*

## Open Questions

1. **Are Phase 2 RLS migrations actually applied to the local dev DB?**
   - What we know: The Alembic migrations were planned and executed in Phase 2
   - What's unclear: Whether the current dev DB has been migrated (no migration status file checked)
   - Recommendation: Run `python3 -m pytest tests/test_tenant_isolation.py -v` immediately after removing xfail — if it fails with "RLS not enabled", the migration needs re-running

2. **WhatsApp inbox 3-column layout on mobile**
   - What we know: `InboxPanel` uses `-m-6` to escape padding for full-height layout; has 3 columns (list, thread, sidebar) with complex flexbox
   - What's unclear: Whether the 3-column inbox should collapse to a 1-column view (show list → tap → show thread) or just be hidden behind a note saying "use tablet or desktop"
   - Recommendation: Collapse to single-panel on mobile (list default, back button to return from thread). This is the standard inbox pattern.

3. **LGPD compliance scope**
   - What we know: The phase goal mentions "compliant with LGPD data handling requirements" but no specific LGPD requirements are in REQUIREMENTS.md
   - What's unclear: Whether any concrete LGPD work is needed (consent logging, data deletion endpoint, privacy policy page) or if this was aspirational wording
   - Recommendation: The success criteria (SC-1 through SC-4) do not include LGPD items — treat as out of scope for this phase unless the user adds explicit requirements. The planner should not invent LGPD tasks not in the success criteria.

## Sources

### Primary (HIGH confidence)
- `frontend/node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/error.md` — error.tsx API, unstable_retry prop, global-error.tsx
- `frontend/node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/loading.md` — loading.tsx API, Suspense integration
- `agent-service/tests/test_tenant_isolation.py` — existing xfail stubs to activate
- `agent-service/tests/conftest.py` — db_conn fixture, skip behavior

### Secondary (MEDIUM confidence)
- Codebase walkthrough: `(dashboard)/layout.tsx`, `DashboardClient.tsx`, `pacientes/page.tsx`, `InboxPanel.tsx` — responsive gaps confirmed by reading source

### Tertiary (LOW confidence)
- LGPD scope interpretation — derived from absence of explicit requirements in REQUIREMENTS.md

## Metadata

**Confidence breakdown:**
- Responsive patterns: HIGH — confirmed by reading actual layout source, Tailwind 4 docs in-project
- Error boundary patterns: HIGH — read from Next.js 16.2.1 official docs in node_modules
- Loading patterns: HIGH — same source
- Tenant isolation tests: HIGH — read actual test stubs and conftest
- LGPD scope: LOW — inferred from requirements absence

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable project, no fast-moving dependencies introduced)
