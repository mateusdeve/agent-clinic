# Technology Stack

**Project:** Clinic Management SaaS — Web Frontend + Multi-Tenant Layer
**Researched:** 2026-03-29
**Scope:** Frontend only. Backend (FastAPI, LangGraph, Redis, PostgreSQL, Evolution API) is already built and out of scope.

---

## Context: What Already Exists

The existing backend (`agent-service/`) exposes:
- `POST /webhook/evolution` — receives messages from WhatsApp via Evolution API
- `GET /health` — health check
- Redis for session state per phone number
- PostgreSQL (SQLAlchemy) for appointments, patients, follow-ups, doctors
- FastAPI with background task processing
- No existing REST API for a frontend; no auth layer

The frontend must call the existing backend (and may need new API endpoints added to it) and also connect directly to the Evolution API WebSocket for real-time conversation monitoring.

---

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js | 16.1 | Full-stack React framework | Latest stable. App Router is now the unquestioned standard — 85%+ of new SaaS templates use it. Turbopack is default (2-5x faster builds). React 19.2 built in. Vercel-maintained. HIGH confidence. |
| React | 19.2 | UI runtime | Ships with Next.js 16. Required for shadcn/ui and TanStack Query v5. |
| TypeScript | 5.x | Type safety | Required by Next.js 16 minimum (5.1.0+). Non-negotiable for any production SaaS. |

**Why Next.js over plain Vite/React:** This is a SaaS dashboard, not a static site. Next.js App Router gives server components (reduces bundle), built-in API routes to proxy the FastAPI backend, middleware for auth, and the Cache Components model (PPR) for dashboards that mix static layout with live data. Plain Vite would require a separate Express/Hono BFF layer to handle auth and proxying — unnecessary complexity.

**Why not Next.js 15:** Next.js 16 released October 2025 and is stable with 16.1 patch. Turbopack stable, React Compiler stable, explicit caching model. Use it from day one.

---

### Styling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Tailwind CSS | v4 | Utility-first CSS | v4 released early 2025, now fully supported by shadcn/ui as of February 2025. Zero-config CSS-first architecture (no `tailwind.config.js` required). Native CSS cascade layers. Faster than v3. HIGH confidence. |
| shadcn/ui | latest (vendored) | UI component library | Not a package — components are copied into your codebase. Full Tailwind v4 support confirmed. React 19 compatible. Uses Recharts v3 for charts. The dominant component system for Next.js SaaS in 2025/2026. Hospital/clinic dashboard templates available. HIGH confidence. |
| tw-animate-css | latest | Animations | Replaces `tailwindcss-animate` (deprecated). Default for new shadcn/ui projects. MEDIUM confidence. |

**Why shadcn/ui over Mantine/Chakra/MUI:** shadcn/ui components live in your repo, so you own and style them fully. No version lock-in or theme conflicts. Tailwind v4 is its primary target. The Radix UI primitives underneath ensure accessibility. For a clinic SaaS, the data-table, form, dialog, and command palette components cover 90% of UI needs out of the box.

---

### Authentication

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Better Auth | 1.5.6 | Auth + multi-tenant organizations | Open-source, self-hosted, TypeScript-first. Has a first-class `organization` plugin with owner/admin/member roles, invitations, RBAC, and dynamic access control. The Auth.js team merged into Better Auth in September 2025 — it is now the recommended library for new projects. No vendor lock-in (unlike Clerk). Works with PostgreSQL directly. HIGH confidence. |

**Why not Clerk:** Clerk charges per monthly active user, which is expensive for a SaaS with many clinic staff accounts. Clerk is hosted — your patient data and session tokens go through a third-party service, which is a compliance concern for healthcare. Better Auth is fully self-hosted.

**Why not Auth.js (NextAuth v5):** The Auth.js development team joined Better Auth in September 2025. Auth.js receives only security patches now. Better Auth is the forward path and has a more complete feature set (RBAC, organization plugin, passkeys, impersonation).

