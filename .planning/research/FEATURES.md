# Feature Landscape

**Domain:** Clinic Management SaaS with AI WhatsApp Agent (Brazil)
**Project:** MedIA
**Researched:** 2026-03-29
**Overall Confidence:** HIGH (corroborated by Brazilian market analysis + international clinic SaaS patterns)

---

## Table Stakes

Features users expect. Missing = product feels incomplete, churn risk is high.

### Authentication and Role-Based Access Control

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Login with email/password | Every SaaS has it | Low | JWT or session-based |
| Three roles: Admin, Receptionist, Doctor | Standard in clinic software; each role has distinct needs | Medium | Admin = full access; Receptionist = scheduling/patients/WhatsApp; Doctor = own agenda + patient records |
| Route-level permission guards | Protects sensitive patient data | Low | Next.js middleware |
| Multi-tenant data isolation | SaaS fundamental; different clinics must never see each other's data | High | tenant_id on all DB queries, enforced at API layer |
| Session management (logout, timeout) | Security expectation | Low | — |

### Main Dashboard

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Today's appointment count | First thing a receptionist needs | Low | Query appointments WHERE date = today |
| Schedule occupancy rate | Top KPI for clinic managers; 70-90% is healthy | Low | (scheduled / available slots) * 100 |
| No-show rate | Directly affects revenue; clinics obsess over this | Low | Aggregate over rolling 30 days |
| Pending confirmations count | Actionable number for receptionist's morning | Low | Appointments without confirmation status |
| Active conversations count (WhatsApp) | Visibility into AI workload | Low | Count open sessions from Redis/DB |
| Upcoming appointments list | Scannable view of what's happening today | Low | Next 5–10 sorted by time |
| Quick stats: total patients, total appointments | Gives manager a pulse on growth | Low | Count queries |

### Appointment Management (Agenda)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Calendar view (day/week/month) | Standard in all clinic software | Medium | FullCalendar or custom; per-doctor filters |
| Create appointment manually | Receptionist needs to book walk-ins and phone calls | Low | Form: patient, doctor, date, time, specialty |
| Edit / reschedule appointment | Routine workflow | Low | Same form, pre-filled |
| Cancel appointment | Routine workflow | Low | With optional cancel reason |
| Appointment status tracking | Agendado → Confirmado → Realizado → Cancelado | Low | Enum status field |
| View appointments by doctor | Each doctor needs to see only their own agenda | Low | Filter by doctor_id |
| Block time slots | Doctor vacation, lunch, unavailability | Medium | Special "block" appointment type |
| Confirmation status update | Receptionist marks confirmed after calling patient | Low | Toggle/dropdown on appointment card |

### Patient Management

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Patient list with search | CRM baseline; find patient by name or phone | Low | Server-side search on name/phone |
| Patient profile page | Aggregate all data about one patient | Medium | Name, phone, appointment history, conversation history |
| Create patient manually | Walk-ins not captured by WhatsApp bot | Low | Basic form: name, phone, birthdate, notes |
| Edit patient info | Data corrections | Low | — |
| Appointment history per patient | Receptionist needs full context | Low | Join patients + appointments |
| Conversation history per patient | View what the AI discussed with the patient | Medium | Join patients + conversations |

### WhatsApp Panel — Conversation Inbox

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Real-time conversation list | Receptionist needs to monitor AI conversations | Medium | WebSocket or polling; list all active sessions |
| Open a conversation and read full history | Full context before intervening | Low | Fetch messages for session_id |
| Conversation status indicators (AI active / human takeover / resolved) | Know who is handling what | Low | Status field on conversation |
| Real-time new message indicator | Receptionist must notice when a patient messages | Medium | WebSocket push or SSE |
| Patient info panel alongside chat | Name, last appointment, phone visible while reading chat | Low | Sidebar join |
| Search conversations by patient name or phone | Find a specific conversation quickly | Low | Filter on phone/name |

