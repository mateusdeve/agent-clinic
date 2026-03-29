# Stack Research: MedIA Frontend

**Research Date:** 2026-03-29
**Domain:** Clinic Management SaaS — Frontend + Multi-tenancy Layer

## Recommended Frontend Stack

### Core Framework

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **Next.js** (App Router) | 15.x | High | SSR for landing page SEO, API routes as BFF, middleware for auth/tenant routing |
| **React** | 19.x | High | Ships with Next.js 15, concurrent features, Server Components |
| **TypeScript** | 5.x | High | Type safety critical for multi-tenant data boundaries |
| **Tailwind CSS** | 4.x | High | Utility-first, fast iteration, matches site.html design system |

### UI Components

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **shadcn/ui** | latest | High | Not a dependency — copy/paste components. Tailwind-native, fully customizable, excellent for dashboards |
| **Radix UI** | 1.x | High | Underlying primitives for shadcn. Accessible, unstyled, composable |
| **Lucide React** | 0.4x | Medium | Icon set, consistent with shadcn defaults |

**Why NOT Material UI / Ant Design:** Heavy bundles, opinionated styling conflicts with custom clinic branding. shadcn gives full control.

### Data Fetching & State

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **TanStack Query** | 5.x | High | Server state management, caching, refetching, optimistic updates. Perfect for dashboard data |
| **Zustand** | 5.x | Medium | Client-only state (UI, modals, sidebar). Minimal API, no boilerplate |
| **nuqs** | 2.x | Medium | URL query state management for filters/pagination in tables |

**Why NOT Redux:** Overkill for this scale. TanStack Query handles server state, Zustand handles the rest.

### Authentication

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **NextAuth.js (Auth.js)** | 5.x | High | Credential provider calling FastAPI /auth/login. JWT strategy for stateless sessions |

**Flow:** NextAuth handles session on frontend → FastAPI issues/validates JWT → tenant_id + role embedded in token.

**Why NOT Clerk/Auth0:** Self-hosted auth avoids vendor lock-in, keeps health data in-house (LGPD compliance).

### Real-time

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **Socket.IO** (client) | 4.x | High | Reliable WebSocket with auto-reconnection, rooms (per-tenant), fallback to polling |
| **Socket.IO** (server, Python) | 5.x | High | python-socketio integrates with FastAPI via ASGI mount |

**Why NOT native WebSocket:** Socket.IO handles reconnection, namespaces (tenant isolation), rooms (conversation channels), and binary data out of the box.

### Forms & Validation

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **React Hook Form** | 7.x | High | Performant, uncontrolled inputs, minimal re-renders |
| **Zod** | 3.x | High | Schema validation, TypeScript-first, shared with API contracts |

### Tables & Data Display

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **TanStack Table** | 8.x | High | Headless table with sorting, filtering, pagination. Patient/appointment lists |
| **Recharts** | 2.x | Medium | Simple declarative charts for dashboard metrics (occupancy, confirmation rates) |

### Date/Time Handling

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **date-fns** | 4.x | High | Tree-shakeable, locale support (pt-BR), timezone handling for appointments |

### Landing Page

| Technology | Version | Confidence | Rationale |
|-----------|---------|------------|-----------|
| **Next.js Static Generation** | — | High | SSG for landing page = fast, SEO-friendly, cheap to host |
| **Framer Motion** | 12.x | Low | Animations matching site.html (fadeUp, hover effects). Optional — CSS animations may suffice |

## Backend Additions Required

The existing FastAPI backend needs these additions:

| Addition | Purpose |
|----------|---------|
| REST API layer | CRUD endpoints for frontend (patients, appointments, doctors, users) |
| JWT auth endpoints | /auth/login, /auth/register, /auth/refresh |
| Multi-tenancy middleware | tenant_id extraction from JWT, row-level filtering |
| Socket.IO server | Real-time WhatsApp message streaming to frontend |
| Template/campaign endpoints | Bulk message dispatch via Evolution API |

## What NOT to Use

| Technology | Reason |
|-----------|--------|
| **Redux / MobX** | Over-engineered for this scale |
| **Prisma** | Python backend, not Node.js |
| **tRPC** | Requires Node.js backend |
| **Clerk / Auth0** | Health data sovereignty, LGPD, vendor lock-in |
| **Firebase** | Vendor lock-in, PostgreSQL already in place |
| **GraphQL** | REST is simpler here, no complex nested queries needed |
| **Chakra UI / MUI** | Bundle size, styling conflicts with custom branding |

---
*Stack research: 2026-03-29*
