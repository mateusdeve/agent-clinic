"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { format, parseISO } from "date-fns";
import { useRouter } from "next/navigation";
import type { Patient } from "@/lib/types";

// Callback types exportados para uso na pagina pai
export interface PatientActionCallbacks {
  onEdit: (patient: Patient) => void;
}

// Funcao que retorna as colunas com acesso aos callbacks de acao
export function buildPatientColumns(
  callbacks: PatientActionCallbacks
): ColumnDef<Patient>[] {
  return [
    {
      accessorKey: "nome",
      header: "Paciente",
      cell: ({ row }) => (
        <span className="font-medium text-gray-800">{row.original.nome}</span>
      ),
    },
    {
      accessorKey: "phone",
      header: "Telefone",
      cell: ({ row }) => (
        <span className="text-gray-600 font-mono text-sm">
          {row.original.phone}
        </span>
      ),
    },
    {
      accessorKey: "data_nascimento",
      header: "Nascimento",
      cell: ({ row }) => {
        const val = row.original.data_nascimento;
        if (!val) return <span className="text-gray-400">-</span>;
        try {
          return (
            <span className="text-gray-600">
              {format(parseISO(val), "dd/MM/yyyy")}
            </span>
          );
        } catch {
          return <span className="text-gray-400">-</span>;
        }
      },
    },
    {
      accessorKey: "total_consultas",
      header: "Consultas",
      cell: ({ row }) => (
        <span className="text-gray-700 tabular-nums">
          {row.original.total_consultas}
        </span>
      ),
    },
    {
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <ActionCell patient={row.original} callbacks={callbacks} />
      ),
    },
  ];
}

// Componente separado para poder usar hooks (useRouter)
function ActionCell({
  patient,
  callbacks,
}: {
  patient: Patient;
  callbacks: PatientActionCallbacks;
}) {
  const router = useRouter();

  return (
    <div className="flex items-center gap-2 justify-end">
      <button
        onClick={() => callbacks.onEdit(patient)}
        className="text-sm text-green-600 hover:text-green-800 font-medium transition-colors px-2 py-1 rounded hover:bg-green-50"
      >
        Editar
      </button>
      <button
        onClick={() => router.push(`/pacientes/${patient.id}`)}
        className="text-sm text-gray-500 hover:text-gray-700 font-medium transition-colors px-2 py-1 rounded hover:bg-gray-50"
      >
        Ver Perfil
      </button>
    </div>
  );
}
