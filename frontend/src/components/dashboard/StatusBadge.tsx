import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AppointmentStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: AppointmentStatus;
}

const STATUS_CONFIG: Record<
  AppointmentStatus,
  { label: string; className: string }
> = {
  agendado: {
    label: "Agendado",
    className: "bg-blue-100 text-blue-700 hover:bg-blue-100 border-blue-200",
  },
  confirmado: {
    label: "Confirmado",
    className:
      "bg-green-100 text-green-700 hover:bg-green-100 border-green-200",
  },
  realizado: {
    label: "Realizado",
    className: "bg-gray-100 text-gray-600 hover:bg-gray-100 border-gray-200",
  },
  cancelado: {
    label: "Cancelado",
    className:
      "bg-red-100 text-red-700 hover:bg-red-100 border-red-200 line-through",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
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
