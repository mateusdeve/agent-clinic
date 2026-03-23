-- Tabela de médicos
CREATE TABLE IF NOT EXISTS doctors (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome         TEXT NOT NULL,
    crm          TEXT UNIQUE,
    especialidade TEXT NOT NULL,
    ativo        BOOLEAN DEFAULT true,
    criado_em    TIMESTAMPTZ DEFAULT NOW()
);

-- Agenda dos médicos (dias e horários de atendimento)
CREATE TABLE IF NOT EXISTS doctor_schedules (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doctor_id        UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    dia_semana       SMALLINT NOT NULL CHECK (dia_semana BETWEEN 0 AND 6), -- 0=Dom 1=Seg ... 6=Sab
    hora_inicio      TIME NOT NULL,
    hora_fim         TIME NOT NULL,
    duracao_consulta INT NOT NULL DEFAULT 30  -- minutos por slot
);

-- Adiciona médico na tabela de agendamentos
ALTER TABLE appointments
    ADD COLUMN IF NOT EXISTS doctor_id   UUID REFERENCES doctors(id),
    ADD COLUMN IF NOT EXISTS doctor_name TEXT;

-- ─────────────────────────────────────────
-- Médicos de exemplo (ajuste como precisar)
-- ─────────────────────────────────────────
INSERT INTO doctors (nome, crm, especialidade) VALUES
    ('Dr. Carlos Mendes',   'CRM/SP 12345', 'Clínica Geral'),
    ('Dra. Ana Lima',       'CRM/SP 12346', 'Clínica Geral'),
    ('Dr. Roberto Costa',   'CRM/SP 12347', 'Cardiologia'),
    ('Dra. Patricia Souza', 'CRM/SP 12348', 'Dermatologia'),
    ('Dr. Marcos Oliveira', 'CRM/SP 12349', 'Ortopedia'),
    ('Dra. Fernanda Santos','CRM/SP 12350', 'Ginecologia'),
    ('Dr. Paulo Ferreira',  'CRM/SP 12351', 'Pediatria')
ON CONFLICT (crm) DO NOTHING;

-- ─────────────────────────────────────────
-- Agendas dos médicos
-- dia_semana: 1=Seg 2=Ter 3=Qua 4=Qui 5=Sex 6=Sab
-- ─────────────────────────────────────────

-- Dr. Carlos Mendes — Clínica Geral — Seg a Sex 08:00-12:00
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, d, '08:00', '12:00' FROM doctors, generate_series(1,5) d
WHERE nome = 'Dr. Carlos Mendes' ON CONFLICT DO NOTHING;

-- Dra. Ana Lima — Clínica Geral — Seg a Sex 13:00-18:00 + Sab 08:00-12:00
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, d, '13:00', '18:00' FROM doctors, generate_series(1,5) d
WHERE nome = 'Dra. Ana Lima' ON CONFLICT DO NOTHING;
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, 6, '08:00', '12:00' FROM doctors WHERE nome = 'Dra. Ana Lima' ON CONFLICT DO NOTHING;

-- Dr. Roberto Costa — Cardiologia — Ter, Qui, Sex 08:00-17:00
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, d, '08:00', '17:00' FROM doctors, (VALUES(2),(4),(5)) t(d)
WHERE nome = 'Dr. Roberto Costa' ON CONFLICT DO NOTHING;

-- Dra. Patricia Souza — Dermatologia — Seg, Qua, Sex 09:00-17:00
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, d, '09:00', '17:00' FROM doctors, (VALUES(1),(3),(5)) t(d)
WHERE nome = 'Dra. Patricia Souza' ON CONFLICT DO NOTHING;

-- Dr. Marcos Oliveira — Ortopedia — Seg a Sex 07:00-13:00
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, d, '07:00', '13:00' FROM doctors, generate_series(1,5) d
WHERE nome = 'Dr. Marcos Oliveira' ON CONFLICT DO NOTHING;

-- Dra. Fernanda Santos — Ginecologia — Seg a Sex 08:00-17:00
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, d, '08:00', '17:00' FROM doctors, generate_series(1,5) d
WHERE nome = 'Dra. Fernanda Santos' ON CONFLICT DO NOTHING;

-- Dr. Paulo Ferreira — Pediatria — Seg a Sab 08:00-16:00
INSERT INTO doctor_schedules (doctor_id, dia_semana, hora_inicio, hora_fim)
SELECT id, d, '08:00', '16:00' FROM doctors, generate_series(1,6) d
WHERE nome = 'Dr. Paulo Ferreira' ON CONFLICT DO NOTHING;

-- Índice para busca rápida por especialidade
CREATE INDEX IF NOT EXISTS idx_doctors_especialidade ON doctors(especialidade) WHERE ativo = true;
CREATE INDEX IF NOT EXISTS idx_doctor_schedules_dia ON doctor_schedules(doctor_id, dia_semana);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id, appointment_date) WHERE status = 'active';
