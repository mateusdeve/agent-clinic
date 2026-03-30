"""FastAPI app com webhook para receber mensagens da Evolution API.

Endpoint principal: POST /webhook/evolution
Health check: GET /health
"""

import asyncio
import os
import logging
from datetime import datetime

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

from src.api.session import SessionManager
from src.api.evolution import EvolutionClient
from src.api.orchestrator import handle_message
from src.api.auth import router as auth_router
from src.api.patients import router as patients_router
from src.api.appointments import router as appointments_router
from src.api.doctors import router as doctors_router
from src.api.users import router as users_router
from src.api.conversations import router as conversations_router
from src.api.dashboard import router as dashboard_router
from src.api.templates import router as templates_router
from src.api.campaigns import router as campaigns_router
from src.api.campaigns import conversations_router as campaigns_conversations_router
from src.tools.followup import buscar_followups_pendentes, marcar_enviado, montar_mensagem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("agent-clinic.webhook")

app = FastAPI(title="Agent Clinic - WhatsApp Bot")

# CORS — permite requests do frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta routers de autenticacao, CRUD, conversas, dashboard e campanhas
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(appointments_router)
app.include_router(doctors_router)
app.include_router(users_router)
app.include_router(conversations_router)
app.include_router(dashboard_router)
app.include_router(templates_router)
app.include_router(campaigns_router)
app.include_router(campaigns_conversations_router)

# Inicializa dependências
session_manager = SessionManager(os.getenv("REDIS_URL", ""))
evolution_client = EvolutionClient()
scheduler = AsyncIOScheduler()


async def dispatch_campaigns():
    """Processa recipients pendentes de campanhas em lote (20 msg/seg).

    Estrategia: busca LIMIT 100 pendentes, marca como processando
    (previne double-dispatch), envia via Evolution API com throttle
    de 0.05s entre mensagens (20 msg/seg, per D-14/WPP-15).
    """
    import os
    import json as _json
    import psycopg2 as _psycopg2

    from src.api.templates import render_template

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return

    try:
        conn = _psycopg2.connect(db_url)

        # Buscar batch de pendentes e marcar como processando (anti double-dispatch)
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE campaign_recipients
                SET status = 'processando', updated_at = NOW()
                WHERE id IN (
                    SELECT id FROM campaign_recipients
                    WHERE status = 'pendente'
                    ORDER BY id
                    LIMIT 100
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING id::text, campaign_id::text, phone, variaveis
                """,
            )
            batch = cur.fetchall()
        conn.commit()

        if not batch:
            conn.close()
            return

        logger.info(f"[campaign_dispatcher] Processando {len(batch)} recipients")

        for rec_id, campaign_id, phone, variaveis_raw in batch:
            try:
                variaveis = variaveis_raw if isinstance(variaveis_raw, dict) else _json.loads(variaveis_raw or "{}")

                # Buscar template via campaign
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT mt.corpo FROM campaigns c
                        JOIN message_templates mt ON c.template_id = mt.id
                        WHERE c.id = %s
                        """,
                        (campaign_id,),
                    )
                    template_row = cur.fetchone()

                if not template_row:
                    raise ValueError(f"Template nao encontrado para campaign_id={campaign_id}")

                rendered = render_template(template_row[0], variaveis)

                # Enviar via Evolution API
                await evolution_client.send_message_with_typing(phone, rendered)

                # Marcar como enviado
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE campaign_recipients
                        SET status = 'enviado', sent_at = NOW(), updated_at = NOW()
                        WHERE id = %s
                        """,
                        (rec_id,),
                    )
                conn.commit()

            except Exception as e:
                logger.error(f"[campaign_dispatcher] Erro ao enviar para {phone}: {e}")
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE campaign_recipients
                        SET status = 'falha', erro = %s, updated_at = NOW()
                        WHERE id = %s
                        """,
                        (str(e), rec_id),
                    )
                conn.commit()

            # Throttle: 20 msg/seg = 0.05s entre envios
            await asyncio.sleep(0.05)

        # Verificar se campanha concluiu (sem mais pendentes/processando)
        campaign_ids = list({row[1] for row in batch})
        for campaign_id in campaign_ids:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*) FROM campaign_recipients
                        WHERE campaign_id = %s AND status IN ('pendente', 'processando')
                        """,
                        (campaign_id,),
                    )
                    remaining = cur.fetchone()[0]

                if remaining == 0:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE campaigns
                            SET status = 'concluida', enviado_at = NOW()
                            WHERE id = %s AND status = 'enviando'
                            """,
                            (campaign_id,),
                        )
                    conn.commit()
                    logger.info(f"[campaign_dispatcher] Campanha {campaign_id} concluida")
            except Exception as e:
                logger.error(f"[campaign_dispatcher] Erro ao verificar conclusao de campanha {campaign_id}: {e}")

        conn.close()

    except Exception as e:
        logger.error(f"[campaign_dispatcher] Erro geral: {e}")


