import { describe, expect, it } from "vitest";

import { assessSystem } from "./assessment";
import { demoSystems } from "./demoSystems";

describe("assessSystem", () => {
  it("flags consequential systems without human oversight", () => {
    const result = assessSystem(
      demoSystems.find((item) => item.systemName === "Hiring Assistant")!,
    );

    expect(result.riskScore).toBeGreaterThanOrEqual(45);
    expect(result.rules).toContainEqual(
      expect.objectContaining({ name: "Meaningful human oversight", status: "Failed" }),
    );
    expect(result.recommendations.some((item) => item.priority === "Critical")).toBe(true);
  });

  it("returns complete category and compliance data", () => {
    const result = assessSystem(demoSystems[4]);

    expect(Object.keys(result.categories)).toHaveLength(6);
    expect(result.compliance).toBeGreaterThan(0);
    expect(result.compliance).toBeLessThanOrEqual(100);
    expect(result.rules).toHaveLength(6);
  });
});
