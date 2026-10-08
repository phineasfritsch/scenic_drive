/**
 * T-0311 (R1-R4, P-COST-01, P-PRIV-05): the plan request carries the vehicle profile. /plan, /loop and /trip accept
 * exactly the enabled profiles; every disabled and unknown value is 400 invalid_request whole, before the quota is
 * reserved and with ZERO router requests, through the shipped worker.fetch. An absent field is standard (R2).
 *
 * Every case is a function of (value, route): the route's reference body with only `vehicle` added. The meta-test
 * proves no row ignores its route: the same body with `vehicle` set to "standard" observes the route's baseline (so
 * each 400 is the vehicle's, not a body malformed for that route), and each row answers each route differently.
 * The expected detail is recomputed here from literals, never imported from src.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import worker, { type Env } from "../src/index";
import placesSql from "../migrations/0001_places.sql?raw";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { LOOP_BODY } from "./loopHarness";
import { NOW, PLACES, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { BIG_SUR, TRIP_BODY } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const ROUTES = ["/plan", "/loop", "/trip"] as const;
type Route = (typeof ROUTES)[number];
const REFERENCE: Record<Route, Record<string, unknown>> = {
  "/plan": SANTA_MONICA_TOPANGA_BODY, "/loop": LOOP_BODY, "/trip": TRIP_BODY,
};
/** ScenicKit VehicleProfile's raw values in case order (PlanVehicleWireTests holds the Swift side to this list). */
const WIRE_VALUES = ["standard", "lowClearance", "motorcycle", "trailer", "rv"];
const ENABLED = ["standard"];
const ABSENT = Symbol("absent");

/** Every value the Worker must refuse: the disabled profiles, near-misses of "standard", and every non-string. */
const REFUSED: readonly { name: string; value: unknown }[] = [
  ...WIRE_VALUES.filter((v) => !ENABLED.includes(v)).map((v) => ({ name: `disabled ${v}`, value: v })),
  { name: "empty", value: "" },
  { name: "capitalised", value: "Standard" },
  { name: "upper case", value: "STANDARD" },
  { name: "leading space", value: " standard" },
  { name: "trailing space", value: "standard " },
  { name: "trailing zero-width space", value: "standard​" },
  { name: "suffix", value: "standards" },
  { name: "prefix", value: "std" },
  { name: "a car nobody named", value: "suv" },
  { name: "null", value: null },
  { name: "zero", value: 0 },
  { name: "one", value: 1 },
  { name: "true", value: true },
  { name: "false", value: false },
  { name: "array of standard", value: ["standard"] },
  { name: "empty object", value: {} },
  { name: "a coordinate", value: { lat: 34.02, lon: -118.49 } },
  { name: "object naming standard", value: { profile: "standard" } },
];

let quota: FakeQuota;
let routerRequests: string[];

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  routerRequests = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    routerRequests.push(String(input instanceof Request ? input.url : input));
    return new Response(JSON.stringify({ message: "the vehicle test answers every router request 500" }), { status: 500 });
  });
  for (const statement of placesSql.split(";").map((s) => s.trim()).filter(Boolean)) await env.DB.prepare(statement).run();
  const topanga = PLACES["la:topanga"]!;
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', ?1, ?2), (?3, ?4, ?5)")
    .bind(topanga.lat, topanga.lon, BIG_SUR.id, BIG_SUR.lat, BIG_SUR.lon).run();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

interface Observation { status: number; json: unknown; router: number; quotaTouched: boolean }

/** The row's body for this route: the route's reference body with only `vehicle` added (or left absent). */
function body(route: Route, value: unknown): Record<string, unknown> {
  const built: Record<string, unknown> = { ...REFERENCE[route] };
  if (value !== ABSENT) built.vehicle = value;
  return built;
}

async function observe(route: Route, value: unknown): Promise<Observation> {
  quota = fakeQuotaNamespace();
  const shipped: Record<string, unknown> = {
    DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
    ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", GRAPH_VERSION: `vehicle-${Math.random()}`,
  };
  const before = JSON.stringify(quota.state());
  const sentBefore = routerRequests.length;
  const response = await worker.fetch(new Request(`https://scenic-api.test${route}`, {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE },
    body: JSON.stringify(body(route, value)),
  }), shipped as unknown as Env);
  const json = (await response.json()) as unknown;
  return { status: response.status, json, router: routerRequests.length - sentBefore,
    quotaTouched: JSON.stringify(quota.state()) !== before };
}

/** The refusal, recomputed: 400 invalid_request naming the route, zero router requests, the quota untouched. */
function refusal(route: Route): Observation {
  return { status: 400, json: { error: "invalid_request", detail: `vehicle must be "standard": the only profile ${route} plans for` },
    router: 0, quotaTouched: false };
}

describe("the plan request carries the vehicle profile (T-0311, P-COST-01, P-PRIV-05)", () => {
  it("an absent vehicle and \"standard\" observe the same answer on every route, and that answer spent the quota and called the router", async () => {
    const seen: [Route, Observation, boolean][] = [];
    for (const route of ROUTES) {
      const absent = await observe(route, ABSENT);
      const standard = await observe(route, "standard");
      seen.push([route, standard, JSON.stringify(standard) === JSON.stringify(absent)]);
    }
    expect(seen.map(([route, o, same]) => [route, o.status !== 400, o.router > 0, o.quotaTouched, same]))
      .toEqual(ROUTES.map((route) => [route, true, true, true, true]));
  });

  it("every disabled and unknown vehicle is 400 invalid_request whole on every route, with zero router requests and an untouched quota", async () => {
    const answered: [string, Route, Observation][] = [];
    for (const row of REFUSED) for (const route of ROUTES) answered.push([row.name, route, await observe(route, row.value)]);
    expect(answered).toEqual(REFUSED.flatMap((row) => ROUTES.map((route) => [row.name, route, refusal(route)])));
  });

  it("no row ignores its route: with vehicle \"standard\" each row's body observes the route's baseline, and each row answers every route differently", async () => {
    const baseline = new Map<Route, string>();
    for (const route of ROUTES) baseline.set(route, JSON.stringify(await observe(route, ABSENT)));
    const live: [string, boolean[], number][] = [];
    for (const row of REFUSED) {
      const restored: boolean[] = [];
      const answers = new Set<string>();
      for (const route of ROUTES) {
        const swapped = { ...body(route, row.value), vehicle: "standard" };
        expect(swapped).toEqual(body(route, "standard"));
        restored.push(JSON.stringify(await observe(route, "standard")) === baseline.get(route));
        answers.add(JSON.stringify(await observe(route, row.value)));
      }
      live.push([row.name, restored, answers.size]);
    }
    expect(live).toEqual(REFUSED.map((row) => [row.name, ROUTES.map(() => true), ROUTES.length]));
  });
});
