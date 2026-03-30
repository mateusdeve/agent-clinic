"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Doctor, SystemUser } from "@/lib/types";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";

const ESPECIALIDADES = [
  "Clinico Geral",
  "Cardiologia",
  "Dermatologia",
  "Ortopedia",
  "Pediatria",
  "Ginecologia",
  "Neurologia",
  "Oftalmologia",
  "Otorrinolaringologia",
  "Psiquiatria",
] as const;

const doctorSchema = z.object({
  nome: z.string().min(1, "Nome e obrigatorio"),
  especialidade: z.string().min(1, "Especialidade e obrigatoria"),
  crm: z.string().min(1, "CRM e obrigatorio"),
  user_id: z.string().nullable().optional(),
});

type DoctorFormValues = z.infer<typeof doctorSchema>;

interface DoctorFormProps {
  doctor: Doctor | null;
  medicUsers: SystemUser[];
  onSubmit: (data: DoctorFormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function DoctorForm({
  doctor,
  medicUsers,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: DoctorFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<DoctorFormValues>({
    resolver: zodResolver(doctorSchema),
    defaultValues: {
      nome: doctor?.nome ?? "",
      especialidade: doctor?.especialidade ?? "",
      crm: doctor?.crm ?? "",
      user_id: doctor?.user_id ?? null,
    },
  });

  const especialidadeValue = watch("especialidade");
  const userIdValue = watch("user_id");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Nome */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Nome <span className="text-red-500">*</span>
        </label>
        <Input {...register("nome")} placeholder="Dr. Joao da Silva" />
        {errors.nome && (
          <p className="text-xs text-red-500">{errors.nome.message}</p>
        )}
      </div>

      {/* Especialidade */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Especialidade <span className="text-red-500">*</span>
        </label>
        <Select
          value={especialidadeValue}
          onValueChange={(val) => setValue("especialidade", val)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Selecione ou digite a especialidade" />
          </SelectTrigger>
          <SelectContent>
            {ESPECIALIDADES.map((esp) => (
              <SelectItem key={esp} value={esp}>
                {esp}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {/* Fallback: free text entry for other specialties */}
        <Input
          {...register("especialidade")}
          placeholder="Ou digite outra especialidade"
          className="mt-1"
        />
        {errors.especialidade && (
          <p className="text-xs text-red-500">{errors.especialidade.message}</p>
        )}
      </div>

      {/* CRM */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          CRM <span className="text-red-500">*</span>
        </label>
        <Input {...register("crm")} placeholder="CRM/SP 123456" />
        {errors.crm && (
          <p className="text-xs text-red-500">{errors.crm.message}</p>
        )}
      </div>

      {/* Vincular usuario medico */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Vincular a usuario (opcional)
        </label>
        <Select
          value={userIdValue ?? "__none__"}
          onValueChange={(val) =>
            setValue("user_id", val === "__none__" ? null : val)
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Nenhum usuario vinculado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__none__">Nenhum</SelectItem>
            {medicUsers.map((u) => (
              <SelectItem key={u.id} value={u.id}>
                {u.name} ({u.email})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-gray-400">
          Vincula perfil do medico a um usuario com acesso ao sistema.
        </p>
      </div>

      {/* Acoes */}
      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting
            ? "Salvando..."
            : doctor
            ? "Salvar"
            : "Cadastrar"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancelar
        </Button>
      </div>
    </form>
  );
}
