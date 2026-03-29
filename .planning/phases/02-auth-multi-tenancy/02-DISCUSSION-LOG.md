# Phase 2: Auth + Multi-Tenancy - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 02-auth-multi-tenancy
**Areas discussed:** Auth strategy, Login page design, Role-based access (RBAC), Tenant isolation

---

## Auth Strategy

### Authentication approach
| Option | Description | Selected |
|--------|-------------|----------|
| NextAuth.js + FastAPI JWT | NextAuth handles login UI/session on frontend, FastAPI issues its own JWT with tenant_id+role for API calls | ✓ |
| Custom JWT end-to-end | Build login API in FastAPI, store JWT in httpOnly cookie, Next.js middleware validates | |
| You decide | Claude picks the best approach | |

**User's choice:** NextAuth.js + FastAPI JWT
**Notes:** Two token layers — NextAuth session cookie for frontend, FastAPI access token for API calls.

### Token storage
| Option | Description | Selected |
|--------|-------------|----------|
| httpOnly cookie | Stored as httpOnly secure cookie — immune to XSS, requires CSRF protection | ✓ |
| Memory + refresh cookie | Access token in JS memory, refresh token in httpOnly cookie | |
| You decide | Claude picks based on security/simplicity | |

**User's choice:** httpOnly cookie

### Registration model
| Option | Description | Selected |
|--------|-------------|----------|
| Invite-only | Admin creates users. No public signup. Matches B2B SaaS for clinics. | ✓ |
| Self-registration with approval | User signs up, Admin approves | |
| Self-registration open | Anyone can register and create a clinic | |

**User's choice:** Invite-only

### Password recovery
| Option | Description | Selected |
|--------|-------------|----------|
| Skip for v1 | Admin resets password manually. Add self-service later. | ✓ |
| Email-based reset | Forgot password sends reset link. Needs email provider. | |
| You decide | Claude picks simplest viable approach | |

**User's choice:** Skip for v1

---

## Login Page Design

### Layout style
| Option | Description | Selected |
|--------|-------------|----------|
| Centered card on green gradient | Full-height page with centered white card | |
| Split layout | Left: branding/illustration. Right: login form. | ✓ |
| Minimal full-width | Simple centered form, minimal branding | |

**User's choice:** Split layout

### Left side content
| Option | Description | Selected |
|--------|-------------|----------|
| MedIA branding + tagline | Green gradient with logo, tagline, chat card visual | |
| Illustration | Custom illustration of clinic/medical theme on green background | ✓ |
| You decide | Claude designs the left panel | |

**User's choice:** Illustration

---

## Role-Based Access (RBAC)

### Where role checks happen
| Option | Description | Selected |
|--------|-------------|----------|
| Both layers | FastAPI middleware enforces (source of truth) + Next.js hides UI elements (UX) | ✓ |
| Backend only | FastAPI enforces, frontend shows everything, gets 403 if unauthorized | |
| You decide | Claude picks standard approach | |

**User's choice:** Both layers (defense in depth)

### Super Admin role
| Option | Description | Selected |
|--------|-------------|----------|
| Not in v1 | Just Admin/Recepcionista/Medico. Platform management via database. | ✓ |
| Yes, add Super Admin | Fourth role that can manage all clinics | |
| You decide | Claude decides based on v1 scope | |

**User's choice:** Not in v1

### Post-login landing
| Option | Description | Selected |
|--------|-------------|----------|
| All land on Dashboard | Everyone sees dashboard first. Content adapts by role. | ✓ |
| Role-specific landing | Admin→Dashboard, Recepcionista→Agenda, Medico→My Agenda | |
| You decide | Claude picks best UX | |

**User's choice:** All land on Dashboard

---

## Tenant Isolation

### DB isolation approach
| Option | Description | Selected |
|--------|-------------|----------|
| PostgreSQL Row-Level Security | Add tenant_id + RLS policies. DB enforces isolation. Strongest guarantee. | ✓ |
| Application middleware filter | FastAPI middleware injects tenant_id. One missed WHERE = data leak. | |
| Separate schemas per tenant | Each clinic gets own PG schema. Perfect isolation but complex. | |
| You decide | Claude picks safest for raw SQL codebase | |

**User's choice:** PostgreSQL Row-Level Security

### Migration strategy
| Option | Description | Selected |
|--------|-------------|----------|
| Add tenant_id + backfill | ALTER TABLE ADD, backfill to default clinic, then enable RLS. Zero data loss. | ✓ |
| Fresh start | Drop and recreate tables. Cleaner but loses data. | |
| You decide | Claude picks safest path | |

**User's choice:** Add tenant_id + backfill to default clinic

### Migration tooling
| Option | Description | Selected |
|--------|-------------|----------|
| Yes, use Alembic | Already in requirements.txt. Set up migration chain now. | ✓ |
| Raw SQL scripts | Keep .sql files in migrations/. Simpler but no state tracking. | |
| You decide | Claude picks based on what's available | |

**User's choice:** Yes, use Alembic

---

## Claude's Discretion

- Login form error states and validation UX
- Exact CSRF protection mechanism
- JWT token expiration times and refresh strategy
- Alembic directory structure and naming conventions
- RLS policy syntax and testing approach
- Left-side illustration choice/style

## Deferred Ideas

None — discussion stayed within phase scope
