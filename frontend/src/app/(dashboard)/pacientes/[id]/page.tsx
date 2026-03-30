"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Phone, Calendar, StickyNote } from "lucide-react";
import { format, parseISO } from "date-fns";
import { apiFetch } from "@/lib/api";
import type { Patient } from "@/lib/types";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import { AppointmentHistory } from "@/components/dashboard/patient/AppointmentHistory";
import { WhatsAppTimeline } from "@/components/dashboard/patient/WhatsAppTimeline";

export default function PatientProfilePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const patientId = params.id;

  const [patient, setPatient] = React.useState<Patient | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiFetch<Patient>(`/api/patients/${patientId}`);
        if (!cancelled) setPatient(data);
      } catch (err) {
        if (!cancelled)
          setError(
            err instanceof Error ? err.message : "Paciente nao encontrado"
          );
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  // ─── Loading state ─────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        {/* Back button skeleton */}
        <div className="w-24 h-8 rounded bg-gray-200 animate-pulse" />
        {/* Header skeleton */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col gap-3">
          <div className="w-48 h-8 rounded bg-gray-200 animate-pulse" />
          <div className="w-32 h-4 rounded bg-gray-200 animate-pulse" />
          <div className="w-40 h-4 rounded bg-gray-200 animate-pulse" />
        </div>
      </div>
    );
  }

  // ─── Error state ───────────────────────────────────────────────────────────

  if (error || !patient) {
    return (
      <div className="flex flex-col gap-6">
        <button
          onClick={() => router.push("/pacientes")}
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors w-fit"
        >
          <ArrowLeft className="size-4" />
          Voltar para Pacientes
        </button>
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error ?? "Paciente nao encontrado"}
        </div>
      </div>
    );
  }

  // ─── Render ────────────────────────────────────────────────────────────────

  const nascimentoFormatted = patient.data_nascimento
    ? (() => {
        try {
          return format(parseISO(patient.data_nascimento), "dd/MM/yyyy");
        } catch {
          return patient.data_nascimento;
        }
      })()
    : null;

  return (
    <div className="flex flex-col gap-6">
      {/* Botao voltar */}
      <button
        onClick={() => router.push("/pacientes")}
        className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors w-fit"
      >
        <ArrowLeft className="size-4" />
        Voltar para Pacientes
      </button>

      {/* Header do perfil */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h1 className="text-2xl font-serif font-bold text-gray-900 mb-3">
          {patient.nome}
        </h1>

        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <span className="inline-flex items-center gap-1.5">
            <Phone className="size-4 text-gray-400" />
            <span className="font-mono">{patient.phone}</span>
          </span>

          {nascimentoFormatted && (
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="size-4 text-gray-400" />
              {nascimentoFormatted}
            </span>
          )}

          <span className="inline-flex items-center gap-1.5 text-gray-500">
            <span className="font-medium text-gray-700">
              {patient.total_consultas}
            </span>{" "}
            {patient.total_consultas === 1 ? "consulta" : "consultas"}
          </span>
        </div>

        {patient.notas && (
          <div className="mt-4 flex items-start gap-2 text-sm text-gray-600 bg-gray-50 rounded-md p-3">
            <StickyNote className="size-4 text-gray-400 shrink-0 mt-0.5" />
            <p className="whitespace-pre-wrap">{patient.notas}</p>
          </div>
        )}
      </div>

      {/* Abas: Consultas e Conversas */}
      <Tabs defaultValue="consultas" className="w-full">
        <TabsList className="bg-white border border-gray-200 p-1 h-auto rounded-lg">
          <TabsTrigger
            value="consultas"
            className="data-[state=active]:bg-green-600 data-[state=active]:text-white rounded-md px-4 py-2 text-sm font-medium transition-all"
          >
            Consultas
          </TabsTrigger>
          <TabsTrigger
            value="conversas"
            className="data-[state=active]:bg-green-600 data-[state=active]:text-white rounded-md px-4 py-2 text-sm font-medium transition-all"
          >
            Conversas WhatsApp
          </TabsTrigger>
        </TabsList>

        <TabsContent value="consultas" className="mt-4">
          <AppointmentHistory patientId={patientId} />
        </TabsContent>

        <TabsContent value="conversas" className="mt-4">
          <WhatsAppTimeline patientId={patientId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
