"""Habilita Row-Level Security em todas as tabelas de dados para isolamento por tenant.

Revision ID: 003
Revises: 002
Create Date: 2026-03-30

Estrategia (D-10): PostgreSQL RLS — cria funcao current_tenant_id() que le a
variavel de sessao app.tenant_id, habilita RLS em todas as tabelas e cria
politicas tenant_isolation_{table}. O usuario do bot recebe BYPASSRLS para
manter compatibilidade com o pipeline WhatsApp existente (D-11).
"""

from alembic import op

# Identificadores da revision
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

# Tabelas com RLS: as 7 tabelas de dados + users
_DATA_TABLES = [
    "patients",
    "appointments",
    "doctors",
    "conversations",
    "conversation_summaries",
    "knowledge_chunks",
    "follow_ups",
]

_ALL_TABLES = _DATA_TABLES + ["users"]


def upgrade() -> None:
    """Cria funcao current_tenant_id(), habilita RLS e cria politicas de isolamento."""

    # Funcao helper que le o tenant atual da variavel de sessao PostgreSQL
    # STABLE SECURITY DEFINER: executada com privilegios do dono da funcao
    op.execute("""
        CREATE OR REPLACE FUNCTION current_tenant_id()
        RETURNS UUID AS $$
        BEGIN
            RETURN NULLIF(current_setting('app.tenant_id', TRUE), '')::UUID;
        END;
        $$ LANGUAGE plpgsql STABLE SECURITY DEFINER
    """)

    # Habilita RLS e cria politica de isolamento por tenant em cada tabela
    for table in _ALL_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
                USING (tenant_id = current_tenant_id())
                WITH CHECK (tenant_id = current_tenant_id())
        """)

    # Concede BYPASSRLS ao usuario atual do banco de dados para que o bot
    # WhatsApp (Sofia/Carla pipeline) continue funcionando sem context de tenant.
    # Em producao com usuarios separados: apenas o usuario do bot deve ter BYPASSRLS;
    # o usuario da API web NAO deve ter (D-11).
    op.execute("""
        DO $$
        BEGIN
            EXECUTE format('ALTER USER %I WITH BYPASSRLS', current_user);
        END $$
    """)


def downgrade() -> None:
    """Remove politicas RLS, desabilita RLS e remove funcao current_tenant_id."""
    for table in reversed(_ALL_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute("DROP FUNCTION IF EXISTS current_tenant_id()")
