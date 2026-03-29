"""Orquestrador do pipeline Sofia + Carla para WhatsApp.

Implementa buffer adaptativo de mensagens:
- Quando chega uma mensagem, registra o timestamp e aguarda um curto silêncio.
- Se o cliente manda mensagens rápidas (< threshold entre elas), espera um pouco mais
  para juntar tudo numa única resposta.
- Tempos padrão mais curtos para resposta rápida; ajuste via variáveis de ambiente:
  ORCHESTRATOR_BUFFER_WAIT_BASE, ORCHESTRATOR_BUFFER_WAIT_FAST,
  ORCHESTRATOR_FAST_TYPING_THRESHOLD (segundos).
"""

import asyncio
import logging
import os
import time
from collections import defaultdict
from typing import Dict, List

from langchain_core.messages import HumanMessage

from src.agent.graph import build_graph
from src.agent_carla.graph import build_carla_graph
from src.core.extraction import (
    determine_etapa,
    extract_data,
    reconcile_state_nome_paciente,
)
from src.api.session import SessionManager
from src.api.evolution import EvolutionClient
from src.observability.langfuse_setup import get_langfuse
from src.tools.patients import buscar_paciente

logger = logging.getLogger("agent-clinic.orchestrator")

# Grafos como singletons (inicializados uma vez)
_sofia_graph = None
_carla_graph = None

# Lock por telefone para evitar race conditions
_phone_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

# Buffer de mensagens por telefone
_message_buffers: Dict[str, List[str]] = defaultdict(list)
_buffer_tasks: Dict[str, asyncio.Task] = {}

# Sequência por telefone — garante que só o último flush processa
_buffer_seq: Dict[str, int] = defaultdict(int)

# Timestamps da última mensagem por telefone (para detectar ritmo)
_last_message_time: Dict[str, float] = {}

# Buffer: silêncio após última mensagem antes de processar (segundos)
BUFFER_WAIT_BASE = float(os.getenv("ORCHESTRATOR_BUFFER_WAIT_BASE", "3.5"))
# Se mensagens chegarem em menos de X segundos, considera "digitando rápido"
FAST_TYPING_THRESHOLD = float(os.getenv("ORCHESTRATOR_FAST_TYPING_THRESHOLD", "4.0"))
# Espera quando o cliente está digitando rápido (ainda junta mensagens)
BUFFER_WAIT_FAST = float(os.getenv("ORCHESTRATOR_BUFFER_WAIT_FAST", "2.5"))


def _get_graphs():
    """Inicializa e retorna os grafos Sofia e Carla (singleton)."""
    global _sofia_graph, _carla_graph
    if _sofia_graph is None:
        _sofia_graph = build_graph()
        logger.info("Grafo Sofia inicializado")
    if _carla_graph is None:
        _carla_graph = build_carla_graph()
        logger.info("Grafo Carla inicializado")
    return _sofia_graph, _carla_graph


def _invoke_carla(carla_graph, texto: str) -> list:
    """Passa texto pela Carla para reformatar e quebrar em mensagens."""
    carla_state = {
        "texto_original": texto,
        "texto_formatado": "",
        "mensagens_quebradas": [],
        "mensagens_enviadas": [],
        "etapa": "processar",
    }
    result = carla_graph.invoke(carla_state)
    return result.get("mensagens_quebradas", [])


async def handle_message(
    phone: str,
    text: str,
    session: SessionManager,
    evolution: EvolutionClient,
):
    """Acumula mensagens no buffer com espera adaptativa.

    Detecta se o cliente está digitando rápido e ajusta o tempo de espera.
    """
    now = time.time()
    last = _last_message_time.get(phone, 0)
    interval = now - last
    _last_message_time[phone] = now

    _message_buffers[phone].append(text)

    # Incrementa sequência — o flush só processa se for o mais recente
    _buffer_seq[phone] += 1
    my_seq = _buffer_seq[phone]

    # Define espera baseada no ritmo do cliente
    if interval < FAST_TYPING_THRESHOLD and len(_message_buffers[phone]) > 1:
        wait = BUFFER_WAIT_FAST
        logger.info(f"[{phone}] Cliente digitando rápido ({interval:.1f}s) — aguardando {wait}s")
    else:
        wait = BUFFER_WAIT_BASE
        logger.info(f"[{phone}] Mensagem recebida — aguardando {wait}s")

    # Cancela o timer anterior se existir (reinicia a espera)
    if phone in _buffer_tasks:
        _buffer_tasks[phone].cancel()

    # Agenda o processamento após o tempo calculado
    _buffer_tasks[phone] = asyncio.create_task(
        _flush_buffer(phone, wait, my_seq, session, evolution)
    )


