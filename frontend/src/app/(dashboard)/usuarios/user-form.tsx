"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { SystemUser } from "@/lib/types";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";

const createSchema = z.object({
  name: z.string().min(1, "Nome e obrigatorio"),
  email: z.string().email("Email invalido"),
  password: z.string().min(6, "Senha deve ter ao menos 6 caracteres"),
  role: z.enum(["admin", "recepcionista", "medico"] as const),
});

const editSchema = z.object({
  role: z.enum(["admin", "recepcionista", "medico"] as const),
});

type CreateFormValues = z.infer<typeof createSchema>;
type EditFormValues = z.infer<typeof editSchema>;

const ROLE_OPTIONS: { value: SystemUser["role"]; label: string }[] = [
  { value: "admin", label: "Admin" },
  { value: "recepcionista", label: "Recepcionista" },
  { value: "medico", label: "Medico" },
];

interface UserFormProps {
  user: SystemUser | null;
  mode: "create" | "edit";
  onSubmit: (data: CreateFormValues | EditFormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function UserForm({
  user,
  mode,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: UserFormProps) {
  if (mode === "create") {
    return (
      <CreateForm
        onSubmit={onSubmit as (data: CreateFormValues) => Promise<void>}
        onCancel={onCancel}
        isSubmitting={isSubmitting}
      />
    );
  }

  return (
    <EditForm
      user={user!}
      onSubmit={onSubmit as (data: EditFormValues) => Promise<void>}
      onCancel={onCancel}
      isSubmitting={isSubmitting}
    />
  );
}

function CreateForm({
  onSubmit,
  onCancel,
  isSubmitting,
}: {
  onSubmit: (data: CreateFormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CreateFormValues>({
    resolver: zodResolver(createSchema),
    defaultValues: { role: "recepcionista" },
  });

  const roleValue = watch("role");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Nome <span className="text-red-500">*</span>
        </label>
        <Input {...register("name")} placeholder="Maria da Silva" />
        {errors.name && (
          <p className="text-xs text-red-500">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Email <span className="text-red-500">*</span>
        </label>
        <Input {...register("email")} type="email" placeholder="maria@clinica.com" />
        {errors.email && (
          <p className="text-xs text-red-500">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Senha <span className="text-red-500">*</span>
        </label>
        <Input {...register("password")} type="password" placeholder="Minimo 6 caracteres" />
        {errors.password && (
          <p className="text-xs text-red-500">{errors.password.message}</p>
        )}
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Perfil <span className="text-red-500">*</span>
        </label>
        <Select
          value={roleValue}
          onValueChange={(val) => setValue("role", val as SystemUser["role"])}
        >
          <SelectTrigger>
            <SelectValue placeholder="Selecione o perfil" />
          </SelectTrigger>
          <SelectContent>
            {ROLE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.role && (
          <p className="text-xs text-red-500">{errors.role.message}</p>
        )}
      </div>

      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting ? "Criando..." : "Criar Usuario"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}

function EditForm({
  user,
  onSubmit,
  onCancel,
  isSubmitting,
}: {
  user: SystemUser;
  onSubmit: (data: EditFormValues) => Promise<void>;
  onCancel: () => void;
  isSubmitting: boolean;
}) {
  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
    defaultValues: { role: user.role },
  });

  const roleValue = watch("role");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Nome (somente leitura) */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">Nome</label>
        <div className="px-3 py-2 rounded-md border border-gray-200 bg-gray-50 text-sm text-gray-600">
          {user.name}
        </div>
      </div>

      {/* Email (somente leitura) */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">Email</label>
        <div className="px-3 py-2 rounded-md border border-gray-200 bg-gray-50 text-sm text-gray-600">
          {user.email}
        </div>
      </div>

      {/* Perfil (editavel) */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Perfil <span className="text-red-500">*</span>
        </label>
        <Select
          value={roleValue}
          onValueChange={(val) => setValue("role", val as SystemUser["role"])}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {ROLE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.role && (
          <p className="text-xs text-red-500">{errors.role.message}</p>
        )}
      </div>

      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting ? "Salvando..." : "Salvar"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
