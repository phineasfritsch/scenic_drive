/**
 * T-0319: the reroute rides /plan as `reroute: {token, first_pin}` (R2), the Worker remembers each plan's pins and
 * lambda under a token in PLANS (R3/R6), an unusable token answers exactly the fresh plan (R5), and a usable one
 * routes the one 2-dp origin through the pins not yet passed at the same lambda, under the ceiling, inside one
 * reservation (R7/R8). Every case drives `handlePlan` - the handler ROUTES["/plan"] runs - and every expectation is
 * whole: the answer, the upstream request list, the KV puts.
 */
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import { handlePlan } from "../src/plan";
import { kvPlanTokens, type PlanTokenKv } from "../src/planToken";
import { PLAN_UPSTREAM_COST } from "../src/quota";
import { ROUTE_DETAILS } from "../src/scenicPlanner";
import { curveRouter, harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY, type Recording } from "./planHarness";

const TOKEN = "0f1e2d3c-4b5a-4968-8776-655443322110";
const MINTED = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const PINS = [{ lat: 34.03, lon: -118.52 }, { lat: 34.04, lon: -118.56 }, { lat: 34.06, lon: -118.58 }];
const RECORD = { device: "device-1", place: "la:topanga", pins: PINS, lambda: 7.75 };
const O = [-118.49, 34.02];
const D = [-118.5957, 34.0676];

interface Put { key: string; value: string; options: { expirationTtl: number } }
interface FakeKv extends PlanTokenKv { reads: string[]; puts: Put[] }

function fakeKv(rows: Record<string, string> = {}, fail: { get?: boolean; put?: boolean } = {}): FakeKv {
  const reads: string[] = [];
  const puts: Put[] = [];
  return {
    reads,
    puts,
    async get(key) {
      reads.push(key);
      if (fail.get) throw new Error("kv down");
      return rows[key] ?? null;
    },
    async put(key, value, options) {
      if (fail.put) throw new Error("kv full");
      puts.push({ key, value, options });
    },
  };
}

const stored = (record: unknown, device = "device-1") => ({ [`plan:${device}:${TOKEN}`]: typeof record === "string" ? record : JSON.stringify(record) });

function rig(router: Recording, kv: FakeKv | null) {
  const h = harness(router);
  let minted = 0;
  (h.deps as { plans?: unknown }).plans = kv === null ? null : kvPlanTokens(kv, () => MINTED(++minted));
  return h;
}

async function send(h: ReturnType<typeof rig>, body: unknown, env: Record<string, string> = {}) {
  const response = await handlePlan(planRequest(body), env, h.deps);
  return { status: response.status, body: (await response.json()) as Record<string, unknown> };
}

const reroute = (fields: unknown, base: object = SANTA_MONICA_TOPANGA_BODY) => ({ ...base, reroute: fields });
const pinned = (firstPin: number) => reroute({ token: TOKEN, first_pin: firstPin });

function routeBody(points: number[][], profile: string, model?: unknown) {
  return { points, profile, points_encoded: false, instructions: false, "ch.disable": true, details: ROUTE_DETAILS,
    ...(model === undefined ? {} : { custom_model: model }) };
}

