import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ToastProvider } from "./ToastProvider";
import { useToast } from "./toast";

function ToastTrigger() {
  const { notify } = useToast();
  return (
    <button
      onClick={() =>
        notify({ title: "Policy saved", message: "Changes applied.", type: "success" })
      }
    >
      Notify
    </button>
  );
}

describe("ToastProvider", () => {
  it("announces and dismisses a typed notification", async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>,
    );

    await user.click(screen.getByRole("button", { name: "Notify" }));
    expect(screen.getByRole("status")).toHaveTextContent("Policy saved");
    expect(screen.getByRole("status")).toHaveTextContent("Changes applied.");

    await user.click(screen.getByRole("button", { name: "Dismiss notification" }));
    expect(screen.queryByText("Policy saved")).not.toBeInTheDocument();
  });
});
