"""Endpoints CRUD para medicos — lista, criacao, edicao, horarios e bloqueios."""

import logging
from typing import Optional, List

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.deps import get_db_for_tenant, require_role

logger = logging.getLogger("agent-clinic.api.doctors")

router = APIRouter(prefix="/api/doctors", tags=["doctors"])

# ─── Modelos ──────────────────────────────────────────────────────────────────


class DoctorCreate(BaseModel):
    nome: str
    especialidade: str
    crm: str
    user_id: Optional[str] = None


class DoctorUpdate(BaseModel):
    nome: Optional[str] = None
    especialidade: Optional[str] = None
    crm: Optional[str] = None
    user_id: Optional[str] = None


class ScheduleSlot(BaseModel):
    day_of_week: int  # 0-6 (0=domingo, conforme convencao do banco)
    start_time: str   # "HH:MM"
    end_time: str     # "HH:MM"


class ScheduleUpdate(BaseModel):
    slots: List[ScheduleSlot]


class BlockedSlotCreate(BaseModel):
    blocked_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    reason: Optional[str] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _paginate(page: int, per_page: int) -> tuple:
    """Retorna (limit, offset) para paginacao."""
    limit = max(1, min(per_page, 100))
    offset = (max(1, page) - 1) * limit
    return limit, offset


# ─── Endpoints — Medicos ──────────────────────────────────────────────────────


