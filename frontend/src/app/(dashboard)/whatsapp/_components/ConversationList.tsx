"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { formatDistanceToNow, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";
import type { ConversationSummary, ConversationStatus } from "@/lib/types";

type FilterOption = "todas" | ConversationStatus;

interface ConversationListProps {
  conversations: ConversationSummary[];
  selectedPhone: string | null;
  onSelectConversation: (phone: string) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  activeFilter: FilterOption;
  onFilterChange: (filter: FilterOption) => void;
}

const FILTER_TABS: { label: string; value: FilterOption }[] = [
  { label: "Todas", value: "todas" },
  { label: "IA Ativa", value: "ia_ativa" },
  { label: "Humano", value: "humano" },
  { label: "Resolvida", value: "resolvida" },
];

function StatusBadge({ status }: { status: ConversationStatus }) {
  if (status === "ia_ativa") {
    return (
      <span className="flex items-center gap-1 text-xs text-green-700">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
        IA
      </span>
    );
  }
  if (status === "humano") {
    return (
      <span className="flex items-center gap-1 text-xs text-orange-700">
        <span className="w-1.5 h-1.5 rounded-full bg-orange-500 shrink-0" />
        Humano
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 text-xs text-gray-500">
      <span className="w-1.5 h-1.5 rounded-full bg-gray-400 shrink-0" />
      Resolvida
    </span>
  );
}

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return "";
  try {
    return formatDistanceToNow(parseISO(isoString), {
      addSuffix: false,
      locale: ptBR,
    });
  } catch {
    return "";
  }
}

export function ConversationList({
  conversations,
  selectedPhone,
  onSelectConversation,
  searchQuery,
  onSearchChange,
  activeFilter,
  onFilterChange,
}: ConversationListProps) {
  // Client-side filter by status
  const filtered = conversations.filter((conv) => {
    if (activeFilter !== "todas" && conv.status !== activeFilter) return false;
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Search */}
      <div className="p-3 border-b border-gray-100">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar por nome ou telefone..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg outline-none focus:border-green-400 focus:ring-1 focus:ring-green-200 transition-colors"
          />
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex border-b border-gray-100 px-2">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onFilterChange(tab.value)}
            className={`px-3 py-2 text-xs font-medium transition-colors whitespace-nowrap ${
              activeFilter === tab.value
                ? "text-green-700 border-b-2 border-green-600"
                : "text-gray-500 hover:text-gray-700 border-b-2 border-transparent"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-sm text-gray-400">
            Nenhuma conversa encontrada
          </div>
        ) : (
          filtered.map((conv) => (
            <button
              key={conv.phone}
              onClick={() => onSelectConversation(conv.phone)}
              className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
                selectedPhone === conv.phone ? "bg-green-50 hover:bg-green-50" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-0.5">
                <span className="text-sm font-medium text-gray-900 truncate">
                  {conv.patient_nome || conv.phone}
                </span>
                <span className="text-[10px] text-gray-400 shrink-0">
                  {formatRelativeTime(conv.last_message_at)}
                </span>
              </div>
              <p className="text-xs text-gray-500 truncate mb-1">
                {conv.last_message_preview || "Sem mensagens"}
              </p>
              <div className="flex items-center justify-between">
                <StatusBadge status={conv.status} />
                {conv.status === "humano" && conv.human_name && (
                  <span className="text-[10px] text-orange-600 truncate max-w-[100px]">
                    {conv.human_name}
                  </span>
                )}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