describe("POST /plan reroute wire (T-0319 R2, P-PRIV-05)", () => {
  it("every bound of reroute.token and reroute.first_pin", async () => {
    const rows: [string, unknown, boolean][] = [
      ["first_pin -1", { token: TOKEN, first_pin: -1 }, false],
      ["first_pin 0", { token: TOKEN, first_pin: 0 }, true],
      ["first_pin 9", { token: TOKEN, first_pin: 9 }, true],
      ["first_pin 10", { token: TOKEN, first_pin: 10 }, false],
      ["first_pin 1.5", { token: TOKEN, first_pin: 1.5 }, false],
      ["first_pin \"1\"", { token: TOKEN, first_pin: "1" }, false],
      ["first_pin null", { token: TOKEN, first_pin: null }, false],
      ["first_pin absent", { token: TOKEN }, false],
      ["token absent", { first_pin: 0 }, false],
      ["token 35 chars", { token: TOKEN.slice(1), first_pin: 0 }, false],
      ["token 37 chars", { token: `${TOKEN}0`, first_pin: 0 }, false],
      ["token uppercase", { token: TOKEN.toUpperCase(), first_pin: 0 }, false],
      ["token non-hex", { token: `g${TOKEN.slice(1)}`, first_pin: 0 }, false],
      ["token a coordinate", { token: { lat: 34.05, lon: -118.55 }, first_pin: 0 }, false],
      ["a pin inside reroute", { token: TOKEN, first_pin: 0, pins: [{ lat: 34.05, lon: -118.55 }] }, false],
      ["lambda inside reroute", { token: TOKEN, first_pin: 0, lambda: 7.75 }, false],
      ["reroute an array", [TOKEN, 0], false],
      ["reroute null", null, false],
    ];
    for (const [name, fields, accepted] of rows) {
      const kv = fakeKv(stored(RECORD));
      const h = rig(SANTA_MONICA_TOPANGA, kv);
      const { status } = await send(h, reroute(fields));
      expect([name, status]).toEqual([name, accepted ? 200 : 400]);
      expect([name, kv.reads.length, h.sent.length > 0]).toEqual([name, accepted ? 1 : 0, accepted]);
      if (!accepted) expect([name, h.events]).toEqual([name, []]);
    }
  });

  it("P-PRIV-05: a reroute sends upstream only the one 2-dp origin plus the pins the Worker remembered", async () => {
    const kv = fakeKv(stored(RECORD));
    const h = rig(SANTA_MONICA_TOPANGA, kv);
    const { status, body } = await send(h, pinned(1));
    expect(status).toBe(200);
    expect(kv.reads).toEqual([`plan:device-1:${TOKEN}`]);
    const through = [O, [PINS[1]!.lon, PINS[1]!.lat], [PINS[2]!.lon, PINS[2]!.lat], D];
    expect(h.sent).toEqual([
      { url: "https://router.test/route", body: routeBody([O, D], "car_fast") },
      { url: "https://router.test/route", body: routeBody(through, "car_scenic", buildCustomModel(7.75, null)) },
    ]);
    expect([body.lambda, body.evaluations]).toEqual([7.75, 1]);
  });

  it("an unusable token answers exactly the fresh plan", async () => {
    const variants: [string, () => FakeKv | null, unknown][] = [
      ["unknown token", () => fakeKv(), pinned(1)],
      ["store unbound", () => null, pinned(1)],
      ["store read throws", () => fakeKv(stored(RECORD), { get: true }), pinned(1)],
      ["another device", () => fakeKv(stored({ ...RECORD, device: "device-2" })), pinned(1)],
      ["another place", () => fakeKv(stored({ ...RECORD, place: "la:malibu" })), pinned(1)],
      ["first_pin past the stored pins", () => fakeKv(stored(RECORD)), pinned(4)],
      ["pins not a list", () => fakeKv(stored({ ...RECORD, pins: "34.03,-118.52" })), pinned(1)],
      ["lambda out of range", () => fakeKv(stored({ ...RECORD, lambda: 9 })), pinned(1)],
      ["not JSON", () => fakeKv(stored("{")), pinned(1)],
    ];
    for (const [name, store, body] of variants) {
      const plain = rig(SANTA_MONICA_TOPANGA, store());
      const fresh = await send(plain, SANTA_MONICA_TOPANGA_BODY);
      const kv = store();
      const h = rig(SANTA_MONICA_TOPANGA, kv);
      const answer = await send(h, body);
      expect([name, fresh.status]).toEqual([name, 200]);
      expect([name, answer]).toEqual([name, fresh]);
      expect([name, h.sent]).toEqual([name, plain.sent]);
      expect([name, kv === null ? 0 : kv.reads.length]).toEqual([name, kv === null ? 0 : 1]);
    }
  });

  it("a foreign device cannot read another device's token: its one read is its own key and it answers the fresh plan", async () => {
    const foreign = { ...RECORD, device: "device-2" };
    const plain = rig(SANTA_MONICA_TOPANGA, fakeKv(stored(foreign, "device-2")));
    const fresh = await send(plain, SANTA_MONICA_TOPANGA_BODY);
    const kv = fakeKv(stored(foreign, "device-2"));
    const h = rig(SANTA_MONICA_TOPANGA, kv);
    const answer = await send(h, pinned(1));
    expect({ status: fresh.status, answer, sent: h.sent, reads: kv.reads })
      .toEqual({ status: 200, answer: fresh, sent: plain.sent, reads: [`plan:device-1:${TOKEN}`] });
  });

  it("the first remaining pin may be the stored count: no pins left, straight to the destination", async () => {
    const h = rig(SANTA_MONICA_TOPANGA, fakeKv(stored(RECORD)));
    const { status } = await send(h, pinned(3));
    expect(status).toBe(200);
    expect(h.sent.map((s) => s.body.points)).toEqual([[O, D], [O, D]]);
    expect(h.sent[1]!.body.custom_model).toEqual(buildCustomModel(7.75, null));
  });
});

