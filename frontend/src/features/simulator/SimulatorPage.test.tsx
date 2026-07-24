import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { SimulatorPage } from "./SimulatorPage";

describe("SimulatorPage", () => {
  beforeEach(() => localStorage.clear());

  it("populates the submission from a demo system", async () => {
    const user = userEvent.setup();
    render(<SimulatorPage />);

    await user.click(screen.getByRole("button", { name: /Healthcare Diagnostic AI/i }));

    expect(screen.getByLabelText("AI system name")).toHaveValue("Healthcare Diagnostic AI");
    expect(screen.getByLabelText("Organization name")).toHaveValue("Northstar Health");
    expect(screen.getByRole("group", { name: "Sensitive data" })).toBeInTheDocument();
  });

  it("shows validation errors for an empty assessment", async () => {
    render(<SimulatorPage />);

    fireEvent.click(screen.getByRole("button", { name: /Run assessment/i }));

    expect(await screen.findByText("Enter the AI system name")).toBeInTheDocument();
  });
});
