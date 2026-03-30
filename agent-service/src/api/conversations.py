"""Endpoints REST para o painel de conversas WhatsApp.

Fornece inbox list, historico de mensagens, envio de mensagem humana,
takeover (assumir controle da IA) e handback (devolver para a IA).

Requer autenticacao via JWT (admin ou recepcionista).
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_for_tenant, require_role

logger = logging.getLogger("agent-clinic.api.conversations")

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# ─── Modelos ──────────────────────────────────────────────────────────────────


class SendMessageBody(BaseModel):
    text: str


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/")
async def list_conversations(
    search: Optional[str] = Query(""),
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna lista de conversas WhatsApp do tenant (WPP-01, WPP-03, WPP-05).

    Busca da tabela conversations agrupada por session_id.
    Status (ia_ativa / humano) derivado do flag Redis takeover:{phone}.
    Filtra por nome de paciente ou telefone quando search fornecido.
    """
    try:
        base_sql = """
            SELECT
                c.session_id,
                p.nome AS patient_nome,
                p.id AS patient_id,
                p.phone AS patient_phone,
                MAX(c.created_at) AS last_message_at,
                (SELECT content FROM conversations c2
                 WHERE c2.session_id = c.session_id
                 ORDER BY c2.created_at DESC LIMIT 1) AS last_message_preview,
                COUNT(*) AS message_count
            FROM conversations c
            LEFT JOIN patients p ON (p.phone = split_part(c.session_id, '@', 1))
            GROUP BY c.session_id, p.nome, p.id, p.phone
        """
        params = []

        if search:
            base_sql += " HAVING (p.nome ILIKE %s OR split_part(c.session_id, '@', 1) LIKE %s)"
            params = [f"%{search}%", f"%{search}%"]

        base_sql += " ORDER BY last_message_at DESC"

        with conn.cursor() as cur:
            cur.execute(base_sql, params)
            rows = cur.fetchall()

        # Derive status from Redis takeover flag (lazy import to avoid circular)
        from src.api.socketio_server import redis_client

        result = []
        for row in rows:
            session_id = row[0]
            patient_nome = row[1]
            patient_id = str(row[2]) if row[2] else None
            patient_phone = row[3]
            last_message_at = row[4]
            last_message_preview = row[5]
            message_count = row[6]

            # Normalize phone — strip @s.whatsapp.net suffix
            phone = patient_phone or split_phone(session_id)

            # Check Redis takeover flag for status
            takeover_raw = await redis_client.get(f"takeover:{phone}")
            if takeover_raw:
                takeover_data = json.loads(takeover_raw)
                conv_status = "humano"
                human_name = takeover_data.get("human_name", "")
            else:
                conv_status = "ia_ativa"
                human_name = ""

            # Truncate preview to 80 chars
            preview = (last_message_preview or "")[:80]

            result.append({
                "session_id": session_id,
                "phone": phone,
                "patient_nome": patient_nome or phone,
                "patient_id": patient_id,
                "last_message_at": last_message_at.isoformat() if last_message_at else None,
                "last_message_preview": preview,
                "message_count": message_count,
                "status": conv_status,
                "human_name": human_name,
            })

        logger.info(f"[conversations] list_conversations: count={len(result)} search={search!r}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[conversations] list_conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar conversas",
        )


