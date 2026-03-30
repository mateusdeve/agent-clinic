"use client";

import * as React from "react";
import { UserCheck, Bot, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { ConversationStatus } from "@/lib/types";

interface TakeoverBarProps {
  phone: string | null;
  status: ConversationStatus;
  humanName: string | null;
}

export function TakeoverBar({ phone, status, humanName }: TakeoverBarProps) {
  const [isLoading, setIsLoading] = React.useState(false);

  if (!phone) return null;

  async function handleTakeover() {
    if (!phone) return;
    setIsLoading(true);
    try {
      await apiFetch(`/api/conversations/${phone}/takeover`, { method: "POST" });
      // Status change arrives via Socket.IO conversation_updated event
    } catch (err) {
      console.error("[TakeoverBar] takeover error:", err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleHandback() {
    if (!phone) return;
    setIsLoading(true);
    try {
      await apiFetch(`/api/conversations/${phone}/handback`, { method: "POST" });
      // Status change arrives via Socket.IO conversation_updated event
    } catch (err) {
      console.error("[TakeoverBar] handback error:", err);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="h-12 px-4 flex items-center justify-between border-b border-gray-100 bg-white shrink-0">
      {/* Status badge */}
      <div className="flex items-center gap-2">
        {status === "ia_ativa" && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
            IA Ativa
          </span>
        )}
        {status === "humano" && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
            Atendimento Humano{humanName ? ` — ${humanName}` : ""}
          </span>
        )}
        {status === "resolvida" && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
            Resolvida
          </span>
        )}
      </div>

      {/* Action buttons */}
      <div>
        {status === "ia_ativa" && (
          <button
            onClick={handleTakeover}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <UserCheck className="w-3.5 h-3.5" />
            )}
            Assumir
          </button>
        )}
        {status === "humano" && (
          <button
            onClick={handleHandback}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Bot className="w-3.5 h-3.5" />
            )}
            Devolver para IA
          </button>
        )}
      </div>
    </div>
  );
}
