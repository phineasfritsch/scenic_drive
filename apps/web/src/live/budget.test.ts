import { describe, expect, it } from "vitest";
import { endGapKm, MAX_SUGGESTED_BUDGET, MIN_SUGGESTED_BUDGET, suggestedBudget } from "./budget";

const westwood: [number, number] = [-118.45, 34.06];

describe("suggestedBudget", () => {
  it("never goes below the floor for a short hop", () => {
    expect(suggestedBudget(westwood, [-118.44, 34.07])).toBe(MIN_SUGGESTED_BUDGET);
  });

  it("grows with the trip, in 5-minute steps", () => {
    const near = suggestedBudget(westwood, [-118.68, 34.03]); // Topanga-ish, ~21 km
    const far = suggestedBudget(westwood, [-118.81, 34.0]); // Point Dume-ish, ~34 km
    expect(far).toBeGreaterThan(near);
    expect(near % 5).toBe(0);
    expect(far % 5).toBe(0);
  });

  it("is capped for a long drive", () => {
    expect(suggestedBudget(westwood, [-117.2, 34.0])).toBe(MAX_SUGGESTED_BUDGET);
  });
});

describe("endGapKm", () => {
  it("is zero when the route ends on the place, and the distance otherwise", () => {
    expect(endGapKm([[-118.4, 34.0], [-118.5, 34.1]], [-118.5, 34.1])).toBe(0);
    expect(endGapKm([[-118.4, 34.0], [-118.5, 34.1]], [-118.5, 34.11])).toBeCloseTo(1.11, 1);
    expect(endGapKm([], [-118.5, 34.1])).toBe(0);
  });
});
