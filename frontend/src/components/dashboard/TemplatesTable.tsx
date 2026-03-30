"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { Pencil, Trash2 } from "lucide-react";
import type { MessageTemplate } from "@/lib/types";

// ─── Opcoes do builder de colunas ─────────────────────────────────────────────

interface BuildTemplateColumnsOpts {
  onEdit: (t: MessageTemplate) => void;
  onDelete: (id: string) => void;
}

// ─── Formatador de data pt-BR ─────────────────────────────────────────────────

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

function formatDate(isoDate: string): string {
  try {
    return dateFormatter.format(new Date(isoDate));
  } catch {
    return isoDate;
  }
}

// ─── Definicoes de colunas ────────────────────────────────────────────────────

export function buildTemplateColumns(
  opts: BuildTemplateColumnsOpts
): ColumnDef<MessageTemplate>[] {
  return [
    {
      accessorKey: "nome",
      header: "Nome",
      cell: ({ row }) => (
        <span className="font-medium text-gray-900">{row.original.nome}</span>
      ),
    },
    {
      accessorKey: "corpo",
      header: "Preview",
      cell: ({ row }) => {
        const preview =
          row.original.corpo.length > 60
            ? row.original.corpo.slice(0, 60) + "..."
            : row.original.corpo;
        return (
          <span className="text-gray-600 text-sm whitespace-nowrap">
            {preview}
          </span>
        );
      },
    },
    {
      accessorKey: "variaveis_usadas",
      header: "Variaveis",
      cell: ({ row }) => {
        const count = row.original.variaveis_usadas.length;
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            {count} {count === 1 ? "var" : "vars"}
          </span>
        );
      },
    },
    {
      accessorKey: "updated_at",
      header: "Atualizado",
      cell: ({ row }) => (
        <span className="text-sm text-gray-500">
          {formatDate(row.original.updated_at)}
        </span>
      ),
    },
    {
      id: "acoes",
      header: "Acoes",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => opts.onEdit(row.original)}
            aria-label="Editar template"
            className="p-1.5 rounded-md text-gray-500 hover:text-green-700 hover:bg-green-50 transition-colors"
          >
            <Pencil className="size-4" />
          </button>
          <button
            onClick={() => opts.onDelete(row.original.id)}
            aria-label="Excluir template"
            className="p-1.5 rounded-md text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors"
          >
            <Trash2 className="size-4" />
          </button>
        </div>
      ),
    },
  ];
}
