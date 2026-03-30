# Phase 4: WhatsApp Panel - Research

**Researched:** 2026-03-30
**Domain:** Real-time WebSocket inbox with Socket.IO, Redis takeover flag, 3-column layout
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Socket.IO — python-socketio on FastAPI + socket.io-client on Next.js. Auto-reconnect, rooms per conversation, namespace isolation.
- **D-02:** 3 core events: `new_message` (message arrived), `conversation_updated` (status/takeover changed), `typing_indicator` (someone is typing). Minimal event surface covering all WPP requirements.
- **D-03:** Socket.IO server mounts on the existing FastAPI ASGI app. Authenticated connections use JWT from session.
- **D-04:** 3-column layout: left=conversation list with search, center=message thread (chat bubbles), right=patient info sidebar (name, phone, last visit, appointments). Like WhatsApp Web with patient context.
- **D-05:** Conversation list sorted by latest message first. Filter tabs: Todas | IA Ativa | Humano | Resolvida. Search by patient name/phone (WPP-05).
- **D-06:** Chat bubble style reuses the WhatsApp timeline pattern from Phase 3 patient profile. Green=outgoing (bot or human), white=incoming (patient).
- **D-07:** Takeover state stored as Redis flag per conversation: `takeover:{phone}` → `{human_id, human_name, timestamp}`. Webhook checks this flag BEFORE invoking Sofia pipeline. Instant check, no DB round-trip.
- **D-08:** No auto-expire — human stays in control until explicitly clicking "Devolver para IA". Prevents accidental AI responses mid-human conversation.
- **D-09:** Socket.IO broadcasts `conversation_updated` on takeover/handback. All connected users see the status indicator change immediately (WPP-11).
- **D-10:** During takeover mode (WPP-10): webhook receives message from patient → stores in DB → broadcasts via Socket.IO to panel → does NOT invoke Sofia. Human responds via panel → Evolution API sends → stored in DB → broadcasts.
- **D-11:** Text input at bottom of thread. Enter sends, Shift+Enter for newline. No rich media in v1 — text only.
- **D-12:** Send flow: FastAPI endpoint receives text → calls Evolution API `send_message` → stores in conversations table → broadcasts `new_message` via Socket.IO.
- **D-13:** Sent messages appear in thread immediately via Socket.IO (optimistic UI), with delivery confirmation updated after Evolution API responds.

### Claude's Discretion

- Socket.IO namespace naming and room strategy
- Reconnection backoff settings
- Conversation list item preview (last message snippet length)
- Status indicator visual design (badge colors, icons)
- Thread scroll behavior on new messages
- Mobile responsive behavior for 3-column layout
- Unread message count per conversation
- Sound/notification for new messages

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WPP-01 | Recepcionista ve lista de conversas em tempo real via WebSocket | Socket.IO `new_message` + `conversation_updated` events push updates to conversation list without polling |
| WPP-02 | Recepcionista pode abrir conversa e ler historico completo de mensagens | GET `/api/conversations/{phone}/messages` endpoint backed by `conversations` table, existing `get_patient_conversations` pattern |
| WPP-03 | Conversas mostram indicador de status: IA ativa / takeover humano / resolvida | Redis `takeover:{phone}` flag read by new conversation list endpoint; status derived at query time |
| WPP-04 | Novas mensagens aparecem em tempo real sem recarregar a pagina | `new_message` Socket.IO event broadcast from webhook + send endpoint |
| WPP-05 | Recepcionista pode buscar conversas por nome/telefone do paciente | SQL LIKE filter on patient name + phone in conversation list query |
| WPP-06 | Painel lateral mostra info do paciente junto com a conversa | GET `/api/patients/{id}` existing endpoint + appointments endpoint; sidebar reads patient by phone lookup |
| WPP-07 | Recepcionista pode clicar "Assumir" para desativar IA naquela conversa | POST `/api/conversations/{phone}/takeover` → sets Redis `takeover:{phone}` → broadcasts `conversation_updated` |
| WPP-08 | Recepcionista pode enviar mensagens como humano pelo painel | POST `/api/conversations/{phone}/send` → Evolution API → DB insert → Socket.IO broadcast |
| WPP-09 | Recepcionista pode clicar "Devolver para IA" para reativar o bot | POST `/api/conversations/{phone}/handback` → deletes Redis flag → broadcasts `conversation_updated` |
| WPP-10 | IA nao responde enquanto conversa esta em modo takeover | `webhook.py` checks `takeover:{phone}` BEFORE calling `handle_message`; if flag exists, store only + broadcast |
| WPP-11 | Indicador visual mostra que conversa esta em modo humano para todos os usuarios conectados | `conversation_updated` broadcast on takeover/handback; all connected clients update their list state |
| API-04 | FastAPI integra Socket.IO para streaming de mensagens WhatsApp em tempo real | python-socketio 5.16.1 AsyncServer + ASGIApp wrapper; run_api.py changed to use `socket_app` as entry point |
</phase_requirements>

