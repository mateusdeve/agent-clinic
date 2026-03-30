import { getSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Wrapper autenticado para chamadas a API FastAPI.
 * Injeta Bearer token do NextAuth session em todos os requests.
 * Levanta Error com detail da API em caso de resposta nao-ok.
 */
export async function apiFetch<T = unknown>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const session = await getSession();
  // NextAuth v5 beta: access_token fica no nivel da session (nao em session.user)
  // Ref: auth.ts session callback — s.access_token = token.access_token
  const token = (session as any)?.access_token;

  // Ensure path has trailing slash before query params to avoid 307 redirects
  // (FastAPI redirect_slashes drops Authorization header on redirect)
  const normalizedPath = path.replace(/^([^?#]*?)\/?(\?|#|$)/, "$1/$2");

  const res = await fetch(`${API_URL}${normalizedPath}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Erro de rede" }));
    const message =
      typeof error.detail === "string"
        ? error.detail
        : `HTTP ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}
