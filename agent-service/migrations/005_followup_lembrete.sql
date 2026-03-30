-- Adiciona tipo e datetime real da consulta na tabela follow_ups
ALTER TABLE follow_ups
    ADD COLUMN IF NOT EXISTS tipo TEXT NOT NULL DEFAULT 'followup',
    ADD COLUMN IF NOT EXISTS appointment_datetime TIMESTAMPTZ;

-- Índice para lembretes pendentes
CREATE INDEX IF NOT EXISTS idx_follow_ups_tipo
    ON follow_ups (tipo, enviar_em) WHERE enviado = false;