---

## Summary

Phase 4 adds a real-time WhatsApp inbox by integrating python-socketio onto the existing FastAPI ASGI app. The socket server wraps the FastAPI app using `socketio.ASGIApp(sio, other_asgi_app=app)` and must be the uvicorn entry point. The existing `run_api.py` must change from `"src.api.webhook:app"` to a new `socket_app` ASGI object. CORS is handled exclusively by FastAPI's existing `CORSMiddleware` — `python-socketio` must be initialized with `cors_allowed_origins=[]` to prevent duplicate CORS headers.

The takeover mechanism is pure Redis: `takeover:{phone}` is a Redis hash key storing `{human_id, human_name, timestamp}`. The existing webhook's `_parse_evolution_payload` + dispatch path gets a check inserted at the top of `_process_message`: if the flag exists, skip Sofia, store message, broadcast. This is a surgical 5-line insertion. The inbox page at `/whatsapp` drops into the existing dashboard shell. The 3-column layout uses the existing `WhatsAppTimeline.tsx` bubble component in the center column unchanged.

**Primary recommendation:** Mount Socket.IO as `socketio.ASGIApp(sio, other_asgi_app=app)`, change uvicorn entry point to the combined app, initialize sio with `cors_allowed_origins=[]`, use `auth` handshake parameter for JWT token, one namespace `/inbox`, rooms named by phone number.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-socketio | 5.16.1 | Socket.IO server (AsyncServer + ASGIApp) | Official Python Socket.IO impl; ASGI mode for FastAPI |
| python-engineio | 4.13.1 | Transport layer (auto-installed with python-socketio) | Required transitive dep |
| socket.io-client | 4.8.3 | Browser Socket.IO client | Matches server protocol version; auto-reconnect built in |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| redis (existing) | 7.3.0 (aioredis) | Takeover flag storage + read in webhook | Already installed; session pattern already established |
| lucide-react (existing) | 1.7.0 | Icons for takeover/handback buttons | Already installed in frontend |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| socket.io-client | native WebSocket | Socket.IO adds namespaces, rooms, reconnect, fallback — worth the dep |
| Redis hash for takeover | DB row | Redis is zero-latency; DB round-trip on every webhook adds ~5ms per message |
| Socket.IO | Server-Sent Events (SSE) | SSE is unidirectional; cannot push typing indicators bidirectionally |

**Installation (backend):**
```bash
cd agent-service
pip install python-socketio==5.16.1
echo "python-socketio==5.16.1" >> requirements.txt
```

**Installation (frontend):**
```bash
cd frontend
npm install socket.io-client@4.8.3
```

**Version verification:**
```bash
# Python
curl -s "https://pypi.org/pypi/python-socketio/json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['info']['version'])"
# Node
npm view socket.io-client version
```
Both verified 2026-03-30: python-socketio=5.16.1, socket.io-client=4.8.3.

---

## Architecture Patterns

### Recommended Project Structure

