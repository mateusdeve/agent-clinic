# Architecture Patterns

**Project:** MedIA — Clinic Management SaaS with AI WhatsApp Agent
**Dimension:** Frontend Integration Architecture
**Researched:** 2026-03-29
**Confidence:** HIGH (verified against official docs and multiple authoritative sources)

---

## Recommended Architecture

### System Overview

```
                        ┌─────────────────────────────────────┐
                        │         NEXT.JS FRONTEND             │
                        │                                     │
                        │  ┌──────────┐  ┌──────────────────┐ │
                        │  │ App      │  │ Route Handlers   │ │
                        │  │ Router   │  │ (API Proxy Layer) │ │
                        │  │ (Pages)  │  │ /api/*           │ │
                        │  └──────────┘  └────────┬─────────┘ │
                        │       │                 │           │
                        │  ┌────▼────────────────▼─────────┐ │
                        │  │     Auth Middleware (JWT)      │ │
                        │  │     Tenant Resolution          │ │
                        │  │     RBAC Route Guards          │ │
                        │  └────────────────────────────────┘ │
                        └─────────────────┬───────────────────┘
                                          │ HTTPS / SSE
                        ┌─────────────────▼───────────────────┐
                        │         FASTAPI BACKEND              │
                        │  (existing agent-service)            │
                        │                                     │
                        │  ┌──────────┐  ┌──────────────────┐ │
                        │  │ Webhook  │  │   NEW REST API   │ │
                        │  │ /webhook │  │   /api/v1/*      │ │
                        │  │ /evolution│  │   + SSE stream   │ │
                        │  └──────────┘  └──────────────────┘ │
                        │                        │            │
                        │  ┌─────────────────────▼──────────┐ │
                        │  │ Tenant Middleware (tenant_id)   │ │
                        │  │ JWT Verify (FastAPI Depends)    │ │
                        │  └────────────────────────────────┘ │
                        │                                     │
                        │  PostgreSQL  Redis  Evolution API   │
                        └─────────────────────────────────────┘
```

---

## Component Boundaries

| Component | Location | Responsibility | Communicates With |
|-----------|----------|---------------|-------------------|
| Next.js App Router Pages | `frontend/app/` | Renders SSR/CSR UI per role and route | Route Handlers, FastAPI (SSR fetch) |
| Next.js Route Handlers (API Proxy) | `frontend/app/api/` | Proxy to FastAPI; handle cookie-to-header JWT conversion; tenant injection | FastAPI REST API |
| Next.js Middleware | `frontend/middleware.ts` | JWT decode, RBAC route guard, redirect unauthorized | Auth cookies, Next.js router |
| Auth Module | `frontend/app/(auth)/` | Login/logout pages, session cookie issuance | FastAPI `/auth` endpoints |
| WhatsApp Panel | `frontend/app/(app)/whatsapp/` | Real-time conversation list + chat view, takeover toggle | SSE stream, POST /messages |
| Dashboard Module | `frontend/app/(app)/dashboard/` | Metrics, occupancy, confirmations KPIs | FastAPI REST (polling or SSE) |
| Agenda Module | `frontend/app/(app)/agenda/` | Calendar grid, slot blocking, rescheduling | FastAPI REST |
| Patients Module | `frontend/app/(app)/patients/` | Patient list, history, profile CRUD | FastAPI REST |
| Doctors Module | `frontend/app/(app)/doctors/` | Doctor profiles, specialties, availability | FastAPI REST |
| Admin Module | `frontend/app/(app)/admin/` | User CRUD, role assignment, tenant settings | FastAPI REST |
| Landing Page | `frontend/app/(marketing)/` | SEO landing page, WhatsApp CTA | Static + WhatsApp deep-link |
| FastAPI REST API (NEW) | `agent-service/src/api/rest.py` | Expose clinic data as tenant-scoped REST | PostgreSQL, Redis |
| FastAPI Auth Endpoints (NEW) | `agent-service/src/api/auth.py` | Issue/verify JWT, manage users/roles | PostgreSQL users table |
| FastAPI SSE Endpoint (NEW) | `agent-service/src/api/sse.py` | Push new WhatsApp messages to connected frontends | Redis pub/sub or PostgreSQL LISTEN |
| FastAPI Tenant Middleware (NEW) | `agent-service/src/api/tenant.py` | Extract tenant_id from JWT, scope all queries | FastAPI Depends chain |
| Existing Webhook + Agents | `agent-service/src/api/webhook.py` | Unchanged WhatsApp ingestion pipeline | Evolution API, Sofia/Carla agents |

---

## Data Flow

### 1. Authentication Flow

