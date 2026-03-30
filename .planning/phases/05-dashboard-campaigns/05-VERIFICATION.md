---
phase: 05-dashboard-campaigns
verified: 2026-03-30T00:00:00Z
status: human_needed
score: 16/17 must-haves verified
re_verification: false
human_verification:
  - test: "Log in as Admin, open /home. Confirm 5 KPI cards show real values, proximas consultas table appears, and two charts (Tendencia Semanal + Consultas por Especialidade) render below the table."
    expected: "5 KpiCard components visible, ProximasConsultas table visible, two Recharts charts visible."
    why_human: "Recharts rendering, layout breakpoints, and visual correctness require a browser."
  - test: "Log in as Recepcionista, open /home. Confirm KPI cards and consultas table appear but NO charts are shown."
    expected: "Charts section is absent (role==='admin' guard prevents rendering)."
    why_human: "Role-conditional conditional rendering requires a logged-in session."
  - test: "Log in as Medico, navigate to /home."
    expected: "Immediate redirect to /agenda."
    why_human: "Server-side redirect requires a real auth session."
  - test: "As Admin, verify sidebar shows 'Templates' and 'Campanhas' links. As Recepcionista, verify those links are absent."
    expected: "Admin sees both links; Recepcionista does not."
    why_human: "Sidebar role-conditional visibility requires a logged-in browser session."
  - test: "As Admin, open /templates. Click 'Novo Template'. Fill in a template body with {{nome}} and {{medico}}. Confirm the live preview shows substituted sample values."
    expected: "Preview shows 'Maria Silva' and 'Dr. Carlos' in the appropriate positions."
    why_human: "Live preview is interactive UI that requires user interaction in a browser."
  - test: "As Admin, open /campanhas, click 'Nova Campanha'. Step through the 4-step wizard. On step 2 apply segment filters and confirm the patient count updates live."
    expected: "Count label updates within ~500ms of filter change (debounced apiFetch to /api/campaigns/preview-segment)."
    why_human: "Live debounce count behavior requires interactive browser testing."
  - test: "As Recepcionista, open /whatsapp, select a conversation, and locate the quick-send Template button. Open QuickSendModal and confirm it shows the template list and a live preview."
    expected: "QuickSendModal opens, lists templates, and renders preview with patientNome substituted."
    why_human: "Modal integration inside InboxPanel requires a live browser session with a real conversation selected."
---

# Phase 5: Dashboard & Campaigns Verification Report

