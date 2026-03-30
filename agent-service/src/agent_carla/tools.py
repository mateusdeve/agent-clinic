import re
import time
from langchain_core.tools import tool


# Mapa de abreviações comuns da internet
ABREVIACOES = {
    r'\bvocê\b': 'vc',
    r'\bVocê\b': 'Vc',
    r'\bpara\b': 'pra',
    r'\bPara\b': 'Pra',
    r'\bInstagram\b': 'Insta',
    r'\binstagram\b': 'insta',
    r'\bWhatsApp\b': 'wpp',
    r'\bwhatsapp\b': 'wpp',
    r'\btambém\b': 'tbm',
    r'\bTambém\b': 'Tbm',
    r'\bestou\b': 'tô',
    r'\bEstou\b': 'Tô',
    r'\bestá\b': 'tá',
    r'\bEstá\b': 'Tá',
    r'\bporque\b': 'pq',
    r'\bPorque\b': 'Pq',
    r'\bhoje\b': 'hj',
    r'\bHoje\b': 'Hj',
    r'\bbeleza\b': 'blz',
    r'\bBeleza\b': 'Blz',
    r'\btudo\b': 'td',
    r'\bTudo\b': 'Td',
    r'\bmensagem\b': 'msg',
    r'\bMensagem\b': 'Msg',
    r'\bdepois\b': 'dps',
    r'\bDepois\b': 'Dps',
}


@tool
def aplicar_abreviacoes(texto: str) -> dict:
    """Aplica abreviações comuns da internet ao texto para torná-lo mais informal e natural."""
    texto_abreviado = texto
    abreviacoes_aplicadas = []

    for padrao, abreviacao in ABREVIACOES.items():
        if re.search(padrao, texto_abreviado):
            abreviacoes_aplicadas.append(f"{padrao} -> {abreviacao}")
            texto_abreviado = re.sub(padrao, abreviacao, texto_abreviado)

    return {
        "texto": texto_abreviado,
        "abreviacoes_aplicadas": abreviacoes_aplicadas,
        "total_abreviacoes": len(abreviacoes_aplicadas),
    }


@tool
def quebrar_em_mensagens(texto: str) -> dict:
    """Quebra o texto formatado em mensagens individuais para envio sequencial no WhatsApp.
    Cada parágrafo se torna uma mensagem separada, simulando envio humano."""
    # Separa por linhas duplas (parágrafos)
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]

    # Se ficou tudo numa mensagem só, tenta separar por quebra simples
    if len(paragrafos) == 1:
        linhas = [l.strip() for l in texto.split("\n") if l.strip()]
        if len(linhas) > 1:
            paragrafos = linhas

    mensagens = []
    for i, paragrafo in enumerate(paragrafos):
        mensagens.append({
            "ordem": i + 1,
            "conteudo": paragrafo,
            "caracteres": len(paragrafo),
        })

    return {
        "mensagens": mensagens,
        "total_mensagens": len(mensagens),
    }


@tool
def enviar_mensagem(mensagem: str, ordem: int) -> dict:
    """Simula o envio de uma mensagem individual no WhatsApp.
    Em produção, aqui seria a integração com a API do WhatsApp."""
    # Simula delay de digitação humana (proporcional ao tamanho)
    delay = min(len(mensagem) * 0.02, 2.0)  # max 2s
    time.sleep(delay)

    return {
        "sucesso": True,
        "ordem": ordem,
        "mensagem_enviada": mensagem,
        "caracteres": len(mensagem),
        "delay_simulado": f"{delay:.1f}s",
        "status": "entregue",
    }
