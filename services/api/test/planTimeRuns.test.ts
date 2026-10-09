/**
 * T-0342 R1-R3: every /plan request asks the router for `time`, and the 200 - a fresh plan AND a reroute's - carries
 * `time_runs`, the shipped route's details=time runs as {from, to, ms}, exactly when they tile route.coordinates edge
 * for edge in whole non-negative milliseconds with some time; anything else omits the field and the plan is still
 * answered. Every case drives `handlePlan`; every answer is compared WHOLE to its recomputation: the same plan's body
 * without the detail, plus the runs the row expects.
 */
import { describe, expect, it } from "vitest";
import { handlePlan } from "../src/plan";
import { kvPlanTokens, type PlanTokenKv } from "../src/planToken";
import { curveRouter, harness, planRequest, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const FAST_WAYS = [1, 2, 3, 4, 5];
const SCENIC_WAYS = [1, 10, 11, 12, 13, 14]; // seven coordinates: vertices 0..6
const DETAILS = ["scenic_score", "road_class", "osm_way_id", "surface", "road_access", "time"];
const TOKEN = "0f1e2d3c-4b5a-4968-8776-655443322110";
const PINS = [{ lat: 34.03, lon: -118.52 }, { lat: 34.04, lon: -118.56 }];
const RECORD = { device: "device-1", place: "la:topanga", pins: PINS, lambda: 7.75 };

type Run = { from: number; to: number; ms: number };
type Variant = "fresh" | "reroute";
const VARIANTS: Variant[] = ["fresh", "reroute"];

const per = (ms: (i: number) => unknown) => Array.from({ length: 6 }, (_, i) => [i, i + 1, ms(i)]);
const whole = (runs: unknown[][]): Run[] => runs.map(([from, to, ms]) => ({ from, to, ms }) as Run);

/** [name, the scenic paths' `time` detail (undefined: none sent), the answer's time_runs (null: omitted)]. */
const ROWS: [string, unknown[][] | undefined, Run[] | null][] = [
  ["no time detail", undefined, null],
  ["one run per edge", per((i) => 100_000 + i), whole(per((i) => 100_000 + i))],
  ["one run over the route", [[0, 6, 1_100_000]], [{ from: 0, to: 6, ms: 1_100_000 }]],
  ["uneven runs, one of them zero", [[0, 2, 300_000], [2, 3, 0], [3, 6, 800_000]],
    [{ from: 0, to: 2, ms: 300_000 }, { from: 2, to: 3, ms: 0 }, { from: 3, to: 6, ms: 800_000 }]],
  ["ms 2^53 - 1", [[0, 6, 2 ** 53 - 1]], [{ from: 0, to: 6, ms: 2 ** 53 - 1 }]],
  ["empty", [], null],
  ["the first from 1", [[1, 6, 5]], null],
  ["the first from -1", [[-1, 6, 5]], null],
  ["a gap", [[0, 2, 5], [3, 6, 5]], null],
  ["an overlap", [[0, 3, 5], [2, 6, 5]], null],
  ["to equal to from", [[0, 0, 5], [0, 6, 5]], null],
  ["to below from", [[0, 3, 5], [3, 2, 5], [2, 6, 5]], null],
  ["ends one vertex short", [[0, 5, 5]], null],
  ["ends one vertex past", [[0, 7, 5]], null],
  ["a negative ms", per((i) => (i === 2 ? -1 : 1000)), null],
  ["every ms zero", per(() => 0), null],
  ["a fractional ms", per((i) => (i === 1 ? 1000.5 : 1000)), null],
  ["a string ms", per((i) => (i === 1 ? "1000" : 1000)), null],
  ["a null ms", per((i) => (i === 1 ? null : 1000)), null],
  ["ms 2^53", [[0, 6, 2 ** 53]], null],
];

function plansKv(): PlanTokenKv {
  const rows: Record<string, string> = { [`plan:device-1:${TOKEN}`]: JSON.stringify(RECORD) };
  return { async get(key) { return rows[key] ?? null; }, async put(key, value) { rows[key] = value; } };
}

async function answer(variant: Variant, time: unknown[][] | undefined) {
  const extra = time === undefined ? {} : { time };
  const h = harness(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, SCENIC_WAYS, extra));
  let minted = 0;
  if (variant === "reroute") (h.deps as { plans?: unknown }).plans = kvPlanTokens(plansKv(), () => `00000000-0000-4000-8000-00000000000${++minted}`);
  const body = variant === "fresh" ? SANTA_MONICA_TOPANGA_BODY : { ...SANTA_MONICA_TOPANGA_BODY, reroute: { token: TOKEN, first_pin: 0 } };
  const response = await handlePlan(planRequest(body), {}, h.deps);
  return { status: response.status, body: (await response.json()) as Record<string, unknown>, sent: h.sent };
}

describe("POST /plan answers carry the shipped route's time runs (T-0342)", () => {
  for (const variant of VARIANTS) {
    it(`${variant}: every row's 200 equals the plan without the detail plus the row's time_runs, whole`, async () => {
      const base = await answer(variant, undefined);
      expect([base.status, "time_runs" in base.body, base.body.continued]).toEqual([200, false, variant === "reroute"]);
      for (const [name, time, runs] of ROWS) {
        const got = await answer(variant, time);
        const expected = runs === null ? base.body : { ...base.body, time_runs: runs };
        expect([name, got.status, got.body]).toStrictEqual([name, 200, expected]);
        expect([name, got.sent.map((s) => s.body.details)]).toEqual([name, got.sent.map(() => DETAILS)]);
      }
    });
  }

  it("meta: four rows keep the runs, sixteen omit them, and no two kept rows expect the same runs", () => {
    const kept = ROWS.filter(([, , runs]) => runs !== null);
    expect([kept.length, ROWS.length - kept.length]).toEqual([4, 16]);
    expect(new Set(kept.map(([, , runs]) => JSON.stringify(runs))).size).toBe(4);
  });
});
