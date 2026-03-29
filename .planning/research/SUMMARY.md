# Project Research Summary

**Project:** MedIA — Clinic Management SaaS with AI WhatsApp Agent
**Domain:** Healthcare SaaS / Clinic Operations / WhatsApp-first Brazil Market
**Researched:** 2026-03-29
**Confidence:** HIGH

## Executive Summary

MedIA is a multi-tenant clinic management SaaS targeting Brazilian outpatient clinics, differentiated by an AI WhatsApp agent (Sofia/Carla) that handles patient scheduling, follow-ups, and confirmations autonomously. The frontend is a Next.js 15 application with three distinct surfaces: a public landing page, an authenticated operations dashboard, and a real-time WhatsApp conversation panel. The existing FastAPI backend already handles the AI agent pipeline and Evolution API integration — the frontend must bridge that into a usable product for clinic administrators, receptionists, and doctors.

The recommended approach is a phased build starting with foundation and auth, then layering core CRUD operations (patients, appointments, doctors), then the WhatsApp panel with real-time Socket.IO, and finally dashboards and campaigns. This order respects hard data dependencies: nothing works without auth and multi-tenancy, appointments cannot exist without patients and doctors, and the WhatsApp panel's human takeover feature is only valuable once conversations are visible. The stack is opinionated toward minimal bundle size and developer speed: Next.js App Router with shadcn/ui (copy-paste, no heavy dependency), TanStack Query for server state, and NextAuth for credentials-based JWT auth that calls the FastAPI backend.

The single most critical risk is multi-tenancy data leakage — in healthcare, a query that misses a `WHERE tenant_id = ?` filter is a LGPD violation with legal consequences. This must be addressed at Phase 2 through ORM-level enforcement, not per-query discipline. The second major risk is the WhatsApp takeover race condition: AI and human sending simultaneously to a patient creates trust-breaking confusion. Both are preventable with deliberate architecture choices (database-level locks, auto-filter base queries) but require intentional design from day one.

---

## Key Findings

### Recommended Stack

The frontend stack is Next.js 15 (App Router) with React 19 and TypeScript. Tailwind CSS 4 + shadcn/ui handle the design system — shadcn is a copy-paste library, not an npm dependency, which eliminates bundle bloat and gives full branding control. TanStack Query 5 manages all server state with caching and optimistic updates; Zustand 5 handles the small amount of client-only UI state. React Hook Form + Zod cover form validation with TypeScript-native schemas. TanStack Table 8 powers the patient and appointment list views. Authentication runs through NextAuth.js 5 using a CredentialsProvider that delegates to the FastAPI `/auth/login` endpoint — JWT contains `tenant_id` and `role`, enabling stateless multi-tenant sessions.

Real-time messaging uses Socket.IO (client 4.x) with a corresponding python-socketio server mounted on FastAPI. Socket.IO is preferred over native WebSocket for its built-in reconnection, tenant-scoped rooms, and namespace isolation.

**Core technologies:**
- **Next.js 15 (App Router):** SSR/SSG for landing page, API routes as BFF, middleware for auth + tenant routing
- **TypeScript 5:** Type safety at multi-tenant data boundaries — critical for health data correctness
- **Tailwind CSS 4 + shadcn/ui:** Fast iteration, full branding control, no heavy component library
- **TanStack Query 5:** Server state, caching, optimistic updates for dashboard and list views
- **NextAuth.js 5:** Credentials auth delegating to FastAPI JWT — keeps health data self-hosted (LGPD)
- **Socket.IO 4 (client):** Real-time WhatsApp message streaming with auto-reconnect and tenant rooms
- **React Hook Form 7 + Zod 3:** Performant forms with TypeScript-native validation
- **TanStack Table 8:** Headless, sortable, filterable tables for patient/appointment management
- **date-fns 4:** pt-BR locale, timezone-aware date handling for appointment scheduling

See `/Users/mateuspires/Dev/agent-clinic/.planning/research/STACK.md` for full rationale and version list.

### Expected Features

The Brazilian clinic SaaS market has clear table stakes. Competitors (iClinic, Doctor Max, Feegow) cover scheduling + PEP + TISS billing. MedIA's differentiation is NOT those features — it is the AI WhatsApp agent. The MVP should deliver the minimum operational surface that makes the AI agent's output visible and actionable for clinic staff.

