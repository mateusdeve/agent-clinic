# Codebase Concerns

**Analysis Date:** 2026-03-29

## Tech Debt

**Synchronous Database Operations in Async Context:**
- Issue: Multiple database operations use blocking psycopg2 connections without proper thread pooling, called from async code via `asyncio.to_thread()`. This creates potential thread pool saturation under high load.
- Files: `src/api/orchestrator.py`, `src/core/extraction.py`, `src/memory/persistence.py`, `src/tools/appointments.py`, `src/tools/patients.py`, `src/tools/doctors.py`, `src/tools/followup.py`
- Impact: Performance degradation, potential message processing delays, incomplete error propagation from database layer
- Fix approach: Migrate to async PostgreSQL driver (asyncpg) or implement dedicated connection pool with proper bounds. Refactor `_get_db()` context manager pattern across all tool modules.

**Duplicated Database Connection Context Managers:**
- Issue: Every tool module (`appointments.py`, `patients.py`, `doctors.py`, `followup.py`) reimplements `_get_db()` context manager instead of using centralized connection management.
- Files: `src/memory/persistence.py` (singleton pattern), `src/tools/appointments.py`, `src/tools/doctors.py`, `src/tools/patients.py`, `src/tools/followup.py`
- Impact: Inconsistent error handling, difficult to change connection strategy, code duplication
- Fix approach: Create `src/db/connection.py` with single source of truth for database access. Update all modules to import from there.

**Broad Exception Catching Without Recovery:**
- Issue: Most database and API operations catch `Exception` generically with only logging, no retry logic or graceful degradation strategy.
- Files: `src/api/orchestrator.py` (lines 158-165, 273-274), `src/api/evolution.py` (lines 56, 69, 113, 144), `src/tools/appointments.py` (60-62, 99-100, 132-134, 168-170), `src/tools/followup.py` (79-80, 112-114, 127-128), `src/memory/persistence.py` (48-49, 84-85, 105-106), `src/memory/rag.py` (40-41, 69-70)
- Impact: Transient failures (network hiccups, database unavailability) silently fail; patient may see generic error instead of retry or meaningful feedback
- Fix approach: Implement retry decorator with exponential backoff for API calls. Separate transient errors (network) from permanent errors (validation). Add circuit breaker for Evolution API calls.

**Unhandled State Consistency Between Redis and Database:**
- Issue: Session state persists in Redis with 24h TTL, but appointment data lives in PostgreSQL. If appointment updates during session, Redis state becomes stale.
- Files: `src/api/session.py` (lines 14-15, 50-60), `src/api/orchestrator.py` (lines 180-190, 262-265)
- Impact: Patient may see outdated appointment availability or confirmation. Session ends and clears Redis, losing recovery capability.
- Fix approach: Implement transaction-like coordination: before confirming appointment, reload latest state from DB. Add version/checksum to Redis state. Implement idempotent re-run logic.

**Blocking LLM Calls in Async Pipeline:**
- Issue: All LLM invocations (`extract_data()`, `graph.invoke()`, `carla_graph.invoke()`, summarization) run via `asyncio.to_thread()` without timeout or cancellation support. A hanging LLM call blocks the thread pool.
- Files: `src/core/extraction.py` (104-133), `src/api/orchestrator.py` (200, 223, 244, 259), `src/agent/nodes.py` (43-63), `src/memory/summarizer.py` (33-47)
- Impact: One slow LLM response can cascade to delay other patient messages if thread pool exhausted. No per-message timeout enforcement.
- Fix approach: Add request timeouts to all LLM calls. Implement asyncio timeout wrapper around `to_thread()` calls. Add circuit breaker if error rate from LLM exceeds threshold.

**Redis Connection Not Closed Properly:**
- Issue: `SessionManager.__init__()` creates `aioredis.from_url()` connection but never explicitly closes it. Connection leaks if SessionManager is recreated or on shutdown.
- Files: `src/api/session.py` (lines 19-20), `src/api/webhook.py` (lines 30)
- Impact: Connection exhaustion over time, memory leaks in long-running deployment
- Fix approach: Add `async def close()` method to SessionManager. Call from webhook shutdown handler. Use context manager or AsyncExitStack for safer lifecycle.

