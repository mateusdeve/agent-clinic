"use client";

import * as React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { format, addDays, addWeeks, addMonths, subDays, subWeeks, subMonths, startOfWeek, endOfWeek } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Doctor } from "@/lib/types";

type CalendarView = "day" | "week" | "month";

interface CalendarToolbarProps {
  currentDate: Date;
  view: CalendarView;
  onDateChange: (d: Date) => void;
  onViewChange: (v: CalendarView) => void;
  doctors: Doctor[];
  selectedDoctorId: string | null;
  onDoctorChange: (id: string | null) => void;
  showDoctorFilter: boolean;
}

function formatDateLabel(date: Date, view: CalendarView): string {
  if (view === "day") {
    return format(date, "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR });
  }
  if (view === "week") {
    const start = startOfWeek(date, { locale: ptBR });
    const end = endOfWeek(date, { locale: ptBR });
    return `${format(start, "d")}–${format(end, "d MMM yyyy", { locale: ptBR })}`;
  }
  // month
  return format(date, "MMMM yyyy", { locale: ptBR });
}

function navigatePrev(date: Date, view: CalendarView): Date {
  if (view === "day") return subDays(date, 1);
  if (view === "week") return subWeeks(date, 1);
  return subMonths(date, 1);
}

function navigateNext(date: Date, view: CalendarView): Date {
  if (view === "day") return addDays(date, 1);
  if (view === "week") return addWeeks(date, 1);
  return addMonths(date, 1);
}

export function CalendarToolbar({
  currentDate,
  view,
  onDateChange,
  onViewChange,
  doctors,
  selectedDoctorId,
  onDoctorChange,
  showDoctorFilter,
}: CalendarToolbarProps) {
  const views: { key: CalendarView; label: string }[] = [
    { key: "day", label: "Dia" },
    { key: "week", label: "Semana" },
    { key: "month", label: "Mes" },
  ];

  return (
    <div className="flex flex-col gap-3 mb-4">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        {/* Left: navigation */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onDateChange(navigatePrev(currentDate, view))}
            className="p-1.5 rounded-md hover:bg-gray-100 text-gray-600 transition-colors"
            aria-label="Anterior"
          >
            <ChevronLeft className="size-4" />
          </button>
          <button
            type="button"
            onClick={() => onDateChange(new Date())}
            className="px-3 py-1.5 text-sm font-medium rounded-md border border-gray-200 hover:bg-gray-50 text-gray-700 transition-colors"
          >
            Hoje
          </button>
          <button
            type="button"
            onClick={() => onDateChange(navigateNext(currentDate, view))}
            className="p-1.5 rounded-md hover:bg-gray-100 text-gray-600 transition-colors"
            aria-label="Proximo"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>

        {/* Center: current date label */}
        <h2 className="text-base font-semibold text-gray-800 capitalize min-w-[180px] text-center">
          {formatDateLabel(currentDate, view)}
        </h2>

        {/* Right: view toggle */}
        <div className="flex items-center gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50">
          {views.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => onViewChange(key)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                view === key
                  ? "bg-green-500 text-white shadow-sm"
                  : "text-gray-600 hover:text-gray-800 hover:bg-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Doctor filter row */}
      {showDoctorFilter && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Medico:</span>
          <Select
            value={selectedDoctorId ?? "all"}
            onValueChange={(val) => onDoctorChange(val === "all" ? null : val)}
          >
            <SelectTrigger className="w-56 h-9 text-sm">
              <SelectValue placeholder="Todos os medicos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os medicos</SelectItem>
              {doctors.map((doctor) => (
                <SelectItem key={doctor.id} value={doctor.id}>
                  {doctor.nome}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  );
}
