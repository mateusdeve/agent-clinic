"""Lógica compartilhada de extração de dados e determinação de etapa.

Usado por main.py (CLI) e src/api/orchestrator.py (WhatsApp).
"""

import os
import json

from langchain_openai import ChatOpenAI

from src.tools.agenda import ESPECIALIDADES, CONVENIOS


EXTRACTION_PROMPT = """Você é um assistente que extrai dados estruturados de conversas de atendimento em clínica.
Analise TODA a conversa abaixo e extraia os dados que conseguir identificar.

Retorne APENAS um JSON válido com os campos abaixo. Use null para campos não identificados.

Campos:
- nome_paciente: nome do paciente (string ou null). Extraia mesmo em frases como "sou o João", "me chamo Maria", "meu nome é Pedro", "aqui é o Carlos". Capture apenas o nome próprio, sem artigos.
- especialidade: deve ser exatamente uma dessas: {especialidades} (string ou null)
- motivo_consulta: "agendamento", "cancelar", "alterar" ou "faq" (string ou null). Se mencionar consulta médica nova → "agendamento". Se quiser cancelar/desmarcar → "cancelar". Se quiser remarcar/alterar → "alterar". Se fizer pergunta geral sobre a clínica (endereço, horário, convênios) → "faq". IMPORTANTE: se o paciente perguntar se um médico trabalha na clínica, mencionar que já consultou com ele, ou indicar que quer ser atendido por um médico específico → "agendamento" (não "faq").
- convenio: deve ser exatamente um desses: {convenios} (string ou null)
- data_agendamento: data desejada para consulta, ex: "próxima terça", "20/03", "amanhã" (string ou null)
- horario_agendamento: horário escolhido, ex: "09:30", "14:00", "9h", "às 10" (string ou null)
- periodo: período do dia preferido — extraia como "manhã" ou "tarde". Considere: "cedo", "de manhã", "pela manhã", "no começo do dia" = "manhã". "tarde", "à tarde", "depois do almoço" = "tarde". (string ou null)
- medico_mencionado: nome do médico mencionado pelo paciente, ex: "Dr. Marcos", "Doutor João", "Dra. Ana". Extraia apenas o nome sem título, ex: "Marcos". (string ou null)
- confirmou_agendamento: se o paciente confirmou os dados com "sim", "confirma", "pode ser", "isso mesmo" etc. (true/false/null)
- protocolo_consulta: número de protocolo informado pelo paciente, no formato #XXXX-XXXX ou similar (string ou null)
- nova_data: nova data desejada caso queira remarcar (string ou null)
- novo_horario: novo horário desejado caso queira remarcar (string ou null)

Conversa:
{conversa}

JSON:"""


def extract_data(messages: list) -> dict:
    """Usa o LLM para extrair dados estruturados da conversa."""
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
        temperature=0,
    )

    conversa = "\n".join(
        f"{'Agente' if m.type == 'ai' else 'Paciente'}: {m.content}"
        for m in messages
    )

    prompt = EXTRACTION_PROMPT.format(
        especialidades=", ".join(ESPECIALIDADES),
        convenios=", ".join(CONVENIOS),
        conversa=conversa,
    )

    response = llm.invoke(prompt)

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(content)
    except (json.JSONDecodeError, IndexError):
        return {}


def determine_etapa(state: dict, extracted: dict) -> str:
    """Determina a próxima etapa baseado nos dados coletados."""
    nome = state.get("nome_paciente") or extracted.get("nome_paciente")
    motivo = state.get("motivo_consulta") or extracted.get("motivo_consulta")
    especialidade = state.get("especialidade") or extracted.get("especialidade")
    convenio = state.get("convenio") or extracted.get("convenio")
    data = state.get("data_agendamento") or extracted.get("data_agendamento")
    horario = state.get("horario_agendamento") or extracted.get("horario_agendamento")
    confirmou = extracted.get("confirmou_agendamento")
    etapa_atual = state.get("etapa", "recepcionar")

    medico_mencionado = state.get("medico_mencionado") or extracted.get("medico_mencionado")

    if not nome:
        return "recepcionar"

    # Se mencionou um médico específico, prioriza identificar_motivo para confirmar
    # com o paciente — não trata como FAQ genérico
    if motivo == "faq" and medico_mencionado:
        return "identificar_motivo"

    if motivo == "faq":
        return "responder_faq"

    if motivo == "cancelar":
        return "cancelar_consulta"

    if motivo == "alterar":
        return "alterar_consulta"

    if not especialidade:
        return "identificar_motivo"

    if not data or not convenio:
        return "coletar_dados"

    if not horario:
        return "verificar_agenda"

    if etapa_atual == "confirmar_agendamento" and confirmou:
        return "encerrar"

    if etapa_atual != "encerrar":
        return "confirmar_agendamento"

    return "encerrar"


def default_state(session_id: str = "") -> dict:
    """Retorna o estado inicial padrão para uma nova conversa."""
    return {
        "messages": [],
        "nome_paciente": "",
        "motivo_consulta": "",
        "especialidade": "",
        "data_nascimento": "",
        "convenio": "",
        "data_agendamento": "",
        "horario_agendamento": "",
        "etapa": "recepcionar",
        "session_id": session_id,
        "rag_context": "",
        "protocolo_consulta": "",
        "nova_data": "",
        "novo_horario": "",
        "medico_agendado": "",
        "medico_id": "",
        "medicos_disponiveis": [],
        "periodo": "",
        "apresentacao_feita": False,
        "medico_mencionado": "",
    }
