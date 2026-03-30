"""Endpoints REST para o dashboard principal — KPIs e graficos.

Fornece metricas de consultas do dia, ocupacao, no-shows, confirmacoes
pendentes, conversas ativas, proximas consultas e tendencias historicas.

Requer autenticacao via JWT. Charts exige role admin.
"""

import logging
from datetime import date, timedelta, datetime
from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_db_for_tenant, require_role

logger = logging.getLogger("agent-clinic.api.dashboard")

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/stats")
async def get_dashboard_stats(
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna KPIs do dia e proximas consultas (DASH-01, DASH-02, DASH-03).

    KPIs retornados:
    - consultas_hoje: total de consultas nao-canceladas do dia
    - taxa_ocupacao: percentual de ocupacao (consultas_hoje / total_slots)
    - no_shows: cancelamentos do dia
    - confirmacoes_pendentes: consultas com status 'agendado' hoje
    - conversas_ativas: sessoes unicas com mensagem nas ultimas 24h
    - proximas_consultas: lista de ate 20 consultas do dia ordenadas por horario
    """
    try:
        hoje = date.today()

        with conn.cursor() as cur:
            # ── KPIs de consultas do dia ──────────────────────────────────────
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status NOT IN ('cancelado','cancelled'))   AS consultas_hoje,
                    COUNT(*) FILTER (WHERE status IN ('cancelado','cancelled'))        AS no_shows,
                    COUNT(*) FILTER (WHERE status = 'agendado')                       AS confirmacoes_pendentes,
                    COUNT(*)                                                            AS total_slots
                FROM appointments
                WHERE COALESCE(data_agendamento, appointment_date::date) = %s
                """,
                (hoje,),
            )
            row = cur.fetchone()

        consultas_hoje = row[0] or 0
        no_shows = row[1] or 0
        confirmacoes_pendentes = row[2] or 0
        total_slots = row[3] or 0
        taxa_ocupacao = round(consultas_hoje / total_slots, 2) if total_slots > 0 else 0.0

        # ── Conversas ativas (ultimas 24h) ────────────────────────────────────
        conversas_ativas = 0
        try:
            since = datetime.utcnow() - timedelta(hours=24)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(DISTINCT session_id)
                    FROM conversations
                    WHERE created_at >= %s
                    """,
                    (since,),
                )
                conversas_ativas = cur.fetchone()[0] or 0
        except Exception as e:
            logger.warning(f"[dashboard] conversas_ativas query error: {e}")

        # ── Proximas consultas do dia ─────────────────────────────────────────
        proximas_consultas = []
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        a.id::text,
                        COALESCE(a.appointment_time::text, a.horario_agendamento::text) AS horario,
                        a.status,
                        d.especialidade,
                        p.nome AS patient_nome,
                        d.nome AS doctor_nome
                    FROM appointments a
                    LEFT JOIN patients p ON a.patient_id = p.id
                    LEFT JOIN doctors d ON a.doctor_id = d.id
                    WHERE COALESCE(a.data_agendamento, a.appointment_date::date) = %s
                      AND a.status NOT IN ('cancelado', 'cancelled')
                    ORDER BY COALESCE(a.appointment_time, a.horario_agendamento) ASC
                    LIMIT 20
                    """,
                    (hoje,),
                )
                rows = cur.fetchall()

            proximas_consultas = [
                {
                    "id": row[0],
                    "horario": row[1],
                    "status": row[2],
                    "especialidade": row[3],
                    "patient_nome": row[4],
                    "doctor_nome": row[5],
                }
                for row in rows
            ]
        except Exception as e:
            logger.warning(f"[dashboard] proximas_consultas query error: {e}")

        logger.info(
            f"[dashboard] stats: consultas_hoje={consultas_hoje} "
            f"conversas_ativas={conversas_ativas}"
        )
        return {
            "consultas_hoje": consultas_hoje,
            "taxa_ocupacao": taxa_ocupacao,
            "no_shows": no_shows,
            "confirmacoes_pendentes": confirmacoes_pendentes,
            "conversas_ativas": conversas_ativas,
            "proximas_consultas": proximas_consultas,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[dashboard] get_dashboard_stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar estatisticas do dashboard",
        )


@router.get("/charts")
def get_dashboard_charts(
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna dados para graficos do dashboard (DASH-04, DASH-06). Admin only.

    Retorna:
    - trend: tendencia de 7 dias (consultas e no-shows por dia)
    - especialidades: distribuicao de consultas por especialidade (ultimos 30 dias)
    """
    try:
        hoje = date.today()

        # ── Tendencia de 7 dias ───────────────────────────────────────────────
        trend = []
        for i in range(6, -1, -1):
            dia = hoje - timedelta(days=i)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*) FILTER (WHERE status NOT IN ('cancelado','cancelled')) AS consultas,
                        COUNT(*) FILTER (WHERE status IN ('cancelado','cancelled'))      AS no_shows
                    FROM appointments
                    WHERE COALESCE(data_agendamento, appointment_date::date) = %s
                    """,
                    (dia,),
                )
                row = cur.fetchone()
            trend.append({
                "date": dia.isoformat(),
                "consultas": row[0] or 0,
                "no_shows": row[1] or 0,
            })

        # ── Especialidades (ultimos 30 dias) ──────────────────────────────────
        inicio_periodo = hoje - timedelta(days=30)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(d.especialidade, 'Nao informada') AS especialidade,
                    COUNT(*) AS count
                FROM appointments a
                LEFT JOIN doctors d ON a.doctor_id = d.id
                WHERE COALESCE(a.data_agendamento, a.appointment_date::date) >= %s
                  AND a.status NOT IN ('cancelado', 'cancelled')
                GROUP BY d.especialidade
                ORDER BY count DESC
                """,
                (inicio_periodo,),
            )
            rows = cur.fetchall()

        especialidades = [
            {"especialidade": row[0], "count": row[1]}
            for row in rows
        ]

        logger.info(f"[dashboard] charts: trend_days=7 especialidades={len(especialidades)}")
        return {
            "trend": trend,
            "especialidades": especialidades,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[dashboard] get_dashboard_charts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar dados dos graficos",
        )
