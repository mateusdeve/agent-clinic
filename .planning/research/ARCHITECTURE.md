# Architecture Research: MedIA Frontend

**Research Date:** 2026-03-29
**Domain:** Clinic Management SaaS — Frontend Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Next.js Frontend                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Landing   │  │ Auth     │  │ Dashboard App     │  │
│  │ Page (SSG)│  │ (NextAuth│  │ (Client-side SPA) │  │
│  │           │  │  + JWT)  │  │                   │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
│                      │                │               │
│              REST API calls    Socket.IO connection   │
└──────────────┬───────────────────┬───────────────────┘
               │                   │
┌──────────────▼───────────────────▼───────────────────┐
│              FastAPI Backend (Python)                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Auth API │  │ REST API │  │ Socket.IO Server  │  │
│  │ (JWT)    │  │ (CRUD)   │  │ (Real-time msgs)  │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Multi-   │  │ Agent    │  │ Evolution API     │  │
│  │ Tenancy  │  │ Pipeline │  │ Integration       │  │
│  │ MW       │  │ (Sofia+  │  │                   │  │
│  │          │  │  Carla)  │  │                   │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
└──────────────┬───────────────────┬───────────────────┘
               │                   │
    ┌──────────▼──────┐   ┌───────▼────────┐
    │  PostgreSQL     │   │  Redis         │
    │  (multi-tenant) │   │  (sessions)    │
    └─────────────────┘   └────────────────┘
