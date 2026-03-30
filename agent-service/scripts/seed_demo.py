"""Seed de dados de demonstracao para o MedIA.

Popula o banco com pacientes, consultas (passadas e futuras),
conversas e follow-ups para que o dashboard e as telas tenham dados.

Uso: python3 scripts/seed_demo.py
"""

import os
import random
import uuid
from datetime import date, datetime, timedelta, time

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"

PACIENTES = [
    ("5511999001001", "Maria Silva"),
    ("5511999001002", "Joao Santos"),
    ("5511999001003", "Ana Oliveira"),
    ("5511999001004", "Carlos Souza"),
    ("5511999001005", "Patricia Lima"),
    ("5511999001006", "Roberto Ferreira"),
    ("5511999001007", "Fernanda Costa"),
    ("5511999001008", "Marcos Pereira"),
    ("5511999001009", "Julia Almeida"),
    ("5511999001010", "Ricardo Nascimento"),
    ("5511999001011", "Camila Rodrigues"),
    ("5511999001012", "Bruno Martins"),
    ("5511999001013", "Larissa Araujo"),
    ("5511999001014", "Daniel Carvalho"),
    ("5511999001015", "Beatriz Gomes"),
]

HORARIOS = ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]

CONVENIOS = ["Unimed", "Bradesco Saude", "Amil", "SulAmerica", "Particular"]

STATUSES = ["agendado", "confirmado", "atendido", "cancelado"]
PAST_STATUSES = ["atendido", "atendido", "atendido", "cancelado"]  # mostly atendido

MOTIVOS = [
    "Consulta de rotina", "Dor de cabeca frequente", "Check-up anual",
    "Dor nas costas", "Acompanhamento pos-cirurgia", "Exame de sangue",
    "Pressao alta", "Dor no joelho", "Consulta dermatologica", "Prenatal",
]


def main():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.autocommit = True
    cur = conn.cursor()

    # Get doctors
    cur.execute("SELECT id, nome, especialidade FROM doctors WHERE ativo = true")
    doctors = cur.fetchall()
    if not doctors:
        print("ERRO: Nenhum medico encontrado. Rode as migrations primeiro.")
        return

    print(f"Encontrados {len(doctors)} medicos")

    # Insert patients
    patient_ids = []
    for phone, nome in PACIENTES:
        pid = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO patients (id, phone, nome, tenant_id, total_consultas, criado_em, ultima_visita)
            VALUES (%s, %s, %s, %s, %s, NOW() - interval '90 days' * random(), NOW())
            ON CONFLICT (phone) DO UPDATE SET nome = EXCLUDED.nome
            RETURNING id
            """,
            (pid, phone, nome, DEFAULT_TENANT_ID, random.randint(1, 8)),
        )
        patient_ids.append((cur.fetchone()[0], phone, nome))

    print(f"Inseridos {len(patient_ids)} pacientes")

    # Insert appointments — past 7 days + today + next 7 days
    hoje = date.today()
    appt_count = 0

    for day_offset in range(-7, 8):
        dia = hoje + timedelta(days=day_offset)
        # Skip sundays
        if dia.weekday() == 6:
            continue

        # 3-8 consultas por dia
        n_consultas = random.randint(3, 8)
        horarios_dia = random.sample(HORARIOS, min(n_consultas, len(HORARIOS)))

        for horario in horarios_dia:
            pid, phone, nome = random.choice(patient_ids)
            doctor = random.choice(doctors)
            doctor_id, doctor_nome, especialidade = doctor
            convenio = random.choice(CONVENIOS)
            protocolo = f"P{dia.strftime('%Y%m%d')}{random.randint(1000, 9999)}"

            if day_offset < 0:
                status = random.choice(PAST_STATUSES)
            elif day_offset == 0:
                status = random.choice(["agendado", "confirmado", "atendido"])
            else:
                status = random.choice(["agendado", "confirmado"])

            motivo_cancel = "Paciente nao compareceu" if status == "cancelado" else None

            cur.execute(
                """
                INSERT INTO appointments (
                    phone, patient_name, specialty, appointment_date, appointment_time,
                    insurance, protocol, status, doctor_id, doctor_name,
                    tenant_id, data_agendamento, horario_agendamento, patient_id,
                    motivo_cancelamento
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (protocol) DO NOTHING
                """,
                (
                    phone, nome, especialidade, str(dia), horario,
                    convenio, protocolo, status, doctor_id, doctor_nome,
                    DEFAULT_TENANT_ID, str(dia), horario, pid,
                    motivo_cancel,
                ),
            )
            appt_count += 1

    print(f"Inseridas {appt_count} consultas")

    # Insert conversations (simulated)
    conv_count = 0
    for pid, phone, nome in patient_ids[:8]:
        session_id = f"session:{phone}"
        msgs = [
            ("user", f"Ola, meu nome e {nome}"),
            ("assistant", f"Ola {nome}! Bem-vinda a Clinica. Como posso ajudar?"),
            ("user", "Gostaria de agendar uma consulta"),
            ("assistant", "Claro! Qual especialidade voce precisa?"),
            ("user", random.choice(["Clinica Geral", "Cardiologia", "Dermatologia"])),
            ("assistant", "Temos horarios disponiveis. Qual dia seria melhor para voce?"),
        ]
        base_time = datetime.now() - timedelta(hours=random.randint(1, 48))
        for i, (role, content) in enumerate(msgs):
            cur.execute(
                """
                INSERT INTO conversations (session_id, role, content, patient_id, tenant_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (session_id, role, content, phone, DEFAULT_TENANT_ID,
                 base_time + timedelta(minutes=i * 2)),
            )
            conv_count += 1

    print(f"Inseridas {conv_count} mensagens de conversa")

    # Insert follow-ups
    fu_count = 0
    for pid, phone, nome in patient_ids[:5]:
        cur.execute(
            """
            INSERT INTO follow_ups (phone, nome, especialidade, protocolo, enviar_em, tenant_id, tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (phone, nome, "Clinica Geral", f"FU{random.randint(10000,99999)}",
             datetime.now() + timedelta(days=random.randint(1, 7)),
             DEFAULT_TENANT_ID, "followup"),
        )
        fu_count += 1

    print(f"Inseridos {fu_count} follow-ups")

    # Seed admin user if not exists
    try:
        from src.api.auth import hash_password
        cur.execute(
            """
            INSERT INTO users (email, name, hashed_password, role, tenant_id)
            VALUES ('admin@teste.com', 'Admin Teste', %s, 'admin', %s)
            ON CONFLICT (email) DO NOTHING
            """,
            (hash_password("123456"), DEFAULT_TENANT_ID),
        )
        print("Usuario admin@teste.com garantido")
    except Exception as e:
        print(f"Seed de usuario pulado: {e}")

    conn.close()
    print("\nSeed completo! Reinicie o backend e acesse o dashboard.")


if __name__ == "__main__":
    main()
