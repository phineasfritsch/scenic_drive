/**
 * T-0268 R1: the /trip body against its WHITELIST, at EVERY bound. Each row is held twice: parseTripRequest's whole
 * result by full equality, and the same body through the shipped ROUTES["/trip"] - a refusal is 400 invalid_request
 * with the same detail, zero router requests and nothing reserved; an exact bound is ACCEPTED, and its first router
 * request carries the origin as sent. "Just outside" is the next double past each bound (Number.EPSILON steps).
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { ROUTES, type Env } from "../src/index";
import { parseTripRequest } from "../src/tripRequest";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { BIG_SUR, NOW, ORIGIN, tripRouter } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const BASE = { origin: ORIGIN, destination: { place: BIG_SUR.id }, days: 3 };
const DAYS = "days must be a whole number of days in [1, 5]";
const PCT = "extra_budget_pct must be a whole percent in [0, 40]";
const LAT_RANGE = "origin.lat is outside [-90, 90]";
const LON_RANGE = "origin.lon is outside [-180, 180]";
const NOT_FINITE = (f: string) => `origin.${f} is not a finite number`;
const PLACE = "destination.place is not a corpus place id";

const with_ = (over: Record<string, unknown>) => ({ ...BASE, ...over });
const at = (lat: unknown, lon: unknown) => with_({ origin: { lat, lon } });
const accepted = (lat: number, lon: number, days: number, extraBudgetPct: number) =>
  ({ ok: true, request: { origin: { lat, lon }, destinationPlace: BIG_SUR.id, days, extraBudgetPct } });

const BELOW_1 = 1 - Number.EPSILON / 2;
const ABOVE_5 = 5 + 4 * Number.EPSILON;
const ABOVE_40 = 40 + 32 * Number.EPSILON;
const ABOVE_90 = 90 + 64 * Number.EPSILON;
const ABOVE_180 = 180 + 128 * Number.EPSILON;

const REFUSED: [string, unknown, string][] = [
  ["days 0", with_({ days: 0 }), DAYS],
  ["days one ulp under 1", with_({ days: BELOW_1 }), DAYS],
  ["days one ulp over 5", with_({ days: ABOVE_5 }), DAYS],
  ["days 6", with_({ days: 6 }), DAYS],
  ["days 2.5", with_({ days: 2.5 }), DAYS],
  ["days NaN", with_({ days: NaN }), DAYS],
  ["days Infinity", with_({ days: Infinity }), DAYS],
  ["days null", with_({ days: null }), DAYS],
  ["days a string", with_({ days: "3" }), DAYS],
  ["days a bool", with_({ days: true }), DAYS],
  ["no days", { origin: ORIGIN, destination: { place: BIG_SUR.id } }, "the body needs days"],
  ["pct -1", with_({ extra_budget_pct: -1 }), PCT],
  ["pct one ulp under 0", with_({ extra_budget_pct: -Number.MIN_VALUE }), PCT],
  ["pct one ulp over 40", with_({ extra_budget_pct: ABOVE_40 }), PCT],
  ["pct 41", with_({ extra_budget_pct: 41 }), PCT],
  ["pct 12.5", with_({ extra_budget_pct: 12.5 }), PCT],
  ["pct NaN", with_({ extra_budget_pct: NaN }), PCT],
  ["pct -Infinity", with_({ extra_budget_pct: -Infinity }), PCT],
  ["pct null", with_({ extra_budget_pct: null }), PCT],
  ["pct a string", with_({ extra_budget_pct: "40" }), PCT],
  ["pct a bool", with_({ extra_budget_pct: false }), PCT],
  ["lat one ulp over 90", at(ABOVE_90, ORIGIN.lon), LAT_RANGE],
  ["lat one ulp under -90", at(-ABOVE_90, ORIGIN.lon), LAT_RANGE],
  ["lon one ulp over 180", at(ORIGIN.lat, ABOVE_180), LON_RANGE],
  ["lon one ulp under -180", at(ORIGIN.lat, -ABOVE_180), LON_RANGE],
  ["lat 3 decimals", at(34.021, ORIGIN.lon), "origin.lat has more than 2 decimals; round it on the device"],
  ["lon 3 decimals", at(ORIGIN.lat, -118.491), "origin.lon has more than 2 decimals; round it on the device"],
  ["lat NaN", at(NaN, ORIGIN.lon), NOT_FINITE("lat")],
  ["lat Infinity", at(Infinity, ORIGIN.lon), NOT_FINITE("lat")],
  ["lat null", at(null, ORIGIN.lon), NOT_FINITE("lat")],
  ["lat a string", at("34.02", ORIGIN.lon), NOT_FINITE("lat")],
  ["lon a bool", at(ORIGIN.lat, true), NOT_FINITE("lon")],
  ["a second coordinate at the top", with_({ destination_lat: 36.27 }), 'the body carries "destination_lat", which /trip does not accept'],
  ["an origin with a third key", with_({ origin: { ...ORIGIN, alt: 3 } }), 'origin carries "alt", which /trip does not accept'],
  ["a destination with a coordinate", with_({ destination: { place: BIG_SUR.id, lat: 36.27 } }), 'destination carries "lat", which /trip does not accept'],
  ["an origin without lon", with_({ origin: { lat: 34.02 } }), "origin needs lon"],
  ["no destination", { origin: ORIGIN, days: 3 }, "the body needs destination"],
  ["an origin that is a pair", with_({ origin: [34.02, -118.49] }), "origin must be {lat, lon}"],
  ["a destination that is a string", with_({ destination: BIG_SUR.id }), "destination must be {place}"],
  ["an empty place", with_({ destination: { place: "" } }), PLACE],
  ["a place with a space", with_({ destination: { place: "la:big sur" } }), PLACE],
  ["a 129-character place", with_({ destination: { place: "a".repeat(129) } }), PLACE],
  ["a numeric place", with_({ destination: { place: 7 } }), PLACE],
  ["an array body", [BASE], "the body must be a JSON object"],
];

const ACCEPTED: [string, unknown, ReturnType<typeof accepted>][] = [
  ["days 1, the lower bound", with_({ days: 1 }), accepted(ORIGIN.lat, ORIGIN.lon, 1, 40)],
  ["days 5, the upper bound", with_({ days: 5 }), accepted(ORIGIN.lat, ORIGIN.lon, 5, 40)],
  ["pct 0, the lower bound", with_({ extra_budget_pct: 0 }), accepted(ORIGIN.lat, ORIGIN.lon, 3, 0)],
  ["pct 40, the upper bound", with_({ extra_budget_pct: 40 }), accepted(ORIGIN.lat, ORIGIN.lon, 3, 40)],
  ["pct absent is the plan's 40", BASE, accepted(ORIGIN.lat, ORIGIN.lon, 3, 40)],
  ["lat 90 and lon 180", at(90, 180), accepted(90, 180, 3, 40)],
  ["lat -90 and lon -180", at(-90, -180), accepted(-90, -180, 3, 40)],
  ["a 128-character place", with_({ destination: { place: "a".repeat(128) } }),
    { ok: true, request: { origin: ORIGIN, destinationPlace: "a".repeat(128), days: 3, extraBudgetPct: 40 } }],
];

describe("parseTripRequest at every bound (R1)", () => {
  it("each just-outside value is a different double from its bound", () => {
    expect([BELOW_1 < 1, ABOVE_5 > 5, ABOVE_40 > 40, ABOVE_90 > 90, ABOVE_180 > 180, -Number.MIN_VALUE < 0])
      .toEqual([true, true, true, true, true, true]);
  });

  it("every refused body is refused with its own detail", () => {
    expect(REFUSED.map(([name, body]) => [name, parseTripRequest(body)]))
      .toEqual(REFUSED.map(([name, , problem]) => [name, { ok: false, problem }]));
  });

  it("every exact bound is accepted with the whole request", () => {
    expect(ACCEPTED.map(([name, body]) => [name, parseTripRequest(body)])).toEqual(ACCEPTED.map(([name, , r]) => [name, r]));
  });
});

let quota: FakeQuota;
let router: ReturnType<typeof tripRouter>;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare(`INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('${BIG_SUR.id}', ${BIG_SUR.lat}, ${BIG_SUR.lon}), ('${"a".repeat(128)}', ${BIG_SUR.lat}, ${BIG_SUR.lon})`).run();
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  router = tripRouter();
  vi.stubGlobal("fetch", router.fetchImpl);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const shippedEnv = (): Env => ({
  DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
  ROUTER_SECRET: "test-router-secret",
} as unknown as Env);

/** JSON with Infinity spelled 1e999, which JSON.parse reads back as Infinity; NaN has no JSON spelling. */
function wire(body: unknown): string {
  return JSON.stringify(body, (_k, v) => (v === Infinity ? "__INF__" : v === -Infinity ? "__NINF__" : v))
    .replaceAll('"__INF__"', "1e999").replaceAll('"__NINF__"', "-1e999");
}

