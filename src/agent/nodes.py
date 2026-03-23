import os
import json
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.agent.state import ClinicaState
from src.agent.prompts import (
    PROMPT_RECEPCIONAR,
    PROMPT_RECEPCIONAR_INICIO,
    PROMPT_IDENTIFICAR_MOTIVO,
    PROMPT_COLETAR_DADOS,
    PROMPT_VERIFICAR_AGENDA,
    PROMPT_CONFIRMAR_AGENDAMENTO,
    PROMPT_ENCERRAR,
    PROMPT_FAQ,
    PROMPT_CANCELAR_CONSULTA,
    PROMPT_ALTERAR_CONSULTA,
)
from src.tools.agenda import (
    verificar_disponibilidade,
    agendar_consulta,
    ESPECIALIDADES,
    CONVENIOS,
)
from src.tools.appointments import db_buscar_consultas, db_cancelar, db_alterar
from src.tools.patients import salvar_paciente
from src.tools.followup import criar_followup
from src.tools.faq import buscar_faq
from src.observability.langfuse_setup import get_langfuse
from src.memory.rag import ClinicRAG
from src.memory.summarizer import ConversationSummarizer
from src.memory.persistence import save_messages, save_summary

logger = logging.getLogger("agent-clinic.nodes")

_rag = ClinicRAG()
_summarizer = ConversationSummarizer()


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        temperature=0.3,
    )


def _invoke_llm(system_prompt: str, messages: list, span, rag_context: str = "") -> str:
    llm = _get_llm()
    if rag_context:
        system_prompt += (
            "\n\nContexto relevante de atendimentos anteriores (use se pertinente):\n"
            + rag_context
        )
    all_messages = [SystemMessage(content=system_prompt)] + messages
    span.update(input={"system_prompt": system_prompt, "messages": [m.content for m in messages]})
    response = llm.invoke(all_messages)
    span.update(output=response.content)
    return response.content


def _get_genero(medico_nome: str) -> str:
    """Detecta gênero do profissional pelo prefixo do nome."""
    nome = (medico_nome or "").strip()
    if nome.lower().startswith("dra.") or nome.lower().startswith("dra "):
        return "F"
    return "M"


def _get_dados_coletados(state: dict) -> str:
    """Monta resumo dos dados já coletados para exibir no prompt."""
    partes = []
    if state.get("data_agendamento"):
        partes.append(f"data: {state['data_agendamento']}")
    if state.get("periodo"):
        partes.append(f"período: {state['periodo']}")
    if state.get("convenio"):
        partes.append(f"convênio: {state['convenio']}")
    return " | ".join(partes) if partes else "nenhum dado coletado ainda"


def _get_periodo(horario: str) -> str:
    """Retorna 'manhã' ou 'tarde' baseado no horário."""
    try:
        hora = int(horario.split(":")[0])
        return "manhã" if hora < 12 else "tarde"
    except Exception:
        return ""


def retrieve_context(state: ClinicaState) -> dict:
    """Recupera contexto RAG relevante antes de gerar resposta."""
    try:
        query = state["messages"][-1].content if state["messages"] else ""
        context = _rag.retrieve(query) if query else ""
    except Exception as e:
        logger.error(f"[retrieve_context] erro: {e}")
        context = ""
    return {**state, "rag_context": context}


def save_and_learn(state: ClinicaState) -> dict:
    """Salva mensagens e, a cada 10 interações, resume e indexa no RAG."""
    try:
        session_id = state.get("session_id", "")
        if session_id and len(state["messages"]) >= 2:
            save_messages(session_id, state["messages"][-2:])

        if session_id and len(state["messages"]) % 10 == 0:
            summary_data = _summarizer.summarize(state["messages"])
            save_summary(session_id, summary_data)
            if summary_data.get("resolved"):
                topics = summary_data.get("key_topics", [])
                _rag.index_summary(
                    session_id=session_id,
                    summary=summary_data["summary"],
                    title=", ".join(topics[:2]),
                )
    except Exception as e:
        logger.error(f"[save_and_learn] erro: {e}")
    return state