@router.get("/{phone}/messages")
def get_messages(
    phone: str,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna historico completo de mensagens de uma conversa (WPP-02).

    Usa LIKE no session_id pois pode conter @s.whatsapp.net (research Pitfall 6).
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, role, content, created_at
                FROM conversations
                WHERE session_id LIKE %s
                ORDER BY created_at ASC
                """,
                (f"%{phone}%",),
            )
            rows = cur.fetchall()

        result = [
            {
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
            }
            for row in rows
        ]

        logger.info(f"[conversations] get_messages: phone={phone} count={len(result)}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[conversations] get_messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar mensagens",
        )


@router.post("/{phone}/send")
async def send_message(
    phone: str,
    body: SendMessageBody,
    user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Envia mensagem humana via painel (WPP-08, D-12).

    Fluxo:
    1. Chama Evolution API com indicador de digitacao
    2. Insere na tabela conversations com metadata sent_by_human=True
    3. Broadcast via Socket.IO para panel viewers
    """
    try:
        # Lazy imports to avoid circular dependency
        from src.api.webhook import evolution_client
        from src.api.socketio_server import broadcast_new_message

        # 1. Send via Evolution API
        await evolution_client.send_message_with_typing(phone, body.text)

        # 2. Insert into conversations table (use phone@s.whatsapp.net as session_id)
        session_id = f"{phone}@s.whatsapp.net"
        metadata = json.dumps({
            "sent_by": user["user_id"],
            "sent_by_human": True,
        })
        now = datetime.utcnow()

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (session_id, role, content, metadata)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, "assistant", body.text, metadata),
            )
        conn.commit()

        # 3. Broadcast via Socket.IO
        await broadcast_new_message(phone, {
            "phone": phone,
            "role": "assistant",
            "content": body.text,
            "sent_by_human": True,
            "created_at": now.isoformat(),
        })

        logger.info(f"[conversations] send_message: phone={phone} by={user['user_id']}")
        return {"status": "sent"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[conversations] send_message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar mensagem",
        )


@router.post("/{phone}/takeover")
async def takeover_conversation(
    phone: str,
    user: dict = Depends(require_role("admin", "recepcionista")),
):
    """Assume controle da conversa — desativa IA (WPP-07, D-07).

    Seta Redis key takeover:{phone} sem TTL (D-08).
    Broadcast conversation_updated para todos os clientes.
    """
    try:
        from src.api.socketio_server import redis_client, broadcast_conversation_updated

        # Look up human name from DB
        human_name = await _get_user_name(user["user_id"])

        # Set Redis key without TTL (D-08: no auto-expire)
        await redis_client.set(
            f"takeover:{phone}",
            json.dumps({
                "human_id": user["user_id"],
                "human_name": human_name,
                "timestamp": time.time(),
            }),
        )

        # Broadcast to all connected users
        await broadcast_conversation_updated({
            "phone": phone,
            "status": "humano",
            "human_name": human_name,
        })

        logger.info(f"[conversations] takeover: phone={phone} by={user['user_id']}")
        return {"status": "takeover_active"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[conversations] takeover error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao assumir conversa",
        )


@router.post("/{phone}/handback")
async def handback_conversation(
    phone: str,
    user: dict = Depends(require_role("admin", "recepcionista")),
):
    """Devolve controle da conversa para a IA (WPP-09).

    Deleta Redis key takeover:{phone}.
    Broadcast conversation_updated para todos os clientes.
    """
    try:
        from src.api.socketio_server import redis_client, broadcast_conversation_updated

        await redis_client.delete(f"takeover:{phone}")

        await broadcast_conversation_updated({
            "phone": phone,
            "status": "ia_ativa",
        })

        logger.info(f"[conversations] handback: phone={phone} by={user['user_id']}")
        return {"status": "ia_active"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[conversations] handback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao devolver conversa para IA",
        )


# ─── Helpers ──────────────────────────────────────────────────────────────────


def split_phone(session_id: str) -> str:
    """Normaliza session_id para telefone limpo (remove @s.whatsapp.net)."""
    return session_id.split("@")[0]


async def _get_user_name(user_id: str) -> str:
    """Busca nome do usuario no banco para exibicao no takeover."""
    import os
    import asyncio
    import psycopg2

    def _query():
        url = os.getenv("DATABASE_URL")
        if not url:
            return ""
        try:
            conn = psycopg2.connect(url)
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
            conn.close()
            return row[0] if row else ""
        except Exception:
            return ""

    return await asyncio.to_thread(_query)
