/**
 * T-0276 R7-R10 through the SHIPPED ROUTES, deps built from env: /plan, /loop, /trip and /isochrone read CLOSURES
 * once, after the kill switch; a fresh set rides every driven request as buildCustomModel's areas; a stale one
 * (P-SAFE-08, 30 min) still rides - the last good set - with closures_hazard in the 200; an unavailable one routes
 * without areas and says so; /isochrone's cache key carries the closures-version.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { CLOSURES_KEY } from "../src/closuresStore";
import { buildCustomModel, rejectCustomModel, type ClosureCollection } from "../src/customModel";
import { ROUTES, type Env } from "../src/index";
import { LOOP_LAMBDA } from "../src/loopPlanner";
import { closuresAt, closuresKv, closuresRecord, EMPTY_CLOSURES, squareClosure, TEST_VERSION, TWO_CLOSURES, type ClosuresKv } from "./closuresFake";
import { fakeQuotaNamespace } from "./doFake";
import { isochroneRouter, REACH_BODY } from "./isochroneHarness";
import { LOOP_BODY, loopPath, squareLoop } from "./loopHarness";
import { SANTA_MONICA_TOPANGA_BODY, syntheticPath } from "./planHarness";
import { TRIP_BODY, tripRouter } from "./tripHarness";

const NOW = new Date("2026-10-05T12:00:00Z");
/** P-SAFE-08's 30 minutes, ruled (R7) - a literal, never the module's own MAX_AGE_MS. */
const MAX_AGE_MS = 1_800_000;
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const AREAS = buildCustomModel(0, TWO_CLOSURES as ClosureCollection).areas;
const IN_CLOSURES = { if: "in_closure_1 || in_closure_2", multiply_by: "0" };
type Path = "/plan" | "/loop" | "/trip" | "/isochrone";
const BODIES: Record<Path, unknown> = { "/plan": SANTA_MONICA_TOPANGA_BODY, "/loop": LOOP_BODY, "/trip": TRIP_BODY, "/isochrone": REACH_BODY };

let sent: { url: string; body: Record<string, unknown> | null }[];
let graph = 0;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957), ('la:big-sur', 36.27, -121.81)").run();
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  sent = [];
  const trip = tripRouter();
  const reach = isochroneRouter();
  vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input instanceof Request ? input.url : input);
    if (url.includes("/isochrone")) {
      sent.push({ url, body: null });
      return reach.fetchImpl(input, init);
    }
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push({ url, body });
    if (body.algorithm === "round_trip") return new Response(loopPath(squareLoop()));
    if (JSON.stringify(body.points).includes("-121.81")) return trip.fetchImpl(input, init);
    return new Response(body.profile === "car_fast" ? syntheticPath(1_000_000, [1, 2, 3]) : syntheticPath(1_200_000, [4, 5, 6]));
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function shipped(closures: KVNamespace | undefined, over: Record<string, unknown> = {}): Env {
  graph += 1;
  const e: Record<string, unknown> = { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: fakeQuotaNamespace().ns,
    ROUTER_URL: "https://router.test", ROUTER_SECRET: "s", GRAPH_VERSION: `closures-graph-${graph}`, CLOSURES: closures, ...over };
  for (const [key, value] of Object.entries(e)) if (value === undefined) delete e[key];
  return e as unknown as Env;
}

