"use client";

import * as React from "react";
import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";
import { apiFetch } from "@/lib/api";
import type { Patient, Appointment } from "@/lib/types";

interface PatientSidebarProps {
  patientId: string | null;
  phone?: string | null;
}

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  agendado: { label: "Agendado", className: "bg-blue-100 text-blue-700" },
  confirmado: { label: "Confirmado", className: "bg-green-100 text-green-700" },
  realizado: { label: "Realizado", className: "bg-gray-100 text-gray-600" },
  cancelado: { label: "Cancelado", className: "bg-red-100 text-red-700" },
};

function formatDate(isoStr: string | null): string {
  if (!isoStr) return "—";
  try {
    return format(parseISO(isoStr), "dd/MM/yyyy", { locale: ptBR });
  } catch {
    return isoStr;
  }
}

function getInitials(name: string | null | undefined): string {
  if (!name) return "?";
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

export function PatientSidebar({ patientId, phone }: PatientSidebarProps) {
  const [patient, setPatient] = React.useState<Patient | null>(null);
  const [appointments, setAppointments] = React.useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);

  React.useEffect(() => {
    if (!patientId) {
      setPatient(null);
      setAppointments([]);
      return;
    }

    let cancelled = false;
    async function loadData() {
      setIsLoading(true);
      try {
        const [patientData, apptData] = await Promise.all([
          apiFetch<Patient>(`/api/patients/${patientId}`),
          apiFetch<{ items: Appointment[] }>(
            `/api/appointments?patient_id=${patientId}&per_page=5`
          ),
        ]);
        if (!cancelled) {
          setPatient(patientData);
          setAppointments(apptData.items ?? []);
        }
      } catch (err) {
        console.error("[PatientSidebar] load error:", err);
        if (!cancelled) {
          setPatient(null);
          setAppointments([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    loadData();
    return () => { cancelled = true; };
  }, [patientId]);

  if (!patientId) {
    return (
      <div className="flex items-center justify-center h-full bg-white p-4">
        <p className="text-sm text-gray-400">Paciente nao identificado</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4 p-4 bg-white h-full">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gray-200 animate-pulse shrink-0" />
          <div className="flex flex-col gap-1 flex-1">
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
            <div className="h-3 bg-gray-200 rounded animate-pulse w-1/2" />
          </div>
        </div>
        <div className="h-px bg-gray-100" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col bg-white h-full overflow-y-auto">
      {/* Patient card */}
      <div className="p-4 border-b border-gray-100">
        {/* Avatar */}
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-green-600 flex items-center justify-center shrink-0">
            <span className="text-white text-sm font-semibold">
              {getInitials(patient?.nome)}
            </span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900 truncate">
              {patient?.nome || phone || "—"}
            </p>
            <p className="text-xs text-gray-500 truncate">{patient?.phone || phone || "—"}</p>
          </div>
        </div>

        {/* Meta */}
        {patient?.created_at && (
          <p className="text-xs text-gray-400">
            Paciente desde {formatDate(patient.created_at)}
          </p>
        )}
      </div>

      {/* Appointments */}
      <div className="flex-1 p-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Proximas consultas
        </h3>
        {appointments.length === 0 ? (
          <p className="text-xs text-gray-400">Nenhuma consulta agendada</p>
        ) : (
          <div className="flex flex-col gap-2">
            {appointments.map((appt) => {
              const badge = STATUS_LABELS[appt.status] || {
                label: appt.status,
                className: "bg-gray-100 text-gray-600",
              };
              return (
                <div
                  key={appt.id}
                  className="rounded-lg border border-gray-100 p-2.5 text-xs"
                >
                  <div className="flex items-start justify-between gap-1 mb-1">
                    <p className="font-medium text-gray-800 truncate">
                      {appt.doctor_nome}
                    </p>
                    <span
                      className={`shrink-0 px-1.5 py-0.5 rounded-full text-[10px] font-medium ${badge.className}`}
                    >
                      {badge.label}
                    </span>
                  </div>
                  <p className="text-gray-500">
                    {formatDate(appt.data_agendamento)} • {appt.horario}
                  </p>
                  <p className="text-gray-400 truncate">{appt.especialidade}</p>
                </div>
              );
            })}
          </div>
        )}

        {/* Link to full profile */}
        {patientId && (
          <a
            href={`/pacientes?id=${patientId}`}
            className="mt-4 block text-center text-xs text-green-700 hover:text-green-800 font-medium py-1.5 border border-green-200 rounded-lg hover:bg-green-50 transition-colors"
          >
            Ver perfil completo
          </a>
        )}
      </div>
    </div>
  );
}
