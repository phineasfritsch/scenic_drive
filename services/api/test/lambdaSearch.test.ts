/**
 * T-0248 R7: src/lambdaSearch.ts is a port of Sources/ScenicKit/Budget/LambdaSearch.swift. These pin the
 * port's arithmetic to the Swift type's documented behaviour with exact expected values typed out here.
 */
import { describe, expect, it } from "vitest";
import { BudgetError, searchLambda, violatesMonotonicity } from "../src/lambdaSearch";

async function run(fastest: number, budget: number, curve: (l: number) => number, max?: number) {
  const visited: number[] = [];
  const outcome = await searchLambda(fastest, budget, async (l) => {
    visited.push(l);
    return curve(l);
  }, max);
  return { outcome, visited };
}

describe("searchLambda - the LambdaSearch port", () => {
  it("bisects [0, 8] up to 6 evaluations when every lambda fits", async () => {
    const { outcome, visited } = await run(1000, 600, (l) => 1000 + l * 10);
    expect(visited).toEqual([0, 4, 6, 7, 7.5, 7.75]);
    expect(outcome).toEqual({ lambda: 7.75, duration: 1077.5, ceiling: 1600, evaluations: 6, usedBudget: false,
      monotonicityViolated: false });
  });

  it("honours maxEvaluations, and never fewer than one", async () => {
    expect((await run(1000, 600, () => 1000, 3)).visited).toEqual([0, 4, 6]);
    expect((await run(1000, 600, () => 1000, 0)).visited).toEqual([0]);
    expect((await run(1000, 600, () => 1000, 10)).visited).toHaveLength(9);
  });

  it("stops when the bracket is within the 0.05 tolerance", async () => {
    // 0, 4, 6, 7, 7.5, 7.75, 7.875, 7.9375, 7.96875: the next width would be 0.03125 < 0.05.
    expect((await run(1000, 600, () => 1000, 50)).visited).toEqual([0, 4, 6, 7, 7.5, 7.75, 7.875, 7.9375, 7.96875]);
  });

  it("keeps the longest feasible duration, not the last one measured", async () => {
    const { outcome } = await run(1000, 600, (l) => (l === 4 ? 1500 : l === 6 ? 1200 : l > 4 ? 2000 : 1100));
    expect(outcome.lambda).toBe(4);
    expect(outcome.duration).toBe(1500);
    // A tie on duration goes to the larger lambda: the flat curve's answer is the last lambda measured.
    expect((await run(1000, 600, () => 1000)).outcome.lambda).toBe(7.75);
  });

  it("flags non-monotone curves and still returns only measured feasible lambdas", async () => {
    const { outcome } = await run(1000, 600, (l) => (l === 4 ? 1590 : l === 6 ? 1200 : 1800));
    expect(outcome.monotonicityViolated).toBe(true);
    expect(outcome.lambda).toBe(4);
    expect(outcome.duration).toBe(1590);
  });

  it("usedBudget is d >= fastest + 0.5 * budget, and true for a zero budget", async () => {
    expect((await run(1000, 600, () => 1300)).outcome.usedBudget).toBe(true);
    expect((await run(1000, 600, () => 1299.999)).outcome.usedBudget).toBe(false);
    expect((await run(1000, 0, () => 1000)).outcome.usedBudget).toBe(true);
    expect((await run(1000, 0, () => 999)).outcome.usedBudget).toBe(true);
  });

  it("refuses a non-positive or non-finite fastest, a negative budget, and a nonsense duration", async () => {
    await expect(searchLambda(0, 600, async () => 1)).rejects.toMatchObject({ reason: "not_a_duration" });
    await expect(searchLambda(Number.NaN, 600, async () => 1)).rejects.toBeInstanceOf(BudgetError);
    await expect(searchLambda(1000, -1, async () => 1)).rejects.toMatchObject({ reason: "not_a_budget" });
    await expect(searchLambda(1000, Number.POSITIVE_INFINITY, async () => 1)).rejects.toMatchObject({ reason: "not_a_budget" });
    await expect(searchLambda(1000, 600, async () => -1)).rejects.toMatchObject({ reason: "router_nonsense" });
    await expect(searchLambda(1000, 600, async () => Number.NaN)).rejects.toMatchObject({ reason: "router_nonsense" });
  });

  it("with nothing feasible it refuses no_feasible_lambda rather than returning an overshoot", async () => {
    await expect(searchLambda(1000, 600, async () => 1601)).rejects.toMatchObject({ reason: "no_feasible_lambda" });
  });

  it("violatesMonotonicity compares every pair, not consecutive samples", () => {
    expect(violatesMonotonicity([{ lambda: 0, duration: 10 }, { lambda: 8, duration: 20 }, { lambda: 4, duration: 9 }]))
      .toBe(true);
    expect(violatesMonotonicity([{ lambda: 0, duration: 10 }, { lambda: 4, duration: 10 }, { lambda: 8, duration: 20 }]))
      .toBe(false);
  });
});
