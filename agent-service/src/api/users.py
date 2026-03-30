"""Endpoints de gestao de usuarios — lista, criacao, role, status e reset de senha."""

import logging
from typing import Optional

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from pwdlib import PasswordHash

from src.api.deps import get_db_for_tenant, require_role

logger = logging.getLogger("agent-clinic.api.users")

router = APIRouter(prefix="/api/users", tags=["users"])

hasher = PasswordHash.recommended()

VALID_ROLES = {"admin", "recepcionista", "medico"}

# ─── Modelos ──────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str  # admin | recepcionista | medico


class UserRoleUpdate(BaseModel):
    role: str  # admin | recepcionista | medico


class UserStatusUpdate(BaseModel):
    is_active: bool


class PasswordReset(BaseModel):
    new_password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _paginate(page: int, per_page: int) -> tuple:
    """Retorna (limit, offset) para paginacao."""
    limit = max(1, min(per_page, 100))
    offset = (max(1, page) - 1) * limit
    return limit, offset


def _validate_role(role: str) -> None:
    """Levanta 400 se role invalido."""
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role invalido. Use: {', '.join(sorted(VALID_ROLES))}",
        )


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/")
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Lista usuarios do tenant com paginacao. USER-01."""
    limit, offset = _paginate(page, per_page)

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            total = cur.fetchone()[0]

            cur.execute(
                """
                SELECT id, email, name, role, is_active, created_at
                FROM users
                ORDER BY name
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cur.fetchall()

        items = [
            {
                "id": str(r[0]),
                "email": r[1],
                "name": r[2],
                "role": r[3],
                "is_active": r[4],
                "created_at": str(r[5]),
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
        logger.error(f"[users] list_users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao listar usuarios",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Cria novo usuario com senha hasheada. USER-02."""
    _validate_role(body.role)
    hashed_password = hasher.hash(body.password)

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, name, hashed_password, role, tenant_id, is_active)
                VALUES (%s, %s, %s, %s, current_setting('app.tenant_id')::uuid, true)
                RETURNING id, email, name, role, is_active, created_at
                """,
                (body.email, body.name, hashed_password, body.role),
            )
            row = cur.fetchone()
        conn.commit()
        logger.info(f"[users] usuario criado: {body.email} ({body.role})")
        return {
            "id": str(row[0]),
            "email": row[1],
            "name": row[2],
            "role": row[3],
            "is_active": row[4],
            "created_at": str(row[5]),
        }
    except psycopg2.IntegrityError:
        logger.warning(f"[users] email duplicado: {body.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ja cadastrado",
        )
    except Exception as e:
        logger.error(f"[users] create_user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar usuario",
        )


@router.patch("/{user_id}/role")
def change_role(
    user_id: str,
    body: UserRoleUpdate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Altera role do usuario. Impede auto-alteracao. USER-03."""
    _validate_role(body.role)

    if user_id == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao e possivel alterar o proprio role",
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users SET role = %s WHERE id = %s
                RETURNING id, email, name, role, is_active, created_at
                """,
                (body.role, user_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario nao encontrado",
            )
        conn.commit()
        logger.info(f"[users] role alterado: {user_id} -> {body.role}")
        return {
            "id": str(row[0]),
            "email": row[1],
            "name": row[2],
            "role": row[3],
            "is_active": row[4],
            "created_at": str(row[5]),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[users] change_role error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao alterar role",
        )


@router.patch("/{user_id}/status")
def change_status(
    user_id: str,
    body: UserStatusUpdate,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Ativa ou desativa usuario. Impede auto-desativacao. USER-04."""
    if user_id == current_user["user_id"] and not body.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao e possivel desativar a propria conta",
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users SET is_active = %s WHERE id = %s
                RETURNING id, email, name, role, is_active, created_at
                """,
                (body.is_active, user_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario nao encontrado",
            )
        conn.commit()
        action = "ativado" if body.is_active else "desativado"
        logger.info(f"[users] usuario {action}: {user_id}")
        return {
            "id": str(row[0]),
            "email": row[1],
            "name": row[2],
            "role": row[3],
            "is_active": row[4],
            "created_at": str(row[5]),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[users] change_status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao alterar status",
        )


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: str,
    body: PasswordReset,
    current_user: dict = Depends(require_role("admin")),
    conn=Depends(get_db_for_tenant),
):
    """Redefine senha do usuario (admin-managed). USER-05.

    Auto-servico via email deferido para v2.
    """
    hashed_password = hasher.hash(body.new_password)

    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET hashed_password = %s WHERE id = %s RETURNING id",
                (hashed_password, user_id),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario nao encontrado",
            )
        conn.commit()
        logger.info(f"[users] senha redefinida para usuario: {user_id}")
        return {"message": "Senha redefinida com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[users] reset_password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao redefinir senha",
        )
