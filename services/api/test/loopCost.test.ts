/**
 * T-0252 R5/R8 (P-COST-01, P-COST-04): the kill switch and the quota stand in front of every router request /loop
 * makes, and one loop is at most LOOP_UPSTREAM_COST = 3 requests - reseed, then areas on the retraced edges.
 * Every case drives `handleLoop` with the counting fake and counts real fetch invocations.
 */
import { SELF, env } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import { ROUTES } from "../src/index";
import { handleLoop } from "../src/loop";
import { LOOP_UPSTREAM_COST, loopSeed, retracedAreas } from "../src/loopPlanner";
import { retraceScan } from "../src/retrace";
import { guardedPlan } from "../src/upstream";
import { LOOP_BODY, loopHarness, loopPath, loopRequest, NOW, outAndBack, squareLoop, START } from "./loopHarness";

const SEED = loopSeed("device-1", "2026-10-05");
const pts = (raw: [number, number][]) => raw.map(([lat, lon]) => ({ lat, lon }));

describe("POST /loop spend control (R8, P-COST-01)", () => {
  it("KILL=1 returns 503 with zero upstream calls and no reservation", async () => {
    const h = loopHarness([loopPath(squareLoop())]);
    const response = await handleLoop(loopRequest(LOOP_BODY), { KILL: "1" }, h.deps);
    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({ error: "planning_paused" });
    expect(h.events).toEqual([]);
  });

  it("KILL=1 is honoured before the body is even read", async () => {
    const h = loopHarness([]);
    const response = await handleLoop(loopRequest("{not json"), { KILL: "1" }, h.deps);
    expect(response.status).toBe(503);
    expect(h.events).toEqual([]);
  });

  it("the quota is reserved once, LOOP_UPSTREAM_COST of it, before the first upstream call", async () => {
    const h = loopHarness([loopPath(squareLoop())]);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(response.status).toBe(200);
    expect(h.events).toEqual(["reserve", "fetch"]);
    expect(h.reserved).toEqual([3]);
  });

  it("an exhausted daily quota is 429 with resets_at and zero upstream calls", async () => {
    const h = loopHarness([loopPath(squareLoop())], { plansUsedToday: 10 });
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(response.status).toBe(429);
    expect(await response.json()).toEqual({ error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" });
    expect(h.events).toEqual([]);
  });

  it("a tripped monthly counter is 503 planning_paused with zero upstream calls", async () => {
    const h = loopHarness([loopPath(squareLoop())], { monthlyUpstreamCalls: 225_000 });
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(response.status).toBe(503);
    expect(h.events).toEqual([]);
  });
});

describe("POST /loop request count (R5, P-COST-04)", () => {
  it("a clean first loop is one request", async () => {
    const h = loopHarness([loopPath(squareLoop())]);
    await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(h.sent.map((s) => s.body["round_trip.seed"])).toEqual([SEED]);
  });

  it("a retraced first loop is reseeded: the second request carries seed + 1 and no areas", async () => {
    const h = loopHarness([loopPath(outAndBack(2000)), loopPath(squareLoop())]);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(response.status).toBe(200);
    expect(h.sent.map((s) => s.body["round_trip.seed"])).toEqual([SEED, (SEED + 1) >>> 0]);
    expect(h.sent[1]!.body.custom_model).toEqual(buildCustomModel(2, null));
    expect(((await response.json()) as { attempts: number; seed: number })).toMatchObject({ attempts: 2, seed: (SEED + 1) >>> 0 });
  });

  it("a loop is at most 3 upstream requests: reseed, then areas on the retraced edges of the reseeded loop", async () => {
    const second = outAndBack(1500);
    const h = loopHarness([loopPath(outAndBack(2000)), loopPath(second), loopPath(outAndBack(1000)), loopPath(squareLoop())]);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(h.sent).toHaveLength(3);
    expect(h.sent.map((s) => s.body["round_trip.seed"])).toEqual([SEED, (SEED + 1) >>> 0, (SEED + 1) >>> 0]);
    const areas = retracedAreas(retraceScan(pts(second))!.retraced, START);
    expect(areas).not.toBeNull();
    // Measured, not derived: the 1500 m spur's return leg, clear of the first 300 m, thinned to 100 m spacing.
    expect(areas!.features.length).toBe(12);
    const ring = areas!.features[0]!.geometry.coordinates[0]!;
    expect(ring.length).toBe(5);
    expect((ring[2]![1]! - ring[0]![1]!) * 111_132).toBeCloseTo(60, 6);
    expect(h.sent[2]!.body.custom_model).toEqual(JSON.parse(JSON.stringify(buildCustomModel(2, areas))));
    expect(response.status).toBe(422);
    const fractions = [outAndBack(2000), second, outAndBack(1000)].map((p) => retraceScan(pts(p))!.fraction);
    expect(await response.json()).toEqual({ error: "no_clean_loop", retrace_fraction: Math.min(...fractions) });
  });

  it("the areas attempt can succeed: the third loop is returned", async () => {
    const h = loopHarness([loopPath(outAndBack(2000)), loopPath(outAndBack(1500)), loopPath(squareLoop())]);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(response.status).toBe(200);
    expect(((await response.json()) as { attempts: number }).attempts).toBe(3);
  });

  it("when every retraced sample is inside the start clearance the third request is not sent", async () => {
    const h = loopHarness([loopPath(outAndBack(2000)), loopPath(outAndBack(240)), loopPath(squareLoop())]);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(h.sent).toHaveLength(2);
    expect(response.status).toBe(422);
  });

  it("guardedPlan at LOOP_UPSTREAM_COST refuses a 4th request before fetch", async () => {
    const h = loopHarness([loopPath(squareLoop()), loopPath(squareLoop()), loopPath(squareLoop()), loopPath(squareLoop())]);
    const refused = guardedPlan(h.deps.upstream, { userId: "device-1", tier: "free" }, async (call) => {
      for (let i = 0; i < 4; i += 1) await call("https://router.test/route", { method: "POST", body: "{}" });
    }, LOOP_UPSTREAM_COST);
    await expect(refused).rejects.toThrow("plan exceeded its budget of 3 upstream calls");
    expect(h.events).toEqual(["reserve", "fetch", "fetch", "fetch"]);
    expect(NOW.toISOString().slice(0, 10)).toBe("2026-10-05");
  });

  it("a router refusal is 502 no_route", async () => {
    const h = loopHarness([]);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(response.status).toBe(502);
    expect(h.sent).toHaveLength(1);
  });
});

describe("ROUTES['/loop'] - the shipped wiring (R10)", () => {
  it("with no router or counters configured it answers 503 planning_unavailable", async () => {
    expect(typeof ROUTES["/loop"]).toBe("function");
    const response = await SELF.fetch("https://scenic-api.test/loop", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(LOOP_BODY),
    });
    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({ error: "planning_unavailable" });
  });

  it("KILL=1 on the shipped route answers 503 planning_paused", async () => {
    (env as unknown as { KILL?: string }).KILL = "1";
    try {
      const response = await SELF.fetch("https://scenic-api.test/loop", { method: "POST", body: "{}" });
      expect(response.status).toBe(503);
      expect(await response.json()).toEqual({ error: "planning_paused" });
    } finally {
      delete (env as unknown as { KILL?: string }).KILL;
    }
  });
});
