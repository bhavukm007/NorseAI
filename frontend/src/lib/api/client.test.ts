import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiRequest, loadSession, saveSession } from "./client";

describe("authenticated API client", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("restores an expired access session when a refresh token remains available", () => {
    saveSession({
      accessToken: "expired-access",
      refreshToken: "persistent-refresh-token",
      expiresAt: new Date(0).toISOString(),
      username: "operator",
      role: "operator",
    });

    expect(loadSession()?.refreshToken).toBe("persistent-refresh-token");
  });

  it("rotates the refresh token and retries one time after a 401", async () => {
    saveSession({
      accessToken: "expired-access",
      refreshToken: "first-refresh-token",
      expiresAt: new Date(0).toISOString(),
      username: "operator",
      role: "operator",
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response("{}", { status: 401 }))
      .mockResolvedValueOnce(
        Response.json({
          access_token: "new-access",
          refresh_token: "rotated-refresh-token",
          expires_at: new Date(Date.now() + 60_000).toISOString(),
          username: "operator",
          role: "operator",
        }),
      )
      .mockResolvedValueOnce(Response.json({ active_agents: 2 }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiRequest<{ active_agents: number }>("overview");

    expect(result.active_agents).toBe(2);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(loadSession()?.accessToken).toBe("new-access");
    expect(loadSession()?.refreshToken).toBe("rotated-refresh-token");
  });

  it("clears the session when refresh fails", async () => {
    saveSession({
      accessToken: "expired-access",
      refreshToken: "expired-refresh-token",
      expiresAt: new Date(0).toISOString(),
      username: "operator",
      role: "operator",
    });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response("{}", { status: 401 }))
        .mockResolvedValueOnce(new Response("{}", { status: 401 })),
    );

    await expect(apiRequest("overview")).rejects.toThrow("Your session has expired.");
    expect(loadSession()).toBeNull();
  });
});
