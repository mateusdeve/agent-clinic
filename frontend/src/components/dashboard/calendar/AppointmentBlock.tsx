"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import type { Appointment } from "@/lib/types";

interface AppointmentBlockProps {
  appointment: Appointment;
  compact?: boolean;
  onClick: () => void;
}

const STATUS_COLORS: Record<
  Appointment["status"],
  { block: string; text: string }
> = {
  agendado: {
    block: "bg-blue-50 border-l-4 border-blue-500",
    text: "text-blue-700",
  },
  confirmado: {
    block: "bg-green-50 border-l-4 border-green-500",
    text: "text-green-700",
  },
  realizado: {
    block: "bg-gray-50 border-l-4 border-gray-400",
    text: "text-gray-500",
  },
  cancelado: {
    block: "bg-red-50 border-l-4 border-red-400",
    text: "text-red-400 line-through",
  },
};

export function AppointmentBlock({
  appointment,
  compact = false,
  onClick,
}: AppointmentBlockProps) {
  const colors = STATUS_COLORS[appointment.status] ?? STATUS_COLORS.agendado;

  if (compact) {
    return (
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "w-full text-left rounded px-1.5 py-0.5 cursor-pointer hover:shadow-sm transition-shadow text-xs",
          colors.block,
          colors.text
        )}
        title={`${appointment.horario} — ${appointment.patient_nome} / ${appointment.doctor_nome}`}
      >
        <span className="font-semibold">{appointment.horario}</span>{" "}
        <span className="truncate">{appointment.patient_nome}</span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full text-left rounded px-2 py-1.5 cursor-pointer hover:shadow-sm transition-shadow text-xs",
        colors.block,
        colors.text
      )}
    >
      <div className="font-semibold">{appointment.horario}</div>
      <div className="truncate">{appointment.patient_nome}</div>
      <div className="truncate opacity-75">{appointment.doctor_nome}</div>
    </button>
  );
}
