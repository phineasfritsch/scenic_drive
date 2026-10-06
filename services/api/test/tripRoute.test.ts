/**
 * T-0268 through the SHIPPED ROUTES["/trip"]: the deps tripDepsFromEnv builds (QuotaCounter DO fake, D1 place
 * resolver, the router behind the global fetch). The shipped identity is anon (T-0256 R3), so this route serves the
 * PREVIEW (R5). Every router request is counted; the quota is read at the first one.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { buildCustomModel } from "../src/customModel";
import { ROUTES, type Env } from "../src/index";
import { TRIP_UPSTREAM_COST } from "../src/trip";
import { fakeKv, fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { BIG_SUR, EDGE_M, EDGES, expectedTrip, NOW, ORIGIN, ROAD, SCENIC_EDGE_MS, TRIP_BODY, tripPath, tripRouter,
  type RouterOptions } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const A_TO_B = [[ORIGIN.lon, ORIGIN.lat], [BIG_SUR.lon, BIG_SUR.lat]];
const REQUEST = { points: A_TO_B, points_encoded: false, instructions: false, "ch.disable": true, details: ["time", "distance"] };
const SEARCHED = [0, 4, 6, 7, 7.5, 7.75];

let quota: FakeQuota;
let router: ReturnType<typeof tripRouter>;
let stateAtFirstFetch: unknown;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare(`INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('${BIG_SUR.id}', ${BIG_SUR.lat}, ${BIG_SUR.lon})`).run();
});

function route(options: RouterOptions = {}) {
  stateAtFirstFetch = undefined;
  router = tripRouter({ ...options, onFetch: () => void (stateAtFirstFetch ??= quota.state()) });
  vi.stubGlobal("fetch", router.fetchImpl);
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  route();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function shippedEnv(over: Record<string, unknown> = {}): Env {
  const e: Record<string, unknown> = { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
    ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", ...over };
  for (const [key, value] of Object.entries(e)) if (value === undefined) delete e[key];
  return e as unknown as Env;
}

async function send(body: unknown = TRIP_BODY, e: Env = shippedEnv()) {
  const req = new Request("https://scenic-api.test/trip", {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
  const response = await ROUTES["/trip"]!(req, e, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

const tripped = (trip: number) => ({ [`device:${DEVICE}`]: { daily: { day: "2026-10-05", plan: 0, loop: 0, trip } },
  global: { monthly: { month: "2026-10", calls: TRIP_UPSTREAM_COST } } });

describe("ROUTES['/trip'] serves the preview (R3, R5)", () => {
  it("a 5-day trip: the whole answer, 7 router requests, one trip and 12 calls reserved BEFORE the first", async () => {
    const r = await send();
    expect(r).toEqual({ status: 200, json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: false }) });
    expect(router.sent.map((s) => s.body)).toEqual([{ ...REQUEST, profile: "car_fast" },
      ...SEARCHED.map((lambda) => ({ ...REQUEST, profile: "car_scenic", custom_model: buildCustomModel(lambda, null) }))]);
    expect(router.sent.map((s) => s.url)).toEqual(Array(7).fill("https://router.test/route"));
    expect(quota.state()).toEqual(tripped(1));
    expect(stateAtFirstFetch).toEqual(tripped(1));
  });

  it("the ceiling holds per day and for the trip on the answer itself", async () => {
    const days = (await send()).json.days as { drive_s: number; ceiling_s: number }[];
    const json = (await send(TRIP_BODY, shippedEnv({ QUOTA: fakeQuotaNamespace().ns }))).json;
    expect(days.every((d) => d.drive_s <= d.ceiling_s)).toBe(true);
    expect(days.reduce((s, d) => s + d.ceiling_s, 0) <= (json.ceiling_s as number)).toBe(true);
    expect((json.eta_s as number) <= (json.fastest_eta_s as number) + (json.budget_s as number)).toBe(true);
  });

  it("every day count is at most 12 router requests: 1 fastest + 6 searched, no legs on the preview", async () => {
    const counts = [];
    for (const days of [1, 2, 3, 4, 5]) {
      quota = fakeQuotaNamespace();
      route();
      const r = await send({ ...TRIP_BODY, days });
      counts.push([days, r.status, router.sent.length, (r.json.days as unknown[]).length]);
    }
    expect(counts).toEqual([1, 2, 3, 4, 5].map((days) => [days, 200, 7, days]));
  });

  it("extra_budget_pct 0 makes the fastest the ceiling: lambda 0 is the only fit", async () => {
    const r = await send({ ...TRIP_BODY, extra_budget_pct: 0 });
    expect(r).toEqual({ status: 200, json: expectedTrip({ days: 5, pct: 0, edgeMs: 360_000, lambda: 0, full: false }) });
  });
});

describe("ROUTES['/trip'] refuses with zero router requests", () => {
  for (const [name, over] of [["env KILL=1", { KILL: "1" }], ["KV KILL=1", { KILL_SWITCH: fakeKv({ KILL: "1" }) }]] as const) {
    it(`${name} is 503 planning_paused before the body is read: nothing reserved`, async () => {
      expect(await send("{not json", shippedEnv(over))).toEqual({ status: 503, json: { error: "planning_paused" } });
      expect([router.sent, quota.state()]).toEqual([[], {}]);
    });
  }

  it("a second trip the same day is 429 quota_exhausted (anon: one a day), the state unchanged", async () => {
    expect((await send()).status).toBe(200);
    const sent = router.sent.length;
    expect(await send()).toEqual({ status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } });
    expect([router.sent.length, quota.state()]).toEqual([sent, tripped(1)]);
  });

  it("a trip spends the trip allowance, not a plan, a loop or a surprise", async () => {
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 3, loop: 1, surprise: 3 });
    expect((await send()).status).toBe(200);
    expect(quota.state()[`device:${DEVICE}`]).toEqual({ daily: { day: "2026-10-05", plan: 3, loop: 1, surprise: 3, trip: 1 } });
  });

  it("without the router secret it is 503 planning_unavailable; an unknown place is 404", async () => {
    expect(await send(TRIP_BODY, shippedEnv({ ROUTER_SECRET: undefined }))).toEqual({ status: 503, json: { error: "planning_unavailable" } });
    expect(await send({ ...TRIP_BODY, destination: { place: "la:nowhere" } })).toEqual({ status: 404, json: { error: "unknown_place" } });
    expect([router.sent, quota.state()]).toEqual([[], {}]);
  });

  it("GET is 405 after the kill switch", async () => {
    const req = new Request("https://scenic-api.test/trip", { method: "GET" });
    const response = await ROUTES["/trip"]!(req, shippedEnv(), new URL(req.url));
    expect([response.status, await response.json()]).toEqual([405, { error: "POST only" }]);
  });
});

describe("the splitter's ceiling and day limits through ROUTES (R7)", () => {
  const scenicRuns = (lastMs: number, edgeMs: number, firstM = EDGE_M, pathMs = edgeMs * (EDGES - 1) + lastMs) => tripPath(ROAD, edgeMs, {
    time: Array.from({ length: EDGES }, (_, i) => [i, i + 1, i === EDGES - 1 ? lastMs : edgeMs]),
    distance: Array.from({ length: EDGES }, (_, i) => [i, i + 1, i === 0 ? firstM : EDGE_M]),
  }, pathMs);

  it("time runs summing to exactly fastest + 40% plan; one millisecond more is 422 ceiling_breached", async () => {
    // The path's own time is 18_000_000 (inside the ceiling, so the search keeps it); its RUNS are what is split.
    route({ scenic: scenicRuns(504_000, 504_000, EDGE_M, 18_000_000) });
    const exact = await send();
    quota = fakeQuotaNamespace();
    route({ scenic: scenicRuns(504_001, 504_000, EDGE_M, 18_000_000) });
    expect([exact.status, exact.json.eta_s, await send()]).toEqual([200, 20_160, { status: 422,
      json: { error: "ceiling_breached", detail: "the route takes 20160001 ms against a ceiling of 20160000 ms" } }]);
  });

  it("a day drives at most 300 mi: an edge of exactly 482_803 m is a day; one metre more is 422 too_few_days", async () => {
    route({ scenic: scenicRuns(450_000, 450_000, 482_803) });
    const exact = await send();
    quota = fakeQuotaNamespace();
    route({ scenic: scenicRuns(450_000, 450_000, 482_804) });
    const over = await send();
    quota = fakeQuotaNamespace();
    route({ scenic: scenicRuns(450_000, 450_000, 482_803.5) });
    const tooFew = { status: 422, json: { error: "too_few_days", days: 5, max_drive_s: 21_600, max_distance_m: 482_803 } };
    // An edge's distance is rounded to the metre (R2): 482_803.5 m is 482_804, one metre over.
    expect([exact.status, (exact.json.days as { distance_m: number }[])[0]!.distance_m, over, await send()])
      .toEqual([200, 482_803, tooFew, tooFew]);
  });

  it("a day drives at most 6 h: 21_600_000 ms in one day plans; one millisecond more is 422 too_few_days", async () => {
    route({ fastEdgeMs: 540_000, scenic: scenicRuns(540_000, 540_000) });
    const exact = await send({ ...TRIP_BODY, days: 1 });
    quota = fakeQuotaNamespace();
    route({ fastEdgeMs: 540_000, scenic: scenicRuns(540_001, 540_000) });
    expect([exact.status, exact.json.eta_s, await send({ ...TRIP_BODY, days: 1 })]).toEqual([200, 21_600,
      { status: 422, json: { error: "too_few_days", days: 1, max_drive_s: 21_600, max_distance_m: 482_803 } }]);
  });
});
