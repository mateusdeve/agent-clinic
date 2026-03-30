import { auth } from "@/lib/auth";

export default async function HomePage() {
  const session = await auth();
  const role = session?.user?.role;

  return (
    <div>
      <h1 className="font-serif text-2xl text-gray-800 mb-6">
        Bem-vindo, {session?.user?.name}
      </h1>

      {/* Role-adaptive content — D-09 */}
      {role === "admin" && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-4">
          <h2 className="font-medium text-gray-800 mb-2">Painel Administrativo</h2>
          <p className="text-gray-600">KPIs e gestao completa — Phase 5</p>
        </div>
      )}

      {role === "medico" && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-4">
          <h2 className="font-medium text-gray-800 mb-2">Sua Agenda</h2>
          <p className="text-gray-600">Consultas do dia — Phase 3</p>
        </div>
      )}

      {(role === "recepcionista" || role === "admin") && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-4">
          <h2 className="font-medium text-gray-800 mb-2">Recepcao</h2>
          <p className="text-gray-600">Agendamentos e pacientes — Phase 3</p>
        </div>
      )}
    </div>
  );
}
