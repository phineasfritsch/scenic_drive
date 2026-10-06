/**
 * T-0256: the SHIPPED /plan and /loop - ROUTES with deps built from env - over the QuotaCounter Durable Object
 * (an in-memory DurableObjectState per instance, R9), the D1 place table from the shipped migration, and a
 * recording router standing in for the global fetch. Counter state is asserted WHOLE after every call.
 */
import { liveClosures } from "./closuresFake";
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { ROUTES, type Env } from "../src/index";
import { fakeKv, fakeQuotaNamespace, recordingRouter, type FakeQuota } from "./doFake";
import { LOOP_BODY, loopPath, squareLoop } from "./loopHarness";
import { NOW, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const SECRET = "test-router-secret";
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const WIRE_HEADERS: [string, string][] = [["content-type", "application/json"], ["x-scenic-router-secret", SECRET]];

let quota: FakeQuota;
let router: ReturnType<typeof recordingRouter>;
let stateAtFirstFetch: unknown;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957), ('la:bad', 91, 0)").run();
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  stateAtFirstFetch = undefined;
  router = recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop()), () => {
    stateAtFirstFetch ??= quota.state();
  });
  vi.stubGlobal("fetch", router.fetchImpl);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function fullEnv(over: Record<string, unknown> = {}): Env {
  const e: Record<string, unknown> = {
    DB: env.DB, GIT_SHA: "test", BUILT_AT: "test",
    QUOTA: quota.ns, ROUTER_URL: "https://router.test", ROUTER_SECRET: SECRET, CLOSURES: liveClosures(), ...over,
  };
  for (const [key, value] of Object.entries(e)) if (value === undefined) delete e[key];
  return e as unknown as Env;
}

async function send(path: "/plan" | "/loop", e: Env, device: string | null = DEVICE, body?: unknown,
  extra: Record<string, string> = {}) {
  const headers: Record<string, string> = { "content-type": "application/json", ...extra };
  if (device !== null) headers["x-scenic-device"] = device;
  const req = new Request(`https://scenic-api.test${path}`, {
    method: "POST", headers, body: JSON.stringify(body ?? (path === "/plan" ? SANTA_MONICA_TOPANGA_BODY : LOOP_BODY)),
  });
  const response = await ROUTES[path]!(req, e, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

const daily = (day: string, plan: number, loop: number) => ({ daily: { day, plan, loop } });
const monthly = (month: string, calls: number) => ({ monthly: { month, calls } });

describe("the shipped routes over the QuotaCounter DO (R1-R4)", () => {
  it("one /plan reserves one plan on the device and 12 calls on the month before the first router request", async () => {
    const r = await send("/plan", fullEnv());
    expect(r.status).toBe(200);
    const after = { [`device:${DEVICE}`]: daily("2026-10-05", 1, 0), global: monthly("2026-10", 12) };
    expect(quota.state()).toEqual(after);
    expect(stateAtFirstFetch).toEqual(after);
    expect(router.calls).toHaveLength(7);
  });

  it("an anon device gets three plans a day; the fourth is 429 with zero router requests and the state unchanged", async () => {
    for (let i = 0; i < 3; i += 1) expect((await send("/plan", fullEnv())).status).toBe(200);
    const three = { [`device:${DEVICE}`]: daily("2026-10-05", 3, 0), global: monthly("2026-10", 36) };
    expect(quota.state()).toEqual(three);
    const fourth = await send("/plan", fullEnv());
    expect(fourth).toEqual({ status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } });
    expect(quota.state()).toEqual(three);
    expect(router.calls).toHaveLength(21);
  });

  it("a loop spends the loop allowance, not a plan: one loop a day, the second is 429", async () => {
    expect((await send("/loop", fullEnv())).status).toBe(200);
    expect(quota.state()).toEqual({ [`device:${DEVICE}`]: daily("2026-10-05", 0, 1), global: monthly("2026-10", 3) });
    expect((await send("/plan", fullEnv())).status).toBe(200);
    const both = { [`device:${DEVICE}`]: daily("2026-10-05", 1, 1), global: monthly("2026-10", 15) };
    expect(quota.state()).toEqual(both);
    const calls = router.calls.length;
    expect(await send("/loop", fullEnv())).toEqual(
      { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } });
    expect(quota.state()).toEqual(both);
    expect(router.calls).toHaveLength(calls);
  });

  it("a new UTC day resets the device's allowance in place", async () => {
    for (let i = 0; i < 3; i += 1) await send("/plan", fullEnv());
    await send("/loop", fullEnv());
    vi.setSystemTime(new Date("2026-10-06T00:00:01Z"));
    expect((await send("/plan", fullEnv())).status).toBe(200);
    expect(quota.state()).toEqual({ [`device:${DEVICE}`]: daily("2026-10-06", 1, 0), global: monthly("2026-10", 51) });
  });

  it("a new UTC month restarts the monthly count", async () => {
    quota.seed("global", "monthly", { month: "2026-09", calls: 224_999 });
    expect((await send("/plan", fullEnv())).status).toBe(200);
    expect(quota.state()).toEqual({ [`device:${DEVICE}`]: daily("2026-10-05", 1, 0), global: monthly("2026-10", 12) });
  });

  it("a tripped month is 503 planning_paused with zero router requests and nothing reserved", async () => {
    quota.seed("global", "monthly", { month: "2026-10", calls: 225_000 });
    expect(await send("/plan", fullEnv())).toEqual({ status: 503, json: { error: "planning_paused" } });
    expect(quota.state()).toEqual({ [`device:${DEVICE}`]: {}, global: monthly("2026-10", 225_000) });
    expect(router.calls).toEqual([]);
  });

  it("devices are counted apart; no or a malformed x-scenic-device shares one unidentified bucket; case folds", async () => {
    await send("/plan", fullEnv());
    await send("/plan", fullEnv(), DEVICE.toUpperCase());
    await send("/plan", fullEnv(), null);
    await send("/plan", fullEnv(), "not-a-device");
    expect(quota.state()).toEqual({
      [`device:${DEVICE}`]: daily("2026-10-05", 2, 0),
      "device:unidentified": daily("2026-10-05", 2, 0),
      global: monthly("2026-10", 48),
    });
  });
});

