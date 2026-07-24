import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { renderApp } from "../../test/renderApp";

const healthResponse = {
  status: "healthy",
  service: "NorseAI",
  version: "0.1.0",
  environment: "test",
};

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(healthResponse),
      }),
    );
  });

  it("renders live backend status and clearly marked unavailable cards", async () => {
    renderApp();

    expect(screen.getByRole("heading", { name: "Operations overview" })).toBeInTheDocument();
    expect(await screen.findByText("Connected")).toBeInTheDocument();
    expect(screen.getAllByText("Not connected")).toHaveLength(3);
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("AI chat is not connected")).toBeInTheDocument();
  });

  it("renders a skeleton while the health request is pending", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );
    renderApp();

    expect(screen.getByRole("article", { name: "Backend status loading" })).toBeInTheDocument();
  });

  it("renders an actionable error and retries health polling", async () => {
    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(healthResponse),
      });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    renderApp();

    expect(await screen.findByRole("alert")).toHaveTextContent("Backend connection unavailable");
    await user.click(screen.getByRole("button", { name: /retry/i }));

    await waitFor(() => expect(screen.getByText("Connected")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
