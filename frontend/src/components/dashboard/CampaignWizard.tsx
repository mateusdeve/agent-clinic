"use client";

import * as React from "react";
import { apiFetch } from "@/lib/api";
import type { MessageTemplate, SegmentPreview } from "@/lib/types";
import { SlideOver } from "./SlideOver";
import { Button } from "@/components/ui/button";

// ─── Tipos ────────────────────────────────────────────────────────────────────

type WizardStep = "template" | "segmento" | "preview" | "confirmar";

interface WizardFilters {
  especialidade?: string;
  ultimo_agendamento_range?: string;
  status_paciente?: string;
}

interface CampaignWizardProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

// ─── Constantes ───────────────────────────────────────────────────────────────

const ESPECIALIDADES = [
  "Todas",
  "Cardiologia",
  "Dermatologia",
  "Ortopedia",
  "Ginecologia",
  "Pediatria",
  "Neurologia",
  "Oftalmologia",
  "Psiquiatria",
  "Endocrinologia",
];

const AGENDAMENTO_RANGES = [
  { value: "", label: "Todos" },
  { value: "30d", label: "Menos de 30 dias" },
  { value: "30_90d", label: "30 a 90 dias" },
  { value: "90d+", label: "Mais de 90 dias" },
];

const STATUS_PACIENTE_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "ativo", label: "Ativo" },
  { value: "inativo", label: "Inativo" },
];

// ─── Titulos por etapa ────────────────────────────────────────────────────────

const STEP_TITLES: Record<WizardStep, string> = {
  template: "Nova Campanha — Template",
  segmento: "Nova Campanha — Segmento",
  preview: "Nova Campanha — Pre-visualizacao",
  confirmar: "Nova Campanha — Confirmacao",
};

// ─── Componente principal ─────────────────────────────────────────────────────