### WhatsApp Panel — Human Takeover

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| "Take over" button to disable AI for a conversation | Core safety valve; AI cannot handle everything | Medium | Set a flag in Redis/DB that mutes the AI for that phone |
| Send message as human from panel | Receptionist types and sends directly via Evolution API | Medium | Call Evolution API send endpoint from frontend API |
| "Return to AI" button to re-enable bot | After human resolves the issue | Low | Flip the takeover flag back |
| Visual indicator that conversation is in human mode | Avoid AI and human talking simultaneously | Low | Status badge |
| Prevent AI from responding during takeover | Most critical correctness requirement | Medium | Orchestrator checks takeover flag before processing |

### Doctor/Professional Management

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Doctor list | View all professionals | Low | — |
| Doctor profile: name, specialty, CRM, availability | Used by scheduling tools and displayed to patients | Low | — |
| Define availability schedule | Which days/times each doctor works | Medium | Availability matrix: day × time slots |
| Edit doctor profile | Admin task | Low | — |

### User Management (System Users)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| User list (admin view) | Admin manages who has access | Low | — |
| Create user with role assignment | Onboard receptionist or doctor | Low | Form: name, email, role |
| Edit user role | Promotion or correction | Low | — |
| Deactivate/reactivate user | Off-boarding without deletion | Low | active flag |
| Password reset flow | Standard auth feature | Low | Email-based or admin-forced reset |

### Landing Page (Lead Capture)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Hero section with clear value prop | Visitors need 3-second hook | Low | Based on existing site.html reference |
| CTA button redirecting to WhatsApp | Core funnel; no form, direct to agent | Low | wa.me link with pre-filled message |
| Services/specialties section | Patients need to know what the clinic offers | Low | Static or CMS-driven |
| SEO meta tags and OpenGraph | SSR benefit of Next.js | Low | next/head |
| Mobile-responsive design | 80%+ of Brazilian WhatsApp users are on mobile | Low | Tailwind responsive utilities |
| Visual identity compliance | Must follow green palette + DM Serif/DM Sans from site.html | Low | Tailwind config with brand tokens |

---

## Differentiators

Features that set the product apart. Not universally expected, but create competitive advantage.

### Dashboard Intelligence

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| AI conversation funnel metrics | How many WhatsApp contacts → scheduled → showed up | Medium | Join conversations + appointments |
| Scheduling conversion rate by source | WhatsApp bot vs human booking; shows AI ROI | Medium | Tag appointments by origin |
| No-show trend chart (weekly/monthly) | Proactive pattern detection | Medium | Chart.js or Recharts |
| Revenue by specialty chart | Manager sees which services are most profitable | Medium | Requires procedure/specialty tagging on appointments |
| Agent performance: Sofia response time avg | LLM observability data surfaced for clinic | High | Pull from Langfuse API |

### WhatsApp Panel — Message Templates and Campaigns

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Pre-built message templates | Receptionists send professional, consistent messages fast | Low | Template library stored in DB |
| Template variable substitution | Auto-fill patient name, appointment date/time | Low | Simple string interpolation |
| Bulk campaign: send to patient segment | Re-engage inactive patients, promote new services | High | Requires Evolution API broadcast, opt-in compliance, rate limiting |
| Campaign status tracking (sent / delivered / read) | ROI visibility on campaigns | High | Evolution API webhook callbacks for message status |
| Scheduled campaigns | Send reminders 24h before appointment automatically | High | Queue/cron job + Evolution API |

Note: Bulk campaigns are a strong differentiator but carry WhatsApp policy risk (opt-in required, daily limits per BSP). Start with templates; add campaigns in v2.

### WhatsApp Panel — Advanced Conversation Management

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Internal notes on conversations | Receptionist leaves context for shift change | Low | Notes field on session |
| Assign conversation to specific staff member | Route complex cases to the right person | Medium | Assignee field + filter by assignee |
| Conversation tagging / categorization | Tag as "urgency", "rescheduling", "complaint" | Low | Tags array on session |
| Conversation search across all history | Find what a patient said 3 months ago | Medium | Full-text search on messages table |
| Auto-summarize conversation with AI | Show what the AI-patient exchange was about without reading everything | High | GPT call on conversation history |