async def dispatch_followups():
    """Verifica e envia follow-ups pendentes a cada 5 minutos."""
    pendentes = buscar_followups_pendentes()
    if not pendentes:
        return
    logger.info(f"[followup] {len(pendentes)} follow-up(s) pendente(s)")
    for fu in pendentes:
        try:
            mensagem = montar_mensagem(fu)
            await evolution_client.send_message_with_typing(fu["phone"], mensagem)
            marcar_enviado(fu["id"])
            logger.info(f"[followup] Enviado para {fu['phone']}")
        except Exception as e:
            logger.error(f"[followup] Erro ao enviar para {fu['phone']}: {e}")


@app.on_event("startup")
async def startup():
    scheduler.add_job(dispatch_followups, "interval", minutes=5, id="followup_dispatcher")
    scheduler.add_job(dispatch_campaigns, "interval", seconds=30, id="campaign_dispatcher")
    scheduler.start()
    logger.info("[scheduler] APScheduler iniciado — follow-ups a cada 5 min, campanhas a cada 30 seg")


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)


def _parse_evolution_payload(payload: dict) -> tuple:
    """Extrai número de telefone e texto da mensagem do payload da Evolution API.

    Retorna (phone, text) ou (None, None) se não for mensagem de texto válida.
    """
    # Ignorar eventos que não são mensagens
    event = payload.get("event", "")
    if event not in ("messages.upsert",):
        return None, None

    data = payload.get("data", {})
    key = data.get("key", {})

    # Ignorar mensagens enviadas pelo próprio bot (evita loop infinito)
    if key.get("fromMe", False):
        return None, None

    phone = key.get("remoteJid", "")
    if not phone:
        return None, None

    # Ignorar mensagens de grupo
    if "@g.us" in phone:
        return None, None

    # Extrair texto da mensagem (pode estar em formatos diferentes)
    message = data.get("message", {})
    text = (
        message.get("conversation")
        or message.get("extendedTextMessage", {}).get("text")
    )

    if not text or not text.strip():
        return None, None

    return phone, text.strip()


@app.post("/webhook/evolution")
async def webhook_evolution(request: Request, background_tasks: BackgroundTasks):
    """Recebe mensagens do WhatsApp via Evolution API.

    Responde 200 imediatamente e processa a mensagem em background
    para evitar timeout do webhook.
    """
    payload = await request.json()

    phone, text = _parse_evolution_payload(payload)

    if not phone or not text:
        return {"status": "ignored"}

    logger.info(f"Mensagem recebida de {phone}: {text[:80]}...")

    # Check takeover flag — skip Sofia if human is in control (WPP-10, D-07)
    # MUST happen BEFORE handle_message dispatch (research Pitfall 4)
    clean_phone = phone.split("@")[0]
    from src.api.socketio_server import redis_client, broadcast_new_message  # lazy import (circular safe)
    takeover_raw = await redis_client.get(f"takeover:{clean_phone}")
    if takeover_raw:
        # Store message + broadcast to panel — do NOT invoke Sofia
        background_tasks.add_task(
            _handle_inbound_takeover,
            phone=phone,
            text=text,
        )
        return {"status": "takeover_mode"}

    # Processa em background para responder rápido ao webhook
    background_tasks.add_task(
        handle_message,
        phone=phone,
        text=text,
        session=session_manager,
        evolution=evolution_client,
    )

    # Broadcast inbound patient message to panel viewers (WPP-04)
    background_tasks.add_task(
        broadcast_new_message,
        clean_phone,
        {
            "phone": clean_phone,
            "role": "user",
            "content": text,
            "created_at": datetime.utcnow().isoformat(),
        },
    )

    return {"status": "processing"}


@app.get("/health")
async def health():
    """Health check do servidor."""
    return {"status": "ok", "service": "agent-clinic-whatsapp"}


async def _handle_inbound_takeover(phone: str, text: str):
    """Armazena mensagem do paciente durante takeover. Nao invoca Sofia.

    Persiste na tabela conversations e faz broadcast via Socket.IO
    para que o painel mostre a mensagem em tempo real (D-10).
    """
    import asyncio
    from src.memory.persistence import save_messages
    from langchain_core.messages import HumanMessage
    from src.api.socketio_server import broadcast_new_message

    await asyncio.to_thread(save_messages, phone, [HumanMessage(content=text)])
    clean_phone = phone.split("@")[0]
    await broadcast_new_message(clean_phone, {
        "phone": clean_phone,
        "role": "user",
        "content": text,
        "created_at": datetime.utcnow().isoformat(),
    })
