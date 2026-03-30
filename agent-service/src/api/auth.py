"""Endpoints de autenticacao — login, refresh, me, seed."""

import os
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import psycopg2
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from pwdlib import PasswordHash

load_dotenv()

logger = logging.getLogger("agent-clinic.auth")

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

password_hash = PasswordHash.recommended()
router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ─── DB helper ────────────────────────────────────────────────────────────────


@contextmanager
def _get_db():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL nao configurado")
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


# ─── Modelos ──────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: str
    email: str
    name: str
    role: str
    tenant_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    tenant_id: str


# ─── Helpers ──────────────────────────────────────────────────────────────────


def create_token(data: dict, expires_delta: timedelta) -> str:
    """Cria JWT com tempo de expiracao."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def hash_password(password: str) -> str:
    """Gera hash Argon2 da senha."""
    return password_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica senha contra hash Argon2."""
    return password_hash.verify(plain, hashed)


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """Autentica usuario com email e senha. Retorna access_token e refresh_token."""
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, name, hashed_password, role, tenant_id, is_active "
                    "FROM users WHERE email = %s",
                    (request.email,),
                )
                row = cur.fetchone()
    except Exception as e:
        logger.error(f"[auth] login db error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )

    if not row or not row[6]:  # nao encontrado ou inativo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id, email, name, hashed_password, role, tenant_id, is_active = row

    if not verify_password(request.password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_token(
        data={"sub": str(user_id), "tenant_id": str(tenant_id), "role": role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_token(
        data={"sub": str(user_id), "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    logger.info(f"[auth] login ok: {email}")
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user_id=str(user_id),
        email=email,
        name=name,
        role=role,
        tenant_id=str(tenant_id),
    )


@router.post("/refresh")
def refresh(request: RefreshRequest):
    """Aceita refresh_token e retorna novo access_token."""
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido: tipo incorreto",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido: sub ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, tenant_id, is_active FROM users WHERE id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
    except Exception as e:
        logger.error(f"[auth] refresh db error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )

    if not row or not row[2]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado ou inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role, tenant_id, _ = row
    access_token = create_token(
        data={"sub": user_id, "tenant_id": str(tenant_id), "role": role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(token: str = Depends(oauth2_scheme)):
    """Retorna dados do usuario autenticado."""
    # importar get_current_user aqui para evitar importacao circular
    from src.api.deps import get_current_user

    user = get_current_user(token)
    user_id = user["user_id"]

    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, email, name, role, tenant_id FROM users WHERE id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
    except Exception as e:
        logger.error(f"[auth] me db error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor",
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado",
        )

    return UserResponse(
        id=str(row[0]),
        email=row[1],
        name=row[2],
        role=row[3],
        tenant_id=str(row[4]),
    )


@router.post("/seed")
def seed(email: str, password: str, name: str):
    """Cria usuario admin de seed para testes. Disponivel apenas fora de producao."""
    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endpoint desativado em producao",
        )

    DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
    hashed = hash_password(password)

    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (email, name, hashed_password, role, tenant_id)
                    VALUES (%s, %s, %s, 'admin', %s)
                    ON CONFLICT (email) DO UPDATE SET
                        name = EXCLUDED.name,
                        hashed_password = EXCLUDED.hashed_password
                    RETURNING id, email, name, role, tenant_id
                    """,
                    (email, name, hashed, DEFAULT_TENANT_ID),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception as e:
        logger.error(f"[auth] seed error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar usuario seed: {e}",
        )

    logger.info(f"[auth] seed user criado: {email}")
    return {
        "id": str(row[0]),
        "email": row[1],
        "name": row[2],
        "role": row[3],
        "tenant_id": str(row[4]),
    }
