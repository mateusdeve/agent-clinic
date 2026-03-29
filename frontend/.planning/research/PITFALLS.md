# Domain Pitfalls

**Domain:** Clinic management SaaS with AI WhatsApp agent — adding web frontend + multi-tenancy to existing Python/FastAPI backend
**Researched:** 2026-03-29
**Confidence:** HIGH (database schema read directly, backend code analyzed, multi-source verified)

---

## Critical Pitfalls

Mistakes that cause rewrites, data breaches, or production incidents.

---

### Pitfall 1: No tenant_id on Existing Tables — Schema Migration Blindspot

**What goes wrong:** The existing database tables (`appointments`, `patients`, `follow_ups`, `doctors`, `doctor_schedules`) have zero multi-tenancy columns. Every row is identified by `phone` number alone. Adding a second clinic to the system means their data immediately co-mingles with the first clinic's data — same `appointments` table, same `patients` table, no partition.

**Why it happens:** The backend was built single-tenant (one clinic, one Evolution API instance). Developers add a frontend and assume "we'll add tenant_id later." Later never comes cleanly — it requires a migration, a backfill of all rows, a change to every query, and an update to the Redis session key space.

**Consequences:** Cross-clinic data leaks (clinic A's receptionist sees clinic B's patients), appointment double-booking across clinics, broken follow-up dispatch that fires to wrong patients.

**Prevention:**
- Add `clinic_id UUID NOT NULL` (or `tenant_id`) to ALL tables in the very first migration before any real data enters.
- Apply PostgreSQL Row-Level Security (RLS) policies at the database layer, not just application layer. A single forgotten WHERE clause in application code cannot leak data when RLS is enforced at Postgres.
- Pattern: `SET app.current_tenant = $1` per request, then `USING (clinic_id = current_setting('app.current_tenant')::uuid)` on every table policy.
- The existing Redis session key `session:{phone}` must become `session:{clinic_id}:{phone}` — otherwise session state from one clinic's patients is readable by the other clinic's backend process.

**Detection:** Try logging into a second-clinic account and calling any list endpoint — if it returns data, the isolation is broken.

**Phase:** Foundation / Phase 1 (schema) — this cannot be retrofitted cheaply after data exists.

---

### Pitfall 2: Exposing the WhatsApp Webhook to the Frontend — Auth Boundary Confusion

**What goes wrong:** The existing `/webhook/evolution` endpoint has no authentication — it is designed to receive unauthenticated POST requests from the Evolution API. When a frontend is added, developers may accidentally route frontend API traffic through the same FastAPI app without establishing a clear auth boundary, or expose the webhook URL publicly without signing verification.

**Why it happens:** It is tempting to add `/api/v1/*` frontend routes to the same FastAPI app as the webhook, blurring the boundary between "unauthenticated webhook receiver" and "authenticated frontend API."

**Consequences:** Replay attacks where anyone can POST fabricated WhatsApp messages; frontend routes become accessible without auth; or the webhook gets locked behind auth and the Evolution API callbacks start failing.

**Prevention:**
- Separate concerns: the webhook receiver validates a shared secret (HMAC signature or static API key header from Evolution). Frontend API routes require JWT. Use FastAPI's dependency injection to enforce this cleanly per router.
- Use a prefix-based separation: `/webhook/*` requires Evolution API key; `/api/v1/*` requires JWT Bearer token.
- Consider splitting into two separate FastAPI apps (webhook service stays lightweight, frontend API lives separately) if the codebase grows.

**Detection:** Can you call `POST /webhook/evolution` from a browser with arbitrary JSON and get `{"status": "processing"}`? If yes, the boundary is not enforced.

**Phase:** Phase 1 (auth + API setup).

---

### Pitfall 3: WebSocket Connection Proliferation in the Chat Panel

**What goes wrong:** A real-time WhatsApp conversation panel requires WebSocket (or SSE) for live message delivery to the browser. A common React mistake is opening a new WebSocket connection per component mount — so when the user navigates between conversations (each mounting a `<ConversationPanel>`), multiple concurrent connections accumulate. This is expensive server-side and creates duplicate message delivery.

**Why it happens:** Developers write `new WebSocket(url)` inside a `useEffect` hook without a global singleton or connection pool. Each component that mounts creates its own socket.

**Consequences:** Server memory grows linearly with user navigation actions; messages appear duplicated; reconnection storms when the user switches tabs; billing spikes if using a managed WebSocket service.