**Timestamp Parsing Fragility:**
- Issue: `_parse_appointment_datetime()` in followup.py uses dateparser with fuzzy Portuguese parsing. No validation that parsed datetime is in future or reasonable range. Could misinterpret dates.
- Files: `src/tools/followup.py` (lines 11-24)
- Impact: Follow-ups scheduled for wrong time or past date. Users see reminder for already-passed appointment.
- Fix approach: Add validation: check parsed datetime is in future, within 1 year, same timezone as clinic. Add logging of parsing input/output. Test with edge cases.

**Stateful Graph Singletons Without Thread Safety:**
- Issue: Sofia and Carla graphs are global singletons (`_sofia_graph`, `_carla_graph`) initialized once. If initialization fails, fallback returns None. No recovery. Also not explicitly thread-safe.
- Files: `src/api/orchestrator.py` (lines 35-37, 60-69)
- Impact: Graph initialization exception silently fails, subsequent calls crash with AttributeError. Multi-threaded access could hit race condition during initialization.
- Fix approach: Use thread-safe lazy initialization (e.g., `threading.Lock` in `_get_graphs()`). Add explicit error handling to raise informative exception if graph build fails. Pre-warm graphs at startup.

**Carla Formatting Decisions Not Validated:**
- Issue: Carla graph breaks text into messages (`mensagens_quebradas`) but there's no guarantee structure matches what Evolution API expects. No schema validation.
- Files: `src/api/orchestrator.py` (lines 259), `src/api/evolution.py` (lines 169-192)
- Impact: Malformed message structure could be sent to WhatsApp, resulting in delivery failure or confusing presentation
- Fix approach: Add TypedDict or Pydantic model for message structure. Validate in `send_messages()` before sending. Log rejected messages.

---

## Known Bugs

**Assistant Name Collision Detection Incomplete:**
- Symptoms: If patient introduces themselves as "Sofia", ambiguity arises between patient name and agent name. Extraction detects this, but state reconciliation may not catch all cases.
- Files: `src/core/extraction.py` (lines 64-101), `src/api/orchestrator.py` (lines 238)
- Trigger: Patient says "sou a Sofia" or similar when agent is named Sofia
- Workaround: System logs detection, but false positives still possible if patient name happens to be Carla or Sofia. Manual state inspection required.

**Message Buffer Sequence Number Race in High Throughput:**
- Symptoms: Multiple messages arrive in rapid succession; sequence increment not atomic. Last flush may process wrong set of messages if timing aligns poorly.
- Files: `src/api/orchestrator.py` (lines 103-104, 135-137)
- Trigger: 10+ messages in <1 second from same patient
- Workaround: Current implementation relies on `asyncio.Lock` per phone, which helps but doesn't guarantee atomicity of seq check + buffer read

**Embedding Model Hardcoded in RAG:**
- Symptoms: RAG uses embedding model configured in `_get_embeddings()` but uses OpenRouter API. If embeddings change (e.g., switch to local or different provider), existing vectors in DB become incompatible.
- Files: `src/memory/rag.py` (lines 8-14)
- Trigger: Switching `EMBEDDING_MODEL` env var; re-indexing doesn't happen automatically
- Workaround: Manual re-index all knowledge_chunks required; documented process missing

---

## Security Considerations

**Environment Variables Logged in Error Messages:**
- Risk: Exception messages may include or reference DATABASE_URL, OPENROUTER_API_KEY, EVOLUTION_API_KEY if exposed in logs.
- Files: `src/memory/persistence.py` (line 16), `src/tools/appointments.py` (line 19), `src/tools/doctors.py` (line 20), `src/api/webhook.py` (line 108)
- Current mitigation: Error messages are generic ("DATABASE_URL não configurado"), but full stack traces could leak if captured by external logging service
- Recommendations: Sanitize exception messages before logging. Use structured logging with redaction rules. Never log full database URLs or API keys.

