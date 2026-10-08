/**
 * T-0316 through worker.fetch (src/index.ts's default export - the entry point production runs): the trip's overnight
 * towns and corridor stops come from the server's own trip_places table (migrations/0009_trip_places.sql). The
 * cross product {no lodging near a boundary, one, several} x {0, 1, 5 corridor places}, each row the WHOLE answer by
 * full equality; the overnight and stops of each row are hand-placed functions of its variant (R5).
 */
import { liveClosures } from "./closuresFake";
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import tripPlacesSql from "../migrations/0009_trip_places.sql?raw";
import worker, { type Env } from "../src/index";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { BIG_SUR, expectedTrip, NOW, ROAD, SCENIC_EDGE_MS, TRIP_BODY, tripRouter } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
/** Typed out, never imported: the sphere the splitter measures on, and one degree of latitude on it. */
const EARTH_M = 6_371_008.8;
const M_PER_DEG = (EARTH_M * Math.PI) / 180;
/** The preview's day boundaries on the 40-edge road over 5 even days: vertices 8, 16, 24, 32 (40 is B). */
const BOUNDARY = [8, 16, 24, 32];

let quota: FakeQuota;
let router: ReturnType<typeof tripRouter>;
let reads: { sql: string; binds: unknown[] | null }[];

/** env.DB, recording every statement the Worker prepares and what it binds. */
function recordingDb(): D1Database {
  return {
    prepare(sql: string) {
      const read: { sql: string; binds: unknown[] | null } = { sql, binds: null };
      reads.push(read);
      const statement = env.DB.prepare(sql);
      return new Proxy(statement, {
        get(target, key) {
          if (key === "bind") return (...args: unknown[]) => { read.binds = args; return target.bind(...args); };
          const value = Reflect.get(target, key, target) as unknown;
          return typeof value === "function" ? (value as (...a: unknown[]) => unknown).bind(target) : value;
        },
      });
    },
  } as unknown as D1Database;
}

function shippedEnv(over: Record<string, unknown> = {}): Env {
  const e: Record<string, unknown> = { DB: recordingDb(), GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
    ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", CLOSURES: liveClosures(), ...over };
  for (const [key, value] of Object.entries(e)) if (value === undefined) delete e[key];
  return e as unknown as Env;
}

async function send(e: Env = shippedEnv()) {
  const req = new Request("https://scenic-api.test/trip", {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(TRIP_BODY),
  });
  const response = await worker.fetch(req, e);
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

interface Row { id: string; name: string; kind: "stop" | "lodging"; score: number; lat: number; lon: number }
/** A place `northM` metres due north of road vertex v (negative: south). */
const at = (id: string, name: string, kind: Row["kind"], score: number, v: number, northM = 0): Row =>
  ({ id, name, kind, score, lat: ROAD[v]![1] + northM / M_PER_DEG, lon: ROAD[v]![0] });

type Night = { kind: "lodging"; name: string; meters: number } | { kind: "no_lodging" } | { kind: "not_searched" };
const NONE: Night = { kind: "no_lodging" };
const inn = (name: string, meters: number): Night => ({ kind: "lodging", name, meters });

/** Lodging variants: the rows, and the overnight of days 1-4 they must give. */
const LODGING = {
  none: { rows: [at("l-far", "Far Inn", "lodging", 0, 8, 16_000)], nights: [NONE, NONE, NONE, NONE] },
  one: { rows: [at("l-cambria", "Cambria Inn", "lodging", 0, 8, 1_000)], nights: [inn("Cambria Inn", 1_000), NONE, NONE, NONE] },
  several: {
    rows: [at("l-bay", "Bay Inn", "lodging", 0, 8, 2_000), at("l-aloha", "Aloha Motel", "lodging", 0, 8, -3_000),
      at("l-edge", "Edge Lodge", "lodging", 0, 16, 14_990), at("l-past", "Past Lodge", "lodging", 0, 24, 15_010),
      at("l-four", "Day Four Inn", "lodging", 0, 32, 4_000)],
    nights: [inn("Bay Inn", 2_000), inn("Edge Lodge", 14_990), NONE, inn("Day Four Inn", 4_000)],
  },
};
/** Corridor variants: the rows, and the stops of days 1-5 they must give (day 2 owns vertices 9-16). */
const CORRIDOR = {
  zero: { rows: [] as Row[], stops: [[], [], [], [], []] as string[][] },
  one: { rows: [at("s-moon", "Moonstone Beach", "stop", 50, 3)], stops: [["Moonstone Beach"], [], [], [], []] },
  five: {
    rows: [at("s-seals", "Elephant Seals", "stop", 10, 10), at("s-ragged", "Ragged Point", "stop", 90, 11),
      at("s-salmon", "Salmon Creek", "stop", 70, 12), at("s-gorda", "Gorda", "stop", 80, 13),
      at("s-lime", "Limekiln", "stop", 60, 14)],
    stops: [[], ["Ragged Point", "Salmon Creek", "Gorda", "Limekiln"], [], [], []],
  },
};

/** The whole answer for a variant: the T-0268 preview over the road, searched, with the variant's nights and stops. */
function expected(nights: Night[], stops: string[][]) {
  const base = expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: false });
  return { ...base, places_searched: true,
    days: base.days.map((d, i) => ({ ...d, stops: stops[i], overnight: i === 4 ? null : nights[i] })) };
}

