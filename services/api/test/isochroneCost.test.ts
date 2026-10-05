/**
 * T-0262 R4-R6 (P-COST-01, P-COST-04): the kill switch, the surprise quota and the daily reach cache in front of the
 * one GraphHopper request /isochrone makes. Every case drives the SHIPPED ROUTES["/isochrone"] (deps from env) over
 * the QuotaCounter fake and caches.default, counts real fetch invocations and asserts the counter state WHOLE.
 */
import { SELF } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { dailyQuota } from "../src/quota";
import { secondsToNextDay } from "../src/reachCache";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { DEVICE, expectedReach, isochroneRouter, NOW, reach, REACH_BODY, reachEnv, START, wire } from "./isochroneHarness";

let quota: FakeQuota;
let router: ReturnType<typeof isochroneRouter>;
let stateAtFirstFetch: unknown;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  stateAtFirstFetch = undefined;
  router = isochroneRouter(() => {
    stateAtFirstFetch ??= quota.state();
  });
  vi.stubGlobal("fetch", router.fetchImpl);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const device = (day: string, surprise: number, plan = 0, loop = 0) => ({ daily: { day, plan, loop, surprise } });
const month = (m: string, calls: number) => ({ monthly: { month: m, calls } });
/** Another install, so a test of the cache key never runs into one device's three a day. */
const other = (n: number) => `0f8b6d5e-1a2b-4c3d-8e9f-01234567890${n}`;