```
User → POST /api/auth/login (Next.js Route Handler)
  → Proxy to FastAPI POST /auth/token
  → FastAPI verifies credentials, issues JWT {user_id, tenant_id, role, exp}
  → Next.js sets HttpOnly cookie "session"
  → Next.js middleware reads cookie on every request
  → JWT decoded in middleware → RBAC check → allow/redirect
```

**Key decision:** JWT stored in HttpOnly cookie (not localStorage). Next.js middleware decodes it client-side using `jose` (edge-compatible). FastAPI receives JWT as Bearer token forwarded by the Route Handler proxy.

### 2. Standard REST Data Flow

```
Browser (Client Component)
  → fetch("/api/v1/appointments")      [same-origin, cookie auto-sent]
  → Next.js Route Handler              [reads cookie, forwards as Authorization: Bearer {jwt}]
  → FastAPI GET /api/v1/appointments   [TenantMiddleware extracts tenant_id from JWT]
  → SQL WHERE tenant_id = {tenant_id}  [PostgreSQL RLS or explicit filter]
  → JSON response → Route Handler → Browser
```

**Why proxy through Route Handler:** Keeps the FastAPI URL and API key hidden from the browser; centralizes token forwarding; allows request transformation.

### 3. Real-Time WhatsApp Panel Flow (SSE)

```
WhatsApp User → Evolution API → FastAPI POST /webhook/evolution
  → Orchestrator → Sofia + Carla agents process message
  → Message persisted to PostgreSQL (conversations table)
  → FastAPI publishes event to Redis channel "clinic:{tenant_id}:messages"
    [NEW: single line added after existing persistence step]
  → FastAPI SSE endpoint GET /api/v1/stream/conversations/{tenant_id}
    listens to Redis channel, yields ServerSentEvent per new message
  → Next.js EventSource("api/v1/stream") receives event
  → React state update → WhatsApp panel re-renders with new message
```

**Pattern:** SSE is the correct choice here. The panel only needs server→client push for new incoming messages. Client→server (sending messages, takeover toggle) uses normal HTTP POST. SSE works through Nginx/proxies with correct headers (FastAPI sets `X-Accel-Buffering: no` automatically from FastAPI 0.115+).

### 4. Human Takeover Flow

```
Receptionist clicks "Assume conversa" button
  → POST /api/v1/conversations/{phone}/takeover {action: "take"}
  → FastAPI sets Redis key "takeover:{tenant_id}:{phone}" = true, TTL = 4h
  → Webhook handler checks key before invoking Sofia graph
  → If takeover active: skip agent, only persist incoming message + mark for human reply
  → Receptionist types reply → POST /api/v1/conversations/{phone}/messages
  → FastAPI calls Evolution API directly (bypassing Sofia/Carla)
  → SSE broadcasts the sent message back to all connected staff panels
  → Release: DELETE /api/v1/conversations/{phone}/takeover → removes Redis key
```

### 5. Multi-Tenancy Data Flow

```
Every FastAPI request:
  1. TenantMiddleware reads JWT from Authorization header
  2. Decodes tenant_id (no DB lookup — embedded in JWT)
  3. Sets request.state.tenant_id
  4. All SQL queries in Tools/REST handlers append WHERE tenant_id = ?
  5. PostgreSQL RLS as secondary safety net (enforcement at DB level)
```

**Tenant identification strategy:** Single shared database, shared schema, `tenant_id` column on all tables. This is already the right model for the v1 scale. RLS policies on PostgreSQL add a defence-in-depth layer without changing application query code.

---

## Patterns to Follow

### Pattern 1: Next.js Route Handler as API Proxy

**What:** All browser→FastAPI calls go through `app/api/[...proxy]/route.ts` which forwards the request with the JWT from the HttpOnly cookie as a Bearer token.

**When:** Always — never expose the FastAPI base URL or credentials to the browser.

**Example:**
```typescript
// app/api/v1/[...path]/route.ts
export async function GET(req: Request, { params }: { params: { path: string[] } }) {
  const token = cookies().get("session")?.value
  const upstreamUrl = `${process.env.FASTAPI_URL}/api/v1/${params.path.join("/")}`
  const res = await fetch(upstreamUrl, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return new Response(res.body, { headers: res.headers })
}
```

### Pattern 2: Middleware-Based RBAC

**What:** `middleware.ts` runs at the Edge before every request. Decodes JWT (using `jose`, edge-compatible), checks role against a route permission map, redirects if unauthorized.

**When:** For route-level protection (e.g., `/admin/*` requires role=admin, `/agenda/*` requires role in [admin, receptionist]).

