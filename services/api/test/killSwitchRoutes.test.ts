/**
 * T-0264 rv1 B1: the kill switch over EVERY upstream route of the shipped ROUTES table (P-COST-01). The route list is
 * derived from ROUTES itself - every key outside the OPERATIONAL whitelist - and must equal the UPSTREAM literal, so
 * a fifth route either joins this loop or fails the equality. Each route is killed by the env KILL and, separately,
 * by the KV KILL_SWITCH key, through the deps the shipped wiring builds from env.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES, type Env } from "../src/index";
import { fakeKv, fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { REACH_BODY } from "./isochroneHarness";
import { LOOP_BODY } from "./loopHarness";
import { NOW, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { TRIP_BODY } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
// /asn and /entitlement read and write D1 only - no upstream call, nothing for the kill switch to save (T-0267 R11).
const OPERATIONAL_ROUTES = ["/__health", "/__version", "/__ro", "/asn", "/entitlement"] as const;
const UPSTREAM_ROUTES = ["/plan", "/loop", "/isochrone", "/trip"] as const;
// /telemetry writes Analytics Engine, not the router: killed by its own ROUTES test below (T-0279 R8), and the ONLY
// route excluded from the upstream derivation besides the operational ones.
const TELEMETRY_ROUTE = "/telemetry";
type UpstreamRoute = (typeof UPSTREAM_ROUTES)[number];
const BODIES: Record<UpstreamRoute, unknown> = {
  "/plan": SANTA_MONICA_TOPANGA_BODY,
  "/loop": LOOP_BODY,
  "/isochrone": REACH_BODY,
  "/trip": TRIP_BODY,
};
const SOURCES: [string, Record<string, unknown>][] = [
  ["env KILL=1", { KILL: "1" }],
  ["KV KILL_SWITCH KILL=1", { KILL_SWITCH: fakeKv({ KILL: "1" }) }],
];

let quota: FakeQuota;
let routerRequests: string[];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  routerRequests = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    routerRequests.push(String(input instanceof Request ? input.url : input));
    return new Response(JSON.stringify({ message: "the kill-switch test answers no router request" }), { status: 500 });
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function killedEnv(source: Record<string, unknown>): Env {
  return {
    DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "test-router-secret", GRAPH_VERSION: "kill-switch-test", ...source,
  } as unknown as Env;
}

async function send(path: string, e: Env) {
  const req = new Request(`https://scenic-api.test${path}`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE },
    body: JSON.stringify(BODIES[path as UpstreamRoute]),
  });
  const response = await ROUTES[path]!(req, e, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

describe("ROUTES kill switch over every upstream route (P-COST-01)", () => {
  it("every upstream key of ROUTES pauses on env KILL and on KV KILL_SWITCH: 503 planning_paused, zero router requests, quota state empty", async () => {
    const upstream = Object.keys(ROUTES).filter((k) => !(OPERATIONAL_ROUTES as readonly string[]).includes(k) && k !== TELEMETRY_ROUTE);
    expect(upstream).toEqual([...UPSTREAM_ROUTES]);
    const answered: [string, string, unknown][] = [];
    for (const [name, source] of SOURCES) {
      for (const path of upstream) {
        answered.push([name, path, await send(path, killedEnv(source))]);
        expect(routerRequests).toEqual([]);
        expect(quota.state()).toEqual({});
      }
    }
    const paused = { status: 503, json: { error: "planning_paused" } };
    expect(answered).toEqual(SOURCES.flatMap(([name]) => UPSTREAM_ROUTES.map((path) => [name, path, paused])));
  });
});

describe("ROUTES['/telemetry'] kill switch (T-0279 R8, P-COST-01)", () => {
  it("ROUTES['/telemetry'] pauses on env KILL and on KV KILL_SWITCH: 503 telemetry_paused, zero Analytics Engine writes, quota state empty", async () => {
    expect(Object.keys(ROUTES).filter((k) => k === TELEMETRY_ROUTE)).toEqual([TELEMETRY_ROUTE]);
    const answered: [string, unknown][] = [];
    for (const [name, source] of SOURCES) {
      const writes: unknown[] = [];
      const e = { ...killedEnv(source), TELEMETRY: { writeDataPoint: (p: unknown) => void writes.push(p) } } as unknown as Env;
      const req = new Request(`https://scenic-api.test${TELEMETRY_ROUTE}`, {
        method: "POST",
        headers: { "content-type": "application/json", "x-scenic-device": DEVICE },
        body: JSON.stringify({ events: [{ blobs: ["drive_started", "", ""], doubles: [0, 0], indexes: ["drive_started"] }] }),
      });
      const response = await ROUTES[TELEMETRY_ROUTE]!(req, e, new URL(req.url));
      answered.push([name, { status: response.status, json: await response.json() }]);
      expect(writes).toEqual([]);
      expect(quota.state()).toEqual({});
    }
    const paused = { status: 503, json: { error: "telemetry_paused" } };
    expect(answered).toEqual(SOURCES.map(([name]) => [name, paused]));
  });
});
