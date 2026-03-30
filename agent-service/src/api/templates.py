"""Endpoints REST para CRUD de templates de mensagem.

Templates suportam variaveis no formato {{nome_variavel}}.
Variaveis permitidas: nome, telefone, data, hora, medico, especialidade.

Requer autenticacao via JWT. Admin para escrita, admin+recepcionista para leitura.
"""

import re
import logging
from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.deps import get_db_for_tenant, require_role

logger = logging.getLogger("agent-clinic.api.templates")

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Variaveis permitidas para substituicao em templates
ALLOWED_VARS = {"nome", "telefone", "data", "hora", "medico", "especialidade"}


# ─── Modelos ──────────────────────────────────────────────────────────────────


class TemplateCreate(BaseModel):
    nome: str
    corpo: str


class TemplateUpdate(BaseModel):
    nome: Optional[str] = None
    corpo: Optional[str] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────


def extract_variables(corpo: str) -> list:
    """Extrai variaveis usadas no corpo do template.

    Aceita apenas variaveis da lista ALLOWED_VARS.
    Retorna lista de strings sem duplicatas na ordem de ocorrencia.
    """
    found = re.findall(r"\{\{(\w+)\}\}", corpo)
    seen = set()
    result = []
    for v in found:
        if v in ALLOWED_VARS and v not in seen:
            seen.add(v)
            result.append(v)
    return result


def render_template(corpo: str, variaveis: dict) -> str:
    """Substitui variaveis no corpo do template pelos valores fornecidos.

    Variaveis nao presentes em variaveis ou fora de ALLOWED_VARS sao mantidas literais.
    """
    def replacer(match):
        key = match.group(1)
        if key in ALLOWED_VARS and key in variaveis:
            return str(variaveis[key])
        return match.group(0)

    return re.sub(r"\{\{(\w+)\}\}", replacer, corpo)


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_template(
    body: TemplateCreate,
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Cria novo template de mensagem para o tenant atual.

    Extrai variaveis automaticamente do corpo (WPP-12).
    """
    try:
        variaveis_usadas = extract_variables(body.corpo)

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO message_templates (tenant_id, nome, corpo, variaveis_usadas)
                VALUES (
                    current_setting('app.tenant_id')::uuid,
                    %s, %s, %s
                )
                RETURNING id, nome, corpo, variaveis_usadas, created_at, updated_at
                """,
                (body.nome, body.corpo, variaveis_usadas),
            )
            row = cur.fetchone()
        conn.commit()

        logger.info(f"[templates] create_template: nome={body.nome} vars={variaveis_usadas}")
        return {
            "id": str(row[0]),
            "nome": row[1],
            "corpo": row[2],
            "variaveis_usadas": row[3],
            "created_at": str(row[4]),
            "updated_at": str(row[5]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[templates] create_template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar template",
        )


@router.get("/")
def list_templates(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Lista templates paginados do tenant atual.

    Retorna {items, total, page, per_page}.
    """
    try:
        offset = (page - 1) * per_page

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM message_templates")
            total = cur.fetchone()[0]

            cur.execute(
                """
                SELECT id, nome, corpo, variaveis_usadas, created_at, updated_at
                FROM message_templates
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (per_page, offset),
            )
            rows = cur.fetchall()

        items = [
            {
                "id": str(row[0]),
                "nome": row[1],
                "corpo": row[2],
                "variaveis_usadas": row[3],
                "created_at": str(row[4]),
                "updated_at": str(row[5]),
            }
            for row in rows
        ]

        logger.info(f"[templates] list_templates: total={total} page={page}")
        return {"items": items, "total": total, "page": page, "per_page": per_page}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[templates] list_templates error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar templates",
        )


@router.get("/{template_id}")
def get_template(
    template_id: str,
    _user: dict = Depends(require_role("admin", "recepcionista")),
    conn=Depends(get_db_for_tenant),
):
    """Retorna um template pelo ID ou 404 se nao encontrado."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, nome, corpo, variaveis_usadas, created_at, updated_at
                FROM message_templates
                WHERE id = %s
                """,
                (template_id,),
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template nao encontrado",
            )

        logger.info(f"[templates] get_template: id={template_id}")
        return {
            "id": str(row[0]),
            "nome": row[1],
            "corpo": row[2],
            "variaveis_usadas": row[3],
            "created_at": str(row[4]),
            "updated_at": str(row[5]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[templates] get_template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao buscar template",
        )


@router.put("/{template_id}")
def update_template(
    template_id: str,
    body: TemplateUpdate,
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Atualiza nome e/ou corpo de um template. Re-extrai variaveis_usadas.

    Apenas campos nao-nulos sao alterados.
    """
    try:
        updates = {}
        if body.nome is not None:
            updates["nome"] = body.nome
        if body.corpo is not None:
            updates["corpo"] = body.corpo

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum campo para atualizar",
            )

        # Buscar corpo atual se nao foi fornecido novo (para re-extrair variaveis)
        if "corpo" not in updates:
            with conn.cursor() as cur:
                cur.execute("SELECT corpo FROM message_templates WHERE id = %s", (template_id,))
                existing = cur.fetchone()
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template nao encontrado",
                )
            corpo_atual = existing[0]
        else:
            corpo_atual = updates["corpo"]

        updates["variaveis_usadas"] = extract_variables(corpo_atual)
        updates["updated_at"] = "NOW()"

        # Montar SET clause (updated_at usa expressao SQL)
        set_parts = []
        values = []
        for col, val in updates.items():
            if col == "updated_at":
                set_parts.append(f"{col} = NOW()")
            else:
                set_parts.append(f"{col} = %s")
                values.append(val)
        values.append(template_id)

        set_clause = ", ".join(set_parts)

        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE message_templates
                SET {set_clause}
                WHERE id = %s
                RETURNING id, nome, corpo, variaveis_usadas, created_at, updated_at
                """,
                values,
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template nao encontrado",
            )

        conn.commit()

        logger.info(f"[templates] update_template: id={template_id} fields={list(updates.keys())}")
        return {
            "id": str(row[0]),
            "nome": row[1],
            "corpo": row[2],
            "variaveis_usadas": row[3],
            "created_at": str(row[4]),
            "updated_at": str(row[5]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[templates] update_template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar template",
        )


@router.delete("/{template_id}")
def delete_template(
    template_id: str,
    _user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Remove um template pelo ID. Retorna 404 se nao encontrado."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM message_templates WHERE id = %s RETURNING id",
                (template_id,),
            )
            row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template nao encontrado",
            )

        conn.commit()

        logger.info(f"[templates] delete_template: id={template_id}")
        return {"status": "deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[templates] delete_template error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao deletar template",
        )
