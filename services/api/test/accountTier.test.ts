/**
 * T-0272 through the SHIPPED ROUTES["/plan"], ["/loop"], ["/trip"]: the caller's tier comes from the entitlements
 * table for the token in x-scenic-account-token and from nowhere else (R1-R4). Every state is driven on a device
 * already at the anon limits (3 plans, 1 loop), so anon answers 429 where paid answers 200, and /trip answers the
 * preview (anon) or the full itinerary (paid). The answers, the quota state, the entitlement reads and every
 * console line are compared WHOLE.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi, type MockInstance } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import type { EntitlementChange } from "../src/asnNotification";
import { applyEntitlement, ENTITLEMENTS_FOR_TOKEN } from "../src/entitlementStore";
import { ROUTES, type Env } from "../src/index";
import { appleChain, notification, type Chain } from "./appleChain";
import { freshTable, postAsn, testDeps, TOKEN } from "./asnHarness";
import { fakeQuotaNamespace, recordingRouter, type FakeQuota } from "./doFake";
import { LOOP_BODY, loopPath, squareLoop } from "./loopHarness";
import { NOW, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { BIG_SUR, expectedTrip, SCENIC_EDGE_MS, TRIP_BODY, tripRouter } from "./tripHarness";

const T = NOW.getTime();
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const OTHER_TOKEN = "11111111-2222-4333-8444-555555555555";
const HEADER = "x-scenic-account-token";
const EXHAUSTED = { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } };
const CONSOLE = ["log", "info", "warn", "error", "debug"] as const;

type Path = "/plan" | "/loop" | "/trip";
type Answer = { status: number; json: unknown };

let quota: FakeQuota;
let spies: MockInstance[];
let planOk: Answer;
let loopOk: Answer;
let chain: Chain;

function shippedEnv(db: D1Database = env.DB): Env {
  return { DB: db, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "test-router-secret" } as unknown as Env;
}

async function send(path: Path, headers: Record<string, string>, e: Env): Promise<Answer> {
  const body = path === "/plan" ? SANTA_MONICA_TOPANGA_BODY : path === "/loop" ? LOOP_BODY : TRIP_BODY;
  vi.stubGlobal("fetch", path === "/trip" ? tripRouter().fetchImpl
    : recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop())).fetchImpl);
  const req = new Request(`https://scenic-api.test${path}`, { method: "POST",
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE, ...headers }, body: JSON.stringify(body) });
  const response = await ROUTES[path]!(req, e, new URL(req.url));
  return { status: response.status, json: await response.json() };
}

/** env.DB, except that the entitlement read is counted and, when told to, fails at prepare or at all(). */
function watchedDb(fail: "none" | "prepare" | "all" = "none") {
  const reads: string[] = [];
  const db = {
    prepare(sql: string) {
      if (sql !== ENTITLEMENTS_FOR_TOKEN) return env.DB.prepare(sql);
      reads.push(sql);
      if (fail === "prepare") throw new Error("D1_ERROR: no such table: entitlements");
      if (fail === "all") return { bind: () => ({ all: async () => { throw new Error("D1_ERROR: network lost"); } }) };
      return env.DB.prepare(sql);
    },
  } as unknown as D1Database;
  return { db, reads };
}

/** A fresh quota with the device at the anon plan and loop limits, then /plan, /loop and /trip with `headers`. */
async function drive(headers: Record<string, string>, fail: "none" | "prepare" | "all" = "none") {
  quota = fakeQuotaNamespace();
  quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 3, loop: 1 });
  const { db, reads } = watchedDb(fail);
  const e = shippedEnv(db);
  const plan = await send("/plan", headers, e);
  const loop = await send("/loop", headers, e);
  const trip = await send("/trip", headers, e);
  return { plan, loop, trip, state: quota.state(), reads: reads.length, logged: spies.flatMap((s) => s.mock.calls) };
}

