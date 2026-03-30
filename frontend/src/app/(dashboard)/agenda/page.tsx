"use client";

import * as React from "react";
import { useSession } from "next-auth/react";
import {
  format,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
} from "date-fns";
import { ptBR } from "date-fns/locale";
import { apiFetch } from "@/lib/api";
import type { Appointment, Doctor, Patient, PaginatedResponse, BlockedSlot } from "@/lib/types";
import { CalendarToolbar } from "@/components/dashboard/calendar/CalendarToolbar";
import { CalendarDay } from "@/components/dashboard/calendar/CalendarDay";
import { CalendarWeek } from "@/components/dashboard/calendar/CalendarWeek";
import { CalendarMonth } from "@/components/dashboard/calendar/CalendarMonth";
import { SlideOver } from "@/components/dashboard/SlideOver";
import { AppointmentForm } from "./appointment-form";

type CalendarView = "day" | "week" | "month";

function getDateRange(
  date: Date,
  view: CalendarView
): { from: string; to: string } {
  if (view === "day") {
    const d = format(date, "yyyy-MM-dd");
    return { from: d, to: d };
  }
  if (view === "week") {
    return {
      from: format(startOfWeek(date, { locale: ptBR }), "yyyy-MM-dd"),
      to: format(endOfWeek(date, { locale: ptBR }), "yyyy-MM-dd"),
    };
  }
  return {
    from: format(startOfMonth(date), "yyyy-MM-dd"),
    to: format(endOfMonth(date), "yyyy-MM-dd"),
  };
}

