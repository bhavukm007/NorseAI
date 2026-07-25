import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { renderApp } from "../../test/renderApp";

const overview = {
  active_agents: 4,
  active_fleets: 2,
  active_policies: 3,
  emergency_fleets: 0,
  budget_limit: "1000.00",
  settled_spend: "250.00",
  reserved_spend: "0.00",
  recent_decisions: [],
  recent_audits: [],
};

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve(
              url.includes("/overview")
                ? overview
                : { status: "healthy", service: "NorseAI", version: "0.1.0" },
            ),
        });
      }),
    );
  });

  it("renders live operator governance metrics", async () => {
    renderApp();

    expect(screen.getByRole("heading", { name: "Operator control center" })).toBeInTheDocument();
    expect(await screen.findByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("25%")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /AI Assessment Lab/i })).toHaveLength(2);
  });

  it("renders loading status while live requests are pending", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );
    renderApp();

    expect(screen.getByRole("article", { name: "System health loading" })).toBeInTheDocument();
  });
});
