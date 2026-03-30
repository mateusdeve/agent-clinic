"use client";

import * as React from "react";
import {
  eachDayOfInterval,
  startOfWeek,
  endOfWeek,
  isSameDay,
  isToday,
  parseISO,
  format,
} from "date-fns";
import { ptBR } from "date-fns/locale";
import type { Appointment, BlockedSlot } from "@/lib/types";
import { AppointmentBlock } from "./AppointmentBlock";

interface CalendarWeekProps {
  date: Date;
  appointments: Appointment[];
  onDayClick: (d: Date) => void;
  onAppointmentClick: (a: Appointment) => void;
  blockedSlots?: BlockedSlot[];
}

export function CalendarWeek({
  date,
  appointments,
  onDayClick,
  onAppointmentClick,
  blockedSlots = [],
}: CalendarWeekProps) {
  const weekDays = eachDayOfInterval({
    start: startOfWeek(date, { locale: ptBR }),
    end: endOfWeek(date, { locale: ptBR }),
  });

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Header row */}
      <div className="grid grid-cols-7 border-b border-gray-200 bg-gray-50">
        {weekDays.map((day) => {
          const today = isToday(day);
          return (
            <button
              key={day.toISOString()}
              type="button"
              onClick={() => onDayClick(day)}
              className={`py-2 text-center cursor-pointer hover:bg-gray-100 transition-colors ${
                today ? "bg-green-50" : ""
              }`}
            >
              <div className="text-xs font-medium text-gray-500 uppercase">
                {format(day, "EEE", { locale: ptBR })}
              </div>
              <div
                className={`text-sm font-semibold mt-0.5 ${
                  today
                    ? "w-7 h-7 bg-green-500 text-white rounded-full flex items-center justify-center mx-auto"
                    : "text-gray-800"
                }`}
              >
                {format(day, "d")}
              </div>
            </button>
          );
        })}
      </div>

      {/* Body: appointment columns */}
      <div className="grid grid-cols-7 divide-x divide-gray-100 min-h-[200px]">
        {weekDays.map((day) => {
          const today = isToday(day);
          const dayAppts = appointments.filter((a) =>
            isSameDay(parseISO(a.data_agendamento), day)
          );
          // Check if day has any blocked slots
          const dayDateStr = format(day, "yyyy-MM-dd");
          const hasBlocked = blockedSlots.some((b) => b.blocked_date === dayDateStr);

          return (
            <div
              key={day.toISOString()}
              className={`p-1 flex flex-col gap-1 min-h-[120px] ${
                today ? "bg-green-50/40" : ""
              }`}
            >
              {/* Blocked indicator */}
              {hasBlocked && (
                <div className="text-xs text-gray-400 italic px-1">
                  Bloqueado
                </div>
              )}

              {/* Appointments sorted by time */}
              {dayAppts
                .sort((a, b) => a.horario.localeCompare(b.horario))
                .map((appt) => (
                  <AppointmentBlock
                    key={appt.id}
                    appointment={appt}
                    compact={false}
                    onClick={() => onAppointmentClick(appt)}
                  />
                ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