async def _flush_buffer(
    phone: str,
    wait: float,
    my_seq: int,
    session: SessionManager,
    evolution: EvolutionClient,
):
    """Espera o buffer encher e processa todas as mensagens de uma vez."""
    await asyncio.sleep(wait)

    # Verifica se ainda somos o flush mais recente (dupla proteção além do cancel)
    if _buffer_seq[phone] != my_seq:
        logger.info(f"[{phone}] Flush {my_seq} descartado (seq atual: {_buffer_seq[phone]})")
        return

    # Coleta e limpa o buffer
    messages = _message_buffers.pop(phone, [])
    _buffer_tasks.pop(phone, None)

    if not messages:
        return

    # Junta todas as mensagens em um texto só
    combined_text = " ".join(messages)
    logger.info(
        f"[{phone}] Buffer expirado. Processando {len(messages)} "
        f"mensagem(ns): {combined_text[:80]}..."
    )

    async with _phone_locks[phone]:
        # Fica online antes de processar
        await evolution.set_online(True)
        try:
            await _process_message(phone, combined_text, session, evolution)
        except Exception as e:
            logger.exception(f"Erro ao processar mensagem de {phone}: {e}")
            try:
                await evolution.send_text(
                    phone, "Desculpe, tive um problema. Pode repetir?"
                )
            except Exception:
                logger.exception("Falha ao enviar mensagem de erro")
        finally:
            # Volta pra offline após responder
            await evolution.set_online(False)


async def _process_message(
    phone: str,
    text: str,
    session: SessionManager,
    evolution: EvolutionClient,
):
    """Lógica principal do pipeline."""
    sofia_graph, carla_graph = _get_graphs()

    # 1. Carregar estado da sessão
    state = await session.load_state(phone)

    # Garante que session_id está presente no state
    if not state.get("session_id"):
        state["session_id"] = phone
    if "rag_context" not in state:
        state["rag_context"] = ""

    # Reconhecimento de paciente retornando (só na primeira mensagem da sessão)
    if not state.get("nome_paciente") and not state.get("messages"):
        paciente = await asyncio.to_thread(buscar_paciente, phone)
        if paciente:
            state["nome_paciente"] = paciente["nome"]
            logger.info(f"[{phone}] Paciente reconhecido: {paciente['nome']} ({paciente['total_consultas']} consultas)")

    # 2. Adicionar mensagem do paciente ao histórico
    state["messages"] = state["messages"] + [HumanMessage(content=text)]

    # 4. Extrair dados e determinar etapa
    extracted = await asyncio.to_thread(extract_data, state["messages"])
    if extracted.pop("_clear_nome_paciente", False):
        state["nome_paciente"] = ""

    for key in [
        "nome_paciente",
        "especialidade",
        "motivo_consulta",
        "convenio",
        "data_agendamento",
        "horario_agendamento",
        "periodo",
        "medico_mencionado",
    ]:
        value = extracted.get(key)
        if value and value != "null" and str(value) != "None":
            state[key] = str(value)

    # Se o paciente mencionou um médico e ainda não temos médico agendado,
    # busca no banco e pré-popula estado para Sofia confirmar com o paciente
    medico_mencionado = state.get("medico_mencionado", "")
    if medico_mencionado and not state.get("medico_id"):
        from src.tools.doctors import buscar_medico_por_nome
        medico_encontrado = await asyncio.to_thread(buscar_medico_por_nome, medico_mencionado)
        if medico_encontrado:
            state["medico_id"] = medico_encontrado["id"]
            state["medico_agendado"] = medico_encontrado["nome"]
            # Preenche especialidade só se ainda não coletada
            if not state.get("especialidade"):
                state["especialidade"] = medico_encontrado["especialidade"]
            logger.info(f"[{phone}] Médico mencionado encontrado: {medico_encontrado['nome']} ({medico_encontrado['especialidade']})")

    # Atualiza protocolo e nova data/horário se extraídos
    for key in ["protocolo_consulta", "nova_data", "novo_horario"]:
        value = extracted.get(key)
        if value and value != "null" and str(value) != "None":
            state[key] = str(value)

    reconcile_state_nome_paciente(state, state["messages"])

    state["etapa"] = determine_etapa(state, extracted)
    logger.info(f"[{phone}] Etapa: {state['etapa']} | Dados: {extracted}")

    # 5. Invocar Sofia
    result = await asyncio.to_thread(sofia_graph.invoke, state)
    state.update(result)

    # Garante apresentação na primeira resposta de IA da sessão
    # (fallback: cobre casos onde recepcionar foi pulado por ter nome na 1ª msg)
    ai_msgs_total = [m for m in state.get("messages", []) if m.type == "ai"]
    is_truly_first_response = len(ai_msgs_total) == 1 and not state.get("apresentacao_feita")
    if is_truly_first_response:
        first_ai = ai_msgs_total[0]
        if "sofia" not in first_ai.content.lower():
            first_ai.content = f"Olá! sou a Sofia, da Clínica Saúde+\n\n{first_ai.content}"
        state["apresentacao_feita"] = True

    # 6. Formatar pela Carla
    ultima_msg = state["messages"][-1].content if state["messages"] else ""
    mensagens = await asyncio.to_thread(_invoke_carla, carla_graph, ultima_msg)

    # 7. Enviar via Evolution API (passa etapa pra detectar botões)
    await evolution.send_messages(phone, mensagens, etapa=state.get("etapa", ""))

    # 8. Salvar estado
    await session.save_state(phone, state)

    # 9. Se encerrou, gerar resumo final e limpar sessão
    if state.get("etapa") == "encerrar":
        logger.info(f"[{phone}] Atendimento encerrado")
        try:
            from src.agent.graph import end_session
            await asyncio.to_thread(end_session, phone)
        except Exception as e:
            logger.error(f"[{phone}] Erro ao encerrar sessão: {e}")
        try:
            langfuse = get_langfuse()
            langfuse.flush()
        except Exception:
            pass
        await session.clear_state(phone)
