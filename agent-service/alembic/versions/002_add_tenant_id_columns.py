"""Adiciona coluna tenant_id em todas as tabelas de dados existentes com backfill.

Revision ID: 002
Revises: 001
Create Date: 2026-03-30

Estrategia (D-11): ADD COLUMN nullable, UPDATE backfill para tenant padrao,
SET NOT NULL, ADD FK constraint e INDEX — zero data loss, bot continua funcionando.
"""

from alembic import op

# Identificadores da revision
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

# Tabelas de dados que precisam de tenant_id
# (nao inclui tenants e users — criadas na 001 com tenant_id nativo)
_TABLES = [
    "patients",
    "appointments",
    "doctors",
    "conversations",
    "conversation_summaries",
    "knowledge_chunks",
    "follow_ups",
]

_DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    """Adiciona tenant_id UUID em todas as tabelas de dados com backfill para o tenant padrao."""
    for table in _TABLES:
        # 1. Adiciona coluna nullable para permitir backfill
        op.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN IF NOT EXISTS tenant_id UUID
        """)

        # 2. Backfill: todos os registros existentes pertencem ao tenant padrao
        op.execute(f"""
            UPDATE {table}
            SET tenant_id = '{_DEFAULT_TENANT_ID}'
            WHERE tenant_id IS NULL
        """)

        # 3. Torna NOT NULL apos backfill
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN tenant_id SET NOT NULL
        """)

        # 4. Adiciona FK constraint para integridade referencial
        op.execute(f"""
            ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_tenant
            FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        """)

        # 5. Cria indice para performance de consultas por tenant
        op.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_tenant_id
            ON {table}(tenant_id)
        """)


def downgrade() -> None:
    """Remove tenant_id das tabelas de dados (FK, index, e coluna)."""
    for table in reversed(_TABLES):
        op.execute(f"DROP INDEX IF EXISTS idx_{table}_tenant_id")
        op.execute(f"""
            ALTER TABLE {table}
            DROP CONSTRAINT IF EXISTS fk_{table}_tenant
        """)
        op.execute(f"""
            ALTER TABLE {table}
            DROP COLUMN IF EXISTS tenant_id
        """)
