const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, "");

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
  const response = await fetch(`${apiBaseUrl}/${path.replace(/^\//, "")}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

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
  return (await response.json()) as T;
}
