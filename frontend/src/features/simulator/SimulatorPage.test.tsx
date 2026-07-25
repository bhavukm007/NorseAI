import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { SimulatorPage } from "./SimulatorPage";

describe("SimulatorPage", () => {
  beforeEach(() => localStorage.clear());

  const renderSimulator = (path = "/assessment-lab") =>
    render(
      <MemoryRouter initialEntries={[path]}>
        <SimulatorPage />
      </MemoryRouter>,
    );

  it("populates the submission from a demo system", async () => {
    const user = userEvent.setup();
    renderSimulator();

    await user.click(screen.getByRole("button", { name: /Healthcare Diagnostic AI/i }));

    expect(screen.getByLabelText("AI system name")).toHaveValue("Healthcare Diagnostic AI");
    expect(screen.getByLabelText("Organization name")).toHaveValue("Northstar Health");
    expect(screen.getByRole("group", { name: "Sensitive data" })).toBeInTheDocument();
  });

  it("shows validation errors for an empty assessment", async () => {
    renderSimulator();

    fireEvent.click(screen.getByRole("button", { name: /Run assessment/i }));

    expect(await screen.findByText("Enter the AI system name")).toBeInTheDocument();
  });

  it("starts the complete judge demo with one action", async () => {
    const user = userEvent.setup();
    renderSimulator();

    await user.click(screen.getByRole("button", { name: /Run judge demo/i }));

    expect(
      screen.getByRole("heading", { name: /Evaluating Healthcare Diagnostic AI/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Assessment in progress")).toBeInTheDocument();
  });
});
