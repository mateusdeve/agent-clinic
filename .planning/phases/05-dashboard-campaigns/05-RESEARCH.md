# Phase 5: Dashboard + Campaigns - Research

**Researched:** 2026-03-30
**Domain:** React dashboard charts (Recharts), KPI aggregation SQL, campaign dispatch queue (APScheduler), WhatsApp template messaging
**Confidence:** HIGH

## Summary

Phase 5 adds two major features to the existing Next.js 16 + FastAPI stack. First, a real-time operational dashboard replaces the `/home` placeholder — 5 KPI cards, a next-appointments table, and two Admin-only charts. Second, a template management system and campaign dispatch engine allowing admins to send bulk WhatsApp messages to filtered patient segments.

All frontend foundations are already in place from Phases 2-4: `apiFetch`, `SlideOver`, `DataTable`, `StatusBadge`, `react-hook-form + zod`, and the existing sidebar layout. The backend has APScheduler (used by the follow-up dispatcher in `webhook.py`) that can host a new campaign dispatch job. Evolution API's `send_message_with_typing()` client is already wired and reusable for campaign sends.

The main new dependency is **Recharts 3.8.1** for charts. It is compatible with React 19 and requires `"use client"` wrapping in Next.js App Router. The campaign system needs two new DB tables (`message_templates`, `campaigns` + `campaign_recipients`) and a new FastAPI router. The 20 msg/sec throttle is straightforward using asyncio.sleep in an APScheduler async job.

**Primary recommendation:** Install Recharts 3.8.1, add two DB migration tables, implement four new FastAPI routers (dashboard stats, templates, campaigns, quick-send), and add three new frontend pages (/home rewrite, /templates, /campanhas) plus a QuickSend UI touch in /whatsapp. Follow the established REST router pattern from Phase 3 throughout.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Top row of 5 KPI cards (consultas hoje, taxa de ocupacao, no-shows, confirmacoes pendentes, conversas WhatsApp ativas) followed by a "Proximas Consultas Hoje" table below, then charts section at bottom.
- **D-02:** Dashboard replaces the current `/home` placeholder page. No separate `/dashboard` route — `/home` IS the dashboard.
- **D-03:** KPI values fetch once on page load. No auto-refresh or Socket.IO — user refreshes the page to update.
- **D-04:** Role-based views: Admin sees everything (KPIs + consultas + charts + campaigns link). Recepcionista sees KPIs + consultas list (no charts). Medico is redirected to `/agenda` (their own schedule).
- **D-05:** Recharts library for all charts. React-native, Tailwind-friendly, declarative API.
- **D-06:** Two charts for DASH-04: Line chart showing 7-day trends (consultas, no-shows) and Bar chart showing consultas by specialty. Admin-only section.
- **D-07:** Charts appear below the "Proximas Consultas" table. Operational data first, analytics second.
- **D-08:** Slide-over form with live preview (consistent with Phase 3 D-06 pattern). Left: template name + textarea with `{{variavel}}` placeholders. Below: live preview with sample data substituted.
- **D-09:** Fixed set of template variables: `{{nome}}`, `{{telefone}}`, `{{data}}`, `{{hora}}`, `{{medico}}`, `{{especialidade}}`. Covers confirmation, reminder, and follow-up use cases.
- **D-10:** Templates live on a new `/templates` page with dedicated sidebar item. Table with name, preview snippet, variable count, last used. Slide-over for create/edit.
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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | Admin/Recepcionista ve KPIs: consultas hoje, taxa de ocupacao, no-shows, confirmacoes pendentes | SQL aggregation on `appointments` table by date + status; new `/api/dashboard/stats` endpoint |
| DASH-02 | Admin/Recepcionista ve lista das proximas consultas do dia | Same endpoint — query `appointments WHERE data_agendamento = today AND status != cancelado ORDER BY horario` |
| DASH-03 | Admin/Recepcionista ve contador de conversas WhatsApp ativas | `conversations` table GROUP BY session_id; Redis takeover keys for ia_ativa vs humano status |
| DASH-04 | Admin ve graficos de tendencias semanais, funil de conversao e receita por especialidade | Recharts 3.8.1 LineChart (7-day trend) + BarChart (by especialidade); `/api/dashboard/charts` endpoint |
| WPP-12 | Admin pode criar/editar templates de mensagem com variaveis (nome, data) | New `message_templates` table + `/api/templates` CRUD router; SlideOver + react-hook-form reuse |
| WPP-13 | Recepcionista pode usar template para enviar mensagem rapida a um paciente | Quick-send modal in WhatsApp inbox; POST `/api/conversations/{phone}/send-template` endpoint |
| WPP-14 | Admin pode criar campanha selecionando segmento de pacientes e template | New `campaigns` + `campaign_recipients` tables; step wizard UI; POST `/api/campaigns` endpoint |
| WPP-15 | Sistema envia campanha respeitando rate limits do WhatsApp | APScheduler async job in webhook.py; 20 msg/sec = asyncio.sleep(0.05) between sends |
| WPP-16 | Admin ve status da campanha (enviado/entregue/lido/falha) | Per-recipient status in `campaign_recipients`; GET `/api/campaigns/{id}/recipients`; page polling |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| recharts | 3.8.1 | LineChart + BarChart for dashboard | Locked decision D-05; React 19 compatible; declarative SVG charts |
| react-is | 19+ | Required peer dep for recharts | Auto-installed with recharts |

