"use client";

import * as React from "react";
import { Plus } from "lucide-react";
import { PaginationState } from "@tanstack/react-table";
import { apiFetch } from "@/lib/api";
import type { Campaign, PaginatedResponse } from "@/lib/types";
import { DataTable } from "@/components/dashboard/DataTable";
import { buildCampaignColumns } from "@/components/dashboard/CampaignTable";
import { CampaignWizard } from "@/components/dashboard/CampaignWizard";
import { Button } from "@/components/ui/button";

const PER_PAGE = 20;

export default function CampanhasPage() {
  const [campaigns, setCampaigns] = React.useState<Campaign[]>([]);
  const [total, setTotal] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(false);
  const [wizardOpen, setWizardOpen] = React.useState(false);
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: PER_PAGE,
  });

  const columns = React.useMemo(() => buildCampaignColumns(), []);
  const pageCount = Math.max(1, Math.ceil(total / PER_PAGE));

  async function loadCampaigns(page: number) {
    setIsLoading(true);
    try {
      const data = await apiFetch<PaginatedResponse<Campaign>>(
        `/api/campaigns?page=${page + 1}&per_page=${PER_PAGE}`
      );
      setCampaigns(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error("[campanhas] load error:", err);
    } finally {
      setIsLoading(false);
    }
  }

  // Carrega ao montar e ao mudar de pagina
  React.useEffect(() => {
    loadCampaigns(pagination.pageIndex);
  }, [pagination.pageIndex]);

  // Polling a cada 30s enquanto ha campanha "enviando"
  React.useEffect(() => {
    const hasEnviando = campaigns.some((c) => c.status === "enviando");
    if (!hasEnviando) return;

    const intervalId = setInterval(() => {
      loadCampaigns(pagination.pageIndex);
    }, 30000);

    return () => clearInterval(intervalId);
  }, [campaigns, pagination.pageIndex]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-2xl font-semibold text-gray-900">
          Campanhas
        </h1>
        <Button
          onClick={() => setWizardOpen(true)}
          className="bg-green-600 hover:bg-green-700 text-white gap-1.5"
        >
          <Plus className="size-4" />
          Nova Campanha
        </Button>
      </div>

      {/* Tabela */}
      {campaigns.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 py-16 text-center">
          <p className="text-base font-medium text-gray-500">Nenhuma campanha criada.</p>
          <p className="text-sm text-gray-400 mt-1 max-w-sm">
            Crie templates primeiro e depois envie campanhas para seus pacientes.
          </p>
          <Button
            onClick={() => setWizardOpen(true)}
            className="mt-4 bg-green-600 hover:bg-green-700 text-white"
          >
            Criar primeira campanha
          </Button>
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={campaigns}
          pageCount={pageCount}
          pagination={pagination}
          onPaginationChange={setPagination}
          isLoading={isLoading}
        />
      )}

      {/* Wizard */}
      <CampaignWizard
        open={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onCreated={() => loadCampaigns(pagination.pageIndex)}
      />
    </div>
  );
}
