CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(50) NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    appointment_date VARCHAR(50) NOT NULL,
    appointment_time VARCHAR(10) NOT NULL,
    insurance VARCHAR(100) NOT NULL,
    protocol VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_appointments_phone ON appointments(phone);
CREATE INDEX IF NOT EXISTS idx_appointments_protocol ON appointments(protocol);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
