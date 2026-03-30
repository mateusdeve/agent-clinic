"""Adiciona colunas para CRUD de entidades: patients, doctors, doctor_schedules, blocked_slots, appointments.

Revision ID: 004
Revises: 003
Create Date: 2026-03-30

Contexto (D-14): Nao modifica funcoes de ferramentas existentes do bot.
Apenas adiciona colunas/tabelas novas para o painel web CRUD.
Todas as DDL usam op.execute() com SQL puro (decisao: sem modelos ORM).
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Adiciona colunas e tabelas necessarias para o CRUD do painel web."""

    # ─── patients: adiciona id UUID, data_nascimento, notas ─────────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'patients' AND column_name = 'id'
            ) THEN
                ALTER TABLE patients ADD COLUMN id UUID DEFAULT gen_random_uuid();
                UPDATE patients SET id = gen_random_uuid() WHERE id IS NULL;
                ALTER TABLE patients ALTER COLUMN id SET NOT NULL;
            END IF;
        END $$
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_id ON patients(id)
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'patients' AND column_name = 'data_nascimento'
            ) THEN
                ALTER TABLE patients ADD COLUMN data_nascimento DATE;
            END IF;
        END $$
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'patients' AND column_name = 'notas'
            ) THEN
                ALTER TABLE patients ADD COLUMN notas TEXT;
            END IF;
        END $$
    """)

    # ─── doctors: adiciona user_id UUID para isolamento de medico (AGENDA-07) ─
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'doctors' AND column_name = 'user_id'
            ) THEN
                ALTER TABLE doctors ADD COLUMN user_id UUID REFERENCES users(id);
            END IF;
        END $$
    """)

    # ─── doctor_schedules: adiciona tenant_id + RLS ──────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'doctor_schedules' AND column_name = 'tenant_id'
            ) THEN
                ALTER TABLE doctor_schedules ADD COLUMN tenant_id UUID;
                UPDATE doctor_schedules ds
                SET tenant_id = d.tenant_id
                FROM doctors d
                WHERE ds.doctor_id = d.id;
                ALTER TABLE doctor_schedules ALTER COLUMN tenant_id SET NOT NULL;
                ALTER TABLE doctor_schedules
                    ADD CONSTRAINT fk_doctor_schedules_tenant
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id);
            END IF;
        END $$
    """)

    op.execute("ALTER TABLE doctor_schedules ENABLE ROW LEVEL SECURITY")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'doctor_schedules'
                  AND policyname = 'tenant_isolation_doctor_schedules'
            ) THEN
                CREATE POLICY tenant_isolation_doctor_schedules ON doctor_schedules
                    USING (tenant_id = current_tenant_id())
                    WITH CHECK (tenant_id = current_tenant_id());
            END IF;
        END $$
    """)

    # ─── blocked_slots: nova tabela para bloqueio de horarios ───────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS blocked_slots (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            doctor_id   UUID        NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            tenant_id   UUID        NOT NULL REFERENCES tenants(id),
            blocked_date DATE       NOT NULL,
            start_time  TIME,
            end_time    TIME,
            reason      TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    op.execute("ALTER TABLE blocked_slots ENABLE ROW LEVEL SECURITY")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'blocked_slots'
                  AND policyname = 'tenant_isolation_blocked_slots'
            ) THEN
                CREATE POLICY tenant_isolation_blocked_slots ON blocked_slots
                    USING (tenant_id = current_tenant_id())
                    WITH CHECK (tenant_id = current_tenant_id());
            END IF;
        END $$
    """)

    # ─── appointments: garante compatibilidade com novos status do painel ────
    # O bot usa 'active'/'cancelled'; o painel usa 'agendado'/'confirmado'/'realizado'/'cancelado'.
    # Se houver CHECK constraint no status, remove e recria para aceitar ambos os conjuntos.
    op.execute("""
        DO $$
        DECLARE
            v_constraint TEXT;
        BEGIN
            SELECT constraint_name INTO v_constraint
            FROM information_schema.table_constraints
            WHERE table_name = 'appointments'
              AND constraint_type = 'CHECK'
              AND constraint_name LIKE '%status%';

            IF v_constraint IS NOT NULL THEN
                EXECUTE format('ALTER TABLE appointments DROP CONSTRAINT %I', v_constraint);
                ALTER TABLE appointments
                    ADD CONSTRAINT appointments_status_check
                    CHECK (status IN (
                        'active', 'cancelled',
                        'agendado', 'confirmado', 'realizado', 'cancelado'
                    ));
            END IF;
        END $$
    """)

    # ─── appointments: adiciona colunas CRUD do painel web ───────────────────
    # data_agendamento, horario_agendamento: aliases para o painel (bot usa appointment_date/time)
    # patient_id: FK para patients.id UUID (bot usava phone + patient_name)
    # motivo_cancelamento: texto de motivo do cancelamento
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'appointments' AND column_name = 'data_agendamento'
            ) THEN
                ALTER TABLE appointments ADD COLUMN data_agendamento DATE;
            END IF;
        END $$
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'appointments' AND column_name = 'horario_agendamento'
            ) THEN
                ALTER TABLE appointments ADD COLUMN horario_agendamento TIME;
            END IF;
        END $$
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'appointments' AND column_name = 'patient_id'
            ) THEN
                ALTER TABLE appointments ADD COLUMN patient_id UUID REFERENCES patients(id);
            END IF;
        END $$
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'appointments' AND column_name = 'motivo_cancelamento'
            ) THEN
                ALTER TABLE appointments ADD COLUMN motivo_cancelamento TEXT;
            END IF;
        END $$
    """)


def downgrade() -> None:
    """Reverte as alteracoes de schema da migration 004."""

    # Remove colunas CRUD adicionadas a appointments
    for col in ("motivo_cancelamento", "patient_id", "horario_agendamento", "data_agendamento"):
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'appointments' AND column_name = '{col}'
                ) THEN
                    ALTER TABLE appointments DROP COLUMN {col};
                END IF;
            END $$
        """)

    # Remove constraint de status ampliada
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'appointments'
                  AND constraint_name = 'appointments_status_check'
            ) THEN
                ALTER TABLE appointments DROP CONSTRAINT appointments_status_check;
            END IF;
        END $$
    """)

    # Remove blocked_slots
    op.execute("DROP TABLE IF EXISTS blocked_slots")

    # Remove RLS e politica de doctor_schedules
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_doctor_schedules ON doctor_schedules
    """)
    op.execute("ALTER TABLE doctor_schedules DISABLE ROW LEVEL SECURITY")

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'doctor_schedules' AND column_name = 'tenant_id'
            ) THEN
                ALTER TABLE doctor_schedules
                    DROP CONSTRAINT IF EXISTS fk_doctor_schedules_tenant;
                ALTER TABLE doctor_schedules DROP COLUMN tenant_id;
            END IF;
        END $$
    """)

    # Remove user_id de doctors
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'doctors' AND column_name = 'user_id'
            ) THEN
                ALTER TABLE doctors DROP COLUMN user_id;
            END IF;
        END $$
    """)

    # Remove colunas adicionadas a patients
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'patients' AND column_name = 'notas'
            ) THEN
                ALTER TABLE patients DROP COLUMN notas;
            END IF;
        END $$
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'patients' AND column_name = 'data_nascimento'
            ) THEN
                ALTER TABLE patients DROP COLUMN data_nascimento;
            END IF;
        END $$
    """)

    op.execute("DROP INDEX IF EXISTS idx_patients_id")

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'patients' AND column_name = 'id'
            ) THEN
                ALTER TABLE patients DROP COLUMN id;
            END IF;
        END $$
    """)
