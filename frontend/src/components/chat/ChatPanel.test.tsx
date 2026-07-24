import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChatPanel } from "./ChatPanel";

describe("ChatPanel", () => {
  it("disables messaging until the backend exists", () => {
    render(<ChatPanel />);

    expect(screen.getByText("AI chat is not connected")).toBeInTheDocument();
    expect(screen.getByLabelText("Message Norse assistant")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
    expect(screen.getByText("Phase 04")).toBeInTheDocument();
  });
});
