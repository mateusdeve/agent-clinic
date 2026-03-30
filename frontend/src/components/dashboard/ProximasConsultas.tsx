"use client";

import type { ProximaConsulta } from "@/lib/types";
import { StatusBadge } from "@/components/dashboard/StatusBadge";

interface ProximasConsultasProps {
  data: ProximaConsulta[];
}

export function ProximasConsultas({ data }: ProximasConsultasProps) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Proximas Consultas</h3>
        <p className="text-sm text-gray-400 text-center py-4">
          Nenhuma consulta agendada para hoje.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Proximas Consultas</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Horario
              </th>
              <th className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Paciente
              </th>
              <th className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Medico
              </th>
              <th className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Especialidade
              </th>
              <th className="text-left py-2 px-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((consulta) => (
              <tr
                key={consulta.id}
                className="border-b border-gray-50 hover:bg-green-50 transition-colors"
              >
                <td className="py-3 px-3 text-gray-800 font-medium">{consulta.horario}</td>
                <td className="py-3 px-3 text-gray-700">{consulta.patient_nome}</td>
                <td className="py-3 px-3 text-gray-700">{consulta.doctor_nome}</td>
                <td className="py-3 px-3 text-gray-500">{consulta.especialidade}</td>
                <td className="py-3 px-3">
                  <StatusBadge status={consulta.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
