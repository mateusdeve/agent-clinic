"use client";

import * as React from "react";
import { format, parseISO } from "date-fns";
import { apiFetch } from "@/lib/api";
import type { ConversationMessage } from "@/lib/types";

interface WhatsAppTimelineProps {
  patientId: string;
}

export function WhatsAppTimeline({ patientId }: WhatsAppTimelineProps) {
  const [messages, setMessages] = React.useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiFetch<ConversationMessage[]>(
          `/api/patients/${patientId}/conversations`
        );
        if (!cancelled) {
          setMessages(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Erro ao carregar conversas"
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3 p-4 bg-gray-50 rounded-lg">
        {/* 3 skeleton bubbles alternando esquerda/direita */}
        {[false, true, false].map((isRight, i) => (
          <div
            key={i}
            className={`flex ${isRight ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`h-12 rounded-2xl animate-pulse bg-gray-300 ${
                isRight ? "rounded-br-sm" : "rounded-bl-sm"
              }`}
              style={{ width: isRight ? "55%" : "45%" }}
            />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex flex-col gap-3 p-4 bg-gray-50 rounded-lg min-h-[120px] items-center justify-center">
        <p className="text-sm text-gray-400">Nenhuma conversa registrada</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 p-4 bg-gray-50 rounded-lg">
      {messages.map((msg) => {
        const isUser = msg.role === "user";
        const timeStr = (() => {
          try {
            return format(parseISO(msg.created_at), "HH:mm");
          } catch {
            return "";
          }
        })();

        return (
          <div
            key={msg.id}
            className={`flex ${isUser ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] px-4 py-2.5 text-sm leading-relaxed ${
                isUser
                  ? // Paciente: bolha verde direita (WhatsApp user style)
                    "bg-green-500 text-white rounded-2xl rounded-br-sm"
                  : // Bot: bolha branca esquerda (WhatsApp assistant style)
                    "bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-bl-sm shadow-sm"
              }`}
            >
              <p className="whitespace-pre-wrap break-words">{msg.content}</p>
              {timeStr && (
                <p
                  className={`text-[10px] mt-1 text-right ${
                    isUser ? "text-green-100" : "text-gray-400"
                  }`}
                >
                  {timeStr}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
