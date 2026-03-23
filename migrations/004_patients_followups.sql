-- Tabela de pacientes (reconhecimento por número)
CREATE TABLE IF NOT EXISTS patients (
    phone       TEXT PRIMARY KEY,
    nome        TEXT NOT NULL,
    criado_em   TIMESTAMPTZ DEFAULT NOW(),
    ultima_visita TIMESTAMPTZ DEFAULT NOW(),
    total_consultas INT DEFAULT 0
);

-- Tabela de follow-ups pós-consulta
CREATE TABLE IF NOT EXISTS follow_ups (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone        TEXT NOT NULL,
    nome         TEXT,
    especialidade TEXT,
    data_consulta TEXT,
    protocolo    TEXT,
    enviar_em    TIMESTAMPTZ NOT NULL,
    enviado      BOOLEAN DEFAULT false,
    enviado_em   TIMESTAMPTZ,
    criado_em    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_follow_ups_pendentes
    ON follow_ups (enviar_em) WHERE enviado = false;
