"""Endpoints REST para gerenciamento de campanhas de mensagens em massa.

Cobre criacao de campanhas, visualizacao de segmento, listagem, detalhes,
destinatarios por campanha e envio rapido de template (quick-send).

Requer autenticacao via JWT. Admin para operacoes de escrita/campanha.
Admin e recepcionista para quick-send.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.deps import get_db_for_tenant, require_role
from src.api.templates import render_template

logger = logging.getLogger("agent-clinic.api.campaigns")

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

# Router secundario para quick-send no namespace de conversas
conversations_router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# ─── Modelos ──────────────────────────────────────────────────────────────────


class CampaignCreate(BaseModel):
    nome: str
    template_id: str
    filtros: dict = {}  # keys: especialidade, ultimo_agendamento_range, status_paciente


class SendTemplateBody(BaseModel):
    template_id: str
    variaveis: dict = {}


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _build_segment_query(filtros: dict) -> tuple:
    """Constroi WHERE clause e params para filtro de segmento de pacientes.

    Filtros suportados:
    - especialidade: filtra por especialidade da ultima consulta
    - ultimo_agendamento_range: 'lt30d' | '30-90d' | 'gt90d' desde ultima consulta
    - status_paciente: 'ativo' (consulta nos ultimos 90d) | 'inativo' (sem consulta)
    """
    conditions = []
    params = []

    if filtros.get("especialidade"):
        conditions.append("""
            EXISTS (
                SELECT 1 FROM appointments a2
                JOIN doctors d ON a2.doctor_id = d.id
                WHERE a2.patient_id = p.id
                  AND d.especialidade = %s
            )
        """)
        params.append(filtros["especialidade"])

    range_filter = filtros.get("ultimo_agendamento_range")
    if range_filter == "lt30d":
        conditions.append("""
            EXISTS (
                SELECT 1 FROM appointments a3
                WHERE a3.patient_id = p.id
                  AND COALESCE(a3.data_agendamento, a3.appointment_date::date) >= NOW() - INTERVAL '30 days'
            )
        """)
    elif range_filter == "30-90d":
        conditions.append("""
            EXISTS (
                SELECT 1 FROM appointments a3
                WHERE a3.patient_id = p.id
                  AND COALESCE(a3.data_agendamento, a3.appointment_date::date) BETWEEN NOW() - INTERVAL '90 days' AND NOW() - INTERVAL '30 days'
            )
        """)
    elif range_filter == "gt90d":
        conditions.append("""
            (
                NOT EXISTS (
                    SELECT 1 FROM appointments a3
                    WHERE a3.patient_id = p.id
                      AND COALESCE(a3.data_agendamento, a3.appointment_date::date) >= NOW() - INTERVAL '90 days'
                )
            )
        """)

    status_paciente = filtros.get("status_paciente")
    if status_paciente == "ativo":
        conditions.append("""
            EXISTS (
                SELECT 1 FROM appointments a4
                WHERE a4.patient_id = p.id
                  AND COALESCE(a4.data_agendamento, a4.appointment_date::date) >= NOW() - INTERVAL '90 days'
            )
        """)
    elif status_paciente == "inativo":
        conditions.append("""
            NOT EXISTS (
                SELECT 1 FROM appointments a4
                WHERE a4.patient_id = p.id
                  AND COALESCE(a4.data_agendamento, a4.appointment_date::date) >= NOW() - INTERVAL '90 days'
            )
        """)

    where = " AND ".join(conditions) if conditions else "TRUE"
    return where, params


def _get_patient_variaveis(patient_row: tuple, appointment_row: Optional[tuple]) -> dict:
    """Monta dict de variaveis para render_template a partir de dados do paciente."""
    variaveis = {
        "nome": patient_row[1] or "",
        "telefone": patient_row[2] or "",
    }
    if appointment_row:
        variaveis["data"] = str(appointment_row[0]) if appointment_row[0] else ""
        variaveis["hora"] = str(appointment_row[1]) if appointment_row[1] else ""
        variaveis["medico"] = appointment_row[2] or ""
        variaveis["especialidade"] = appointment_row[3] or ""
    return variaveis


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/preview-segment")
def preview_segment(
    especialidade: Optional[str] = Query(None),
    ultimo_agendamento_range: Optional[str] = Query(None),
    status_paciente: Optional[str] = Query(None),
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Previa do segmento de pacientes para campanha (D-11).

    Retorna count total e amostra de 5 pacientes que correspondem ao filtro.
    """
    try:
        filtros = {}
        if especialidade:
            filtros["especialidade"] = especialidade
        if ultimo_agendamento_range:
            filtros["ultimo_agendamento_range"] = ultimo_agendamento_range
        if status_paciente:
            filtros["status_paciente"] = status_paciente

        where, params = _build_segment_query(filtros)

        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM patients p WHERE p.phone IS NOT NULL AND ({where})",
                params,
            )
            count = cur.fetchone()[0]

            cur.execute(
                f"""
                SELECT p.id::text, p.nome, p.phone
                FROM patients p
                WHERE p.phone IS NOT NULL AND ({where})
                ORDER BY p.nome ASC
                LIMIT 5
                """,
                params,
            )
            sample_rows = cur.fetchall()

        sample = [
            {"id": row[0], "nome": row[1], "phone": row[2]}
            for row in sample_rows
        ]

        logger.info(f"[campaigns] preview_segment: count={count} filtros={filtros}")
        return {"count": count, "sample": sample}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[campaigns] preview_segment error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao calcular segmento",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_campaign(
    body: CampaignCreate,
    user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Cria campanha e popula campaign_recipients com pacientes do segmento (D-12, WPP-14).

    Fluxo:
    1. Valida que template existe
    2. Cria registro de campanha com status='rascunho'
    3. Busca pacientes do segmento (filtros)
    4. Para cada paciente, insere campaign_recipients com variaveis pre-calculadas
    5. Atualiza total_recipients e muda status para 'enviando'
    """
    try:
        # Validar template
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, corpo FROM message_templates WHERE id = %s",
                (body.template_id,),
            )
            template_row = cur.fetchone()

        if not template_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template nao encontrado",
            )

        # Criar campanha
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO campaigns (tenant_id, nome, template_id, filtros, status, created_by)
                VALUES (
                    current_setting('app.tenant_id')::uuid,
                    %s, %s, %s, 'rascunho', %s
                )
                RETURNING id
                """,
                (body.nome, body.template_id, json.dumps(body.filtros), user["user_id"]),
            )
            campaign_id = str(cur.fetchone()[0])
        conn.commit()

        # Buscar pacientes do segmento
        where, params = _build_segment_query(body.filtros)

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT p.id::text, p.nome, p.phone
                FROM patients p
                WHERE p.phone IS NOT NULL AND ({where})
                ORDER BY p.nome ASC
                """,
                params,
            )
            patients = cur.fetchall()

        # Inserir recipients com variaveis pre-calculadas
        recipient_count = 0
        for patient_row in patients:
            patient_id = patient_row[0]
            phone = patient_row[2]

            # Buscar ultima consulta do paciente
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COALESCE(a.data_agendamento::text, a.appointment_date::text),
                        COALESCE(a.appointment_time::text, a.horario_agendamento::text),
                        d.nome,
                        d.especialidade
                    FROM appointments a
                    LEFT JOIN doctors d ON a.doctor_id = d.id
                    WHERE a.patient_id = %s
                    ORDER BY COALESCE(a.data_agendamento, a.appointment_date::date) DESC
                    LIMIT 1
                    """,
                    (patient_id,),
                )
                appt = cur.fetchone()

            variaveis = _get_patient_variaveis(patient_row, appt)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO campaign_recipients (campaign_id, patient_id, phone, variaveis, status)
                    VALUES (%s, %s, %s, %s, 'pendente')
                    """,
                    (campaign_id, patient_id, phone, json.dumps(variaveis)),
                )
            recipient_count += 1

        # Atualizar total e status
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE campaigns
                SET total_recipients = %s, status = 'enviando'
                WHERE id = %s
                RETURNING id, nome, template_id, status, total_recipients, created_at
                """,
                (recipient_count, campaign_id),
            )
            campaign = cur.fetchone()
        conn.commit()

        logger.info(f"[campaigns] create_campaign: id={campaign_id} recipients={recipient_count}")
        return {
            "id": str(campaign[0]),
            "nome": campaign[1],
            "template_id": str(campaign[2]),
            "status": campaign[3],
            "total_recipients": campaign[4],
            "created_at": str(campaign[5]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[campaigns] create_campaign error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar campanha",
        )


@router.get("/")
def list_campaigns(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Lista campanhas paginadas com stats de entrega agregadas (D-15)."""
    try:
        offset = (page - 1) * per_page

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM campaigns")
            total = cur.fetchone()[0]

            cur.execute(
                """
                SELECT
                    c.id,
                    c.nome,
                    mt.nome AS template_nome,
                    c.status,
                    c.total_recipients,
                    c.created_at,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'enviado'), 0) AS enviado,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'entregue'), 0) AS entregue,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'lido'), 0) AS lido,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'falha'), 0) AS falha
                FROM campaigns c
                LEFT JOIN message_templates mt ON c.template_id = mt.id
                ORDER BY c.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (per_page, offset),
            )
            rows = cur.fetchall()

        items = [
            {
                "id": str(row[0]),
                "nome": row[1],
                "template_nome": row[2],
                "status": row[3],
                "total_recipients": row[4],
                "created_at": str(row[5]),
                "stats": {
                    "enviado": row[6],
                    "entregue": row[7],
                    "lido": row[8],
                    "falha": row[9],
                },
            }
            for row in rows
        ]

        logger.info(f"[campaigns] list_campaigns: total={total} page={page}")
        return {"items": items, "total": total, "page": page, "per_page": per_page}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[campaigns] list_campaigns error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar campanhas",
        )


