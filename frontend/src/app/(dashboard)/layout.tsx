import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { LogoutButton } from "./logout-button";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  // Defense in depth alongside proxy.ts (AUTH-05)
  if (!session) {
    redirect("/login");
  }

  const role = session.user.role;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header bar */}
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
        <span className="font-serif text-green-600 text-xl">MedIA</span>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-800">{session.user.name}</p>
            <p className="text-xs text-gray-400 capitalize">{role}</p>
          </div>
          <LogoutButton />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="hidden md:flex w-64 bg-white border-r border-gray-200 flex-col p-4 shrink-0">
          <nav className="flex flex-col gap-1">
            <a
              href="/home"
              className="px-3 py-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-50 text-sm font-medium transition-colors"
            >
              Inicio
            </a>
            <a
              href="/agenda"
              className="px-3 py-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-50 text-sm font-medium transition-colors"
            >
              Agenda
            </a>
            <a
              href="/pacientes"
              className="px-3 py-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-50 text-sm font-medium transition-colors"
            >
              Pacientes
            </a>

            {/* WhatsApp — admin and recepcionista only (AUTH-06) */}
            {(role === "admin" || role === "recepcionista") && (
              <a
                href="/whatsapp"
                className="px-3 py-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-50 text-sm font-medium transition-colors"
              >
                WhatsApp
              </a>
            )}

            {/* Admin-only links (AUTH-06) */}
            {role === "admin" && (
              <>
                <a
                  href="/medicos"
                  className="px-3 py-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-50 text-sm font-medium transition-colors"
                >
                  Medicos
                </a>
                <a
                  href="/usuarios"
                  className="px-3 py-2 rounded-md text-gray-600 hover:text-gray-800 hover:bg-gray-50 text-sm font-medium transition-colors"
                >
                  Usuarios
                </a>
              </>
            )}
          </nav>
        </aside>

        {/* Main content area */}
        <main className="flex-1 p-6 bg-off-white overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
