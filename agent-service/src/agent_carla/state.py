from typing import TypedDict


class CarlaState(TypedDict):
    texto_original: str          # Texto corrido recebido da Márcia
    texto_formatado: str         # Texto reestruturado em parágrafos curtos
    mensagens_quebradas: list    # Lista de mensagens individuais para envio
    mensagens_enviadas: list     # Mensagens já enviadas (mock)
    etapa: str                   # processar | quebrar | enviar | concluido