```

## Frontend-Backend Integration

### REST API (CRUD Operations)

**Pattern:** Next.js client components → fetch() → FastAPI REST endpoints

- All API calls go through a centralized `api` client with interceptors
- JWT token attached to every request via Authorization header
- tenant_id embedded in JWT — backend filters all queries automatically
- TanStack Query manages caching, refetching, and optimistic updates

**Key Endpoints Needed:**

| Group | Endpoints | Used By |
|-------|-----------|---------|
| Auth | POST /auth/login, /auth/register, /auth/refresh, /auth/me | Login page, session refresh |
| Patients | GET/POST/PUT/DELETE /patients | Patient management |
| Appointments | GET/POST/PUT/DELETE /appointments | Agenda views |
| Doctors | GET/POST/PUT/DELETE /doctors | Doctor management |
| Users | GET/POST/PUT/DELETE /users | User management (admin) |
| Dashboard | GET /dashboard/metrics | Dashboard charts |
| Conversations | GET /conversations, /conversations/:id/messages | WhatsApp history |
| Templates | GET/POST /templates, POST /campaigns/send | Message campaigns |
| Tenants | GET/PUT /tenants/current | Clinic settings |

### Socket.IO (Real-time)

**Pattern:** Persistent WebSocket connection per authenticated user

**Server-side (Python):**
- python-socketio mounted on FastAPI ASGI app
- Namespaces: `/whatsapp` for conversation streaming
- Rooms: one room per tenant (clinic) for broadcast
- Events: `new_message`, `conversation_updated`, `takeover_started`, `takeover_ended`

**Client-side (Next.js):**
- Socket.IO client connects after authentication
- Auto-joins tenant room based on JWT
- Messages streamed to TanStack Query cache via `queryClient.setQueryData()`
- Reconnection handled automatically by Socket.IO

**Takeover Flow:**
1. Receptionist clicks "Take Over" on conversation
2. Frontend emits `start_takeover` event with conversation_id
3. Backend sets flag on conversation → AI agent stops responding
4. Backend broadcasts `takeover_started` to all connected users in tenant
5. Human messages sent via REST POST /conversations/:id/messages
6. Backend routes through Evolution API (same as AI would)
7. When done, emit `end_takeover` → AI resumes

## Multi-Tenancy Architecture

### Strategy: Row-Level Isolation with tenant_id

Every table gets a `tenant_id` column. Every query is filtered.

**Implementation layers:**

1. **JWT Token:** Contains `tenant_id`, `user_id`, `role`
2. **FastAPI Middleware:** Extracts tenant_id from JWT, attaches to request state
3. **Database Layer:** All queries include `WHERE tenant_id = :tenant_id`
4. **SQLAlchemy:** Base query class that auto-filters by tenant_id

**Migration plan for existing tables:**
- Add `tenant_id` column to: patients, appointments, doctors, conversations, knowledge_chunks, followups
- Create default tenant for existing data
- Add composite indexes on (tenant_id, id) for all tables

### Tenant Onboarding

1. Landing page capture → WhatsApp conversation with sales AI
2. Sales closes → Admin creates tenant via internal tool
3. Tenant gets: clinic name, Evolution API instance, initial admin user
4. Admin logs in → sets up doctors, schedule, customize AI agent

## Authentication & Authorization

### Auth Flow

```
1. User enters email/password on login page
2. NextAuth CredentialsProvider calls FastAPI POST /auth/login
3. FastAPI validates credentials, returns JWT with {user_id, tenant_id, role}
4. NextAuth stores JWT in encrypted httpOnly cookie
5. On each API call, Next.js middleware reads cookie, attaches JWT to headers
6. FastAPI validates JWT, extracts tenant context
```

### Role-Based Access Control (RBAC)

| Feature | Admin | Receptionist | Doctor |
|---------|-------|-------------|--------|
| Dashboard (full) | Yes | Limited | No |
| WhatsApp conversations | Yes | Yes | No |
| Takeover conversations | Yes | Yes | No |
| Templates/Campaigns | Yes | Yes | No |
| Patient management | Yes | Yes | View own |
| Appointment management | Yes | Yes | View own |
| Doctor management | Yes | No | View own |
| User management | Yes | No | No |
| Clinic settings | Yes | No | No |
| AI agent config | Yes | No | No |

**Implementation:**
- Next.js middleware checks role on route access
- FastAPI endpoints check role via dependency injection
- UI hides/shows features based on role from session

## Component Architecture (Next.js)

### Route Structure

```
app/
├── (landing)/              # Public landing page group
│   ├── page.tsx            # Landing page (SSG)
│   └── layout.tsx          # Minimal layout (no sidebar)
├── (auth)/                 # Auth pages group
│   ├── login/page.tsx
│   └── register/page.tsx
├── (dashboard)/            # Authenticated app group
│   ├── layout.tsx          # Sidebar + header layout
│   ├── page.tsx            # Dashboard overview
│   ├── agenda/page.tsx     # Appointment calendar
│   ├── patients/
│   │   ├── page.tsx        # Patient list
│   │   └── [id]/page.tsx   # Patient detail
│   ├── whatsapp/
│   │   ├── page.tsx        # Conversation inbox
│   │   └── [id]/page.tsx   # Conversation detail
│   ├── campaigns/page.tsx  # Templates & campaigns
│   ├── doctors/page.tsx    # Doctor management
│   ├── users/page.tsx      # User management (admin)
│   └── settings/page.tsx   # Clinic settings (admin)
└── api/auth/[...nextauth]/ # NextAuth API routes
```

### Key Shared Components

- `<Sidebar />` — Navigation with role-based menu items
- `<DataTable />` — Reusable TanStack Table wrapper
- `<ConversationPanel />` — WhatsApp-style chat viewer
- `<MetricsCard />` — Dashboard KPI card
- `<ScheduleGrid />` — Weekly/daily appointment grid

## Suggested Build Order

**Phase 1: Foundation** (no dependencies)
- Next.js project setup, Tailwind config, shadcn/ui
- Design system (colors from site.html, typography, spacing)
- Landing page (SSG, waitlist → WhatsApp redirect)

**Phase 2: Auth + Multi-tenancy** (depends on Phase 1)
- FastAPI auth endpoints + JWT
- NextAuth integration
- Multi-tenancy middleware + DB migration
- Login/register pages
- Protected route layout with sidebar

**Phase 3: Core CRUD** (depends on Phase 2)
- REST API endpoints (patients, doctors, appointments)
- Patient management pages
- Doctor management pages
- Appointment/agenda views

**Phase 4: WhatsApp Panel** (depends on Phase 2)
- Socket.IO server on FastAPI
- Conversation list + detail views
- Real-time message streaming
- Manual takeover flow

**Phase 5: Dashboard + Campaigns** (depends on Phase 3 + 4)
- Dashboard metrics API
- Charts and KPI cards
- Template management
- Campaign dispatch

**Phase 6: Polish** (depends on all)
- User management (admin)
- Clinic settings
- Responsive design
- Error handling + loading states

---
*Architecture research: 2026-03-29*
