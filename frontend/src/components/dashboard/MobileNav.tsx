"use client";

import { useState } from "react";
import { Menu, X } from "lucide-react";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

interface MobileNavProps {
  role: string;
}

interface NavLink {
  href: string;
  label: string;
}

function getNavLinks(role: string): NavLink[] {
  const links: NavLink[] = [
    { href: "/home", label: "Inicio" },
    { href: "/agenda", label: "Agenda" },
    { href: "/pacientes", label: "Pacientes" },
  ];

  if (role === "admin" || role === "recepcionista") {
    links.push({ href: "/whatsapp", label: "WhatsApp" });
  }

  if (role === "admin") {
    links.push(
      { href: "/medicos", label: "Medicos" },
      { href: "/usuarios", label: "Usuarios" },
      { href: "/templates", label: "Templates" },
      { href: "/campanhas", label: "Campanhas" }
    );
  }

  return links;
}

export function MobileNav({ role }: MobileNavProps) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  const links = getNavLinks(role);

  return (
    <>
      {/* Hamburger button — visible only below md breakpoint */}
      <button
        className="md:hidden p-2 text-gray-600 hover:text-gray-800"
        onClick={() => setOpen(true)}
        aria-label="Abrir menu"
      >
        <Menu className="size-5" />
      </button>

      {/* Backdrop overlay — always in DOM, opacity toggled */}
      <div
        className={clsx(
          "fixed inset-0 z-40 md:hidden transition-opacity duration-300",
          open
            ? "bg-black/40 opacity-100"
            : "opacity-0 pointer-events-none"
        )}
        onClick={() => setOpen(false)}
      />

      {/* Drawer panel — always in DOM, translate toggled */}
      <div
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out md:hidden",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Drawer header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
          <span className="font-serif text-green-600 text-xl">MedIA</span>
          <button
            className="p-1 text-gray-600 hover:text-gray-800"
            onClick={() => setOpen(false)}
            aria-label="Fechar menu"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex flex-col gap-1 p-4">
          {links.map((link) => {
            const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
            return (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={clsx(
                  "px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-green-50 text-green-700"
                    : "text-gray-600 hover:text-gray-800 hover:bg-gray-50"
                )}
              >
                {link.label}
              </a>
            );
          })}
        </nav>
      </div>
    </>
  );
}