```
agent-service/src/api/
├── webhook.py          # MODIFIED: adds takeover check + Socket.IO broadcast
├── socketio_server.py  # NEW: sio = AsyncServer(...); socket_app = ASGIApp(sio, app)
├── conversations.py    # NEW: REST endpoints for inbox list, send, takeover, handback
├── orchestrator.py     # UNCHANGED (takeover bypass in webhook, not here)
└── session.py          # UNCHANGED (takeover uses same Redis client)

frontend/src/
├── lib/
│   └── socket.ts       # NEW: "use client"; singleton socket factory
├── hooks/
│   └── useSocket.ts    # NEW: React hook managing socket lifecycle + events
└── app/(dashboard)/
    └── whatsapp/
        ├── page.tsx                    # NEW: route entry, server component
        └── _components/
            ├── InboxPanel.tsx          # NEW: 3-column layout shell
            ├── ConversationList.tsx    # NEW: left column — list + search + filter tabs
            ├── ConversationThread.tsx  # NEW: center column — wraps WhatsAppTimeline + send bar
            ├── PatientSidebar.tsx      # NEW: right column — patient info condensed
            └── TakeoverBar.tsx         # NEW: prominent takeover/handback button strip
```

### Pattern 1: Socket.IO + FastAPI ASGI Mounting

**What:** Wrap FastAPI app inside `socketio.ASGIApp`. Uvicorn runs the wrapper, not FastAPI directly.
**When to use:** Every python-socketio + FastAPI integration.
**Example:**
```python
# agent-service/src/api/socketio_server.py
# Source: https://github.com/miguelgrinberg/python-socketio/blob/main/examples/server/asgi/fastapi-fiddle.py
import socketio
from src.api.webhook import app  # existing FastAPI app

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],  # CRITICAL: empty list — FastAPI CORSMiddleware handles CORS
)

# Combined ASGI app — this is what uvicorn must run
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
```

**run_api.py change:**
```python
# Before: "src.api.webhook:app"
# After:  "src.api.socketio_server:socket_app"
uvicorn.run("src.api.socketio_server:socket_app", host="0.0.0.0", port=8000, reload=True)
```

### Pattern 2: Socket.IO JWT Authentication via connect event

**What:** Client passes JWT in `auth` option at connection time. Server validates in `connect` handler and rejects with `False` if invalid.
**When to use:** All authenticated Socket.IO connections.
**Example:**
```python
# agent-service/src/api/socketio_server.py
import jwt, os
from fastapi import HTTPException

@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    if not token:
        return False  # reject connection
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        # Store user context on session
        await sio.save_session(sid, {
            "user_id": payload["sub"],
            "tenant_id": payload["tenant_id"],
            "role": payload["role"],
        })
    except Exception:
        return False  # reject connection
```

```typescript
// frontend/src/lib/socket.ts
"use client";
import { io, Socket } from "socket.io-client";

const SOCKET_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let socket: Socket | null = null;

export function getSocket(token: string): Socket {
  if (!socket) {
    socket = io(SOCKET_URL + "/inbox", {
      auth: { token },
      reconnectionDelayMax: 10000,
      transports: ["websocket"],
    });
  }
  return socket;
}

export function disconnectSocket() {
  socket?.disconnect();
  socket = null;
}
```

### Pattern 3: Rooms per Conversation

**What:** When a user opens a conversation, the client emits `join_conversation`. Server calls `sio.enter_room(sid, phone)`. Broadcasts for that phone target the room.
**When to use:** Ensures `new_message` events for a conversation only go to users watching that conversation. The `conversation_updated` event (takeover/status) is broadcast to all connected clients (no room filter needed).

```python
@sio.event
async def join_conversation(sid, data):
    """data = {"phone": "5511999999999"}"""
    phone = data.get("phone", "")
    await sio.enter_room(sid, f"conv:{phone}")

@sio.event
async def leave_conversation(sid, data):
    phone = data.get("phone", "")
    await sio.leave_room(sid, f"conv:{phone}")

# Broadcasting from REST endpoint or webhook:
async def broadcast_new_message(phone: str, message: dict):
    await sio.emit("new_message", message, room=f"conv:{phone}")

async def broadcast_conversation_updated(conversation: dict):
    await sio.emit("conversation_updated", conversation)  # all clients
```

