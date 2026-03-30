"use client";

import { ColumnDef } from "@tanstack/react-table";
import { Doctor } from "@/lib/types";
import { Button } from "@/components/ui/button";

interface DoctorColumnsOptions {
  onEdit: (doctor: Doctor) => void;
  onSchedule: (doctor: Doctor) => void;
}

export function getDoctorColumns({
  onEdit,
  onSchedule,
}: DoctorColumnsOptions): ColumnDef<Doctor>[] {
  return [
    {
      accessorKey: "nome",
      header: "Medico",
    },
    {
      accessorKey: "especialidade",
      header: "Especialidade",
    },
    {
      accessorKey: "crm",
      header: "CRM",
    },
    {
      id: "actions",
      header: "Acoes",
      cell: ({ row }) => {
        const doctor = row.original;
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(doctor)}
            >
              Editar
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSchedule(doctor)}
            >
              Horarios
            </Button>
          </div>
        );
      },
    },
  ];
}
