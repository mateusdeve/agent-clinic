"""Gerenciador de sessões de conversa via Redis.

Cada número de WhatsApp tem seu próprio estado de conversa,
persistido no Redis com TTL de 24 horas.
"""

import json
import logging

import redis.asyncio as aioredis
from langchain_core.messages import messages_to_dict, messages_from_dict

logger = logging.getLogger("agent-clinic.session")

SESSION_TTL = 86400  # 24 horas


class SessionManager:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)

    async def load_state(self, phone: str) -> dict:
        """Carrega o estado da conversa do Redis.

        Retorna estado inicial padrão se não existir sessão.
        """
        from src.core.extraction import default_state

        key = f"session:{phone}"
        raw = await self.redis.get(key)

        if not raw:
            logger.info(f"Nova sessão para {phone}")
            return default_state()

        try:
            data = json.loads(raw)
            data["messages"] = messages_from_dict(data["messages"])
            logger.info(f"Sessão carregada para {phone} (etapa: {data.get('etapa')})")
            return data
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Sessão corrompida para {phone}: {e}. Criando nova.")
            return default_state()

    async def save_state(self, phone: str, state: dict):
        """Persiste o estado da conversa no Redis com TTL."""
        key = f"session:{phone}"
        data = {**state}
        data["messages"] = messages_to_dict(state["messages"])
        await self.redis.set(
            key,
            json.dumps(data, ensure_ascii=False),
            ex=SESSION_TTL,
        )
        logger.info(f"Sessão salva para {phone} (etapa: {state.get('etapa')})")

    async def clear_state(self, phone: str):
        """Remove a sessão após encerramento da conversa."""
        await self.redis.delete(f"session:{phone}")
        logger.info(f"Sessão removida para {phone}")
