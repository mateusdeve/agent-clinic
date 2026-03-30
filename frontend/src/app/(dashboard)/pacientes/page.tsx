"use client";

import * as React from "react";
import { PaginationState } from "@tanstack/react-table";
import { Plus } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { Patient, PaginatedResponse } from "@/lib/types";
import { DataTable } from "@/components/dashboard/DataTable";
import { SlideOver } from "@/components/dashboard/SlideOver";
import { buildPatientColumns } from "./columns";
import { PatientForm, type PatientFormData } from "./patient-form";

// ─── Debounce hook ─────────────────────────────────────────────────────────────

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = React.useState<T>(value);
  React.useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

// ─── Pagina ────────────────────────────────────────────────────────────────────

export default function PacientesPage() {
  // Dados
  const [patients, setPatients] = React.useState<Patient[]>([]);
  const [total, setTotal] = React.useState(0);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Paginacao
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize: 20,
  });

  // Busca
  const [searchInput, setSearchInput] = React.useState("");
  const searchQuery = useDebounce(searchInput, 300);

  // Slide-over
  const [slideOverOpen, setSlideOverOpen] = React.useState(false);
  const [selectedPatient, setSelectedPatient] =
    React.useState<Patient | null>(null);

  // ─── Fetch ────────────────────────────────────────────────────────────────────

  const fetchPatients = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const effectiveQuery =
        searchQuery.length >= 2 ? searchQuery : "";
      const params = new URLSearchParams({
        page: String(pagination.pageIndex + 1),
        per_page: String(pagination.pageSize),
        ...(effectiveQuery ? { search: effectiveQuery } : {}),
      });
      const data = await apiFetch<PaginatedResponse<Patient>>(
        `/api/patients?${params.toString()}`
      );
      setPatients(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar pacientes");
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, pagination.pageIndex, pagination.pageSize]);

  // Refetch quando busca ou paginacao mudar
  React.useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  // Resetar para pagina 0 ao mudar busca
  React.useEffect(() => {
    setPagination((prev) => ({ ...prev, pageIndex: 0 }));
  }, [searchQuery]);

  // ─── Acoes de formulario ──────────────────────────────────────────────────────

  const openCreate = () => {
    setSelectedPatient(null);
    setSlideOverOpen(true);
  };

  const openEdit = (patient: Patient) => {
    setSelectedPatient(patient);
    setSlideOverOpen(true);
  };

  const closeSlideOver = () => {
    setSlideOverOpen(false);
    setSelectedPatient(null);
  };

  const handleFormSubmit = async (formData: PatientFormData) => {
    if (selectedPatient) {
      // Editar paciente existente
      await apiFetch(`/api/patients/${selectedPatient.id}`, {
        method: "PUT",
        body: JSON.stringify(formData),
      });
    } else {
      // Criar novo paciente
      await apiFetch("/api/patients", {
        method: "POST",
        body: JSON.stringify(formData),
      });
    }
    closeSlideOver();
    fetchPatients();
  };

  // ─── Colunas com callbacks ────────────────────────────────────────────────────

  const columns = React.useMemo(
    () => buildPatientColumns({ onEdit: openEdit }),
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
            Pacientes
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Gerencie os pacientes da clinica
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors"
        >
          <Plus className="size-4" />
          Novo Paciente
        </button>
      </div>

      {/* Barra de busca */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Buscar por nome ou telefone..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex h-10 w-full max-w-sm rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-shadow"
        />
        {searchInput.length > 0 && searchInput.length < 2 && (
          <p className="text-xs text-gray-400">Digite pelo menos 2 caracteres</p>
        )}
      </div>

      {/* Erro */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Tabela */}
      <DataTable
        columns={columns}
        data={patients}
        pageCount={pageCount}
        pagination={pagination}
        onPaginationChange={setPagination}
        isLoading={isLoading}
      />

      {/* Slide-over criar/editar */}
      <SlideOver
        open={slideOverOpen}
        onClose={closeSlideOver}
        title={selectedPatient ? "Editar Paciente" : "Novo Paciente"}
      >
        <PatientForm
          patient={selectedPatient}
          onSubmit={handleFormSubmit}
          onCancel={closeSlideOver}
        />
      </SlideOver>
    </div>
  );
}
