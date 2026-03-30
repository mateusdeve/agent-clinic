// Shared TypeScript interfaces for MedIA API responses
// Cobre todos os tipos de entidade usados pelo painel web CRUD

// ─── Envelope de paginacao (D-12) ────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

// ─── Entidades principais ─────────────────────────────────────────────────────

export interface Patient {
  id: string;
  phone: string;
  nome: string;
  data_nascimento: string | null;
  notas: string | null;
  total_consultas: number;
  created_at: string;
}

export interface Doctor {
  id: string;
  nome: string;
  especialidade: string;
  crm: string;
  user_id: string | null;
  is_active: boolean;
}

export interface DoctorSchedule {
  id: string;
  doctor_id: string;
  day_of_week: number; // 0=Sunday ... 6=Saturday
  start_time: string;  // "08:00"
  end_time: string;    // "18:00"
}

export interface Appointment {
  id: string;
  patient_id: string;
  patient_nome: string;
  doctor_id: string;
  doctor_nome: string;
  especialidade: string;
  data_agendamento: string; // ISO date "2026-04-01"
  horario: string;          // "09:30"
  status: "agendado" | "confirmado" | "realizado" | "cancelado";
  motivo_cancelamento: string | null;
  created_at: string;
}

export type AppointmentStatus = Appointment["status"];

export interface SystemUser {
  id: string;
  email: string;
  name: string;
  role: "admin" | "recepcionista" | "medico";
  is_active: boolean;
  created_at: string;
}

export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface BlockedSlot {
  id: string;
  doctor_id: string;
  blocked_date: string;
  start_time: string | null;
  end_time: string | null;
  reason: string | null;
}
