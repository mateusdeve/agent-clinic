"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import type { CampaignRecipient } from "@/lib/types";
import { RecipientStatusBadge } from "./CampaignStatusBadge";

const ptBR = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function buildRecipientColumns(): ColumnDef<CampaignRecipient>[] {
  return [
    {
      accessorKey: "phone",
      header: "Telefone",
      cell: ({ row }) => (
        <span className="text-gray-700 font-mono text-sm">{row.original.phone}</span>
      ),
    },
    {
      accessorKey: "patient_nome",
      header: "Paciente",
      cell: ({ row }) => (
        <span className="text-gray-800">{row.original.patient_nome}</span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <RecipientStatusBadge status={row.original.status} />,
    },
    {
      accessorKey: "erro",
      header: "Erro",
      cell: ({ row }) => (
        <span className={row.original.erro ? "text-red-600 text-sm" : "text-gray-400 text-sm"}>
          {row.original.erro ?? "-"}
        </span>
      ),
    },
    {
      accessorKey: "sent_at",
      header: "Enviado em",
      cell: ({ row }) => {
        const value = row.original.sent_at;
        const formatted = value ? ptBR.format(new Date(value)) : "-";
        return <span className="text-gray-500 text-sm">{formatted}</span>;
      },
    },
  ];
}
