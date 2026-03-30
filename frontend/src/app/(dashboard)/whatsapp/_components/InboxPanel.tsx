"use client";

import * as React from "react";
import { useSession } from "next-auth/react";
import { useSocket } from "@/hooks/useSocket";
import { apiFetch } from "@/lib/api";
import type {
  ConversationSummary,
  ConversationStatus,
  NewMessageEvent,
  ConversationUpdatedEvent,
} from "@/lib/types";
import { ConversationList } from "./ConversationList";
import { ConversationThread } from "./ConversationThread";
import { PatientSidebar } from "./PatientSidebar";
import { TakeoverBar } from "./TakeoverBar";

type FilterOption = "todas" | ConversationStatus;

// Debounce helper
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value);
  React.useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}

export function InboxPanel() {
  const { data: session } = useSession();
  const token = (session as any)?.access_token as string | undefined;

  const { socket, isConnected } = useSocket(token);

  const [conversations, setConversations] = React.useState<ConversationSummary[]>([]);
  const [selectedPhone, setSelectedPhone] = React.useState<string | null>(null);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [activeFilter, setActiveFilter] = React.useState<FilterOption>("todas");
  const [isLoadingList, setIsLoadingList] = React.useState(false);

  const debouncedSearch = useDebounce(searchQuery, 300);

  // Derive selected conversation's status and human_name from state
  const selectedConv = conversations.find((c) => c.phone === selectedPhone);
  const selectedStatus: ConversationStatus = selectedConv?.status ?? "ia_ativa";
  const selectedHumanName: string | null = selectedConv?.human_name ?? null;
  const selectedPatientId: string | null = selectedConv?.patient_id ?? null;

  // Fetch conversations list
  async function loadConversations(search = "") {
    setIsLoadingList(true);
    try {
      const params = search ? `?search=${encodeURIComponent(search)}` : "";
      const data = await apiFetch<ConversationSummary[]>(`/api/conversations/${params}`);
      setConversations(data);
    } catch (err) {
      console.error("[InboxPanel] load conversations error:", err);
    } finally {
      setIsLoadingList(false);
    }
  }

  // Initial load
  React.useEffect(() => {
    loadConversations();
  }, []);

  // Re-fetch on debounced search change
  React.useEffect(() => {
    loadConversations(debouncedSearch);
  }, [debouncedSearch]);

  // Socket.IO event listeners
  React.useEffect(() => {
    if (!socket) return;

    function onNewMessage(event: NewMessageEvent) {
      setConversations((prev) => {
        const idx = prev.findIndex((c) => c.phone === event.phone);
        if (idx === -1) return prev;

        const updated = { ...prev[idx] };
        updated.last_message_preview = event.content;
        updated.last_message_at = event.created_at;
        updated.message_count = (updated.message_count ?? 0) + 1;

        // Move to top of list
        const rest = prev.filter((_, i) => i !== idx);
        return [updated, ...rest];
      });
    }

    function onConversationUpdated(event: ConversationUpdatedEvent) {
      setConversations((prev) =>
        prev.map((c) => {
          if (c.phone !== event.phone) return c;
          return {
            ...c,
            status: event.status,
            human_name: event.human_name ?? c.human_name ?? null,
          };
        })
      );
    }

    socket.on("new_message", onNewMessage);
    socket.on("conversation_updated", onConversationUpdated);

    return () => {
      socket.off("new_message", onNewMessage);
      socket.off("conversation_updated", onConversationUpdated);
    };
  }, [socket]);

  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6 overflow-hidden">
      {/* Connection indicator */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5">
        <span
          className={`w-2 h-2 rounded-full ${
            isConnected ? "bg-green-500" : "bg-red-400"
          }`}
        />
        <span className="text-[10px] text-gray-400 hidden sm:inline">
          {isConnected ? "Conectado" : "Desconectado"}
        </span>
      </div>

      {/* Left column: Conversation list */}
      <div className="w-80 border-r border-gray-200 flex flex-col shrink-0">
        <div className="px-4 py-3 border-b border-gray-100 bg-white">
          <h1 className="text-sm font-semibold text-gray-900">WhatsApp</h1>
          {isLoadingList && (
            <p className="text-xs text-gray-400 mt-0.5">Carregando...</p>
          )}
        </div>
        <ConversationList
          conversations={conversations}
          selectedPhone={selectedPhone}
          onSelectConversation={setSelectedPhone}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
        />
      </div>

      {/* Center column: Takeover bar + Message thread */}
      <div className="flex-1 flex flex-col min-w-0">
        <TakeoverBar
          phone={selectedPhone}
          status={selectedStatus}
          humanName={selectedHumanName}
        />
        <ConversationThread
          phone={selectedPhone}
          socket={socket}
          status={selectedStatus}
          humanName={selectedHumanName}
        />
      </div>

      {/* Right column: Patient sidebar */}
      {selectedPhone && (
        <div className="w-80 border-l border-gray-200 shrink-0">
          <PatientSidebar
            patientId={selectedPatientId}
            phone={selectedPhone}
          />
        </div>
      )}
    </div>
  );
}
