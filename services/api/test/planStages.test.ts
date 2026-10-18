/**
 * T-0411: where /plan's time goes, per stage, over the recorded fixtures - and the rounds each answer takes now.
 *
 * A router whose every request takes T ms on a virtual clock (timedRouter.ts) times each row. Every request is
 * labelled by its stage - `fast` (car_fast), `search` (a scenic lambda the bisection records), `spec` (a scenic
 * lambda it does not), `offer` (the nothing_pretty back-roads route at lambda 8 outside an all-back-roads plan) - and
 * the Worker-side reads the handler awaits in series (D1 place, KV closures, identity, quota read, quota reserve) are
 * counted. The table is printed so the task Log can quote it.
 *
 * Acceptance: each row's WHOLE answer (status, length, sha256 of the exact text) equals GOLDEN, captured from main
 * 311aefaf's src before any src change; each row answers in exactly ROUNDS[row] rounds; never more than 2 requests in
 * flight (P-COST-04); never more than PLAN_UPSTREAM_COST requests.
 */
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import { handlePlan } from "../src/plan";
import { PLAN_UPSTREAM_COST } from "../src/quota";
import { curveRouter, harness, planRequest, recorded, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY,
  type Recording } from "./planHarness";
import { timedRouter } from "./timedRouter";
import wwFastest from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/fastest.json?raw";
import ww0 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-0.json?raw";
import ww4 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-4.json?raw";
import ww6 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-6.json?raw";
import ww7 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-7.json?raw";
import ww75 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-7.5.json?raw";
import ww775 from "../../../Tests/Fixtures/t0221/westwood-woodland-hills/lambda-7.75.json?raw";
import wmFastest from "../../../Tests/Fixtures/t0221/westwood-malibu/fastest.json?raw";
import wm0 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-0.json?raw";
import wm2 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-2.json?raw";
import wm3 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.json?raw";
import wm325 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.25.json?raw";
import wm35 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.5.json?raw";
import wm4 from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-4.json?raw";

const WOODLAND_HILLS = recorded(wwFastest, new Map([[0, ww0], [4, ww4], [6, ww6], [7, ww7], [7.5, ww75], [7.75, ww775]]));
/** As planSchedule: no lambda-8 recording exists, so lambda 8 answers the recorded lambda-4 body. */
const MALIBU = recorded(wmFastest, new Map([[0, wm0], [2, wm2], [3, wm3], [3.25, wm325], [3.5, wm35], [4, wm4], [8, wm4]]));
const FAST_WAYS = [1, 2, 3, 4, 5];
const SCENIC_WAYS = [1, 10, 11, 12, 13, 14];
/** A dull scenic middle: one scenic_score run of 0 over the whole path, so RouteScore is below 0.45. */
const DULL = { scenic_score: [[0, SCENIC_WAYS.length, 0]] };

const plan = (minutes: number, extra: Record<string, unknown> = {}) => ({ ...SANTA_MONICA_TOPANGA_BODY, budget_minutes: minutes, ...extra });

interface Row {
  name: string;
  router: Recording;
  body: Record<string, unknown>;
  /** The lambdas the search records, in no order - every other scenic request is a spec or the offer. */
  searched: number[];
}

const ROWS: Row[] = [
  { name: "santa-monica-topanga +25 (200)", router: SANTA_MONICA_TOPANGA, body: plan(25), searched: [0, 4, 6, 7, 7.5, 7.75] },
  { name: "westwood-woodland-hills +25 (200)", router: WOODLAND_HILLS, body: plan(25), searched: [0, 4, 6, 7, 7.5, 7.75] },
  { name: "westwood-malibu +25 (422 nothing_pretty)", router: MALIBU, body: plan(25), searched: [0, 4, 2, 3, 3.5, 3.25] },
  { name: "every scenic route on the fastest's ways (422 no_scenic_alternative)",
    router: curveRouter(1_000_000, (l) => 1_000_000 + l * 60_000, FAST_WAYS, FAST_WAYS), body: plan(25),
    searched: [0, 4, 6, 7, 7.5, 7.75] },
  { name: "every scenic route overshoots (502)", router: curveRouter(1_000_000, () => 1_000_000 + 25 * 60_000 + 1, FAST_WAYS, SCENIC_WAYS),
    body: plan(25), searched: [0, 4, 2, 1, 0.5, 0.25] },
  { name: "dull at every lambda (422 nothing_pretty, no offer)",
    router: curveRouter(1_000_000, (l) => 1_000_000 + l * 60_000, FAST_WAYS, SCENIC_WAYS, DULL), body: plan(25),
    searched: [0, 4, 6, 7, 7.5, 7.75] },
  { name: "westwood-malibu back roads 32 (200)", router: MALIBU, body: plan(32, { back_roads: true }), searched: [8] },
  { name: "dull back roads 40 (422 nothing_pretty)",
    router: curveRouter(1_000_000, (l) => 1_000_000 + l * 60_000, FAST_WAYS, SCENIC_WAYS, DULL), body: plan(40, { back_roads: true }),
    searched: [8] },
];

