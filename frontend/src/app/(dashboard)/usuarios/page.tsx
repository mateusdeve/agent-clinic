"use client";

import * as React from "react";
import { PaginationState } from "@tanstack/react-table";
import { useSession } from "next-auth/react";
import { SystemUser, PaginatedResponse } from "@/lib/types";
import { apiFetch } from "@/lib/api";
import { DataTable } from "@/components/dashboard/DataTable";
import { SlideOver } from "@/components/dashboard/SlideOver";
import { getUserColumns } from "./columns";
import { UserForm } from "./user-form";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

type FormMode = "create" | "edit";

export default function UsuariosPage() {
  const { data: session } = useSession();
  // NextAuth v5 beta: user.id from session.user
  const currentUserId = (session?.user as any)?.id ?? null;

  const [users, setUsers] = React.useState<SystemUser[]>([]);
  const [total, setTotal] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Slide-over para criar/editar usuario
  const [slideOverOpen, setSlideOverOpen] = React.useState(false);
  const [selectedUser, setSelectedUser] = React.useState<SystemUser | null>(null);
  const [formMode, setFormMode] = React.useState<FormMode>("create");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Dialog de confirmacao de status (ativar/desativar)
  const [statusDialogOpen, setStatusDialogOpen] = React.useState(false);
  const [statusUser, setStatusUser] = React.useState<SystemUser | null>(null);
  const [isTogglingStatus, setIsTogglingStatus] = React.useState(false);

  // Dialog de redefinicao de senha
  const [passwordDialogOpen, setPasswordDialogOpen] = React.useState(false);
  const [passwordUser, setPasswordUser] = React.useState<SystemUser | null>(null);
  const [newPassword, setNewPassword] = React.useState("");
  const [passwordMsg, setPasswordMsg] = React.useState<string | null>(null);
  const [isResettingPassword, setIsResettingPassword] = React.useState(false);

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });

  const pageCount = Math.ceil(total / pagination.pageSize) || 1;

  const fetchUsers = React.useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const page = pagination.pageIndex + 1;
      const data = await apiFetch<PaginatedResponse<SystemUser>>(
        `/api/users?page=${page}&per_page=${pagination.pageSize}`
      );
      setUsers(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar usuarios");
    } finally {
      setIsLoading(false);
    }
  }, [pagination.pageIndex, pagination.pageSize]);

  React.useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  function openNewUser() {
    setSelectedUser(null);
    setFormMode("create");
    setSlideOverOpen(true);
  }

  function openEditUser(user: SystemUser) {
    setSelectedUser(user);
    setFormMode("edit");
    setSlideOverOpen(true);
  }

  function openToggleStatus(user: SystemUser) {
    setStatusUser(user);
    setStatusDialogOpen(true);
  }

  function openResetPassword(user: SystemUser) {
    setPasswordUser(user);
    setNewPassword("");
    setPasswordMsg(null);
    setPasswordDialogOpen(true);
  }

  async function handleFormSubmit(data: { name?: string; email?: string; password?: string; role: "admin" | "recepcionista" | "medico" }) {
    try {
      setIsSubmitting(true);
      if (formMode === "create") {
        await apiFetch("/api/users", {
          method: "POST",
          body: JSON.stringify(data),
        });
      } else if (selectedUser) {
        await apiFetch(`/api/users/${selectedUser.id}/role`, {
          method: "PATCH",
          body: JSON.stringify({ role: data.role }),
        });
      }
      setSlideOverOpen(false);
      setSelectedUser(null);
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar usuario");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleConfirmStatusToggle() {
    if (!statusUser) return;
    try {
      setIsTogglingStatus(true);
      await apiFetch(`/api/users/${statusUser.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !statusUser.is_active }),
      });
      setStatusDialogOpen(false);
      setStatusUser(null);
      await fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao alterar status");
    } finally {
      setIsTogglingStatus(false);
    }
  }

  async function handlePasswordReset() {
    if (!passwordUser || !newPassword) return;
    try {
      setIsResettingPassword(true);
      setPasswordMsg(null);
      await apiFetch(`/api/users/${passwordUser.id}/reset-password`, {
        method: "POST",
        body: JSON.stringify({ new_password: newPassword }),
      });
      setPasswordMsg("Senha redefinida com sucesso!");
      setNewPassword("");
    } catch (err) {
      setPasswordMsg(err instanceof Error ? err.message : "Erro ao redefinir senha");
    } finally {
      setIsResettingPassword(false);
    }
  }

  const columns = getUserColumns({
    onEdit: openEditUser,
    onResetPassword: openResetPassword,
    onToggleStatus: openToggleStatus,
    currentUserId,
  });

  return (
    <div className="space-y-6">
      {/* Cabecalho */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-serif font-semibold text-gray-900">
            Usuarios
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Gerencie os usuarios e permissoes de acesso ao sistema.
          </p>
        </div>
        <Button onClick={openNewUser}>Novo Usuario</Button>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Tabela de usuarios */}
      <DataTable
        columns={columns}
        data={users}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
      />

      {/* Slide-over: Criar/Editar usuario */}
      <SlideOver
        open={slideOverOpen}
        onClose={() => {
          setSlideOverOpen(false);
          setSelectedUser(null);
        }}
        title={formMode === "create" ? "Novo Usuario" : "Editar Usuario"}
      >
        <UserForm
          user={selectedUser}
          mode={formMode}
          onSubmit={handleFormSubmit}
          onCancel={() => {
            setSlideOverOpen(false);
            setSelectedUser(null);
          }}
          isSubmitting={isSubmitting}
        />
      </SlideOver>

      {/* Dialog: Confirmar ativar/desativar */}
      <Dialog open={statusDialogOpen} onOpenChange={(open) => {
        if (!open) setStatusDialogOpen(false);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {statusUser?.is_active ? "Desativar usuario" : "Reativar usuario"}
            </DialogTitle>
            <DialogDescription>
              {statusUser?.is_active
                ? `Deseja desativar o usuario "${statusUser?.name}"? O usuario perdera acesso ao sistema.`
                : `Deseja reativar o usuario "${statusUser?.name}"? O usuario recuperara acesso ao sistema.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setStatusDialogOpen(false)}
              disabled={isTogglingStatus}
            >
              Cancelar
            </Button>
            <Button
              variant={statusUser?.is_active ? "destructive" : "default"}
              onClick={handleConfirmStatusToggle}
              disabled={isTogglingStatus}
            >
              {isTogglingStatus
                ? "Aguarde..."
                : statusUser?.is_active
                ? "Desativar"
                : "Reativar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Redefinir senha */}
      <Dialog open={passwordDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setPasswordDialogOpen(false);
          setPasswordMsg(null);
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Redefinir Senha</DialogTitle>
            <DialogDescription>
              Defina uma nova senha para o usuario{" "}
              <span className="font-medium">{passwordUser?.name}</span>.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            <Input
              type="password"
              placeholder="Nova senha (minimo 6 caracteres)"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={isResettingPassword}
            />
            {passwordMsg && (
              <p
                className={`text-sm ${
                  passwordMsg.includes("sucesso")
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {passwordMsg}
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setPasswordDialogOpen(false);
                setPasswordMsg(null);
              }}
              disabled={isResettingPassword}
            >
              Fechar
            </Button>
            <Button
              onClick={handlePasswordReset}
              disabled={isResettingPassword || newPassword.length < 6}
            >
              {isResettingPassword ? "Redefinindo..." : "Confirmar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
