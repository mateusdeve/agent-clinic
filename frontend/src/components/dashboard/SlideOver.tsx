"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface SlideOverProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function SlideOver({ open, onClose, title, children }: SlideOverProps) {
  // Fecha com Escape
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        aria-hidden="true"
        onClick={onClose}
        className={cn(
          "fixed inset-0 bg-black/40 z-40 transition-opacity duration-200",
          open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
      />

      {/* Painel lateral */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={cn(
          "fixed right-0 top-0 h-full w-full max-w-md bg-white z-50 shadow-2xl",
          "flex flex-col",
          "transition-transform duration-300 ease-in-out",
          open ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-green-600">
          <h2 className="font-serif text-lg font-semibold text-white">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Fechar painel"
            className="text-white hover:text-green-100 transition-colors rounded-md p-1 focus:outline-none focus:ring-2 focus:ring-white/50"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Corpo com scroll */}
        <div
          className="flex-1 overflow-y-auto p-6"
          style={{ maxHeight: "calc(100vh - 64px)" }}
        >
          {children}
        </div>
      </div>
    </>
  );
}
