# Roadmap: MedIA

## Overview

MedIA is built in six phases that respect hard data dependencies. Foundation and landing page ship first (immediate value). Auth and multi-tenancy come second — nothing works without them and tenant isolation cannot be retrofitted safely. Core CRUD (patients, doctors, appointments, users) comes third because appointments require both patients and doctors. The WhatsApp panel ships fourth, making the existing AI agent visible and controllable for the first time. Dashboard and campaigns come fifth because metrics require both CRUD and conversation data to be meaningful. Polish and hardening close the milestone, ensuring the product is production-ready for launch.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Next.js project, design system, and public landing page (completed 2026-03-29)
- [x] **Phase 2: Auth + Multi-Tenancy** - Login, JWT, roles, tenant isolation, backend API layer (completed 2026-03-30)
- [x] **Phase 3: Core CRUD** - Patients, doctors, appointments, and user management (completed 2026-03-30)
- [x] **Phase 4: WhatsApp Panel** - Real-time inbox, conversation history, and human takeover (completed 2026-03-30)
- [ ] **Phase 5: Dashboard + Campaigns** - KPI metrics, charts, message templates, and bulk campaigns
- [ ] **Phase 6: Polish + Hardening** - Responsive verification, error boundaries, LGPD, and integration testing

## Phase Details

### Phase 1: Foundation
**Goal**: The project scaffolding exists and the public landing page is live and capturing leads
**Depends on**: Nothing (first phase)
**Requirements**: LAND-01, LAND-02, LAND-03, LAND-04
**Success Criteria** (what must be TRUE):
  1. Visiting the root URL shows a hero section with a CTA button that opens a WhatsApp conversation
  2. The landing page displays features, how-it-works, and testimonial sections matching site.html structure
  3. The landing page renders correctly on a mobile device (375px width) with no horizontal overflow
  4. The visual identity matches site.html: green palette, DM Serif Display headings, DM Sans body text, rounded borders
  5. Next.js project runs locally with Tailwind CSS 4, shadcn/ui configured, and route groups (landing/auth/dashboard) separated
**Plans**: 3 plans
Plans:
- [x] 01-01-PLAN.md — Scaffold Next.js project, Tailwind 4 design tokens, shadcn init, route groups
- [x] 01-02-PLAN.md — Build all 8 landing page section components with WhatsApp CTAs
- [x] 01-03-PLAN.md — Responsive audit at 900px breakpoint and visual verification
**UI hint**: yes

### Phase 2: Auth + Multi-Tenancy
**Goal**: Users can securely log in with role-based access and every data operation is automatically scoped to the correct clinic
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, TENANT-01, TENANT-02, TENANT-03, API-02, API-03
**Success Criteria** (what must be TRUE):
  1. User can log in with email and password and remain logged in after a browser refresh
  2. User can log out from any page and is immediately redirected to the login screen
  3. Visiting a protected route while unauthenticated redirects to the login page
  4. An Admin user sees admin-only controls that are not visible to a Recepcionista or Medico user
  5. A Medico user cannot see or access data from a different clinic even if they modify the JWT manually
**Plans**: 4 plans
Plans:
- [x] 02-00-PLAN.md — Wave 0: pytest config + test stubs for auth, RBAC, and tenant isolation
- [x] 02-01-PLAN.md — Alembic init + migrations: tenants, users, tenant_id columns, RLS policies
- [x] 02-02-PLAN.md — FastAPI auth endpoints (login, refresh, me) + deps (tenant, role) + CORS
- [x] 02-03-PLAN.md — NextAuth v5 + login page + proxy.ts route protection + dashboard shell with RBAC
**UI hint**: yes

### Phase 3: Core CRUD
**Goal**: Receptionists and admins can fully manage patients, doctors, appointments, and system users through the web interface
**Depends on**: Phase 2
**Requirements**: AGENDA-01, AGENDA-02, AGENDA-03, AGENDA-04, AGENDA-05, AGENDA-06, AGENDA-07, PAT-01, PAT-02, PAT-03, PAT-04, PAT-05, DOC-01, DOC-02, DOC-03, USER-01, USER-02, USER-03, USER-04, USER-05, API-01
**Success Criteria** (what must be TRUE):
  1. Recepcionista can search for a patient by name or phone and open their profile showing appointment and WhatsApp conversation history
  2. Recepcionista can create, edit, and cancel an appointment from the visual calendar and see its status change (Agendado, Confirmado, Realizado, Cancelado)
  3. Admin can create a doctor profile with specialty, CRM, and weekly availability grid
  4. Medico logs in and sees only their own appointment calendar, not other doctors' schedules
  5. Admin can create, deactivate, and change the role of a system user
