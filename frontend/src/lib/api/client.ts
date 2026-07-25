const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
const TOKEN_KEY = "norseai.operator.session";

export interface StoredSession {
  accessToken: string;
  expiresAt: string;
  username: string;
  role: string;
}

export function loadSession(): StoredSession | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(TOKEN_KEY) ?? "null") as StoredSession | null;
    if (!value?.accessToken || new Date(value.expiresAt).getTime() <= Date.now()) {
      sessionStorage.removeItem(TOKEN_KEY);
      return null;
    }
    return value;
  } catch {
    sessionStorage.removeItem(TOKEN_KEY);
    return null;
  }
}

export function saveSession(session: StoredSession | null) {
  if (session) sessionStorage.setItem(TOKEN_KEY, JSON.stringify(session));
  else sessionStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event("norse:session"));
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = loadSession();
  const response = await fetch(`${apiBaseUrl}/${path.replace(/^\//, "")}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(session ? { Authorization: `Bearer ${session.accessToken}` } : {}),
      ...init.headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401 && path !== "auth/login") saveSession(null);
    let message =
      response.status >= 500
        ? "The service is temporarily unavailable."
        : "The request could not be completed.";
    try {
      const body = (await response.json()) as { error?: { message?: string } };
      if (body.error?.message) message = body.error.message;
    } catch {
      // Some gateways return an empty or non-JSON error response.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function downloadAudit(format: "csv" | "jsonl") {
  const session = loadSession();
  const response = await fetch(`${apiBaseUrl}/audit-logs/export?format=${format}`, {
    headers: session ? { Authorization: `Bearer ${session.accessToken}` } : {},
  });
  if (!response.ok) throw new ApiError("Audit export failed.", response.status);
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `norseai-audit.${format === "csv" ? "csv" : "jsonl"}`;
  anchor.click();
  URL.revokeObjectURL(url);
}