async function send(body: unknown) {
  const req = new Request("https://scenic-api.test/trip", {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: wire(body),
  });
  const response = await ROUTES["/trip"]!(req, shippedEnv(), new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

describe("ROUTES['/trip'] at every bound (R1)", () => {
  it("every wire-expressible refusal is 400 invalid_request with its detail, zero router requests, nothing reserved", async () => {
    const nanFree = REFUSED.filter(([name]) => !name.includes("NaN"));
    const answered = [];
    for (const [name, body] of nanFree) answered.push([name, await send(body)]);
    expect(answered).toEqual(nanFree.map(([name, , detail]) => [name, { status: 400, json: { error: "invalid_request", detail } }]));
    expect(router.sent).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("every exact bound is accepted through the shipped route: 200, and the first router request carries that origin", async () => {
    const answered = [];
    for (const [name, body] of ACCEPTED) {
      quota = fakeQuotaNamespace();
      router = tripRouter();
      vi.stubGlobal("fetch", router.fetchImpl);
      const r = await send(body);
      answered.push([name, r.status, router.sent[0]?.body.points, (r.json.days as unknown[] | undefined)?.length, r.json.extra_budget_pct]);
    }
    expect(answered).toEqual(ACCEPTED.map(([name, , parsed]) => {
      const { origin, days, extraBudgetPct } = parsed.request;
      return [name, 200, [[origin.lon, origin.lat], [BIG_SUR.lon, BIG_SUR.lat]], days, extraBudgetPct];
    }));
  });
});
