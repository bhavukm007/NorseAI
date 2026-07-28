import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthProvider";
import { LoginPage } from "../auth/LoginPage";
import { AgentsPage } from "./AgentsPage";
import { AuditPage } from "./AuditPage";
import { BudgetsPage } from "./BudgetsPage";
import { EmergencyPage } from "./EmergencyPage";
import { FinancialActionsPage } from "./FinancialActionsPage";
import { FleetsPage } from "./FleetsPage";
import { OrganizationsPage } from "./OrganizationsPage";
import { PoliciesPage } from "./PoliciesPage";

function renderPage(page: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{page}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("operator governance pages", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve(String(input).includes("/overview") ? { reserved_spend: "10.00" } : []),
        }),
      ),
    );
  });

  it.each([
    [<AgentsPage />, "Financial agents"],
    [<OrganizationsPage />, "Organizations"],
    [<FleetsPage />, "Financial agent fleets"],
    [<PoliciesPage />, "Policy management"],
    [<BudgetsPage />, "Budget management"],
    [<EmergencyPage />, "Emergency control center"],
    [<FinancialActionsPage />, "Financial actions"],
  ])("renders the live management surface", (page, heading) => {
    renderPage(page);
    expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
  });

  it("exposes every required audit filter", () => {
    renderPage(<AuditPage />);
    expect(screen.getByLabelText("Filter actor")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter fleet")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter organization")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter policy")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter action")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter result")).toBeInTheDocument();
  });

  it("renders operator authentication controls", () => {
    localStorage.clear();
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Govern financial agents" })).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });
});