**Example:**
```typescript
// middleware.ts
import { jwtVerify } from "jose"
const ROLE_MAP: Record<string, string[]> = {
  "/admin": ["admin"],
  "/agenda": ["admin", "receptionist"],
  "/whatsapp": ["admin", "receptionist"],
  "/doctors": ["admin", "receptionist", "doctor"],
}
export async function middleware(request: NextRequest) {
  const token = request.cookies.get("session")?.value
  const { payload } = await jwtVerify(token, secret)
  const allowedRoles = ROLE_MAP[matchedPath]
  if (!allowedRoles.includes(payload.role)) return redirect("/unauthorized")
}
```

### Pattern 3: SSE for WhatsApp Panel Real-Time Updates

**What:** FastAPI exposes a `GET /api/v1/stream/conversations` SSE endpoint. Frontend connects with `EventSource`. On each new WhatsApp message (after Sofia/Carla pipeline), FastAPI publishes to a Redis pub/sub channel and the SSE handler yields it.

**When:** For the WhatsApp panel only. Dashboard metrics use 30-second polling (SWR with `refreshInterval`). Avoid SSE for everything — it's only worth the complexity for the inbox.

**FastAPI side:**
```python
# src/api/sse.py
@router.get("/stream/conversations", response_class=EventSourceResponse)
async def stream_conversations(
    request: Request,
    tenant_id: str = Depends(get_tenant_id),
) -> AsyncIterable[ServerSentEvent]:
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"clinic:{tenant_id}:messages")
    async for message in pubsub.listen():
        if await request.is_disconnected():
            break
        if message["type"] == "message":
            yield ServerSentEvent(data=message["data"], event="new_message")
```

**Next.js side:**
```typescript
// In WhatsApp panel component
useEffect(() => {
  const es = new EventSource("/api/v1/stream/conversations")
  es.addEventListener("new_message", (e) => {
    setConversations(prev => mergeMessage(prev, JSON.parse(e.data)))
  })
  return () => es.close()
}, [])
```

### Pattern 4: Tenant Context via FastAPI Dependency Injection

**What:** A single `get_tenant_id` dependency extracts and validates tenant context from the JWT for every protected endpoint.

**When:** Every endpoint under `/api/v1/` except `/auth`.

```python
# src/api/tenant.py
async def get_tenant_id(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    payload = verify_jwt(credentials.credentials)
    return payload["tenant_id"]

# Usage in any endpoint
@router.get("/appointments")
async def list_appointments(
    tenant_id: str = Depends(get_tenant_id),
    db: Connection = Depends(get_db),
):
    return await db.fetch("SELECT * FROM appointments WHERE tenant_id = $1", tenant_id)
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Calling FastAPI Directly from the Browser

**What:** Setting `NEXT_PUBLIC_FASTAPI_URL` and calling FastAPI from client components.

**Why bad:** Exposes backend URL, bypasses the proxy's auth forwarding, breaks tenant scoping, creates CORS complexity.

**Instead:** Always proxy through Next.js Route Handlers.

### Anti-Pattern 2: WebSockets for the WhatsApp Panel

**What:** Using `ws://` WebSocket connection for the conversation feed.