async function send(path: Path, e: Env) {
  const req = new Request(`https://scenic-api.test${path}`, { method: "POST",
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(BODIES[path]) });
  const response = await ROUTES[path]!(req, e, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

/** The models of every request that carries one, and whether a car_fast probe carried any. */
const models = () => sent.flatMap((s) => (s.body?.custom_model === undefined ? [] : [s.body.custom_model as Record<string, any>]));
const fastWithModel = () => sent.filter((s) => s.body?.profile === "car_fast" && s.body.custom_model !== undefined).length;

const ROUTED: Path[] = ["/plan", "/loop", "/trip"];

describe("a fresh set rides every driven request as areas (R7, R8)", () => {
  for (const path of ROUTED) {
    it(`${path}: 200 with no closures_hazard; every model carries the areas and the zero clause, gate-clean; no car_fast model`, async () => {
      const r = await send(path, shipped(closuresAt(new Date(NOW.getTime() - MAX_AGE_MS), TWO_CLOSURES).kv));
      const m = models();
      expect([r.status, "closures_hazard" in r.json, m.length > 0, fastWithModel()]).toEqual([200, false, true, 0]);
      expect(m.map((x) => [x.areas, x.priority.at(-1), rejectCustomModel(x)])).toEqual(m.map(() => [AREAS, IN_CLOSURES, null]));
    });
  }

  it("/loop's round trip is buildCustomModel(LOOP_LAMBDA, the set), whole", async () => {
    await send("/loop", shipped(closuresAt(NOW, TWO_CLOSURES).kv));
    expect(models()).toEqual([buildCustomModel(LOOP_LAMBDA, TWO_CLOSURES as ClosureCollection)]);
  });
});

describe("stale: the last good set, with the hazard (R7, P-SAFE-08)", () => {
  const ages: [string, number][] = [["30 min + 1 ms old", MAX_AGE_MS + 1], ["45 min old", 2_700_000], ["1 ms in the future", -1], ["a day old", 86_400_000]];
  for (const path of [...ROUTED, "/isochrone"] as Path[]) {
    for (const [name, age] of ages) {
      it(`${path}, a record ${name}: 200 with closures_hazard stale, routed around the record's set`, async () => {
        const at = new Date(NOW.getTime() - age);
        const r = await send(path, shipped(closuresAt(at, TWO_CLOSURES).kv));
        expect([r.status, r.json.closures_hazard]).toEqual([200, { state: "stale", version: TEST_VERSION, fetched_at: at.toISOString() }]);
        expect(models().map((x) => x.areas)).toEqual(models().map(() => AREAS));
      });
    }
  }

  it("a record exactly 0 ms old is fresh", async () => {
    const r = await send("/plan", shipped(closuresAt(NOW, TWO_CLOSURES).kv));
    expect([r.status, r.json.closures_hazard]).toEqual([200, undefined]);
  });
});

describe("unavailable: no set, never silent (R7)", () => {
  const record = (over: Record<string, unknown>) => JSON.stringify({ version: TEST_VERSION, fetched_at: NOW.toISOString(), geojson: TWO_CLOSURES, ...over });
  const fiftyOne = { type: "FeatureCollection", features: Array.from({ length: 51 }, (_, i) => squareClosure(-118.6 + i * 0.01, 34.05)) };
  const raw = (text: string) => () => closuresKv({ [CLOSURES_KEY]: text });
  const bad = (field: string, value: unknown) => () => closuresKv({ [CLOSURES_KEY]: record({ [field]: value }) });
  /** Every field record() reads x every shape that is not one: missing, null, wrong type, empty, off the format. */
  const shapes: [string, unknown][] = [["missing", undefined], ["null", null], ["a number", 16], ["true", true],
    ["an empty string", ""], ["an empty array", []], ["an empty object", {}]];
  const cases: [string, () => ClosuresKv | undefined][] = [
    ["no CLOSURES binding", () => undefined],
    ["a get that throws", () => closuresKv({}, true)],
    ["no record", () => closuresKv({})],
    ["a record that is not JSON", raw("{")],
    ["a record that is an empty string", raw("")],
    ["a record that is JSON null", raw("null")],
    ["a record that is a number", raw("7")],
    ["a record that is a string", raw(JSON.stringify(record({})))],
    ["a record that is an array", raw(`[${record({})}]`)],
    ["a record that is an empty object", raw("{}")],
    ...(["version", "fetched_at", "geojson"] as const).flatMap((field) =>
      shapes.map(([name, value]): [string, () => ClosuresKv] => [`${field} ${name}`, bad(field, value)])),
    ["a version off the pattern", bad("version", "lcs-d7-XYZ")],
    ["a version of 15 hex", bad("version", "lcs-d7-00000000000000a")],
    ["a version of 17 hex", bad("version", "lcs-d7-00000000000000aaa")],
    ["a version in upper-case hex", bad("version", "lcs-d7-00000000000000AA")],
    ["a version of another district", bad("version", "lcs-d4-00000000000000aa")],
    ["a version with a trailing newline", bad("version", `${TEST_VERSION}\n`)],
    ["a version wrapped in an array", bad("version", [TEST_VERSION])],
    ["a fetched_at that is not an instant", bad("fetched_at", "2026-10-05 12:00")],
    ["a fetched_at with an offset, not Z", bad("fetched_at", "2026-10-05T12:00:00+00:00")],
    ["a fetched_at as epoch ms", bad("fetched_at", NOW.getTime())],
    ["a fetched_at wrapped in an array", bad("fetched_at", [NOW.toISOString()])],
    ["a fetched_at in month 13", bad("fetched_at", "2026-13-05T12:00:00Z")],
    ["a fetched_at at hour 25", bad("fetched_at", "2026-10-05T25:00:00Z")],
    ["a geojson that is a string", bad("geojson", JSON.stringify(TWO_CLOSURES))],
    ["a geojson that is one Feature", bad("geojson", TWO_CLOSURES.features[0])],
    ["a geojson with no features", bad("geojson", { type: "FeatureCollection" })],
    ["a geojson whose features are an object", bad("geojson", { type: "FeatureCollection", features: {} })],
    ["a geojson whose features are null", bad("geojson", { type: "FeatureCollection", features: null })],
    ["a geojson with no type", bad("geojson", { features: TWO_CLOSURES.features })],
    ["51 polygons", bad("geojson", fiftyOne)],
    ["a closure that is a Point", bad("geojson", { type: "FeatureCollection",
      features: [{ type: "Feature", geometry: { type: "Point", coordinates: [-118.6, 34.05] } }] })],
  ];
  for (const path of [...ROUTED, "/isochrone"] as Path[]) {
    for (const [name, make] of cases) {
      it(`${path}, ${name}: 200 with closures_hazard unavailable and no areas`, async () => {
        const r = await send(path, shipped(make()?.kv));
        expect([r.status, r.json.closures_hazard, models().filter((x) => x.areas !== undefined).length])
          .toEqual([200, { state: "unavailable", version: "none", fetched_at: null }, 0]);
      });
    }
  }
});

describe("read, by ruling: shapes the reader accepts are fresh, routed around exactly their set (R6, R7)", () => {
  const cases: [string, string, unknown][] = [
    ["a FeatureCollection with zero features (R6 writes it when nothing is active)", closuresRecord(NOW, EMPTY_CLOSURES), undefined],
    ["an unknown extra key (the reader is not strict; stats rides already)", JSON.stringify({ version: TEST_VERSION,
      fetched_at: NOW.toISOString(), geojson: TWO_CLOSURES, stats: { kept: 2 }, extra: true }), AREAS],
    ["a version that is not sha256(geojson) (the version is a cache key, never a gate)", closuresRecord(NOW, TWO_CLOSURES,
      "lcs-d7-ffffffffffffffff"), AREAS],
  ];
  for (const path of ROUTED) {
    for (const [name, text, areas] of cases) {
      it(`${path}, ${name}: 200, no closures_hazard, areas exactly the record's`, async () => {
        const r = await send(path, shipped(closuresKv({ [CLOSURES_KEY]: text }).kv));
        const m = models();
        expect([r.status, r.json.closures_hazard, m.length > 0, m.map((x) => x.areas)]).toEqual([200, undefined, true, m.map(() => areas)]);
      });
    }
  }
});

describe("KILL first, the closures-version in the cache key (R9, R10)", () => {
  for (const path of [...ROUTED, "/isochrone"] as Path[]) {
    it(`${path}: KILL=1 is 503 with zero closures reads and zero router requests`, async () => {
      const k = closuresAt(NOW, TWO_CLOSURES);
      const r = await send(path, shipped(k.kv, { KILL: "1" }));
      expect([r.status, k.gets, sent.length]).toEqual([503, [], 0]);
    });

    it(`${path}: a request reads closures exactly once`, async () => {
      const k = closuresAt(NOW, TWO_CLOSURES);
      await send(path, shipped(k.kv));
      expect(k.gets).toEqual([CLOSURES_KEY]);
    });
  }

  it("/isochrone: the same closures-version hits the cache; a new version misses it; a hit carries the hazard", async () => {
    const e = shipped(closuresAt(NOW).kv) as unknown as Record<string, unknown>;
    await send("/isochrone", e as unknown as Env);
    await send("/isochrone", e as unknown as Env);
    const misses = [sent.length];
    e.CLOSURES = closuresAt(NOW, undefined, "lcs-d7-00000000000000bb").kv;
    await send("/isochrone", e as unknown as Env);
    misses.push(sent.length);
    e.CLOSURES = closuresKv({ [CLOSURES_KEY]: closuresRecord(new Date(NOW.getTime() - MAX_AGE_MS - 1), undefined, "lcs-d7-00000000000000bb") }).kv;
    const hit = await send("/isochrone", e as unknown as Env);
    misses.push(sent.length);
    expect([misses, hit.json.closures_hazard]).toEqual([[1, 2, 2],
      { state: "stale", version: "lcs-d7-00000000000000bb", fetched_at: new Date(NOW.getTime() - MAX_AGE_MS - 1).toISOString() }]);
  });
});
