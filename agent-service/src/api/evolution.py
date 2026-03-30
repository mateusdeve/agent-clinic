"""Cliente para a Evolution API — envio de mensagens WhatsApp.

Features:
- Indicador "digitando..." proporcional ao tamanho da mensagem
- Envio de botões de resposta rápida quando apropriado
- Delay entre mensagens para parecer humano
"""

import os
import asyncio
import logging
import re
from typing import List

import httpx

logger = logging.getLogger("agent-clinic.evolution")

# Velocidade de "digitação" — caracteres por segundo
TYPING_SPEED = float(os.getenv("EVOLUTION_TYPING_SPEED", "30"))
# Tempo mínimo e máximo de digitação antes de enviar (segundos)
TYPING_MIN = float(os.getenv("EVOLUTION_TYPING_MIN", "1.0"))
TYPING_MAX = float(os.getenv("EVOLUTION_TYPING_MAX", "8.0"))


class EvolutionClient:
    def __init__(self):
        self.base_url = os.getenv("EVOLUTION_API_URL", "").rstrip("/")
        self.api_key = os.getenv("EVOLUTION_API_KEY", "")
        self.instance = os.getenv("EVOLUTION_INSTANCE_NAME", "")
        self.send_delay = float(os.getenv("EVOLUTION_SEND_DELAY", "1.0"))

    def _clean_phone(self, phone: str) -> str:
        """Remove o sufixo @s.whatsapp.net do número."""
        return phone.split("@")[0]

    def _headers(self) -> dict:
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    def _typing_duration(self, text: str) -> float:
        """Calcula tempo de digitação baseado no tamanho do texto."""
        duration = len(text) / TYPING_SPEED
        return max(TYPING_MIN, min(duration, TYPING_MAX))

    async def set_online(self, available: bool = True):
        """Marca a instância como online/offline no WhatsApp."""
        url = f"{self.base_url}/instance/setPresence/{self.instance}"
        payload = {"presence": "available" if available else "unavailable"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json=payload, headers=self._headers())
                logger.info(f"Instância marcada como {'online' if available else 'offline'}")
        except Exception as e:
            logger.warning(f"Erro ao definir presença da instância: {e}")

    async def send_presence(self, phone: str, composing: bool = True):
        """Envia status 'digitando...' ou 'parou de digitar' para um chat."""
        url = f"{self.base_url}/chat/updatePresence/{self.instance}"
        payload = {
            "number": self._clean_phone(phone),
            "presence": "composing" if composing else "paused",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json=payload, headers=self._headers())
        except Exception as e:
            logger.warning(f"Erro ao enviar presence: {e}")

    async def send_text(self, phone: str, text: str):
        """Envia uma mensagem de texto via Evolution API."""
        url = f"{self.base_url}/message/sendText/{self.instance}"
        payload = {
            "number": self._clean_phone(phone),
            "text": text,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()
            logger.info(f"Texto enviado para {self._clean_phone(phone)}")
            return response.json()

    async def send_buttons(self, phone: str, text: str, buttons: List[str]):
        """Envia mensagem com botões de resposta rápida.

        Args:
            phone: número do WhatsApp
            text: texto da mensagem
            buttons: lista de textos dos botões (máx 3)
        """
        url = f"{self.base_url}/message/sendButtons/{self.instance}"
        payload = {
            "number": self._clean_phone(phone),
            "title": "",
            "description": text,
            "buttons": [
                {"type": "reply", "displayText": btn, "id": f"btn_{i}"}
                for i, btn in enumerate(buttons[:3])
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url, json=payload, headers=self._headers()
                )
                response.raise_for_status()
                logger.info(f"Botões enviados para {self._clean_phone(phone)}")
                return response.json()
        except Exception as e:
            # Fallback: se botões falharem, envia como texto normal
            logger.warning(f"Botões falharam, enviando como texto: {e}")
            await self.send_text(phone, text)

    async def send_list(self, phone: str, text: str, title: str, sections: list):
        """Envia mensagem com lista de opções.

        Args:
            phone: número do WhatsApp
            text: texto da mensagem
            title: título do botão da lista
            sections: lista de seções com rows
        """
        url = f"{self.base_url}/message/sendList/{self.instance}"
        payload = {
            "number": self._clean_phone(phone),
            "title": "",
            "description": text,
            "buttonText": title,
            "sections": sections,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url, json=payload, headers=self._headers()
                )
                response.raise_for_status()
                logger.info(f"Lista enviada para {self._clean_phone(phone)}")
                return response.json()
        except Exception as e:
            logger.warning(f"Lista falhou, enviando como texto: {e}")
            await self.send_text(phone, text)

    async def send_message_with_typing(self, phone: str, text: str):
        """Envia mensagem com indicador de digitação proporcional."""
        # Ativa "digitando..."
        await self.send_presence(phone, composing=True)

        # Espera proporcional ao tamanho da mensagem
        duration = self._typing_duration(text)
        await asyncio.sleep(duration)

        # Envia a mensagem
        await self.send_text(phone, text)

    async def send_buttons_with_typing(
        self, phone: str, text: str, buttons: List[str]
    ):
        """Envia botões com indicador de digitação."""
        await self.send_presence(phone, composing=True)
        duration = self._typing_duration(text)
        await asyncio.sleep(duration)
        await self.send_buttons(phone, text, buttons)

    async def send_messages(self, phone: str, mensagens: list, etapa: str = ""):
        """Envia múltiplas mensagens da Carla sequencialmente.

        Cada mensagem tem typing proporcional ao tamanho.
        """
        if not mensagens:
            return

        total = len(mensagens)

        for i, msg in enumerate(mensagens):
            conteudo = msg.get("conteudo", "")
            if not conteudo:
                continue

            await self.send_message_with_typing(phone, conteudo)

            # Delay extra entre mensagens (exceto a última)
            if i < total - 1:
                await asyncio.sleep(self.send_delay)

        logger.info(
            f"Enviadas {total} mensagens para {self._clean_phone(phone)}"
        )


def _detect_buttons(text: str, etapa: str) -> List[str]:
    """Detecta se a mensagem deve ter botões baseado no conteúdo e etapa.

    Retorna lista de botões ou lista vazia.
    """
    text_lower = text.lower()

    # Confirmação de agendamento → Sim / Não
    if etapa == "confirmar_agendamento":
        return ["Sim, confirmar", "Não, corrigir"]

    # Pergunta sobre agendar ou tirar dúvida
    if etapa == "identificar_motivo" or (
        "agendar" in text_lower and "dúvida" in text_lower
    ):
        return ["Agendar consulta", "Tirar dúvida"]

    # Convênios listados
    if any(
        conv.lower() in text_lower
        for conv in ["unimed", "bradesco", "sulamérica", "amil", "particular"]
    ):
        # Se lista muitos convênios, não usar botões (máx 3)
        convs_found = []
        for conv in ["Unimed", "Bradesco Saúde", "SulAmérica", "Amil", "Particular"]:
            if conv.lower() in text_lower:
                convs_found.append(conv)
        if 2 <= len(convs_found) <= 3:
            return convs_found

    # Horários disponíveis (detecta padrão HH:MM)
    horarios = re.findall(r"\b\d{1,2}:\d{2}\b", text)
    if horarios and len(horarios) <= 3:
        return horarios

    return []


def _clean_text_for_buttons(text: str, buttons: List[str]) -> str:
    """Remove opções do texto quando serão apresentadas como botões."""
    # Não mexe no texto — deixa o texto original + botões embaixo
    return text