**Plans**: 7 plans
Plans:
- [x] 03-01-PLAN.md — Migration 004, frontend deps, shared types, API wrapper, reusable components (DataTable, SlideOver, StatusBadge)
- [x] 03-02-PLAN.md — FastAPI patients + appointments routers with pagination, search, and medico isolation
- [x] 03-03-PLAN.md — FastAPI doctors + users routers with schedules, role management, and password reset
- [x] 03-04-PLAN.md — Custom calendar page (Day/Week/Month) with appointment CRUD slide-over
- [x] 03-05-PLAN.md — Patient list page with search + patient profile with appointment/WhatsApp tabs
- [x] 03-06-PLAN.md — Doctor management with availability grid + user management with role/status controls
- [x] 03-07-PLAN.md — Build verification + end-to-end visual walkthrough checkpoint
**UI hint**: yes

### Phase 4: WhatsApp Panel
**Goal**: Receptionists can monitor all active WhatsApp conversations in real time and take over from the AI agent when needed
**Depends on**: Phase 3
**Requirements**: WPP-01, WPP-02, WPP-03, WPP-04, WPP-05, WPP-06, WPP-07, WPP-08, WPP-09, WPP-10, WPP-11, API-04
**Success Criteria** (what must be TRUE):
  1. Recepcionista sees the list of WhatsApp conversations update in real time as new messages arrive, without refreshing the page
  2. Opening a conversation shows the full message history and a sidebar with the patient's information
  3. Each conversation shows a visible status indicator: IA ativa, Atendimento humano, or Resolvida
  4. Recepcionista clicks "Assumir" and can send messages as a human; the AI stops responding immediately and all other logged-in users see the takeover indicator
  5. Recepcionista clicks "Devolver para IA" and the AI agent resumes responding to that conversation
**Plans**: 3 plans
Plans:
- [x] 04-01-PLAN.md — Socket.IO server + conversations REST router + takeover mechanism + webhook bypass
- [x] 04-02-PLAN.md — Frontend Socket.IO client + 3-column inbox layout + real-time conversation UI
- [x] 04-03-PLAN.md — Build verification + visual walkthrough checkpoint
**UI hint**: yes

### Phase 5: Dashboard + Campaigns
**Goal**: Admins and receptionists have operational visibility through a metrics dashboard, and admins can send message templates and bulk campaigns via WhatsApp
**Depends on**: Phase 4
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, WPP-12, WPP-13, WPP-14, WPP-15, WPP-16
**Success Criteria** (what must be TRUE):
  1. Admin/Recepcionista opens the dashboard and sees today's KPIs: consultas hoje, taxa de ocupacao, no-shows, confirmacoes pendentes, and active WhatsApp conversations
  2. Admin sees weekly trend charts and specialty breakdown charts rendered with real data
  3. Admin can create a message template with named variables (e.g., {{nome}}, {{data}}) and preview the substituted output
  4. Admin selects a patient segment and a template, dispatches a campaign, and sees per-recipient delivery status (enviado/entregue/lido/falha)
**Plans**: 5 plans
Plans:
- [ ] 05-01-PLAN.md — Migration 005 + dashboard/templates/campaigns backend routers + test stubs
- [ ] 05-02-PLAN.md — Install recharts + dashboard /home page rewrite + KPI cards + charts + sidebar nav
- [ ] 05-03-PLAN.md — Templates page with CRUD, slide-over form, and live preview
- [ ] 05-04-PLAN.md — Campaigns list page, step wizard, detail page, and QuickSend in inbox
- [ ] 05-05-PLAN.md — Build verification + visual walkthrough checkpoint
**UI hint**: yes

### Phase 6: Polish + Hardening
**Goal**: The full application is production-ready: responsive on all devices, resilient to errors, and compliant with LGPD data handling requirements
**Depends on**: Phase 5
**Requirements**: None (cross-cutting quality layer across all prior phases)
**Success Criteria** (what must be TRUE):
  1. Every page in the dashboard renders correctly and is usable on a tablet (768px) and a mobile device (375px)
  2. Network errors and API failures show user-friendly error states (not blank screens or console errors leaking to UI)
  3. Cross-tenant isolation passes integration tests: no query in the system returns data from a different tenant_id
  4. Loading states appear for all async operations (table loads, form submissions, real-time connection establishment)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete   | 2026-03-29 |
| 2. Auth + Multi-Tenancy | 4/4 | Complete   | 2026-03-30 |
| 3. Core CRUD | 7/7 | Complete   | 2026-03-30 |
| 4. WhatsApp Panel | 3/3 | Complete   | 2026-03-30 |
| 5. Dashboard + Campaigns | 0/5 | Not started | - |
| 6. Polish + Hardening | 0/TBD | Not started | - |
