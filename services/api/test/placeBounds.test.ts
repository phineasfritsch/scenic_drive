/**
 * T-0256 rv1: EVERY boundary of d1PlaceResolver's row check, through the SHIPPED ROUTES["/plan"] with deps built
 * from env. A row one step outside any half-bound, or not a number, answers exactly 503 planning_unavailable with
 * zero router requests and nothing reserved; a row exactly on each of the four bounds plans and the router sees it.
 * Rows the shipped DDL can hold go through the real D1 table; null and NaN (which REAL NOT NULL refuses - asserted
 * below) and a numeric string come from a D1 stand-in that answers the row as given.
 */
import { liveClosures } from "./closuresFake";
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { ROUTES, type Env } from "../src/index";
import { fakeQuotaNamespace, recordingRouter, type FakeQuota } from "./doFake";
import { loopPath, squareLoop } from "./loopHarness";
import { NOW, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const LAT = 34.0676;
const LON = -118.5957;

type Row = { lat: unknown; lon: unknown };
const IN_D1: [string, Row][] = [
  ["lat -90.0001", { lat: -90.0001, lon: LON }],
  ["lat 90.0001", { lat: 90.0001, lon: LON }],
  ["lon -180.0001", { lat: LAT, lon: -180.0001 }],
  ["lon 180.0001", { lat: LAT, lon: 180.0001 }],
  ["lat non-numeric text", { lat: "abc", lon: LON }],
  ["lon non-numeric text", { lat: LAT, lon: "abc" }],
];
const FROM_STAND_IN: [string, Row][] = [
  ["lat null", { lat: null, lon: LON }],
  ["lon null", { lat: LAT, lon: null }],
  ["lat NaN", { lat: Number.NaN, lon: LON }],
  ["lon NaN", { lat: LAT, lon: Number.NaN }],
  ["lat Infinity", { lat: Number.POSITIVE_INFINITY, lon: LON }],
  ["lon -Infinity", { lat: LAT, lon: Number.NEGATIVE_INFINITY }],
  ["lat numeric string", { lat: String(LAT), lon: LON }],
  ["lon numeric string", { lat: LAT, lon: String(LON) }],
];
const ON_BOUND: [string, Row][] = [
  ["lat -90", { lat: -90, lon: LON }],
  ["lat 90", { lat: 90, lon: LON }],
  ["lon -180", { lat: LAT, lon: -180 }],
  ["lon 180", { lat: LAT, lon: 180 }],
];
const d1Id = (name: string) => `bound:${name.replace(/ /g, "_")}`;

let quota: FakeQuota;
let router: ReturnType<typeof recordingRouter>;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  for (const [name, row] of [...IN_D1, ...ON_BOUND]) {
    await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES (?1, ?2, ?3)").bind(d1Id(name), row.lat, row.lon).run();
  }
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  router = recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop()));
  vi.stubGlobal("fetch", router.fetchImpl);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function standIn(row: Row): D1Database {
  return { prepare: () => ({ bind: () => ({ first: async () => row }) }) } as unknown as D1Database;
}

async function plan(place: string, db: D1Database) {
  const e = { DB: db, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "test-router-secret", CLOSURES: liveClosures() } as unknown as Env;
  const req = new Request("https://scenic-api.test/plan", {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE },
    body: JSON.stringify({ ...SANTA_MONICA_TOPANGA_BODY, destination: { place } }),
  });
  const response = await ROUTES["/plan"]!(req, e, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

describe("every boundary of the place row check, through the shipped /plan", () => {
  it.each(IN_D1)("D1 row %s is 503 planning_unavailable, zero router requests, nothing reserved", async (name, row) => {
    const stored = await env.DB.prepare("SELECT lat, lon FROM places WHERE id = ?1").bind(d1Id(name)).first();
    expect(stored).toEqual(row);
    expect(await plan(d1Id(name), env.DB)).toEqual({ status: 503, json: { error: "planning_unavailable" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it.each(FROM_STAND_IN)("row %s is 503 planning_unavailable, zero router requests, nothing reserved", async (_name, row) => {
    expect(await plan("la:any", standIn(row))).toEqual({ status: 503, json: { error: "planning_unavailable" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it.each(ON_BOUND)("D1 row exactly on %s plans and the router receives that coordinate", async (name, row) => {
    const answer = await plan(d1Id(name), env.DB);
    expect(answer.status).toBe(200);
    expect(router.calls[0]!.body.points).toEqual([[-118.49, 34.02], [row.lon, row.lat]]);
  });

  it("the shipped DDL refuses a null or NaN coordinate, so only a stand-in can answer one", async () => {
    const insert = "INSERT INTO places (id, lat, lon) VALUES (?1, ?2, ?3)";
    await expect(env.DB.prepare(insert).bind("x:null-lat", null, LON).run()).rejects.toThrow(/NOT NULL/);
    await expect(env.DB.prepare(insert).bind("x:null-lon", LAT, null).run()).rejects.toThrow(/NOT NULL/);
    await expect(env.DB.prepare(insert).bind("x:nan-lat", Number.NaN, LON).run()).rejects.toThrow();
  });
});
