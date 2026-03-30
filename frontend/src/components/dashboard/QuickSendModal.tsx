"use client";

import * as React from "react";
import { X } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { MessageTemplate } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface QuickSendModalProps {
  open: boolean;
  onClose: () => void;
  phone: string;
  patientNome: string;
}

export function QuickSendModal({ open, onClose, phone, patientNome }: QuickSendModalProps) {
  const [templates, setTemplates] = React.useState<MessageTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = React.useState<MessageTemplate | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isSending, setIsSending] = React.useState(false);
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Fecha com Escape
  React.useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) handleClose();
    };
    document.addEventListener("keydown", handle);
    return () => document.removeEventListener("keydown", handle);
  }, [open]);

  // Carrega templates ao abrir
  React.useEffect(() => {
    if (!open) return;
    setIsLoading(true);
    apiFetch<{ items: MessageTemplate[] }>("/api/templates?per_page=50")
      .then((res) => setTemplates(res.items))
      .catch(() => setTemplates([]))
      .finally(() => setIsLoading(false));
  }, [open]);

  function handleClose() {
    setSelectedTemplate(null);
    setSuccess(false);
    setError(null);
    onClose();
  }

  async function handleSend() {
    if (!selectedTemplate) return;
    setIsSending(true);
    setError(null);
    try {
      await apiFetch(`/api/conversations/${phone}/send-template`, {
        method: "POST",
        body: JSON.stringify({
          template_id: selectedTemplate.id,
          variaveis: { nome: patientNome, telefone: phone },
        }),
      });
      setSuccess(true);
      setTimeout(handleClose, 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao enviar mensagem");
    } finally {
      setIsSending(false);
    }
  }

  // Preview da mensagem com substituicao simples de variaveis
  const preview = React.useMemo(() => {
    if (!selectedTemplate) return "";
    return selectedTemplate.corpo
      .replace(/\{\{nome\}\}/gi, patientNome)
      .replace(/\{\{telefone\}\}/gi, phone);
  }, [selectedTemplate, patientNome, phone]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        aria-hidden="true"
        onClick={handleClose}
        className="fixed inset-0 bg-black/40 z-40"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Enviar Template para ${patientNome}`}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90vh]">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-green-600 rounded-t-xl">
            <h2 className="font-serif text-lg font-semibold text-white truncate">
              Enviar Template para {patientNome}
            </h2>
            <button
              onClick={handleClose}
              aria-label="Fechar modal"
              className="text-white hover:text-green-100 transition-colors rounded-md p-1 focus:outline-none focus:ring-2 focus:ring-white/50 shrink-0"
            >
              <X className="size-5" />
            </button>
          </div>

          {/* Corpo */}
          <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
            {success ? (
              <div className="flex flex-col items-center gap-3 py-6">
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <span className="text-green-600 text-2xl">✓</span>
                </div>
                <p className="text-base font-semibold text-green-700">Mensagem enviada!</p>
              </div>
            ) : (
              <>
                {/* Lista de templates */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    Selecione um template
                  </p>
                  {isLoading ? (
                    <p className="text-sm text-gray-400">Carregando templates...</p>
                  ) : templates.length === 0 ? (
                    <p className="text-sm text-gray-400">Nenhum template disponivel.</p>
                  ) : (
                    <div className="flex flex-col gap-2 max-h-48 overflow-y-auto">
                      {templates.map((t) => (
                        <button
                          key={t.id}
                          type="button"
                          onClick={() => setSelectedTemplate(t)}
                          className={cn(
                            "text-left rounded-lg border p-3 transition-colors",
                            selectedTemplate?.id === t.id
                              ? "border-green-500 bg-green-50"
                              : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                          )}
                        >
                          <p className="text-sm font-medium text-gray-800">{t.nome}</p>
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                            {t.corpo.slice(0, 80)}{t.corpo.length > 80 ? "..." : ""}
                          </p>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Preview */}
                {selectedTemplate && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">
                      Pre-visualizacao
                    </p>
                    <div className="rounded-md bg-gray-50 border border-gray-200 p-3 text-sm text-gray-700 whitespace-pre-line">
                      {preview}
                    </div>
                  </div>
                )}

                {/* Erro */}
                {error && (
                  <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-600">
                    {error}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer */}
          {!success && (
            <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-gray-200">
              <Button variant="outline" onClick={handleClose} disabled={isSending}>
                Cancelar
              </Button>
              <Button
                onClick={handleSend}
                disabled={!selectedTemplate || isSending}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {isSending ? "Enviando..." : "Enviar"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
