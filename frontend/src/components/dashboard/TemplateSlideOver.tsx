"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { SlideOver } from "@/components/dashboard/SlideOver";
import { apiFetch } from "@/lib/api";
import type { MessageTemplate } from "@/lib/types";

// ─── Schema de validacao ──────────────────────────────────────────────────────

const templateSchema = z.object({
  nome: z.string().min(1, "Nome e obrigatorio"),
  corpo: z.string().min(1, "Corpo da mensagem e obrigatorio"),
});

type TemplateFormData = z.infer<typeof templateSchema>;

// ─── Dados de amostra para preview ───────────────────────────────────────────

const SAMPLE_DATA: Record<string, string> = {
  nome: "Maria Silva",
  telefone: "11999990000",
  data: "01/04/2026",
  hora: "09:30",
  medico: "Dr. Carlos",
  especialidade: "Cardiologia",
};

function previewTemplate(body: string): string {
  return body.replace(/\{\{(\w+)\}\}/g, (_, key) => SAMPLE_DATA[key] ?? `{{${key}}}`);
}

// ─── Variaveis permitidas ─────────────────────────────────────────────────────

const ALLOWED_VARS = [
  "{{nome}}",
  "{{telefone}}",
  "{{data}}",
  "{{hora}}",
  "{{medico}}",
  "{{especialidade}}",
] as const;

// ─── Props ────────────────────────────────────────────────────────────────────

interface TemplateSlideOverProps {
  open: boolean;
  onClose: () => void;
  template: MessageTemplate | null; // null = modo criar, nao-null = modo editar
  onSaved: () => void; // callback para atualizar lista apos salvar
}

// ─── Componente ───────────────────────────────────────────────────────────────

export function TemplateSlideOver({
  open,
  onClose,
  template,
  onSaved,
}: TemplateSlideOverProps) {
  const isEditing = template !== null;

  const textareaRef = React.useRef<HTMLTextAreaElement>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<TemplateFormData>({
    resolver: zodResolver(templateSchema),
    defaultValues: {
      nome: template?.nome ?? "",
      corpo: template?.corpo ?? "",
    },
  });

  // Atualiza valores do formulario quando template mudar (abrir editar)
  React.useEffect(() => {
    reset({
      nome: template?.nome ?? "",
      corpo: template?.corpo ?? "",
    });
    setSubmitError(null);
  }, [template, reset]);

  const corpoValue = watch("corpo");

  // ─── Insercao de variavel na posicao do cursor ────────────────────────────────

  const insertVariable = (variable: string) => {
    const textarea = textareaRef.current;
    if (!textarea) {
      // Fallback: appende ao final
      setValue("corpo", corpoValue + variable, { shouldValidate: true });
      return;
    }

    const start = textarea.selectionStart ?? corpoValue.length;
    const end = textarea.selectionEnd ?? corpoValue.length;
    const newValue =
      corpoValue.slice(0, start) + variable + corpoValue.slice(end);

    setValue("corpo", newValue, { shouldValidate: true });

    // Restaura cursor apos a variavel inserida
    requestAnimationFrame(() => {
      if (textarea) {
        const cursorPos = start + variable.length;
        textarea.setSelectionRange(cursorPos, cursorPos);
        textarea.focus();
      }
    });
  };

  // ─── Submit ───────────────────────────────────────────────────────────────────

  const onSubmit = async (data: TemplateFormData) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      if (isEditing && template) {
        await apiFetch<MessageTemplate>(`/api/templates/${template.id}`, {
          method: "PUT",
          body: JSON.stringify({ nome: data.nome, corpo: data.corpo }),
        });
      } else {
        await apiFetch<MessageTemplate>("/api/templates", {
          method: "POST",
          body: JSON.stringify({ nome: data.nome, corpo: data.corpo }),
        });
      }
      onSaved();
      onClose();
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : "Erro ao salvar template"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // ─── Render ───────────────────────────────────────────────────────────────────

  return (
    <SlideOver
      open={open}
      onClose={onClose}
      title={isEditing ? "Editar Template" : "Novo Template"}
    >
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="flex flex-col gap-6"
        noValidate
      >
        {/* Nome do template */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="template-nome"
            className="text-sm font-medium text-gray-700"
          >
            Nome do Template
          </label>
          <input
            id="template-nome"
            type="text"
            {...register("nome")}
            placeholder="Ex: Confirmacao de Consulta"
            className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-shadow"
          />
          {errors.nome && (
            <p className="text-xs text-red-600">{errors.nome.message}</p>
          )}
        </div>

        {/* Corpo da mensagem */}
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="template-corpo"
            className="text-sm font-medium text-gray-700"
          >
            Corpo da Mensagem
          </label>
          <textarea
            id="template-corpo"
            {...register("corpo")}
            ref={(el) => {
              // Compatibilidade com react-hook-form ref e nosso ref local
              (register("corpo") as any).ref?.(el);
              (textareaRef as React.MutableRefObject<HTMLTextAreaElement | null>).current = el;
            }}
            rows={5}
            placeholder="Digite a mensagem. Use {{nome}}, {{data}}, etc."
            className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-shadow resize-none"
          />
          {errors.corpo && (
            <p className="text-xs text-red-600">{errors.corpo.message}</p>
          )}
        </div>

        {/* Botoes de insercao de variaveis (D-09) */}
        <div className="flex flex-col gap-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Inserir variavel
          </p>
          <div className="flex flex-wrap gap-2">
            {ALLOWED_VARS.map((variable) => (
              <button
                key={variable}
                type="button"
                onClick={() => insertVariable(variable)}
                className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-gray-100 text-gray-700 hover:bg-green-100 hover:text-green-800 transition-colors border border-gray-200"
              >
                {variable}
              </button>
            ))}
          </div>
        </div>

        {/* Pre-visualizacao (D-08) */}
        <div className="flex flex-col gap-2">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Pre-visualizacao
          </p>
          <div className="rounded-md border border-gray-200 bg-gray-50 p-4 min-h-[80px]">
            {corpoValue ? (
              <p className="text-sm text-gray-800" style={{ whiteSpace: "pre-wrap" }}>
                {previewTemplate(corpoValue)}
              </p>
            ) : (
              <p className="text-sm text-gray-400 italic">
                O preview aparecera aqui conforme voce digitar.
              </p>
            )}
          </div>
        </div>

        {/* Erro de submit */}
        {submitError && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {submitError}
          </div>
        )}

        {/* Acoes */}
        <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? "Salvando..." : isEditing ? "Salvar" : "Criar"}
          </button>
        </div>
      </form>
    </SlideOver>
  );
}
