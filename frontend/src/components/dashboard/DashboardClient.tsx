"use client";

import { useEffect, useState } from "react";
import { CalendarCheck, TrendingUp, UserX, Clock, MessageCircle } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { DashboardStats, DashboardCharts } from "@/lib/types";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { ErrorAlert } from "@/components/dashboard/ErrorAlert";
import { ProximasConsultas } from "@/components/dashboard/ProximasConsultas";
import { TrendChart } from "@/components/dashboard/TrendChart";
import { EspecialidadeChart } from "@/components/dashboard/EspecialidadeChart";

interface DashboardClientProps {
  role: string;
}

export function DashboardClient({ role }: DashboardClientProps) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [charts, setCharts] = useState<DashboardCharts | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const statsData = await apiFetch<DashboardStats>("/api/dashboard/stats");
        setStats(statsData);

        if (role === "admin") {
          const chartsData = await apiFetch<DashboardCharts>("/api/dashboard/charts");
          setCharts(chartsData);
        }
      } catch (err) {
        console.error("[DashboardClient] erro ao carregar dados:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [role]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 h-20 animate-pulse" />
          ))}
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4 h-40 animate-pulse" />
      </div>
    );
  }

  if (!stats) {
    return (
      <ErrorAlert message="Nao foi possivel carregar os dados do dashboard." />
    );
  }

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <KpiCard
          label="Consultas Hoje"
          value={stats.consultas_hoje}
          icon={CalendarCheck}
          color="bg-green-50"
          iconColor="text-green-600"
        />
        <KpiCard
          label="Taxa de Ocupacao"
          value={`${stats.taxa_ocupacao}%`}
          icon={TrendingUp}
          color="bg-blue-50"
          iconColor="text-blue-600"
        />
        <KpiCard
          label="No-shows"
          value={stats.no_shows}
          icon={UserX}
          color="bg-red-50"
          iconColor="text-red-600"
        />
        <KpiCard
          label="Confirmacoes Pendentes"
          value={stats.confirmacoes_pendentes}
          icon={Clock}
          color="bg-yellow-50"
          iconColor="text-yellow-600"
        />
        <KpiCard
          label="Conversas WhatsApp"
          value={stats.conversas_ativas}
          icon={MessageCircle}
          color="bg-emerald-50"
          iconColor="text-emerald-600"
        />
      </div>

      {/* Proximas consultas table */}
      <ProximasConsultas data={stats.proximas_consultas} />

      {/* Admin-only charts */}
      {role === "admin" && charts && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TrendChart data={charts.trend} />
          <EspecialidadeChart data={charts.especialidades} />
        </div>
      )}
    </div>
  );
}
