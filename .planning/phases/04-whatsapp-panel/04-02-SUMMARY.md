---
phase: 04-whatsapp-panel
plan: 02
subsystem: ui
tags: [socket.io, react, nextjs, whatsapp, real-time, inbox, takeover]

# Dependency graph
requires:
  - phase: 04-whatsapp-panel plan 01
    provides: Socket.IO server, REST endpoints for conversations, takeover, handback, send
  - phase: 03-core-crud
    provides: apiFetch wrapper, Patient/Appointment types, WhatsAppTimeline bubble style, dashboard layout
provides:
  - /whatsapp route accessible to admin/recepcionista with 3-column inbox layout
  - ConversationList with search, filter tabs, status badges
  - ConversationThread with WhatsApp-style bubbles, send bar (disabled in ia_ativa mode), typing indicator
  - PatientSidebar showing patient info and recent appointments
  - TakeoverBar for Assumir/Devolver para IA actions
  - Socket.IO singleton (getSocket) and useSocket hook
  - ConversationSummary, ConversationStatus, NewMessageEvent, ConversationUpdatedEvent, TypingIndicatorEvent types
affects: [04-whatsapp-panel plan 03, any future inbox features]

# Tech tracking
tech-stack:
  added: [socket.io-client@4.8.3]
  patterns:
    - "Socket.IO singleton via module-level variable (getSocket) — one connection per browser session"
    - "useSocket hook owns connection lifecycle — no disconnect in cleanup to preserve singleton"
    - "InboxPanel derives selectedStatus/selectedHumanName from conversations array (single source of truth)"
    - "Socket.IO listeners in InboxPanel for conversation list updates, ConversationThread for per-message updates"
    - "Send bar disabled via status!='humano' — ConversationThread reads status prop from InboxPanel"

key-files:
  created:
    - frontend/src/lib/socket.ts
    - frontend/src/hooks/useSocket.ts
    - frontend/src/app/(dashboard)/whatsapp/page.tsx
    - frontend/src/app/(dashboard)/whatsapp/_components/InboxPanel.tsx
    - frontend/src/app/(dashboard)/whatsapp/_components/ConversationList.tsx
    - frontend/src/app/(dashboard)/whatsapp/_components/ConversationThread.tsx
    - frontend/src/app/(dashboard)/whatsapp/_components/PatientSidebar.tsx
    - frontend/src/app/(dashboard)/whatsapp/_components/TakeoverBar.tsx
  modified:
    - frontend/package.json (socket.io-client@4.8.3 added)
    - frontend/src/lib/types.ts (ConversationSummary, ConversationStatus, event interfaces added)

key-decisions:
  - "Socket.IO singleton uses default namespace (no /inbox suffix) matching socketio_server.py server setup"
  - "InboxPanel uses -m-6 to escape main padding and fill full viewport height with h-[calc(100vh-4rem)]"
  - "PatientSidebar hidden when no conversation selected (no empty column shown)"
  - "typing_indicator auto-clears after 15s safety fallback per D-02"
  - "ConversationThread appends messages from Socket.IO new_message event with synthetic id (Date.now + random)"

patterns-established:
  - "Socket singleton: lib/socket.ts module-level variable, getSocket(token) idempotent factory"
  - "useSocket hook: subscribes connect/disconnect only, returns {socket, isConnected}, no disconnect in cleanup"
  - "3-column layout: w-80 left + flex-1 center + w-80 right (hidden when nothing selected)"

requirements-completed: [WPP-01, WPP-02, WPP-03, WPP-04, WPP-05, WPP-06, WPP-07, WPP-08, WPP-09, WPP-11]

# Metrics
duration: 6min
completed: 2026-03-30
---

# Phase 04 Plan 02: WhatsApp Inbox Frontend Summary

**Socket.IO-powered 3-column WhatsApp inbox with conversation list, message thread (send bar gated to takeover mode), typing indicator, patient sidebar, and Assumir/Devolver para IA controls**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-30T11:23:12Z
- **Completed:** 2026-03-30T11:29:12Z
- **Tasks:** 2
- **Files modified:** 10 (8 created, 2 modified)

## Accomplishments

- Installed socket.io-client@4.8.3 and established singleton socket factory with useSocket React hook
- Built /whatsapp page as server component (auth check + medico redirect) rendering InboxPanel client orchestrator
- Delivered complete 3-column inbox: ConversationList (search + filter tabs + status badges), ConversationThread (WhatsApp-style bubbles + typing dots + disabled send bar in ia_ativa mode), PatientSidebar (patient info + appointments), TakeoverBar (Assumir/Devolver buttons)
- Wired Socket.IO events: new_message updates conversation list and appends to thread; conversation_updated refreshes status for all users; typing_indicator shows animated dots with 15s auto-clear

## Task Commits

1. **Task 1: socket.io-client + socket singleton + useSocket hook + conversation types** - `8ca57ec` (feat)
2. **Task 2: 3-column inbox layout with all components** - `42c147e` (feat)

## Files Created/Modified

- `frontend/src/lib/socket.ts` - getSocket singleton factory, disconnectSocket export, "use client"
- `frontend/src/hooks/useSocket.ts` - useSocket hook managing connect/disconnect state, no cleanup disconnect
- `frontend/src/lib/types.ts` - Added ConversationSummary, ConversationStatus, NewMessageEvent, ConversationUpdatedEvent, TypingIndicatorEvent
- `frontend/package.json` - Added socket.io-client@4.8.3
- `frontend/src/app/(dashboard)/whatsapp/page.tsx` - Server component, auth + role guard, renders InboxPanel
- `frontend/src/app/(dashboard)/whatsapp/_components/InboxPanel.tsx` - Main orchestrator, useSocket, conversation state, Socket.IO listeners, 3-column layout, connection indicator
- `frontend/src/app/(dashboard)/whatsapp/_components/ConversationList.tsx` - Search input, 4 filter tabs, scrollable conversation cards with status badges
- `frontend/src/app/(dashboard)/whatsapp/_components/ConversationThread.tsx` - Message bubbles (green right/white left), typing indicator, send bar disabled when ia_ativa, Enter sends / Shift+Enter newline
- `frontend/src/app/(dashboard)/whatsapp/_components/PatientSidebar.tsx` - Patient avatar + meta, recent appointments, "Ver perfil completo" link
- `frontend/src/app/(dashboard)/whatsapp/_components/TakeoverBar.tsx` - Assumir (orange) / Devolver para IA (green) buttons with loading spinner

## Decisions Made

- Socket.IO singleton uses default namespace (no `/inbox`) to match the server setup in socketio_server.py which does not specify a namespace
- Layout uses `-m-6` negative margin on InboxPanel to escape the dashboard's `p-6` main padding and achieve full-height 3-column layout with `h-[calc(100vh-4rem)]` (subtracts 4rem header)
- PatientSidebar is conditionally rendered — only appears when a conversation is selected, avoiding an empty right column
- Typing indicator auto-clears after 15s as safety fallback per context decision D-02 specification
- Synthetic message IDs generated with `Date.now()-${Math.random()}` when appending Socket.IO new_message events (backend broadcasts don't include id)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

None — all data flows are wired to live backend endpoints.

## Next Phase Readiness

- /whatsapp inbox fully functional, waiting on plan 03 (verification + any remaining backend polish)
- Backend Socket.IO server (plan 01) must be running for real-time features to work
- TypeScript compiles cleanly, Next.js build succeeds with /whatsapp as dynamic route

---
*Phase: 04-whatsapp-panel*
*Completed: 2026-03-30*