@router.get("/")
def list_doctors(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("admin", "recepcionista", "medico")),
    conn=Depends(get_db_for_tenant),
):
    """Lista medicos com paginacao e busca opcional por nome ou especialidade. DOC-01."""
    limit, offset = _paginate(page, per_page)

    try:
        with conn.cursor() as cur:
            # Monta filtro de busca
            if search:
                where = "WHERE (LOWER(nome) LIKE LOWER(%s) OR LOWER(especialidade) LIKE LOWER(%s))"
                search_param = f"%{search}%"
                params_count = (search_param, search_param)
                params_items = (search_param, search_param, limit, offset)
            else:
                where = ""
                params_count = ()
                params_items = (limit, offset)

            cur.execute(
                f"SELECT COUNT(*) FROM doctors {where}",
                params_count,
            )
            total = cur.fetchone()[0]

            # SELECT adaptado: user_id adicionado na migration 004
            # ativo/is_active: o bot usa 'ativo', vamos tentar ambos
            cur.execute(
                f"""
                SELECT id, nome, especialidade, crm, user_id
                FROM doctors
                {where}
                ORDER BY nome
                LIMIT %s OFFSET %s
                """,
                params_items,
            )
            rows = cur.fetchall()

        items = [
            {
                "id": str(r[0]),
                "nome": r[1],
                "especialidade": r[2],
                "crm": r[3],
                "user_id": str(r[4]) if r[4] else None,
            }
            for r in rows
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, -(-total // per_page)),
        }
    except Exception as e:
        logger.error(f"[doctors] list_doctors error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar medicos",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_doctor(
    body: DoctorCreate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Cria novo medico. DOC-02."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO doctors (nome, especialidade, crm, user_id, tenant_id)
                VALUES (%s, %s, %s, %s, current_setting('app.tenant_id')::uuid)
                RETURNING id, nome, especialidade, crm, user_id
                """,
                (body.nome, body.especialidade, body.crm, body.user_id),
            )
            row = cur.fetchone()
        conn.commit()
        logger.info(f"[doctors] medico criado: {body.nome} (CRM {body.crm})")
        return {
            "id": str(row[0]),
            "nome": row[1],
            "especialidade": row[2],
            "crm": row[3],
            "user_id": str(row[4]) if row[4] else None,
        }
    except Exception as e:
        logger.error(f"[doctors] create_doctor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar medico",
        )


@router.put("/{doctor_id}")
def update_doctor(
    doctor_id: str,
    body: DoctorUpdate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Edita perfil do medico. DOC-02."""
    # Monta SET clause dinamico com campos nao-nulos
    fields = {}
    if body.nome is not None:
        fields["nome"] = body.nome
    if body.especialidade is not None:
        fields["especialidade"] = body.especialidade
    if body.crm is not None:
        fields["crm"] = body.crm
    if body.user_id is not None:
        fields["user_id"] = body.user_id

    if not fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo fornecido para atualizacao",
        )

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [doctor_id]

    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE doctors
                SET {set_clause}
                WHERE id = %s
                RETURNING id, nome, especialidade, crm, user_id
                """,
                values,
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medico nao encontrado",
            )
        conn.commit()
        logger.info(f"[doctors] medico atualizado: {doctor_id}")
        return {
            "id": str(row[0]),
            "nome": row[1],
            "especialidade": row[2],
            "crm": row[3],
            "user_id": str(row[4]) if row[4] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[doctors] update_doctor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar medico",
        )


# ─── Endpoints — Horarios ─────────────────────────────────────────────────────


@router.get("/{doctor_id}/schedules")
def get_schedules(
    doctor_id: str,
    current_user: dict = Depends(require_role("admin", "recepcionista", "medico")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna grade de disponibilidade semanal do medico. DOC-03."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, doctor_id, dia_semana, hora_inicio::text, hora_fim::text
                FROM doctor_schedules
                WHERE doctor_id = %s
                ORDER BY dia_semana, hora_inicio
                """,
                (doctor_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "id": str(r[0]),
                "doctor_id": str(r[1]),
                "day_of_week": r[2],
                "start_time": r[3],
                "end_time": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"[doctors] get_schedules error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar horarios",
        )


@router.put("/{doctor_id}/schedules")
def set_schedules(
    doctor_id: str,
    body: ScheduleUpdate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Define grade de disponibilidade semanal (DELETE + INSERT atomico). DOC-03."""
    try:
        with conn.cursor() as cur:
            # Verifica se medico existe
            cur.execute("SELECT id FROM doctors WHERE id = %s", (doctor_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medico nao encontrado",
                )

            # DELETE todos os horarios existentes e INSERT novos
            cur.execute("DELETE FROM doctor_schedules WHERE doctor_id = %s", (doctor_id,))

            for slot in body.slots:
                cur.execute(
                    """
                    INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim, tenant_id)
                    VALUES (%s, %s, %s, %s, current_setting('app.tenant_id')::uuid)
                    """,
                    (doctor_id, slot.day_of_week, slot.start_time, slot.end_time),
                )

            # Busca resultado apos inserir
            cur.execute(
                """
                SELECT id, doctor_id, dia_semana, hora_inicio::text, hora_fim::text
                FROM doctor_schedules
                WHERE doctor_id = %s
                ORDER BY dia_semana, hora_inicio
                """,
                (doctor_id,),
            )
            rows = cur.fetchall()

        conn.commit()
        logger.info(f"[doctors] horarios atualizados para medico {doctor_id}: {len(body.slots)} slot(s)")

        return [
            {
                "id": str(r[0]),
                "doctor_id": str(r[1]),
                "day_of_week": r[2],
                "start_time": r[3],
                "end_time": r[4],
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[doctors] set_schedules error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao salvar horarios",
        )


# ─── Endpoints — Bloqueios ────────────────────────────────────────────────────


@router.get("/{doctor_id}/blocked-slots")
def get_blocked_slots(
    doctor_id: str,
    current_user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna slots bloqueados do medico. AGENDA-06."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, doctor_id, blocked_date::text, start_time::text, end_time::text,
                       reason, created_at::text
                FROM blocked_slots
                WHERE doctor_id = %s
                ORDER BY blocked_date, start_time
                """,
                (doctor_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "id": str(r[0]),
                "doctor_id": str(r[1]),
                "blocked_date": r[2],
                "start_time": r[3],
                "end_time": r[4],
                "reason": r[5],
                "created_at": r[6],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"[doctors] get_blocked_slots error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar bloqueios",
        )


@router.post("/{doctor_id}/blocked-slots", status_code=status.HTTP_201_CREATED)
def create_blocked_slot(
    doctor_id: str,
    body: BlockedSlotCreate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Bloqueia horario do medico. AGENDA-06."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO blocked_slots
                    (doctor_id, blocked_date, start_time, end_time, reason, tenant_id)
                VALUES (%s, %s, %s, %s, %s, current_setting('app.tenant_id')::uuid)
                RETURNING id, doctor_id, blocked_date::text, start_time::text,
                          end_time::text, reason, created_at::text
                """,
                (
                    doctor_id,
                    body.blocked_date,
                    body.start_time,
                    body.end_time,
                    body.reason,
                ),
            )
            row = cur.fetchone()
        conn.commit()
        logger.info(f"[doctors] slot bloqueado para medico {doctor_id}: {body.blocked_date}")
        return {
            "id": str(row[0]),
            "doctor_id": str(row[1]),
            "blocked_date": row[2],
            "start_time": row[3],
            "end_time": row[4],
            "reason": row[5],
            "created_at": row[6],
        }
    except Exception as e:
        logger.error(f"[doctors] create_blocked_slot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao bloquear horario",
        )


@router.delete("/blocked-slots/{slot_id}")
def delete_blocked_slot(
    slot_id: str,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Remove bloqueio de horario. AGENDA-06."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM blocked_slots WHERE id = %s RETURNING id",
                (slot_id,),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloqueio nao encontrado",
            )
        conn.commit()
        logger.info(f"[doctors] bloqueio removido: {slot_id}")
        return {"message": "Bloqueio removido com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[doctors] delete_blocked_slot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao remover bloqueio",
        )