### Pattern 4: Takeover Flag in Redis

**What:** Redis hash key `takeover:{phone}` stores human_id, human_name, timestamp. Webhook checks for existence before invoking Sofia.
**When to use:** Every inbound webhook message processing.

```python
# Reading takeover flag (async redis already available via SessionManager)
async def get_takeover(redis, phone: str) -> dict | None:
    raw = await redis.get(f"takeover:{phone}")
    if not raw:
        return None
    import json
    return json.loads(raw)

async def set_takeover(redis, phone: str, human_id: str, human_name: str):
    import json, time
    await redis.set(f"takeover:{phone}", json.dumps({
        "human_id": human_id,
        "human_name": human_name,
        "timestamp": time.time(),
    }))  # No TTL — cleared only by explicit handback (D-08)

async def clear_takeover(redis, phone: str):
    await redis.delete(f"takeover:{phone}")
```

**Webhook integration (surgical insert into webhook.py):**
```python
@app.post("/webhook/evolution")
async def webhook_evolution(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    phone, text = _parse_evolution_payload(payload)
    if not phone or not text:
        return {"status": "ignored"}

    # Check takeover flag BEFORE dispatching to Sofia pipeline
    takeover = await session_manager.redis.get(f"takeover:{phone}")
    if takeover:
        # Store message in DB + broadcast to panel — skip Sofia
        background_tasks.add_task(handle_inbound_takeover, phone=phone, text=text)
        return {"status": "takeover_mode"}

    background_tasks.add_task(handle_message, phone=phone, text=text, ...)
    return {"status": "processing"}
```

### Pattern 5: Conversation List API Query

**What:** New GET `/api/conversations` endpoint aggregates last message per phone from `conversations` table, joins with `patients` for name, checks Redis takeover flag for status.
**When to use:** Initial page load and status polling fallback.

```python
# Conversation status is derived: takeover flag in Redis takes priority
# conversations table already has tenant_id (added in migration 002)
# session_id in conversations = phone or phone@s.whatsapp.net

SELECT
    c.session_id,               -- phone identifier
    p.nome AS patient_nome,
    p.id AS patient_id,
    p.phone,
    MAX(c.created_at) AS last_message_at,
    (SELECT content FROM conversations c2
     WHERE c2.session_id = c.session_id
     ORDER BY c2.created_at DESC LIMIT 1) AS last_message_preview,
    COUNT(*) FILTER (WHERE c.role = 'user') AS message_count
FROM conversations c
LEFT JOIN patients p ON (p.phone = split_part(c.session_id, '@', 1))
WHERE c.tenant_id = current_tenant_id()
GROUP BY c.session_id, p.nome, p.id, p.phone
ORDER BY last_message_at DESC
```

*Status (`ia_ativa` | `humano` | `resolvida`) is determined post-query by checking Redis takeover flags.*

### Pattern 6: React Socket Hook (useSocket.ts)

**What:** Custom hook that initializes socket once, subscribes to events, cleans up on unmount.
**When to use:** InboxPanel component (top-level socket owner for the WhatsApp page).

```typescript
// frontend/src/hooks/useSocket.ts
"use client";
import * as React from "react";
import { getSocket, disconnectSocket } from "@/lib/socket";

export function useSocket(token: string) {
  const [isConnected, setIsConnected] = React.useState(false);

  React.useEffect(() => {
    const socket = getSocket(token);

    function onConnect() { setIsConnected(true); }
    function onDisconnect() { setIsConnected(false); }

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);

    if (socket.connected) setIsConnected(true);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      // Do NOT disconnect here — socket is a singleton across remounts
    };
  }, [token]);

  return { isConnected };
}
```

### Anti-Patterns to Avoid

