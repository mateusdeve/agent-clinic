"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Input } from "@/components/ui/input";
import type { Patient } from "@/lib/types";

// ─── Schema de validacao ───────────────────────────────────────────────────────

const patientSchema = z.object({
  nome: z
    .string()
    .min(2, "Nome deve ter pelo menos 2 caracteres")
    .max(120, "Nome muito longo"),
  phone: z
    .string()
    .regex(/^\d{10,11}$/, "Telefone deve ter 10 ou 11 digitos (somente numeros)"),
  data_nascimento: z.string().optional(),
  notas: z.string().optional(),
});

export type PatientFormData = z.infer<typeof patientSchema>;

// ─── Props ─────────────────────────────────────────────────────────────────────

interface PatientFormProps {
  patient: Patient | null; // null = criar novo
  onSubmit: (data: PatientFormData) => Promise<void>;
  onCancel: () => void;
}

// ─── Componente ───────────────────────────────────────────────────────────────

export function PatientForm({ patient, onSubmit, onCancel }: PatientFormProps) {
  const isEdit = patient !== null;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      nome: patient?.nome ?? "",
      phone: patient?.phone ?? "",
      data_nascimento: patient?.data_nascimento ?? "",
      notas: patient?.notas ?? "",
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      {/* Nome */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-gray-700" htmlFor="pf-nome">
          Nome completo <span className="text-red-500">*</span>
        </label>
        <Input
          id="pf-nome"
          placeholder="Ex: Maria Silva"
          {...register("nome")}
        />
        {errors.nome && (
          <p className="text-xs text-red-500">{errors.nome.message}</p>
        )}
      </div>

      {/* Telefone */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-gray-700" htmlFor="pf-phone">
          Telefone (WhatsApp) <span className="text-red-500">*</span>
        </label>
        <Input
          id="pf-phone"
          placeholder="Ex: 11987654321"
          inputMode="tel"
          {...register("phone")}
        />
        {errors.phone && (
          <p className="text-xs text-red-500">{errors.phone.message}</p>
        )}
      </div>

      {/* Data de nascimento */}
      <div className="flex flex-col gap-1.5">
        <label
          className="text-sm font-medium text-gray-700"
          htmlFor="pf-data-nascimento"
        >
          Data de nascimento
        </label>
        <Input
          id="pf-data-nascimento"
          type="date"
          {...register("data_nascimento")}
        />
        {errors.data_nascimento && (
          <p className="text-xs text-red-500">
            {errors.data_nascimento.message}
          </p>
        )}
      </div>

      {/* Notas */}
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-gray-700" htmlFor="pf-notas">
          Notas
        </label>
        <textarea
          id="pf-notas"
          rows={3}
          placeholder="Observacoes sobre o paciente..."
          className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
          {...register("notas")}
        />
        {errors.notas && (
          <p className="text-xs text-red-500">{errors.notas.message}</p>
        )}
      </div>

      {/* Acoes */}
      <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-100">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {isSubmitting && (
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          )}
          {isEdit ? "Salvar" : "Cadastrar"}
        </button>
      </div>
    </form>
  );
}
