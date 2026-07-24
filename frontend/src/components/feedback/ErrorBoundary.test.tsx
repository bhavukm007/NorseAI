import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ErrorBoundary } from "./ErrorBoundary";

function BrokenView(): never {
  throw new Error("sensitive exception detail");
}

describe("ErrorBoundary", () => {
  it("shows a friendly recovery action without exposing exception details", () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    render(
      <ErrorBoundary>
        <BrokenView />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("heading", { name: "Something interrupted this view" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Reload workspace" })).toBeEnabled();
    expect(screen.queryByText("sensitive exception detail")).not.toBeInTheDocument();
  });
});
