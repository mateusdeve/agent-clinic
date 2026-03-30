"use client";

import * as React from "react";
import {
  eachHourOfInterval,
  setHours,
  setMinutes,
  isSameDay,
  isToday,
  parseISO,
  format,
} from "date-fns";
import { ptBR } from "date-fns/locale";
import type { Appointment, BlockedSlot } from "@/lib/types";
import { AppointmentBlock } from "./AppointmentBlock";

interface CalendarDayProps {
  date: Date;
  appointments: Appointment[];
  onSlotClick: (time: string) => void;
  onAppointmentClick: (a: Appointment) => void;
  blockedSlots?: BlockedSlot[];
}

// Calendar time range: 07:00 to 20:00
const START_HOUR = 7;
const END_HOUR = 20;
const ROW_HEIGHT = 48; // px per 30-minute row

function timeToMinutes(timeStr: string): number {
  const [h, m] = timeStr.split(":").map(Number);
  return h * 60 + m;
}

function minutesToOffset(totalMinutes: number): number {
  const startMinutes = START_HOUR * 60;
  return ((totalMinutes - startMinutes) / 30) * ROW_HEIGHT;
}

function minutesToHeight(durationMinutes: number): number {
  return (durationMinutes / 30) * ROW_HEIGHT;
}

export function CalendarDay({
  date,
  appointments,
  onSlotClick,
  onAppointmentClick,
  blockedSlots = [],
}: CalendarDayProps) {
  // Generate 30-minute slots from 07:00 to 19:30
  const hourIntervals = eachHourOfInterval({
    start: setHours(date, START_HOUR),
    end: setHours(date, END_HOUR - 1),
  });

  const slots: Date[] = [];
  hourIntervals.forEach((h) => {
    slots.push(h);
    slots.push(setMinutes(h, 30));
  });

  // Filter appointments for this date
  const dayAppointments = appointments.filter((a) =>
    isSameDay(parseISO(a.data_agendamento), date)
  );

  // Filter blocked slots for this date
  const dayBlocked = blockedSlots.filter(
    (b) => b.blocked_date === format(date, "yyyy-MM-dd")
  );

  // Current time indicator position
  const now = new Date();
  const showNow = isToday(date);
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  const nowOffset = minutesToOffset(nowMinutes);
  const nowVisible = nowMinutes >= START_HOUR * 60 && nowMinutes < END_HOUR * 60;

  const totalHeight = slots.length * ROW_HEIGHT;

  return (
    <div className="flex border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Time labels column */}
      <div className="w-14 shrink-0 border-r border-gray-100 bg-gray-50">
        {slots.map((slot, i) => (
          <div
            key={i}
            className="border-b border-gray-100 flex items-center justify-end pr-2"
            style={{ height: ROW_HEIGHT }}
          >
            <span className="text-xs text-gray-400">
              {format(slot, "HH:mm")}
            </span>
          </div>
        ))}
      </div>

      {/* Grid column */}
      <div className="flex-1 relative" style={{ height: totalHeight }}>
        {/* Row backgrounds + clickable slots */}
        {slots.map((slot, i) => (
          <button
            key={i}
            type="button"
            onClick={() => onSlotClick(format(slot, "HH:mm"))}
            className="absolute left-0 right-0 border-b border-gray-100 hover:bg-green-50/40 transition-colors cursor-pointer"
            style={{ top: i * ROW_HEIGHT, height: ROW_HEIGHT }}
            aria-label={`Agendar as ${format(slot, "HH:mm")}`}
          />
        ))}

        {/* Blocked slot bands (behind appointments, z-10) */}
        {dayBlocked.map((blocked) => {
          const startMin = blocked.start_time
            ? timeToMinutes(blocked.start_time)
            : START_HOUR * 60;
          const endMin = blocked.end_time
            ? timeToMinutes(blocked.end_time)
            : END_HOUR * 60;
          const clampedStart = Math.max(startMin, START_HOUR * 60);
          const clampedEnd = Math.min(endMin, END_HOUR * 60);
          if (clampedEnd <= clampedStart) return null;
          const top = minutesToOffset(clampedStart);
          const height = minutesToHeight(clampedEnd - clampedStart);
          return (
            <div
              key={blocked.id}
              className="absolute left-0 right-0 bg-gray-200/60 z-10 flex items-start px-2 pt-1"
              style={{ top, height }}
              title={blocked.reason ?? "Horario bloqueado"}
            >
              <span className="text-xs text-gray-400 select-none">
                {blocked.reason ?? "Bloqueado"}
              </span>
            </div>
          );
        })}

        {/* Appointment blocks (z-20) */}
        {dayAppointments.map((appt) => {
          const apptMinutes = timeToMinutes(appt.horario);
          const top = minutesToOffset(apptMinutes);
          return (
            <div
              key={appt.id}
              className="absolute left-1 right-1 z-20"
              style={{ top: top + 2, minHeight: ROW_HEIGHT - 4 }}
            >
              <AppointmentBlock
                appointment={appt}
                compact={false}
                onClick={() => onAppointmentClick(appt)}
              />
            </div>
          );
        })}

        {/* Current time indicator */}
        {showNow && nowVisible && (
          <div
            className="absolute left-0 right-0 z-30 pointer-events-none"
            style={{ top: nowOffset }}
          >
            <div className="flex items-center">
              <div className="w-2 h-2 rounded-full bg-red-500 -ml-1 shrink-0" />
              <div className="flex-1 h-px bg-red-500" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
