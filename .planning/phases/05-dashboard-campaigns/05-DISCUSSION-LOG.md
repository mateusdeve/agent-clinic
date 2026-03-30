# Phase 5: Dashboard + Campaigns - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 05-dashboard-campaigns
**Areas discussed:** Dashboard KPIs and layout, Charts and data viz, Template editor UX, Campaign dispatch flow

---

## Dashboard KPIs and Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Top row of cards + list below | 4-5 KPI cards in a row, then consultas table below | ✓ |
| Two-column dashboard | KPI cards left, appointments right side-by-side | |
| Full-width metric tiles | Large tiles with sparkline mini-charts | |

**User's choice:** Top row of cards + list below
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| /home becomes the dashboard | Replace placeholder home page with real dashboard | ✓ |
| Separate /dashboard route | Keep /home as welcome, add /dashboard | |

**User's choice:** /home becomes the dashboard

| Option | Description | Selected |
|--------|-------------|----------|
| Page load only | KPIs fetch once on load, user refreshes | ✓ |
| Auto-refresh every 60s | Poll backend every minute | |
| Real-time via Socket.IO | Live updates via Socket.IO events | |

**User's choice:** Page load only

| Option | Description | Selected |
|--------|-------------|----------|
| Admin full, Recep. operational, Medico own agenda | Role-based views with different content per role | ✓ |
| Same dashboard for all roles | Everyone sees same KPIs, charts hidden from non-admin | |

**User's choice:** Admin sees everything, Recep. sees operational, Medico sees own agenda

---

## Charts and Data Viz

| Option | Description | Selected |
|--------|-------------|----------|
| Recharts | React-native, Tailwind-friendly, lightweight | ✓ |
| Chart.js + react-chartjs-2 | Canvas-based, performant, more setup | |
| Tremor | Pre-built dashboard components, may conflict with shadcn | |

**User's choice:** Recharts

| Option | Description | Selected |
|--------|-------------|----------|
| Weekly trend line + specialty bar chart | Line for 7-day trends, bar for specialty breakdown | ✓ |
| + occupancy gauge | Same plus radial gauge for occupancy | |
| Single combined chart with tabs | One chart area, tab-switched | |

**User's choice:** Weekly trend line + specialty bar chart

| Option | Description | Selected |
|--------|-------------|----------|
| Below the consultas list | Charts are secondary, operational data first | ✓ |
| Between KPI cards and consultas | Charts prominent, pushes list down | |

**User's choice:** Below the consultas list

---

## Template Editor UX

| Option | Description | Selected |
|--------|-------------|----------|
| Slide-over form with live preview | Consistent with Phase 3 slide-over pattern | ✓ |
| Full page editor | Dedicated page with side-by-side edit/preview | |
| Simple form, no live preview | Just textarea, preview after saving | |

**User's choice:** Slide-over form with live preview

| Option | Description | Selected |
|--------|-------------|----------|
| Patient + appointment basics | nome, telefone, data, hora, medico, especialidade | ✓ |
| Basics + clinic info | Same plus clinica, endereco, telefone_clinica | |
| Free-form custom variables | Admin defines any variable name | |

**User's choice:** Patient + appointment basics

| Option | Description | Selected |
|--------|-------------|----------|
| New /templates page in sidebar | Dedicated sidebar item with template table | ✓ |
| Inside the WhatsApp panel as tab | Templates as secondary tab in inbox | |

**User's choice:** New /templates page in sidebar

---

## Campaign Dispatch Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Filter builder with predefined criteria | Dropdowns for especialidade, ultimo agendamento, status | ✓ |
| Manual patient selection | Checkbox list with search | |
| Saved segments | Named reusable segment definitions | |

**User's choice:** Filter builder with predefined criteria

| Option | Description | Selected |
|--------|-------------|----------|
| Backend queue with 20 msg/sec throttle | APScheduler processes queue, status via polling | ✓ |
| Backend queue with Socket.IO status | Same queue, real-time status via Socket.IO | |
| Synchronous batch send | Single loop, blocks UI | |

**User's choice:** Backend queue with 20 msg/sec throttle

| Option | Description | Selected |
|--------|-------------|----------|
| New /campanhas page in sidebar | Dedicated sidebar item with campaign table | ✓ |
| Inside /templates page as tab | Templates and campaigns share page | |

**User's choice:** New /campanhas page in sidebar

| Option | Description | Selected |
|--------|-------------|----------|
| Step wizard: Template > Segment > Preview > Send | Multi-step form, clear flow | ✓ |
| Single-page form | All fields on one page | |

**User's choice:** Step wizard

| Option | Description | Selected |
|--------|-------------|----------|
| Campaign detail page with recipient table | Stats bar + per-recipient table with status badges | ✓ |
| Inline status in campaign list | Progress bar and counts inline, no detail page | |
| Real-time status via Socket.IO | Live-updating recipient statuses | |

**User's choice:** Campaign detail page with recipient table

| Option | Description | Selected |
|--------|-------------|----------|
| Admin only | Only Admin creates/sends campaigns. Recep. uses quick-send | ✓ |
| Both Admin and Recepcionista | Both roles can create campaigns | |

**User's choice:** Admin only

---

## Claude's Discretion

- KPI card visual design (icons, colors, hover states)
- Chart styling and colors
- Template variable insertion UX
- Campaign wizard step navigation design
- Quick-send UX for Recepcionista
- Sidebar ordering for new items
- Empty states
- Campaign recipient table pagination
- Filter builder dropdown styling

## Deferred Ideas

None