@router.get("/{campaign_id}")
def get_campaign(
    campaign_id: str,
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna detalhes de uma campanha com stats de entrega agregadas."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.id,
                    c.nome,
                    mt.nome AS template_nome,
                    c.status,
                    c.total_recipients,
                    c.created_at,
                    c.enviado_at,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'enviado'), 0) AS enviado,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'entregue'), 0) AS entregue,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'lido'), 0) AS lido,
                    COALESCE((SELECT COUNT(*) FROM campaign_recipients cr WHERE cr.campaign_id = c.id AND cr.status = 'falha'), 0) AS falha
                FROM campaigns c
                LEFT JOIN message_templates mt ON c.template_id = mt.id
                WHERE c.id = %s
                """,
                (campaign_id,),
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campanha nao encontrada",
            )

        logger.info(f"[campaigns] get_campaign: id={campaign_id}")
        return {
            "id": str(row[0]),
            "nome": row[1],
            "template_nome": row[2],
            "status": row[3],
            "total_recipients": row[4],
            "created_at": str(row[5]),
            "enviado_at": str(row[6]) if row[6] else None,
            "stats": {
                "enviado": row[7],
                "entregue": row[8],
                "lido": row[9],
                "falha": row[10],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[campaigns] get_campaign error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar campanha",
        )


@router.get("/{campaign_id}/recipients")
def get_campaign_recipients(
    campaign_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Lista destinatarios de uma campanha com status de entrega por recipient (D-16)."""
    try:
        # Verificar que campanha existe
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM campaigns WHERE id = %s", (campaign_id,))
            if not cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campanha nao encontrada",
                )

        offset = (page - 1) * per_page

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM campaign_recipients WHERE campaign_id = %s",
                (campaign_id,),
            )
            total = cur.fetchone()[0]

            cur.execute(
                """
                SELECT
                    cr.id::text,
                    cr.phone,
                    p.nome AS patient_nome,
                    cr.status,
                    cr.erro,
                    cr.sent_at
                FROM campaign_recipients cr
                LEFT JOIN patients p ON cr.patient_id = p.id
                WHERE cr.campaign_id = %s
                ORDER BY cr.updated_at DESC
                LIMIT %s OFFSET %s
                """,
                (campaign_id, per_page, offset),
            )
            rows = cur.fetchall()

        items = [
            {
                "id": row[0],
                "phone": row[1],
                "patient_nome": row[2],
                "status": row[3],
                "erro": row[4],
                "sent_at": str(row[5]) if row[5] else None,
            }
            for row in rows
        ]

        logger.info(f"[campaigns] get_campaign_recipients: campaign_id={campaign_id} total={total}")
        return {"items": items, "total": total, "page": page, "per_page": per_page}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[campaigns] get_campaign_recipients error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar destinatarios da campanha",
        )


