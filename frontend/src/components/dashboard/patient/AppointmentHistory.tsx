"use client";

import * as React from "react";
import { format, parseISO } from "date-fns";
import { apiFetch } from "@/lib/api";
import type { Appointment } from "@/lib/types";
import { StatusBadge } from "@/components/dashboard/StatusBadge";

interface AppointmentHistoryProps {
  patientId: string;
}

export function AppointmentHistory({ patientId }: AppointmentHistoryProps) {
  const [appointments, setAppointments] = React.useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiFetch<Appointment[]>(
          `/api/patients/${patientId}/appointments`
        );
        if (!cancelled) {
          setAppointments(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Erro ao carregar consultas"
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  if (isLoading) {
    return (
      <div className="rounded-md border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {["Data", "Horario", "Medico", "Especialidade", "Status"].map(
                (h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                  >
                    {h}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 3 }).map((_, i) => (
              <tr key={i} className="border-b border-gray-100">
                {Array.from({ length: 5 }).map((_, j) => (
                  <td key={j} className="px-4 py-3">
                    <div
                      className="h-4 rounded bg-gray-200 animate-pulse"
                      style={{ width: j === 0 ? "6rem" : j === 2 ? "8rem" : "5rem" }}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (appointments.length === 0) {
    return (
      <div className="rounded-md border border-gray-200 bg-white px-4 py-8 text-center text-sm text-gray-400">
        Nenhuma consulta registrada
      </div>
    );
  }

  return (
    <div className="rounded-md border border-gray-200 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {["Data", "Horario", "Medico", "Especialidade", "Status"].map(
              (h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {appointments.map((appt, idx) => (
            <tr
              key={appt.id}
              className={
                idx < appointments.length - 1
                  ? "border-b border-gray-100"
                  : ""
              }
            >
              <td className="px-4 py-3 text-gray-700 tabular-nums">
                {appt.data_agendamento
                  ? (() => {
                      try {
                        return format(
                          parseISO(appt.data_agendamento),
                          "dd/MM/yyyy"
                        );
                      } catch {
                        return appt.data_agendamento;
                      }
                    })()
                  : "-"}
              </td>
              <td className="px-4 py-3 text-gray-700 font-mono tabular-nums">
                {appt.horario ?? "-"}
              </td>
              <td className="px-4 py-3 text-gray-800 font-medium">
                {appt.doctor_nome ?? "-"}
              </td>
              <td className="px-4 py-3 text-gray-600">
                {appt.especialidade ?? "-"}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={appt.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