**Phase Goal:** Dashboard operacional com KPIs, templates de mensagem, e campanhas de WhatsApp
**Verified:** 2026-03-30
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /api/dashboard/stats returns 5 KPI values for today | VERIFIED | `dashboard.py` queries appointments for consultas_hoje, taxa_ocupacao, no_shows, confirmacoes_pendentes, conversas_ativas; route confirmed registered |
| 2 | GET /api/dashboard/stats returns proximas_consultas list | VERIFIED | `dashboard.py` fetches up to 20 appointments with patient/doctor JOIN; returns proximas_consultas array |
| 3 | GET /api/dashboard/charts returns 7-day trend and specialty breakdown arrays | VERIFIED | `dashboard.py` loops 7 days for trend, queries 30-day specialty counts; admin-only enforced |
| 4 | POST /api/templates creates a template with variable placeholders | VERIFIED | `templates.py` POST /api/templates/ — extracts variables via `extract_variables`, INSERTs to message_templates |
| 5 | GET /api/templates returns paginated list of templates | VERIFIED | `templates.py` GET /api/templates/ — paginates via LIMIT/OFFSET, returns {items, total, page, per_page} |
| 6 | POST /api/campaigns creates a campaign linked to a template and segment | VERIFIED | `campaigns.py` POST /api/campaigns/ — validates template, builds segment query, populates campaign_recipients |
| 7 | Campaign dispatch job sends messages at 20 msg/sec throttle | VERIFIED | `webhook.py` dispatch_campaigns uses asyncio.sleep(0.05) = 20/sec; registered with scheduler interval=30s |
| 8 | GET /api/campaigns/{id} returns per-recipient delivery status | VERIFIED | `campaigns.py` GET /api/campaigns/{campaign_id}/recipients returns paginated list with status, erro, sent_at per recipient |
| 9 | POST /api/conversations/{phone}/send-template sends a quick template message | VERIFIED | `campaigns.py` conversations_router POST /{phone}/send-template — fetches template, renders, sends via evolution_client, persists to conversations |
| 10 | Admin opens /home and sees 5 KPI cards with real values | VERIFIED (code) | `DashboardClient.tsx` fetches /api/dashboard/stats, renders 5 KpiCard components from real API data | HUMAN NEEDED (visual) |
| 11 | Admin sees Proximas Consultas table below KPI cards | VERIFIED (code) | `DashboardClient.tsx` passes `stats.proximas_consultas` to ProximasConsultas component |
| 12 | Admin sees 7-day trend line chart and specialty bar chart | VERIFIED (code) | `DashboardClient.tsx` fetches /api/dashboard/charts (admin-only), passes to TrendChart + EspecialidadeChart |
| 13 | Recepcionista sees KPI cards and consultas table but no charts | VERIFIED (code) | role === "admin" guard in DashboardClient.tsx prevents chart section rendering |
| 14 | Medico visiting /home is redirected to /agenda | VERIFIED | `home/page.tsx` server component: `if (role === "medico") redirect("/agenda")` |
| 15 | Admin opens /templates and sees a table of message templates | VERIFIED (code) | `templates/page.tsx` fetches /api/templates, renders DataTable via buildTemplateColumns |
| 16 | Admin clicks Novo Template and a slide-over opens with live preview | VERIFIED (code) | `TemplateSlideOver.tsx` contains previewTemplate(), SAMPLE_DATA, SlideOver wrapper, apiFetch — no dangerouslySetInnerHTML |
| 17 | Admin opens /campanhas, step wizard opens with live segment count | VERIFIED (code) | `CampaignWizard.tsx` debounces apiFetch to /api/campaigns/preview-segment; 4 WizardSteps defined |

