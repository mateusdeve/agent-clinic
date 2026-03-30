# Phase 5: Dashboard + Campaigns - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Operational metrics dashboard for admins and receptionists, plus WhatsApp message templates and bulk campaign system for admins. Dashboard shows today's KPIs, upcoming appointments, and weekly trend charts. Campaigns allow creating templates with variables, selecting patient segments, and dispatching bulk messages with delivery tracking.

</domain>

<decisions>
## Implementation Decisions

### Dashboard Layout and KPIs
- **D-01:** Top row of 5 KPI cards (consultas hoje, taxa de ocupacao, no-shows, confirmacoes pendentes, conversas WhatsApp ativas) followed by a "Proximas Consultas Hoje" table below, then charts section at bottom.
- **D-02:** Dashboard replaces the current `/home` placeholder page. No separate `/dashboard` route — `/home` IS the dashboard.
- **D-03:** KPI values fetch once on page load. No auto-refresh or Socket.IO — user refreshes the page to update.
- **D-04:** Role-based views: Admin sees everything (KPIs + consultas + charts + campaigns link). Recepcionista sees KPIs + consultas list (no charts). Medico is redirected to `/agenda` (their own schedule).

### Charts and Data Visualization
- **D-05:** Recharts library for all charts. React-native, Tailwind-friendly, declarative API.
- **D-06:** Two charts for DASH-04: Line chart showing 7-day trends (consultas, no-shows) and Bar chart showing consultas by specialty. Admin-only section.
- **D-07:** Charts appear below the "Proximas Consultas" table. Operational data first, analytics second.

### Template Editor
- **D-08:** Slide-over form with live preview (consistent with Phase 3 D-06 pattern). Left: template name + textarea with `{{variavel}}` placeholders. Below: live preview with sample data substituted.
- **D-09:** Fixed set of template variables: `{{nome}}`, `{{telefone}}`, `{{data}}`, `{{hora}}`, `{{medico}}`, `{{especialidade}}`. Covers confirmation, reminder, and follow-up use cases.
- **D-10:** Templates live on a new `/templates` page with dedicated sidebar item. Table with name, preview snippet, variable count, last used. Slide-over for create/edit.

### Campaign Dispatch
- **D-11:** New `/campanhas` page with dedicated sidebar item. Table of campaigns with status (rascunho/enviando/concluida/falha), recipient count, delivery stats.
- **D-12:** Campaign creation uses a step wizard: 1) Pick template, 2) Build segment with filter criteria, 3) Preview with sample recipients, 4) Confirm and send.
- **D-13:** Patient segment selection via filter builder with predefined criteria: especialidade dropdown, ultimo agendamento range (< 30d, 30-90d, > 90d), status (ativo/inativo). Shows matching patient count live.
- **D-14:** Backend queue with 20 msg/sec throttle for campaign sending. APScheduler (already in stack) processes the queue. Status updates per recipient stored in DB, refreshed via page polling.
- **D-15:** Campaign detail page shows: summary stats bar (enviado/entregue/lido/falha counts) + recipient table with per-row status badges and timestamps.
- **D-16:** Campaigns are Admin-only. Recepcionista can use quick-send (WPP-13): send a single template message to one patient from the inbox.

### Claude's Discretion
- KPI card visual design (icons, colors, hover states)
- Exact chart styling and colors (follow green palette)
- Template variable insertion UX (click to insert vs manual typing)
- Campaign wizard step navigation design
- Quick-send UX for Recepcionista in WhatsApp inbox
- Sidebar ordering for new items (Templates, Campanhas)
- Empty states for new features
- Campaign recipient table pagination
- Filter builder dropdown styling

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Dashboard requirements
- `.planning/REQUIREMENTS.md` §Dashboard — DASH-01 through DASH-04 acceptance criteria
- `.planning/REQUIREMENTS.md` §WhatsApp — WPP-12 through WPP-16 campaign requirements

### Prior phase patterns
- `.planning/phases/03-core-crud/03-CONTEXT.md` — D-05 (DataTable), D-06 (slide-over), D-07 (pagination), D-08 (form validation), D-11..D-14 (API design)
- `.planning/phases/04-whatsapp-panel/04-CONTEXT.md` — D-01..D-03 (Socket.IO), D-12 (Evolution API send flow)

### Existing code
- `frontend/src/app/(dashboard)/home/page.tsx` — Current placeholder, to be replaced with dashboard
- `frontend/src/app/(dashboard)/layout.tsx` — Dashboard shell with sidebar (add new items)
- `agent-service/src/api/conversations.py` — Pattern for new REST routers
- `agent-service/src/api/orchestrator.py` — APScheduler already integrated here

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `shadcn/ui Table + @tanstack/react-table` — established in Phase 3 for all entity tables; reuse for templates, campaigns, and recipients tables
- `SlideOver component` — Phase 3 pattern for create/edit forms; reuse for template editor
- `StatusBadge component` — Phase 3 status badges; reuse for campaign delivery statuses
- `apiFetch wrapper` — Phase 3 API call pattern with auth headers
- `react-hook-form + zod` — Form validation pattern from Phase 2/3; reuse for template forms and campaign wizard

### Established Patterns
- REST routers with `get_current_user` + `get_db_for_tenant` deps (Phase 2/3)
- Pagination envelope: `{ items, total, page, per_page }` (Phase 3)
- Role-based component rendering with `session?.user?.role` checks (Phase 2/3)
- Sidebar navigation in dashboard layout (add new items for Templates, Campanhas)

### Integration Points
- `/home` page.tsx — replace placeholder with real dashboard
- Dashboard layout sidebar — add Templates and Campanhas nav items
- APScheduler in orchestrator.py — add campaign dispatch job
- Evolution API client — reuse for campaign message sending
- Conversations table — source for active WhatsApp conversation count KPI

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-dashboard-campaigns*
*Context gathered: 2026-03-30*