def _extract_json_field(text: str, field: str) -> Optional[str]:
    """Tenta extrair um campo de uma resposta que pode conter JSON."""
    try:
        data = json.loads(text)
        return data.get(field)
    except (json.JSONDecodeError, TypeError):
        return None


def recepcionar(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    trace = langfuse.trace(
        name="atendimento-clinica",
        user_id="paciente",
        metadata={"etapa": "recepcionar"},
        tags=["agent-clinic"],
    )
    span = trace.span(name="recepcionar", input={"etapa": "recepcionar"})

    # is_first = nenhuma resposta de IA ainda na conversa
    # (state["messages"] já tem a mensagem do paciente quando este nó roda)
    ai_msgs_count = sum(1 for m in state["messages"] if m.type == "ai")
    is_first = ai_msgs_count == 0

    prompt = PROMPT_RECEPCIONAR_INICIO if is_first else PROMPT_RECEPCIONAR
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    # Garante apresentação na primeira mensagem, independente do LLM
    if is_first:
        apresentacao = "sou a Sofia, da Clínica Saúde+"
        if "sofia" not in response_text.lower():
            response_text = f"Olá! {apresentacao}\n\n{response_text}"

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "recepcionar",
        "apresentacao_feita": True,
    }


def identificar_motivo(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    span = langfuse.span(name="identificar_motivo", input={"etapa": "identificar_motivo", "nome": state.get("nome_paciente", "")})

    # Se o paciente mencionou um médico e ele foi encontrado no banco,
    # instrui Sofia a confirmar/usar esse médico com o paciente
    medico_agendado = state.get("medico_agendado", "")
    especialidade_medico = state.get("especialidade", "")
    medico_info = ""
    if medico_agendado and state.get("medico_id"):
        medico_info = (
            f"\nO paciente mencionou o médico {medico_agendado} ({especialidade_medico}), "
            f"que trabalha aqui na clínica. Confirme com o paciente se ele quer marcar com {medico_agendado} "
            f"e pergunte se é pra agendar uma consulta. Seja natural, não robotize.\n"
        )

    prompt = PROMPT_IDENTIFICAR_MOTIVO.format(
        nome_paciente=state.get("nome_paciente", "Paciente"),
        medico_info=medico_info,
    )
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "identificar_motivo",
    }


def coletar_dados(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    span = langfuse.span(name="coletar_dados", input={"etapa": "coletar_dados", "especialidade": state.get("especialidade", "")})

    prompt = PROMPT_COLETAR_DADOS.format(
        nome_paciente=state.get("nome_paciente", "Paciente"),
        especialidade=state.get("especialidade", "não informada"),
        dados_coletados=_get_dados_coletados(state),
    )
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "coletar_dados",
    }


def verificar_agenda(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    span = langfuse.span(name="verificar_agenda", input={
        "etapa": "verificar_agenda",
        "especialidade": state.get("especialidade", ""),
        "data": state.get("data_agendamento", ""),
    })

    resultado = verificar_disponibilidade.invoke({
        "especialidade": state.get("especialidade", ""),
        "data": state.get("data_agendamento", ""),
    })

    medicos = resultado.get("medicos", [])
    periodo = state.get("periodo") or _get_periodo(state.get("horario_agendamento", ""))

    prompt = PROMPT_VERIFICAR_AGENDA.format(
        nome_paciente=state.get("nome_paciente", "Paciente"),
        especialidade=state.get("especialidade", "não informada"),
        data_agendamento=state.get("data_agendamento", "não informada"),
        periodo=periodo or "qualquer período",
        slots_disponiveis=json.dumps(medicos, ensure_ascii=False),
    )
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "verificar_agenda",
        "medicos_disponiveis": medicos,
    }