export function CampaignWizard({ open, onClose, onCreated }: CampaignWizardProps) {
  const [step, setStep] = React.useState<WizardStep>("template");
  const [nome, setNome] = React.useState("");
  const [templateId, setTemplateId] = React.useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = React.useState<MessageTemplate | null>(null);
  const [filters, setFilters] = React.useState<WizardFilters>({});
  const [segmentPreview, setSegmentPreview] = React.useState<SegmentPreview | null>(null);
  const [templates, setTemplates] = React.useState<MessageTemplate[]>([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = React.useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState(false);

  // Carrega templates ao abrir
  React.useEffect(() => {
    if (!open) return;
    setIsLoadingTemplates(true);
    apiFetch<{ items: MessageTemplate[] }>("/api/templates?per_page=100")
      .then((res) => setTemplates(res.items))
      .catch(() => setTemplates([]))
      .finally(() => setIsLoadingTemplates(false));
  }, [open]);

  // Debounce: busca preview-segment ao mudar filtros
  React.useEffect(() => {
    if (step !== "segmento") return;
    const timer = setTimeout(() => {
      setIsLoadingPreview(true);
      const params = new URLSearchParams();
      if (filters.especialidade && filters.especialidade !== "Todas") {
        params.set("especialidade", filters.especialidade);
      }
      if (filters.ultimo_agendamento_range) {
        params.set("ultimo_agendamento_range", filters.ultimo_agendamento_range);
      }
      if (filters.status_paciente) {
        params.set("status_paciente", filters.status_paciente);
      }
      apiFetch<SegmentPreview>(`/api/campaigns/preview-segment?${params.toString()}`)
        .then(setSegmentPreview)
        .catch(() => setSegmentPreview(null))
        .finally(() => setIsLoadingPreview(false));
    }, 500);
    return () => clearTimeout(timer);
  }, [filters, step]);

  // Reset ao fechar
  function handleClose() {
    setStep("template");
    setNome("");
    setTemplateId(null);
    setSelectedTemplate(null);
    setFilters({});
    setSegmentPreview(null);
    setError(null);
    setSuccess(false);
    onClose();
  }

  async function handleSubmit() {
    if (!templateId || !nome) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const filtrosSanitizados: Record<string, string> = {};
      if (filters.especialidade && filters.especialidade !== "Todas") {
        filtrosSanitizados.especialidade = filters.especialidade;
      }
      if (filters.ultimo_agendamento_range) {
        filtrosSanitizados.ultimo_agendamento_range = filters.ultimo_agendamento_range;
      }
      if (filters.status_paciente) {
        filtrosSanitizados.status_paciente = filters.status_paciente;
      }
      await apiFetch("/api/campaigns", {
        method: "POST",
        body: JSON.stringify({ nome, template_id: templateId, filtros: filtrosSanitizados }),
      });
      setSuccess(true);
      onCreated();
      setTimeout(handleClose, 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao criar campanha");
    } finally {
      setIsSubmitting(false);
    }
  }

  const canGoNext = (): boolean => {
    if (step === "template") return !!templateId && nome.trim().length > 0;
    if (step === "segmento") return true;
    if (step === "preview") return true;
    return false;
  };

  function nextStep() {
    if (step === "template") setStep("segmento");
    else if (step === "segmento") setStep("preview");
    else if (step === "preview") setStep("confirmar");
  }

  function prevStep() {
    if (step === "segmento") setStep("template");
    else if (step === "preview") setStep("segmento");
    else if (step === "confirmar") setStep("preview");
  }

  return (
    <SlideOver open={open} onClose={handleClose} title={STEP_TITLES[step]}>
      <div className="flex flex-col gap-6">

        {/* ── Indicador de progresso ── */}
        <StepIndicator current={step} />

        {/* ── Etapa 1: Template ── */}
        {step === "template" && (
          <StepTemplate
            nome={nome}
            onNomeChange={setNome}
            templates={templates}
            isLoading={isLoadingTemplates}
            selectedId={templateId}
            onSelect={(t) => {
              setTemplateId(t.id);
              setSelectedTemplate(t);
            }}
          />
        )}

        {/* ── Etapa 2: Segmento ── */}
        {step === "segmento" && (
          <StepSegmento
            filters={filters}
            onFiltersChange={setFilters}
            preview={segmentPreview}
            isLoadingPreview={isLoadingPreview}
          />
        )}

        {/* ── Etapa 3: Preview ── */}
        {step === "preview" && (
          <StepPreview
            nome={nome}
            template={selectedTemplate}
            filters={filters}
            preview={segmentPreview}
          />
        )}

        {/* ── Etapa 4: Confirmar ── */}
        {step === "confirmar" && (
          <StepConfirmar
            success={success}
            error={error}
            isSubmitting={isSubmitting}
            onSubmit={handleSubmit}
          />
        )}

        {/* ── Navegacao ── */}
        {!success && (
          <div className="flex justify-between pt-4 border-t border-gray-100">
            {step !== "template" ? (
              <Button variant="outline" onClick={prevStep} disabled={isSubmitting}>
                Voltar
              </Button>
            ) : (
              <div />
            )}
            {step !== "confirmar" ? (
              <Button
                onClick={nextStep}
                disabled={!canGoNext()}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                Proximo
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {isSubmitting ? "Criando..." : "Confirmar e Enviar"}
              </Button>
            )}
          </div>
        )}
      </div>
    </SlideOver>
  );
}

// ─── Sub-componentes ──────────────────────────────────────────────────────────

const STEP_ORDER: WizardStep[] = ["template", "segmento", "preview", "confirmar"];
const STEP_LABELS: Record<WizardStep, string> = {
  template: "Template",
  segmento: "Segmento",
  preview: "Preview",
  confirmar: "Confirmar",
};

function StepIndicator({ current }: { current: WizardStep }) {
  const currentIdx = STEP_ORDER.indexOf(current);
  return (
    <div className="flex items-center gap-2">
      {STEP_ORDER.map((s, i) => (
        <React.Fragment key={s}>
          <div className="flex items-center gap-1.5">
            <span
              className={`w-5 h-5 rounded-full text-[11px] font-semibold flex items-center justify-center ${
                i < currentIdx
                  ? "bg-green-600 text-white"
                  : i === currentIdx
                  ? "bg-green-100 text-green-700 border border-green-600"
                  : "bg-gray-100 text-gray-400"
              }`}
            >
              {i + 1}
            </span>
            <span
              className={`text-xs ${
                i === currentIdx ? "text-green-700 font-medium" : "text-gray-400"
              }`}
            >
              {STEP_LABELS[s]}
            </span>
          </div>
          {i < STEP_ORDER.length - 1 && (
            <div className={`h-px flex-1 ${i < currentIdx ? "bg-green-600" : "bg-gray-200"}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

function StepTemplate({
  nome,
  onNomeChange,
  templates,
  isLoading,
  selectedId,
  onSelect,
}: {
  nome: string;
  onNomeChange: (v: string) => void;
  templates: MessageTemplate[];
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (t: MessageTemplate) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Nome da campanha
        </label>
        <input
          type="text"
          value={nome}
          onChange={(e) => onNomeChange(e.target.value)}
          placeholder="Ex: Lembrete retorno cardiologia"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Selecione o template
        </label>
        {isLoading ? (
          <p className="text-sm text-gray-400">Carregando templates...</p>
        ) : templates.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhum template disponivel. Crie um template primeiro.</p>
        ) : (
          <div className="flex flex-col gap-2 max-h-80 overflow-y-auto">
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => onSelect(t)}
                className={`text-left rounded-lg border p-3 transition-colors ${
                  selectedId === t.id
                    ? "border-green-500 bg-green-50"
                    : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                }`}
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
    </div>
  );
}

function StepSegmento({
  filters,
  onFiltersChange,
  preview,
  isLoadingPreview,
}: {
  filters: WizardFilters;
  onFiltersChange: (f: WizardFilters) => void;
  preview: SegmentPreview | null;
  isLoadingPreview: boolean;
}) {
  function update(key: keyof WizardFilters, value: string) {
    onFiltersChange({ ...filters, [key]: value });
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Especialidade
        </label>
        <select
          value={filters.especialidade ?? "Todas"}
          onChange={(e) => update("especialidade", e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          {ESPECIALIDADES.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Ultimo Agendamento
        </label>
        <select
          value={filters.ultimo_agendamento_range ?? ""}
          onChange={(e) => update("ultimo_agendamento_range", e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          {AGENDAMENTO_RANGES.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Status do Paciente
        </label>
        <select
          value={filters.status_paciente ?? ""}
          onChange={(e) => update("status_paciente", e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          {STATUS_PACIENTE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {/* Contagem em tempo real */}
      <div className="rounded-lg bg-green-50 border border-green-200 p-3">
        {isLoadingPreview ? (
          <p className="text-sm text-green-600">Calculando...</p>
        ) : preview ? (
          <>
            <p className="text-sm font-semibold text-green-700">
              {preview.count} paciente{preview.count !== 1 ? "s" : ""} encontrado{preview.count !== 1 ? "s" : ""}
            </p>
            {preview.sample.length > 0 && (
              <ul className="mt-2 text-xs text-green-600 space-y-0.5">
                {preview.sample.slice(0, 5).map((p) => (
                  <li key={p.id}>• {p.nome} ({p.phone})</li>
                ))}
                {preview.count > 5 && (
                  <li className="text-gray-400">...e mais {preview.count - 5}</li>
                )}
              </ul>
            )}
          </>
        ) : (
          <p className="text-sm text-gray-400">Ajuste os filtros para ver a contagem</p>
        )}
      </div>
    </div>
  );
}

function StepPreview({
  nome,
  template,
  filters,
  preview,
}: {
  nome: string;
  template: MessageTemplate | null;
  filters: WizardFilters;
  preview: SegmentPreview | null;
}) {
  const filterLabels: string[] = [];
  if (filters.especialidade && filters.especialidade !== "Todas") {
    filterLabels.push(`Especialidade: ${filters.especialidade}`);
  }
  if (filters.ultimo_agendamento_range) {
    const found = AGENDAMENTO_RANGES.find((o) => o.value === filters.ultimo_agendamento_range);
    if (found) filterLabels.push(`Agendamento: ${found.label}`);
  }
  if (filters.status_paciente) {
    const found = STATUS_PACIENTE_OPTIONS.find((o) => o.value === filters.status_paciente);
    if (found) filterLabels.push(`Status: ${found.label}`);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-gray-200 p-4 flex flex-col gap-3">
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Nome</p>
          <p className="text-sm text-gray-800 mt-0.5">{nome}</p>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Template</p>
          <p className="text-sm text-gray-800 mt-0.5">{template?.nome ?? "—"}</p>
        </div>
        {template && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Mensagem</p>
            <div className="mt-1 rounded-md bg-gray-50 border border-gray-100 p-3 text-sm text-gray-700 whitespace-pre-line">
              {template.corpo}
            </div>
          </div>
        )}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Filtros</p>
          <p className="text-sm text-gray-700 mt-0.5">
            {filterLabels.length > 0 ? filterLabels.join(" · ") : "Todos os pacientes"}
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Destinatarios</p>
          <p className="text-sm text-gray-800 mt-0.5 font-semibold">
            {preview ? `${preview.count} paciente${preview.count !== 1 ? "s" : ""}` : "—"}
          </p>
        </div>
      </div>
      <p className="text-xs text-gray-500">
        Revise as informacoes acima. Ao confirmar, a campanha sera criada e o envio iniciado imediatamente.
      </p>
    </div>
  );
}

function StepConfirmar({
  success,
  error,
  isSubmitting,
  onSubmit,
}: {
  success: boolean;
  error: string | null;
  isSubmitting: boolean;
  onSubmit: () => void;
}) {
  if (success) {
    return (
      <div className="flex flex-col items-center gap-3 py-8">
        <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
          <span className="text-green-600 text-2xl">✓</span>
        </div>
        <p className="text-base font-semibold text-green-700">Campanha criada com sucesso!</p>
        <p className="text-sm text-gray-500">O painel sera atualizado em breve.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-gray-600">
        Clique em <strong>Confirmar e Enviar</strong> para criar a campanha e iniciar o envio para os destinatarios selecionados.
      </p>
      {error && (
        <div className="rounded-md bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-600">
          {error}
        </div>
      )}
      {isSubmitting && (
        <p className="text-sm text-gray-400">Criando campanha...</p>
      )}
    </div>
  );
}
