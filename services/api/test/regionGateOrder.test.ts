/**
 * T-0293 rv1 B1 (R5, P-COST-01): the served-region gate runs BEFORE every precondition that sits after it in a planning
 * handler - the bindings that make deps null (ROUTER_URL, ROUTER_SECRET, QUOTA, DB), the place resolve (an unknown id,
 * a D1 that throws), identify (an account token reads D1), the closures read (CLOSURES bound) and the quota (spent).
 * A refused coordinate costs nothing: 422 whole with ZERO D1 reads, zero KV reads, zero router requests and an
 * untouched quota, through the shipped worker.fetch.
 *
 * Every case is a function of (precondition, route, coordinate): the route's reference body with only its coordinate
 * (and, for the place rows, its destination place) replaced, under the precondition's env. The meta-test proves no
 * row ignores its precondition: INSIDE the region, each row's observation differs from the route's baseline on exactly
 * the routes the row is typed for, and equals it on the rest.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import worker, { type Env } from "../src/index";
import placesSql from "../migrations/0001_places.sql?raw";
import { fakeKv, fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { REACH_BODY } from "./isochroneHarness";
import { LOOP_BODY } from "./loopHarness";
import { NOW, PLACES, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { recordReads, type ReadLog } from "./recordReads";
import { BIG_SUR, TRIP_BODY } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const ACCOUNT_TOKEN = "7c1e2d3f-4a5b-4c6d-8e7f-90a1b2c3d4e5";
const GATED = ["/plan", "/loop", "/isochrone", "/trip"] as const;
type Route = (typeof GATED)[number];
const FIELD: Record<Route, "origin" | "start"> = { "/plan": "origin", "/loop": "start", "/isochrone": "start", "/trip": "origin" };
const REFERENCE: Record<Route, Record<string, unknown>> = {
  "/plan": SANTA_MONICA_TOPANGA_BODY, "/loop": LOOP_BODY, "/isochrone": REACH_BODY, "/trip": TRIP_BODY,
};
/** Between the la and sfbay boxes (Paso Robles): outside the served region, 2 dp, valid for the whitelist. */
const OUTSIDE = { lat: 35.63, lon: -120.69 };

interface Setup {
  drop: ("ROUTER_URL" | "ROUTER_SECRET" | "QUOTA" | "DB")[];
  db: "counted" | "throws";
  place: "reference" | "unknown";
  token: boolean;
  closures: boolean;
  spent: boolean;
}
const BASELINE: Setup = { drop: [], db: "counted", place: "reference", token: false, closures: false, spent: false };
interface Precondition { name: string; setup: Partial<Setup>; routes: readonly Route[] }
/** Every precondition after the gate, and the routes it sits on - typed, and held by the meta-test below. */
const PRECONDITIONS: readonly Precondition[] = [
  { name: "no ROUTER_URL (deps null)", setup: { drop: ["ROUTER_URL"] }, routes: GATED },
  { name: "no ROUTER_SECRET (deps null)", setup: { drop: ["ROUTER_SECRET"] }, routes: GATED },
  { name: "no QUOTA binding (deps null)", setup: { drop: ["QUOTA"] }, routes: GATED },
  { name: "no DB binding (deps null)", setup: { drop: ["DB"] }, routes: ["/plan", "/trip"] },
  { name: "an unknown destination place (the place resolve)", setup: { place: "unknown" }, routes: ["/plan", "/trip"] },
  { name: "a D1 whose prepare throws (the place resolve)", setup: { db: "throws" }, routes: ["/plan", "/trip"] },
  { name: "an account token (identify reads D1)", setup: { token: true }, routes: GATED },
  { name: "a bound CLOSURES namespace (the closures read)", setup: { closures: true }, routes: GATED },
  { name: "today's quota spent (the quota)", setup: { spent: true }, routes: GATED },
];

let quota: FakeQuota;
let routerRequests: string[];

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  routerRequests = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    routerRequests.push(String(input instanceof Request ? input.url : input));
    return new Response(JSON.stringify({ message: "the gate-order test answers every router request 500" }), { status: 500 });
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

interface Observation { status: number; json: unknown; d1: ReadLog; kv: ReadLog; router: number; quotaTouched: boolean }

/** The case (precondition, route, coordinate): the route's reference body and the shipped env, each a function of it. */
async function observe(route: Route, partial: Partial<Setup>, coordinate: { lat: number; lon: number } | null): Promise<Observation> {
  const setup = { ...BASELINE, ...partial };
  quota = fakeQuotaNamespace();
  const d1: ReadLog = [];
  const kv: ReadLog = [];
  const throwing = { prepare: () => { throw new Error("d1 unavailable"); } } as unknown as D1Database;
  const shipped: Record<string, unknown> = {
    DB: recordReads(setup.db === "throws" ? throwing : env.DB, d1), GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
    ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", GRAPH_VERSION: `region-order-${Math.random()}`,
  };
  if (setup.closures) shipped.CLOSURES = recordReads(fakeKv({}), kv);
  for (const key of setup.drop) delete shipped[key];
  if (setup.spent) quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 1000, loop: 1000, surprise: 1000, trip: 1000 });
  const reference = REFERENCE[route];
  const body: Record<string, unknown> = { ...reference };
  if (coordinate !== null) body[FIELD[route]] = coordinate;
  if (setup.place === "unknown" && "destination" in reference) body.destination = { place: "la:no-such-place" };
  const headers: Record<string, string> = { "content-type": "application/json", "x-scenic-device": DEVICE };
  if (setup.token) headers["x-scenic-account-token"] = ACCOUNT_TOKEN;
  const before = JSON.stringify(quota.state());
  const sentBefore = routerRequests.length;
  const response = await worker.fetch(new Request(`https://scenic-api.test${route}`, {
    method: "POST", headers, body: JSON.stringify(body),
  }), shipped as unknown as Env);
  const json = (await response.json()) as unknown;
  return { status: response.status, json, d1, kv, router: routerRequests.length - sentBefore,
    quotaTouched: JSON.stringify(quota.state()) !== before };
}

describe("the region gate precedes every precondition after it (T-0293 rv1 B1, R5, P-COST-01)", () => {
  it("no row ignores its precondition: inside the region each row changes the route's answer on exactly its typed routes", async () => {
    const live: [string, Route[]][] = [];
    for (const row of PRECONDITIONS) {
      const changed: Route[] = [];
      for (const route of GATED) {
        const baseline = await observe(route, {}, null);
        const perturbed = await observe(route, row.setup, null);
        if (JSON.stringify(perturbed) !== JSON.stringify(baseline)) changed.push(route);
      }
      live.push([row.name, changed]);
    }
    expect(live).toEqual(PRECONDITIONS.map((row) => [row.name, [...row.routes]]));
  });

  it("an out-of-region coordinate is 422 region_unsupported whole under every precondition on every route, with zero D1 reads, zero KV reads, zero router requests and an untouched quota", async () => {
    const answered: [string, Route, Observation][] = [];
    for (const row of [{ name: "baseline", setup: {}, routes: GATED }, ...PRECONDITIONS]) {
      for (const route of GATED) answered.push([row.name, route, await observe(route, row.setup, OUTSIDE)]);
    }
    const refused: Observation = { status: 422, json: { error: "region_unsupported" }, d1: [], kv: [], router: 0, quotaTouched: false };
    expect(answered).toEqual(["baseline", ...PRECONDITIONS.map((row) => row.name)]
      .flatMap((name) => GATED.map((route) => [name, route, refused])));
  });
});