async function load(rows: Row[]) {
  await env.DB.prepare("DELETE FROM trip_places").run();
  for (const r of rows) {
    await env.DB.prepare("INSERT INTO trip_places (id, name, kind, score, lat, lon) VALUES (?1, ?2, ?3, ?4, ?5, ?6)")
      .bind(r.id, r.name, r.kind, r.score, r.lat, r.lon).run();
  }
}

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare(`INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('${BIG_SUR.id}', ${BIG_SUR.lat}, ${BIG_SUR.lon})`).run();
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  reads = [];
  router = tripRouter();
  vi.stubGlobal("fetch", router.fetchImpl);
  await env.DB.prepare(tripPlacesSql).run();
  await load([]);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("worker.fetch /trip names overnight towns and corridor stops from trip_places (T-0316 R4, R5)", () => {
  it("the road splits at the boundaries the variants are placed on", () => {
    const days = expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: false }).days;
    expect(days.map((d) => d.end)).toEqual([...BOUNDARY, 40].map((v) => ({ lat: ROAD[v]![1], lon: ROAD[v]![0] })));
  });

  for (const [lodging, l] of Object.entries(LODGING)) {
    for (const [corridor, c] of Object.entries(CORRIDOR)) {
      it(`lodging ${lodging} x corridor ${corridor}: the whole answer`, async () => {
        await load([...l.rows, ...c.rows]);
        expect(await send()).toEqual({ status: 200, json: expected(l.nights, c.stops) });
      });
    }
  }

  it("no row ignores its variant: the nine answers are pairwise distinct", () => {
    const answers = Object.values(LODGING).flatMap((l) => Object.values(CORRIDOR).map((c) => JSON.stringify(expected(l.nights, c.stops))));
    expect(new Set(answers).size).toBe(9);
  });

  it("an empty corpus is searched and says no lodging on every night, honestly", async () => {
    expect(await send()).toEqual({ status: 200, json: expected([NONE, NONE, NONE, NONE], CORRIDOR.zero.stops) });
  });

  it("a trip_places read that fails is not_searched, places_searched false: never claimed as searched", async () => {
    await env.DB.prepare("DROP TABLE trip_places").run();
    expect(await send()).toEqual({ status: 200, json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: false }) });
  });
});

describe("the places read takes nothing from the request (T-0316 R3, P-PRIV-05)", () => {
  it("a trip's D1 statements are the destination lookup and one unbound trip_places read; router bodies carry no place", async () => {
    await load([...LODGING.several.rows, ...CORRIDOR.five.rows]);
    expect((await send()).status).toBe(200);
    expect(reads).toEqual([{ sql: "SELECT lat, lon FROM places WHERE id = ?1", binds: [BIG_SUR.id] },
      { sql: "SELECT name, kind, score, lat, lon FROM trip_places", binds: null }]);
    expect(router.sent.every((s) => Object.keys(s.body).sort().join() ===
      (s.body.profile === "car_fast" ? "ch.disable,details,instructions,points,points_encoded,profile"
        : "ch.disable,custom_model,details,instructions,points,points_encoded,profile"))).toBe(true);
  });

  it("KILL=1 is 503 with zero router requests and no D1 statement at all (P-COST-01)", async () => {
    await load(LODGING.one.rows);
    expect(await send(shippedEnv({ KILL: "1" }))).toEqual({ status: 503, json: { error: "planning_paused" } });
    expect(router.sent).toEqual([]);
    expect(reads).toEqual([]);
  });
});

describe("the trip_places table (migrations/0009_trip_places.sql, T-0316 R1)", () => {
  it("its columns are exactly (id, name, kind, score, lat, lon): no device, no instant (P-PRIV-05)", async () => {
    const info = await env.DB.prepare("SELECT name FROM pragma_table_info('trip_places') ORDER BY cid").all();
    expect((info.results as { name: string }[]).map((c) => c.name)).toEqual(["id", "name", "kind", "score", "lat", "lon"]);
  });

  const up = (x: number) => x + Math.max(Number.MIN_VALUE, Math.abs(x) * Number.EPSILON);
  const down = (x: number) => -up(-x);
  const ok = { name: "Inn", kind: "lodging", score: 1, lat: 35, lon: -120 };
  const CASES: [string, Record<string, unknown>, boolean][] = [
    ["a valid row", {}, true], ["lat exactly 90", { lat: 90 }, true], ["lat exactly -90", { lat: -90 }, true],
    ["lon exactly 180", { lon: 180 }, true], ["lon exactly -180", { lon: -180 }, true], ["kind stop", { kind: "stop" }, true],
    ["lat just above 90", { lat: up(90) }, false], ["lat just below -90", { lat: down(-90) }, false],
    ["lon just above 180", { lon: up(180) }, false], ["lon just below -180", { lon: down(-180) }, false],
    ["lat text", { lat: "north" }, false], ["lon text", { lon: "west" }, false], ["lat null", { lat: null }, false],
    ["kind hotel", { kind: "hotel" }, false], ["kind Lodging", { kind: "Lodging" }, false], ["kind null", { kind: null }, false],
    ["score 1.5", { score: 1.5 }, false], ["score text", { score: "high" }, false], ["score null", { score: null }, false],
    ["name empty", { name: "" }, false], ["name null", { name: null }, false],
  ];
  for (const [name, over, accepted] of CASES) {
    it(`${name} is ${accepted ? "accepted" : "refused"}`, async () => {
      const r = { ...ok, ...over };
      const insert = env.DB.prepare("INSERT INTO trip_places (id, name, kind, score, lat, lon) VALUES ('x', ?1, ?2, ?3, ?4, ?5)")
        .bind(r.name, r.kind, r.score, r.lat, r.lon).run();
      if (accepted) await expect(insert).resolves.toBeTruthy();
      else await expect(insert).rejects.toThrow();
      const { results } = await env.DB.prepare("SELECT name, kind, score, lat, lon FROM trip_places").all();
      expect(results).toEqual(accepted ? [r] : []);
    });
  }
});
