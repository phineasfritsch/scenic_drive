/**
 * T-0272 (rv1 BLOCKING) through the SHIPPED ROUTES["/plan"]: the active token in any carrier other than the one
 * x-scenic-account-token header - query parameters, a body field, a URL fragment, a path suffix, and every header
 * name in a generated list - answers EXACTLY what no token answers (full equality: the answer, the quota state, the
 * entitlement reads, every console line). The device is at the anon plan limit, so anon is 429 and paid is 200.
 */
import { liveClosures } from "./closuresFake";
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi, type MockInstance } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { applyEntitlement, ENTITLEMENTS_FOR_TOKEN } from "../src/entitlementStore";
import { ROUTES, type Env } from "../src/index";
import { freshTable, TOKEN } from "./asnHarness";
import { fakeQuotaNamespace, recordingRouter, type FakeQuota } from "./doFake";
import { loopPath, squareLoop } from "./loopHarness";
import { NOW, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const T = NOW.getTime();
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const HEADER = "x-scenic-account-token";
const BASE = "https://scenic-api.test/plan";
const CONSOLE = ["log", "info", "warn", "error", "debug"] as const;
const EXHAUSTED = { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } };

/** Query-parameter and body-field names a client (or a fallback) might carry the token under. */
const NAMES = ["account_token", "accountToken", "account-token", HEADER, "x_scenic_account_token", "appAccountToken",
  "app_account_token", "token", "purchase_id", "entitlement", "tier", "access_token", "auth"];

/** A deterministic header-name list: every stem under every prefix, less the one real header and the device header. */
const STEMS = ["account", "account-token", "account_token", "scenic-account", "scenic-account-token", "app-account-token",
  "purchase-id", "entitlement", "tier", "token", "auth-token", "access-token", "subscription"];
const HEADER_NAMES = [...new Set(["", "x-", "x-scenic-"].flatMap((p) => STEMS.map((s) => `${p}${s}`))
  .concat(["authorization", "proxy-authorization", "cookie", `${HEADER}-v2`, `x-${HEADER}`, "x-forwarded-account-token"]))]
  .filter((n) => n !== HEADER && n !== "x-scenic-device");

let quota: FakeQuota;
let spies: MockInstance[];
let planOk: { status: number; json: unknown };

type Carrier = { url?: string; headers?: Record<string, string>; body?: unknown };

/** A fresh quota with the device at the anon plan limit, then one POST through ROUTES["/plan"]. */
async function drive(c: Carrier) {
  quota = fakeQuotaNamespace();
  quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 3 });
  let reads = 0;
  const db = { prepare(sql: string) { if (sql === ENTITLEMENTS_FOR_TOKEN) reads += 1; return env.DB.prepare(sql); } };
  const e = { DB: db, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "test-router-secret", CLOSURES: liveClosures() } as unknown as Env;
  vi.stubGlobal("fetch", recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop())).fetchImpl);
  const req = new Request(c.url ?? BASE, { method: "POST", body: JSON.stringify(c.body ?? SANTA_MONICA_TOPANGA_BODY),
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE, ...c.headers } });
  const response = await ROUTES["/plan"]!(req, e, new URL(req.url));
  return { answer: { status: response.status, json: await response.json() }, state: quota.state(), reads,
    logged: spies.flatMap((s) => s.mock.calls) };
}

const query = (pairs: [string, string][]) => `${BASE}?${new URLSearchParams(pairs).toString()}`;

const CARRIERS: [string, Carrier][] = [
  ...NAMES.map((n): [string, Carrier] => [`query ?${n}=`, { url: query([[n, TOKEN]]) }]),
  ["every query name at once", { url: query(NAMES.map((n) => [n, TOKEN])) }],
  ["the URL fragment", { url: `${BASE}#${HEADER}=${TOKEN}` }],
  ["a path suffix /plan/<token>", { url: `${BASE}/${TOKEN}` }],
  ["a path parameter /plan;account_token=<token>", { url: `${BASE};account_token=${TOKEN}` }],
  ...HEADER_NAMES.map((n): [string, Carrier] => [`header ${n}`, { headers: { [n]: TOKEN } }]),
  ["every header name at once", { headers: Object.fromEntries(HEADER_NAMES.map((n) => [n, TOKEN])) }],
  ["every carrier at once", { url: `${query(NAMES.map((n) => [n, TOKEN]))}#${TOKEN}`,
    headers: Object.fromEntries(HEADER_NAMES.map((n) => [n, TOKEN])) }],
];

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957)").run();
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  vi.stubGlobal("fetch", recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop())).fetchImpl);
  const req = new Request(BASE, { method: "POST", body: JSON.stringify(SANTA_MONICA_TOPANGA_BODY),
    headers: { "content-type": "application/json" } });
  const fresh = await ROUTES["/plan"]!(req, { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
    ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", CLOSURES: liveClosures() } as unknown as Env, new URL(req.url));
  planOk = { status: fresh.status, json: await fresh.json() };
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshTable();
  await applyEntitlement(env.DB, { originalTransactionId: "1000", appAccountToken: TOKEN, environment: "Production",
    productId: "scenic.pro.monthly", status: "active", activeUntil: null, notificationType: "SUBSCRIBED", subtype: null,
    signedDate: T - 60_000 });
  spies = CONSOLE.map((name) => vi.spyOn(console, name));
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("the active token anywhere but x-scenic-account-token answers exactly the anon answer (T-0272 rv1)", () => {
  it("the header list is generated, deterministic and at least 20 names; the references are 429 anon and 200 paid", async () => {
    expect(HEADER_NAMES.length).toBeGreaterThanOrEqual(20);
    const anon = await drive({});
    expect([anon.answer, anon.reads, anon.logged]).toEqual([EXHAUSTED, 0, []]);
    const paid = await drive({ headers: { [HEADER]: TOKEN } });
    expect([paid.answer, paid.reads, paid.logged, planOk.status]).toEqual([planOk, 1, [], 200]);
    expect(paid.state).not.toEqual(anon.state);
  });

  it.each(CARRIERS)("%s", async (_name, carrier) => {
    const anon = await drive({});
    expect(await drive(carrier)).toEqual(anon);
  });

  it.each(NAMES)("a body field %s is refused 400 by the /plan key whitelist, whole answer", async (name) => {
    const answer = { status: 400, json: { error: "invalid_request",
      detail: `the body carries ${JSON.stringify(name)}, which /plan does not accept` } };
    const untouched = { [`device:${DEVICE}`]: { daily: { day: "2026-10-05", plan: 3 } } };
    expect(await drive({ body: { ...SANTA_MONICA_TOPANGA_BODY, [name]: TOKEN } }))
      .toEqual({ answer, state: untouched, reads: 0, logged: [] });
  });
});
