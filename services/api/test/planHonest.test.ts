/**
 * T-0332 A3/A4/A5: /plan says so when nothing pretty is reachable, through handlePlan - the shipping entry point.
 *
 * A3 is the population the Brief names: the recorded t0221 westwood-malibu pair at +25 chooses lambda 3.25, a route
 * RouteScore puts at 0.226 (half of it PCH trunk at score 0). Before T-0332 the Worker answered it 200 as scenic.
 * Every expected body here is the WHOLE body, recomputed in the test from the recorded bytes.
 */
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import { handlePlan } from "../src/plan";
import { PLAN_UPSTREAM_COST } from "../src/quota";
import { curveRouter, harness, planRequest, recorded, SANTA_MONICA_TOPANGA_BODY, type Recording } from "./planHarness";
import fastestRaw from "../../../Tests/Fixtures/t0221/westwood-malibu/fastest.json?raw";
import l0Raw from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-0.json?raw";
import l2Raw from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-2.json?raw";
import l3Raw from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.json?raw";
import l325Raw from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.25.json?raw";
import l35Raw from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-3.5.json?raw";
import l4Raw from "../../../Tests/Fixtures/t0221/westwood-malibu/lambda-4.json?raw";

const FILES: [number, string][] = [[0, l0Raw], [2, l2Raw], [3, l3Raw], [3.25, l325Raw], [3.5, l35Raw], [4, l4Raw]];
/** No lambda-8 recording exists for this pair (R5): the fake answers lambda 8 with the recorded lambda-4 body. */
const WESTWOOD_MALIBU = recorded(fastestRaw, new Map([...FILES, [8, l4Raw]]));
const timeSeconds = (raw: string) => (JSON.parse(raw) as { paths: { time: number }[] }).paths[0]!.time / 1000;

async function send(router: Recording, budget: number) {
  const h = harness(router);
  const response = await handlePlan(planRequest({ ...SANTA_MONICA_TOPANGA_BODY, budget_minutes: budget }), {}, h.deps);
  return { h, status: response.status, body: (await response.json()) as Record<string, unknown> };
}

const isBackRoads = (model: unknown) => JSON.stringify(model) === JSON.stringify(buildCustomModel(8, null));

/** A dull chosen route (every scenic answer scored 2 of 10) with the lambda-8 answer scored `backRoads`. */
function dullWith(backRoads: Record<string, unknown[]> | "refused"): Recording {
  const dull = curveRouter(1_200_000, (l) => 1_200_000 + Math.round(l * 30_000), [1, 2, 3], [7, 8, 9],
    { scenic_score: [[0, 3, 2]] });
  const back = backRoads === "refused" ? null
    : curveRouter(1_200_000, (l) => 1_200_000 + Math.round(l * 30_000), [1, 2, 3], [7, 8, 9], backRoads);
  return {
    fastest: dull.fastest,
    scenic: (model) => (isBackRoads(model) ? back?.scenic(model) : dull.scenic(model)),
  };
}
const BACK_ROADS_S = (1_200_000 + 8 * 30_000) / 1000;

describe("POST /plan honest failure (T-0332 A3, P-SAFE-04)", () => {
  it("westwood-malibu +25 (RouteScore 0.226) answers nothing_pretty with both offers, never a 200 route", async () => {
    const { h, status, body } = await send(WESTWOOD_MALIBU, 25);
    expect({ status, body }).toEqual({ status: 422, body: {
      error: "nothing_pretty", budget_minutes: 25, more_time_minutes: 65, back_roads_eta_s: timeSeconds(l4Raw),
      back_roads_budget_minutes: Math.ceil((timeSeconds(l4Raw) - timeSeconds(fastestRaw)) / 60) } });
    expect(h.sent.length).toBeLessThanOrEqual(PLAN_UPSTREAM_COST);
    expect(h.sent.filter((s) => isBackRoads(s.body.custom_model))).toHaveLength(1);
    expect(h.reserved).toHaveLength(1);
  });
});

describe("POST /plan honest-failure offers (T-0332 A4/A5)", () => {
  const scored = { scenic_score: [[0, 3, 8]] };
  const rows: [string, number, Recording, unknown][] = [
    ["budget 140 offers exactly 180", 140, dullWith(scored), { more: 180, back: BACK_ROADS_S }],
    ["the next double above 140 offers no more time", 140 + 2 ** -45, dullWith(scored), { more: null, back: BACK_ROADS_S }],
    ["budget 180 offers no more time", 180, dullWith(scored), { more: null, back: BACK_ROADS_S }],
    ["a dull back-roads route is not offered", 25, dullWith({ scenic_score: [[0, 3, 2]] }), { more: 65, back: null }],
    ["an unscored back-roads route is not offered", 25, dullWith({ scenic_score: [] }), { more: 65, back: null }],
    ["a refused back-roads request is no offer, not a failed answer", 25, dullWith("refused"), { more: 65, back: null }],
  ];
  it.each(rows)("%s", async (_name, budget, router, expected) => {
    const { more, back } = expected as { more: number | null; back: number | null };
    const { h, status, body } = await send(router, budget);
    expect({ status, body }).toEqual({ status: 422, body: {
      error: "nothing_pretty", budget_minutes: budget, more_time_minutes: more, back_roads_eta_s: back,
      back_roads_budget_minutes: back === null ? null : Math.ceil((back - 1_200) / 60) } });
    const backRoads = h.sent.filter((s) => s.body.profile === "car_scenic" && isBackRoads(s.body.custom_model));
    expect(backRoads).toHaveLength(1);
    expect(h.sent.length).toBeLessThanOrEqual(PLAN_UPSTREAM_COST);
    expect(h.reserved).toHaveLength(1);
  });

  it("a chosen route with no scenic_score detail is an honest failure, never a 200 (R3, fail closed)", async () => {
    const unscored = curveRouter(1_200_000, (l) => 1_200_000 + Math.round(l * 30_000), [1, 2, 3], [7, 8, 9],
      { scenic_score: [] });
    const { status, body } = await send(unscored, 25);
    expect({ status, body }).toEqual({ status: 422, body: {
      error: "nothing_pretty", budget_minutes: 25, more_time_minutes: 65, back_roads_eta_s: null,
      back_roads_budget_minutes: null } });
  });

  it("a pretty chosen route still answers 200 (the default synthetic score is 8)", async () => {
    const pretty = curveRouter(1_200_000, (l) => 1_200_000 + Math.round(l * 30_000), [1, 2, 3], [7, 8, 9]);
    const { status } = await send(pretty, 25);
    expect(status).toBe(200);
  });
});
