/**
 * T-0334: the nothing_pretty offers become plans, through handlePlan - the shipping entry point.
 *
 * A1: the 422 names the budget that covers the back-roads ETA (R3), recomputed here from the recorded bytes.
 * A2: `back_roads` is whitelisted as the literal true only (P-PRIV-05). A3: a back-roads plan is ONE plan at
 * MAX_LAMBDA, checked against the budget it names like every plan (P-SAFE-04, P-COST-04).
 */
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import { handlePlan } from "../src/plan";
import { parsePlanRequest } from "../src/planRequest";
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
/** No lambda-8 recording exists for this pair (T-0332 R5): the fake answers lambda 8 with the recorded lambda-4 body. */
const WESTWOOD_MALIBU = recorded(fastestRaw, new Map([...FILES, [8, l4Raw]]));
const timeSeconds = (raw: string) => (JSON.parse(raw) as { paths: { time: number }[] }).paths[0]!.time / 1000;
const isBackRoads = (model: unknown) => JSON.stringify(model) === JSON.stringify(buildCustomModel(8, null));

async function send(router: Recording, extra: Record<string, unknown>) {
  const h = harness(router);
  const response = await handlePlan(planRequest({ ...SANTA_MONICA_TOPANGA_BODY, ...extra }), {}, h.deps);
  return { h, status: response.status, body: (await response.json()) as Record<string, unknown> };
}

/** Every searched route dull (2 of 10); the lambda-8 route pretty (8 of 10) and taking `backMs`. */
function dullWithBackRoads(backMs: number): Recording {
  const dull = curveRouter(1_200_000, (l) => 1_200_000 + Math.round(l * 30_000), [1, 2, 3], [7, 8, 9],
    { scenic_score: [[0, 3, 2]] });
  const back = curveRouter(1_200_000, () => backMs, [1, 2, 3], [7, 8, 9], { scenic_score: [[0, 3, 8]] });
  return { fastest: dull.fastest, scenic: (model) => (isBackRoads(model) ? back.scenic(model) : dull.scenic(model)) };
}

describe("POST /plan back-roads offer budget (T-0334 A1)", () => {
  it("westwood-malibu +25 names the whole minutes that cover the back-roads ETA", async () => {
    const { status, body } = await send(WESTWOOD_MALIBU, { budget_minutes: 25 });
    const back = timeSeconds(l4Raw);
    expect({ status, body }).toEqual({ status: 422, body: { error: "nothing_pretty", budget_minutes: 25,
      more_time_minutes: 65, back_roads_eta_s: back,
      back_roads_budget_minutes: Math.ceil((back - timeSeconds(fastestRaw)) / 60) } });
    expect(body.back_roads_budget_minutes).toBe(32);
  });

  const rows: [string, number, number | null][] = [
    ["a back-roads route a minute quicker than the fastest asks 0, never a negative budget", 1_200_000 - 60_000, 0],
    ["an extra of exactly 25 minutes asks 25", 1_200_000 + 25 * 60_000, 25],
    ["a millisecond above 25 minutes asks 26", 1_200_000 + 25 * 60_000 + 1, 26],
    ["an extra of exactly 180 minutes asks 180", 1_200_000 + 180 * 60_000, 180],
    ["a millisecond above 180 minutes asks nothing, the ETA still shown", 1_200_000 + 180 * 60_000 + 1, null],
  ];
  it.each(rows)("%s", async (_name, backMs, minutes) => {
    const { h, status, body } = await send(dullWithBackRoads(backMs), { budget_minutes: 0 });
    expect({ status, body }).toEqual({ status: 422, body: { error: "nothing_pretty", budget_minutes: 0,
      more_time_minutes: 40, back_roads_eta_s: backMs / 1000, back_roads_budget_minutes: minutes } });
    expect(h.reserved).toHaveLength(1);
  });
});

describe("POST /plan back_roads whitelist (T-0334 A2, P-PRIV-05)", () => {
  const refused: [string, unknown][] = [["false", false], ["1", 1], ["'true'", "true"], ["null", null],
    ["{}", {}], ["[]", []]];
  it.each(refused)("back_roads %s is 400 with zero upstream calls", async (_name, value) => {
    const { h, status, body } = await send(WESTWOOD_MALIBU, { back_roads: value });
    expect({ status, error: body.error }).toEqual({ status: 400, error: "invalid_request" });
    expect(h.sent).toHaveLength(0);
    expect(h.reserved).toHaveLength(0);
  });

  it("back_roads beside reroute is 400 with zero upstream calls", async () => {
    const { h, status, body } = await send(WESTWOOD_MALIBU, { back_roads: true,
      reroute: { token: "0123abcd-0123-4567-89ab-0123456789ab", first_pin: 0 } });
    expect({ status, error: body.error }).toEqual({ status: 400, error: "invalid_request" });
    expect(h.sent).toHaveLength(0);
  });

  it("parsePlanRequest reads back_roads absent as false and true as true, whole", () => {
    const base = { origin: { lat: 34.02, lon: -118.49 }, destinationPlace: "la:topanga", budgetMinutes: 25,
      departsAt: null, reroute: null };
    expect(parsePlanRequest(SANTA_MONICA_TOPANGA_BODY)).toEqual({ ok: true, request: { ...base, allBackRoads: false } });
    expect(parsePlanRequest({ ...SANTA_MONICA_TOPANGA_BODY, back_roads: true }))
      .toEqual({ ok: true, request: { ...base, allBackRoads: true } });
  });
});

describe("POST /plan all back roads (T-0334 A3, P-SAFE-04)", () => {
  it("westwood-malibu back roads at the offered 32 minutes is one lambda-8 plan inside the ceiling", async () => {
    const { h, status, body } = await send(WESTWOOD_MALIBU, { budget_minutes: 32, back_roads: true });
    const fastest = timeSeconds(fastestRaw);
    expect({ status, lambda: body.lambda, evaluations: body.evaluations, eta_s: body.eta_s,
      fastest_eta_s: body.fastest_eta_s, ceiling_s: body.ceiling_s, budget_s: body.budget_s }).toEqual({
      status: 200, lambda: 8, evaluations: 1, eta_s: timeSeconds(l4Raw), fastest_eta_s: fastest,
      ceiling_s: fastest + 32 * 60, budget_s: 32 * 60 });
    expect(timeSeconds(l4Raw)).toBeLessThanOrEqual(fastest + 32 * 60);
    expect(h.sent.map((s) => [s.body.profile, s.body.custom_model])).toEqual([
      ["car_fast", undefined], ["car_scenic", buildCustomModel(8, null)]]);
    expect(h.sent.length).toBeLessThanOrEqual(PLAN_UPSTREAM_COST);
    expect(h.reserved).toHaveLength(1);
  });

  it("westwood-malibu back roads at 31 minutes is ceiling_breached, never an over-ceiling 200", async () => {
    const { h, status, body } = await send(WESTWOOD_MALIBU, { budget_minutes: 31, back_roads: true });
    expect({ status, body }).toEqual({ status: 500, body: { error: "ceiling_breached" } });
    expect(h.reserved).toHaveLength(1);
  });
});
