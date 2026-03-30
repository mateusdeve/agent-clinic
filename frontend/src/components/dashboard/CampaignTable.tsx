"use client";

import * as React from "react";
import Link from "next/link";
import { ColumnDef } from "@tanstack/react-table";
import type { Campaign } from "@/lib/types";
import { CampaignStatusBadge } from "./CampaignStatusBadge";

const ptBR = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export function buildCampaignColumns(): ColumnDef<Campaign>[] {
  return [
    {
      accessorKey: "nome",
      header: "Nome",
      cell: ({ row }) => (
        <Link
          href={`/campanhas/${row.original.id}`}
          className="font-medium text-green-700 hover:underline"
        >
          {row.original.nome}
        </Link>
      ),
    },
    {
      accessorKey: "template_nome",
      header: "Template",
      cell: ({ row }) => (
        <span className="text-gray-700">{row.original.template_nome}</span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => <CampaignStatusBadge status={row.original.status} />,
    },
    {
      accessorKey: "total_recipients",
      header: "Destinatarios",
      cell: ({ row }) => (
        <span className="text-gray-700">{row.original.total_recipients}</span>
      ),
    },
    {
      id: "entregues",
      header: "Entregues",
      cell: ({ row }) => {
        const { stats, total_recipients } = row.original;
        const delivered = stats.enviado + stats.entregue + stats.lido;
        return (
          <span className="text-gray-700">
            {delivered}/{total_recipients}
          </span>
        );
      },
    },
    {
      accessorKey: "created_at",
      header: "Criado",
      cell: ({ row }) => {
        const date = row.original.created_at
          ? ptBR.format(new Date(row.original.created_at))
          : "-";
        return <span className="text-gray-500 text-sm">{date}</span>;
      },
    },
  ];
}