- **Running uvicorn against `webhook:app` after adding Socket.IO:** The FastAPI app alone does not serve `/socket.io/`. Must run `socket_app` (the ASGIApp wrapper). Symptom: 404 on Socket.IO handshake.
- **Setting `cors_allowed_origins` in both FastAPI and AsyncServer:** Causes duplicate `Access-Control-Allow-Origin` headers. Set `cors_allowed_origins=[]` on sio, let FastAPI's CORSMiddleware handle CORS.
- **Creating a new socket instance in every component:** Creates multiple connections. Use singleton `getSocket()` from `lib/socket.ts`.
- **Adding `socket.disconnect()` in useEffect cleanup:** Unmounting a sub-component should not kill the connection. Only disconnect when navigating away from the inbox page entirely.
- **Checking takeover AFTER calling `handle_message`:** Sofia may invoke LLM before the check. The takeover check must be the FIRST thing in `webhook_evolution` after parsing the payload.
- **Using `room=None` (global emit) for `new_message`:** Sends every message to all connected users. Use per-phone rooms: `room=f"conv:{phone}"`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket reconnection logic | Custom retry loop with setTimeout | socket.io-client built-in reconnection | Exponential backoff, jitter, connection state machine already solved |
| Socket.IO protocol framing | Raw WebSocket with custom message format | python-socketio + socket.io-client | Namespace mux, room management, fallback transports |
| JWT extraction from environ | Parsing raw HTTP headers in ASGI environ | `auth` parameter in connect handler | Socket.IO delivers handshake auth as structured dict |

**Key insight:** The takeover flag is intentionally simple (Redis string, not a DB row) because it needs zero-latency read on every inbound webhook message. Do not add DB persistence for this state.

---

## Common Pitfalls

### Pitfall 1: Uvicorn Entry Point Not Updated

**What goes wrong:** After adding `socketio.ASGIApp`, developers forget to change `run_api.py` and keep running `uvicorn src.api.webhook:app`. The Socket.IO handshake path `/socket.io/` is not served by FastAPI alone — returns HTTP 404. Client shows `connect_error`.
**Why it happens:** FastAPI app is still importable and serves REST endpoints fine; only WebSocket upgrade fails silently.
**How to avoid:** `run_api.py` must point to `src.api.socketio_server:socket_app`. Also update any `uvicorn` invocations in deployment scripts or Docker commands.
**Warning signs:** Browser console shows `GET http://localhost:8000/socket.io/?EIO=4... 404`.

### Pitfall 2: Duplicate CORS Headers

**What goes wrong:** Both `CORSMiddleware` and `AsyncServer` set `Access-Control-Allow-Origin`. Browser rejects response: "Header contains multiple values".
**Why it happens:** python-socketio sets CORS headers by default even when mounted as ASGI inside FastAPI.
**How to avoid:** Always initialize: `sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=[])`.
**Warning signs:** Browser console CORS error even though CORSMiddleware is configured correctly.

### Pitfall 3: Socket Singleton Not Maintained

**What goes wrong:** Multiple socket connections opened (one per re-render or navigation). Server sees many duplicate connections per user. Events received multiple times.
**Why it happens:** Calling `io(...)` inside a React component body or useEffect without checking if socket already exists.
**How to avoid:** `lib/socket.ts` exports a module-level singleton. `getSocket(token)` returns the existing instance if already created.
**Warning signs:** Server logs show many `connect` events from same browser; client receives duplicate `new_message` events.

### Pitfall 4: Takeover Check Location

**What goes wrong:** Takeover check is placed inside `_process_message` (after the buffer flush). If two messages arrive rapidly and get buffered, the check runs after the full buffer wait (~3.5s). Patient message visible in DB but Sofia has already started processing before check completes.
**Why it happens:** The buffer logic in `handle_message` → `_flush_buffer` → `_process_message` was designed for AI processing, not conditional bypasses.
**How to avoid:** Check takeover flag in `webhook_evolution` (the FastAPI endpoint), before `background_tasks.add_task(handle_message, ...)`. If takeover flag exists, dispatch a different background task (`handle_inbound_takeover`) that only stores + broadcasts.
**Warning signs:** Occasional AI responses during human takeover, especially when patient sends messages quickly.

