"""Endpoints REST para gestao de pacientes — listagem, busca, criacao, edicao e historico.

Todos os endpoints usam RLS via get_db_for_tenant para isolamento de tenant automatico.
"""

import logging
from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_for_tenant, require_role

logger = logging.getLogger("agent-clinic.api.patients")

router = APIRouter(prefix="/api/patients", tags=["patients"])


# ─── Modelos ──────────────────────────────────────────────────────────────────


class PatientCreate(BaseModel):
    nome: str
    phone: str
    data_nascimento: Optional[str] = None  # ISO date YYYY-MM-DD
    notas: Optional[str] = None


class PatientUpdate(BaseModel):
    nome: Optional[str] = None
    phone: Optional[str] = None
    data_nascimento: Optional[str] = None
    notas: Optional[str] = None


class PatientOut(BaseModel):
    id: str
    phone: str
    nome: str
    data_nascimento: Optional[str] = None
    notas: Optional[str] = None
    total_consultas: int
    created_at: str


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int


class ConversationMessage(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/", response_model=PaginatedResponse)
def list_patients(
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Lista pacientes com busca por nome ou telefone. Retorna resposta paginada.

    PAT-01: Permite filtro por nome (case-insensitive parcial) ou telefone.
    """
    try:
        offset = (page - 1) * per_page
        base_sql = """
            SELECT
                p.id,
                p.phone,
                p.nome,
                p.data_nascimento,
                p.notas,
                (SELECT COUNT(*) FROM appointments WHERE appointments.patient_id = p.id) AS total_consultas,
                p.created_at
            FROM patients p
        """
        count_sql = "SELECT COUNT(*) FROM patients p"
        params = []
        where_clause = ""

        if search:
            where_clause = " WHERE LOWER(p.nome) LIKE LOWER(%s) OR p.phone LIKE %s"
            search_param = f"%{search}%"
            params = [search_param, search_param]

        order_limit = " ORDER BY p.nome ASC LIMIT %s OFFSET %s"

        with conn.cursor() as cur:
            cur.execute(count_sql + where_clause, params)
            total = cur.fetchone()[0]

            cur.execute(base_sql + where_clause + order_limit, params + [per_page, offset])
            rows = cur.fetchall()

        items = [
            PatientOut(
                id=str(row[0]),
                phone=row[1],
                nome=row[2],
                data_nascimento=str(row[3]) if row[3] else None,
                notas=row[4],
                total_consultas=row[5],
                created_at=str(row[6]),
            )
            for row in rows
        ]

        logger.info(f"[patients] list_patients: total={total} page={page}")
        return PaginatedResponse(items=[i.dict() for i in items], total=total, page=page, per_page=per_page)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[patients] list_patients error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao listar pacientes")


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_patient(
    body: PatientCreate,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Cria novo paciente no tenant atual.

    PAT-02: tenant_id inserido via current_setting('app.tenant_id') (RLS).
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO patients (phone, nome, data_nascimento, notas, tenant_id)
                VALUES (%s, %s, %s, %s, current_setting('app.tenant_id')::uuid)
                RETURNING id, phone, nome, data_nascimento, notas, created_at
                """,
                (body.phone, body.nome, body.data_nascimento, body.notas),
            )
            row = cur.fetchone()
        conn.commit()

        logger.info(f"[patients] create_patient: phone={body.phone} nome={body.nome}")
        return PatientOut(
            id=str(row[0]),
            phone=row[1],
            nome=row[2],
            data_nascimento=str(row[3]) if row[3] else None,
            notas=row[4],
            total_consultas=0,
            created_at=str(row[5]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[patients] create_patient error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar paciente")


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: str,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna um paciente pelo ID ou 404 se nao encontrado."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id,
                    p.phone,
                    p.nome,
                    p.data_nascimento,
                    p.notas,
                    (SELECT COUNT(*) FROM appointments WHERE appointments.patient_id = p.id) AS total_consultas,
                    p.created_at
                FROM patients p
                WHERE p.id = %s
                """,
                (patient_id,),
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado")

        logger.info(f"[patients] get_patient: id={patient_id}")
        return PatientOut(
            id=str(row[0]),
            phone=row[1],
            nome=row[2],
            data_nascimento=str(row[3]) if row[3] else None,
            notas=row[4],
            total_consultas=row[5],
            created_at=str(row[6]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[patients] get_patient error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao buscar paciente")


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: str,
    body: PatientUpdate,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Atualiza dados de um paciente. Apenas campos nao-nulos sao alterados.

    PAT-03: Atualizacao parcial (PATCH semantics via PUT com campos opcionais).
    """
    try:
        updates = {}
        if body.nome is not None:
            updates["nome"] = body.nome
        if body.phone is not None:
            updates["phone"] = body.phone
        if body.data_nascimento is not None:
            updates["data_nascimento"] = body.data_nascimento
        if body.notas is not None:
            updates["notas"] = body.notas

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar",
            )

        set_clause = ", ".join(f"{col} = %s" for col in updates)
        values = list(updates.values()) + [patient_id]

        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE patients
                SET {set_clause}
                WHERE id = %s
                RETURNING id, phone, nome, data_nascimento, notas, created_at
                """,
                values,
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado")

        conn.commit()

        # total_consultas nao retornado pelo UPDATE — buscar separado
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM appointments WHERE patient_id = %s",
                (patient_id,),
            )
            total_consultas = cur.fetchone()[0]

        logger.info(f"[patients] update_patient: id={patient_id} fields={list(updates.keys())}")
        return PatientOut(
            id=str(row[0]),
            phone=row[1],
            nome=row[2],
            data_nascimento=str(row[3]) if row[3] else None,
            notas=row[4],
            total_consultas=total_consultas,
            created_at=str(row[5]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[patients] update_patient error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao atualizar paciente")


@router.get("/{patient_id}/appointments")
def get_patient_appointments(
    patient_id: str,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna historico de consultas de um paciente.

    PAT-04: JOIN com doctors para incluir nome e especialidade do medico.
    Usa colunas reais da tabela: appointment_date, appointment_time (bot legacy).
    """
    try:
        # Verificar se paciente existe
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM patients WHERE id = %s", (patient_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado")

            cur.execute(
                """
                SELECT
                    a.id,
                    COALESCE(a.appointment_date::text, a.data_agendamento::text) AS data_agendamento,
                    COALESCE(a.appointment_time::text, a.horario_agendamento::text) AS horario,
                    a.status,
                    d.nome AS doctor_nome,
                    d.especialidade
                FROM appointments a
                LEFT JOIN doctors d ON a.doctor_id = d.id
                WHERE a.patient_id = %s
                ORDER BY
                    COALESCE(a.appointment_date, a.data_agendamento) DESC,
                    COALESCE(a.appointment_time, a.horario_agendamento) DESC
                """,
                (patient_id,),
            )
            rows = cur.fetchall()

        result = [
            {
                "id": str(row[0]),
                "data_agendamento": row[1],
                "horario": row[2],
                "status": row[3],
                "doctor_nome": row[4],
                "especialidade": row[5],
            }
            for row in rows
        ]

        logger.info(f"[patients] get_patient_appointments: patient_id={patient_id} count={len(result)}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[patients] get_patient_appointments error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao buscar consultas do paciente")


@router.get("/{patient_id}/conversations")
def get_patient_conversations(
    patient_id: str,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna historico de conversas WhatsApp de um paciente.

    PAT-05: Busca conversations pelo telefone do paciente.
    session_id na tabela conversations contem o numero de telefone (formato: phone@s.whatsapp.net ou phone).
    """
    try:
        with conn.cursor() as cur:
            # Busca o telefone do paciente
            cur.execute("SELECT phone FROM patients WHERE id = %s", (patient_id,))
            row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente nao encontrado")

        phone = row[0]

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, role, content, created_at::text
                FROM conversations
                WHERE session_id LIKE %s
                ORDER BY created_at ASC
                """,
                (f"%{phone}%",),
            )
            rows = cur.fetchall()

        result = [
            ConversationMessage(
                id=row[0],
                role=row[1],
                content=row[2],
                created_at=row[3],
            ).dict()
            for row in rows
        ]

        logger.info(f"[patients] get_patient_conversations: patient_id={patient_id} phone={phone} count={len(result)}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[patients] get_patient_conversations error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao buscar conversas do paciente")
