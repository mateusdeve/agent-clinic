"use client";

import * as React from "react";
import { apiFetch } from "@/lib/api";
import { DoctorSchedule } from "@/lib/types";
import { Button } from "@/components/ui/button";

const DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];
// day_of_week: 1=Monday ... 7=Sunday (or 0=Sunday depending on API)
// Per types.ts: 0=Sunday ... 6=Saturday
const DAY_INDICES = [1, 2, 3, 4, 5, 6, 0]; // Mon-Sun order for display, mapped to 0=Sun..6=Sat

// Generate 30-min time slots from 07:00 to 20:00
function generateTimeSlots(): string[] {
  const slots: string[] = [];
  for (let h = 7; h < 20; h++) {
    slots.push(`${String(h).padStart(2, "0")}:00`);
    slots.push(`${String(h).padStart(2, "0")}:30`);
  }
  return slots;
}

const TIME_SLOTS = generateTimeSlots();

// Adds 30 minutes to a time string "HH:MM" -> "HH:MM"
function addThirtyMinutes(time: string): string {
  const [h, m] = time.split(":").map(Number);
  const total = h * 60 + m + 30;
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

// Build initial active cells set from existing DoctorSchedule records
function buildActiveCells(schedules: DoctorSchedule[]): Set<string> {
  const active = new Set<string>();
  for (const sch of schedules) {
    const dayIdx = DAY_INDICES.indexOf(sch.day_of_week);
    if (dayIdx === -1) continue;
    for (let i = 0; i < TIME_SLOTS.length; i++) {
      const slot = TIME_SLOTS[i];
      if (slot >= sch.start_time && slot < sch.end_time) {
        active.add(`${dayIdx}-${slot}`);
      }
    }
  }
  return active;
}

// Convert active cells back to DoctorSchedule-like slots for API
interface ScheduleSlot {
  day_of_week: number;
  start_time: string;
  end_time: string;
}

function buildScheduleSlots(activeCells: Set<string>): ScheduleSlot[] {
  // Group by day
  const byDay: Record<number, string[]> = {};
  for (const key of activeCells) {
    const [dayStr, time] = key.split("-");
    const day = Number(dayStr);
    if (!byDay[day]) byDay[day] = [];
    byDay[day].push(time);
  }

  const slots: ScheduleSlot[] = [];
  for (const [dayStr, times] of Object.entries(byDay)) {
    const day = Number(dayStr);
    const sorted = [...times].sort();
    // Build consecutive ranges
    let rangeStart = sorted[0];
    let prev = sorted[0];

    for (let i = 1; i <= sorted.length; i++) {
      const curr = sorted[i];
      if (curr !== undefined && curr === addThirtyMinutes(prev)) {
        prev = curr;
      } else {
        slots.push({
          day_of_week: DAY_INDICES[day],
          start_time: rangeStart,
          end_time: addThirtyMinutes(prev),
        });
        if (curr !== undefined) {
          rangeStart = curr;
          prev = curr;
        }
      }
    }
  }
  return slots;
}

interface ScheduleGridProps {
  doctorId: string;
  doctorNome: string;
  onClose: () => void;
}

export function ScheduleGrid({ doctorId, doctorNome, onClose }: ScheduleGridProps) {
  const [activeCells, setActiveCells] = React.useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = React.useState(true);
  const [isSaving, setIsSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  // Drag selection state
  const isDragging = React.useRef(false);
  const dragValue = React.useRef<boolean>(true); // true = activate, false = deactivate

  React.useEffect(() => {
    async function loadSchedule() {
      try {
        setIsLoading(true);
        const schedules = await apiFetch<DoctorSchedule[]>(
          `/api/doctors/${doctorId}/schedules`
        );
        setActiveCells(buildActiveCells(schedules));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar horarios");
      } finally {
        setIsLoading(false);
      }
    }
    loadSchedule();
  }, [doctorId]);

  function toggleCell(key: string) {
    setActiveCells((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  function handleCellMouseDown(key: string) {
    isDragging.current = true;
    dragValue.current = !activeCells.has(key);
    setActiveCells((prev) => {
      const next = new Set(prev);
      if (dragValue.current) {
        next.add(key);
      } else {
        next.delete(key);
      }
      return next;
    });
  }

  function handleCellMouseEnter(key: string) {
    if (!isDragging.current) return;
    setActiveCells((prev) => {
      const next = new Set(prev);
      if (dragValue.current) {
        next.add(key);
      } else {
        next.delete(key);
      }
      return next;
    });
  }

  function handleMouseUp() {
    isDragging.current = false;
  }

  async function handleSave() {
    try {
      setIsSaving(true);
      setError(null);
      setSuccessMsg(null);
      const slots = buildScheduleSlots(activeCells);
      await apiFetch(`/api/doctors/${doctorId}/schedules`, {
        method: "PUT",
        body: JSON.stringify({ slots }),
      });
      setSuccessMsg("Horarios salvos com sucesso!");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar horarios");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-gray-500">Carregando horarios...</p>
        {/* Skeleton grid */}
        <div className="grid grid-cols-8 gap-1">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-6 bg-gray-200 rounded animate-pulse" />
          ))}
          {Array.from({ length: 8 * 6 }).map((_, i) => (
            <div key={`sk-${i}`} className="h-6 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className="select-none"
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="mb-3">
        <p className="text-sm text-gray-600">
          Defina a disponibilidade semanal de{" "}
          <span className="font-medium">{doctorNome}</span>.
          Clique ou arraste para selecionar.
        </p>
      </div>

      {error && (
        <div className="mb-3 p-3 rounded bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="mb-3 p-3 rounded bg-green-50 text-green-700 text-sm">
          {successMsg}
        </div>
      )}

      {/* Grid: time column + 7 day columns */}
      <div className="overflow-x-auto">
        <div
          className="grid gap-px bg-gray-200 rounded border border-gray-200"
          style={{ gridTemplateColumns: `auto repeat(7, 1fr)` }}
        >
          {/* Header row */}
          <div className="bg-gray-50 px-2 py-1 text-xs font-medium text-gray-500">
            Hora
          </div>
          {DAYS.map((day) => (
            <div
              key={day}
              className="bg-gray-50 text-center py-1 text-xs font-semibold text-gray-700"
            >
              {day}
            </div>
          ))}

          {/* Time rows */}
          {TIME_SLOTS.map((time) => (
            <React.Fragment key={time}>
              {/* Time label */}
              <div className="bg-white px-2 py-1 text-xs text-gray-400 leading-5 min-w-[48px]">
                {time}
              </div>
              {/* Day cells */}
              {DAYS.map((_, dayIdx) => {
                const key = `${dayIdx}-${time}`;
                const isActive = activeCells.has(key);
                return (
                  <div
                    key={key}
                    className={`
                      cursor-pointer h-6 transition-colors
                      ${isActive
                        ? "bg-green-100 border border-green-400"
                        : "bg-white border border-gray-100 hover:bg-gray-50"
                      }
                    `}
                    onMouseDown={() => handleCellMouseDown(key)}
                    onMouseEnter={() => handleCellMouseEnter(key)}
                    onClick={() => toggleCell(key)}
                  />
                );
              })}
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3 mt-4">
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? "Salvando..." : "Salvar Horarios"}
        </Button>
        <Button variant="outline" onClick={onClose} disabled={isSaving}>
          Fechar
        </Button>
        <span className="text-xs text-gray-400 ml-auto">
          {activeCells.size} slot(s) selecionado(s)
        </span>
      </div>
    </div>
  );
}
