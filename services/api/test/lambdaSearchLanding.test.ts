/**
 * T-0411 pre-review M3: searchLambdaAlongside sends each lambda at most once WHATEVER order its requests land in.
 * lambdaSearch.test.ts's 400-row oracle lands every request one timer hop after it starts, so the fastest always
 * lands before a guess and a guess is never re-proposed while the bisection stands still. Here every generated
 * row runs under every landing order (the cross product), each delay a function of the row's seed and the lambda.
 */
import { describe, expect, it } from "vitest";
import { BudgetError, searchLambda, searchLambdaAlongside } from "../src/lambdaSearch";

/** A seeded generator, so a failing row is reproducible from its seed. */
function lcg(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 2 ** 32;
  };
}

type Answer = number | "reject";

/** Row `seed`: fastest, budget, cap and a per-lambda answer table; rare rows carry nonsense or rejections. */
function row(seed: number) {
  const random = lcg(seed);
  const pick = <T>(xs: T[]) => xs[Math.floor(random() * xs.length)]!;
  const fastest = 600 + Math.floor(random() * 1200);
  const budget = pick([0, Math.floor(random() * 2400)]);
  const cap = Math.floor(random() * 11);
  const shape = pick(["monotone", "non-monotone", "step", "flat"]);
  const knots = Array.from({ length: 9 }, () => Math.floor(random() * 3000));
  const bad = new Map<number, Answer>();
  if (random() < 0.15) bad.set(pick([0, 4, 2, 6, 3, 1, 7]), pick<Answer>([Number.NaN, -1, "reject"]));
  const curve = (lambda: number): Answer => {
    if (bad.has(lambda)) return bad.get(lambda)!;
    if (shape === "monotone") return fastest + lambda * 120;
    if (shape === "step") return lambda >= 4 ? fastest + 5000 : fastest + lambda * 50;
    if (shape === "flat") return fastest + 300;
    return fastest + knots[Math.min(8, Math.floor(lambda))]! - 900;
  };
  return { fastest, budget, cap, curve };
}

/** A landing order: the fastest's delay and each lambda's delay, in timer hops, as functions of the seed. */
type Landing = { name: string; fastest: (seed: number) => number; measure: (seed: number, lambda: number) => number };
const LANDINGS: Landing[] = [
  { name: "together", fastest: () => 1, measure: () => 1 },
  { name: "fastest-first", fastest: () => 0, measure: () => 1 },
  { name: "fastest-late", fastest: () => 12, measure: () => 1 },
  { name: "fastest-last", fastest: () => 40, measure: () => 1 },
  { name: "jitter", fastest: (seed) => Math.floor(lcg(seed * 7919)() * 13),
    measure: (seed, lambda) => Math.floor(lcg(seed * 104729 + Math.round(lambda * 256))() * 7) },
];

const hops = async (n: number) => {
  for (let i = 0; i < n; i += 1) await new Promise((done) => setTimeout(done, 0));
};
const refused = (lambda: number) => new Error(`router refused lambda ${lambda}`);

async function whole(run: () => Promise<unknown>) {
  try {
    return { outcome: await run() };
  } catch (error) {
    return error instanceof BudgetError ? { reason: error.reason, message: error.message } : { rejected: error };
  }
}

/** One row under one landing order: the result, every lambda sent in order, the peak in flight, and how many
 *  requests went out after lambda 0 while the fastest was still outstanding. */
async function alongside(seed: number, landing: Landing) {
  const r = row(seed);
  const sent: number[] = [];
  let inFlight = 0;
  let peak = 0;
  let fastestLanded = false;
  let beforeFastest = 0;
  const start = () => {
    inFlight += 1;
    peak = Math.max(peak, inFlight);
  };
  start();
  const fastest = (async () => {
    await hops(landing.fastest(seed));
    inFlight -= 1;
    fastestLanded = true;
    return r.fastest;
  })();
  const result = await whole(() => searchLambdaAlongside(fastest, r.budget, async (l) => {
    if (!fastestLanded && sent.includes(0)) beforeFastest += 1;
    sent.push(l);
    start();
    await hops(landing.measure(seed, l));
    inFlight -= 1;
    const a = r.curve(l);
    if (a === "reject") throw refused(l);
    return a;
  }, r.cap));
  await fastest;
  return { result, sent, peak, beforeFastest };
}

async function sequential(seed: number) {
  const r = row(seed);
  return whole(() => searchLambda(r.fastest, r.budget, async (l) => {
    const a = r.curve(l);
    if (a === "reject") throw refused(l);
    return a;
  }, r.cap));
}

describe("searchLambdaAlongside - each lambda sent once under every landing order (T-0411 M3)", () => {
  it("200 generated rows x 5 landing orders: no lambda sent twice, the whole result equal, <= 2 in flight", async () => {
    let raced = 0;
    for (let seed = 1; seed <= 200; seed += 1) {
      const seq = await sequential(seed);
      for (const landing of LANDINGS) {
        const got = await alongside(seed, landing);
        const twice = got.sent.filter((l, i) => got.sent.indexOf(l) !== i);
        expect({ seed, landing: landing.name, twice, peak: got.peak <= 2, result: got.result })
          .toEqual({ seed, landing: landing.name, twice: [], peak: true, result: seq });
        if (got.beforeFastest > 0) raced += 1;
      }
    }
    // The cross product reaches the case M3 needs: a request after lambda 0 while the fastest is still out.
    expect(raced).toBeGreaterThan(300);
  });

  it("the guess at 6 that lands before a late fastest is not re-sent: exactly 4, 0, 6, 7, 7.5, 7.75", async () => {
    let fastestLanded = false;
    const fastest = (async () => {
      await hops(12);
      fastestLanded = true;
      return 1000;
    })();
    const sent: [number, boolean][] = [];
    const outcome = await searchLambdaAlongside(fastest, 600, async (l) => {
      sent.push([l, fastestLanded]);
      await hops(1);
      return 1000 + l * 10;
    });
    expect(sent).toEqual([[4, false], [0, false], [6, false], [7, true], [7.5, true], [7.75, true]]);
    expect(outcome).toEqual({ lambda: 7.75, duration: 1077.5, ceiling: 1600, evaluations: 6, usedBudget: false,
      monotonicityViolated: false });
  });
});
