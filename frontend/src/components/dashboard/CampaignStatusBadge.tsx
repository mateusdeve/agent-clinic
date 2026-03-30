import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CampaignStatus, RecipientStatus } from "@/lib/types";

// ─── Campanha ─────────────────────────────────────────────────────────────────

const CAMPAIGN_STATUS_CONFIG: Record<
  CampaignStatus,
  { label: string; className: string }
> = {
  rascunho: {
    label: "Rascunho",
    className: "bg-gray-100 text-gray-700 hover:bg-gray-100 border-gray-200",
  },
  enviando: {
    label: "Enviando",
    className: "bg-blue-100 text-blue-700 hover:bg-blue-100 border-blue-200",
  },
  concluida: {
    label: "Concluida",
    className: "bg-green-100 text-green-700 hover:bg-green-100 border-green-200",
  },
  falha: {
    label: "Falha",
    className: "bg-red-100 text-red-700 hover:bg-red-100 border-red-200",
  },
};

interface CampaignStatusBadgeProps {
  status: CampaignStatus;
}

export function CampaignStatusBadge({ status }: CampaignStatusBadgeProps) {
  const config = CAMPAIGN_STATUS_CONFIG[status] ?? {
    label: status,
    className: "bg-gray-100 text-gray-600",
  };

  return (
    <Badge
      variant="outline"
      className={cn("text-xs font-medium capitalize", config.className)}
    >
      {config.label}
    </Badge>
  );
}

// ─── Destinatario ─────────────────────────────────────────────────────────────

const RECIPIENT_STATUS_CONFIG: Record<
  RecipientStatus,
  { label: string; className: string }
> = {
  pendente: {
    label: "Pendente",
    className: "bg-gray-100 text-gray-700 hover:bg-gray-100 border-gray-200",
  },
  processando: {
    label: "Processando",
    className: "bg-yellow-100 text-yellow-700 hover:bg-yellow-100 border-yellow-200",
  },
  enviado: {
    label: "Enviado",
    className: "bg-blue-100 text-blue-700 hover:bg-blue-100 border-blue-200",
  },
  entregue: {
    label: "Entregue",
    className: "bg-green-100 text-green-700 hover:bg-green-100 border-green-200",
  },
  lido: {
    label: "Lido",
    className: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100 border-emerald-200",
  },
  falha: {
    label: "Falha",
    className: "bg-red-100 text-red-700 hover:bg-red-100 border-red-200",
  },
};

interface RecipientStatusBadgeProps {
  status: RecipientStatus;
}

export function RecipientStatusBadge({ status }: RecipientStatusBadgeProps) {
  const config = RECIPIENT_STATUS_CONFIG[status] ?? {
    label: status,
    className: "bg-gray-100 text-gray-600",
  };

  return (
    <Badge
      variant="outline"
      className={cn("text-xs font-medium capitalize", config.className)}
    >
      {config.label}
    </Badge>
  );
}
