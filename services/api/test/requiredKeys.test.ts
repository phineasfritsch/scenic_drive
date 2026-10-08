/**
 * T-0311 rv1 B1 (P-PRIV-05): the key tables of the three coordinate parsers - /plan, /loop, /trip - through the
 * shipped worker.fetch. Every level of every body has an allowed list AND a required list; each row is a function
 * of (route, level, variant, key): one required key missing, every required key at that level missing, or one key
 * the level does not name. Each is 400 invalid_request with its exact detail, zero router requests and an
 * untouched quota. The required lists are written here as literals, never imported from src.
 *
 * The meta-test proves no row ignores its key: undoing the row's one edit gives back the route's reference body,
 * which the Worker accepts (it spends the quota and calls the router), and every one-key-missing row of a route
 * answers differently from every other.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import worker, { type Env } from "../src/index";
import placesSql from "../migrations/0001_places.sql?raw";
import { fakeQuotaNamespace } from "./doFake";
import { LOOP_BODY } from "./loopHarness";
import { NOW, PLACES, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { BIG_SUR, TRIP_BODY } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const ROUTES = ["/plan", "/loop", "/trip"] as const;
type Route = (typeof ROUTES)[number];
type Body = Record<string, unknown>;
const REFERENCE: Record<Route, Body> = { "/plan": SANTA_MONICA_TOPANGA_BODY, "/loop": LOOP_BODY, "/trip": TRIP_BODY };
const TOP = "the body";
/** Each route's required keys per level, in the order the parser checks them; TOP is the body itself. */
const REQUIRED: Record<Route, [string, string[]][]> = {
  "/plan": [[TOP, ["origin", "destination", "budget_minutes"]], ["origin", ["lat", "lon"]], ["destination", ["place"]]],
  "/loop": [[TOP, ["start", "minutes"]], ["start", ["lat", "lon"]]],
  "/trip": [[TOP, ["origin", "destination", "days"]], ["origin", ["lat", "lon"]], ["destination", ["place"]]],
};
const EXTRA = "second";
const SECOND_COORDINATE = { lat: 36.27, lon: -121.81 };

interface Row { name: string; route: Route; variant: "missing" | "all missing" | "extra"; level: string; keys: string[] }

const ROWS: Row[] = ROUTES.flatMap((route) => REQUIRED[route].flatMap(([level, keys]): Row[] => [
  ...keys.map((key) => ({ name: `${route} ${level} without ${key}`, route, variant: "missing" as const, level, keys: [key] })),
  { name: `${route} ${level} without any of ${keys.join(", ")}`, route, variant: "all missing", level, keys },
  { name: `${route} ${level} with ${EXTRA}`, route, variant: "extra", level, keys: [EXTRA] },
]));

function reference(route: Route): Body {
  return JSON.parse(JSON.stringify(REFERENCE[route])) as Body;
}

function at(body: Body, level: string): Body {
  return (level === TOP ? body : body[level]) as Body;
}

/** The row's body: the route's reference body with only the row's edit at the row's level. */
function rowBody(row: Row): Body {
  const built = reference(row.route);
  const target = at(built, row.level);
  for (const key of row.keys) {
    if (row.variant === "extra") target[key] = SECOND_COORDINATE;
    else delete target[key];
  }
  return built;
}

/** The row's edit undone: what the meta-test must find equal to the reference body. */
function undone(row: Row): Body {
  const built = rowBody(row);
  const target = at(built, row.level);
  const original = at(reference(row.route), row.level);
  for (const key of row.keys) {
    if (row.variant === "extra") delete target[key];
    else target[key] = original[key];
  }
  return built;
}

/** The detail, recomputed from the row: the first missing required key, or the key the level does not name. */
function detail(row: Row): string {
  if (row.variant === "extra") return `${row.level} carries ${JSON.stringify(EXTRA)}, which ${row.route} does not accept`;
  return `${row.level} needs ${row.keys[0]}`;
}

interface Observation { status: number; json: unknown; router: number; quotaTouched: boolean }

let routerRequests: string[];

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  routerRequests = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    routerRequests.push(String(input instanceof Request ? input.url : input));
    return new Response(JSON.stringify({ message: "the key-table test answers every router request 500" }), { status: 500 });
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

async function observe(route: Route, body: Body): Promise<Observation> {
  const quota = fakeQuotaNamespace();
  const shipped: Record<string, unknown> = {
    DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
    ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", GRAPH_VERSION: `keys-${Math.random()}`,
  };
  const before = JSON.stringify(quota.state());
  const sentBefore = routerRequests.length;
  const response = await worker.fetch(new Request(`https://scenic-api.test${route}`, {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(body),
  }), shipped as unknown as Env);
  const json = (await response.json()) as unknown;
  return { status: response.status, json, router: routerRequests.length - sentBefore,
    quotaTouched: JSON.stringify(quota.state()) !== before };
}

describe("every required key and every unnamed key at each level of /plan, /loop and /trip (T-0311 rv1 B1, P-PRIV-05)", () => {
  it("every row is 400 invalid_request with its exact detail, zero router requests and an untouched quota", async () => {
    const answered: [string, Observation][] = [];
    for (const row of ROWS) answered.push([row.name, await observe(row.route, rowBody(row))]);
    expect(answered).toEqual(ROWS.map((row) => [row.name, {
      status: 400, json: { error: "invalid_request", detail: detail(row) }, router: 0, quotaTouched: false }]));
  });

  it("no row ignores its key: undoing each row's edit gives the reference body the Worker accepts, and each missing key answers differently", async () => {
    const accepted: [Route, boolean, boolean][] = [];
    for (const route of ROUTES) {
      const o = await observe(route, reference(route));
      accepted.push([route, o.status !== 400 && o.router > 0, o.quotaTouched]);
    }
    expect(accepted).toEqual(ROUTES.map((route) => [route, true, true]));
    expect(ROWS.map((row) => [row.name, undone(row)])).toEqual(ROWS.map((row) => [row.name, reference(row.route)]));
    expect(ROWS.map((row) => [row.name, JSON.stringify(rowBody(row)) === JSON.stringify(reference(row.route))]))
      .toEqual(ROWS.map((row) => [row.name, false]));
    const distinct: [Route, number, number][] = [];
    for (const route of ROUTES) {
      const missing = ROWS.filter((row) => row.route === route && row.variant === "missing");
      const answers = new Set<string>();
      for (const row of missing) answers.add(JSON.stringify(await observe(route, rowBody(row))));
      distinct.push([route, answers.size, missing.length]);
    }
    expect(distinct).toEqual(ROUTES.map((route) => [route, REQUIRED[route].flatMap(([, keys]) => keys).length,
      REQUIRED[route].flatMap(([, keys]) => keys).length]));
  });
});
