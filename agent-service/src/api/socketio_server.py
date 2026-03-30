"""Socket.IO AsyncServer + ASGIApp wrapping FastAPI.

Provides:
- sio: AsyncServer instance for emitting events
- socket_app: ASGI app wrapping FastAPI (uvicorn entry point)
- redis_client: Shared async Redis client for takeover flags
- broadcast_new_message: Emit new_message to per-phone room
- broadcast_conversation_updated: Emit conversation_updated to all clients
- broadcast_typing_indicator: Emit typing_indicator per D-02
"""

import os
import logging

import jwt
import redis.asyncio as aioredis
import socketio

logger = logging.getLogger("agent-clinic.socketio")


# ─── Socket.IO Server ─────────────────────────────────────────────────────────
# cors_allowed_origins=[] is CRITICAL: empty list so FastAPI CORSMiddleware
# handles CORS alone (per D-03, research Pitfall 2 — prevents duplicate headers)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],
)

# Wrap FastAPI app — imported lazily at module level to avoid circular imports
# socketio_server imports from webhook; webhook imports broadcast functions lazily
from src.api.webhook import app  # noqa: E402

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


# ─── Shared Redis Client ───────────────────────────────────────────────────────
# Module-level singleton for takeover flags — shared with conversations router
# and webhook takeover check (resolves research Open Question 2)
redis_client = aioredis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True,
)


# ─── Socket.IO Events ─────────────────────────────────────────────────────────


@sio.event
async def connect(sid, environ, auth):
    """Authenticate JWT on Socket.IO handshake.

    Validates Bearer token from auth dict; saves user context in session.
    Rejects connection (returns False) if token missing or invalid.
    """
    token = (auth or {}).get("token")
    if not token:
        logger.warning(f"[socketio] connection rejected — no token (sid={sid})")
        return False

    secret = os.getenv("JWT_SECRET_KEY")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except Exception as e:
        logger.warning(f"[socketio] connection rejected — invalid token (sid={sid}): {e}")
        return False

    await sio.save_session(sid, {
        "user_id": payload["sub"],
        "tenant_id": payload["tenant_id"],
        "role": payload["role"],
    })
    logger.info(f"[socketio] connected sid={sid} user={payload['sub']}")


@sio.event
async def disconnect(sid):
    """Log Socket.IO disconnection."""
    logger.info(f"[socketio] disconnected sid={sid}")


@sio.event
async def join_conversation(sid, data):
    """Join the per-phone room for a conversation.

    data = {"phone": "5511999999999"}
    Room name pattern: conv:{phone}
    """
    phone = data.get("phone", "") if isinstance(data, dict) else ""
    if phone:
        await sio.enter_room(sid, f"conv:{phone}")
        logger.info(f"[socketio] sid={sid} joined conv:{phone}")


@sio.event
async def leave_conversation(sid, data):
    """Leave the per-phone room for a conversation.

    data = {"phone": "5511999999999"}
    """
    phone = data.get("phone", "") if isinstance(data, dict) else ""
    if phone:
        await sio.leave_room(sid, f"conv:{phone}")
        logger.info(f"[socketio] sid={sid} left conv:{phone}")


# ─── Broadcast Helpers ────────────────────────────────────────────────────────


async def broadcast_new_message(phone: str, message: dict):
    """Emit new_message to the per-phone room.

    Only panel users watching this conversation receive it.
    """
    await sio.emit("new_message", message, room=f"conv:{phone}")


async def broadcast_conversation_updated(data: dict):
    """Emit conversation_updated to all connected clients.

    Used on takeover (WPP-07), handback (WPP-09), and status changes.
    """
    await sio.emit("conversation_updated", data)


async def broadcast_typing_indicator(phone: str, is_typing: bool):
    """Emit typing_indicator per D-02.

    Used when Sofia starts/finishes processing a message.
    Sent to the per-phone room so only watchers of that conversation see it.
    """
    await sio.emit(
        "typing_indicator",
        {"phone": phone, "is_typing": is_typing},
        room=f"conv:{phone}",
    )
