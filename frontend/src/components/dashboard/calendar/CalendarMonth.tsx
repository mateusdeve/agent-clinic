"use client";

import * as React from "react";
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameDay,
  isSameMonth,
  isToday,
  parseISO,
  format,
} from "date-fns";
import { ptBR } from "date-fns/locale";
import type { Appointment, BlockedSlot } from "@/lib/types";
import { AppointmentBlock } from "./AppointmentBlock";

interface CalendarMonthProps {
  date: Date;
  appointments: Appointment[];
  onDayClick: (d: Date) => void;
  onAppointmentClick: (a: Appointment) => void;
  blockedSlots?: BlockedSlot[];
}

const DAY_HEADERS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"];
const MAX_VISIBLE = 3;

export function CalendarMonth({
  date,
  appointments,
  onDayClick,
  onAppointmentClick,
  blockedSlots = [],
}: CalendarMonthProps) {
  // Build the 6x7 grid: pad to full weeks
  const monthStart = startOfMonth(date);
  const monthEnd = endOfMonth(date);
  const gridStart = startOfWeek(monthStart, { locale: ptBR });
  const gridEnd = endOfWeek(monthEnd, { locale: ptBR });

  const gridDays = eachDayOfInterval({ start: gridStart, end: gridEnd });

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Day name headers */}
      <div className="grid grid-cols-7 border-b border-gray-200 bg-gray-50">
        {DAY_HEADERS.map((d) => (
          <div key={d} className="py-2 text-center text-xs font-medium text-gray-500 uppercase">
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 border-b border-gray-200">
        {gridDays.map((day) => {
          const inMonth = isSameMonth(day, date);
          const today = isToday(day);
          const dayAppts = appointments.filter((a) =>
            isSameDay(parseISO(a.data_agendamento), day)
          );
          const visible = dayAppts.slice(0, MAX_VISIBLE);
          const overflow = dayAppts.length - MAX_VISIBLE;

          return (
            <div
              key={day.toISOString()}
              className={`min-h-[100px] p-1 border-r border-b border-gray-100 last:border-r-0 flex flex-col gap-0.5 ${
                !inMonth ? "bg-gray-50" : ""
              }`}
            >
              {/* Date number */}
              <button
                type="button"
                onClick={() => onDayClick(day)}
                className={`text-xs font-semibold self-start w-6 h-6 flex items-center justify-center rounded-full transition-colors cursor-pointer ${
                  today
                    ? "ring-2 ring-green-500 text-green-700"
                    : inMonth
                    ? "text-gray-700 hover:bg-gray-100"
                    : "text-gray-400 hover:bg-gray-100"
                }`}
              >
                {format(day, "d")}
              </button>

              {/* Appointments */}
              {visible.map((appt) => (
                <AppointmentBlock
                  key={appt.id}
                  appointment={appt}
                  compact={true}
                  onClick={() => onAppointmentClick(appt)}
                />
              ))}

              {/* Overflow link */}
              {overflow > 0 && (
                <button
                  type="button"
                  onClick={() => onDayClick(day)}
                  className="text-xs text-green-600 hover:text-green-800 text-left px-1.5 font-medium cursor-pointer"
                >
                  +{overflow} mais
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