# ─── Quick-send (namespace /api/conversations) ────────────────────────────────


@conversations_router.post("/{phone}/send-template")
async def send_template(
    phone: str,
    body: SendTemplateBody,
    user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Envia template rapido para um numero de telefone (WPP-13, D-13).

    Fluxo:
    1. Busca template pelo template_id
    2. Renderiza corpo com variaveis fornecidas
    3. Envia via Evolution API com indicador de digitacao
    4. Persiste na tabela conversations

    Retorna {"status": "sent"}.
    """
    try:
        # Lazy imports para evitar circulares
        from src.api.webhook import evolution_client

        # Buscar template
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, corpo FROM message_templates WHERE id = %s",
                (body.template_id,),
            )
            template_row = cur.fetchone()

        if not template_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template nao encontrado",
            )

        # Renderizar mensagem
        rendered = render_template(template_row[1], body.variaveis)

        # Enviar via Evolution API
        await evolution_client.send_message_with_typing(phone, rendered)

        # Persistir na tabela conversations
        session_id = f"{phone}@s.whatsapp.net"
        metadata = json.dumps({
            "sent_by": user["user_id"],
            "sent_by_human": True,
            "template_id": body.template_id,
            "quick_send": True,
        })

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (session_id, role, content, metadata)
                VALUES (%s, %s, %s, %s)
                """,
                (session_id, "assistant", rendered, metadata),
            )
        conn.commit()

        logger.info(f"[campaigns] send_template: phone={phone} template_id={body.template_id}")
        return {"status": "sent"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[campaigns] send_template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar template",
        )
