# Phase 4: WhatsApp Panel - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Real-time WhatsApp inbox for receptionists. Monitor active conversations, read full message history with patient sidebar, see conversation status (IA ativa / Humano / Resolvida), take over from AI to send messages as human, hand back to AI. All via Socket.IO real-time streaming.

</domain>

<decisions>
## Implementation Decisions

### Real-time Transport
- **D-01:** Socket.IO — python-socketio on FastAPI + socket.io-client on Next.js. Auto-reconnect, rooms per conversation, namespace isolation.
- **D-02:** 3 core events: `new_message` (message arrived), `conversation_updated` (status/takeover changed), `typing_indicator` (someone is typing). Minimal event surface covering all WPP requirements.
- **D-03:** Socket.IO server mounts on the existing FastAPI ASGI app. Authenticated connections use JWT from session.

### Inbox Layout and UX
- **D-04:** 3-column layout: left=conversation list with search, center=message thread (chat bubbles), right=patient info sidebar (name, phone, last visit, appointments). Like WhatsApp Web with patient context.
- **D-05:** Conversation list sorted by latest message first. Filter tabs: Todas | IA Ativa | Humano | Resolvida. Search by patient name/phone (WPP-05).
- **D-06:** Chat bubble style reuses the WhatsApp timeline pattern from Phase 3 patient profile. Green=outgoing (bot or human), white=incoming (patient).

### Takeover Flow
- **D-07:** Takeover state stored as Redis flag per conversation: `takeover:{phone}` → `{human_id, human_name, timestamp}`. Webhook checks this flag BEFORE invoking Sofia pipeline. Instant check, no DB round-trip.
- **D-08:** No auto-expire — human stays in control until explicitly clicking "Devolver para IA". Prevents accidental AI responses mid-human conversation.
- **D-09:** Socket.IO broadcasts `conversation_updated` on takeover/handback. All connected users see the status indicator change immediately (WPP-11).
- **D-10:** During takeover mode (WPP-10): webhook receives message from patient → stores in DB → broadcasts via Socket.IO to panel → does NOT invoke Sofia. Human responds via panel → Evolution API sends → stored in DB → broadcasts.

### Message Sending
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### WhatsApp integration
- `agent-service/src/api/webhook.py` — Existing webhook endpoint, Evolution payload parsing, orchestrator dispatch. THIS IS THE FILE that must check takeover flag before invoking Sofia.
- `agent-service/src/api/evolution.py` — EvolutionClient with `send_message_with_typing()`. Reuse for human-sent messages.
- `agent-service/src/api/orchestrator.py` — Message buffering and graph invocation. Takeover must bypass this.
- `agent-service/src/api/session.py` — Redis session management pattern. Takeover flag follows similar pattern.

### Database
- `agent-service/src/memory/persistence.py` — `save_messages()`, `load_session_history()`. Message storage pattern.
- `agent-service/alembic/versions/` — Existing migration chain (001-004).

### Frontend patterns
- `frontend/src/components/dashboard/patient/WhatsAppTimeline.tsx` — Chat bubble component from Phase 3. Reuse for inbox thread.
- `frontend/src/lib/api.ts` — apiFetch wrapper with auth
- `frontend/src/lib/auth.ts` — NextAuth session for Socket.IO auth
- `frontend/src/app/(dashboard)/layout.tsx` — Dashboard shell with sidebar

### Requirements
- `.planning/REQUIREMENTS.md` — WPP-01 through WPP-11, API-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- WhatsAppTimeline.tsx (Phase 3) — chat bubble component, green right / white left style
- EvolutionClient.send_message_with_typing() — sends messages via Evolution API
- Redis session manager (`src/api/session.py`) — pattern for takeover flag storage
- DataTable, StatusBadge components — for conversation list
- apiFetch wrapper — for REST calls alongside Socket.IO

### Established Patterns
- Webhook receives Evolution API payload → parses → dispatches to orchestrator
- Messages stored in `conversations` table with role (user/assistant), content, metadata
- Redis keys use `session:{phone}` pattern → takeover can use `takeover:{phone}`
- FastAPI ASGI app supports mounting additional protocols (Socket.IO)

### Integration Points
- Webhook must check takeover flag BEFORE orchestrator.handle_message()
- Socket.IO server mounts on same FastAPI ASGI app (port 8000)
- Next.js client connects to Socket.IO on port 8000 (CORS already configured from Phase 2)
- Conversation list page slots into `(dashboard)/conversas/` route
- Human-sent messages go through Evolution API same as bot messages

</code_context>

<specifics>
## Specific Ideas

- The inbox should feel like WhatsApp Web — familiar for clinic staff
- Takeover button should be prominent and clearly show current state (IA or Human)
- Patient sidebar should show the same info as patient profile but condensed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-whatsapp-panel*
*Context gathered: 2026-03-30*
