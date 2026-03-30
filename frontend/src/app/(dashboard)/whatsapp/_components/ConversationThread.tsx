"use client";

import * as React from "react";
import { Send } from "lucide-react";
import { format, parseISO } from "date-fns";
import { apiFetch } from "@/lib/api";
import type { ConversationMessage, ConversationStatus, NewMessageEvent, TypingIndicatorEvent } from "@/lib/types";
import type { Socket } from "socket.io-client";

interface ConversationThreadProps {
  phone: string | null;
  socket: Socket | null;
  status: ConversationStatus;
  humanName: string | null;
}

function TypingDots() {
  return (
    <div className="flex justify-start">
      <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm shadow-sm px-4 py-3 flex items-center gap-1">
        <span
          className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
          style={{ animationDelay: "0ms" }}
        />
        <span
          className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
          style={{ animationDelay: "150ms" }}
        />
        <span
          className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
          style={{ animationDelay: "300ms" }}
        />
      </div>
    </div>
  );
}

function SkeletonBubbles() {
  return (
    <div className="flex flex-col gap-3 p-4">
      {[false, true, false, true].map((isRight, i) => (
        <div key={i} className={`flex ${isRight ? "justify-end" : "justify-start"}`}>
          <div
            className={`h-12 rounded-2xl animate-pulse bg-gray-200 ${
              isRight ? "rounded-br-sm" : "rounded-bl-sm"
            }`}
            style={{ width: isRight ? "55%" : "45%" }}
          />
        </div>
      ))}
    </div>
  );
}

export function ConversationThread({
  phone,
  socket,
  status,
  humanName,
}: ConversationThreadProps) {
  const [messages, setMessages] = React.useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [newText, setNewText] = React.useState("");
  const [isTyping, setIsTyping] = React.useState(false);
  const [isSending, setIsSending] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const typingTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load messages when phone changes
  React.useEffect(() => {
    if (!phone) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    async function loadMessages() {
      setIsLoading(true);
      try {
        const data = await apiFetch<ConversationMessage[]>(
          `/api/conversations/${phone}/messages`
        );
        if (!cancelled) setMessages(data);
      } catch (err) {
        console.error("[ConversationThread] load messages error:", err);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    loadMessages();
    return () => { cancelled = true; };
  }, [phone]);

  // Join/leave conversation room on Socket.IO
  React.useEffect(() => {
    if (!socket || !phone) return;
    socket.emit("join_conversation", { phone });
    return () => {
      socket.emit("leave_conversation", { phone });
    };
  }, [socket, phone]);

  // Socket.IO listeners for new messages and typing indicator
  React.useEffect(() => {
    if (!socket || !phone) return;

    function onNewMessage(event: NewMessageEvent) {
      if (event.phone !== phone) return;
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random()}`,
          role: event.role,
          content: event.content,
          created_at: event.created_at,
          // @ts-ignore — sent_by_human is extra metadata
          sent_by_human: event.sent_by_human,
        } as ConversationMessage & { sent_by_human?: boolean },
      ]);
    }

    function onTypingIndicator(event: TypingIndicatorEvent) {
      if (event.phone !== phone) return;
      setIsTyping(event.is_typing);

      // Auto-clear after 15 seconds as safety fallback (D-02)
      if (event.is_typing) {
        if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
        typingTimerRef.current = setTimeout(() => setIsTyping(false), 15000);
      } else {
        if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
      }
    }

    socket.on("new_message", onNewMessage);
    socket.on("typing_indicator", onTypingIndicator);

    return () => {
      socket.off("new_message", onNewMessage);
      socket.off("typing_indicator", onTypingIndicator);
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    };
  }, [socket, phone]);

  // Auto-scroll to bottom on new messages or typing change
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  async function handleSend() {
    if (!phone || !newText.trim() || isSending || status !== "humano") return;
    const text = newText.trim();
    setNewText("");
    setIsSending(true);
    try {
      await apiFetch(`/api/conversations/${phone}/send`, {
        method: "POST",
        body: JSON.stringify({ text }),
      });
      // Message appears via Socket.IO broadcast (D-13 optimistic UI via server echo)
    } catch (err) {
      console.error("[ConversationThread] send error:", err);
      // Restore text on error
      setNewText(text);
    } finally {
      setIsSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  if (!phone) {
    return (
      <div className="flex-1 flex items-center justify-center text-sm text-gray-400 bg-gray-50">
        Selecione uma conversa
      </div>
    );
  }

  const sendDisabled = status !== "humano";

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        {isLoading ? (
          <SkeletonBubbles />
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-sm text-gray-400">
            Nenhuma mensagem ainda
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === "user";
            const sentByHuman = (msg as any).sent_by_human;
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
                      ? "bg-green-500 text-white rounded-2xl rounded-br-sm"
                      : "bg-white border border-gray-200 text-gray-800 rounded-2xl rounded-bl-sm shadow-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                  <div className={`flex items-center justify-end gap-1.5 mt-1`}>
                    {timeStr && (
                      <p
                        className={`text-[10px] ${
                          isUser ? "text-green-100" : "text-gray-400"
                        }`}
                      >
                        {timeStr}
                      </p>
                    )}
                    {sentByHuman && (
                      <p className="text-[10px] text-orange-300 font-medium">
                        Humano
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}

        {/* Typing indicator */}
        {isTyping && <TypingDots />}

        {/* Auto-scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Send bar */}
      <div
        className={`border-t border-gray-200 bg-white p-3 flex gap-2 items-end shrink-0 ${
          sendDisabled ? "opacity-60" : ""
        }`}
      >
        <textarea
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sendDisabled || isSending}
          rows={1}
          placeholder={
            sendDisabled
              ? "Assuma o controle para enviar mensagens"
              : "Digite uma mensagem..."
          }
          className="flex-1 resize-none px-3 py-2 text-sm border border-gray-200 rounded-lg outline-none focus:border-green-400 focus:ring-1 focus:ring-green-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors max-h-32 overflow-y-auto"
        />
        <button
          onClick={handleSend}
          disabled={sendDisabled || isSending || !newText.trim()}
          className="p-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