**Prevention:**
- Maintain a single WebSocket connection per authenticated session (browser tab), managed as a React context or global store (Zustand/Redux singleton).
- Multiplex conversation subscriptions over one connection via a room/channel model: `subscribe({type: "conversation", id: phone})`.
- Implement heartbeat/ping-pong to detect stale connections before they cause silent data gaps.
- When the connection drops, fetch missed messages via REST before re-subscribing (don't assume WS delivery is reliable).

**Detection:** Open DevTools Network tab, navigate between 5 conversations — if there are 5+ open WebSocket connections, the problem exists.

**Phase:** Phase 2 (real-time panel).

---

### Pitfall 4: Redis Session State Is Not Tenant-Scoped — Cross-Clinic Session Contamination

**What goes wrong:** The existing `SessionManager` stores state at key `session:{phone}`. Two different clinics that share a Redis instance and both have a patient with the same phone number (e.g., `5511999999999`) will overwrite each other's session state. The second clinic's conversation picks up mid-flow from the first clinic's agent state.

**Why it happens:** Phone number as the sole session key was sufficient for a single-clinic deployment. The abstraction did not anticipate a shared Redis cluster serving multiple tenants.

**Consequences:** Patient greets the wrong AI persona (Sofia instead of another clinic's configured agent), agent flow jumps to wrong `etapa`, personal health data leaks across clinic boundaries.

**Prevention:**
- Change key format to `session:{clinic_id}:{phone}` from day one of multi-tenancy work.
- Pass `clinic_id` through the entire call chain: webhook payload → `handle_message` → `SessionManager`.
- If Redis is shared across tenants, use key prefixes AND Redis ACLs so each clinic's application role can only access its own key namespace.

**Detection:** Two tenants with the same test phone number — does session.load_state return the correct clinic's state?

**Phase:** Phase 1 (multi-tenancy foundation).

---

### Pitfall 5: Timezone Handling — Appointments Stored as Strings, Displayed Wrong

**What goes wrong:** The `appointments` table stores `appointment_date` as `VARCHAR(50)` and `appointment_time` as `VARCHAR(10)` — plain text strings, not `TIMESTAMPTZ`. The frontend will need to display these, allow filtering by date, and potentially sort them. String-based dates break chronological ordering (lexicographic vs. calendar order), break timezone conversion, and cause off-by-one errors when the clinic is in Brazil (America/Sao_Paulo, UTC-3) but the server logs in UTC.

**Why it happens:** During the initial AI agent build, dates were captured from natural language ("próxima terça-feira de manhã") and stored as-is for display. A proper calendar system was out of scope.

**Consequences:** Frontend shows appointments in wrong order; follow-up scheduler fires at wrong local time; "today's appointments" query returns wrong results at midnight UTC (which is 9pm in Sao Paulo).

**Prevention:**
- During the frontend phase, migrate `appointment_date`/`appointment_time` columns to a single `appointment_at TIMESTAMPTZ` column. All queries use UTC internally; display layer converts to `America/Sao_Paulo` using `Intl.DateTimeFormat` or `date-fns-tz`.
- Never store "next Tuesday" as a display string — resolve it to an ISO date at ingestion time.
- Brazil abolished DST in 2019 (fixed UTC-3 year-round), simplifying timezone math — but some older libraries still have stale DST rules for Brazil. Verify library timezone database version.

**Detection:** Book an appointment at 23:30 BRT — does it show up under "today" or "tomorrow" in the dashboard?

**Phase:** Phase 1 (schema) + Phase 2 (frontend display layer).

---

### Pitfall 6: LGPD / Patient Data Exposure in the Frontend

**What goes wrong:** The frontend displays patient names, phone numbers, conversation history, and health-related information (insurance, reason for visit, symptoms). If the frontend API does not enforce field-level access control, a receptionist role can access the same data as a clinic administrator, or API responses include raw patient data that gets logged in browser developer tools or error trackers (Sentry, LogRocket).

**Why it happens:** LGPD (Brazil's GDPR equivalent) is treated as a backend concern. Frontend developers integrate analytics, error tracking, or logging libraries without sanitizing PHI (personally identifiable health information) from payloads.

**Consequences:** LGPD compliance violation; patient data in third-party error tracker logs; junior staff accessing sensitive consultation notes they should not see.

**Prevention:**
- Define role-based access at the API layer: receptionists get `{name, phone, appointment_time}` only; admins get full record.
- Sanitize error tracking payloads — configure Sentry/equivalent to scrub fields matching `phone`, `cpf`, `nome_paciente`, `motivo_consulta` before transmission.
- Do not log conversation text in browser console in production builds.
- Patient conversation history requires explicit access justification and should be paginated/lazy-loaded, never bulk-exported from the frontend.

**Detection:** Check what fields a Sentry error event captures when a fetch to `/api/conversations` fails — does it include PHI in the request body or response context?

**Phase:** Phase 1 (auth/roles) + Phase 2 (conversation panel) + Phase 3 (observability).

---

## Moderate Pitfalls

---

### Pitfall 7: Optimistic UI Causing Message Duplication in the Conversation Panel

**What goes wrong:** The conversation panel sends a message (e.g., operator override) optimistically, appending it to the UI immediately. The WebSocket then delivers the server-confirmed message. Without deduplication logic, the message appears twice.

**Prevention:**
- Assign a client-generated `tempId` to optimistically inserted messages. When the WS event arrives with a server-assigned `id`, replace the temp entry by matching on `tempId`. Never add a message to the list if a matching `id` already exists.
- Use a `Map<id, message>` as the canonical store rather than an array.

**Phase:** Phase 2 (real-time panel).

---

### Pitfall 8: APScheduler Follow-Up Dispatcher Runs on Multiple Instances

**What goes wrong:** The follow-up scheduler inside `webhook.py` uses APScheduler running in-process. When the backend scales to 2+ instances (replicas), each instance runs its own scheduler. The same follow-up row gets dispatched 2x or 3x — the patient receives duplicate messages.

**Why it happens:** In-process scheduling is not distributed. The `enviado` flag check in `marcar_enviado` has a TOCTOU (time-of-check-time-of-use) race condition under concurrent execution.

**Consequences:** Patients receive duplicate WhatsApp follow-up messages; `enviado` flag is set twice; confusing conversation history in the frontend.

**Prevention:**
- Use SELECT ... FOR UPDATE SKIP LOCKED when claiming follow-up rows to ensure only one instance processes each row.
- Alternatively, move the scheduler to a dedicated worker process (Celery Beat, pg_cron, or a standalone APScheduler service) rather than embedding it in the HTTP server.
- At minimum, add a database-level unique constraint or advisory lock on the follow-up dispatch.

**Phase:** Phase 1 (backend hardening before frontend exposes multi-instance deployment).

---

### Pitfall 9: Langfuse Traces Contain Cross-Tenant Data in Shared Instance

**What goes wrong:** If Langfuse is self-hosted and shared across multiple clinic tenants (to save cost), traces from Clinic A are visible to Clinic B's admin if the Langfuse project is not separated per tenant. Even with separate Langfuse projects, trace metadata must not include raw patient names or phone numbers.

**Prevention:**
- One Langfuse project per clinic (tenant), with separate API keys.
- Pass `clinic_id` (not patient name/phone) as trace metadata. Use opaque identifiers in traces.
- If using Langfuse Cloud, verify their data isolation and LGPD/GDPR compliance posture.

**Phase:** Phase 3 (AI observability dashboard).

---

### Pitfall 10: CORS Wildcard Origin With Credentials

**What goes wrong:** FastAPI's `CORSMiddleware` with `allow_origins=["*"]` and `allow_credentials=True` is rejected by browsers. Developers then set `allow_origins=["*"]` without credentials, which silently drops Authorization headers, causing 401 errors on every authenticated request.

**Prevention:**
- Always enumerate exact origins: `allow_origins=["https://app.yourclinic.com"]`.
- In development, use `["http://localhost:5173"]` explicitly. Never use wildcard in production.
- The `Authorization` header must be in `allow_headers`.

**Phase:** Phase 1 (API integration).

---

### Pitfall 11: Agent State Leaking Between Conversations in the Singleton Graph

**What goes wrong:** The LangGraph `_sofia_graph` and `_carla_graph` are initialized as module-level singletons. If graph nodes accidentally write to shared module state (rather than to the passed `state` dict), concurrent requests for different phone numbers can corrupt each other's conversation state.

**Why it happens:** A developer adds a "global cache" variable at module level inside `nodes.py` to avoid re-querying the database, but accidentally shares it across invocations.

**Prevention:**
- All state must flow through the LangGraph `state` TypedDict, never through module-level variables.
- Audit `nodes.py` and `agent_carla/nodes.py` for any mutable module-level variables before scaling beyond 1 worker.
- Add integration tests that run two concurrent conversations for different phone numbers and assert no state cross-contamination.

**Phase:** Phase 1 (backend hardening).

---

## Minor Pitfalls

---

### Pitfall 12: Unread Count Badge Goes Stale After WebSocket Reconnect

**What goes wrong:** The sidebar conversation list shows unread badges. When the WebSocket reconnects after a brief disconnect, missed messages are not backfilled, so badges show the count from before the disconnect.

**Prevention:**
- On reconnect, re-fetch the full conversation list (or unread summary) via REST before re-subscribing to WebSocket events.
- Unread count is server-authoritative; never compute it solely from client-side event accumulation.

**Phase:** Phase 2 (real-time panel).

---

### Pitfall 13: Phone Number Format Inconsistency Between WhatsApp and Database

**What goes wrong:** Evolution API delivers phone as `5511999999999@s.whatsapp.net`. The `_clean_phone` method strips the suffix. But the `patients` table uses `phone TEXT PRIMARY KEY` with whatever format was first inserted. If one code path inserts `5511999999999` and another inserts `11999999999` (without country code), the same patient appears as two records and recognition fails.

**Prevention:**
- Canonicalize all phone numbers to E.164 format (`+5511999999999`) at the point of first contact — both in the database and in Redis keys.
- Write a single `normalize_phone(raw: str) -> str` utility and use it at every ingestion boundary.

**Phase:** Phase 1 (data model).

---

### Pitfall 14: React Query / SWR Refetch-on-Window-Focus Hammering the AI Conversation Endpoint

**What goes wrong:** React Query's default `staleTime: 0` and `refetchOnWindowFocus: true` cause the conversation history endpoint to be re-fetched every time the user switches browser tabs. For a clinic receptionist managing 20 active chats, this fires 20 concurrent requests on every tab switch.

**Prevention:**
- Set `staleTime` to a reasonable value (e.g., 30 seconds) for conversation history queries.
- Use WebSocket-driven cache invalidation: only refetch when a new message WS event arrives for that conversation, not on focus.

**Phase:** Phase 2 (real-time panel).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Schema migration for multi-tenancy | No tenant_id on existing tables (#1) | Add clinic_id to ALL tables in first migration, apply RLS |
| Redis session scoping | Cross-clinic session contamination (#4) | Change key to `session:{clinic_id}:{phone}` |
| Auth layer on existing FastAPI | Webhook/API boundary confusion (#2) | Separate routers with different auth dependencies |
| Real-time chat panel (WebSocket) | Connection proliferation (#3) | Singleton WS context, room-based subscriptions |
| Appointment display | Timezone bugs with VARCHAR dates (#5) | Migrate to TIMESTAMPTZ, display in America/Sao_Paulo |
| Patient data in frontend | LGPD exposure (#6) | Role-based field projection, scrub PHI from error trackers |
| Multi-instance deployment | APScheduler duplicate follow-ups (#8) | SELECT FOR UPDATE SKIP LOCKED or dedicated scheduler worker |
| AI observability dashboard | Cross-tenant Langfuse traces (#9) | One project per clinic, opaque identifiers in trace metadata |
| API integration | CORS wildcard with credentials (#10) | Enumerate origins explicitly |
| Conversation panel UI | Optimistic message duplication (#7) | tempId → server-id replacement, Map-based dedup |

---

## Sources

- [Multi-Tenant SaaS Architecture Mistakes — SaaSAdviser](https://www.saasadviser.co/blog/multi-tenant-saas-architecture-mistakes-best-practices)
- [Multi-Tenant Data Isolation with PostgreSQL RLS — AWS](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
- [Postgres RLS Implementation Guide — Permit.io](https://www.permit.io/blog/postgres-rls-implementation-guide)
- [Multi-Tenant Leakage: When RLS Fails — Medium/InstaTunnel](https://medium.com/@instatunnel/multi-tenant-leakage-when-row-level-security-fails-in-saas-da25f40c788c)
- [Multi-Tenant Architecture with FastAPI — Medium/Koushik Sathish](https://medium.com/@koushiksathish3/multi-tenant-architecture-with-fastapi-design-patterns-and-pitfalls-aa3f9e75bf8c)
- [How to Avoid Multiple WebSocket Connections in React — GetStream](https://getstream.io/blog/websocket-connections-react/)
- [Using WebSockets with React Query — Dominik Dorfmeister](https://tkdodo.eu/blog/using-web-sockets-with-react-query)
- [Data Isolation in Multi-Tenant SaaS with Redis — Redis.io](https://redis.io/blog/data-isolation-multi-tenant-saas/)
- [Brazil DST Bug Case Study — DEV Community](https://dev.to/arthurmde/the-bolsonaro-s-bug-the-end-of-daylight-saving-time-in-brazil-may-affect-your-system-2e38)
- [Timezones and Timestamps in Medical Scheduling — Medplum](https://www.medplum.com/docs/scheduling/timezones)
- [Multi-Tenant AI Leakage: Isolation Challenges — LayerX Security](https://layerxsecurity.com/generative-ai/multi-tenant-ai-leakage/)
- [AI Agent Security Risks — Obsidian Security](https://www.obsidiansecurity.com/blog/ai-agent-security-risks)
- [CORS Configuration in FastAPI — FastAPI Docs](https://fastapi.tiangolo.com/tutorial/cors/)
- [Agentic AI Data Breach Affects 483,000 Patients — BankInfoSecurity](https://www.bankinfosecurity.com/agentic-ai-tech-firm-says-health-data-leak-affects-483000-a-28424)
