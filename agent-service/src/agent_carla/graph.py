from langgraph.graph import StateGraph, END

from src.agent_carla.state import CarlaState
from src.agent_carla.nodes import processar_texto, quebrar_mensagens, enviar


def build_carla_graph():
    """Constrói o grafo do agente Carla.

    Fluxo linear:
    [START] → processar_texto → quebrar_mensagens → enviar → [END]

    1. processar_texto: LLM reestrutura o texto da Márcia em parágrafos curtos
    2. quebrar_mensagens: Separa em mensagens individuais para WhatsApp
    3. enviar: Simula envio sequencial com delay humano
    """
    graph = StateGraph(CarlaState)

    # Adiciona os nós
    graph.add_node("processar_texto", processar_texto)
    graph.add_node("quebrar_mensagens", quebrar_mensagens)
    graph.add_node("enviar", enviar)

    # Fluxo linear: processar → quebrar → enviar → END
    graph.set_entry_point("processar_texto")
    graph.add_edge("processar_texto", "quebrar_mensagens")
    graph.add_edge("quebrar_mensagens", "enviar")
    graph.add_edge("enviar", END)

    return graph.compile()