const usage = (plan: number, loop: number, calls: number) => ({
  [`device:${DEVICE}`]: { daily: { day: "2026-10-05", plan, loop, trip: 1 } },
  global: { monthly: { month: "2026-10", calls } },
});

function expected(tier: "paid" | "anon", reads: number) {
  const trip = { status: 200, json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: tier === "paid" }) };
  return tier === "paid"
    ? { plan: planOk, loop: loopOk, trip, state: usage(4, 2, 12 + 3 + 12), reads, logged: [] }
    : { plan: EXHAUSTED, loop: EXHAUSTED, trip, state: usage(3, 1, 12), reads, logged: [] };
}

const row = (over: Partial<EntitlementChange> = {}): EntitlementChange => ({
  originalTransactionId: "1000", appAccountToken: TOKEN, environment: "Production", productId: "scenic.pro.monthly",
  status: "active", activeUntil: null, notificationType: "SUBSCRIBED", subtype: null, signedDate: T - 60_000, ...over,
});
const grace = (activeUntil: number) => row({ activeUntil, notificationType: "DID_FAIL_TO_RENEW", subtype: "GRACE_PERIOD" });

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare(`INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957),
    ('${BIG_SUR.id}', ${BIG_SUR.lat}, ${BIG_SUR.lon})`).run();
  chain = await appleChain({ now: T });
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  planOk = await send("/plan", {}, shippedEnv());
  loopOk = await send("/loop", {}, shippedEnv());
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshTable();
  spies = CONSOLE.map((name) => vi.spyOn(console, name));
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const STATES: [string, EntitlementChange[], Record<string, string>, "paid" | "anon", number][] = [
  ["no account token", [row()], {}, "anon", 0],
  ["a malformed token", [row()], { [HEADER]: "not-a-purchase-id" }, "anon", 0],
  ["the active token cut by one character", [row()], { [HEADER]: TOKEN.slice(0, -1) }, "anon", 0],
  ["the active token with one character more", [row()], { [HEADER]: `${TOKEN}0` }, "anon", 0],
  ["an unknown token", [row()], { [HEADER]: OTHER_TOKEN }, "anon", 3],
  ["an inactive (REFUND) row", [row({ status: "inactive", notificationType: "REFUND" })], { [HEADER]: TOKEN }, "anon", 3],
  ["an active row with no end", [row()], { [HEADER]: TOKEN }, "paid", 3],
  ["the active token upper-cased", [row()], { [HEADER]: TOKEN.toUpperCase() }, "paid", 3],
  ["active until exactly now (expired at the boundary instant)", [row({ activeUntil: T })], { [HEADER]: TOKEN }, "anon", 3],
  ["active until now + 1 ms", [row({ activeUntil: T + 1 })], { [HEADER]: TOKEN }, "paid", 3],
  ["in grace until exactly now (expired at the boundary instant)", [grace(T)], { [HEADER]: TOKEN }, "anon", 3],
  ["in grace until now + 1 ms", [grace(T + 1)], { [HEADER]: TOKEN }, "paid", 3],
  ["one expired and one active transaction", [row({ status: "inactive", notificationType: "EXPIRED" }),
    row({ originalTransactionId: "2000", activeUntil: T + 1 })], { [HEADER]: TOKEN }, "paid", 3],
  ["the active token in every other client field (T-0256 R3)", [row()], { authorization: `Bearer ${TOKEN}`,
    "x-scenic-tier": "paid", "x-scenic-account": TOKEN, "x-account-token": TOKEN, cookie: `${HEADER}=${TOKEN}` }, "anon", 0],
];

describe("the tier is the entitlement of x-scenic-account-token, through the shipped ROUTES (R1-R3)", () => {
  it("the paid states' reference answers are a plan and a loop served 200 to a fresh anon device", () => {
    expect([planOk.status, loopOk.status, Object.keys(planOk.json as object).length > 0]).toEqual([200, 200, true]);
  });

  it.each(STATES)("%s", async (_name, rows, headers, tier, reads) => {
    for (const r of rows) await applyEntitlement(env.DB, r);
    expect(await drive(headers)).toEqual(expected(tier, reads));
  });
});

