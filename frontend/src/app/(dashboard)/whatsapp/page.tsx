import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { InboxPanel } from "./_components/InboxPanel";

export default async function WhatsAppPage() {
  const session = await auth();

  if (!session) {
    redirect("/login");
  }

  // Medico role cannot access WhatsApp panel (WPP access requires admin or recepcionista)
  const role = (session as any)?.user?.role;
  if (role === "medico") {
    redirect("/home");
  }

  return <InboxPanel />;
}
