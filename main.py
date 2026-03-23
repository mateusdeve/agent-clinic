from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage

from src.agent.graph import build_graph
from src.agent_carla.graph import build_carla_graph
from src.core.extraction import extract_data, determine_etapa, default_state
from src.observability.langfuse_setup import get_langfuse


def _formatar_com_carla(carla_graph, texto: str) -> list:
    """Passa o texto da Sofia pela Carla para reformatar e quebrar em mensagens."""
    carla_state = {
        "texto_original": texto,
        "texto_formatado": "",
        "mensagens_quebradas": [],
        "mensagens_enviadas": [],
        "etapa": "processar",
    }

    result = carla_graph.invoke(carla_state)
    return result.get("mensagens_quebradas", [])


def _exibir_mensagens_carla(mensagens: list):
    """Exibe as mensagens formatadas pela Carla como envios separados."""
    for msg in mensagens:
        print(f"\n  Sofia: {msg['conteudo']}")


def main():
    print("=" * 60)
    print("  Clinica Saude+ — Sofia + Carla (integrado)")
    print("  Sofia responde | Carla reformata e envia")
    print("  Digite 'sair' para encerrar o atendimento")
    print("=" * 60)
    print()

    graph = build_graph()
    carla_graph = build_carla_graph()

    state = default_state()

    # Mensagem inicial do agente
    result = graph.invoke(state)
    state.update(result)

    ultima_msg = state["messages"][-1].content if state["messages"] else ""

    # Primeira mensagem passa pela Carla
    mensagens = _formatar_com_carla(carla_graph, ultima_msg)
    _exibir_mensagens_carla(mensagens)
    print()

    while True:
        try:
            user_input = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nAté logo!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("sair", "exit", "quit"):
            print("\n  Sofia: ate mais!")
            break

        state["messages"] = state["messages"] + [HumanMessage(content=user_input)]

        # Extrai dados da conversa e determina próxima etapa
        extracted = extract_data(state["messages"])

        for key in ["nome_paciente", "especialidade", "motivo_consulta", "convenio",
                     "data_agendamento", "horario_agendamento"]:
            value = extracted.get(key)
            if value and value != "null" and str(value) != "None":
                state[key] = str(value)

        state["etapa"] = determine_etapa(state, extracted)

        # Sofia gera a resposta
        result = graph.invoke(state)
        state.update(result)

        ultima_msg = state["messages"][-1].content if state["messages"] else ""

        # Carla reformata e quebra em mensagens
        mensagens = _formatar_com_carla(carla_graph, ultima_msg)
        _exibir_mensagens_carla(mensagens)
        print()

        if state.get("etapa") == "encerrar":
            langfuse = get_langfuse()
            langfuse.flush()
            print("[Atendimento encerrado]")
            break

    # Flush final do Langfuse
    try:
        langfuse = get_langfuse()
        langfuse.flush()
    except Exception:
        pass


if __name__ == "__main__":
    main()
