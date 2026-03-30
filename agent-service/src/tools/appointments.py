"""Operações de banco de dados para agendamentos de consultas."""

import os
import uuid
import logging
from contextlib import contextmanager
from typing import List, Dict

from src.tools.agenda import ESPECIALIDADES, CONVENIOS, HORARIOS_MOCK  # noqa: F401

logger = logging.getLogger("agent-clinic.appointments")


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


def db_agendar(phone: str, nome: str, especialidade: str, data: str, horario: str, convenio: str,
               doctor_id: str = "", doctor_name: str = "") -> Dict:
    """Insere um novo agendamento no banco e retorna protocolo e resumo."""
    try:
        raw = uuid.uuid4().hex[:8].upper()
        protocolo = f"#{raw[:4]}-{raw[4:]}"

        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO appointments
                        (phone, patient_name, specialty, appointment_date, appointment_time,
                         insurance, protocol, doctor_id, doctor_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (phone, nome, especialidade, data, horario, convenio, protocolo,
                     doctor_id or None, doctor_name or None),
                )
            conn.commit()

        logger.info(f"[db_agendar] agendamento criado: protocolo={protocolo} phone={phone}")
        return {
            "sucesso": True,
            "protocolo": protocolo,
            "resumo": {
                "paciente": nome,
                "especialidade": especialidade,
                "data": data,
                "horario": horario,
                "convenio": convenio,
            },
        }
    except Exception as e:
        logger.error(f"[db_agendar] erro: {e}")
        return {"sucesso": False, "mensagem": f"Erro ao agendar consulta: {e}"}


def db_buscar_consultas(phone: str, nome: str) -> List[Dict]:
    """Busca consultas ativas pelo telefone e nome do paciente."""
    try:
        primeiro_nome = nome.split()[0] if nome.strip() else nome
        nome_like = f"%{primeiro_nome}%"

        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, specialty, appointment_date, appointment_time, insurance, protocol
                    FROM appointments
                    WHERE phone = %s
                      AND LOWER(patient_name) LIKE LOWER(%s)
                      AND status = 'active'
                    ORDER BY created_at ASC
                    """,
                    (phone, nome_like),
                )
                rows = cur.fetchall()

        result = [
            {
                "id": str(row[0]),
                "especialidade": row[1],
                "data": row[2],
                "horario": row[3],
                "convenio": row[4],
                "protocolo": row[5],
            }
            for row in rows
        ]
        logger.info(f"[db_buscar_consultas] encontradas {len(result)} consultas para phone={phone}")
        return result
    except Exception as e:
        logger.error(f"[db_buscar_consultas] erro: {e}")
        return []


def db_cancelar(phone: str, nome: str, protocolo: str) -> Dict:
    """Cancela uma consulta ativa pelo protocolo, telefone e nome."""
    try:
        primeiro_nome = nome.split()[0] if nome.strip() else nome
        nome_like = f"%{primeiro_nome}%"

        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE appointments
                    SET status = 'cancelled', updated_at = NOW()
                    WHERE protocol = %s
                      AND phone = %s
                      AND LOWER(patient_name) LIKE LOWER(%s)
                      AND status = 'active'
                    """,
                    (protocolo, phone, nome_like),
                )
                affected = cur.rowcount
            conn.commit()

        if affected > 0:
            logger.info(f"[db_cancelar] consulta cancelada: protocolo={protocolo} phone={phone}")
            return {"sucesso": True, "mensagem": f"Consulta {protocolo} cancelada com sucesso."}
        else:
            logger.warning(f"[db_cancelar] consulta não encontrada: protocolo={protocolo} phone={phone}")
            return {"sucesso": False, "mensagem": "Consulta não encontrada ou já cancelada."}
    except Exception as e:
        logger.error(f"[db_cancelar] erro: {e}")
        return {"sucesso": False, "mensagem": f"Erro ao cancelar consulta: {e}"}


def db_alterar(phone: str, nome: str, protocolo: str, nova_data: str, novo_horario: str) -> Dict:
    """Altera data e horário de uma consulta ativa."""
    try:
        primeiro_nome = nome.split()[0] if nome.strip() else nome
        nome_like = f"%{primeiro_nome}%"

        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE appointments
                    SET appointment_date = %s, appointment_time = %s, updated_at = NOW()
                    WHERE protocol = %s
                      AND phone = %s
                      AND LOWER(patient_name) LIKE LOWER(%s)
                      AND status = 'active'
                    """,
                    (nova_data, novo_horario, protocolo, phone, nome_like),
                )
                affected = cur.rowcount
            conn.commit()

        if affected > 0:
            logger.info(f"[db_alterar] consulta remarcada: protocolo={protocolo} nova_data={nova_data} novo_horario={novo_horario}")
            return {
                "sucesso": True,
                "mensagem": f"Consulta {protocolo} remarcada para {nova_data} às {novo_horario}.",
            }
        else:
            logger.warning(f"[db_alterar] consulta não encontrada: protocolo={protocolo} phone={phone}")
            return {"sucesso": False, "mensagem": "Consulta não encontrada ou já cancelada."}
    except Exception as e:
        logger.error(f"[db_alterar] erro: {e}")
        return {"sucesso": False, "mensagem": f"Erro ao alterar consulta: {e}"}
