"""Lógica de seleção de médicos com verificação de disponibilidade e balanceamento de carga."""

import os
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger("agent-clinic.doctors")

# Mapeamento dia da semana Python (Mon=0) → banco (Seg=1)
_DIA_SEMANA_MAP = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}


@contextmanager
def _get_db():
    import psycopg2
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não configurado")
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def _gerar_slots(hora_inicio: time, hora_fim: time, duracao_min: int) -> List[str]:
    """Gera lista de horários disponíveis de hora_inicio até hora_fim com intervalos de duracao_min."""
    slots = []
    atual = datetime.combine(datetime.today(), hora_inicio)
    fim = datetime.combine(datetime.today(), hora_fim)
    while atual < fim:
        slots.append(atual.strftime("%H:%M"))
        atual += timedelta(minutes=duracao_min)
    return slots


def _normalizar_data(data: str) -> Optional[str]:
    """Converte texto de data para formato YYYY-MM-DD."""
    try:
        import dateparser
        dt = dateparser.parse(
            data,
            languages=["pt"],
            settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False},
        )
        if dt:
            return dt.strftime("%Y-%m-%d"), dt
        return None, None
    except Exception as e:
        logger.warning(f"[doctors] não conseguiu normalizar data '{data}': {e}")
        return None, None


def buscar_horarios_com_medico(especialidade: str, data: str) -> List[Dict]:
    """
    Retorna horários disponíveis por médico para a especialidade e data.
    Aplica balanceamento de carga: médicos com menos consultas no dia aparecem primeiro.

    Retorno:
        [
            {
                "doctor_id": "uuid",
                "medico": "Dr. Carlos Mendes",
                "slots": ["08:00", "08:30", ...]
            },
            ...
        ]
    """
    data_formatada, dt = _normalizar_data(data)
    if not data_formatada or not dt:
        logger.warning(f"[doctors] data inválida: '{data}'")
        return []

    dia_semana_db = _DIA_SEMANA_MAP.get(dt.weekday(), -1)

    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                # Busca médicos da especialidade que trabalham nesse dia
                cur.execute(
                    """
                    SELECT d.id, d.nome, ds.hora_inicio, ds.hora_fim, ds.duracao_consulta
                    FROM doctors d
                    JOIN doctor_schedules ds ON ds.doctor_id = d.id
                    WHERE d.especialidade = %s
                      AND d.ativo = true
                      AND ds.dia_semana = %s
                    ORDER BY d.nome
                    """,
                    (especialidade, dia_semana_db),
                )
                medicos = cur.fetchall()

                if not medicos:
                    logger.info(f"[doctors] nenhum médico de {especialidade} disponível em {data_formatada} (dia_semana={dia_semana_db})")
                    return []

                resultado = []
                for doc_id, nome, h_inicio, h_fim, duracao in medicos:
                    # Horários já ocupados para esse médico na data
                    cur.execute(
                        """
                        SELECT appointment_time FROM appointments
                        WHERE doctor_id = %s
                          AND appointment_date = %s
                          AND status = 'active'
                        """,
                        (str(doc_id), data_formatada),
                    )
                    ocupados = {str(r[0])[:5] for r in cur.fetchall()}  # "HH:MM"

                    # Gera todos os slots e remove os ocupados
                    todos_slots = _gerar_slots(h_inicio, h_fim, duracao)
                    livres = [s for s in todos_slots if s not in ocupados]

                    if livres:
                        resultado.append({
                            "doctor_id": str(doc_id),
                            "medico": nome,
                            "slots": livres,
                            "consultas_hoje": len(ocupados),  # usado no balanceamento
                        })

                # Balanceamento de carga: médico com menos consultas no dia aparece primeiro
                resultado.sort(key=lambda d: d["consultas_hoje"])

                # Remove campo interno de contagem antes de retornar
                for item in resultado:
                    item.pop("consultas_hoje", None)

                logger.info(f"[doctors] {len(resultado)} médico(s) disponível(is) para {especialidade} em {data_formatada}")
                return resultado

    except Exception as e:
        logger.error(f"[doctors] erro ao buscar horários: {e}")
        return []


def buscar_medico_por_id(doctor_id: str) -> Optional[Dict]:
    """Retorna dados de um médico pelo ID."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, nome, crm, especialidade FROM doctors WHERE id = %s",
                    (doctor_id,),
                )
                row = cur.fetchone()
        if row:
            return {"id": str(row[0]), "nome": row[1], "crm": row[2], "especialidade": row[3]}
        return None
    except Exception as e:
        logger.error(f"[doctors] erro ao buscar médico {doctor_id}: {e}")
        return None


def buscar_medico_por_nome(nome: str) -> Optional[Dict]:
    """Busca médico pelo nome parcial (case-insensitive)."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nome, crm, especialidade
                    FROM doctors
                    WHERE ativo = true AND LOWER(nome) LIKE LOWER(%s)
                    ORDER BY nome LIMIT 1
                    """,
                    (f"%{nome}%",),
                )
                row = cur.fetchone()
        if row:
            return {"id": str(row[0]), "nome": row[1], "crm": row[2], "especialidade": row[3]}
        return None
    except Exception as e:
        logger.error(f"[doctors] erro ao buscar médico por nome '{nome}': {e}")
        return None


def listar_medicos(especialidade: Optional[str] = None) -> List[Dict]:
    """Lista médicos ativos, opcionalmente filtrados por especialidade."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                if especialidade:
                    cur.execute(
                        "SELECT id, nome, crm, especialidade FROM doctors WHERE ativo = true AND especialidade = %s ORDER BY nome",
                        (especialidade,),
                    )
                else:
                    cur.execute(
                        "SELECT id, nome, crm, especialidade FROM doctors WHERE ativo = true ORDER BY especialidade, nome"
                    )
                rows = cur.fetchall()
        return [{"id": str(r[0]), "nome": r[1], "crm": r[2], "especialidade": r[3]} for r in rows]
    except Exception as e:
        logger.error(f"[doctors] erro ao listar médicos: {e}")
        return []