**Must have (table stakes):**
- Auth with three roles (Admin, Receptionist, Doctor) + multi-tenant data isolation
- Dashboard with today's appointments, occupancy rate, no-show rate, pending confirmations, active WhatsApp conversations
- Appointment calendar (day/week/month) with create/edit/cancel and status tracking
- Patient list with search, profile page with appointment and conversation history
- Doctor management with availability schedule
- User management (admin creates/deactivates staff accounts)
- WhatsApp conversation inbox with real-time updates and full message history
- Human takeover: disable AI for a conversation, send messages as human, re-enable AI
- Landing page (SSG, SEO, WhatsApp CTA, brand compliance with site.html)

**Should have (competitive differentiators):**
- AI conversation funnel metrics (contacts → scheduled → showed up) on dashboard
- Scheduling conversion rate by source (bot vs human)
- Message templates with variable substitution for receptionists
- Internal notes and conversation tagging in WhatsApp panel
- Patient segmentation (active/inactive/at-risk) for targeted follow-up
- Appointment color-coding by status on calendar
- Automatic confirmation reminder UI controls (backend sends them; surface the toggle)

**Defer to v1.1+:**
- Bulk WhatsApp campaigns (Evolution API broadcast + opt-in compliance + rate limiting)
- Campaign status tracking (sent/delivered/read)
- Conversation auto-summarization with AI
- Waitlist management
- Patient-facing portal
- Electronic Medical Record (PEP), TISS billing, video telemedicine, in-app staff chat

See `/Users/mateuspires/Dev/agent-clinic/.planning/research/FEATURES.md` for full dependency graph and anti-feature rationale.

### Architecture Approach

The system is a Next.js frontend consuming a FastAPI backend over two channels: REST (CRUD operations via TanStack Query) and WebSocket (real-time conversation streaming via Socket.IO). Multi-tenancy is implemented as row-level isolation: every database table carries a `tenant_id` column, the JWT embeds the tenant context, and a FastAPI middleware auto-injects the filter into every query. The frontend route structure uses Next.js route groups — `(landing)`, `(auth)`, and `(dashboard)` — with separate layouts to prevent dashboard JavaScript from loading on the public landing page.

**Major components:**
1. **Landing page (SSG)** — public, zero client JS, SEO-optimized, WhatsApp CTA funnel
2. **Auth layer (NextAuth + FastAPI JWT)** — credentials provider, httpOnly cookie, tenant context embedded in token
3. **REST API client** — centralized fetch wrapper with JWT injection, 401 interceptor for token refresh, TanStack Query cache
4. **Socket.IO context** — singleton connection per authenticated user, auto-joins tenant room, merges real-time messages into TanStack Query cache
5. **Dashboard** — KPI cards + Recharts for occupancy/no-show/funnel metrics; aggregated queries via `/dashboard/metrics`
6. **Agenda (appointment calendar)** — custom ScheduleGrid component, per-doctor filtering, block slots
7. **WhatsApp panel** — ConversationPanel with real-time streaming, human takeover flow with database-level lock, template dispatch
8. **Patient/Doctor/User management** — DataTable (TanStack Table wrapper) pattern, shared form components

See `/Users/mateuspires/Dev/agent-clinic/.planning/research/ARCHITECTURE.md` for route tree and endpoint inventory.

### Critical Pitfalls

1. **Multi-tenancy data leak (CRITICAL)** — Implement at ORM level: SQLAlchemy base query with auto `WHERE tenant_id = :tenant_id` filter. Never accept tenant_id as a URL/body parameter. Write cross-tenant integration tests before shipping any CRUD endpoint.

2. **WhatsApp takeover race condition (HIGH)** — Use a database-level optimistic lock (`UPDATE ... WHERE takeover_by IS NULL`) to claim a conversation atomically. AI agent must check the takeover flag immediately before sending, not before generating. Broadcast takeover state via Socket.IO to all connected users in the tenant room immediately.

3. **WebSocket zombie connections (HIGH)** — Manage a single Socket.IO instance via React context (not per-component). On reconnect, fetch missed messages via REST using the last known message timestamp. Heartbeat every 30 seconds. Clean up event listeners on component unmount.

4. **JWT expiry during long sessions (MEDIUM)** — Short-lived access tokens (15 min) + long-lived refresh tokens (7 days). API client interceptor retries on 401 with refreshed token. Socket.IO reconnects with refreshed token on `connect_error`. Show a toast on refresh, never a hard logout during active work.

5. **Landing page bundle contamination (MEDIUM)** — Route groups enforce separate layouts. Landing page uses Server Components only. Dynamic imports (`next/dynamic`) for any heavy dashboard component. Target 95+ Lighthouse score on landing page before launch.

