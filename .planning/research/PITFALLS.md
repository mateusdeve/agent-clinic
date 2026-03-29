# Pitfalls Research: MedIA Frontend

**Research Date:** 2026-03-29
**Domain:** Clinic Management SaaS — Common Mistakes

## Critical Pitfalls

### 1. Multi-Tenancy Data Leaks

**Risk Level:** CRITICAL
**Phase:** 2 (Auth + Multi-tenancy)

**What goes wrong:** A query forgets the `WHERE tenant_id = ?` filter. Clinic A sees Clinic B's patients. In healthcare, this is a LGPD/HIPAA violation with legal consequences.

**Warning signs:**
- Any raw SQL query without tenant_id filter
- API endpoint that doesn't extract tenant from JWT
- JOIN queries that cross tenant boundaries
- Admin endpoints that list all tenants' data

**Prevention strategy:**
- Implement tenant filtering at the ORM level (SQLAlchemy base query with auto-filter)
- Never pass tenant_id as a query parameter — always extract from JWT
- Write integration tests that create data for Tenant A and verify Tenant B can't see it
- Code review checklist: "Does every query filter by tenant_id?"

### 2. WhatsApp Takeover Race Conditions

**Risk Level:** HIGH
**Phase:** 4 (WhatsApp Panel)

**What goes wrong:** Human clicks "Take Over" at the same moment AI is generating a response. Both send messages to the patient simultaneously, causing confusion.

**Warning signs:**
- AI response arrives after takeover flag is set
- Two humans try to take over the same conversation
- Takeover flag not synced across all connected clients in real-time

**Prevention strategy:**
- Use database-level lock: `UPDATE conversations SET takeover_by = ? WHERE id = ? AND takeover_by IS NULL`
- AI agent checks takeover flag BEFORE sending (not just before generating)
- Socket.IO broadcasts takeover status immediately to all connected users
- Queue AI responses — if takeover happens during generation, discard the response
- Add 2-second grace period after takeover where AI responses are suppressed

### 3. WebSocket Connection Management

**Risk Level:** HIGH
**Phase:** 4 (WhatsApp Panel)

**What goes wrong:** User's browser loses connection, reconnects, and misses messages. Or connection stays "open" but is actually dead (zombie connection). Chat panel shows stale data.

**Warning signs:**
- Messages appear out of order after reconnect
- "Online" indicator shows online but user isn't receiving messages
- Memory leak from accumulating Socket.IO event listeners on reconnect

**Prevention strategy:**
- Socket.IO handles reconnection automatically — but sync state on reconnect
- On reconnect event: fetch missed messages via REST API (since last known message timestamp)
- Heartbeat every 30s to detect zombie connections
- Client-side: single Socket.IO instance managed by React context, not per-component
- Clean up event listeners on component unmount

### 4. Message Ordering and Deduplication

**Risk Level:** MEDIUM
**Phase:** 4 (WhatsApp Panel)

**What goes wrong:** Same message appears twice in the panel (WebSocket delivers it AND REST API fetch includes it). Or messages appear in wrong order when multiple arrive quickly.

**Warning signs:**
- Duplicate messages in conversation view
- Messages jumping positions as they arrive
- Timestamps inconsistent between WebSocket and REST data

**Prevention strategy:**
- Every message gets a unique ID (UUID) at creation time
- Frontend deduplicates by message ID before rendering
- Sort by server-side timestamp, not client arrival time
- TanStack Query cache update: merge WebSocket messages with existing cache, dedup by ID

### 5. Auth Token Expiry During Long Sessions

**Risk Level:** MEDIUM
**Phase:** 2 (Auth + Multi-tenancy)

**What goes wrong:** Receptionist opens the system in the morning, works all day. JWT expires at 4pm. Next API call fails with 401. Socket.IO disconnects. All unsaved state lost.

**Warning signs:**
- Random 401 errors after hours of use
- Socket.IO disconnect without user action
- Form submission fails because token expired mid-edit

**Prevention strategy:**
- Short-lived access token (15min) + long-lived refresh token (7 days)
- API client interceptor: on 401, refresh token, retry original request
- Socket.IO: include token in auth handshake, handle `connect_error` with token refresh
- NextAuth `jwt` callback handles refresh automatically
- Show toast notification on session refresh, not hard redirect to login

### 6. Landing Page Performance vs Dashboard Bundle

**Risk Level:** MEDIUM
**Phase:** 1 (Foundation)

**What goes wrong:** Landing page loads the entire dashboard JavaScript bundle. Page load goes from 0.5s to 4s. Google penalizes SEO score. Conversion drops.

**Warning signs:**
- Landing page bundle size > 200KB
- Dashboard components imported in landing page route
- Shared layout imports heavy dependencies

**Prevention strategy:**
- Route groups: `(landing)` and `(dashboard)` with separate layouts
- Landing page uses Server Components only (zero client JS except waitlist form)
- Dynamic imports for dashboard components: `dynamic(() => import('./HeavyChart'))`
- Verify with `next build` — check page sizes in build output
- Landing page should score 95+ on Lighthouse

### 7. LGPD/Privacy Compliance for Health Data

**Risk Level:** HIGH
**Phase:** 2+ (all phases)

**What goes wrong:** Patient health information stored without consent, shared across tenants, or exposed in logs/error messages. LGPD violation can result in fines up to 2% of revenue.

**Warning signs:**
- Patient names/CPF in server logs
- Error messages that include patient data
- No consent tracking for data processing
- Conversation data retained indefinitely

**Prevention strategy:**
- Never log patient PII (names, CPF, phone) — use anonymized IDs
- Implement data retention policy: conversations older than X months auto-archived
- Consent checkbox on patient registration (track in DB)
- Sanitize error messages before sending to frontend
- SSL/TLS everywhere (already standard but verify)
- Document data processing purposes (required by LGPD)

### 8. Evolution API Reliability

**Risk Level:** MEDIUM
**Phase:** 4 (WhatsApp Panel)

**What goes wrong:** Evolution API goes down or rate-limits. Messages fail silently. Patients think the clinic is ignoring them. Campaign sends partially — some patients get the message, others don't.

**Warning signs:**
- Increased 5xx errors from Evolution API
- Message send latency > 5 seconds
- Campaign completion percentage < 100%

**Prevention strategy:**
- Implement retry with exponential backoff for message sends
- Queue campaign messages (don't blast all at once)
- Rate limit: respect WhatsApp's per-number limits (~80 msgs/min)
- Show delivery status in WhatsApp panel (sent/delivered/read/failed)
- Alert admin when Evolution API error rate > threshold
- Store failed messages for manual retry

### 9. Dashboard Performance with Large Datasets

**Risk Level:** MEDIUM
**Phase:** 5 (Dashboard + Campaigns)

**What goes wrong:** Clinic has 10,000 patients, 50,000 conversations. Patient list takes 10 seconds to load. Dashboard metrics query times out. Conversation history search is unusable.

**Warning signs:**
- API response time > 2 seconds for list endpoints
- Frontend freezing during data rendering
- Browser memory usage growing unbounded

**Prevention strategy:**
- Server-side pagination for all list endpoints (never return full dataset)
- Database indexes on: (tenant_id, created_at), (tenant_id, patient_id), (tenant_id, status)
- Dashboard metrics: pre-computed daily/weekly aggregates (materialized views or cron)
- Conversation search: full-text search index in PostgreSQL (tsvector)
- Virtual scrolling for long lists (TanStack Virtual)
- TanStack Query: aggressive cache with background refetch

---
*Pitfalls research: 2026-03-29*
