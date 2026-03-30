---
phase: 04-whatsapp-panel
plan: 01
subsystem: backend
tags: [socketio, realtime, conversations, takeover, webhooks]
dependency_graph:
  requires: [02-auth-multi-tenancy, redis, evolution-api]
  provides: [socketio-server, conversations-api, takeover-mechanism]
  affects: [webhook, orchestrator, run_api]
tech_stack:
  added: [python-socketio==5.16.1]
  patterns:
    - ASGIApp wrapping FastAPI for Socket.IO + REST on same port
    - Redis flag pattern for takeover state (zero-latency, no DB round-trip)
    - Lazy imports inside function bodies to avoid circular import (socketio_server ↔ webhook)
    - asyncio.ensure_future for non-blocking broadcast calls from sync-ish orchestrator paths
key_files:
  created:
    - agent-service/src/api/socketio_server.py
    - agent-service/src/api/conversations.py
    - agent-service/tests/test_conversations.py
  modified:
    - agent-service/requirements.txt
    - agent-service/run_api.py
    - agent-service/src/api/webhook.py
    - agent-service/src/api/orchestrator.py
    - agent-service/tests/conftest.py
decisions:
  - "python-socketio cors_allowed_origins=[] prevents duplicate CORS headers with FastAPI CORSMiddleware"
  - "Takeover check in webhook_evolution BEFORE handle_message dispatch — prevents Sofia responding during human control"
  - "Lazy imports inside function bodies for socketio_server in webhook.py and conversations.py — solves circular import"
  - "Module-level redis_client in socketio_server.py — shared by conversations router and webhook without re-initialization"
  - "broadcast_typing_indicator for both True (Sofia starts) and False (Sofia done) in orchestrator — panel shows real-time typing state"
metrics:
  duration: "5min"
  completed_date: "2026-03-30"
  tasks_completed: 3
  files_modified: 7
---

# Phase 04 Plan 01: Socket.IO Backend Infrastructure Summary

**One-liner:** Socket.IO AsyncServer wrapping FastAPI ASGI app with 5-endpoint conversations REST router and Redis takeover mechanism for AI/human control switching.

## What Was Built

Backend real-time infrastructure for the WhatsApp inbox panel:

1. **socketio_server.py** — Socket.IO AsyncServer with JWT authentication in connect handler, per-phone rooms (`conv:{phone}`), shared Redis client, and 3 broadcast helpers: `broadcast_new_message`, `broadcast_conversation_updated`, `broadcast_typing_indicator`.

2. **conversations.py** — REST router with 5 endpoints:
   - `GET /api/conversations` — inbox list with search, last message preview, Redis-derived status
   - `GET /api/conversations/{phone}/messages` — full message history (LIKE pattern for session_id variants)
   - `POST /api/conversations/{phone}/send` — sends via Evolution API, stores in DB, broadcasts
   - `POST /api/conversations/{phone}/takeover` — sets Redis `takeover:{phone}` without TTL (D-08)
   - `POST /api/conversations/{phone}/handback` — deletes Redis flag, broadcasts `ia_ativa`

3. **webhook.py** modifications:
   - Import and mount `conversations_router`
   - Takeover check BEFORE `handle_message` dispatch (critical ordering per D-10)
   - `_handle_inbound_takeover` for patient messages during human control
   - Inbound patient message broadcast in normal flow (WPP-04)

4. **orchestrator.py** modifications:
   - `broadcast_typing_indicator(phone, True)` at start of buffer flush processing
   - Bot response broadcast via `broadcast_new_message` after Sofia responds
   - `broadcast_typing_indicator(phone, False)` after all messages sent

5. **Test infrastructure** — 6 xfail test stubs + mock_redis, mock_sio, mock_evolution fixtures in conftest.py.

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Socket.IO server + uvicorn entry point update | 216a5c9 |
| 2 | Conversations REST router + webhook takeover bypass + bot broadcast | 423c18f |
| 3 | Test stubs + mock fixtures | 704fd16 |

## Known Stubs

None — all endpoints are wired to real implementations. Test stubs are intentionally xfail (contract tests awaiting auth fixtures for full integration testing in Phase 4 Plan 2/3).

## Self-Check

Files created:
- agent-service/src/api/socketio_server.py ✓
- agent-service/src/api/conversations.py ✓
- agent-service/tests/test_conversations.py ✓