6. **LGPD / health data exposure (HIGH)** — Never log patient PII. Sanitize error messages before sending to frontend. Implement data retention policy (auto-archive old conversations). Consent tracking on patient registration. SSL everywhere. Document data processing purposes.

See `/Users/mateuspires/Dev/agent-clinic/.planning/research/PITFALLS.md` for full prevention strategies.

---

## Implications for Roadmap

Based on research, the feature dependency graph and architectural constraints drive a clear 6-phase order. The rule is: nothing is buildable without its dependency, so each phase unlocks the next.

### Phase 1: Foundation
**Rationale:** No code is useful until the design system and project structure exist. Landing page can deploy immediately, generating revenue conversation before the app is complete.
**Delivers:** Next.js project with Tailwind + shadcn/ui configured, brand tokens from site.html, deployed landing page with WhatsApp CTA.
**Addresses:** Landing page (table stakes), design system coherence.
**Avoids:** Landing page bundle contamination pitfall — route groups established at project init, not retrofitted.

### Phase 2: Auth + Multi-Tenancy
**Rationale:** Every single subsequent feature is gated behind auth. Multi-tenancy must be implemented before any real data is inserted — retrofitting tenant_id into populated tables is error-prone and risky.
**Delivers:** FastAPI auth endpoints (login/register/refresh/me), NextAuth integration, JWT with tenant_id + role, protected route layout with sidebar, login page.
**Uses:** NextAuth.js 5, JWT, FastAPI middleware.
**Avoids:** Multi-tenancy data leak pitfall (ORM-level filter established here), JWT expiry pitfall (refresh token flow built in from day one), LGPD pitfall (no PII in logs from start).

### Phase 3: Core CRUD Operations
**Rationale:** Appointment management is the primary daily workflow for receptionists, but appointments reference both patients and doctors — both must exist first. This phase ships the core operations surface.
**Delivers:** Patient list + profile page, doctor management with availability, appointment calendar (create/edit/cancel/status), user management (admin).
**Uses:** TanStack Query, TanStack Table, React Hook Form + Zod, date-fns (pt-BR), ScheduleGrid component.
**Implements:** REST API client, DataTable pattern, shared form components.
**Avoids:** Dashboard performance pitfall — pagination and indexes on (tenant_id, created_at) implemented from the first CRUD endpoint.

### Phase 4: WhatsApp Panel + Real-Time
**Rationale:** The AI agent is already running in production. The WhatsApp panel is what makes it visible and controllable. Human takeover must ship alongside the inbox — the inbox without takeover is dangerous (no safety valve).
**Delivers:** Socket.IO server on FastAPI, conversation inbox with real-time updates, conversation detail with full message history, human takeover flow, "return to AI" flow.
**Uses:** Socket.IO (client + python-socketio), TanStack Query cache merge, ConversationPanel component.
**Avoids:** Takeover race condition pitfall (database-level lock), WebSocket zombie connection pitfall (singleton Socket.IO context, reconnect + REST catch-up), message deduplication (UUID-based dedup in cache merge).

### Phase 5: Dashboard + Campaigns
**Rationale:** Dashboard metrics require both appointment data (Phase 3) and conversation data (Phase 4) to be meaningful. Campaigns require templates first, then broadcast infrastructure.
**Delivers:** Dashboard with KPI cards and charts (occupancy, no-show, confirmation rate, AI funnel), Recharts visualizations, message templates with variable substitution, campaign dispatch.
**Uses:** Recharts 2, `/dashboard/metrics` aggregated endpoint, Evolution API campaign send.
**Avoids:** Dashboard performance pitfall — pre-computed aggregates (materialized views or cron), not live queries.

### Phase 6: Polish + Hardening
**Rationale:** Before launch, the full application needs production-quality error handling, responsive design verification, and LGPD documentation.
**Delivers:** Responsive design for all views, error boundaries and loading states, clinic settings page, LGPD consent tracking, data retention policy implementation, end-to-end testing of cross-tenant isolation.
**Avoids:** All remaining pitfalls that need application-wide treatment (Evolution API error handling, performance at scale, LGPD audit trail).

### Phase Ordering Rationale

