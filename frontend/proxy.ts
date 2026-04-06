import { auth } from "@/lib/auth";

export const proxy = auth((req) => {
  const { pathname } = req.nextUrl;

  // Skip API and static routes (defense-in-depth alongside matcher)
  if (pathname.startsWith("/api/") || pathname.startsWith("/_next/")) {
    return;
  }

  // Protected routes: everything under (dashboard) group
  const isProtected =
    pathname.startsWith("/home") ||
    pathname.startsWith("/agenda") ||
    pathname.startsWith("/pacientes") ||
    pathname.startsWith("/medicos") ||
    pathname.startsWith("/whatsapp") ||
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/usuarios");

  // Unauthenticated trying to access protected route -> login (AUTH-05)
  if (!req.auth && isProtected) {
    return Response.redirect(new URL("/login", req.nextUrl.origin));
  }

  // Authenticated visiting login -> dashboard (D-09)
  if (req.auth && pathname === "/login") {
    return Response.redirect(new URL("/home", req.nextUrl.origin));
  }
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
