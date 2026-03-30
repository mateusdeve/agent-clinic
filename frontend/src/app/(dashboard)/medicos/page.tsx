"use client";

import * as React from "react";
import { PaginationState } from "@tanstack/react-table";
import { Doctor, PaginatedResponse, SystemUser } from "@/lib/types";
import { apiFetch } from "@/lib/api";
import { DataTable } from "@/components/dashboard/DataTable";
import { SlideOver } from "@/components/dashboard/SlideOver";
import { getDoctorColumns } from "./columns";
import { DoctorForm } from "./doctor-form";
import { ScheduleGrid } from "./schedule-grid";
import { Button } from "@/components/ui/button";

export default function MedicosPage() {
  const [doctors, setDoctors] = React.useState<Doctor[]>([]);
  const [total, setTotal] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Slide-over para criar/editar medico
  const [slideOverOpen, setSlideOverOpen] = React.useState(false);
  const [selectedDoctor, setSelectedDoctor] = React.useState<Doctor | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  // Slide-over para grade de horarios
  const [scheduleGridOpen, setScheduleGridOpen] = React.useState(false);
  const [scheduleDoctor, setScheduleDoctor] = React.useState<Doctor | null>(null);

  // Usuarios medico para vinculacao
  const [medicUsers, setMedicUsers] = React.useState<SystemUser[]>([]);

  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });

  const pageCount = Math.ceil(total / pagination.pageSize) || 1;

  // Buscar lista de medicos
  const fetchDoctors = React.useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const page = pagination.pageIndex + 1;
      const data = await apiFetch<PaginatedResponse<Doctor>>(
        `/api/doctors?page=${page}&per_page=${pagination.pageSize}`
      );
      setDoctors(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar medicos");
    } finally {
      setIsLoading(false);
    }
  }, [pagination.pageIndex, pagination.pageSize]);

  // Buscar usuarios com role medico para vinculacao
  const fetchMedicUsers = React.useCallback(async () => {
    try {
      const data = await apiFetch<PaginatedResponse<SystemUser>>(
        "/api/users?page=1&per_page=100"
      );
      setMedicUsers(data.items.filter((u) => u.role === "medico" && u.is_active));
    } catch {
      // Nao bloquear o fluxo principal se falhar
    }
  }, []);

  React.useEffect(() => {
    fetchDoctors();
  }, [fetchDoctors]);

  React.useEffect(() => {
    fetchMedicUsers();
  }, [fetchMedicUsers]);

  function openNewDoctor() {
    setSelectedDoctor(null);
    setSlideOverOpen(true);
  }

  function openEditDoctor(doctor: Doctor) {
    setSelectedDoctor(doctor);
    setSlideOverOpen(true);
  }

  function openScheduleGrid(doctor: Doctor) {
    setScheduleDoctor(doctor);
    setScheduleGridOpen(true);
  }

  async function handleFormSubmit(data: {
    nome: string;
    especialidade: string;
    crm: string;
    user_id?: string | null;
  }) {
    try {
      setIsSubmitting(true);
      if (selectedDoctor) {
        await apiFetch(`/api/doctors/${selectedDoctor.id}`, {
          method: "PUT",
          body: JSON.stringify(data),
        });
      } else {
        await apiFetch("/api/doctors", {
          method: "POST",
          body: JSON.stringify(data),
        });
      }
      setSlideOverOpen(false);
      setSelectedDoctor(null);
      await fetchDoctors();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar medico");
    } finally {
      setIsSubmitting(false);
    }
  }

  const columns = getDoctorColumns({
    onEdit: openEditDoctor,
    onSchedule: openScheduleGrid,
  });

  return (
    <div className="space-y-6">
      {/* Cabecalho da pagina */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-serif font-semibold text-gray-900">
            Medicos
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Gerencie o cadastro e disponibilidade dos medicos da clinica.
          </p>
        </div>
        <Button onClick={openNewDoctor}>Novo Medico</Button>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Tabela de medicos */}
      <DataTable
        columns={columns}
        data={doctors}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
      />

      {/* Slide-over: Criar/Editar medico */}
      <SlideOver
        open={slideOverOpen}
        onClose={() => {
          setSlideOverOpen(false);
          setSelectedDoctor(null);
        }}
        title={selectedDoctor ? "Editar Medico" : "Novo Medico"}
      >
        <DoctorForm
          doctor={selectedDoctor}
          medicUsers={medicUsers}
          onSubmit={handleFormSubmit}
          onCancel={() => {
            setSlideOverOpen(false);
            setSelectedDoctor(null);
          }}
          isSubmitting={isSubmitting}
        />
      </SlideOver>

      {/* Slide-over: Grade de horarios (mais largo) */}
      {scheduleDoctor && (
        <div
          className={`
            fixed inset-0 z-40 flex justify-end
            transition-opacity duration-200
            ${scheduleGridOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}
          `}
        >
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setScheduleGridOpen(false)}
          />
          {/* Painel */}
          <div
            className={`
              relative bg-white z-50 shadow-2xl h-full w-full max-w-2xl
              flex flex-col transition-transform duration-300 ease-in-out
              ${scheduleGridOpen ? "translate-x-0" : "translate-x-full"}
            `}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-green-600">
              <h2 className="font-serif text-lg font-semibold text-white">
                Horarios — {scheduleDoctor.nome}
              </h2>
              <button
                onClick={() => setScheduleGridOpen(false)}
                className="text-white hover:text-green-100 transition-colors rounded-md p-1"
                aria-label="Fechar"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <ScheduleGrid
                doctorId={scheduleDoctor.id}
                doctorNome={scheduleDoctor.nome}
                onClose={() => setScheduleGridOpen(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
