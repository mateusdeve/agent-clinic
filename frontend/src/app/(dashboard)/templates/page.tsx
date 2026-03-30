"use client";

import * as React from "react";
import { PaginationState } from "@tanstack/react-table";
import { Plus } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { MessageTemplate, PaginatedResponse } from "@/lib/types";
import { DataTable } from "@/components/dashboard/DataTable";
import { buildTemplateColumns } from "@/components/dashboard/TemplatesTable";
import { TemplateSlideOver } from "@/components/dashboard/TemplateSlideOver";

// ─── Pagina de Templates ──────────────────────────────────────────────────────

export default function TemplatesPage() {
  // Dados
  const [templates, setTemplates] = React.useState<MessageTemplate[]>([]);
  const [total, setTotal] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Paginacao
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });

  // Slide-over
  const [slideOverOpen, setSlideOverOpen] = React.useState(false);
  const [editingTemplate, setEditingTemplate] =
    React.useState<MessageTemplate | null>(null);

  // ─── Fetch ────────────────────────────────────────────────────────────────────

  const fetchTemplates = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiFetch<PaginatedResponse<MessageTemplate>>(
        `/api/templates?page=${pagination.pageIndex + 1}&per_page=${pagination.pageSize}`
      );
      setTemplates(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erro ao carregar templates"
      );
    } finally {
      setIsLoading(false);
    }
  }, [pagination.pageIndex, pagination.pageSize]);

  React.useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  // ─── Acoes ────────────────────────────────────────────────────────────────────

  const handleEdit = (t: MessageTemplate) => {
    setEditingTemplate(t);
    setSlideOverOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (
      !window.confirm("Tem certeza que deseja excluir este template?")
    ) {
      return;
    }
    try {
      await apiFetch(`/api/templates/${id}`, { method: "DELETE" });
      fetchTemplates();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erro ao excluir template"
      );
    }
  };

  const openCreate = () => {
    setEditingTemplate(null);
    setSlideOverOpen(true);
  };

  const closeSlideOver = () => {
    setSlideOverOpen(false);
    setEditingTemplate(null);
  };

  const handleSaved = () => {
    fetchTemplates();
  };

  // ─── Colunas ──────────────────────────────────────────────────────────────────

  const columns = React.useMemo(
    () =>
      buildTemplateColumns({
        onEdit: handleEdit,
        onDelete: handleDelete,
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const pageCount = Math.ceil(total / pagination.pageSize);

  // ─── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-6">
      {/* Cabecalho da pagina */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-serif font-bold text-gray-900">
            Templates de Mensagem
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Gerencie os templates de mensagem para campanhas e envios rapidos
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors"
        >
          <Plus className="size-4" />
          Novo Template
        </button>
      </div>

      {/* Erro */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Estado vazio */}
      {templates.length === 0 && !isLoading && !error && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-gray-500 text-sm max-w-sm">
            Nenhum template criado. Crie seu primeiro template para enviar
            mensagens padronizadas.
          </p>
        </div>
      )}

      {/* Tabela */}
      {(templates.length > 0 || isLoading) && (
        <DataTable
          columns={columns}
          data={templates}
          pageCount={pageCount}
          pagination={pagination}
          onPaginationChange={setPagination}
          isLoading={isLoading}
        />
      )}

      {/* Slide-over criar/editar */}
      <TemplateSlideOver
        open={slideOverOpen}
        onClose={closeSlideOver}
        template={editingTemplate}
        onSaved={handleSaved}
      />
    </div>
  );
}
