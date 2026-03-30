"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { PaginationState } from "@tanstack/react-table";
import { apiFetch } from "@/lib/api";
import type { CampaignDetail, CampaignRecipient, PaginatedResponse } from "@/lib/types";
import { DataTable } from "@/components/dashboard/DataTable";
import { buildRecipientColumns } from "@/components/dashboard/RecipientTable";
import { CampaignStatusBadge } from "@/components/dashboard/CampaignStatusBadge";
import { ChevronLeft } from "lucide-react";

const PER_PAGE = 20;

export default function CampaignDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [campaign, setCampaign] = React.useState<CampaignDetail | null>(null);
  const [recipients, setRecipients] = React.useState<CampaignRecipient[]>([]);
  const [total, setTotal] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(false);
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: PER_PAGE,
  });

  const columns = React.useMemo(() => buildRecipientColumns(), []);
  const pageCount = Math.max(1, Math.ceil(total / PER_PAGE));

  async function loadData(page: number) {
    if (!id) return;
    setIsLoading(true);
    try {
      const [camp, recips] = await Promise.all([
        apiFetch<CampaignDetail>(`/api/campaigns/${id}`),
        apiFetch<PaginatedResponse<CampaignRecipient>>(
          `/api/campaigns/${id}/recipients?page=${page + 1}&per_page=${PER_PAGE}`
        ),
      ]);
      setCampaign(camp);
      setRecipients(recips.items);
      setTotal(recips.total);
    } catch (err) {
      console.error("[campaign-detail] load error:", err);
    } finally {
      setIsLoading(false);
    }
  }

  // Carrega ao montar e ao mudar paginacao
  React.useEffect(() => {
    loadData(pagination.pageIndex);
  }, [id, pagination.pageIndex]);

  // Polling a cada 10s enquanto status === "enviando"
  React.useEffect(() => {
    if (campaign?.status !== "enviando") return;

    const intervalId = setInterval(() => {
      loadData(pagination.pageIndex);
    }, 10000);

    return () => clearInterval(intervalId);
  }, [campaign?.status, pagination.pageIndex]);

  if (!campaign && isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-gray-400">Carregando campanha...</p>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="flex items-center justify-center py-24">
        <p className="text-gray-400">Campanha nao encontrada.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Voltar */}
      <Link
        href="/campanhas"
        className="inline-flex items-center gap-1 text-sm text-green-700 hover:underline"
      >
        <ChevronLeft className="size-4" />
        Voltar para Campanhas
      </Link>

      {/* Header */}
      <div className="flex items-center gap-3">
        <h1 className="font-serif text-2xl font-semibold text-gray-900">
          {campaign.nome}
        </h1>
        <CampaignStatusBadge status={campaign.status} />
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Enviado"
          value={campaign.stats.enviado}
          colorClass="text-blue-700 bg-blue-50 border-blue-200"
        />
        <StatCard
          label="Entregue"
          value={campaign.stats.entregue}
          colorClass="text-green-700 bg-green-50 border-green-200"
        />
        <StatCard
          label="Lido"
          value={campaign.stats.lido}
          colorClass="text-emerald-700 bg-emerald-50 border-emerald-200"
        />
        <StatCard
          label="Falha"
          value={campaign.stats.falha}
          colorClass="text-red-700 bg-red-50 border-red-200"
        />
      </div>

      {/* Tabela de destinatarios */}
      <div>
        <h2 className="text-base font-semibold text-gray-700 mb-3">
          Destinatarios ({total})
        </h2>
        <DataTable
          columns={columns}
          data={recipients}
          pageCount={pageCount}
          pagination={pagination}
          onPaginationChange={setPagination}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: number;
  colorClass: string;
}) {
  return (
    <div className={`rounded-lg border p-4 flex flex-col gap-1 ${colorClass}`}>
      <p className="text-xs font-semibold uppercase tracking-wide opacity-70">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