def _resolver_medico_e_horario(state: dict) -> tuple:
    """
    Cruza horário escolhido com a lista de médicos disponíveis.
    Retorna (medico_nome, medico_id, horario).
    Se paciente não escolheu → pega o menos ocupado + primeiro slot disponível.
    """
    horario = state.get("horario_agendamento", "").strip()
    medicos = state.get("medicos_disponiveis", [])

    # Já tem médico E horário definidos → mantém
    if state.get("medico_agendado") and state.get("medico_id") and horario:
        return state["medico_agendado"], state["medico_id"], horario

    if not medicos:
        return state.get("medico_agendado", ""), state.get("medico_id", ""), horario

    # Paciente escolheu um horário → acha qual médico tem esse slot
    if horario:
        for medico in medicos:
            if horario in medico.get("slots", []):
                return medico["medico"], medico["doctor_id"], horario

    # Sem preferência → pega o menos ocupado (primeiro da lista) e o primeiro slot dele
    primeiro = medicos[0]
    slot_auto = primeiro["slots"][0] if primeiro.get("slots") else horario
    return primeiro["medico"], primeiro["doctor_id"], slot_auto


def confirmar_agendamento(state: ClinicaState) -> dict:
    langfuse = get_langfuse()

    # Resolve médico e horário — auto-atribui se paciente não escolheu
    medico_nome, medico_id, horario_resolvido = _resolver_medico_e_horario(state)

    span = langfuse.span(name="confirmar_agendamento", input={
        "etapa": "confirmar_agendamento",
        "dados": {
            "nome": state.get("nome_paciente"),
            "especialidade": state.get("especialidade"),
            "data": state.get("data_agendamento"),
            "horario": state.get("horario_agendamento"),
            "convenio": state.get("convenio"),
            "medico": medico_nome,
        },
    })

    prompt = PROMPT_CONFIRMAR_AGENDAMENTO.format(
        nome_paciente=state.get("nome_paciente", "Paciente"),
        medico_agendado=medico_nome or "médico",
        genero_profissional=_get_genero(medico_nome),
        especialidade=state.get("especialidade", "não informada"),
        data_agendamento=state.get("data_agendamento", "não informada"),
        horario_agendamento=horario_resolvido or "não informado",
        convenio=state.get("convenio", "não informado"),
    )
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "confirmar_agendamento",
        "medico_agendado": medico_nome,
        "medico_id": medico_id,
        "horario_agendamento": horario_resolvido,  # garante que o horário está no estado
    }


def encerrar(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    span = langfuse.span(name="encerrar", input={"etapa": "encerrar"})

    from src.tools.appointments import db_agendar
    resultado = db_agendar(
        phone=state.get("session_id", ""),
        nome=state.get("nome_paciente", ""),
        especialidade=state.get("especialidade", ""),
        data=state.get("data_agendamento", ""),
        horario=state.get("horario_agendamento", ""),
        convenio=state.get("convenio", ""),
        doctor_id=state.get("medico_id", ""),
        doctor_name=state.get("medico_agendado", ""),
    )

    protocolo = resultado.get("protocolo", "#0000-0000")
    phone = state.get("session_id", "")
    nome = state.get("nome_paciente", "")

    # Salva paciente e agenda follow-up
    if phone and nome:
        try:
            salvar_paciente(phone=phone, nome=nome)
            criar_followup(
                phone=phone,
                nome=nome,
                especialidade=state.get("especialidade", ""),
                data_consulta=state.get("data_agendamento", ""),
                horario=state.get("horario_agendamento", ""),
                protocolo=protocolo,
                horas_depois=24,
            )
        except Exception as e:
            logger.error(f"[encerrar] erro ao salvar paciente/followup: {e}")

    prompt = PROMPT_ENCERRAR.format(
        nome_paciente=state.get("nome_paciente", "Paciente"),
        medico_agendado=state.get("medico_agendado", "médico"),
        genero_profissional=_get_genero(state.get("medico_agendado", "")),
        especialidade=state.get("especialidade", "não informada"),
        data_agendamento=state.get("data_agendamento", "não informada"),
        horario_agendamento=state.get("horario_agendamento", "não informado"),
        convenio=state.get("convenio", "não informado"),
        protocolo=protocolo,
    )
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    span.end(output={"response": response_text, "protocolo": protocolo})
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "encerrar",
    }