### Patient Management — CRM Layer

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Patient segmentation (active, inactive, at-risk) | Target follow-up campaigns | Medium | Last visit date logic |
| Patient notes / clinical annotations | Receptionist context for next contact | Low | Free text notes field |
| WhatsApp conversation summary on patient card | Receptionist sees AI conversation summary at a glance | Medium | Depends on conversation summarizer already in backend |

### Appointment Management — Automation

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Automatic confirmation reminder via WhatsApp | Reduces no-show rate (up to 25% improvement per studies) | Medium | Scheduled job + Evolution API send; AI already does this, surface control in UI |
| Waitlist management | When cancellation occurs, notify waitlisted patient automatically | High | Queue system + bot trigger |
| Appointment color coding by status | Instant visual scan of calendar health | Low | CSS classes per status |

---

## Anti-Features

Features to explicitly NOT build in v1. Each has a reason and a "what to do instead."

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Electronic Medical Record (Prontuario Eletronico) | Full PEP requires specialty-specific forms, CFM compliance, digital signature infrastructure, TISS integration — months of work with no WhatsApp AI differentiation | Store basic appointment notes only; full PEP is v2+ |
| Patient-facing portal / patient login | Doubles auth complexity, requires patient onboarding flow, competes with the WhatsApp channel which already works | Keep patients on WhatsApp; the web panel is for clinic staff only |
| Online payment / billing | PCI compliance, gateway integration (Stripe, PagSeguro, Cielo), split payment for insurance — high compliance cost for v1 | Track appointment status as "paid/unpaid" flag at most; full billing is v2 |
| Native mobile app (iOS/Android) | Next.js web app is already responsive; native apps require separate build/deploy cycles and App Store approval delays | Build responsive web; a PWA can bridge the gap if needed |
| Video consultation / telemedicine | Different product category; requires WebRTC, recording, prescription in-session — distraction from core WhatsApp differentiation | Out of scope; if needed, link out to Zoom/Google Meet |
| Multi-language support | pt-BR is the only market for v1; i18n boilerplate adds code complexity for zero v1 value | Hardcode pt-BR strings; add i18n layer only when expanding market |
| TISS/ANS insurance billing integration | Each health plan has different TISS rules; dedicated integration project; not core to WhatsApp AI flow | Manual recording of insurance name on appointment is enough for v1 |
| Custom report builder / BI tool | Generic drag-and-drop BI is a product in itself; clinics don't need Tableau, they need specific answers | Build 5–7 opinionated charts on the dashboard instead |
| Email marketing / newsletter | Clinic–patient communication is WhatsApp-first in Brazil; email open rates are negligible for this audience | WhatsApp templates and campaigns cover the communication need |
| In-app chat between staff members | Clinics already use WhatsApp internally; this would compete with a tool they already love and won't replace | Out of scope; staff use WhatsApp or Slack |
| Inventory / pharmacy management | Different domain; relevant for hospitals, not for outpatient clinics | Out of scope entirely |

---

## Feature Dependencies

```
Auth (roles + multi-tenancy)
  └── All features (nothing works without auth)

Patient Management
  └── Appointment Management (appointments reference patient_id)
  └── WhatsApp Panel (conversations tied to patient phone)
  └── Dashboard (metrics aggregate patient + appointment data)

Doctor Management
  └── Appointment Management (appointments reference doctor_id)
  └── Availability → Calendar Blocking

Appointment Management
  └── Dashboard (occupancy, no-show, confirmation metrics)
  └── Automatic reminders (depends on appointment status + scheduled job)

WhatsApp Panel — Conversation Inbox
  └── WhatsApp Panel — Human Takeover (takeover is action within conversation)
  └── WhatsApp Panel — Templates (sending template = action within conversation)
  └── Patient Management (conversation links to patient profile)

Evolution API integration (backend already exists)
  └── WhatsApp Panel — Human Takeover (send message from panel)
  └── WhatsApp Panel — Campaigns (broadcast via API)
  └── Automatic Reminders

Landing Page
  └── No dependencies; fully standalone; deploy independently
```

