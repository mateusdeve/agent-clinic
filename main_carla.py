import os
from dotenv import load_dotenv

load_dotenv()

from src.agent_carla.graph import build_carla_graph
from src.observability.langfuse_setup import get_langfuse


# Texto de exemplo para teste
TEXTO_EXEMPLO = """Oi! Tudo bem? Então, o Stories10x é uma ferramenta incrível que vai transformar a forma como você cria conteúdo para o Instagram. Com ele, você consegue gerar stories profissionais em poucos minutos, sem precisar de designer. Estou aqui pra te ajudar com qualquer dúvida! O plano básico custa R$29,90 por mês e você tem acesso a mais de 500 templates exclusivos. Para assinar, é só acessar o link https://stories10x.com/assinar e escolher o melhor plano para você. Se precisar de mais detalhes ou tiver outra dúvida, me avisa! Ah, e também temos um grupo no WhatsApp onde compartilhamos dicas exclusivas. O link é https://chat.whatsapp.com/abc123. Qualquer dúvida, tô aqui!"""


def main():
    print("=" * 60)
    print("  Carla — Revisora de Mensagens da Márcia (Stories10x)")
    print("  Digite o texto da Márcia ou 'sair' para encerrar")
    print("  Digite 'exemplo' para usar um texto de teste")
    print("=" * 60)
    print()

    graph = build_carla_graph()

    while True:
        try:
            print("-" * 40)
            user_input = input("\nTexto da Márcia (ou 'exemplo'): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nAté logo!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("sair", "exit", "quit"):
            print("\nCarla: Até mais!")
            break

        if user_input.lower() == "exemplo":
            texto = TEXTO_EXEMPLO
            print(f"\n[Usando texto de exemplo]\n")
        else:
            texto = user_input

        # Estado inicial
        state = {
            "texto_original": texto,
            "texto_formatado": "",
            "mensagens_quebradas": [],
            "mensagens_enviadas": [],
            "etapa": "processar",
        }

        print("\n[Processando texto...]")

        # Executa o grafo completo
        result = graph.invoke(state)

        # Exibe resultado
        print("\n" + "=" * 40)
        print("  TEXTO REVISADO (completo)")
        print("=" * 40)
        print(result["texto_formatado"])

        print("\n" + "=" * 40)
        print("  MENSAGENS PARA ENVIO")
        print("=" * 40)

        for msg in result["mensagens_quebradas"]:
            print(f"\n  [{msg['ordem']}] ({msg['caracteres']} chars)")
            print(f"  {msg['conteudo']}")

        print(f"\n  Total: {len(result['mensagens_quebradas'])} mensagens")

        # Status de envio
        print("\n" + "=" * 40)
        print("  STATUS DE ENVIO")
        print("=" * 40)

        for env in result["mensagens_enviadas"]:
            print(f"  msg {env['ordem']}: {env['status']} (delay: {env['delay_simulado']})")

        print(f"\n  Todas as {len(result['mensagens_enviadas'])} mensagens enviadas!")
        print()

    # Flush final
    try:
        langfuse = get_langfuse()
        langfuse.flush()
    except Exception:
        pass


if __name__ == "__main__":
    main()