### Supporting — Already Installed
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tanstack/react-table | 8.21.3 | Templates, campaigns, recipients tables | All entity list pages (established pattern) |
| react-hook-form | 7.72.0 | Template form, campaign wizard steps | All forms (established pattern) |
| zod | 4.3.6 | Schema validation for template + campaign bodies | All form schemas (established pattern) |
| lucide-react | 1.7.0 | KPI card icons | Established icon library |
| date-fns | 4.1.0 | Date math for KPI query boundaries, trend dates | Already in stack |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Recharts | Chart.js or Nivo | Decision locked — Recharts is declarative React, zero canvas API learning curve |
| APScheduler async job | Celery/Redis Queue | APScheduler already in stack; Celery would be a major new dependency for a simple throttled loop |
| Page polling for campaign status | Socket.IO | Decision locked (D-03/D-14); polling is simpler and acceptable for campaign status (not real-time critical) |

**Installation:**
```bash
# From frontend directory
npm install recharts

# Verify (recharts 3.8.1 latest as of 2026-03-30)
npm view recharts version
```

**Version verification:** Confirmed `recharts@3.8.1` is `latest` as of 2026-03-30 (`npm view recharts dist-tags`). Compatible with React 19, react-dom 19, react-is (auto-installed as dep).

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/app/(dashboard)/
├── home/
│   └── page.tsx             # REPLACE placeholder — full dashboard (Server Component, passes data to Client charts)
├── templates/
│   └── page.tsx             # WPP-12 — template CRUD page
├── campanhas/
│   ├── page.tsx             # WPP-14/16 — campaign list
│   └── [id]/
│       └── page.tsx         # WPP-16 — campaign detail + recipient table

frontend/src/components/dashboard/
├── KpiCard.tsx              # Reusable card for 5 KPIs
├── ProximasConsultas.tsx    # Today's appointments table (uses DataTable)
├── TrendChart.tsx           # Recharts LineChart 7-day wrapper (use client)
├── EspecialidadeChart.tsx   # Recharts BarChart by specialty (use client)
├── TemplatesTable.tsx       # Column defs for /templates
├── CampaignWizard.tsx       # Step wizard (multi-step state machine)
├── CampaignTable.tsx        # Campaign list columns + status
├── RecipientTable.tsx       # Per-recipient status table
└── QuickSendModal.tsx       # WPP-13 — inline template picker for inbox

agent-service/src/api/
├── dashboard.py             # GET /api/dashboard/stats + /api/dashboard/charts
├── templates.py             # CRUD /api/templates
├── campaigns.py             # POST /api/campaigns, GET list + detail + recipients

