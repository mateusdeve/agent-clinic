"""Endpoints REST para gestao de consultas — listagem, criacao, edicao, cancelamento e status.

Todos os endpoints usam RLS via get_db_for_tenant para isolamento de tenant automatico.
Medicos so visualizam as proprias consultas (AGENDA-07).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_for_tenant, require_role

logger = logging.getLogger("agent-clinic.api.appointments")

router = APIRouter(prefix="/api/appointments", tags=["appointments"])

ALLOWED_STATUSES = {"agendado", "confirmado", "realizado", "cancelado", "active", "cancelled"}


# ─── Modelos ──────────────────────────────────────────────────────────────────


class AppointmentCreate(BaseModel):
    patient_id: str
    doctor_id: str
    data_agendamento: str  # ISO date YYYY-MM-DD
    horario: str           # HH:MM
    especialidade: Optional[str] = None


class AppointmentUpdate(BaseModel):
    doctor_id: Optional[str] = None
    data_agendamento: Optional[str] = None
    horario: Optional[str] = None
    especialidade: Optional[str] = None


class AppointmentCancel(BaseModel):
    motivo: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


class AppointmentOut(BaseModel):
    id: str
    patient_id: str
    patient_nome: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_nome: Optional[str] = None
    especialidade: Optional[str] = None
    data_agendamento: Optional[str] = None
    horario: Optional[str] = None
    status: str
    motivo_cancelamento: Optional[str] = None
    created_at: str


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _row_to_appointment_out(row) -> AppointmentOut:
    """Converte linha do banco para AppointmentOut.

    Compativel com coluna appointment_date/appointment_time (bot legacy)
    e data_agendamento/horario_agendamento (novo CRUD).
    """
    return AppointmentOut(
        id=str(row[0]),
        patient_id=str(row[1]),
        patient_nome=row[2],
        doctor_id=str(row[3]) if row[3] else None,
        doctor_nome=row[4],
        especialidade=row[5],
        data_agendamento=str(row[6]) if row[6] else None,
        horario=str(row[7]) if row[7] else None,
        status=row[8] or "agendado",
        motivo_cancelamento=row[9] if len(row) > 9 else None,
        created_at=str(row[10]) if len(row) > 10 else "",
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/", response_model=PaginatedResponse)
def list_appointments(
    doctor_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    filter_status: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    conn=Depends(get_db_for_tenant),
):
    """Lista consultas com filtros por medico, data e status. Retorna resposta paginada.

    AGENDA-07: Medico so ve as proprias consultas — doctor_id forcado pelo user_id via doctors.user_id.
    """
    try:
        # AGENDA-07: Medico so pode ver as proprias consultas
        if current_user["role"] == "medico":
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM doctors WHERE user_id = %s",
                    (current_user["user_id"],),
                )
                doctor_row = cur.fetchone()

            if not doctor_row:
                # Medico sem vinculo com doctor — retornar lista vazia por seguranca
                logger.info(f"[appointments] medico sem vinculo doctor: user_id={current_user['user_id']}")
                return PaginatedResponse(items=[], total=0, page=page, per_page=per_page)

            # Forcando doctor_id independente do que vier no request
            doctor_id = str(doctor_row[0])
        elif current_user["role"] not in ("admin", "recepcionista"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissao insuficiente")

        offset = (page - 1) * per_page
        filters = []
        params = []

        if doctor_id:
            filters.append("a.doctor_id = %s")
            params.append(doctor_id)
        if date_from:
            filters.append(
                "(COALESCE(a.appointment_date::date, a.data_agendamento) >= %s::date)"
            )
            params.append(date_from)
        if date_to:
            filters.append(
                "(COALESCE(a.appointment_date::date, a.data_agendamento) <= %s::date)"
            )
            params.append(date_to)
        if filter_status:
            filters.append("a.status = %s")
            params.append(filter_status)

        where = ("WHERE " + " AND ".join(filters)) if filters else ""

        base_sql = f"""
            SELECT
                a.id,
                a.patient_id,
                p.nome AS patient_nome,
                a.doctor_id,
                d.nome AS doctor_nome,
                d.especialidade,
                COALESCE(a.appointment_date::date, a.data_agendamento) AS data_agendamento,
                COALESCE(a.appointment_time, a.horario_agendamento::text) AS horario,
                a.status,
                a.motivo_cancelamento,
                a.created_at
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            LEFT JOIN doctors d ON a.doctor_id = d.id
            {where}
            ORDER BY
                COALESCE(a.appointment_date::date, a.data_agendamento) ASC,
                COALESCE(a.appointment_time, a.horario_agendamento::text) ASC
            LIMIT %s OFFSET %s
        """

        count_sql = f"""
            SELECT COUNT(*) FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            LEFT JOIN doctors d ON a.doctor_id = d.id
            {where}
        """

        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]

            cur.execute(base_sql, params + [per_page, offset])
            rows = cur.fetchall()

        items = [_row_to_appointment_out(row).dict() for row in rows]
        logger.info(f"[appointments] list_appointments: total={total} page={page} role={current_user['role']}")
        return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[appointments] list_appointments error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao listar consultas")


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_appointment(
    body: AppointmentCreate,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Cria nova consulta com status inicial 'agendado'.

    AGENDA-02: Inserção com patient_id e doctor_id.
    AGENDA-05: status sempre inicia como 'agendado'.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO appointments
                    (patient_id, doctor_id, data_agendamento, horario_agendamento,
                     specialty, status, tenant_id)
                VALUES (%s, %s, %s, %s, %s, 'agendado', current_setting('app.tenant_id')::uuid)
                RETURNING
                    id, patient_id, NULL AS patient_nome,
                    doctor_id, NULL AS doctor_nome,
                    specialty, data_agendamento, horario_agendamento,
                    status, motivo_cancelamento, created_at
                """,
                (
                    body.patient_id,
                    body.doctor_id,
                    body.data_agendamento,
                    body.horario,
                    body.especialidade,
                ),
            )
            row = cur.fetchone()
        conn.commit()

        logger.info(f"[appointments] create_appointment: patient_id={body.patient_id} doctor_id={body.doctor_id}")
        return _row_to_appointment_out(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[appointments] create_appointment error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar consulta")


@router.put("/{appointment_id}")
def update_appointment(
    appointment_id: str,
    body: AppointmentUpdate,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Edita ou remarca uma consulta.

    AGENDA-03: Atualizacao parcial de medico, data, horario ou especialidade.
    """
    try:
        updates = {}
        if body.doctor_id is not None:
            updates["doctor_id"] = body.doctor_id
        if body.data_agendamento is not None:
            updates["data_agendamento"] = body.data_agendamento
        if body.horario is not None:
            updates["horario_agendamento"] = body.horario
        if body.especialidade is not None:
            updates["specialty"] = body.especialidade

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar",
            )

        set_clause = ", ".join(f"{col} = %s" for col in updates)
        values = list(updates.values()) + [appointment_id]

        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE appointments
                SET {set_clause}
                WHERE id = %s
                RETURNING
                    id, patient_id, NULL AS patient_nome,
                    doctor_id, NULL AS doctor_nome,
                    specialty, data_agendamento, horario_agendamento,
                    status, motivo_cancelamento, created_at
                """,
                values,
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta nao encontrada")

        conn.commit()
        logger.info(f"[appointments] update_appointment: id={appointment_id} fields={list(updates.keys())}")
        return _row_to_appointment_out(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[appointments] update_appointment error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao atualizar consulta")


@router.patch("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: str,
    body: AppointmentCancel = None,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Cancela uma consulta. Nao cancela se ja estiver cancelada.

    AGENDA-04: Seta status='cancelado' com motivo opcional.
    """
    try:
        motivo = body.motivo if body else None

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE appointments
                SET status = 'cancelado', motivo_cancelamento = %s
                WHERE id = %s AND status != 'cancelado'
                RETURNING
                    id, patient_id, NULL AS patient_nome,
                    doctor_id, NULL AS doctor_nome,
                    specialty, data_agendamento, horario_agendamento,
                    status, motivo_cancelamento, created_at
                """,
                (motivo, appointment_id),
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consulta nao encontrada ou ja cancelada",
            )

        conn.commit()
        logger.info(f"[appointments] cancel_appointment: id={appointment_id}")
        return _row_to_appointment_out(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[appointments] cancel_appointment error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao cancelar consulta")


@router.patch("/{appointment_id}/status")
def update_appointment_status(
    appointment_id: str,
    body: StatusUpdate,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Atualiza o status de uma consulta.

    AGENDA-05: Statuses permitidos: agendado, confirmado, realizado, cancelado, active, cancelled.
    """
    try:
        if body.status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status invalido. Permitidos: {', '.join(sorted(ALLOWED_STATUSES))}",
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE appointments
                SET status = %s
                WHERE id = %s
                RETURNING
                    id, patient_id, NULL AS patient_nome,
                    doctor_id, NULL AS doctor_nome,
                    specialty, data_agendamento, horario_agendamento,
                    status, motivo_cancelamento, created_at
                """,
                (body.status, appointment_id),
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta nao encontrada")

        conn.commit()
        logger.info(f"[appointments] update_appointment_status: id={appointment_id} status={body.status}")
        return _row_to_appointment_out(row)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[appointments] update_appointment_status error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao atualizar status da consulta")