/** Captured from main 311aefaf's src (T-0403's schedule), before any src change - quoted in the task Log. */
const GOLDEN: Record<string, { status: number; length: number; sha256: string }> = {
  "santa-monica-topanga +25 (200)": { status: 200, length: 17016, sha256: "4aef4e516b779603df39ccbec0a86ff3ebbb2e8039c564b7b2e09f5194deab9a" },
  "westwood-woodland-hills +25 (200)": { status: 200, length: 18835, sha256: "5ca7b072c771d5ce1794074963fa74638db7557672372633789b278dc24dbe8d" },
  "westwood-malibu +25 (422 nothing_pretty)": { status: 422, length: 127, sha256: "0715a41dca92e98be08d963e29d6f6a1e995aa923bff5acf0ebe1f6c8d066300" },
  "every scenic route on the fastest's ways (422 no_scenic_alternative)": { status: 422, length: 33, sha256: "abd9c85d4bcb5af181b8c23705c13bf0875a1b0a529dc6587e9a236c49fe53b1" },
  "every scenic route overshoots (502)": { status: 502, length: 118, sha256: "a5de0ac7046d669f99db8df12363c3f70f868b496754ec2fcf36018071b91f7b" },
  "dull at every lambda (422 nothing_pretty, no offer)": { status: 422, length: 126, sha256: "b27b187d1cc4c78a8ef41a44f303a0cc16ac1ca11f179f9686ccd339802b0972" },
  "westwood-malibu back roads 32 (200)": { status: 200, length: 45085, sha256: "e8dd87bcd7dcfbb2cd88b4fb0dbd89063295e78652b3c7d3fde3cbb1a83ff9e7" },
  "dull back roads 40 (422 nothing_pretty)": { status: 422, length: 126, sha256: "f6ea0cffe8aa71ba698c3c38822c87a449feba150c823369a9ff020397b9d19a" },
};

/** The rounds (T each) every row answers in - asserted exactly, so a slower schedule and a faster one are both seen. */
const ROUNDS: Record<string, number> = {
  "santa-monica-topanga +25 (200)": 4,
  "westwood-woodland-hills +25 (200)": 4,
  "westwood-malibu +25 (422 nothing_pretty)": 5,
  "every scenic route on the fastest's ways (422 no_scenic_alternative)": 4,
  "every scenic route overshoots (502)": 5,
  "dull at every lambda (422 nothing_pretty, no offer)": 5,
  "westwood-malibu back roads 32 (200)": 1,
  "dull back roads 40 (422 nothing_pretty)": 1,
};

const T = 100;

async function sha256(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const LATTICE = [0, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.25, 3.5, 3.75, 4, 5, 6, 6.5, 7, 7.5, 7.75, 7.875, 8];

async function measureRow(row: Row) {
  const h = harness(row.router);
  const reads: string[] = [];
  const wrap = <A extends unknown[], R>(label: string, f: (...a: A) => R) => (...a: A): R => {
    reads.push(label);
    return f(...a);
  };
  h.deps.resolvePlace = wrap("d1-place", h.deps.resolvePlace);
  h.deps.closures = wrap("kv-closures", h.deps.closures);
  h.deps.identify = wrap("identify", h.deps.identify);
  const counters = h.deps.upstream.counters;
  h.deps.upstream.counters = { read: wrap("quota-read", counters.read), reserve: wrap("quota-reserve", counters.reserve) };
  const timed = timedRouter(h, T);
  const { value, wall } = await timed.drive(async () => {
    const response = await handlePlan(planRequest(row.body), {}, h.deps);
    return { status: response.status, text: await response.text() };
  });
  const back = row.body.back_roads === true;
  const lambdaOf = (model: unknown) => LATTICE.find((l) => JSON.stringify(model) === JSON.stringify(buildCustomModel(l, null)));
  const labels = h.sent.map((s) => {
    if (s.body.profile === "car_fast") return "fast";
    const l = lambdaOf(s.body.custom_model);
    if (l === 8 && !back) return "offer@8";
    return `${l !== undefined && row.searched.includes(l) ? "search" : "spec"}@${l}`;
  });
  const starts = timed.calls.map((c) => c.start / T);
  return { status: value.status, length: value.text.length, sha256: await sha256(value.text), rounds: wall / T,
    requests: h.sent.length, peak: timed.peakInFlight(), reads, schedule: labels.map((l, i) => `r${starts[i]! + 1}:${l}`) };
}

describe("POST /plan per stage over the recorded fixtures (T-0411)", () => {
  it("prints the attribution table", async () => {
    const lines: string[] = [];
    for (const row of ROWS) {
      const m = await measureRow(row);
      lines.push(`T0411 ${row.name}: status=${m.status} rounds=${m.rounds} requests=${m.requests} peak=${m.peak} ` +
        `serial-reads=${m.reads.length}[${m.reads.join(",")}] sha256=${m.sha256} length=${m.length}`);
      lines.push(`T0411   ${m.schedule.join(" ")}`);
    }
    console.log(lines.join("\n"));
    expect(lines).toHaveLength(2 * ROWS.length);
  });

  it("GOLDEN and ROUNDS hold exactly the rows of the table", () => {
    expect(Object.keys(GOLDEN).sort()).toEqual(ROWS.map((r) => r.name).sort());
    expect(Object.keys(ROUNDS).sort()).toEqual(ROWS.map((r) => r.name).sort());
  });

  for (const row of ROWS) {
    it(`${row.name}: the whole answer byte-equal, in exactly its rounds, <= 2 in flight, <= the plan budget`, async () => {
      const m = await measureRow(row);
      expect({ [row.name]: { status: m.status, length: m.length, sha256: m.sha256, rounds: m.rounds, peak: m.peak <= 2,
        budget: m.requests <= PLAN_UPSTREAM_COST } })
        .toEqual({ [row.name]: { ...GOLDEN[row.name], rounds: ROUNDS[row.name], peak: true, budget: true } });
    });
  }
});