agent-service/alembic/versions/
└── 005_templates_campaigns.py   # New tables: message_templates, campaigns, campaign_recipients
```

### Pattern 1: Recharts in Next.js App Router (CRITICAL)
**What:** Recharts uses browser APIs — components must be Client Components
**When to use:** Any file that imports from recharts
**Example:**
```tsx
// Source: recharts.org + Next.js App Router "use client" requirement
"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from "recharts";

interface TrendData {
  date: string;
  consultas: number;
  no_shows: number;
}

interface TrendChartProps {
  data: TrendData[];
}

export function TrendChart({ data }: TrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e8ece9" />
        <XAxis dataKey="date" tick={{ fill: "#5a6b5f", fontSize: 12 }} />
        <YAxis tick={{ fill: "#5a6b5f", fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="consultas" stroke="#2e9e60" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="no_shows" stroke="#9aaa9e" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Pattern 2: KPI Stats SQL Aggregation
**What:** Single SQL query returning all 5 KPI values for today's date
**When to use:** GET /api/dashboard/stats — called once on page load

```python
# agent-service/src/api/dashboard.py
# Uses get_db_for_tenant pattern from Phase 3 (RLS automatic)
@router.get("/api/dashboard/stats")
async def get_dashboard_stats(
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn = Depends(get_db_for_tenant),
):
    today = date.today().isoformat()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status != 'cancelado') AS consultas_hoje,
                COUNT(*) FILTER (WHERE status = 'cancelado') AS no_shows,
                COUNT(*) FILTER (WHERE status = 'agendado') AS confirmacoes_pendentes,
                COUNT(*) FILTER (WHERE status IN ('agendado','confirmado','realizado','cancelado')) AS total_slots
            FROM appointments
            WHERE data_agendamento = %s
        """, (today,))
        row = cur.fetchone()
    # taxa_ocupacao = consultas_hoje / total_slots if total_slots > 0
    # conversas_ativas: separate query on conversations table
```

### Pattern 3: Campaign Dispatch with APScheduler Rate Limiting
**What:** Async APScheduler job picks pending campaign_recipients and sends at 20 msg/sec
**When to use:** Campaign status transitions from `rascunho` → `enviando` → `concluida`

```python
# agent-service/src/api/webhook.py — add to existing scheduler
import asyncio

async def dispatch_campaigns():
    """Envia mensagens de campanhas pendentes a 20 msgs/seg (WPP-15)."""
    # 1. Find campaign_recipients with status='pendente' grouped by campaign
    # 2. For each recipient: render template, call evolution_client.send_message_with_typing()
    # 3. Update status to 'enviado', 'falha' on error
    # 4. After all recipients done, update campaign.status = 'concluida'
    DELAY = 1.0 / 20  # 0.05s between messages = 20/sec

    # ... fetch pendentes from DB ...
    for recipient in pendentes:
        try:
            message = render_template(template_body, recipient.variables)
            await evolution_client.send_message_with_typing(recipient.phone, message)
            update_recipient_status(recipient.id, "enviado")
        except Exception as e:
            update_recipient_status(recipient.id, "falha")
        await asyncio.sleep(DELAY)

# In startup():
scheduler.add_job(dispatch_campaigns, "interval", seconds=30, id="campaign_dispatcher")
```

### Pattern 4: Template Variable Substitution
**What:** Replace `{{variavel}}` placeholders in template body with patient data
**When to use:** Live preview in template editor + campaign dispatch

```python
import re

ALLOWED_VARS = {"nome", "telefone", "data", "hora", "medico", "especialidade"}

def render_template(body: str, variables: dict) -> str:
    """Substitui variaveis {{nome}} no corpo do template."""
    def replacer(match):
        key = match.group(1)
        if key in ALLOWED_VARS and key in variables:
            return variables[key]
        return match.group(0)  # leave unresolved vars as-is
    return re.sub(r"\{\{(\w+)\}\}", replacer, body)
```

Frontend live preview (React):
```tsx
// In template SlideOver — pure string replacement, no library needed
function previewTemplate(body: string, sampleData: Record<string, string>): string {
  return body.replace(/\{\{(\w+)\}\}/g, (_, key) => sampleData[key] ?? `{{${key}}}`);
}

const SAMPLE_DATA = {
  nome: "Maria Silva", telefone: "11999990000", data: "01/04/2026",
  hora: "09:30", medico: "Dr. Carlos", especialidade: "Cardiologia"
};
```

### Pattern 5: Campaign Wizard (Multi-Step State)
**What:** Step wizard with local React state — no external step library needed
**When to use:** /campanhas create flow (D-12)

```tsx
"use client";
type WizardStep = "template" | "segmento" | "preview" | "confirmar";

export function CampaignWizard() {
  const [step, setStep] = React.useState<WizardStep>("template");
  const [templateId, setTemplateId] = React.useState<string | null>(null);
  const [filters, setFilters] = React.useState<SegmentFilters>({});
  const [recipients, setRecipients] = React.useState<Patient[]>([]);
  // Each step renders a form section; Back/Proximo buttons advance state
}
```

### Pattern 6: Patient Segment Count (Live Filter)
**What:** GET `/api/campaigns/preview-segment?especialidade=X&ultimo_agendamento_range=30-90d` returns count
**When to use:** Filter builder in wizard step 2 (D-13) — debounced on filter change

```python
# DB query for segment filter
WHERE
  (%s IS NULL OR especialidade = %s)
  AND (%s IS NULL OR (
    CASE %s
      WHEN 'lt30d' THEN last_appointment >= NOW() - INTERVAL '30 days'
      WHEN '30-90d' THEN last_appointment BETWEEN NOW() - INTERVAL '90 days' AND NOW() - INTERVAL '30 days'
      WHEN 'gt90d' THEN last_appointment < NOW() - INTERVAL '90 days'
    END
  ))
```

### Anti-Patterns to Avoid

- **Server Component importing recharts directly:** Will crash — recharts needs browser SVG/DOM. Always isolate in `"use client"` wrapper component, then import that wrapper from Server Components as a prop-receiving island.
- **Polling on every keystroke for segment count:** Debounce segment filter changes 500ms before fetching preview count — prevents N API calls while user selects filters.
- **Storing template body with pre-substituted values:** Store raw template with `{{variavel}}` syntax in DB. Substitute at dispatch time per recipient. Avoids data duplication.
- **Running campaign dispatch inline with HTTP request:** Always queue the campaign in DB with status `rascunho`, then transition to `enviando` via the APScheduler job — never dispatch in the POST handler (risk of timeout, no retries).
- **Blocking `dispatch_campaigns` on Evolution API timeout:** Wrap each individual send in try/except with per-recipient error status. One failed send must not abort the campaign.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Charts / data viz | Custom SVG chart components | Recharts 3.8.1 (locked D-05) | Responsive containers, tooltips, legends, animation — 500+ lines of code handled |
| Template variable parsing | Custom regex engine | Simple `str.replace` / `re.sub` with ALLOWED_VARS whitelist | Only 6 variables, no nesting — regex is sufficient and safe |
| Message rate limiting | Custom token bucket | `asyncio.sleep(0.05)` in APScheduler job | Simple interval dispatch at 20/sec; no bursting needed |
| Multi-step form state | react-step-wizard library | Local React `useState` with step enum | Wizard is 4 steps with no branching logic; library adds unnecessary weight |
| Patient segment queries | ORM model layer | Raw psycopg2 queries via `get_db_for_tenant` (established pattern) | Entire codebase uses raw SQL; introducing ORM here would be inconsistent |

**Key insight:** All infra is already in place. Phase 5 is predominantly assembling new features from existing building blocks. The main risks are chart `"use client"` isolation and correct campaign queue flow, not fundamental new architecture.

## Common Pitfalls

### Pitfall 1: Recharts SSR Crash
**What goes wrong:** Importing `recharts` components directly in a Server Component (or a module imported by one) throws `window is not defined` at build/render time in Next.js App Router.
**Why it happens:** Recharts reads browser APIs at import time. Next.js SSR pre-renders server components without a DOM.
**How to avoid:** Every recharts import MUST be in a file with `"use client"` at the top. The dashboard `page.tsx` (Server Component) passes data as props to `<TrendChart data={...} />` and `<EspecialidadeChart data={...} />` which are isolated client components.
**Warning signs:** Build error `ReferenceError: window is not defined` or `document is not defined` when running `next build`.

### Pitfall 2: ResponsiveContainer Width in Hidden Containers
**What goes wrong:** `ResponsiveContainer width="100%"` returns width=0 when chart is rendered inside a hidden/collapsed section, causing charts to appear as empty or broken.
**Why it happens:** ResponsiveContainer measures its parent DOM node — if parent has no layout (display:none or 0-width), it gets 0.
**How to avoid:** Always give the chart wrapper div an explicit min-height and ensure it is visible when mounted. For admin-only sections, render conditionally (not hidden with CSS).
**Warning signs:** Chart renders with zero size on first load; re-renders when browser is resized.

### Pitfall 3: Campaign Double-Dispatch
**What goes wrong:** Campaign job runs every 30 seconds; if the previous run is still processing (slow Evolution API), the next invocation starts processing the same recipients again.
**Why it happens:** APScheduler `interval` jobs do not wait for the previous execution to finish.
**How to avoid:** Use a DB-level lock or status transition. When picking `pendente` recipients, immediately UPDATE status to `processando` in the same transaction. Only `pendente` records get picked; `processando` records are skipped by concurrent runs.
**Warning signs:** Recipients show duplicate messages; campaign delivery count exceeds recipient count.

### Pitfall 4: Template Body XSS in Preview
**What goes wrong:** Template body contains HTML/script injection that executes in the live preview.
**Why it happens:** Using `dangerouslySetInnerHTML` for the preview with user-provided body.
**How to avoid:** Render preview as plain text in a `<pre>` or `<p>` — never use `dangerouslySetInnerHTML`. The preview is just a string substitution result, not rich HTML.
**Warning signs:** `<script>` tags in template body execute in preview panel.

### Pitfall 5: Medico Role on /home Redirect
**What goes wrong:** Medico opens `/home` and sees either an error or a broken partial dashboard.
**Why it happens:** Dashboard data queries assume admin/recepcionista context (RLS still applies but stats are confusing for medico).
**How to avoid:** Per D-04, redirect Medico role immediately in `page.tsx` before any data fetch: `if (role === "medico") redirect("/agenda")`. This is a Server Component redirect — zero flicker.
**Warning signs:** Medico sees admin KPI cards or empty stats.

### Pitfall 6: Conversations Active Count Requires Redis
**What goes wrong:** DASH-03 (active WhatsApp conversations) returns 0 or errors because the takeover status lives in Redis, not the DB.
**Why it happens:** Conversation `status` is not persisted in PostgreSQL — it is derived from Redis keys (`takeover:{phone}`).
**How to avoid:** The `/api/dashboard/stats` endpoint must call Redis (via `redis_client` from `socketio_server.py`) to enumerate `takeover:*` keys for the `humano` count. For `ia_ativa` count: count distinct session_ids in `conversations` table with last message in last 24h MINUS those in Redis takeover set.
**Warning signs:** Dashboard shows 0 active conversations when WhatsApp inbox clearly has conversations.

## Code Examples

### Dashboard Stats Endpoint Skeleton
```python
# Source: appointments.py pattern + conversations.py count pattern
@router.get("/api/dashboard/stats")
async def get_dashboard_stats(
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn = Depends(get_db_for_tenant),
):
    today = date.today().isoformat()
    with conn.cursor() as cur:
        # KPI aggregation in single query
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status NOT IN ('cancelado')) AS consultas_hoje,
                COUNT(*) FILTER (WHERE status = 'cancelado') AS no_shows,
                COUNT(*) FILTER (WHERE status = 'agendado') AS confirmacoes_pendentes,
                COUNT(*) AS total_agendamentos_hoje
            FROM appointments
            WHERE data_agendamento = %s
        """, (today,))
        stats_row = cur.fetchone()

        # Proximas consultas today
        cur.execute("""
            SELECT a.id, a.horario, a.status, a.especialidade,
                   p.nome AS patient_nome, d.nome AS doctor_nome
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.id
            LEFT JOIN doctors d ON a.doctor_id = d.id
            WHERE a.data_agendamento = %s AND a.status != 'cancelado'
            ORDER BY a.horario
            LIMIT 20
        """, (today,))
        proximas = cur.fetchall()

    # conversas_ativas from conversations table (last 24h unique sessions)
    # takeover count from Redis keys (see pitfall 6)
    ...
```

### Recharts BarChart by Specialty
```tsx
// Source: recharts.org BarChart API
"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface EspecialidadeData { especialidade: string; count: number; }

export function EspecialidadeChart({ data }: { data: EspecialidadeData[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e8ece9" />
        <XAxis dataKey="especialidade" tick={{ fill: "#5a6b5f", fontSize: 11 }} />
        <YAxis tick={{ fill: "#5a6b5f", fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="count" fill="#2e9e60" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

### New DB Tables (Migration 005)
```sql
-- message_templates
CREATE TABLE message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    nome TEXT NOT NULL,
    corpo TEXT NOT NULL,             -- raw body with {{variavel}} placeholders
    variaveis_usadas TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    nome TEXT NOT NULL,
    template_id UUID NOT NULL REFERENCES message_templates(id),
    filtros JSONB NOT NULL DEFAULT '{}',   -- segment filter criteria
    status TEXT NOT NULL DEFAULT 'rascunho',  -- rascunho|enviando|concluida|falha
    total_recipients INT DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    enviado_at TIMESTAMPTZ
);

-- campaign_recipients
CREATE TABLE campaign_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL,
    phone TEXT NOT NULL,
    variaveis JSONB NOT NULL DEFAULT '{}',  -- resolved variable values for this recipient
    status TEXT NOT NULL DEFAULT 'pendente',  -- pendente|processando|enviado|entregue|lido|falha
    erro TEXT,
    sent_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS policies (same pattern as 003)
ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_recipients ENABLE ROW LEVEL SECURITY;
-- policies use current_tenant_id() function from migration 003
```

### Sidebar Update Pattern
```tsx
// frontend/src/app/(dashboard)/layout.tsx — add admin-only nav items
{role === "admin" && (
  <>
    <a href="/templates" className="...">Templates</a>
    <a href="/campanhas" className="...">Campanhas</a>
  </>
)}
// Recepcionista gets no direct template/campaign nav access
// (quick-send is inline in /whatsapp)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Chart.js (canvas-based) | Recharts (SVG React) | 2021+ | No imperative canvas API; fully declarative, Tailwind-color-compatible |
| Recharts v2 API | Recharts v3 API | 2024 | v3 has minor breaking changes in Tooltip/Legend props — use v3.8.1 docs, not training data |
| APScheduler `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.93+ | `on_event` is deprecated in newer FastAPI; however it still works in 0.115.5 — no migration needed now, but planner should not introduce new `@app.on_event` uses |

**Deprecated/outdated:**
- Recharts v2 `<Tooltip content={...}>` signature changed in v3 — do not assume v2 examples from training data apply.
- `@app.on_event` in FastAPI: still functional in 0.115.5 but the pattern already in webhook.py; just ADD to existing scheduler startup, do not refactor.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| recharts | Dashboard charts (DASH-04) | needs install | 3.8.1 (npm registry) | — none — required by D-05 |
| Node.js | npm install recharts | ✓ | v24.14.0 | — |
| Python 3.9.6 | Backend API | ✓ | 3.9.6 | — |
| APScheduler | Campaign dispatch | ✓ (in stack) | 3.11.0 | — already wired in webhook.py |
| PostgreSQL | DB tables (migration 005) | not in PATH locally | — | Dev connects via DATABASE_URL env var |
| Redis | Takeover flag lookup for DASH-03 | not locally available | — | Dev connects via REDIS_URL env var |
| Evolution API | Campaign send (WPP-15) | external service | — | Configured via EVOLUTION_API_KEY env var |

**Missing dependencies with no fallback:**
- `recharts` package not yet installed in `frontend/` — must be installed in Wave 0

**Missing dependencies with fallback:**
- `psql` / `redis-cli` not in local PATH — tests connect via env vars; runtime services assumed running in dev environment per existing phases

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `agent-service/pytest.ini` |
| Quick run command | `cd agent-service && pytest tests/test_dashboard.py tests/test_templates.py tests/test_campaigns.py -x` |
| Full suite command | `cd agent-service && pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | `/api/dashboard/stats` returns correct KPI counts for today | unit | `pytest tests/test_dashboard.py::test_stats_kpis -x` | ❌ Wave 0 |
| DASH-02 | Stats response includes proximas_consultas list | unit | `pytest tests/test_dashboard.py::test_proximas_consultas -x` | ❌ Wave 0 |
| DASH-03 | Stats conversas_ativas count derived correctly | unit | `pytest tests/test_dashboard.py::test_conversas_ativas -x` | ❌ Wave 0 |
| DASH-04 | `/api/dashboard/charts` returns 7-day trend + specialty breakdown | unit | `pytest tests/test_dashboard.py::test_charts_data -x` | ❌ Wave 0 |
| WPP-12 | Template CRUD: create/read/update/delete | unit | `pytest tests/test_templates.py -x` | ❌ Wave 0 |
| WPP-13 | Quick-send endpoint sends via Evolution API and stores in DB | unit | `pytest tests/test_campaigns.py::test_quick_send -x` | ❌ Wave 0 |
| WPP-14 | Campaign creation with segment filter; recipients populated | unit | `pytest tests/test_campaigns.py::test_create_campaign -x` | ❌ Wave 0 |
| WPP-15 | Dispatch job respects 20 msg/sec throttle (mocked Evolution) | unit | `pytest tests/test_campaigns.py::test_dispatch_rate_limit -x` | ❌ Wave 0 |
| WPP-16 | Campaign detail returns per-recipient status | unit | `pytest tests/test_campaigns.py::test_campaign_status -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd agent-service && pytest tests/test_dashboard.py tests/test_templates.py tests/test_campaigns.py -x`
- **Per wave merge:** `cd agent-service && pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `agent-service/tests/test_dashboard.py` — covers DASH-01 through DASH-04
- [ ] `agent-service/tests/test_templates.py` — covers WPP-12
- [ ] `agent-service/tests/test_campaigns.py` — covers WPP-13 through WPP-16
- [ ] `npm install recharts` in `frontend/` directory — required before any chart component can be written

## Sources

### Primary (HIGH confidence)
- npm registry `npm view recharts dist-tags` — confirmed 3.8.1 is latest, React 19 compatible peer deps verified
- Direct file inspection of `frontend/package.json` — confirmed all supporting libraries already installed
- Direct inspection of `agent-service/src/api/webhook.py` — confirmed APScheduler AsyncIOScheduler already in use at startup
- Direct inspection of `frontend/src/components/dashboard/` — confirmed SlideOver, DataTable, StatusBadge exist and their props
- Direct inspection of `frontend/src/lib/types.ts` — confirmed existing entity types; new types needed for templates/campaigns
- Direct inspection of `frontend/src/app/(dashboard)/layout.tsx` — confirmed sidebar structure for adding new nav items
- Direct inspection of `agent-service/alembic/versions/` — confirmed migration sequence; next is 005

### Secondary (MEDIUM confidence)
- Recharts v3 API patterns from recharts.org (accessed via training knowledge; v3.8.1 confirmed current via npm registry)
- APScheduler async job pattern — verified against existing dispatch_followups implementation in webhook.py
- PostgreSQL `FILTER (WHERE ...)` aggregate syntax — standard SQL, used in existing appointments queries

### Tertiary (LOW confidence)
- Recharts `ResponsiveContainer` width=0 in hidden containers: known community pitfall, not formally documented but widely reported

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — recharts version confirmed via npm registry; all supporting libraries confirmed installed
- Architecture: HIGH — all patterns extrapolated from existing Phase 3/4 code which is verified
- Pitfalls: HIGH for chart SSR and campaign double-dispatch (these are common failure modes with clear remediation); MEDIUM for Redis-based conversation count (depends on Redis connection availability in dev)

**Research date:** 2026-03-30
**Valid until:** 2026-04-29 (recharts is stable; APScheduler API is stable)