**Patient Data in Redis Without Encryption:**
- Risk: Session state including patient name, phone, appointment details stored in plain text in Redis. If Redis is exposed or logs are captured, patient PII is compromised.
- Files: `src/api/session.py` (lines 50-60), `src/api/webhook.py` (line 30 - REDIS_URL from env)
- Current mitigation: Redis TTL of 24h limits window. Assumes Redis server access is restricted.
- Recommendations: Enable Redis encryption at rest (`requirepass`). Use TLS for Redis connection. Consider encrypting sensitive fields in session state before persistence. Audit Redis access logs.

**API Key in Headers Not Validated:**
- Risk: Evolution API key passed in HTTP headers (`_headers()`) without TLS certificate pinning. Man-in-the-middle could intercept key.
- Files: `src/api/evolution.py` (lines 37-41, 53-54, 67-68)
- Current mitigation: Assumes HTTPS connection is used (httpx default)
- Recommendations: Add certificate pinning for Evolution API endpoint. Validate domain name in certificate. Add request signing if Evolution API supports it.

**Patient Phone Number Used as Session Key:**
- Risk: Phone numbers are personally identifiable and used directly as Redis key (`session:{phone}`). If Redis is compromised, attacker knows phone → session mapping.
- Files: `src/api/session.py` (line 29), `src/api/orchestrator.py` (lines 40, 43, 45)
- Current mitigation: Session IDs are derived from phone but not hashed
- Recommendations: Hash phone numbers for session keys. Use anonymous session IDs. Implement session lookup table with encryption.

---

## Performance Bottlenecks

**LLM Extraction on Every Turn:**
- Problem: Every message triggers `extract_data()` which calls LLM. With 5-10 turn conversations, that's 5-10 LLM API calls. Even at 2s per call, feels slow.
- Files: `src/api/orchestrator.py` (line 200), `src/core/extraction.py` (104-133)
- Cause: No caching of extracted fields. State is loaded from Redis but extraction runs fresh each turn.
- Improvement path: Cache extraction results indexed by message content hash. Invalidate only when new human message added. Implement incremental extraction (only extract new fields).

**Synchronous Database Queries Block Async Loop:**
- Problem: `asyncio.to_thread()` calls for DB operations consume thread pool. If 10+ concurrent patients, thread pool can saturate.
- Files: `src/api/orchestrator.py` (multiple `asyncio.to_thread()` calls), all database operations
- Cause: psycopg2 is synchronous; no async driver used
- Improvement path: Switch to asyncpg (async PostgreSQL driver). Implement connection pooling with bounded size.

**RAG Retrieval on Every Message:**
- Problem: `retrieve_context()` queries vector database on every turn, even if recent context was already retrieved.
- Files: `src/agent/nodes.py` (lines 95-103)
- Cause: No caching mechanism; every message triggers `_rag.retrieve()`
- Improvement path: Cache last retrieved context. Only re-query if significant time elapsed or conversation topic changed. Use simple keyword-based cache invalidation.

**No Batch Processing for Followups:**
- Problem: `dispatch_followups()` runs every 5 minutes, retrieves pending, sends one-by-one with delays. If 50+ pending, takes 5+ minutes total.
- Files: `src/api/webhook.py` (lines 35-48)
- Cause: Sequential sending with `EVOLUTION_SEND_DELAY` (1 second) between messages
- Improvement path: Implement worker pool or queue (e.g., Celery, RQ). Batch send to Evolution API if supported. Increase frequency of follow-up dispatch, send in parallel with per-phone rate limiting.

---

## Fragile Areas

**Message State Machine Transitions:**
- Files: `src/core/extraction.py` (lines 136-193)
- Why fragile: `determine_etapa()` has complex conditional logic with multiple interacting flags (nome, motivo, especialidade, data, horario, medico_mencionado, etapa_atual, agendamento_concluido). Edge cases: what if patient hasn't given name but gave specialty? What if they confirm but haven't given all data? Difficult to reason about all paths.
- Safe modification: Write state transition tests covering all flag combinations. Use formal state machine library or decision table instead of nested ifs. Document each transition requirement clearly.
- Test coverage: `determine_etapa()` lacks unit tests. Add test matrix for all state combinations.

