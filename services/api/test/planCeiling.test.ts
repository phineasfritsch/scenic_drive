/**
 * T-0248 R7 (P-SAFE-04): the extra-time budget is a CEILING on the returned route's real ETA. Always.
 *
 * Driven through `handlePlan` over synthetic routers whose duration curves include non-monotone ones, so the
 * ceiling is checked on what the shipped handler returns, against fastest + budget recomputed HERE from the
 * router's own fastest time and the minutes the request typed - never against a number the handler reported.
 */
import { describe, expect, it } from "vitest";
import { handlePlan } from "../src/plan";
import { curveRouter, harness, planRequest, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const FAST_WAYS = [1, 2, 3, 4, 5];
const SCENIC_WAYS = [1, 10, 11, 12, 13, 14];

async function plan(router: ReturnType<typeof curveRouter>, minutes: number) {
  const h = harness(router);
  const response = await handlePlan(planRequest({ ...SANTA_MONICA_TOPANGA_BODY, budget_minutes: minutes }), {}, h.deps);
  return { status: response.status, body: (await response.json()) as Record<string, unknown>, h };
}

/** A seeded generator so a failing curve is reproducible from its index. */
function lcg(seed: number) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 2 ** 32;
  };
}

describe("POST /plan budget ceiling (R7, P-SAFE-04)", () => {
  it("never returns a route whose ETA exceeds fastest + budget, over 120 random curves incl. non-monotone", async () => {
    let planned = 0;
    for (let index = 0; index < 120; index += 1) {
      const random = lcg(index + 1);
      const fastestMs = 600_000 + Math.floor(random() * 1_200_000);
      const minutes = Math.floor(random() * 40);
      const knots = Array.from({ length: 9 }, () => Math.floor(random() * 3_000_000));
      const curve = (lambda: number) => fastestMs + knots[Math.min(8, Math.floor(lambda))]! - 900_000;
      const { status, body } = await plan(curveRouter(fastestMs, (l) => Math.max(1, curve(l)), FAST_WAYS, SCENIC_WAYS), minutes);
      if (status === 200) {
        planned += 1;
        expect(body.eta_s as number).toBeLessThanOrEqual(fastestMs / 1000 + minutes * 60);
        expect(body.eta_s).toBe(Math.max(1, curve(body.lambda as number)) / 1000);
      } else {
        expect(status).toBe(502);
      }
    }
    expect(planned).toBeGreaterThan(30);
  });

  it("a router whose every scenic route overshoots answers no_route, never an over-ceiling route", async () => {
    const { status, body } = await plan(curveRouter(1_000_000, () => 1_000_000 + 25 * 60_000 + 1, FAST_WAYS, SCENIC_WAYS), 25);
    expect(status).toBe(502);
    expect(body.error).toBe("no_route");
  });

  it("a scenic route exactly at the ceiling is returned (the ceiling is inclusive)", async () => {
    const { status, body } = await plan(curveRouter(1_000_000, () => 1_000_000 + 25 * 60_000, FAST_WAYS, SCENIC_WAYS), 25);
    expect(status).toBe(200);
    expect(body.eta_s).toBe(2500);
    expect(body.lambda).toBe(7.75);
  });

  it("on a flat curve the tie goes to the larger lambda", async () => {
    const { body } = await plan(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, SCENIC_WAYS), 25);
    expect(body.lambda).toBe(7.75);
    expect(body.evaluations).toBe(6);
  });

  it("an overshoot backs the bisection off: 0, 4, 2, 3, 3.5, 3.75 on a step at lambda 4", async () => {
    const { body, h } = await plan(curveRouter(1_000_000, (l) => (l >= 4 ? 9_000_000 : 1_000_000 + l * 100_000), FAST_WAYS, SCENIC_WAYS), 25);
    expect(body.lambda).toBe(3.75);
    expect(body.eta_s).toBe(1375);
    expect(h.sent).toHaveLength(7);
  });

  it("used_budget is true once half the budget is spent and false below it", async () => {
    const half = await plan(curveRouter(1_000_000, () => 1_000_000 + 750_000, FAST_WAYS, SCENIC_WAYS), 25);
    expect(half.body.used_budget).toBe(true);
    const under = await plan(curveRouter(1_000_000, () => 1_000_000 + 749_000, FAST_WAYS, SCENIC_WAYS), 25);
    expect(under.body.used_budget).toBe(false);
  });

  it("a scenic route sharing >= 0.6 of its ways with the fastest is 422 no_scenic_alternative", async () => {
    // [1, 2, 3] against [1..5]: Jaccard 3/5 = 0.6 exactly, which the strict < 0.6 refuses.
    const { status, body } = await plan(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, [1, 2, 3]), 25);
    expect(body.error).toBe("no_scenic_alternative");
    expect(status).toBe(422);
    const under = await plan(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, [1, 2, 3, 6, 7]), 25);
    expect(under.status).toBe(200);
  });

  it("a route with no osm_way_id detail is not 'different' - it is refused", async () => {
    const { status } = await plan(curveRouter(1_000_000, () => 1_100_000, [], []), 25);
    expect(status).toBe(422);
  });
});

describe("POST /plan hazards (R8)", () => {
  it("reports unpaved surface and restricted access runs of the chosen route, nothing else", async () => {
    const extra = {
      surface: [[0, 2, "asphalt"], [2, 3, "gravel"], [3, 4, "missing"], [4, 6, "COMPACTED"]],
      road_access: [[0, 1, "yes"], [1, 2, "destination"], [2, 6, "missing"]],
    };
    const { body } = await plan(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, SCENIC_WAYS, extra), 25);
    expect(body.hazards).toEqual([
      { kind: "surface", value: "gravel", from_index: 2, to_index: 3 },
      { kind: "surface", value: "compacted", from_index: 4, to_index: 6 },
      { kind: "road_access", value: "destination", from_index: 1, to_index: 2 },
    ]);
  });

  it("asks the router for the surface and road_access details the hazards are read from", async () => {
    const { h } = await plan(curveRouter(1_000_000, () => 1_100_000, FAST_WAYS, SCENIC_WAYS), 25);
    expect(h.sent).toHaveLength(7);
    for (const sent of h.sent) {
      expect(sent.body.details).toEqual(["scenic_score", "road_class", "osm_way_id", "surface", "road_access"]);
      expect(sent.body.points_encoded).toBe(false);
      expect(sent.body["ch.disable"]).toBe(true);
    }
  });
});
