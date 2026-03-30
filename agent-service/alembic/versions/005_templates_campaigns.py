"""Adiciona tabelas para templates de mensagens, campanhas e destinatarios.

Revision ID: 005
Revises: 004
Create Date: 2026-03-30

Contexto: Suporta o modulo de campanhas de mensagens em massa do painel web.
Todas as DDL usam op.execute() com SQL puro (decisao: sem modelos ORM).
RLS ativado em todas as 3 tabelas para isolamento de tenant automatico.
"""

from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria tabelas message_templates, campaigns e campaign_recipients com RLS."""

    # ─── message_templates ───────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS message_templates (
            id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id         UUID        NOT NULL REFERENCES tenants(id),
            nome              TEXT        NOT NULL,
            corpo             TEXT        NOT NULL,
            variaveis_usadas  TEXT[]      NOT NULL DEFAULT '{}',
            created_at        TIMESTAMPTZ DEFAULT NOW(),
            updated_at        TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'message_templates'
                  AND policyname = 'tenant_isolation_message_templates'
            ) THEN
                CREATE POLICY tenant_isolation_message_templates ON message_templates
                    USING (tenant_id = current_tenant_id())
                    WITH CHECK (tenant_id = current_tenant_id());
            END IF;
        END $$
    """)

    # ─── campaigns ───────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id         UUID        NOT NULL REFERENCES tenants(id),
            nome              TEXT        NOT NULL,
            template_id       UUID        NOT NULL REFERENCES message_templates(id),
            filtros           JSONB       NOT NULL DEFAULT '{}',
            status            TEXT        NOT NULL DEFAULT 'rascunho'
                                          CHECK (status IN ('rascunho','enviando','concluida','falha')),
            total_recipients  INT         DEFAULT 0,
            created_by        UUID        REFERENCES users(id),
            created_at        TIMESTAMPTZ DEFAULT NOW(),
            enviado_at        TIMESTAMPTZ
        )
    """)

    op.execute("ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'campaigns'
                  AND policyname = 'tenant_isolation_campaigns'
            ) THEN
                CREATE POLICY tenant_isolation_campaigns ON campaigns
                    USING (tenant_id = current_tenant_id())
                    WITH CHECK (tenant_id = current_tenant_id());
            END IF;
        END $$
    """)

    # ─── campaign_recipients ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_recipients (
            id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            campaign_id   UUID        NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
            patient_id    UUID        NOT NULL,
            phone         TEXT        NOT NULL,
            variaveis     JSONB       NOT NULL DEFAULT '{}',
            status        TEXT        NOT NULL DEFAULT 'pendente'
                                      CHECK (status IN ('pendente','processando','enviado','entregue','lido','falha')),
            erro          TEXT,
            sent_at       TIMESTAMPTZ,
            updated_at    TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("ALTER TABLE campaign_recipients ENABLE ROW LEVEL SECURITY")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'campaign_recipients'
                  AND policyname = 'tenant_isolation_campaign_recipients'
            ) THEN
                CREATE POLICY tenant_isolation_campaign_recipients ON campaign_recipients
                    USING (campaign_id IN (
                        SELECT id FROM campaigns WHERE tenant_id = current_tenant_id()
                    ));
            END IF;
        END $$
    """)


def downgrade() -> None:
    """Remove tabelas de campanhas e templates na ordem correta (FK)."""

    op.execute("DROP TABLE IF EXISTS campaign_recipients")
    op.execute("DROP TABLE IF EXISTS campaigns")
    op.execute("DROP TABLE IF EXISTS message_templates")