**Patient Name Recognition:**
- Files: `src/core/extraction.py` (lines 46-100), `src/api/orchestrator.py` (lines 190-194)
- Why fragile: Two separate mechanisms detect patient name: LLM extraction (can be wrong) and database lookup by phone (depends on exact match). If patient name changes or is misspelled, both fail. False positive for "Sofia" name still possible even with mitigation.
- Safe modification: Add confidence score to LLM extraction. Cross-reference with DB lookup. Log conflicts for manual review. Add explicit "confirm name?" step if high uncertainty.
- Test coverage: No test for name collision. Add integration test with Sofia/Carla patient names.

**Evolution API Response Handling:**
- Files: `src/api/evolution.py` (lines 72-147)
- Why fragile: Error handling is catch-all; response validation is minimal. If Evolution API changes response format or adds new status codes, code breaks silently.
- Safe modification: Add strict response schema validation. Log full response for debugging. Implement version check for API. Add timeout handling.
- Test coverage: No mocking of Evolution API in tests. Add integration tests with mock responses.

**Langfuse Integration:**
- Files: `src/observability/langfuse_setup.py`, `src/agent/nodes.py` (lines 138-145), `src/api/orchestrator.py` (lines 276-279)
- Why fragile: Langfuse initialization can fail silently. Spans are opened but exception handling is minimal. If Langfuse is down, traces are dropped without retry.
- Safe modification: Add explicit initialization check at startup. Implement buffering for failed traces. Add timeout and fallback for Langfuse calls.
- Test coverage: No tests for Langfuse failures. Add mock Langfuse service test.

**Carla Graph Message Formatting:**
- Files: `src/agent_carla/nodes.py` (106 lines), `src/api/orchestrator.py` (lines 259-262)
- Why fragile: Carla's output structure (`mensagens_quebradas`) is not validated. If Carla graph changes or fails, message list could be empty, malformed, or missing required keys.
- Safe modification: Add schema validation. Test Carla graph output. Add fallback if structure is invalid.
- Test coverage: No test of Carla graph output format.

---

## Scaling Limits

**Redis Session Storage Linear with Active Conversations:**
- Current capacity: Single Redis instance with default memory. No sharding strategy.
- Limit: At ~1KB per session, 1GB Redis = ~1M sessions. But practical limit lower (~100-500K concurrent) due to connection overhead, default memory allocations.
- Scaling path: Implement Redis cluster or sentinel. Use Redis Streams for high-volume scenarios. Consider moving ephemeral session state to in-memory cache (memcached) and keeping only critical data in Redis.

**PostgreSQL Connections Exhausted Under Load:**
- Current capacity: psycopg2 opens new connection per database call. Default max_connections in PostgreSQL ~100.
- Limit: >100 concurrent API requests trigger "too many connections" errors. Blocks message processing.
- Scaling path: Implement pgBouncer or similar connection pooler. Migrate to asyncpg with proper connection pool. Set reasonable pool size limits.

**LLM API Rate Limits:**
- Current capacity: OpenRouter API has rate limits (varies by model). Each turn triggers 1-2 LLM calls.
- Limit: High-traffic deployment hits OpenRouter rate limit after ~100-200 concurrent conversations (depending on model).
- Scaling path: Implement request queuing/batching. Add fallback model. Cache common prompts/responses. Use cheaper model variants for simple operations.

**Evolution API Send Rate Limits:**
- Current capacity: Evolution API likely has per-instance throttling (typically 100-300 msgs/min).
- Limit: >5-10 concurrent patient conversations can hit send rate limits, causing message delays.
- Scaling path: Implement message queue (e.g., Celery, Bull). Respect Evolution API rate limits. Batch follow-up sending. Request higher tier with Evolution if available.

---

## Dependencies at Risk

**langchain and langgraph Rapid Evolution:**
- Risk: Both are pre-1.0, API changes frequently. Current requirements pin specific versions but no CI to detect breaking upgrades.
- Impact: Dependency updates can break graph execution, state handling, or message format.
- Migration plan: Add version constraint tests. Pin to major.minor version, allow patch updates only. Monitor release notes. Set up CI to test against latest minor version.