describe("ROUTES['/isochrone'] spend control (R4, R5, P-COST-01)", () => {
  it("KILL=1 is 503 before the body is read: zero router requests and no reservation", async () => {
    const r = await reach(reachEnv(quota, { KILL: "1" }), "{not json");
    expect(r).toEqual({ status: 503, json: { error: "planning_paused" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("every method but POST is 405 POST only, a PUT carrying a valid body too: zero router requests, no reservation", async () => {
    const e = reachEnv(quota);
    for (const method of ["GET", "PUT", "PATCH", "DELETE"]) {
      expect(await reach(e, REACH_BODY, DEVICE, method)).toEqual({ status: 405, json: { error: "POST only" } });
    }
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("with no router configured a refused body is the whole 400 it is with one: the whitelist before the deps", async () => {
    const refused: unknown[] = [
      "{not json",
      { ...REACH_BODY, end: START },
      { start: { lat: 34.071, lon: -118.45 }, minutes: 120 },
      { start: { lat: 34.07, lon: -118.451 }, minutes: 120 },
      { start: START, minutes: 29 },
    ];
    for (const body of refused) {
      const bound = await reach(reachEnv(quota), body);
      expect([bound.status, bound.json.error]).toEqual([400, "invalid_request"]);
      expect(await reach(reachEnv(quota, { ROUTER_URL: undefined }), body)).toEqual(bound);
    }
    expect(await reach(reachEnv(quota, { ROUTER_URL: undefined }))).toEqual({ status: 503, json: { error: "planning_unavailable" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("the surprise allowance and one monthly call are reserved before the one router request", async () => {
    const r = await reach(reachEnv(quota));
    expect(r.status).toBe(200);
    const after = { [`device:${DEVICE}`]: device("2026-10-05", 1), global: month("2026-10", 1) };
    expect(quota.state()).toEqual(after);
    expect(stateAtFirstFetch).toEqual(after);
    expect(router.calls).toHaveLength(1);
  });

  it("an anon device gets three surprise reaches a day; the fourth is 429 with zero router requests", async () => {
    const e = reachEnv(quota);
    for (const lat of [34.01, 34.02, 34.03]) expect((await reach(e, { start: { lat, lon: -118.45 }, minutes: 60 })).status).toBe(200);
    const fourth = await reach(e, { start: { lat: 34.04, lon: -118.45 }, minutes: 60 });
    expect(fourth).toEqual({ status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } });
    expect(router.calls).toHaveLength(3);
    expect(quota.state()).toEqual({ [`device:${DEVICE}`]: device("2026-10-05", 3), global: month("2026-10", 3) });
  });

  it("the surprise allowance is its own: 3 anon, 3 free, the paid plan cap; plans and loops do not spend it", async () => {
    expect([dailyQuota("surprise", "anon"), dailyQuota("surprise", "free"), dailyQuota("surprise", "paid")]).toEqual([3, 3, 200]);
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 3, loop: 1 });
    expect((await reach(reachEnv(quota))).status).toBe(200);
    expect(quota.state()).toEqual({ [`device:${DEVICE}`]: device("2026-10-05", 1, 3, 1), global: month("2026-10", 1) });
  });
});

describe("ROUTES['/isochrone'] request count and the daily cache (R5, R6, P-COST-04)", () => {
  it("the request count is exactly 1 per call and 0 on a cache hit", async () => {
    const e = reachEnv(quota);
    const first = await reach(e);
    const second = await reach(e);
    expect(router.calls.map((c) => c.url)).toEqual([wire("34.07", "-118.45", 3600, 4)]);
    expect(first).toEqual({ status: 200, json: expectedReach(120, 4) });
    expect(second).toEqual(first);
  });

  it("a cache hit spends no quota, and is served after the day's three are spent", async () => {
    const e = reachEnv(quota);
    expect((await reach(e)).status).toBe(200);
    const once = { [`device:${DEVICE}`]: device("2026-10-05", 1), global: month("2026-10", 1) };
    expect(quota.state()).toEqual(once);
    expect((await reach(e)).status).toBe(200);
    expect(quota.state()).toEqual(once);
    for (const lat of [34.01, 34.02]) expect((await reach(e, { start: { lat, lon: -118.45 }, minutes: 120 })).status).toBe(200);
    expect((await reach(e, { start: { lat: 34.03, lon: -118.45 }, minutes: 120 })).status).toBe(429);
    const spent = quota.state();
    expect(await reach(e)).toEqual({ status: 200, json: expectedReach(120, 4) });
    expect(quota.state()).toEqual(spent);
    expect(router.calls).toHaveLength(3);
  });

  it("the cache key is the start at 2 dp, the minutes bucket, the UTC day and the graph version", async () => {
    const graph = "graph-key-test";
    const e = reachEnv(quota, { GRAPH_VERSION: graph });
    await reach(e);
    const hit = await reach(e, { start: START, minutes: 125 });
    expect(hit).toEqual({ status: 200, json: expectedReach(125, 4) });
    expect(router.calls).toHaveLength(1);
    await reach(e, { start: START, minutes: 150 }, other(1));
    const north = { lat: 34.08, lon: -118.45 };
    const west = { lat: 34.07, lon: -118.46 };
    expect(await reach(e, { start: north, minutes: 120 }, other(2))).toEqual({ status: 200, json: expectedReach(120, 4, north) });
    expect(await reach(e, { start: west, minutes: 120 }, other(4))).toEqual({ status: 200, json: expectedReach(120, 4, west) });
    await reach(reachEnv(quota, { GRAPH_VERSION: `${graph}-rebuilt` }), REACH_BODY, other(3));
    vi.setSystemTime(new Date("2026-10-06T00:00:00Z"));
    await reach(e);
    expect(router.calls.map((c) => c.url)).toEqual([
      wire("34.07", "-118.45", 3600, 4),
      wire("34.07", "-118.45", 4500, 5),
      wire("34.08", "-118.45", 3600, 4),
      wire("34.07", "-118.46", 3600, 4),
      wire("34.07", "-118.45", 3600, 4),
      wire("34.07", "-118.45", 3600, 4),
    ]);
    await reach(e, { start: { lat: 34.08, lon: -118.45 }, minutes: 121 });
    expect(router.calls).toHaveLength(7);
    await reach(e, { start: { lat: 34.08, lon: -118.45 }, minutes: 134 });
    expect(router.calls).toHaveLength(7);
    expect([secondsToNextDay(NOW), secondsToNextDay(new Date("2026-10-05T23:59:59.500Z"))]).toEqual([43_200, 1]);
  });

  it("with no router configured the shipped worker answers 503 planning_unavailable", async () => {
    const response = await SELF.fetch("https://scenic-api.test/isochrone", {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(REACH_BODY),
    });
    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({ error: "planning_unavailable" });
    expect(router.calls).toEqual([]);
  });
});
