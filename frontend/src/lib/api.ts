const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let _accessToken: string | null = null;

/** Called by TokenProvider to inject the server-side token into client fetches. */
export function setAccessToken(token: string) {
  _accessToken = token;
}

/**
 * Wrapper autenticado para chamadas a API FastAPI.
 * Injeta Bearer token do TokenProvider em todos os requests.
 */
export async function apiFetch<T = unknown>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(_accessToken ? { Authorization: `Bearer ${_accessToken}` } : {}),
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
