/**
 * T-0248 R7: src/lambdaSearch.ts is a port of Sources/ScenicKit/Budget/LambdaSearch.swift. These pin the
 * port's arithmetic to the Swift type's documented behaviour with exact expected values typed out here.
 */
import { describe, expect, it } from "vitest";
import { BudgetError, searchLambda, searchLambdaAlongside, violatesMonotonicity } from "../src/lambdaSearch";

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

/** A seeded generator, so a failing row is reproducible from its seed. */
function lcg(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 2 ** 32;
  };
}

type Answer = number | "reject";

/** Row `seed` as a function of the seed: fastest, budget, cap and a per-lambda answer table (lambdas snap to the
 *  bisection lattice, so one lambda always gets one answer); rare rows carry nonsense, rejections or bad inputs. */
function row(seed: number) {
  const random = lcg(seed);
  const pick = <T>(xs: T[]) => xs[Math.floor(random() * xs.length)]!;
  const fastest = random() < 0.08 ? pick([0, -5, Number.NaN, Number.POSITIVE_INFINITY]) : 600 + Math.floor(random() * 1200);
  const budget = random() < 0.08 ? pick([-1, Number.NaN, Number.POSITIVE_INFINITY]) : pick([0, Math.floor(random() * 2400)]);
  const cap = Math.floor(random() * 11);
  const fastestRejects = random() < 0.04;
  const shape = pick(["monotone", "non-monotone", "step", "flat"]);
  const knots = Array.from({ length: 9 }, () => Math.floor(random() * 3000));
  const bad = new Map<number, Answer>();
  for (let k = 0; k < 2; k += 1) {
    if (random() < 0.15) bad.set(pick([0, 4, 2, 6, 3, 1, 7]), pick<Answer>([Number.NaN, -1, "reject"]));
  }
  const curve = (lambda: number): Answer => {
    if (bad.has(lambda)) return bad.get(lambda)!;
    const base = Number.isFinite(fastest) && fastest > 0 ? fastest : 1000;
    if (shape === "monotone") return base + lambda * 120;
    if (shape === "step") return lambda >= 4 ? base + 5000 : base + lambda * 50;
    if (shape === "flat") return base + 300;
    return base + knots[Math.min(8, Math.floor(lambda))]! - 900;
  };
  return { fastest, budget, cap, fastestRejects, curve };
}

/** One refusal per lambda, so which request's failure surfaced is visible to toEqual. */
const refused = (lambda: number) => new Error(`router refused lambda ${lambda}`);
const FASTEST_REFUSED = new Error("fastest refused");

/** The whole result of one search: its outcome, or the BudgetError's reason AND message, or the rejection itself. */
async function whole(run: () => Promise<unknown>) {
  try {
    return { outcome: await run() };
  } catch (error) {
    return error instanceof BudgetError ? { reason: error.reason, message: error.message } : { rejected: error };
  }
}

describe("searchLambdaAlongside - searchLambda's samples two in flight (T-0403 acceptance 3)", () => {
  it("over 400 generated rows: the whole result equal, the same set of lambdas, evaluations <= the cap, <= 2 in flight", async () => {
    let succeeded = 0;
    for (let seed = 1; seed <= 400; seed += 1) {
      const r = row(seed);
      const seqVisited: number[] = [];
      const seq = r.fastestRejects ? { rejected: FASTEST_REFUSED } : await whole(() => searchLambda(r.fastest, r.budget, async (l) => {
        seqVisited.push(l);
        const a = r.curve(l);
        if (a === "reject") throw refused(l);
        return a;
      }, r.cap));

      const visited: number[] = [];
      let inFlight = 0;
      let peak = 0;
      const tick = async () => {
        inFlight += 1;
        peak = Math.max(peak, inFlight);
        await new Promise((done) => setTimeout(done, 0));
        inFlight -= 1;
      };
      const fastest = (async () => {
        await tick();
        if (r.fastestRejects) throw FASTEST_REFUSED;
        return r.fastest;
      })();
      const got = await whole(() => searchLambdaAlongside(fastest, r.budget, async (l) => {
        visited.push(l);
        await tick();
        const a = r.curve(l);
        if (a === "reject") throw refused(l);
        return a;
      }, r.cap));

      expect({ seed, result: got }).toEqual({ seed, result: seq });
      expect({ seed, peak: peak <= 2 }).toEqual({ seed, peak: true });
      expect(new Set(visited).size).toBe(visited.length);
      if ("outcome" in seq) {
        succeeded += 1;
        expect({ seed, set: [...visited].sort((a, b) => a - b) }).toEqual({ seed, set: [...seqVisited].sort((a, b) => a - b) });
      } else {
        expect(seqVisited.every((l) => visited.includes(l))).toBe(true);
        expect(visited.length).toBeLessThanOrEqual(seqVisited.length + 2);
      }
      expect(visited.length).toBeLessThanOrEqual(Math.max(1, r.cap));
    }
    expect(succeeded).toBeGreaterThan(150);
  });

  it("every pair of failing requests among the first three surfaces searchLambda's error, never the other one", async () => {
    const kinds: Answer[] = [Number.NaN, -1, "reject"];
    let rows = 0;
    for (const a of [0, 4, 6, 2]) {
      for (const b of [0, 4, 6, 2]) {
        for (const kindA of kinds) {
          for (const kindB of kinds) {
            if (a === b) continue;
            const curve = (l: number): Answer => (l === a ? kindA : l === b ? kindB : 1000 + l * 10);
            const answer = async (l: number) => {
              const x = curve(l);
              if (x === "reject") throw refused(l);
              return x;
            };
            const seq = await whole(() => searchLambda(1000, 600, answer));
            const got = await whole(() => searchLambdaAlongside(Promise.resolve(1000), 600, answer));
            expect({ a, b, kindA, kindB, got }).toEqual({ a, b, kindA, kindB, got: seq });
            rows += 1;
          }
        }
      }
    }
    expect(rows).toBe(108);
  });

  it("the first midpoint runs alongside the fastest and lambda 0 alongside the second: 4, then 0 and 6, then 7, 7.5, 7.75", async () => {
    const visited: number[] = [];
    const outcome = await searchLambdaAlongside(Promise.resolve(1000), 600, async (l) => {
      visited.push(l);
      return 1000 + l * 10;
    });
    expect(visited).toEqual([4, 0, 6, 7, 7.5, 7.75]);
    expect(outcome).toEqual({ lambda: 7.75, duration: 1077.5, ceiling: 1600, evaluations: 6, usedBudget: false,
      monotonicityViolated: false });
  });
});