### Pitfall 5: conversations Table Lacks `id` Column

**What goes wrong:** Broadcasting `new_message` event with message data, but `conversations` table was created by the legacy bot code without a stable `id` column. `persistence.py` inserts without returning id.
**Why it happens:** The `save_messages()` function in `persistence.py` uses INSERT without `RETURNING id`. The patient conversations endpoint does `SELECT id::text` — meaning `id` must exist.
**How to avoid:** Check migration 004 — it adds `id UUID DEFAULT gen_random_uuid()` to `patients` but NOT `conversations`. A migration 005 must add `id UUID DEFAULT gen_random_uuid()` to `conversations` IF it does not already exist. Verify actual DB schema before writing migration.
**Warning signs:** `psycopg2.errors.UndefinedColumn: column "id" does not exist` in patient conversations endpoint.

### Pitfall 6: session_id Format in conversations Table

**What goes wrong:** Queries using `WHERE session_id = phone` miss rows because `session_id` stores `phone@s.whatsapp.net` (with suffix from Evolution API key format).
**Why it happens:** Evolution API `remoteJid` field includes `@s.whatsapp.net` suffix. `_parse_evolution_payload` returns raw `phone` including suffix. `persistence.py` stores it as-is in `session_id`.
**How to avoid:** The existing `get_patient_conversations` already handles this with `LIKE %{phone}%`. New conversation list endpoint must use the same pattern. When broadcasting `new_message`, use `split_part(session_id, '@', 1)` to normalize phone.
**Warning signs:** Inbox shows 0 conversations for a phone that has history.

### Pitfall 7: Socket.IO auth in Next.js SSR Context

**What goes wrong:** `socket.ts` module is imported in a Server Component, causing `io()` to run server-side where WebSocket is unavailable.
**Why it happens:** Next.js App Router runs non-`"use client"` components on the server.
**How to avoid:** `lib/socket.ts` must have `"use client"` directive at the top. The InboxPanel and all socket-consuming components must also be client components.
**Warning signs:** Build error: `ReferenceError: WebSocket is not defined` or `window is not defined`.

---

## Code Examples

Verified patterns from official sources:

### Socket.IO Server Initialization (python-socketio 5.x)

```python
# Source: https://github.com/miguelgrinberg/python-socketio/blob/main/examples/server/asgi/fastapi-fiddle.py
import socketio
from src.api.webhook import app

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],  # let FastAPI CORSMiddleware handle it
)
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    if not token:
        return False
    # validate JWT here

@sio.event
async def disconnect(sid):
    logger.info(f"[socketio] disconnected sid={sid}")

@sio.event
async def join_conversation(sid, data):
    phone = data.get("phone", "")
    if phone:
        await sio.enter_room(sid, f"conv:{phone}")

@sio.event
async def leave_conversation(sid, data):
    phone = data.get("phone", "")
    if phone:
        await sio.leave_room(sid, f"conv:{phone}")
```

### Socket.IO Client Singleton (socket.io-client 4.x)

```typescript
// Source: https://socket.io/how-to/use-with-nextjs + https://socket.io/docs/v4/client-api/
"use client";
import { io, Socket } from "socket.io-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
let _socket: Socket | null = null;

export function getSocket(token: string): Socket {
  if (!_socket) {
    _socket = io(`${API_URL}/inbox`, {
      auth: { token },
      transports: ["websocket"],          // skip polling for cleaner behavior
      reconnectionDelayMax: 10000,        // max 10s between reconnect attempts
    });
  }
  return _socket;
}

export function disconnectSocket(): void {
  _socket?.disconnect();
  _socket = null;
}
```

### Emit new_message from Webhook (takeover bypass path)

