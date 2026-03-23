"""Follow-up pós-consulta e lembretes — agendamento e disparo de mensagens."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from src.memory.persistence import _get_db

logger = logging.getLogger("agent-clinic.followup")


def _parse_appointment_datetime(data: str, horario: str) -> Optional[datetime]:
    """Converte data e horário em texto para datetime real."""
    try:
        import dateparser
        texto = f"{data} {horario}"
        dt = dateparser.parse(
            texto,
            languages=["pt"],
            settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": False},
        )
        return dt
    except Exception as e:
        logger.warning(f"[followup] não conseguiu parsear data '{data} {horario}': {e}")
        return None


def criar_followup(
    phone: str,
    nome: str,
    especialidade: str,
    data_consulta: str,
    protocolo: str,
    horario: str = "",
    horas_depois: int = 24,
) -> None:
    """Cria follow-up (pós-consulta) e lembrete (pré-consulta) automaticamente."""
    try:
        # Resolve datetime real da consulta
        appointment_dt = _parse_appointment_datetime(data_consulta, horario)

        # Follow-up: 24h após a consulta (ou 24h após agora se não parseou)
        if appointment_dt:
            followup_em = appointment_dt + timedelta(hours=horas_depois)
        else:
            followup_em = datetime.utcnow() + timedelta(hours=horas_depois)

        with _get_db() as conn:
            with conn.cursor() as cur:
                # Cria follow-up pós-consulta
                cur.execute(
                    """
                    INSERT INTO follow_ups
                        (phone, nome, especialidade, data_consulta, protocolo,
                         enviar_em, tipo, appointment_datetime)
                    VALUES (%s, %s, %s, %s, %s, %s, 'followup', %s)
                    """,
                    (phone, nome, especialidade, data_consulta, protocolo,
                     followup_em, appointment_dt),
                )

                # Cria lembrete pré-consulta (2h antes) se souber o datetime
                if appointment_dt and appointment_dt > datetime.utcnow():
                    lembrete_em = appointment_dt - timedelta(hours=2)
                    if lembrete_em > datetime.utcnow():
                        cur.execute(
                            """
                            INSERT INTO follow_ups
                                (phone, nome, especialidade, data_consulta, protocolo,
                                 enviar_em, tipo, appointment_datetime)
                            VALUES (%s, %s, %s, %s, %s, %s, 'lembrete', %s)
                            """,
                            (phone, nome, especialidade, data_consulta, protocolo,
                             lembrete_em, appointment_dt),
                        )
                        logger.info(f"[followup] Lembrete criado para {phone} em {lembrete_em}")

            conn.commit()
        logger.info(f"[followup] Follow-up criado para {phone} em {followup_em}")
    except Exception as e:
        logger.error(f"[followup] criar_followup error: {e}")


def buscar_followups_pendentes() -> List[dict]:
    """Retorna follow-ups que já passaram do horário de envio e ainda não foram enviados."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, phone, nome, especialidade, data_consulta, protocolo, tipo,
                           TO_CHAR(appointment_datetime AT TIME ZONE 'America/Sao_Paulo', 'HH24:MI') AS horario
                    FROM follow_ups
                    WHERE enviado = false AND enviar_em <= NOW()
                    ORDER BY enviar_em ASC
                    LIMIT 50
                    """,
                )
                rows = cur.fetchall()
        return [
            {
                "id": str(r[0]),
                "phone": r[1],
                "nome": r[2],
                "especialidade": r[3],
                "data_consulta": r[4],
                "protocolo": r[5],
                "tipo": r[6] or "followup",
                "horario": r[7] or "",
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"[followup] buscar_followups_pendentes error: {e}")
        return []


def marcar_enviado(followup_id: str) -> None:
    """Marca follow-up como enviado."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE follow_ups SET enviado = true, enviado_em = NOW() WHERE id = %s",
                    (followup_id,),
                )
            conn.commit()
    except Exception as e:
        logger.error(f"[followup] marcar_enviado error: {e}")


def montar_mensagem(fu: dict) -> str:
    """Monta a mensagem certa dependendo do tipo (followup ou lembrete)."""
    nome_curto = (fu.get("nome") or "").split()[0] or "paciente"
    especialidade = fu.get("especialidade") or "consulta"
    data = fu.get("data_consulta") or ""
    horario = fu.get("horario") or ""
    tipo = fu.get("tipo", "followup")

    if tipo == "lembrete":
        quando = f"hj às {horario}" if horario else f"dia {data}"
        return (
            f"Oi {nome_curto}! aqui é a Sofia da Clínica Saúde+\n\n"
            f"só passando pra lembrar que vc tem uma consulta de {especialidade} "
            f"{quando}\n\n"
            "qualquer coisa é só falar por aqui"
        )
    else:
        return (
            f"Oi {nome_curto}! aqui é a Sofia da Clínica Saúde+\n\n"
            f"queria saber como foi sua consulta de {especialidade} no dia {data}\n\n"
            "espero que tudo tenha corrido bem"
        )


# Mantém compatibilidade com chamadas antigas
def montar_mensagem_followup(nome: str, especialidade: str, data_consulta: str) -> str:
    return montar_mensagem({
        "nome": nome, "especialidade": especialidade,
        "data_consulta": data_consulta, "tipo": "followup"
    })