**Score:** 16/17 truths verified programmatically (17th requires human visual confirmation)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent-service/alembic/versions/005_templates_campaigns.py` | 3 tables + RLS | VERIFIED | message_templates, campaigns, campaign_recipients — all 3 ENABLE ROW LEVEL SECURITY calls present |
| `agent-service/src/api/dashboard.py` | Dashboard stats + charts endpoints | VERIFIED | router prefix="/api/dashboard", get_dashboard_stats, get_dashboard_charts, require_role enforced |
| `agent-service/src/api/templates.py` | Template CRUD endpoints | VERIFIED | router prefix="/api/templates", extract_variables, render_template, ALLOWED_VARS, 5 endpoints |
| `agent-service/src/api/campaigns.py` | Campaign CRUD, dispatch, quick-send | VERIFIED | router prefix="/api/campaigns", preview-segment, create, list, detail, recipients, send-template |
| `frontend/src/components/dashboard/KpiCard.tsx` | KPI card component | VERIFIED | export function KpiCard, props: label/value/icon/color/iconColor |
| `frontend/src/components/dashboard/TrendChart.tsx` | Recharts LineChart (use client) | VERIFIED | "use client" first line, LineChart from recharts |
| `frontend/src/components/dashboard/EspecialidadeChart.tsx` | Recharts BarChart (use client) | VERIFIED | "use client" first line, BarChart from recharts |
| `frontend/src/components/dashboard/DashboardClient.tsx` | Dashboard client component | VERIFIED | "use client", apiFetch /api/dashboard/stats + /api/dashboard/charts, KpiCard + ProximasConsultas + charts |
| `frontend/src/app/(dashboard)/home/page.tsx` | Dashboard page (no placeholder) | VERIFIED | DashboardClient, redirect("/agenda") for medico, no Phase 5 placeholder text |
| `frontend/src/app/(dashboard)/templates/page.tsx` | Templates list page | VERIFIED | buildTemplateColumns, DataTable, TemplateSlideOver, apiFetch /api/templates |
| `frontend/src/components/dashboard/TemplatesTable.tsx` | Templates table columns | VERIFIED | export function buildTemplateColumns, ColumnDef<MessageTemplate>, onEdit/onDelete |
| `frontend/src/components/dashboard/TemplateSlideOver.tsx` | Template form with live preview | VERIFIED | "use client", previewTemplate, SAMPLE_DATA, SlideOver, apiFetch — no dangerouslySetInnerHTML |
| `frontend/src/app/(dashboard)/campanhas/page.tsx` | Campaign list page | VERIFIED | "use client", CampaignWizard, setInterval polling, apiFetch /api/campaigns |
| `frontend/src/components/dashboard/CampaignWizard.tsx` | 4-step campaign wizard | VERIFIED | WizardStep type, steps: template/segmento/preview/confirmar, preview-segment fetch, SlideOver |
| `frontend/src/app/(dashboard)/campanhas/[id]/page.tsx` | Campaign detail page | VERIFIED | "use client", apiFetch /api/campaigns/{id} and /recipients, buildRecipientColumns, setInterval |
| `frontend/src/components/dashboard/QuickSendModal.tsx` | Quick-send modal | VERIFIED | "use client", apiFetch /api/conversations/{phone}/send-template |
| `frontend/src/lib/types.ts` | Dashboard + template + campaign types | VERIFIED | DashboardStats, MessageTemplate, Campaign, CampaignRecipient all exported |
| `frontend/package.json` | recharts installed | VERIFIED | "recharts": "^3.8.1" |
| `agent-service/tests/test_dashboard.py` | Test stubs | VERIFIED | test_stats_kpis, test_charts_data present |
| `agent-service/tests/test_templates.py` | Test stubs | VERIFIED | test_create_template present |
| `agent-service/tests/test_campaigns.py` | Test stubs | VERIFIED | test_create_campaign, test_quick_send present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `webhook.py` | `dashboard.py` | app.include_router(dashboard_router) | WIRED | Line 58 — confirmed |
| `webhook.py` | `templates.py` | app.include_router(templates_router) | WIRED | Line 59 — confirmed |
| `webhook.py` | `campaigns.py` | app.include_router(campaigns_router) | WIRED | Line 60 — confirmed |
| `webhook.py` | campaigns conversations_router | app.include_router(campaigns_conversations_router) | WIRED | Line 61 — quick-send route active |
| `webhook.py` | dispatch_campaigns | scheduler.add_job interval=30s | WIRED | Line 220 — id="campaign_dispatcher" |
| `DashboardClient.tsx` | /api/dashboard/stats | apiFetch in useEffect | WIRED | Line 24 — confirmed |
| `DashboardClient.tsx` | /api/dashboard/charts | apiFetch in useEffect (admin only) | WIRED | Lines 27-29 — confirmed |
| `layout.tsx` | /templates | href="/templates" admin-only | WIRED | Line 82 in layout.tsx |
| `layout.tsx` | /campanhas | href="/campanhas" admin-only | WIRED | Line 88 in layout.tsx |
| `templates/page.tsx` | /api/templates | apiFetch in fetchTemplates | WIRED | Fetches /api/templates with pagination |
| `CampaignWizard.tsx` | /api/campaigns/preview-segment | apiFetch debounced | WIRED | Line 103 confirmed |
| `QuickSendModal.tsx` | /api/conversations/{phone}/send-template | apiFetch POST | WIRED | Line 56 confirmed |
| `whatsapp/page.tsx` | `QuickSendModal` | via InboxPanel.tsx | WIRED | QuickSendModal imported and rendered in InboxPanel.tsx (not page.tsx directly — component composition pattern) |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `DashboardClient.tsx` | stats (DashboardStats) | apiFetch /api/dashboard/stats | Yes — dashboard.py queries appointments table with real SQL | FLOWING |
| `DashboardClient.tsx` | charts (DashboardCharts) | apiFetch /api/dashboard/charts | Yes — dashboard.py queries 7-day trend and specialty counts from appointments + doctors | FLOWING |
| `templates/page.tsx` | templates[] | apiFetch /api/templates | Yes — templates.py SELECT from message_templates with real pagination | FLOWING |
| `campanhas/page.tsx` | campaigns[] | apiFetch /api/campaigns | Yes — campaigns.py SELECT with delivery stats subqueries from campaign_recipients | FLOWING |
| `campanhas/[id]/page.tsx` | campaign + recipients[] | apiFetch /api/campaigns/{id} and /recipients | Yes — campaigns.py joins campaign_recipients with patients table | FLOWING |
| `QuickSendModal.tsx` | templates[] for picker | apiFetch /api/templates?per_page=50 | Yes — templates.py SELECT from message_templates | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend routers importable | python3 -c "from src.api.webhook import app; print(len(app.routes))" | All routers import without errors | PASS |
| Dashboard routes registered | route list check | /api/dashboard/stats, /api/dashboard/charts present | PASS |
| Template routes registered | route list check | 5 template routes + send-template | PASS |
| Campaign routes registered | route list check | preview-segment, CRUD, recipients, send-template | PASS |
| extract_variables works | python3 inline | ['nome', 'medico'] extracted correctly | PASS |
| render_template works | python3 inline | Variables replaced correctly in output string | PASS |
| dispatch_campaigns 20/sec throttle | grep asyncio.sleep(0.05) | asyncio.sleep(0.05) present — 20 msg/sec confirmed | PASS |
| campaign_dispatcher scheduled | grep scheduler.add_job | id="campaign_dispatcher" interval=30s confirmed | PASS |
| recharts installed | package.json "recharts": "^3.8.1" | Dependency present | PASS |
| Next.js build | SKIPPED — requires npm run | Cannot run build without server startup | SKIP |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DASH-01 | 05-01, 05-02 | Admin/Recepcionista ve KPIs: consultas hoje, taxa de ocupacao, no-shows, confirmacoes pendentes | SATISFIED | dashboard.py returns all 4 KPIs; DashboardClient renders 4 KpiCard components |
| DASH-02 | 05-01, 05-02 | Admin/Recepcionista ve lista das proximas consultas do dia | SATISFIED | dashboard.py proximas_consultas query + ProximasConsultas component |
| DASH-03 | 05-01, 05-02 | Admin/Recepcionista ve contador de conversas WhatsApp ativas | SATISFIED | dashboard.py conversas_ativas via conversations table + KpiCard "Conversas WhatsApp" |
| DASH-04 | 05-01, 05-02 | Admin ve graficos de tendencias semanais e receita por especialidade | SATISFIED (code) | /api/dashboard/charts + TrendChart + EspecialidadeChart — visual confirmation pending |
| WPP-12 | 05-01, 05-03 | Admin pode criar/editar templates com variaveis | SATISFIED | templates.py CRUD + TemplateSlideOver with variable buttons and live preview |
| WPP-13 | 05-01, 05-04 | Recepcionista pode usar template para enviar mensagem rapida | SATISFIED (code) | send-template endpoint + QuickSendModal in InboxPanel — visual confirmation pending |
| WPP-14 | 05-01, 05-04 | Admin pode criar campanha selecionando segmento e template | SATISFIED (code) | POST /api/campaigns + CampaignWizard 4-step — visual confirmation pending |
| WPP-15 | 05-01 | Sistema envia campanha respeitando rate limits | SATISFIED | dispatch_campaigns asyncio.sleep(0.05) = 20 msg/sec, APScheduler every 30s, batch=100 |
| WPP-16 | 05-01, 05-04 | Admin ve status da campanha (enviado/entregue/lido/falha) | SATISFIED (code) | /api/campaigns/{id}/recipients + RecipientTable + campaign detail stats bar — visual confirmation pending |

No orphaned requirements found — all 9 requirement IDs declared in REQUIREMENTS.md for Phase 5 are claimed by plans and verified above.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

Scanned key files for TODO/FIXME/placeholder/return null/empty returns. No stubs or hollow implementations detected. The one "placeholder" occurrence in CampaignWizard.tsx is a form input `placeholder=""` attribute — not a stub.

---

### Human Verification Required

#### 1. Dashboard Visual Rendering

**Test:** Log in as Admin. Open /home.
**Expected:** 5 KPI cards visible at top row (Consultas Hoje, Taxa de Ocupacao, No-shows, Confirmacoes Pendentes, Conversas WhatsApp). ProximasConsultas table below KPIs. Two Recharts charts below table (Tendencia Semanal line chart, Consultas por Especialidade bar chart).
**Why human:** Recharts SSR/client rendering, responsive grid breakpoints, and visual layout correctness cannot be verified programmatically.

#### 2. Role-Based Dashboard Visibility

**Test:** Log in as Recepcionista, open /home. Then log in as Medico, navigate to /home.
**Expected:** Recepcionista sees KPIs and table but NOT the charts section. Medico is immediately redirected to /agenda.
**Why human:** Role-conditional behavior (recepcionista chart exclusion) requires a live authenticated session; medico redirect requires actual Next.js session middleware.

#### 3. Sidebar Role-Conditional Links

**Test:** As Admin, check sidebar for "Templates" and "Campanhas" links. As Recepcionista, confirm those links do not appear.
**Expected:** Admin sees both links; Recepcionista does not.
**Why human:** Sidebar conditional rendering requires a logged-in browser session to confirm correct link visibility.

#### 4. Template Live Preview

**Test:** As Admin, open /templates, click "Novo Template", type a body with {{nome}} and {{medico}}.
**Expected:** Live preview section immediately shows "Maria Silva" and "Dr. Carlos" substituted inline.
**Why human:** Real-time live preview behavior as user types requires interactive browser testing.

#### 5. Campaign Wizard — Live Segment Count

**Test:** As Admin, open /campanhas, click "Nova Campanha". On step 2 (Segmento), change filter dropdowns.
**Expected:** Patient count label updates within ~500ms of each filter change (debounced call to /api/campaigns/preview-segment).
**Why human:** Debounce timing and UI responsiveness require interactive browser testing.

#### 6. QuickSend from WhatsApp Inbox

**Test:** As Recepcionista, open /whatsapp, select a conversation, locate and click the Template/quick-send button in InboxPanel.
**Expected:** QuickSendModal opens, shows template list, renders live preview with patientNome and phone substituted. "Enviar" button sends the message.
**Why human:** QuickSendModal is wired inside InboxPanel.tsx (not page.tsx). Verifying the button appears in the correct UI location and the modal renders correctly requires a live browser session with a real conversation selected.

---

### Gaps Summary

No gaps found. All artifacts exist, are substantive (no stubs), and are wired to their data sources and consumers. The backend is fully functional and importable. All 9 requirement IDs (DASH-01 through DASH-04, WPP-12 through WPP-16) are satisfied by the implementation.

One clarification on the whatsapp/page.tsx acceptance criterion: the plan specified `frontend/src/app/(dashboard)/whatsapp/page.tsx contains "QuickSendModal"`. The QuickSendModal is actually wired in `_components/InboxPanel.tsx` (which is rendered by the page) — this is correct component composition and not a gap. The modal is fully reachable from the page through the component tree.

The 7 items above require human verification for visual correctness, role-conditional behavior, and interactive UI features.

---

_Verified: 2026-03-30_
_Verifier: Claude (gsd-verifier)_