describe("the tier is never read from the client (R3)", () => {
  const claimsPaid = { "x-scenic-tier": "paid" };
  const refused = { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } };

  it("a device sending x-scenic-tier: paid still gets the anon allowance: the 4th plan and the 2nd loop are 429", async () => {
    for (let i = 0; i < 3; i += 1) expect((await send("/plan", fullEnv(), DEVICE, undefined, claimsPaid)).status).toBe(200);
    expect((await send("/loop", fullEnv(), DEVICE, undefined, claimsPaid)).status).toBe(200);
    const spent = { [`device:${DEVICE}`]: daily("2026-10-05", 3, 1), global: monthly("2026-10", 39) };
    expect(quota.state()).toEqual(spent);
    const calls = router.calls.length;
    expect(await send("/plan", fullEnv(), DEVICE, undefined, claimsPaid)).toEqual(refused);
    expect(await send("/loop", fullEnv(), DEVICE, undefined, claimsPaid)).toEqual(refused);
    expect(quota.state()).toEqual(spent);
    expect(router.calls).toHaveLength(calls);
  });

  for (const path of ["/plan", "/loop"] as const) {
    it(`${path} with a tier field in the body is 400 with zero router requests and nothing reserved`, async () => {
      const body = { ...(path === "/plan" ? SANTA_MONICA_TOPANGA_BODY : LOOP_BODY), tier: "paid" };
      expect(await send(path, fullEnv(), DEVICE, body)).toEqual({ status: 400, json: {
        error: "invalid_request", detail: `the body carries "tier", which ${path} does not accept` } });
      expect(router.calls).toEqual([]);
      expect(quota.state()).toEqual({});
    });
  }
});

