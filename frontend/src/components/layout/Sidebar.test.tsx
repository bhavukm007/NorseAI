import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { renderApp } from "../../test/renderApp";

describe("Sidebar navigation", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise(() => undefined)),
    );
  });

  it("navigates and exposes the active route with aria-current", async () => {
    const user = userEvent.setup();
    const { router } = renderApp();
    const chatLink = screen.getByRole("link", { name: "Chat" });

    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
    await user.click(chatLink);

    expect(router.state.location.pathname).toBe("/chat");
    expect(chatLink).toHaveAttribute("aria-current", "page");
  });

  it("opens the mobile drawer and closes it with Escape", async () => {
    const user = userEvent.setup();
    renderApp();
    const menu = screen.getByRole("button", { name: "Open navigation" });

    await user.click(menu);
    expect(menu).toHaveAttribute("aria-expanded", "true");
    expect(document.querySelector(".sidebar")).toHaveClass("mobile-open");
    expect(screen.getByRole("button", { name: "Close menu" })).toHaveFocus();

    await user.keyboard("{Escape}");
    expect(menu).toHaveAttribute("aria-expanded", "false");
    expect(document.querySelector(".sidebar")).not.toHaveClass("mobile-open");
    await waitFor(() => expect(menu).toHaveFocus());
  });
});
