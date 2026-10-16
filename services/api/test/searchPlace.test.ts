/**
 * T-0362 R1-R5 (P-PRIV-05): a searched address reaches /plan as the place id /search issued, never as a coordinate.
 * /search runs through the SHIPPED ROUTES["/search"]; /plan through handlePlan, the handler ROUTES["/plan"] runs, with
 * the counting harness (planPrivacy's precedent) and the production kvSearchPlaces over a recording KV.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES } from "../src/index";
import { handlePlan, planDepsFromEnv, type PlanDeps } from "../src/plan";
import { sweepPlans } from "../src/planSweep";
import { isSearchPlaceId, kvSearchPlaces, SEARCH_PLACE_ID, SEARCH_PLACE_TTL_SECONDS } from "../src/searchPlaces";
import { fakeQuotaNamespace } from "./doFake";
import { harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { DEVICE, feature, NOW, SEARCH_BODY, searchEnv, searchRequest } from "./searchHarness";

class RecordingKv {
  readonly values = new Map<string, string>();
  readonly puts: [string, string, unknown][] = [];
  failPut: (key: string) => boolean = () => false;
  failGet = false;
  async get(key: string): Promise<string | null> {
    if (this.failGet) throw new Error("kv down");
    return this.values.get(key) ?? null;
  }
  async put(key: string, value: string, options: { expirationTtl: number }): Promise<void> {
    this.puts.push([key, value, options]);
    if (this.failPut(key)) throw new Error("kv down");
    this.values.set(key, value);
  }
}

const CA = { city: "Los Angeles", state: "California" };
const ROWS = [
  { label: "Griffith Observatory, Los Angeles, California", lat: 34.1184, lon: -118.3004 },
  { label: "Mulholland Drive, Los Angeles, California", lat: 34.13, lon: -118.45 },
];
const PHOTON = {
  features: [feature({ name: "Griffith Observatory", ...CA }, [-118.3004, 34.1184]),
    feature({ street: "Mulholland Drive", ...CA }, [-118.45, 34.13])],
};

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  vi.stubGlobal("fetch", async () => new Response(JSON.stringify(PHOTON), { status: 200 }));
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function search(kv: RecordingKv | null, headers: Record<string, string> = {}) {
  const req = searchRequest(SEARCH_BODY, headers);
  const env = searchEnv(fakeQuotaNamespace(), kv ? { PLANS: kv } : {});
  const response = await ROUTES["/search"]!(req, env, new URL(req.url));
  return { status: response.status, json: (await response.json()) as { results: { place?: string }[] } };
}

describe("POST /search issues one place id per result (T-0362 R1, R5)", () => {
  it("answers every row with the id it wrote, and writes exactly the row's coordinate under this device", async () => {
    const kv = new RecordingKv();
    const answer = await search(kv);
    const ids = answer.json.results.map((row) => String(row.place));
    expect(answer).toEqual({ status: 200, json: { results: ROWS.map((row, i) => ({ ...row, place: ids[i] })) } });
    expect(kv.puts).toEqual(ROWS.map((row, i) => [`plan:${DEVICE}:${ids[i]}`, JSON.stringify({ lat: row.lat, lon: row.lon }),
      { expirationTtl: SEARCH_PLACE_TTL_SECONDS }]));
    expect([SEARCH_PLACE_TTL_SECONDS, new Set(ids).size, ids.every((id) => isSearchPlaceId(id))]).toEqual([86_400, 2, true]);
  });

  it("answers T-0359's rows exactly, with no place, when PLANS is unbound", async () => {
    expect(await search(null)).toEqual({ status: 200, json: { results: ROWS } });
  });

  it("answers a row whose write failed without a place, and the others with theirs", async () => {
    const kv = new RecordingKv();
    let first = true;
    kv.failPut = () => (first ? !(first = false) : false);
    const answer = await search(kv);
    const second = String(answer.json.results[1]?.place);
    expect(answer).toEqual({ status: 200, json: { results: [ROWS[0], { ...ROWS[1], place: second }] } });
    expect([...kv.values.keys()]).toEqual([`plan:${DEVICE}:${second}`]);
  });

  it("writes nothing for the shared unidentified caller, whose ids any other unidentified caller could read", async () => {
    const kv = new RecordingKv();
    expect(await search(kv, { "x-scenic-device": "not-a-device" })).toEqual({ status: 200, json: { results: ROWS } });
    expect(kv.puts).toEqual([]);
  });
});

const ID = "-42";
const TOPANGA = { lat: 34.0676, lon: -118.5957 };
const SEARCHED = { ...SANTA_MONICA_TOPANGA_BODY, destination: { place: ID } };

function planHarness(kv: RecordingKv | null, over: Partial<PlanDeps> = {}) {
  const h = harness(SANTA_MONICA_TOPANGA);
  const corpus: string[] = [];
  h.deps = { ...h.deps, resolvePlace: async (id) => { corpus.push(id); return null; },
    searchPlaces: kv ? kvSearchPlaces(kv) : null, ...over };
  return { h, corpus };
}

const nextUp = (x: number) => x + Math.max(Math.abs(x) * Number.EPSILON, Number.MIN_VALUE);

describe("POST /plan resolves a searched place id for its own identity only (T-0362 R3)", () => {
  it("plans to the remembered coordinate - the one coordinate sent is the origin - without the corpus", async () => {
    const kv = new RecordingKv();
    kv.values.set(`plan:device-1:${ID}`, JSON.stringify(TOPANGA));
    const { h, corpus } = planHarness(kv);
    const response = await handlePlan(planRequest(SEARCHED), {}, h.deps);
    expect([response.status, h.sent[0]!.body.points, corpus]).toEqual([200, [[-118.49, 34.02], [-118.5957, 34.0676]], []]);
  });

  const STORED: [string, string | null, string][] = [
    ["another device's id", null, "device-2"],
    ["an id nobody wrote", null, "device-1"],
    ["lat just above 90", JSON.stringify({ lat: nextUp(90), lon: -118 }), "device-1"],
    ["lat just below -90", JSON.stringify({ lat: -nextUp(90), lon: -118 }), "device-1"],
    ["lon just above 180", JSON.stringify({ lat: 34, lon: nextUp(180) }), "device-1"],
    ["lon just below -180", JSON.stringify({ lat: 34, lon: -nextUp(180) }), "device-1"],
    ["a string lat", JSON.stringify({ lat: "34", lon: -118 }), "device-1"],
    ["a bool lon", JSON.stringify({ lat: 34, lon: true }), "device-1"],
    ["a null lat", JSON.stringify({ lat: null, lon: -118 }), "device-1"],
    ["no lon", JSON.stringify({ lat: 34 }), "device-1"],
    ["an extra key", JSON.stringify({ lat: 34, lon: -118, label: "x" }), "device-1"],
    ["not JSON", "{", "device-1"],
    ["an array", JSON.stringify([34, -118]), "device-1"],
    ["null", "null", "device-1"],
  ];
  for (const [name, value, owner] of STORED) {
    it(`${name}: 404 unknown_place with zero upstream calls`, async () => {
      const kv = new RecordingKv();
      if (value !== null || owner !== "device-1") kv.values.set(`plan:${owner}:${ID}`, value ?? JSON.stringify(TOPANGA));
      const { h } = planHarness(kv);
      const response = await handlePlan(planRequest(SEARCHED), {}, h.deps);
      expect([response.status, await response.json(), h.sent, h.events]).toEqual([404, { error: "unknown_place" }, [], []]);
    });
  }

  for (const [lat, lon] of [[90, 180], [-90, -180], [90, -180], [-90, 180]] as const) {
    it(`a stored place at the bound (${lat}, ${lon}) is the destination the router is asked for`, async () => {
      const kv = new RecordingKv();
      kv.values.set(`plan:device-1:${ID}`, JSON.stringify({ lat, lon }));
      const { h } = planHarness(kv);
      await handlePlan(planRequest(SEARCHED), {}, h.deps);
      expect(h.sent[0]!.body.points).toEqual([[-118.49, 34.02], [lon, lat]]);
    });
  }

  it("PLANS unbound: 404 unknown_place with zero upstream calls", async () => {
    const { h } = planHarness(null);
    const response = await handlePlan(planRequest(SEARCHED), {}, h.deps);
    expect([response.status, h.sent, h.events]).toEqual([404, [], []]);
  });

  it("a PLANS that cannot answer: 503 planning_unavailable with zero upstream calls", async () => {
    const kv = new RecordingKv();
    kv.failGet = true;
    const { h } = planHarness(kv);
    const response = await handlePlan(planRequest(SEARCHED), {}, h.deps);
    expect([response.status, await response.json(), h.sent]).toEqual([503, { error: "planning_unavailable" }, []]);
  });

  it("a rejected session: 401 before PLANS is read", async () => {
    const kv = new RecordingKv();
    kv.failGet = true;
    const { h } = planHarness(kv, { identify: () => ({ userId: "unidentified", tier: "anon", rejected: true }) });
    const response = await handlePlan(planRequest(SEARCHED), {}, h.deps);
    expect([response.status, h.sent]).toEqual([401, []]);
  });

  it("every id spelling outside SEARCH_PLACE_ID or below -(2^53 - 1) is the corpus's, never PLANS'", async () => {
    const kv = new RecordingKv();
    kv.failGet = true;
    const ids = ["-0", "-01", "0", "1", "-9007199254740992", "-12345678901234567", "+1", "- 1", "-1 "];
    const answers: [string, number, string[]][] = [];
    for (const id of ids) {
      const { h, corpus } = planHarness(kv);
      const response = await handlePlan(planRequest({ ...SEARCHED, destination: { place: id } }), {}, h.deps);
      answers.push([id, response.status, corpus]);
    }
    expect(answers).toEqual(ids.map((id) => [id, PLACE_ID_OK(id) ? 404 : 400, PLACE_ID_OK(id) ? [id] : []]));
    expect(["-1", "-9007199254740991"].map(isSearchPlaceId)).toEqual([true, true]);
    expect(SEARCH_PLACE_ID.source).toBe("^-[1-9][0-9]{0,15}$");
  });

  it("planDepsFromEnv reads searched places from env.PLANS", async () => {
    const kv = new RecordingKv();
    kv.values.set(`plan:device-1:${ID}`, JSON.stringify(TOPANGA));
    const deps = planDepsFromEnv({ QUOTA: fakeQuotaNamespace().ns, ROUTER_URL: "https://router.test", ROUTER_SECRET: "s",
      DB: {} as D1Database, PLANS: kv } as never);
    expect(await deps!.searchPlaces!.recall("device-1", ID)).toEqual(TOPANGA);
  });
});

const PLACE_ID_OK = (id: string) => /^[A-Za-z0-9:._-]+$/.test(id);

describe("DELETE /account's sweep reaches searched places (T-0362 R4)", () => {
  it("deletes this device's searched-place keys and keeps every near-miss", async () => {
    const prefix = `plan:${DEVICE}:`;
    const names = [`${prefix}-42`, `${prefix}-9007199254740991`, `${prefix}-0`, `${prefix}-042`, `${prefix}42`,
      `${prefix}-9007199254740992`, `${prefix}-42x`, `plan:${DEVICE}x:-42`];
    const deleted: string[] = [];
    const kv = {
      async list() { return { keys: names.map((name) => ({ name })), list_complete: true }; },
      async delete(name: string) { deleted.push(name); },
    };
    expect([await sweepPlans(kv, [DEVICE]), deleted]).toEqual([true, [`${prefix}-42`, `${prefix}-9007199254740991`]]);
  });
});
