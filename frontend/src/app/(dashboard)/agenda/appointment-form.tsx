"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { apiFetch } from "@/lib/api";
import { StatusBadge } from "@/components/dashboard/StatusBadge";
import type { Appointment, Doctor, Patient } from "@/lib/types";

// ─── Validation schema ─────────────────────────────────────────────────────────

const appointmentSchema = z.object({
  patient_id: z.string().min(1, "Selecione um paciente"),
  doctor_id: z.string().min(1, "Selecione um medico"),
  data_agendamento: z.string().min(1, "Selecione a data"),
  horario: z.string().regex(/^\d{2}:\d{2}$/, "Formato invalido (HH:MM)"),
  especialidade: z.string().optional(),
});

type AppointmentFormData = z.infer<typeof appointmentSchema>;

interface AppointmentFormProps {
  appointment: Appointment | null;
  patients: Patient[];
  doctors: Doctor[];
  prefillDate?: string;
  prefillTime?: string;
  onSuccess: () => void;
  onCancel: () => void;
}

export function AppointmentForm({
  appointment,
  patients,
  doctors,
  prefillDate,
  prefillTime,
  onSuccess,
  onCancel,
}: AppointmentFormProps) {
  const isEdit = appointment !== null;
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Cancel confirmation state
  const [showCancelConfirm, setShowCancelConfirm] = React.useState(false);
  const [cancelMotivo, setCancelMotivo] = React.useState("");
  const [cancelling, setCancelling] = React.useState(false);

  // Status transition state
  const [transitioning, setTransitioning] = React.useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<AppointmentFormData>({
    resolver: zodResolver(appointmentSchema),
    defaultValues: {
      patient_id: appointment?.patient_id ?? "",
      doctor_id: appointment?.doctor_id ?? "",
      data_agendamento: appointment?.data_agendamento ?? prefillDate ?? "",
      horario: appointment?.horario ?? prefillTime ?? "",
      especialidade: appointment?.especialidade ?? "",
    },
  });

  const watchedDoctorId = watch("doctor_id");

  // Auto-fill especialidade when doctor changes
  React.useEffect(() => {
    const doc = doctors.find((d) => d.id === watchedDoctorId);
    if (doc) setValue("especialidade", doc.especialidade);
  }, [watchedDoctorId, doctors, setValue]);

  async function onSubmit(data: AppointmentFormData) {
    setSubmitting(true);
    setError(null);
    try {
      if (isEdit && appointment) {
        await apiFetch(`/api/appointments/${appointment.id}`, {
          method: "PUT",
          body: JSON.stringify({
            doctor_id: data.doctor_id,
            data_agendamento: data.data_agendamento,
            horario_agendamento: data.horario,
            especialidade: data.especialidade ?? "",
          }),
        });
      } else {
        await apiFetch("/api/appointments", {
          method: "POST",
          body: JSON.stringify({
            patient_id: data.patient_id,
            doctor_id: data.doctor_id,
            data_agendamento: data.data_agendamento,
            horario_agendamento: data.horario,
            especialidade: data.especialidade ?? "",
          }),
        });
      }
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel() {
    if (!appointment) return;
    setCancelling(true);
    setError(null);
    try {
      await apiFetch(`/api/appointments/${appointment.id}/cancel`, {
        method: "PATCH",
        body: JSON.stringify({ motivo_cancelamento: cancelMotivo || null }),
      });
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao cancelar");
      setCancelling(false);
    }
  }

  async function handleStatusChange(newStatus: string) {
    if (!appointment) return;
    setTransitioning(true);
    setError(null);
    try {
      await apiFetch(`/api/appointments/${appointment.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar status");
      setTransitioning(false);
    }
  }

  // ─── Cancel confirmation dialog ──────────────────────────────────────────────
  if (showCancelConfirm) {
    return (
      <div className="flex flex-col gap-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm font-medium text-red-800 mb-1">
            Cancelar consulta?
          </p>
          <p className="text-xs text-red-600">Esta acao nao pode ser desfeita.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Motivo do cancelamento (opcional)
          </label>
          <textarea
            value={cancelMotivo}
            onChange={(e) => setCancelMotivo(e.target.value)}
            rows={3}
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="Informe o motivo..."
          />
        </div>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleCancel}
            disabled={cancelling}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50"
          >
            {cancelling ? "Cancelando..." : "Confirmar cancelamento"}
          </button>
          <button
            type="button"
            onClick={() => setShowCancelConfirm(false)}
            className="flex-1 border border-gray-200 text-gray-700 text-sm font-medium py-2 px-4 rounded-md hover:bg-gray-50 transition-colors"
          >
            Voltar
          </button>
        </div>
      </div>
    );
  }

  // ─── Main form ────────────────────────────────────────────────────────────────
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      {/* Current status display (edit mode) */}
      {isEdit && appointment && (
        <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
          <span className="text-sm text-gray-600">Status atual:</span>
          <StatusBadge status={appointment.status} />
        </div>
      )}

      {/* Patient select */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Paciente <span className="text-red-500">*</span>
        </label>
        {isEdit ? (
          <div className="text-sm text-gray-800 py-2 px-3 bg-gray-50 rounded-md border border-gray-200">
            {appointment?.patient_nome}
          </div>
        ) : (
          <select
            {...register("patient_id")}
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
          >
            <option value="">Selecione um paciente...</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nome} — {p.phone}
              </option>
            ))}
          </select>
        )}
        {errors.patient_id && (
          <p className="text-xs text-red-600 mt-1">{errors.patient_id.message}</p>
        )}
      </div>

      {/* Doctor select */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Medico <span className="text-red-500">*</span>
        </label>
        <select
          {...register("doctor_id")}
          className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
        >
          <option value="">Selecione um medico...</option>
          {doctors.map((d) => (
            <option key={d.id} value={d.id}>
              {d.nome} — {d.especialidade}
            </option>
          ))}
        </select>
        {errors.doctor_id && (
          <p className="text-xs text-red-600 mt-1">{errors.doctor_id.message}</p>
        )}
      </div>

      {/* Especialidade (auto-filled, read-only) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Especialidade
        </label>
        <input
          type="text"
          {...register("especialidade")}
          readOnly
          className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm bg-gray-50 text-gray-600"
          placeholder="Preenchida automaticamente"
        />
      </div>

      {/* Date */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Data <span className="text-red-500">*</span>
        </label>
        <input
          type="date"
          {...register("data_agendamento")}
          min={new Date().toISOString().split("T")[0]}
          className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        {errors.data_agendamento && (
          <p className="text-xs text-red-600 mt-1">{errors.data_agendamento.message}</p>
        )}
      </div>

      {/* Time */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Horario <span className="text-red-500">*</span>
        </label>
        <input
          type="time"
          {...register("horario")}
          className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        {errors.horario && (
          <p className="text-xs text-red-600 mt-1">{errors.horario.message}</p>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      {/* Action buttons */}
      <div className="flex flex-col gap-2 pt-2">
        <button
          type="submit"
          disabled={submitting || appointment?.status === "cancelado"}
          className="w-full bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50"
        >
          {submitting ? "Salvando..." : isEdit ? "Salvar alteracoes" : "Agendar"}
        </button>

        {/* Status transition buttons (edit mode) */}
        {isEdit && appointment && (
          <>
            {appointment.status === "agendado" && (
              <button
                type="button"
                onClick={() => handleStatusChange("confirmado")}
                disabled={transitioning}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50"
              >
                {transitioning ? "..." : "Confirmar consulta"}
              </button>
            )}
            {appointment.status === "confirmado" && (
              <button
                type="button"
                onClick={() => handleStatusChange("realizado")}
                disabled={transitioning}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50"
              >
                {transitioning ? "..." : "Marcar como realizado"}
              </button>
            )}

            {/* Cancel button (show if not already cancelled) */}
            {appointment.status !== "cancelado" && (
              <button
                type="button"
                onClick={() => setShowCancelConfirm(true)}
                className="w-full border border-red-300 text-red-600 hover:bg-red-50 text-sm font-medium py-2 px-4 rounded-md transition-colors"
              >
                Cancelar consulta
              </button>
            )}
          </>
        )}

        <button
          type="button"
          onClick={onCancel}
          className="w-full border border-gray-200 text-gray-700 text-sm font-medium py-2 px-4 rounded-md hover:bg-gray-50 transition-colors"
        >
          Fechar
        </button>
      </div>
    </form>
  );
}