```python
# Inside webhook_evolution — the new takeover bypass branch
async def handle_inbound_takeover(
    phone: str,
    text: str,
    session: SessionManager,
):
    """Store inbound patient message during human takeover. No Sofia invocation."""
    from src.memory.persistence import save_messages
    from langchain_core.messages import HumanMessage
    import asyncio

    msg = HumanMessage(content=text)
    await asyncio.to_thread(save_messages, phone, [msg])

    # Broadcast to panel users watching this conversation
    await sio.emit("new_message", {
        "phone": phone.split("@")[0],
        "role": "user",
        "content": text,
    }, room=f"conv:{phone.split('@')[0]}")
```

### Takeover REST Endpoint Pattern

```python
# agent-service/src/api/conversations.py (new file)
@router.post("/{phone}/takeover")
async def takeover_conversation(
    phone: str,
    _user: dict = Depends(require_role("admin", "recepcionista")),
):
    """WPP-07: Disable IA for this conversation."""
    import json, time
    await redis_client.set(f"takeover:{phone}", json.dumps({
        "human_id": _user["user_id"],
        "human_name": _user.get("name", ""),
        "timestamp": time.time(),
    }))
    await sio.emit("conversation_updated", {
        "phone": phone,
        "status": "humano",
        "human_id": _user["user_id"],
    })
    return {"status": "takeover_active"}

@router.post("/{phone}/handback")
async def handback_conversation(
    phone: str,
    _user: dict = Depends(require_role("admin", "recepcionista")),
):
    """WPP-09: Re-enable IA for this conversation."""
    await redis_client.delete(f"takeover:{phone}")
    await sio.emit("conversation_updated", {
        "phone": phone,
        "status": "ia_ativa",
    })
    return {"status": "ia_active"}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| flask-socketio (Flask only) | python-socketio + ASGIApp (FastAPI) | 2019+ | ASGI mode required for modern async Python |
| Polling for updates | Socket.IO push | — | No periodic GET /conversations required |
| `socketio.AsyncServer(cors_allowed_origins='*')` | `cors_allowed_origins=[]` when FastAPI CORSMiddleware is present | 2021 (discussion #1304) | Prevents duplicate CORS header error |
| `uvicorn main:app` | `uvicorn main:socket_app` | Whenever python-socketio is added | socket.io/ path not served by bare FastAPI |

**Deprecated/outdated:**
- `app.mount("/socket.io", sio_app)`: Mounting to a sub-path with `app.mount()` has had compatibility issues with FastAPI 0.109+. Use `ASGIApp(sio, other_asgi_app=app)` + change uvicorn target instead.

---

## Open Questions

1. **Does the `conversations` table have a stable `id` column?**
   - What we know: Migration 004 adds `id` to `patients`. The `SELECT id::text FROM conversations` in `patients.py` works in production (Phase 3 PAT-05 passed), so `id` column exists.
   - What's unclear: Was it added by a pre-existing SQL migration (003_appointments.sql, etc.) not reflected in alembic chain? The legacy SQL files in `migrations/` predate the alembic chain.
   - Recommendation: Wave 0 task should verify `\d conversations` against live DB. If `id` is missing, migration 005 adds it with `gen_random_uuid()` default.

2. **Redis client availability in the new conversations router**
   - What we know: `session_manager` is initialized in `webhook.py` as a module-level singleton. `conversations.py` router cannot import from `webhook.py` without circular import.
   - What's unclear: Best pattern to share the Redis client between webhook and conversations router.
   - Recommendation: Move Redis client initialization to `socketio_server.py` as a module-level singleton `redis_client = aioredis.from_url(...)`. Both `webhook.py` and `conversations.py` import from `socketio_server.py`.

3. **Circular import between socketio_server.py and webhook.py**
   - What we know: `socketio_server.py` imports `app` from `webhook.py`. `webhook.py` needs to call `sio.emit(...)` for broadcast. If `webhook.py` imports `sio` from `socketio_server.py`, this creates a circular import.
   - Recommendation: Lazy import pattern — `from src.api.socketio_server import sio` inside the function body of `handle_inbound_takeover`, not at module level. Python's module cache handles this safely for runtime calls.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Redis | Takeover flag + existing sessions | Configured (SESSION_MANAGER uses REDIS_URL) | 7.3.0 (redis-py) | No fallback — takeover requires Redis |
| Evolution API | Sending human messages (WPP-08) | Configured (.env EVOLUTION_API_URL) | Existing EvolutionClient | — |
| python-socketio | API-04 | NOT installed | — | No fallback — required for phase |
| socket.io-client | Frontend real-time | NOT installed | — | No fallback — required for phase |

**Missing dependencies with no fallback:**
- `python-socketio==5.16.1` — install in agent-service
- `socket.io-client@4.8.3` — install in frontend

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (backend) |
| Config file | `agent-service/pytest.ini` |
| Quick run command | `cd agent-service && pytest tests/test_conversations.py -x -q` |
| Full suite command | `cd agent-service && pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-04 | Socket.IO server mounts on FastAPI, `/socket.io/` responds | integration | `pytest tests/test_conversations.py::test_socketio_endpoint_reachable -x` | ❌ Wave 0 |
| WPP-07 | Takeover endpoint sets Redis flag | unit | `pytest tests/test_conversations.py::test_takeover_sets_redis_flag -x` | ❌ Wave 0 |
| WPP-09 | Handback endpoint clears Redis flag | unit | `pytest tests/test_conversations.py::test_handback_clears_redis_flag -x` | ❌ Wave 0 |
| WPP-10 | Webhook skips Sofia when takeover flag exists | unit | `pytest tests/test_conversations.py::test_webhook_takeover_bypass -x` | ❌ Wave 0 |
| WPP-01 | Conversation list endpoint returns conversations | integration | `pytest tests/test_conversations.py::test_conversation_list_returns_data -x` | ❌ Wave 0 |
| WPP-08 | Send endpoint calls Evolution API + stores in DB | integration (mock) | `pytest tests/test_conversations.py::test_send_message_stores_and_broadcasts -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd agent-service && pytest tests/test_conversations.py -x -q`
- **Per wave merge:** `cd agent-service && pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `agent-service/tests/test_conversations.py` — covers all backend WPP/API-04 requirements above
- [ ] `agent-service/tests/conftest.py` — extend with `mock_redis` and `mock_sio` fixtures (add to existing conftest)
- [ ] Framework install: `cd agent-service && pip install python-socketio==5.16.1` + `cd frontend && npm install socket.io-client@4.8.3`

---

## Sources

### Primary (HIGH confidence)

- python-socketio GitHub (fastapi-fiddle.py example) — ASGIApp mounting pattern, connect auth parameter
- socket.io official docs (client-api) — `auth` option, reconnection options, namespace syntax
- socket.io official docs (use-with-nextjs) — "use client" directive pattern, singleton socket, SSR exclusion
- python-socketio GitHub discussion #1304 — `cors_allowed_origins=[]` fix for FastAPI CORSMiddleware conflict

### Secondary (MEDIUM confidence)

- WebSearch: "python-socketio ASGIApp cors_allowed_origins empty FastAPI" — CORS duplicate header pattern confirmed by multiple GitHub issues (#23, #28 in fastapi-socketio)
- WebSearch: "python-socketio emit to room enter_room leave_room asyncio" — room management API confirmed consistent with official docs

### Tertiary (LOW confidence)

- None used for architectural decisions — all patterns verified against official sources

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — versions verified against PyPI/npm registry on 2026-03-30
- Architecture: HIGH — ASGIApp pattern from official python-socketio example; CORS fix from official GitHub discussion
- Pitfalls: HIGH — each pitfall derived from direct code inspection of existing webhook.py/session.py or from verified GitHub issues
- Test architecture: MEDIUM — test structure follows existing conftest.py pattern; specific assertions TBD by implementation

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (python-socketio 5.x API is stable; socket.io-client 4.x LTS)