describe("a D1 failure while resolving the tier fails CLOSED to anon, and nothing is logged (R4)", () => {
  it("an entitlement read that throws at prepare leaves an active token anon", async () => {
    await applyEntitlement(env.DB, row());
    expect(await drive({ [HEADER]: TOKEN }, "prepare")).toEqual(expected("anon", 3));
  });

  it("an entitlement read that rejects at all() leaves an active token anon", async () => {
    await applyEntitlement(env.DB, row());
    expect(await drive({ [HEADER]: TOKEN }, "all")).toEqual(expected("anon", 3));
  });

  it("no answer and no console line carries the token, paid or failed", async () => {
    await applyEntitlement(env.DB, row());
    const seen = JSON.stringify([await drive({ [HEADER]: TOKEN }), await drive({ [HEADER]: TOKEN }, "all")]);
    expect(seen.includes(TOKEN)).toBe(false);
  });
});

const TX = { originalTransactionId: "1000", productId: "scenic.pro.monthly", appAccountToken: TOKEN };

async function notify(type: string, signedDate: number, tx: Record<string, unknown> = TX) {
  const deps = testDeps(chain.rootSha256);
  expect(await postAsn(await notification(chain, { type, signedDate, tx }), deps)).toEqual({ status: 200, json: { received: true } });
}

describe("REFUND_REVERSED restores access through the shipped ROUTES (R6)", () => {
  it("SUBSCRIBED, REFUND, REFUND_REVERSED: paid, then anon, then paid again", async () => {
    await notify("SUBSCRIBED", T - 3000);
    expect(await drive({ [HEADER]: TOKEN })).toEqual(expected("paid", 3));
    await notify("REFUND", T - 2000);
    expect(await drive({ [HEADER]: TOKEN })).toEqual(expected("anon", 3));
    await notify("REFUND_REVERSED", T - 1000);
    expect(await drive({ [HEADER]: TOKEN })).toEqual(expected("paid", 3));
  });

  it("an older REFUND_REVERSED after a newer REFUND leaves the caller anon (signedDate guard)", async () => {
    await notify("SUBSCRIBED", T - 3000);
    await notify("REFUND", T - 1000);
    await notify("REFUND_REVERSED", T - 2000);
    expect(await drive({ [HEADER]: TOKEN })).toEqual(expected("anon", 3));
  });

  it("a REFUND_REVERSED whose expiresDate is exactly now leaves the caller anon; now + 1 ms is paid", async () => {
    await notify("REFUND", T - 2000);
    await notify("REFUND_REVERSED", T - 1000, { ...TX, expiresDate: T });
    expect(await drive({ [HEADER]: TOKEN })).toEqual(expected("anon", 3));
    await notify("REFUND_REVERSED", T - 500, { ...TX, expiresDate: T + 1 });
    expect(await drive({ [HEADER]: TOKEN })).toEqual(expected("paid", 3));
  });
});

/** Every activating type, its transaction's expiresDate one ms before, at, and one ms after Apple's signedDate. */
const LAPSED_AT_SIGNING: [string, number][] = ["SUBSCRIBED", "DID_RENEW", "OFFER_REDEEMED", "REFUND_REVERSED"]
  .flatMap((type) => [-1, 0, 1].map((offset): [string, number] => [type, offset]));

describe("an activation whose expiresDate had passed when Apple signed it stays anon through the shipped ROUTES (R6)", () => {
  it.each(LAPSED_AT_SIGNING)("%s with expiresDate - signedDate = %d ms, both before now, leaves the caller anon",
    async (type, offset) => {
      if (type === "REFUND_REVERSED") await notify("REFUND", T - 2000);
      await notify(type, T - 1000, { ...TX, expiresDate: T - 1000 + offset });
      expect(await drive({ [HEADER]: TOKEN })).toEqual(expected("anon", 3));
    });
});