**Multi-tenancy model:** Each clinic is an `organization` in Better Auth. Users belong to one or more organizations with roles. Session includes `activeOrganizationId`, which is passed as a header to the FastAPI backend for tenant scoping. PostgreSQL Row-Level Security (RLS) on the backend enforces tenant isolation at the database level.

---

### Data Fetching

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| TanStack Query | v5.95+ | Server state, caching, mutations | 12.3M weekly downloads, overtook SWR in late 2024. Superior TypeScript inference in v5. Built-in devtools. Optimistic updates with rollback (critical for appointment booking). Garbage collection and stale-time configuration. Works seamlessly with Next.js App Router via prefetch/hydration. HIGH confidence. |

**Why not SWR:** SWR is a fine library, but TanStack Query's mutation support, devtools, garbage collection, and dependent query patterns are essential for a dashboard with appointment management, patient records, and real-time follow-up data. SWR is better for simple read-heavy use cases.

**Why not exclusively Server Components:** The WhatsApp conversation panel requires real-time updates and interactive filtering — these are inherently client-side. Use Server Components for static dashboard shells (layout, navigation, initial data) and TanStack Query for the interactive portions.

---

### Forms

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| React Hook Form | 7.72.0 | Form state management | Industry standard. Zero re-renders on input change. Integrates directly with shadcn/ui via the Form component. MEDIUM-HIGH confidence. |
| Zod | v3 (pin to ^3.x) | Schema validation | **Use Zod v3, not v4.** Zod v4 was released in 2025 but has known compatibility issues with `@hookform/resolvers` (tracked in react-hook-form#12816 and zod#4989). shadcn/ui's form docs use Zod v3. Stick with v3 until resolvers fully support v4. HIGH confidence for v3 recommendation. |
| @hookform/resolvers | ^5.x | Bridges RHF and Zod | Required adapter. Install alongside react-hook-form and zod. HIGH confidence. |

---

### Real-Time (WhatsApp Panel)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Evolution API WebSocket | — | Live message feed | Evolution API natively exposes WebSocket events (global mode: all instances; traditional mode: per instance). The frontend connects directly to the Evolution API WebSocket to receive `messages.upsert` and status events. No additional real-time infrastructure needed for the conversation panel. MEDIUM confidence (verify WebSocket event schema from Evolution API docs). |
| Native `WebSocket` API or `useWebSocket` (react-use-websocket) | ^4.x | WebSocket client hook | `react-use-websocket` provides reconnection, heartbeat, and message history out of the box. Alternatively, wrap native WebSocket in a custom hook if avoiding an extra dependency. MEDIUM confidence. |

**Architecture note:** For the real-time WhatsApp panel, the frontend connects to the Evolution API WebSocket directly (or via a Next.js API route proxy for auth). Do NOT use Socket.io — there is no Node.js WebSocket server in this stack. Do NOT use server-sent events from FastAPI for the conversation panel (FastAPI is not running as a persistent WebSocket server; it handles webhooks and background tasks). The Evolution API is already the source of truth for message events.

**For dashboard metrics (appointment counts, agent activity):** Use TanStack Query with a short `staleTime` (e.g., 30s) polling pattern against new FastAPI REST endpoints. SSE from FastAPI is an option for live agent status if polling is insufficient, but implement it only if polling causes UX issues.

---

### Charts & Analytics

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| shadcn/ui Charts (built on Recharts v3) | — | Dashboard charts | shadcn/ui's chart components are the lowest-friction choice — they use the same design system as the rest of the UI, are copy-pasteable, and internally use Recharts v3. Recharts v3 requires a `react-is` override for React 19 (documented in shadcn/ui React 19 guide). For simple appointment trend lines, conversion funnels, and agent activity charts, this is sufficient. HIGH confidence. |

**Why not Tremor:** Tremor was acquired by Vercel in January 2025. Its component library overlaps heavily with shadcn/ui charts, and maintaining two design systems is expensive. shadcn/ui charts cover all dashboard needs for this project.

**Why not Chart.js:** Chart.js has no first-class React integration (you use `react-chartjs-2`, a wrapper). Recharts is written for React from the ground up and renders via SVG with proper React reconciliation.

---

### State Management

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Zustand | ^5.x | Global client state | Used for UI state that spans components but isn't server state: active conversation, selected clinic (active organization), sidebar open/close, notification preferences. Not for API data — TanStack Query owns that. Zustand grew 150% in 2025 adoption. Simple store model, no boilerplate, good TypeScript support. HIGH confidence. |

**What NOT to use:** Redux / Redux Toolkit — significant boilerplate overhead for this scale. React Context for frequently-updating state — causes unnecessary re-renders across the component tree.

---

### ORM / Database Client (Frontend API layer)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Prisma | ^6.x | TypeScript ORM for Next.js API routes | The Next.js API routes (or Server Actions) that query PostgreSQL directly need an ORM. Prisma is recommended over Drizzle here because: (1) the backend already uses SQLAlchemy with existing migrations — Prisma will introspect the existing schema rather than own migrations; (2) Prisma's DX is faster for new team members; (3) Prisma 7 improved edge runtime support. Use Prisma for READ queries from the frontend (dashboard stats, patient lists). All writes that involve business logic (booking, follow-up) should call the FastAPI backend, not bypass it. MEDIUM confidence — Drizzle is a valid alternative if the team prefers SQL-first. |

**Alternative (if edge runtime is required):** Drizzle ORM — smaller bundle, code-first TypeScript schemas, better for Cloudflare Workers / Vercel Edge. Choose Drizzle if you plan to run any Next.js route handlers on the edge.

---

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| next-safe-action | ^7.x | Type-safe Server Actions | Wraps Next.js Server Actions with input validation (Zod), error handling, and optimistic updates. Use for all mutations that go through Server Actions. |
| date-fns | ^3.x | Date formatting | Appointment dates, conversation timestamps. Prefer over dayjs for tree-shaking. |
| lucide-react | latest | Icons | Default icon set for shadcn/ui. Do not add another icon library. |
| nuqs | ^2.x | URL search params state | For filterable tables (patient list, conversation history). Syncs filter state to URL, enabling shareable links. |
| @tanstack/react-table | ^8.x | Headless table primitives | shadcn/ui DataTable is built on this. Use for patient lists, appointment tables. |
| react-use-websocket | ^4.x | WebSocket hook | For the WhatsApp conversation panel. Handles reconnection and message buffering. |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Framework | Next.js 16 | Remix v3 / Vite+React | Remix is excellent but smaller ecosystem for SaaS templates. Next.js 16 has Cache Components + Turbopack stable now. |
| Auth | Better Auth | Clerk | Per-MAU pricing, third-party data hosting (compliance risk for clinic patient data). |
| Auth | Better Auth | NextAuth v5 / Auth.js | Auth.js team merged into Better Auth September 2025. Auth.js is in maintenance mode. |
| Styling | Tailwind v4 + shadcn/ui | MUI (Material UI) | MUI imposes Google's design language. Tailwind gives full design control. shadcn/ui healthcare templates exist. |
| Charts | shadcn/ui Charts (Recharts) | Tremor | Tremor overlaps with shadcn/ui and adds a second design system. Acquired by Vercel but still a separate dependency. |
| ORM | Prisma | Drizzle | Both are valid. Prisma chosen for DX; swap to Drizzle if edge runtime or raw SQL control is needed. |
| State | Zustand | Jotai | Jotai is better for fine-grained atomic state. Zustand is simpler for the slice-based state this dashboard needs (activeOrg, activeConversation, etc.). |
| Real-time | Evolution API WebSocket | Socket.io | No Node.js WebSocket server exists in this stack. Evolution API already emits WebSocket events natively. |
| Forms | React Hook Form + Zod v3 | TanStack Form | TanStack Form is newer and more type-safe, but ecosystem (shadcn/ui form docs, tutorials) is built around RHF. Use RHF for now. |

---

## Installation

```bash
# Create Next.js 16 project
npx create-next-app@latest clinic-frontend --typescript --tailwind --app --src-dir

# Authentication
npm install better-auth

# Data fetching
npm install @tanstack/react-query @tanstack/react-query-devtools

# Forms
npm install react-hook-form zod @hookform/resolvers

# State
npm install zustand

# UI primitives (shadcn CLI handles component installation)
npx shadcn@latest init

# Date utilities
npm install date-fns

# URL state
npm install nuqs

# WebSocket hook
npm install react-use-websocket

# Server Actions
npm install next-safe-action

# ORM (for Next.js API routes that query Postgres directly)
npm install prisma @prisma/client
npx prisma db pull  # introspect existing SQLAlchemy schema

# Charts (via shadcn CLI)
npx shadcn@latest add chart
# Note: React 19 requires react-is override:
# Add to package.json: "overrides": { "react-is": "^19.0.0" }
```

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Next.js 16 | HIGH | Official docs verified, stable release October 2025 |
| Tailwind v4 + shadcn/ui | HIGH | shadcn/ui Tailwind v4 guide published February 2025, fully supported |
| Better Auth 1.5.6 | HIGH | npm verified, organization plugin confirmed, Auth.js merger confirmed |
| TanStack Query v5 | HIGH | npm verified at 5.95.x, official docs current |
| React Hook Form + Zod v3 | HIGH | npm verified, Zod v4 compatibility issue confirmed via GitHub issues |
| Evolution API WebSocket | MEDIUM | WebSocket existence confirmed in Evolution docs; specific event schema requires runtime verification |
| Prisma for frontend ORM | MEDIUM | Valid choice but Drizzle is a strong alternative — team preference should decide |
| Recharts v3 + React 19 | MEDIUM | Works with `react-is` override workaround; shadcn/ui documents the fix |
| Zustand | HIGH | npm trends and multiple sources confirm dominance for SaaS dashboards in 2025 |

---

## Sources

- [Next.js 16 Release Blog](https://nextjs.org/blog/next-16) — official
- [Next.js 16.1 Release](https://nextjs.org/blog/next-16-1) — official
- [shadcn/ui Tailwind v4 Guide](https://ui.shadcn.com/docs/tailwind-v4) — official
- [shadcn/ui React 19 Guide](https://ui.shadcn.com/docs/react-19) — official
- [Better Auth Organization Plugin](https://better-auth.com/docs/plugins/organization) — official
- [Better Auth 1.4 Blog](https://better-auth.com/blog/1-4) — official
- [TanStack Query v5 Docs](https://tanstack.com/query/v5/docs/react/installation) — official
- [Evolution API WebSocket Docs](https://doc.evolution-api.com/v2/en/integrations/websocket) — official
- [better-auth vs NextAuth vs Clerk Comparison](https://supastarter.dev/blog/better-auth-vs-nextauth-vs-clerk) — MEDIUM confidence
- [Drizzle vs Prisma 2026](https://makerkit.dev/blog/tutorials/drizzle-vs-prisma) — MEDIUM confidence
- [Recharts Support Recharts v3 — shadcn/ui issue](https://github.com/shadcn-ui/ui/issues/7669) — official tracker
- [Zod v4 zodResolver compatibility issue](https://github.com/react-hook-form/react-hook-form/issues/12829) — official tracker
- [Next.js App Router in 2026 Guide](https://dev.to/ottoaria/nextjs-app-router-in-2026-the-complete-guide-for-full-stack-developers-5bjl) — MEDIUM confidence
- [Multi-Tenant SaaS with Postgres RLS](https://www.thenile.dev/blog/multi-tenant-rls) — MEDIUM confidence