def responder_faq(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    span = langfuse.span(name="responder_faq", input={"etapa": "faq"})

    ultima_mensagem = state["messages"][-1].content if state["messages"] else ""
    resultado_faq = buscar_faq.invoke({"pergunta": ultima_mensagem})

    prompt = PROMPT_FAQ.format(nome_paciente=state.get("nome_paciente", "Paciente"))
    faq_info = f"\n\nResultado da busca FAQ: {json.dumps(resultado_faq, ensure_ascii=False)}\nPergunta do paciente: {ultima_mensagem}"
    response_text = _invoke_llm(prompt + faq_info, state["messages"], span, state.get("rag_context", ""))

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "identificar_motivo",
    }


def cancelar_consulta(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    span = langfuse.span(name="cancelar_consulta", input={"etapa": "cancelar_consulta", "nome": state.get("nome_paciente", "")})

    phone = state.get("session_id", "")
    nome = state.get("nome_paciente", "")
    protocolo = state.get("protocolo_consulta", "")

    consultas = db_buscar_consultas(phone=phone, nome=nome)

    # Se tiver protocolo confirmado, executa o cancelamento
    resultado_cancelamento = None
    if protocolo:
        resultado_cancelamento = db_cancelar(phone=phone, nome=nome, protocolo=protocolo)

    if consultas:
        consultas_str = "\n".join(
            f"- Protocolo: {c['protocolo']} | {c['especialidade']} | {c['data']} às {c['horario']} | {c['convenio']}"
            for c in consultas
        )
    else:
        consultas_str = "Nenhuma consulta ativa encontrada."

    if resultado_cancelamento:
        consultas_str += f"\n\nResultado do cancelamento: {json.dumps(resultado_cancelamento, ensure_ascii=False)}"

    prompt = PROMPT_CANCELAR_CONSULTA.format(
        nome_paciente=nome or "Paciente",
        consultas_encontradas=consultas_str,
    )
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "cancelar_consulta",
    }


def alterar_consulta(state: ClinicaState) -> dict:
    langfuse = get_langfuse()
    span = langfuse.span(name="alterar_consulta", input={"etapa": "alterar_consulta", "nome": state.get("nome_paciente", "")})

    phone = state.get("session_id", "")
    nome = state.get("nome_paciente", "")
    protocolo = state.get("protocolo_consulta", "")
    nova_data = state.get("nova_data", "")
    novo_horario = state.get("novo_horario", "")

    consultas = db_buscar_consultas(phone=phone, nome=nome)

    # Se tiver protocolo, nova_data e novo_horario confirmados, executa a alteração
    resultado_alteracao = None
    if protocolo and nova_data and novo_horario:
        resultado_alteracao = db_alterar(
            phone=phone,
            nome=nome,
            protocolo=protocolo,
            nova_data=nova_data,
            novo_horario=novo_horario,
        )

    if consultas:
        consultas_str = "\n".join(
            f"- Protocolo: {c['protocolo']} | {c['especialidade']} | {c['data']} às {c['horario']} | {c['convenio']}"
            for c in consultas
        )
    else:
        consultas_str = "Nenhuma consulta ativa encontrada."

    if resultado_alteracao:
        consultas_str += f"\n\nResultado da alteração: {json.dumps(resultado_alteracao, ensure_ascii=False)}"

    # Busca slots disponíveis para nova data (se informada)
    slots_nova_data = []
    if nova_data and consultas:
        especialidade_consulta = consultas[0].get("especialidade", "")
        from src.tools.doctors import buscar_horarios_com_medico
        slots_nova_data = buscar_horarios_com_medico(especialidade_consulta, nova_data)

    prompt = PROMPT_ALTERAR_CONSULTA.format(
        nome_paciente=nome or "Paciente",
        consultas_encontradas=consultas_str,
        slots_disponiveis=json.dumps(slots_nova_data, ensure_ascii=False) if slots_nova_data else "[]",
    )
    response_text = _invoke_llm(prompt, state["messages"], span, state.get("rag_context", ""))

    span.end(output=response_text)
    langfuse.flush()

    return {
        "messages": state["messages"] + [AIMessage(content=response_text)],
        "etapa": "alterar_consulta",
    }
