import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage

from src.agent_carla.state import CarlaState
from src.agent_carla.prompts import PROMPT_CARLA
from src.agent_carla.tools import aplicar_abreviacoes, quebrar_em_mensagens, enviar_mensagem
from src.observability.langfuse_setup import get_langfuse


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        temperature=0.3,
    )


def processar_texto(state: CarlaState) -> dict:
    """Nó que recebe o texto corrido da Márcia e o reestrutura usando o LLM."""
    langfuse = get_langfuse()
    trace = langfuse.trace(
        name="carla-revisora",
        user_id="marcia",
        metadata={"etapa": "processar"},
        tags=["agent-carla", "stories10x"],
    )
    span = trace.span(
        name="processar_texto",
        input={"texto_original": state["texto_original"]},
    )

    llm = _get_llm()
    prompt = PROMPT_CARLA.format(texto_original=state["texto_original"])

    response = llm.invoke([SystemMessage(content=prompt)])
    texto_formatado = response.content.strip()

    # Aplica abreviações via tool
    resultado_abrev = aplicar_abreviacoes.invoke({"texto": texto_formatado})
    texto_formatado = resultado_abrev["texto"]

    span.end(output={
        "texto_formatado": texto_formatado,
        "abreviacoes_aplicadas": resultado_abrev["total_abreviacoes"],
    })
    langfuse.flush()

    return {
        "texto_formatado": texto_formatado,
        "etapa": "processar",
    }


def quebrar_mensagens(state: CarlaState) -> dict:
    """Nó que quebra o texto formatado em mensagens individuais para envio."""
    langfuse = get_langfuse()
    span = langfuse.span(
        name="quebrar_mensagens",
        input={"texto_formatado": state["texto_formatado"]},
    )

    resultado = quebrar_em_mensagens.invoke({"texto": state["texto_formatado"]})

    mensagens = resultado["mensagens"]

    span.end(output={
        "total_mensagens": resultado["total_mensagens"],
        "mensagens": mensagens,
    })
    langfuse.flush()

    return {
        "mensagens_quebradas": mensagens,
        "etapa": "quebrar",
    }


def enviar(state: CarlaState) -> dict:
    """Nó que simula o envio sequencial de cada mensagem no WhatsApp."""
    langfuse = get_langfuse()
    span = langfuse.span(
        name="enviar_mensagens",
        input={"total_mensagens": len(state["mensagens_quebradas"])},
    )

    enviadas = []
    for msg in state["mensagens_quebradas"]:
        resultado = enviar_mensagem.invoke({
            "mensagem": msg["conteudo"],
            "ordem": msg["ordem"],
        })
        enviadas.append(resultado)

    span.end(output={
        "total_enviadas": len(enviadas),
        "status": "todas_enviadas",
    })
    langfuse.flush()

    return {
        "mensagens_enviadas": enviadas,
        "etapa": "concluido",
    }
