import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ActivityFeed } from "./ActivityFeed";

describe("ActivityFeed", () => {
  it("shows an explicit unavailable state instead of fixture events", () => {
    render(<ActivityFeed />);

    expect(screen.getByRole("heading", { name: "Recent activity" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("No live activity data");
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });
});
