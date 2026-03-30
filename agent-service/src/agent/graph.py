from langgraph.graph import StateGraph, END

from src.agent.state import ClinicaState
from src.agent.nodes import (
    recepcionar,
    identificar_motivo,
    coletar_dados,
    verificar_agenda,
    confirmar_agendamento,
    encerrar,
    responder_faq,
    cancelar_consulta,
    alterar_consulta,
    retrieve_context,
    save_and_learn,
)
from src.memory.summarizer import ConversationSummarizer
from src.memory.persistence import save_summary, load_session_history
from src.memory.rag import ClinicRAG

_summarizer = ConversationSummarizer()
_rag = ClinicRAG()

_GENERATION_NODES = [
    "recepcionar",
    "identificar_motivo",
    "coletar_dados",
    "verificar_agenda",
    "confirmar_agendamento",
    "encerrar",
    "responder_faq",
    "cancelar_consulta",
    "alterar_consulta",
]


def _entry_router(state: ClinicaState) -> str:
    """Roteia para o nó correto baseado na etapa atual."""
    etapa = state.get("etapa", "recepcionar")
    if etapa in _GENERATION_NODES:
        return etapa
    return "recepcionar"


def build_graph():
    graph = StateGraph(ClinicaState)

    # Nó de entrada: recupera contexto RAG
    graph.add_node("retrieve_context", retrieve_context)

    # Nós de geração
    for name, fn in [
        ("recepcionar", recepcionar),
        ("identificar_motivo", identificar_motivo),
        ("coletar_dados", coletar_dados),
        ("verificar_agenda", verificar_agenda),
        ("confirmar_agendamento", confirmar_agendamento),
        ("encerrar", encerrar),
        ("responder_faq", responder_faq),
        ("cancelar_consulta", cancelar_consulta),
        ("alterar_consulta", alterar_consulta),
    ]:
        graph.add_node(name, fn)

    # Nó de persistência
    graph.add_node("save_and_learn", save_and_learn)

    # Fluxo: START → retrieve_context → (router) → nó gerador → save_and_learn → END
    graph.set_entry_point("retrieve_context")
    graph.add_conditional_edges("retrieve_context", _entry_router)
    for node in _GENERATION_NODES:
        graph.add_edge(node, "save_and_learn")
    graph.add_edge("save_and_learn", END)

    return graph.compile()


def end_session(session_id: str, feedback_score=None):
    """Gera resumo final da sessão, salva e indexa no RAG se resolvido.

    Exemplo de uso:
        from src.agent.graph import end_session
        end_session("556184288058@s.whatsapp.net", feedback_score=5)
    """
    try:
        history = load_session_history(session_id)
        if not history:
            return
        summary_data = _summarizer.summarize(history)
        save_summary(session_id, summary_data, feedback_score=feedback_score)
        if summary_data.get("resolved"):
            topics = summary_data.get("key_topics", [])
            _rag.index_summary(
                session_id=session_id,
                summary=summary_data["summary"],
                title=", ".join(topics[:2]),
            )
    except Exception as e:
        import logging
        logging.getLogger("agent-clinic.graph").error(f"[end_session] erro: {e}")
