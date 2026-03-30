# Phase 4: WhatsApp Panel - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 04-whatsapp-panel
**Areas discussed:** Real-time transport, Inbox layout and UX, Takeover flow, Message sending

---

## Real-time Transport

### Transport mechanism
| Option | Description | Selected |
|--------|-------------|----------|
| Socket.IO | python-socketio + socket.io-client. Auto-reconnect, rooms, namespaces. | ✓ |
| Native WebSocket | FastAPI WebSocket + browser API. Lighter but manual reconnect. | |
| SSE | One-way server→client. Can't send back through same channel. | |

**User's choice:** Socket.IO

### Event granularity
| Option | Description | Selected |
|--------|-------------|----------|
| 3 core events | new_message, conversation_updated, typing_indicator | ✓ |
| Fine-grained events | Separate event per action type | |
| You decide | | |

**User's choice:** 3 core events

---

## Inbox Layout and UX

### Layout style
| Option | Description | Selected |
|--------|-------------|----------|
| 3-column: list + thread + sidebar | Like WhatsApp Web with patient context | ✓ |
| 2-column: list + thread | Simpler, patient info via click | |
| You decide | | |

**User's choice:** 3-column

### Sort and filter
| Option | Description | Selected |
|--------|-------------|----------|
| Latest message first + status filter | Filter tabs: Todas/IA Ativa/Humano/Resolvida + search | ✓ |
| Unread first, then chronological | Unread pinned to top | |
| You decide | | |

**User's choice:** Latest message first + status filter

---

## Takeover Flow

### State storage
| Option | Description | Selected |
|--------|-------------|----------|
| Redis flag per conversation | takeover:{phone} → {human_id, timestamp}. Instant check. | ✓ |
| Database column | Status column on conversations table | |
| You decide | | |

**User's choice:** Redis flag

### Auto-expire
| Option | Description | Selected |
|--------|-------------|----------|
| No auto-expire | Human until explicit handback | ✓ |
| Auto-expire 30min | Auto-handback after idle | |
| You decide | | |

**User's choice:** No auto-expire

---

## Message Sending

### Composer style
| Option | Description | Selected |
|--------|-------------|----------|
| Text input + Enter to send | Simple text, Shift+Enter for newline. No rich media v1. | ✓ |
| Rich composer | Text + images + emoji picker | |
| You decide | | |

**User's choice:** Text input + Enter

---

## Claude's Discretion

- Socket.IO namespace/room strategy, reconnection settings, conversation preview length, status indicator design, scroll behavior, mobile responsive, unread counts, notifications

## Deferred Ideas

None