describe("POST /plan reroute ceiling and cost (T-0319 R7/R8, P-SAFE-04, P-COST-01)", () => {
  const FAST_MS = 1_200_000;
  const MINUTES = 20;
  const CEILING_MS = FAST_MS + MINUTES * 60_000;
  const router = (atFour: number) =>
    curveRouter(FAST_MS, (l) => (l === 4 ? atFour : FAST_MS + l * 100_000), [1, 2, 3, 4, 5], [1, 10, 11, 12, 13, 14]);
  const body = { ...SANTA_MONICA_TOPANGA_BODY, budget_minutes: MINUTES, reroute: { token: TOKEN, first_pin: 0 } };
  const four = stored({ ...RECORD, lambda: 4 });

  it("the budget ceiling holds on a reroute", async () => {
    const at = rig(router(CEILING_MS), fakeKv(four));
    const exact = await send(at, body);
    expect([exact.status, exact.body.eta_s, exact.body.lambda, exact.body.evaluations, exact.body.used_budget])
      .toEqual([200, CEILING_MS / 1000, 4, 1, true]);
    expect(at.sent.length).toBe(2);

    const over = rig(router(CEILING_MS + 1000), fakeKv(four));
    const breached = await send(over, body);
    const plain = rig(router(CEILING_MS + 1000), fakeKv());
    const fresh = await send(plain, { ...SANTA_MONICA_TOPANGA_BODY, budget_minutes: MINUTES });
    expect(breached).toEqual(fresh);
    expect(breached.body.eta_s as number).toBeLessThanOrEqual(CEILING_MS / 1000);
    expect(over.sent.slice(2)).toEqual(plain.sent);
    expect(over.reserved).toEqual([PLAN_UPSTREAM_COST]);
    expect(over.sent.length).toBeLessThanOrEqual(PLAN_UPSTREAM_COST);
  });

  it("a reroute reserves one plan before its first upstream call", async () => {
    const h = rig(router(CEILING_MS), fakeKv(four));
    await send(h, body);
    expect(h.events).toEqual(["reserve", "fetch", "fetch"]);
    expect(h.reserved).toEqual([PLAN_UPSTREAM_COST]);
    const over = rig(router(CEILING_MS + 1000), fakeKv(four));
    await send(over, body);
    expect(over.events[0]).toBe("reserve");
    expect(over.events.filter((e) => e === "reserve")).toEqual(["reserve"]);
  });

  it("the kill switch covers a reroute", async () => {
    const kv = fakeKv(four);
    const h = rig(router(CEILING_MS), kv);
    const { status, body: answer } = await send(h, body, { KILL: "1" });
    expect([status, answer]).toEqual([503, { error: "planning_paused" }]);
    expect([kv.reads, kv.puts, h.events, h.sent]).toEqual([[], [], [], []]);
  });
});

describe("POST /plan remembers every answer (T-0319 R3/R6)", () => {
  it("every answer remembers its pins and lambda under plan_token for 43200 s", async () => {
    const kv = fakeKv();
    const h = rig(SANTA_MONICA_TOPANGA, kv);
    const plain = await send(h, SANTA_MONICA_TOPANGA_BODY);
    const remember = (answer: Record<string, unknown>) => ({ key: `plan:device-1:${MINTED(1)}`, options: { expirationTtl: 43_200 },
      value: JSON.stringify({ device: "device-1", place: "la:topanga", pins: answer.waypoints, lambda: answer.lambda }) });
    expect(plain.body.plan_token).toBe(MINTED(1));
    expect(kv.puts).toEqual([remember(plain.body)]);

    const again = fakeKv(stored(RECORD));
    const r = rig(SANTA_MONICA_TOPANGA, again);
    const rerouted = await send(r, pinned(1));
    expect(rerouted.body.plan_token).toBe(MINTED(1));
    expect(again.puts).toEqual([remember(rerouted.body)]);
  });

  it("an unbound store or a failed write answers plan_token null with the plan intact", async () => {
    const unbound = await send(rig(SANTA_MONICA_TOPANGA, null), SANTA_MONICA_TOPANGA_BODY);
    const failed = await send(rig(SANTA_MONICA_TOPANGA, fakeKv({}, { put: true })), SANTA_MONICA_TOPANGA_BODY);
    const bound = await send(rig(SANTA_MONICA_TOPANGA, fakeKv()), SANTA_MONICA_TOPANGA_BODY);
    expect([unbound.status, unbound.body.plan_token]).toEqual([200, null]);
    expect(failed).toEqual(unbound);
    expect({ ...bound.body, plan_token: null }).toEqual(unbound.body);
  });
});