---

## MVP Recommendation

Build in this priority order:

1. **Auth + role-based access** — everything gates on this
2. **Landing page** — revenue-generating entry point; quick win, deploy early
3. **Dashboard (core KPIs)** — demonstrates value to clinic owner immediately
4. **Appointment management (calendar)** — receptionist's primary daily tool
5. **Patient management (list + profile)** — enables context when managing appointments
6. **Doctor management** — needed before appointments work correctly
7. **User management** — admin needs to onboard staff
8. **WhatsApp Panel — Conversation Inbox** — real-time monitoring
9. **WhatsApp Panel — Human Takeover** — safety valve; must ship with inbox

Defer for v1.1 or later:
- WhatsApp templates (low complexity, but not day-1 critical)
- WhatsApp campaigns (high complexity + compliance risk)
- Advanced dashboard charts (trend lines, funnel analytics)
- Conversation auto-summarization in panel
- Patient segmentation
- Waitlist management
- Automatic scheduled reminders UI (backend already sends them; a UI control panel can come later)

---

## Brazilian Market Context

- 70% of Brazilian clinics already use some management software (source: Jestor 2026 market report) — this means you're displacing existing tools, so onboarding friction is the main conversion barrier.
- WhatsApp penetration in Brazil is ~97% of smartphone users — the WhatsApp-first strategy is not a feature, it's market fit.
- Competitors in Brazil (iClinic, Doctor Max, Feegow, GestaoDS, Cloudia) all offer scheduling + PEP + TISS billing. None leads with AI WhatsApp agent as primary differentiator. This is MedIA's wedge.
- LGPD (Brazil's GDPR equivalent) applies. Patient data handling must be documented; audit trails are needed, but full compliance tooling is not v1 scope.
- Pricing range in the market: R$66–R$499/month per clinic. Multi-tenant SaaS at this price point means UI simplicity is critical — clinic staff are not technical users.

---

## Sources

- [Cloudia.com.br — 15 melhores softwares medicos do Brasil](https://www.cloudia.com.br/8-melhores-softwares-medicos-do-mercado-2024/) — MEDIUM confidence (Brazilian competitor analysis)
- [AVI MedTech — Clinic Management Software 2026 Must-Have Features](https://avimedtech.com/clinic-management-software-in-2026-what-it-is-and-key-features-clinics-must-have/) — MEDIUM confidence
- [Apolo Blog — 9 Indicadores Essenciais para Clinicas 2025](https://blog.apolo.app/9-indicadores-essenciais-para-clinicas-em-2025/) — HIGH confidence (Brazil-specific KPI list)
- [AiSensy — WhatsApp Team Inbox Guide 2026](https://m.aisensy.com/blog/whatsapp-team-inbox/) — HIGH confidence (feature list for shared inbox + handoff)
- [Respond.io — WhatsApp AI Agent Overview 2026](https://respond.io/blog/whatsapp-ai-agent) — HIGH confidence
- [Gallabox — WhatsApp for Healthcare Complete Guide](https://gallabox.com/blog/whatsapp-for-healthcare) — MEDIUM confidence
- [Jestor Blog — Melhores Softwares de Gestao para Clinicas 2026](https://blog.jestor.com/melhores-softwares-de-gestao-para-clinicas-e-consultorios-em-2026/) — MEDIUM confidence (market sizing)
- [AiSensy — WhatsApp Templates for Healthcare](https://m.aisensy.com/whatsapp-marketing-template-for-healthcare/) — MEDIUM confidence