**Why bad:** WebSockets require a stateful server (can't run on Vercel serverless), add bidirectional complexity when the panel only needs server→client push, harder to proxy through Nginx.

**Instead:** SSE for push + HTTP POST for user-initiated actions (sending message, takeover). SSE is natively supported by FastAPI 0.115+ without extra libraries.

### Anti-Pattern 3: Storing JWT in localStorage

**What:** Saving the auth token in `localStorage` and reading it in client components.

**Why bad:** Vulnerable to XSS. The existing backend has no XSS surface but the React frontend will.

**Instead:** HttpOnly cookie set by Next.js Route Handler login endpoint. Middleware reads it at the Edge.

### Anti-Pattern 4: Trusting Frontend-Provided tenant_id

**What:** Accepting `tenant_id` as a query parameter or request body field from the client.

**Why bad:** Any user can set any `tenant_id` and access other clinics' data.

**Instead:** `tenant_id` extracted exclusively from the server-verified JWT in `get_tenant_id` dependency.

### Anti-Pattern 5: Modifying the Existing Webhook Flow

**What:** Changing `src/api/webhook.py` or the Sofia/Carla pipeline to add frontend features.

**Why bad:** The webhook flow is production-critical and handles live patient conversations. Changes introduce risk of breaking the AI agent.

**Instead:** Add the REST API and SSE as a separate FastAPI router (`include_router`). The only addition to the existing pipeline is a single Redis publish call after the existing `save_messages()` call in `orchestrator.py`.

---

## Suggested Build Order (Dependencies Between Components)

The build order follows strict dependency chains: auth gates everything, tenant scoping gates all data access, and real-time features depend on the base REST layer.

```
Phase 1 — Foundation (unblocks everything else)
  1a. FastAPI: users + roles + tenants table migrations
  1b. FastAPI: JWT auth endpoints (POST /auth/token, GET /auth/me)
  1c. FastAPI: TenantMiddleware + get_tenant_id dependency
  1d. Next.js: project scaffold (App Router, Tailwind, shadcn/ui)
  1e. Next.js: Auth middleware + login page + session cookie
  → Unblocks: ALL subsequent phases

Phase 2 — REST API Layer (needed before any dashboard page)
  2a. FastAPI: REST router for appointments, patients, doctors, agenda
  2b. FastAPI: Scope all queries with tenant_id
  2c. Next.js: Route Handler proxy (/api/v1/[...path])
  → Unblocks: All dashboard modules

Phase 3 — Core Dashboard Modules (parallel after Phase 2)
  3a. Dashboard page — metrics (uses REST, polling)
  3b. Agenda page — calendar + slot management
  3c. Patients page — list + profile
  3d. Doctors page — profiles + availability

Phase 4 — WhatsApp Panel (depends on Phase 2 + Redis pub/sub)
  4a. FastAPI: Redis publish on new message (1 line in orchestrator.py)
  4b. FastAPI: SSE endpoint /api/v1/stream/conversations
  4c. Next.js: WhatsApp panel with EventSource + conversation list
  4d. Next.js: Chat view with message history
  4e. FastAPI + Next.js: Human takeover toggle (Redis key + REST endpoints)

Phase 5 — Admin + Multi-Tenancy Management
  5a. FastAPI: User CRUD endpoints + role assignment
  5b. Next.js: Admin module (requires admin role guard)
  5c. Next.js: Tenant onboarding flow (clinic registration)

Phase 6 — Landing Page (independent, can be done any time after Phase 1d)
  6a. Next.js: Marketing landing page (SSG, SEO)
  6b. WhatsApp deep-link CTA button
```

**Critical path:** 1a → 1b → 1c → 1d → 1e → 2a → 2b → 2c → any Phase 3/4/5 work.

Phase 6 (landing page) has no dependency on Phase 2+ and can be parallelized from Phase 1d onwards.

---

## Scalability Considerations

| Concern | At 10 clinics | At 100 clinics | At 1,000 clinics |
|---------|--------------|----------------|-----------------|
| Tenant isolation | tenant_id column + app-level filter | Add PostgreSQL RLS policies | Consider schema-per-tenant for top-tier plans |
| SSE connections | In-process asyncio fine | Redis pub/sub per-tenant channel (already recommended) | Add dedicated SSE service or use managed push (Pusher/Ably) |
| Database | Single PostgreSQL | Connection pooling (PgBouncer) | Read replicas per region |
| Auth | Stateless JWT (no DB hit per request) | Same | Add token revocation list in Redis |
| WhatsApp instances | Single Evolution instance | Multiple instances, route by tenant | Evolution cluster or per-tenant instance |

---

## Sources

- FastAPI Server-Sent Events (native support): https://fastapi.tiangolo.com/tutorial/server-sent-events/ (HIGH confidence — official docs)
- Next.js Route Handlers as proxy: https://nextjs.org/docs/app/getting-started/route-handlers (HIGH confidence — official docs)
- Next.js middleware RBAC pattern: https://www.jigz.dev/blogs/how-to-use-middleware-for-role-based-access-control-in-next-js-15-app-router (MEDIUM confidence)
- SSE vs WebSockets for dashboards (95% cases prefer SSE): https://dev.to/polliog/server-sent-events-beat-websockets-for-95-of-real-time-apps-heres-why-a4l (MEDIUM confidence — widely corroborated)
- Multi-tenancy shared schema with tenant_id pattern: https://mvpfactory.io/blog/row-level-security-in-postgresql-multi-tenant-data-isolation-for-your-saas (MEDIUM confidence)
- FastAPI multi-tenancy with dependency injection: https://mergeboard.com/blog/6-multitenancy-fastapi-sqlalchemy-postgresql/ (MEDIUM confidence)
- NextAuth + FastAPI JWT integration: https://tom.catshoek.dev/posts/nextauth-fastapi/ (MEDIUM confidence)
- WhatsApp human takeover architecture: https://www.mitchellbryson.com/articles/whatsapp-ai-customer-support-agent (MEDIUM confidence)
- Next.js + FastAPI full-stack template (Vinta): https://github.com/vintasoftware/nextjs-fastapi-template (MEDIUM confidence)

---

*Architecture research: 2026-03-29*
