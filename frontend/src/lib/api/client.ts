const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");
const TOKEN_KEY = "norseai.operator.session";

export interface StoredSession {
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
  username: string;
  role: string;
}

export function loadSession(): StoredSession | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(TOKEN_KEY) ?? "null") as StoredSession | null;
    if (!value?.accessToken || !value.refreshToken) {
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

interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  expires_at: string;
  username: string;
  role: string;
}

let refreshRequest: Promise<StoredSession> | null = null;

async function refreshSession(session: StoredSession): Promise<StoredSession> {
  if (!refreshRequest) {
    refreshRequest = fetch(`${apiBaseUrl}/auth/refresh`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: session.refreshToken }),
    })
      .then(async (response) => {
        if (!response.ok) throw new ApiError("Your session has expired.", response.status);
        const result = (await response.json()) as RefreshResponse;
        const next = {
          accessToken: result.access_token,
          refreshToken: result.refresh_token,
          expiresAt: result.expires_at,
          username: result.username,
          role: result.role,
        };
        saveSession(next);
        return next;
      })
      .catch((error) => {
        saveSession(null);
        throw error;
      })
      .finally(() => {
        refreshRequest = null;
      });
  }
  return refreshRequest;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
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

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const request = (session: StoredSession | null) =>
    fetch(`${apiBaseUrl}/${path.replace(/^\//, "")}`, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(session ? { Authorization: `Bearer ${session.accessToken}` } : {}),
        ...init.headers,
      },
    });
  const session = loadSession();
  let response = await request(session);
  const canRefresh =
    response.status === 401 && session && path !== "auth/login" && path !== "auth/refresh";
  if (canRefresh) {
    const refreshed = await refreshSession(session);
    response = await request(refreshed);
  }
  if (response.status === 401 && path !== "auth/login") saveSession(null);
  return parseResponse<T>(response);
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
