import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useSystemHealth } from "./useSystemHealth";

describe("useSystemHealth", () => {
  afterEach(() => vi.useRealTimers());

  it("reports connection state, service version, and latency", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ status: "healthy", service: "NorseAI", version: "0.1.0" }),
      }),
    );

    const { result } = renderHook(() => useSystemHealth());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeNull();
    expect(result.current.health).toMatchObject({
      connected: true,
      service: "NorseAI",
      version: "0.1.0",
    });
    expect(result.current.health.latency).toEqual(expect.any(Number));
    expect(result.current.health.lastSync).toBeInstanceOf(Date);
  });

  it("reports failures and supports manual retry", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: "healthy", service: "NorseAI", version: "0.1.0" }),
      });
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useSystemHealth());

    await waitFor(() => expect(result.current.error).toBe("Unable to reach the backend."));
    await act(async () => result.current.refresh());

    expect(result.current.health.connected).toBe(true);
    expect(result.current.error).toBeNull();
  });
});