export default function AgendaPage() {
  const { data: session } = useSession();
  const userRole = (session as any)?.user?.role as string | undefined;
  const isMedico = userRole === "medico";

  // Calendar state
  const [currentDate, setCurrentDate] = React.useState<Date>(new Date());
  const [view, setView] = React.useState<CalendarView>("week");
  const [selectedDoctorId, setSelectedDoctorId] = React.useState<string | null>(null);

  // Data state
  const [appointments, setAppointments] = React.useState<Appointment[]>([]);
  const [doctors, setDoctors] = React.useState<Doctor[]>([]);
  const [patients, setPatients] = React.useState<Patient[]>([]);
  const [blockedSlots, setBlockedSlots] = React.useState<BlockedSlot[]>([]);
  const [loading, setLoading] = React.useState(true);

  // Slide-over state
  const [slideOverOpen, setSlideOverOpen] = React.useState(false);
  const [selectedAppointment, setSelectedAppointment] = React.useState<Appointment | null>(null);
  const [prefillDate, setPrefillDate] = React.useState<string | undefined>();
  const [prefillTime, setPrefillTime] = React.useState<string | undefined>();

  // ─── Initial data load ──────────────────────────────────────────────────────

  React.useEffect(() => {
    async function loadStaticData() {
      try {
        const [doctorsRes, patientsRes] = await Promise.all([
          apiFetch<PaginatedResponse<Doctor>>("/api/doctors?per_page=100"),
          apiFetch<PaginatedResponse<Patient>>("/api/patients?per_page=500"),
        ]);
        setDoctors(doctorsRes.items);
        setPatients(patientsRes.items);
      } catch (e) {
        console.error("[agenda] failed to load static data", e);
      }
    }
    loadStaticData();
  }, []);

  // ─── Appointments fetch (re-runs on date/view/doctor changes) ───────────────

  React.useEffect(() => {
    async function loadAppointments() {
      setLoading(true);
      try {
        const { from, to } = getDateRange(currentDate, view);
        const params = new URLSearchParams({
          date_from: from,
          date_to: to,
          per_page: "500",
        });
        if (selectedDoctorId) params.set("doctor_id", selectedDoctorId);
        const res = await apiFetch<PaginatedResponse<Appointment>>(
          `/api/appointments?${params.toString()}`
        );
        setAppointments(res.items);
      } catch (e) {
        console.error("[agenda] failed to load appointments", e);
      } finally {
        setLoading(false);
      }
    }
    loadAppointments();
  }, [currentDate, view, selectedDoctorId]);

  // ─── Blocked slots fetch (re-runs when doctor is selected) ─────────────────

  React.useEffect(() => {
    if (!selectedDoctorId) {
      setBlockedSlots([]);
      return;
    }
    apiFetch<BlockedSlot[]>(`/api/doctors/${selectedDoctorId}/blocked-slots`)
      .then(setBlockedSlots)
      .catch((e) => {
        console.error("[agenda] failed to load blocked slots", e);
        setBlockedSlots([]);
      });
  }, [selectedDoctorId]);

  // ─── Slide-over handlers ────────────────────────────────────────────────────

  function handleSlotClick(time: string) {
    setSelectedAppointment(null);
    setPrefillDate(format(currentDate, "yyyy-MM-dd"));
    setPrefillTime(time);
    setSlideOverOpen(true);
  }

  function handleAppointmentClick(appt: Appointment) {
    setSelectedAppointment(appt);
    setPrefillDate(undefined);
    setPrefillTime(undefined);
    setSlideOverOpen(true);
  }

  function handleDayClick(day: Date) {
    setCurrentDate(day);
    setView("day");
  }

  function handleSlideOverClose() {
    setSlideOverOpen(false);
    setSelectedAppointment(null);
  }

  async function handleFormSuccess() {
    setSlideOverOpen(false);
    setSelectedAppointment(null);
    // Refetch appointments
    try {
      const { from, to } = getDateRange(currentDate, view);
      const params = new URLSearchParams({
        date_from: from,
        date_to: to,
        per_page: "500",
      });
      if (selectedDoctorId) params.set("doctor_id", selectedDoctorId);
      const res = await apiFetch<PaginatedResponse<Appointment>>(
        `/api/appointments?${params.toString()}`
      );
      setAppointments(res.items);
    } catch (e) {
      console.error("[agenda] failed to refetch after form success", e);
    }
  }

  // ─── Slide-over title ────────────────────────────────────────────────────────

  const slideOverTitle = selectedAppointment
    ? "Editar Agendamento"
    : "Novo Agendamento";

  // ─── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-serif text-2xl text-gray-800">Agenda</h1>
        <button
          type="button"
          onClick={() => {
            setSelectedAppointment(null);
            setPrefillDate(format(currentDate, "yyyy-MM-dd"));
            setPrefillTime(undefined);
            setSlideOverOpen(true);
          }}
          className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors"
        >
          + Novo Agendamento
        </button>
      </div>

      {/* Toolbar: navigation, view toggle, doctor filter */}
      <CalendarToolbar
        currentDate={currentDate}
        view={view}
        onDateChange={setCurrentDate}
        onViewChange={(v) => setView(v as CalendarView)}
        doctors={doctors}
        selectedDoctorId={selectedDoctorId}
        onDoctorChange={setSelectedDoctorId}
        showDoctorFilter={!isMedico}
      />

      {/* Calendar body */}
      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-gray-500">Carregando agenda...</span>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-auto">
          {view === "day" && (
            <CalendarDay
              date={currentDate}
              appointments={appointments}
              onSlotClick={handleSlotClick}
              onAppointmentClick={handleAppointmentClick}
              blockedSlots={blockedSlots}
            />
          )}
          {view === "week" && (
            <CalendarWeek
              date={currentDate}
              appointments={appointments}
              onDayClick={handleDayClick}
              onAppointmentClick={handleAppointmentClick}
              blockedSlots={blockedSlots}
            />
          )}
          {view === "month" && (
            <CalendarMonth
              date={currentDate}
              appointments={appointments}
              onDayClick={handleDayClick}
              onAppointmentClick={handleAppointmentClick}
              blockedSlots={blockedSlots}
            />
          )}
        </div>
      )}

      {/* Slide-over for create/edit */}
      <SlideOver
        open={slideOverOpen}
        onClose={handleSlideOverClose}
        title={slideOverTitle}
      >
        <AppointmentForm
          key={selectedAppointment?.id ?? "new"}
          appointment={selectedAppointment}
          patients={patients}
          doctors={doctors}
          prefillDate={prefillDate}
          prefillTime={prefillTime}
          onSuccess={handleFormSuccess}
          onCancel={handleSlideOverClose}
        />
      </SlideOver>
    </div>
  );
}
