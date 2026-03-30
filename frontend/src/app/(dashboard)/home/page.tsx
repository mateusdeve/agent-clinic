import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { DashboardClient } from "@/components/dashboard/DashboardClient";

export default async function HomePage() {
  const session = await auth();
  const role = session?.user?.role;

  // Per D-04: Medico redirected to /agenda
  if (role === "medico") {
    redirect("/agenda");
  }

  return (
    <div>
      <h1 className="font-serif text-2xl text-gray-800 mb-6">Dashboard</h1>
      <DashboardClient role={role || ""} />
    </div>
  );
}