**OpenRouter API as LLM Provider (No Redundancy):**
- Risk: Single point of failure for all LLM calls. OpenRouter outage stops entire system.
- Impact: Patients cannot get responses. Followups don't send. Extraction fails.
- Migration plan: Implement fallback to another LLM provider (e.g., OpenAI direct, Anthropic). Add circuit breaker to detect OpenRouter unavailability. Support local models as fallback.

**Evolution API Dependency for WhatsApp:**
- Risk: Evolution API changes or becomes unavailable. No alternative WhatsApp integration layer.
- Impact: Cannot send/receive WhatsApp messages. Deployment is broken.
- Migration plan: Abstract Evolution API behind interface. Support multiple WhatsApp providers (e.g., official WhatsApp Business API). Test failover.

---

## Missing Critical Features

**No Persistent Task Queue:**
- Problem: Follow-ups and reminders dispatched from single webhook instance. If server crashes, pending follow-ups are lost (Redis TTL expires).
- Blocks: Cannot guarantee delivery. No retry on failure. Cannot scale to multiple servers.
- Fix: Implement persistent queue (Celery, RQ) with proper acknowledgment and retry. Store follow-ups durably, re-trigger if not acknowledged.

**No Monitoring/Alerting:**
- Problem: System logs to console/file, but no alerting for errors, timeouts, or performance degradation. No dashboards.
- Blocks: Ops team cannot detect issues proactively. Can only react to customer complaints.
- Fix: Integrate structured logging to centralized platform (ELK, Datadog). Add alerts for critical errors, LLM failures, API timeouts. Add metrics (message latency, success rate).

**No Graceful Degradation:**
- Problem: If Redis unavailable, session state lost and patient starts fresh. If LLM unavailable, responds with generic error. If database down, cannot load patient history.
- Blocks: No fallback behavior. Cannot operate in degraded mode.
- Fix: Implement fallback storage (local cache, in-memory), fallback LLM (cheaper model), offline capabilities (canned responses for FAQ). Design system to handle service degradation.

**No Audit Trail for Compliance:**
- Problem: Patient appointments and changes not logged in immutable format for compliance (GDPR, healthcare regulations).
- Blocks: Cannot prove what was promised to patient. Cannot recover from data corruption.
- Fix: Add audit table logging all patient interactions, appointment changes, consent given. Sign audit records. Implement retention policy.

---

## Test Coverage Gaps

**Untested State Machine Logic:**
- What's not tested: `determine_etapa()` function with all state combinations. Transition paths under edge cases (missing data, conflicting inputs).
- Files: `src/core/extraction.py` (lines 136-193)
- Risk: Bug in state machine silently routes patient to wrong conversation phase. Undetected until production.
- Priority: High

**No Integration Tests for API Pipeline:**
- What's not tested: End-to-end message flow from webhook to response. Multi-turn conversations. Session state persistence.
- Files: `src/api/webhook.py`, `src/api/orchestrator.py`, `src/api/session.py`
- Risk: Regressions in orchestrator logic undetected. Race conditions in message buffering not caught.
- Priority: High

**Untested Error Recovery:**
- What's not tested: What happens when LLM fails? Database unavailable? Evolution API timeout? Partial graph execution?
- Files: `src/api/orchestrator.py` (158-165), all database operations
- Risk: Silent failures, confusing error states, customer impact unknown.
- Priority: Medium

**Evolution API Response Validation:**
- What's not tested: Response format from Evolution API, error responses, edge cases (null fields, malformed JSON).
- Files: `src/api/evolution.py`
- Risk: Unexpected response format causes exception, message not sent.
- Priority: Medium

**RAG and Memory Components:**
- What's not tested: Retrieval quality, embedding consistency, persistence of summaries, cleanup of old sessions.
- Files: `src/memory/rag.py`, `src/memory/persistence.py`, `src/memory/summarizer.py`
- Risk: Memory leaks, stale data retrieved, search results irrelevant.
- Priority: Medium

**Carla Graph Output:**
- What's not tested: Message structure validation, empty output handling, very long text segmentation.
- Files: `src/agent_carla/nodes.py`
- Risk: Malformed messages sent, chat experience broken.
- Priority: Low

---

*Concerns audit: 2026-03-29*
