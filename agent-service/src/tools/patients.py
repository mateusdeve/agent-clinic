"""Operações de pacientes — reconhecimento e persistência por número."""

import logging
from typing import Optional
from src.memory.persistence import _get_db

logger = logging.getLogger("agent-clinic.patients")


def buscar_paciente(phone: str) -> Optional[dict]:
    """Busca paciente pelo telefone. Retorna dict com nome etc ou None."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT phone, nome, total_consultas FROM patients WHERE phone = %s",
                    (phone,),
                )
                row = cur.fetchone()
        if row:
            return {"phone": row[0], "nome": row[1], "total_consultas": row[2]}
        return None
    except Exception as e:
        logger.error(f"[patients] buscar_paciente error: {e}")
        return None


def salvar_paciente(phone: str, nome: str) -> None:
    """Cria paciente se não existir, ou atualiza nome e incrementa consultas."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO patients (phone, nome, total_consultas)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (phone) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        ultima_visita = NOW(),
                        total_consultas = patients.total_consultas + 1
                    """,
                    (phone, nome),
                )
            conn.commit()
        logger.info(f"[patients] Paciente salvo: {phone} — {nome}")
    except Exception as e:
        logger.error(f"[patients] salvar_paciente error: {e}")
