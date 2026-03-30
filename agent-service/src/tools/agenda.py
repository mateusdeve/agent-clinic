import uuid
from langchain_core.tools import tool
from typing import List, Dict

ESPECIALIDADES = [
    "Clínica Geral",
    "Cardiologia",
    "Dermatologia",
    "Ortopedia",
    "Ginecologia",
    "Pediatria",
]

CONVENIOS = [
    "Unimed",
    "Bradesco Saúde",
    "SulAmérica",
    "Amil",
    "Particular",
]

HORARIOS_MOCK = {
    "manhã": ["08:00", "09:00", "09:30", "10:00", "11:00"],
    "tarde": ["13:00", "14:00", "14:30", "15:00", "16:00"],
    "integral": ["08:00", "09:00", "09:30", "10:00", "11:00", "13:00", "14:00", "14:30", "15:00", "16:00"],
}


@tool
def verificar_disponibilidade(especialidade: str, data: str) -> dict:
    """Verifica horários disponíveis para uma especialidade em uma data específica.

    Args:
        especialidade: A especialidade médica desejada.
        data: A data desejada para a consulta.
    """
    from src.tools.doctors import buscar_horarios_com_medico

    especialidade_normalizada = especialidade.strip().title()

    if especialidade_normalizada not in ESPECIALIDADES:
        return {
            "disponivel": False,
            "mensagem": f"Especialidade '{especialidade}' não encontrada. Especialidades disponíveis: {', '.join(ESPECIALIDADES)}",
            "medicos": [],
        }

    medicos = buscar_horarios_com_medico(especialidade_normalizada, data)

    if not medicos:
        return {
            "disponivel": False,
            "especialidade": especialidade_normalizada,
            "data": data,
            "medicos": [],
            "mensagem": f"Sem horários disponíveis para {especialidade_normalizada} em {data}.",
        }

    return {
        "disponivel": True,
        "especialidade": especialidade_normalizada,
        "data": data,
        "medicos": medicos,
        "mensagem": f"Horários disponíveis para {especialidade_normalizada} em {data}.",
    }


@tool
def agendar_consulta(
    phone: str,
    nome: str,
    especialidade: str,
    data: str,
    horario: str,
    convenio: str,
) -> dict:
    """Realiza o agendamento de uma consulta salvando no banco de dados.

    Args:
        phone: Telefone/session_id do paciente.
        nome: Nome completo do paciente.
        especialidade: Especialidade médica.
        data: Data da consulta.
        horario: Horário da consulta.
        convenio: Convênio ou Particular.
    """
    from src.tools.appointments import db_agendar
    return db_agendar(phone=phone, nome=nome, especialidade=especialidade, data=data, horario=horario, convenio=convenio)


@tool
def buscar_consultas_paciente(phone: str, nome: str) -> list:
    """Busca as consultas ativas de um paciente pelo telefone e nome.

    Args:
        phone: Telefone/session_id do paciente.
        nome: Nome do paciente (aceita primeiro nome).
    """
    from src.tools.appointments import db_buscar_consultas
    return db_buscar_consultas(phone=phone, nome=nome)


@tool
def cancelar_consulta_db(phone: str, nome: str, protocolo: str) -> dict:
    """Cancela uma consulta ativa pelo protocolo.

    Args:
        phone: Telefone/session_id do paciente.
        nome: Nome do paciente.
        protocolo: Protocolo da consulta a cancelar (ex: #ABCD-1234).
    """
    from src.tools.appointments import db_cancelar
    return db_cancelar(phone=phone, nome=nome, protocolo=protocolo)


@tool
def alterar_consulta_db(phone: str, nome: str, protocolo: str, nova_data: str, novo_horario: str) -> dict:
    """Altera a data e horário de uma consulta ativa.

    Args:
        phone: Telefone/session_id do paciente.
        nome: Nome do paciente.
        protocolo: Protocolo da consulta a alterar (ex: #ABCD-1234).
        nova_data: Nova data desejada para a consulta.
        novo_horario: Novo horário desejado para a consulta.
    """
    from src.tools.appointments import db_alterar
    return db_alterar(phone=phone, nome=nome, protocolo=protocolo, nova_data=nova_data, novo_horario=novo_horario)
