"use client";

import { ColumnDef } from "@tanstack/react-table";
import { SystemUser } from "@/lib/types";
import { Button } from "@/components/ui/button";

interface UserColumnsOptions {
  onEdit: (user: SystemUser) => void;
  onResetPassword: (user: SystemUser) => void;
  onToggleStatus: (user: SystemUser) => void;
  currentUserId: string | null;
}

const ROLE_BADGE: Record<SystemUser["role"], { label: string; className: string }> = {
  admin: { label: "Admin", className: "bg-purple-100 text-purple-700" },
  recepcionista: { label: "Recepcionista", className: "bg-blue-100 text-blue-700" },
  medico: { label: "Medico", className: "bg-green-100 text-green-700" },
};

export function getUserColumns({
  onEdit,
  onResetPassword,
  onToggleStatus,
  currentUserId,
}: UserColumnsOptions): ColumnDef<SystemUser>[] {
  return [
    {
      accessorKey: "name",
      header: "Nome",
    },
    {
      accessorKey: "email",
      header: "Email",
    },
    {
      accessorKey: "role",
      header: "Perfil",
      cell: ({ row }) => {
        const role = row.original.role;
        const badge = ROLE_BADGE[role];
        return (
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.className}`}
          >
            {badge.label}
          </span>
        );
      },
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => {
        const user = row.original;
        const isSelf = currentUserId === user.id;
        return (
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                user.is_active
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-500"
              }`}
            >
              {user.is_active ? "Ativo" : "Inativo"}
            </span>
            {/* Toggle switch */}
            <button
              type="button"
              role="switch"
              aria-checked={user.is_active}
              disabled={isSelf}
              onClick={() => onToggleStatus(user)}
              className={`
                relative inline-flex h-5 w-9 items-center rounded-full
                transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1
                ${user.is_active ? "bg-green-500" : "bg-gray-300"}
                ${isSelf ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}
              `}
              title={isSelf ? "Voce nao pode alterar seu proprio status" : undefined}
            >
              <span
                className={`
                  inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform
                  ${user.is_active ? "translate-x-4" : "translate-x-1"}
                `}
              />
            </button>
          </div>
        );
      },
    },
    {
      id: "actions",
      header: "Acoes",
      cell: ({ row }) => {
        const user = row.original;
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(user)}
            >
              Editar
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onResetPassword(user)}
            >
              Redefinir Senha
            </Button>
          </div>
        );
      },
    },
  ];
}
