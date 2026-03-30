import os
import json
import logging
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage

logger = logging.getLogger("agent-clinic.memory")

_PROMPT = """Analise a conversa de atendimento e retorne APENAS um JSON com:
- summary: resumo em 2-4 frases do atendimento
- key_topics: lista de até 5 tópicos principais (strings)
- sentiment: "positivo", "neutro" ou "negativo"
- resolved: true se a solicitação foi atendida, false se pendente

Retorne SOMENTE o JSON, sem texto adicional.

Conversa:
{conversa}

JSON:"""


class ConversationSummarizer:
    def __init__(self):
        self._llm = ChatOpenAI(
            model=os.getenv("SUMMARIZER_MODEL", os.getenv("LLM_MODEL")),
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
            temperature=0,
        )

    def summarize(self, messages: List[BaseMessage]) -> dict:
        try:
            conversa = "\n".join(
                f"{'Agente' if m.type == 'ai' else 'Paciente'}: {m.content}"
                for m in messages
            )
            prompt = _PROMPT.format(conversa=conversa)
            response = self._llm.invoke([SystemMessage(content=prompt)])
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except Exception as e:
            logger.error(f"[summarizer] erro: {e}")
            return {}
