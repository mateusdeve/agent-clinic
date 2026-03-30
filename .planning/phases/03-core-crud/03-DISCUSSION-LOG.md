# Phase 3: Core CRUD - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 03-core-crud
**Areas discussed:** Calendar / Agenda UI, Data tables and forms, Patient profile page, API design pattern

---

## Calendar / Agenda UI

### Calendar views
| Option | Description | Selected |
|--------|-------------|----------|
| Day + Week + Month | All three views with toggle | ✓ |
| Week only | Just weekly grid | |
| Day + Week only | Skip month view | |

**User's choice:** Day + Week + Month

### Calendar library
| Option | Description | Selected |
|--------|-------------|----------|
| Build custom with date-fns | Custom grid + Tailwind. Full brand control. | ✓ |
| FullCalendar React | Feature-rich but heavy (~150kb), harder to customize | |
| You decide | Claude picks | |

**User's choice:** Build custom with date-fns

### Status display
| Option | Description | Selected |
|--------|-------------|----------|
| Color-coded blocks | Agendado=blue, Confirmado=green, Realizado=gray, Cancelado=red | ✓ |
| Status badge on card | Same color, text badge | |
| You decide | Claude picks | |

**User's choice:** Color-coded blocks

---

## Data Tables and Forms

### Table component
| Option | Description | Selected |
|--------|-------------|----------|
| shadcn Table + TanStack Table | Headless logic + Tailwind control | ✓ |
| shadcn Table only | Manual sort/filter/pagination | |
| You decide | Claude picks | |

**User's choice:** shadcn Table + TanStack Table

### Create/edit forms
| Option | Description | Selected |
|--------|-------------|----------|
| Slide-over panel | Side panel from right, list stays visible | ✓ |
| Modal dialog | Centered overlay | |
| Full page | Separate route per form | |

**User's choice:** Slide-over panel

### Pagination
| Option | Description | Selected |
|--------|-------------|----------|
| Server-side pagination | Page numbers, 20/page, API paginated | ✓ |
| Load more / infinite scroll | Button/auto-load | |
| You decide | Claude picks | |

**User's choice:** Server-side pagination

---

## Patient Profile Page

### Profile layout
| Option | Description | Selected |
|--------|-------------|----------|
| Tabbed layout | Header + tabs: Consultas / Conversas WhatsApp | ✓ |
| Single scrollable page | All sections stacked | |
| Sidebar + content | Info left, content right | |

**User's choice:** Tabbed layout

### WhatsApp history display
| Option | Description | Selected |
|--------|-------------|----------|
| Chat bubble timeline | Read-only chat bubbles like WhatsApp | ✓ |
| Message table | Table with timestamp/sender/content | |
| You decide | Claude picks | |

**User's choice:** Chat bubble timeline

---

## API Design Pattern

### API structure
| Option | Description | Selected |
|--------|-------------|----------|
| RESTful with FastAPI routers | /api/patients, /api/appointments, etc. | ✓ |
| GraphQL | Single /graphql endpoint | |
| You decide | Claude picks | |

**User's choice:** RESTful with FastAPI routers

### Pagination response
| Option | Description | Selected |
|--------|-------------|----------|
| Envelope: { items, total, page, per_page } | Standard envelope | ✓ |
| Link-based (RFC 5988) | Next/prev URLs in headers | |
| You decide | Claude picks | |

**User's choice:** Envelope format

---

## Claude's Discretion

- Column definitions per entity, time slot granularity, availability grid UX, deactivation flow, password reset, slide-over animation, search debounce, empty states

## Deferred Ideas

None
