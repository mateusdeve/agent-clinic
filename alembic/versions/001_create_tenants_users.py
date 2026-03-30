"""Cria tabelas tenants e users para multi-tenancy e autenticacao.

Revision ID: 001
Revises: None
Create Date: 2026-03-30
"""

from alembic import op

# Identificadores da revision
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria tabela tenants com tenant padrao e tabela users com controle de acesso."""
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
    """)

    op.execute("""
        CREATE TABLE tenants (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    # Insere tenant padrao para backfill dos dados existentes (D-11)
    op.execute("""
        INSERT INTO tenants (id, name, slug)
        VALUES ('00000000-0000-0000-0000-000000000001', 'Clinica Padrao', 'clinica-padrao')
    """)

    op.execute("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'recepcionista', 'medico')),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    op.execute("CREATE INDEX idx_users_email ON users(email)")
    op.execute("CREATE INDEX idx_users_tenant_id ON users(tenant_id)")


def downgrade() -> None:
    """Remove tabelas users e tenants."""
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS tenants")
