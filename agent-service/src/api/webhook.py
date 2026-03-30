"""FastAPI app com webhook para receber mensagens da Evolution API.

Endpoint principal: POST /webhook/evolution
Health check: GET /health
"""

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

# Monta routers de autenticacao, CRUD e conversas
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(appointments_router)
app.include_router(doctors_router)
app.include_router(users_router)
app.include_router(conversations_router)

# Inicializa dependências
session_manager = SessionManager(os.getenv("REDIS_URL", ""))
evolution_client = EvolutionClient()
scheduler = AsyncIOScheduler()


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
    scheduler.start()
    logger.info("[scheduler] APScheduler iniciado — follow-ups a cada 5 min")


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
