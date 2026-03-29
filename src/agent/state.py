from typing import TypedDict, List, Any
from langchain_core.messages import BaseMessage


class ClinicaState(TypedDict):
    messages: List[BaseMessage]
    nome_paciente: str
    motivo_consulta: str
    especialidade: str
    data_nascimento: str
    convenio: str
    data_agendamento: str
    horario_agendamento: str
    etapa: str  # recepcionar | identificar_motivo | coletar_dados | verificar_agenda | confirmar | encerrar | cancelar_consulta | alterar_consulta
    session_id: str
    rag_context: str
    protocolo_consulta: str
    nova_data: str
    novo_horario: str
    medico_agendado: str    # nome do médico selecionado
    medico_id: str          # UUID do médico selecionado
    medicos_disponiveis: List[Any]  # lista de {doctor_id, medico, slots} da última busca
    periodo: str            # "manhã" | "tarde" | ""
    apresentacao_feita: bool  # True depois da primeira apresentação
    medico_mencionado: str  # nome do médico que o paciente pediu (ex: "Marcos")
    agendamento_concluido: bool  # True após salvar consulta — evita re-salvar e re-apresentação
    protocolo_gerado: str  # protocolo da última consulta confirmada nesta sessão
