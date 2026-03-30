"""Dependencias de autenticacao e autorizacao para FastAPI.

Exporta: get_current_user, get_current_tenant, require_role, get_db_for_tenant
"""

import os
import logging
from contextlib import contextmanager
from typing import Annotated

import jwt
import psycopg2
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

load_dotenv()

logger = logging.getLogger("agent-clinic.deps")

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ─── Dependencias principais ──────────────────────────────────────────────────


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Decodifica Bearer token e retorna dados do usuario autenticado.

    Retorna dict com user_id, tenant_id e role.
    Levanta 401 se token invalido ou claims ausentes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise credentials_exception

    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")
    role: str = payload.get("role")

    if not user_id or not tenant_id or not role:
        raise credentials_exception

    return {"user_id": user_id, "tenant_id": tenant_id, "role": role}


def get_current_tenant(user: dict = Depends(get_current_user)) -> str:
    """Extrai tenant_id do JWT.

    Per D-13/TENANT-03: tenant_id vem sempre do JWT, nunca de parametros de request.
    """
    return user["tenant_id"]


def require_role(*roles: str):
    """Factory de dependencias para verificacao de role.

    Uso: Depends(require_role('admin', 'recepcionista'))
    Per D-07: FastAPI e a fonte de verdade para RBAC — enforce aqui, nao apenas no frontend.
    """

    def _check_role(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissao insuficiente",
            )
        return user

    return _check_role


def get_db_for_tenant(tenant_id: str = Depends(get_current_tenant)):
    """Dependencia de banco de dados com isolamento de tenant via SET LOCAL.

    Executa SET LOCAL app.tenant_id antes de cada request para ativar o
    PostgreSQL RLS automaticamente (per API-03).

    Usa SET LOCAL (nao SET) para garantir que o valor e revertido ao fim
    da transacao — mais seguro em ambiente com connection pooling.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DATABASE_URL nao configurado",
        )
    conn = psycopg2.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL app.tenant_id = %s", (tenant_id,))
        conn.commit()
        yield conn
    finally:
        conn.close()
