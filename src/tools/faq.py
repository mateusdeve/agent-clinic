from langchain_core.tools import tool

FAQ_BASE = {
    "horario": {
        "palavras_chave": ["horário", "horario", "funciona", "abre", "fecha", "expediente"],
        "resposta": "A Clínica Saúde+ funciona de Segunda a Sexta, das 7h às 19h, e aos Sábados, das 7h às 12h.",
    },
    "endereco": {
        "palavras_chave": ["endereço", "endereco", "localização", "localizacao", "onde fica", "como chegar"],
        "resposta": "Nosso endereço é Rua das Flores, 123 - Centro. Telefone: (11) 3456-7890.",
    },
    "convenios": {
        "palavras_chave": ["convênio", "convenio", "plano", "aceita", "aceitam"],
        "resposta": "Aceitamos os seguintes convênios: Unimed, Bradesco Saúde, SulAmérica e Amil. Também atendemos pacientes particulares.",
    },
    "exame_sangue": {
        "palavras_chave": ["exame de sangue", "jejum", "sangue", "coleta"],
        "resposta": "Para exames de sangue, é necessário jejum de 8 a 12 horas. Você pode beber água normalmente.",
    },
    "exame_imagem": {
        "palavras_chave": ["exame de imagem", "raio-x", "ultrassom", "ressonância", "tomografia"],
        "resposta": "Para exames de imagem, entre em contato com nossa recepção pelo telefone (11) 3456-7890 para orientações específicas sobre preparo.",
    },
    "documentos": {
        "palavras_chave": ["documento", "levar", "preciso levar", "necessário"],
        "resposta": "Para sua consulta, traga: RG, carteirinha do convênio (se tiver) e pedido médico (se houver).",
    },
    "especialidades": {
        "palavras_chave": ["especialidade", "médico", "doutor", "quais áreas"],
        "resposta": "Nossas especialidades são: Clínica Geral, Cardiologia, Dermatologia, Ortopedia, Ginecologia e Pediatria.",
    },
}


@tool
def buscar_faq(pergunta: str) -> dict:
    """Busca resposta para dúvidas frequentes sobre a clínica.

    Args:
        pergunta: A pergunta ou dúvida do paciente.
    """
    pergunta_lower = pergunta.lower()

    for topico, info in FAQ_BASE.items():
        for palavra in info["palavras_chave"]:
            if palavra in pergunta_lower:
                return {
                    "encontrado": True,
                    "topico": topico,
                    "resposta": info["resposta"],
                }

    return {
        "encontrado": False,
        "resposta": "Não encontrei informações sobre essa dúvida. Recomendo ligar para a clínica: (11) 3456-7890.",
    }