- Auth before everything: feature dependency graph from FEATURES.md has auth as the root node for all other features.
- Patients + Doctors before Appointments: foreign key dependencies enforce this; inserting appointments without patient_id and doctor_id is impossible.
- WhatsApp Inbox before Dashboard: dashboard WhatsApp metrics (active conversations, conversion funnel) require real conversation data flowing through the panel.
- Campaigns after Templates: bulk campaigns are a superset of templates; templates are also lower compliance risk and faster to build.
- Multi-tenancy at Phase 2 not retrofitted: PITFALLS.md is unambiguous — adding tenant_id to populated tables later is a data migration risk with LGPD implications.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (WhatsApp Panel):** Socket.IO integration between Next.js and python-socketio has specific ASGI mounting nuances. Takeover state machine should be designed carefully — recommend dedicated research-phase for this phase.
- **Phase 5 (Campaigns):** WhatsApp Business API rate limits and opt-in compliance rules (Meta policy + LGPD overlap) need validation before building campaign dispatch. Recommend research-phase before implementation.
- **Phase 2 (Auth + Multi-tenancy):** NextAuth 5 + FastAPI CredentialsProvider integration pattern is newer — verify correct cookie/session configuration for App Router before building.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Next.js + Tailwind + shadcn/ui setup is thoroughly documented with official guides.
- **Phase 3 (Core CRUD):** TanStack Query + REST CRUD is extremely well-documented; standard patterns apply.
- **Phase 6 (Polish):** Responsive Tailwind, error boundaries, and loading states are standard Next.js patterns.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies are industry-standard with strong official documentation. Versions verified. No experimental choices. |
| Features | HIGH | Brazilian market analysis + international clinic SaaS patterns corroborate the feature set. The AI WhatsApp differentiation angle is strongly validated by market data. |
| Architecture | HIGH | Multi-tenant row-level isolation, NextAuth + FastAPI JWT, and Socket.IO patterns are well-established. Route group strategy is Next.js official recommendation. |
| Pitfalls | HIGH | Pitfalls are derived from known failure modes in multi-tenant SaaS, healthcare data, and real-time messaging — not speculative. |

**Overall confidence:** HIGH

### Gaps to Address

- **Evolution API version compatibility:** The python-socketio and python-evolution-api versions used in the existing backend need to be pinned and verified compatible with the Socket.IO client 4.x on the frontend. Check before Phase 4.
- **Framer Motion vs CSS animations:** STACK.md flags Framer Motion as LOW confidence (may be unnecessary). Decide before Phase 1 whether to include it or use Tailwind CSS animations for the landing page transitions.
- **Dashboard aggregation strategy:** Pre-computed aggregates (materialized views) vs cron-job summaries need a decision before Phase 5. Materialized views are simpler but require PostgreSQL-specific DDL; cron jobs are more portable. Validate with backend team.
- **Tenant onboarding flow:** ARCHITECTURE.md describes tenant creation via "internal tool" — this is not built in the frontend scope. Clarify whether the admin panel needs a self-serve signup or if onboarding stays manual for v1.
- **LGPD formal compliance scope:** Research notes the need to "document data processing purposes" but stops short of specifying the full DPA (Data Processing Agreement) requirements. Legal review recommended before launch.

---

## Sources

### Primary (HIGH confidence)
- [Apolo Blog — 9 Indicadores Essenciais para Clinicas 2025](https://blog.apolo.app/9-indicadores-essenciais-para-clinicas-em-2025/) — Brazilian clinic KPIs
- [AiSensy — WhatsApp Team Inbox Guide 2026](https://m.aisensy.com/blog/whatsapp-team-inbox/) — shared inbox feature patterns and human takeover flows
- [Respond.io — WhatsApp AI Agent Overview 2026](https://respond.io/blog/whatsapp-ai-agent) — AI handoff patterns

### Secondary (MEDIUM confidence)
- [Cloudia.com.br — 15 melhores softwares medicos do Brasil](https://www.cloudia.com.br/8-melhores-softwares-medicos-do-mercado-2024/) — Brazilian competitor feature landscape
- [Jestor Blog — Melhores Softwares de Gestao para Clinicas 2026](https://blog.jestor.com/melhores-softwares-de-gestao-para-clinicas-e-consultorios-em-2026/) — market sizing and pricing data
- [AVI MedTech — Clinic Management Software 2026 Must-Have Features](https://avimedtech.com/clinic-management-software-in-2026-what-it-is-and-key-features-clinics-must-have/) — international SaaS feature baseline
- [Gallabox — WhatsApp for Healthcare Complete Guide](https://gallabox.com/blog/whatsapp-for-healthcare) — WhatsApp healthcare communication patterns
- [AiSensy — WhatsApp Templates for Healthcare](https://m.aisensy.com/whatsapp-marketing-template-for-healthcare/) — template and campaign patterns

---
*Research completed: 2026-03-29*
*Ready for roadmap: yes*