describe("deps exist exactly when every binding does (R8)", () => {
  const missing: [string, Record<string, unknown>][] = [
    ["no QUOTA binding", { QUOTA: undefined }],
    ["no ROUTER_URL", { ROUTER_URL: undefined }],
    ["no ROUTER_SECRET", { ROUTER_SECRET: undefined }],
    ["an empty ROUTER_SECRET", { ROUTER_SECRET: "" }],
    ["the placeholder ROUTER_URL https://router.invalid", { ROUTER_URL: "https://router.invalid" }],
    ["an http: ROUTER_URL", { ROUTER_URL: "http://router.test" }],
  ];
  for (const path of ["/plan", "/loop"] as const) {
    for (const [name, over] of missing) {
      it(`${path} with ${name} is 503 planning_unavailable with zero router requests`, async () => {
        expect(await send(path, fullEnv(over))).toEqual({ status: 503, json: { error: "planning_unavailable" } });
        expect(router.calls).toEqual([]);
        expect(quota.state()).toEqual({});
      });
    }
  }

  it("/plan without the DB binding is 503 planning_unavailable with zero router requests", async () => {
    expect(await send("/plan", fullEnv({ DB: undefined }))).toEqual({ status: 503, json: { error: "planning_unavailable" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });
});

describe("the router secret header (R7, P-COST-03)", () => {
  it("every router request /plan makes carries x-scenic-router-secret, recorded at the wire", async () => {
    await send("/plan", fullEnv());
    expect(router.calls.map((c) => [c.url, c.headers])).toEqual(Array(7).fill(["https://router.test/route", WIRE_HEADERS]));
  });

  it("every router request /loop makes carries x-scenic-router-secret, recorded at the wire", async () => {
    await send("/loop", fullEnv());
    expect(router.calls.map((c) => [c.url, c.headers])).toEqual([["https://router.test/route", WIRE_HEADERS]]);
  });

  it("a trailing slash on ROUTER_URL does not double the path", async () => {
    await send("/loop", fullEnv({ ROUTER_URL: "https://router.test/" }));
    expect(router.calls.map((c) => c.url)).toEqual(["https://router.test/route"]);
  });
});

describe("the kill switch reads KV if bound and the env var always (R5)", () => {
  const paused = { status: 503, json: { error: "planning_paused" } };
  for (const path of ["/plan", "/loop"] as const) {
    it(`${path}: KV KILL=1 pauses with zero router requests and nothing reserved`, async () => {
      expect(await send(path, fullEnv({ KILL_SWITCH: fakeKv({ KILL: "1" }) }))).toEqual(paused);
      expect(router.calls).toEqual([]);
      expect(quota.state()).toEqual({});
    });
  }

  it("a KV read that throws pauses (fail closed)", async () => {
    expect(await send("/plan", fullEnv({ KILL_SWITCH: fakeKv({}, true) }))).toEqual(paused);
    expect(router.calls).toEqual([]);
  });

  it("env KILL=1 pauses even when KV says 0", async () => {
    expect(await send("/plan", fullEnv({ KILL: "1", KILL_SWITCH: fakeKv({ KILL: "0" }) }))).toEqual(paused);
    expect(router.calls).toEqual([]);
  });

  it("KV KILL other than exactly 1, or absent, does not pause", async () => {
    expect((await send("/plan", fullEnv({ KILL_SWITCH: fakeKv({ KILL: "0" }) }))).status).toBe(200);
    expect((await send("/plan", fullEnv({ KILL_SWITCH: fakeKv({}) }))).status).toBe(200);
  });
});

describe("the place resolver over D1 (R6)", () => {
  it("an unknown place id is 404 unknown_place with zero router requests and nothing reserved", async () => {
    const body = { ...SANTA_MONICA_TOPANGA_BODY, destination: { place: "la:nowhere" } };
    expect(await send("/plan", fullEnv(), DEVICE, body)).toEqual({ status: 404, json: { error: "unknown_place" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("a place row with an out-of-range coordinate is 503 planning_unavailable, zero router requests", async () => {
    const body = { ...SANTA_MONICA_TOPANGA_BODY, destination: { place: "la:bad" } };
    expect(await send("/plan", fullEnv(), DEVICE, body)).toEqual({ status: 503, json: { error: "planning_unavailable" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("a D1 that cannot answer (no places table yet) is 503 planning_unavailable, zero router requests", async () => {
    const broken = { prepare: () => { throw new Error("D1_ERROR: no such table: places"); } };
    expect(await send("/plan", fullEnv({ DB: broken }))).toEqual({ status: 503, json: { error: "planning_unavailable" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("the destination is the coordinate the D1 row holds", async () => {
    await send("/plan", fullEnv());
    expect(router.calls[0]!.body.points).toEqual([[-118.49, 34.02], [-118.5957, 34.0676]]);
  });
});
