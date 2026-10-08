/**
 * T-0322 R1, R5, R6 through the SHIPPED routes: the session carries the purchase, and the Worker - never the client -
 * decides the tier. POST /attest and /attest/assert take the app's exact sorted-key body over {no purchase, live,
 * expired} and answer a session whose token EQUALS a JWT minted here from the ruled claims (act exactly when a token
 * was named; no entitlement is read to sign it). Those sessions then ride /plan, /trip and /loop - with the live
 * x-scenic-account-token header beside every one, as the app sends it in the migration window - under IDENTITY_HEADERS
 * "1" and unset, and every answer, quota state and console record EQUALS its route's paid or anon reference. The
 * device and the unidentified bucket sit at the anon limit, so anon is 429 and paid is routed.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi, type MockInstance } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { applyEntitlement } from "../src/entitlementStore";
import { ROUTES, type Env } from "../src/index";
import { freshTable } from "./asnHarness";
import { assertion, freshAssertTables, post, route, seedKey, testKey, type TestKey } from "./assertHarness";
import { ADMITTED_TOKENS } from "./accountTokenShapes";
import { attestation, CHALLENGE, DEVICE, mintJwt, NOW, postAttest, SECRET, seedChallenge, testDeps, type Attested } from "./attestHarness";
import { liveClosures } from "./closuresFake";
import { fakeQuotaNamespace, recordingRouter, type FakeQuota } from "./doFake";
import { LOOP_BODY, loopPath, squareLoop } from "./loopHarness";
import { SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { BIG_SUR, TRIP_BODY, tripRouter } from "./tripHarness";

const S = NOW / 1000;
const LIVE = "0e6b9a4c-5f1d-4c2b-9a8e-3d7f1b2c4a5e";
const EXPIRED = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d";
const PURCHASES = { none: undefined, live: LIVE, expired: EXPIRED } as const;
type Purchase = keyof typeof PURCHASES;
const HEADER = "x-scenic-account-token";
const CONSOLE = ["log", "info", "warn", "error", "debug"] as const;
const ROUTE_NAMES = ["/plan", "/trip", "/loop"] as const;
type RouteName = (typeof ROUTE_NAMES)[number];
const BODIES: Record<RouteName, unknown> = { "/plan": SANTA_MONICA_TOPANGA_BODY, "/trip": TRIP_BODY, "/loop": LOOP_BODY };

let KEY: TestKey;
let ATTESTED: Attested;
let spies: MockInstance[];
let quota: FakeQuota;

/** The claims the Worker must sign: act exactly when the body named a token (T-0278 R5), no entitlement consulted. */
const claims = (p: Purchase) => ({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600, ...(PURCHASES[p] ? { act: PURCHASES[p] } : {}) });
const granted = async (p: Purchase) => ({ status: 200, json: { token: await mintJwt(claims(p)), expires_at: "2026-10-06T13:00:00.000Z" } });
/** The app's bodies, byte for byte: JSONEncoder's sorted keys put appAccountToken first (AttestClient, R1). */
const lead = (p: Purchase) => (PURCHASES[p] ? `"appAccountToken":"${PURCHASES[p]}",` : "");
async function assertSession(p: Purchase, head = lead(p)) {
  await freshAssertTables();
  await seedKey(KEY, DEVICE, 5);
  await seedChallenge(CHALLENGE, NOW + 300_000);
  return route("/attest/assert", {}, post(`{${head}"assertion":"${await assertion(KEY)}","challenge":"${CHALLENGE}","keyId":"${KEY.keyId}"}`));
}

async function attestSession(p: Purchase, head = lead(p)) {
  await freshAssertTables();
  await seedChallenge(CHALLENGE, NOW + 300_000);
  const body = `{${head}"attestation":"${ATTESTED.attestation}","challenge":"${CHALLENGE}","device":"${DEVICE}","keyId":"${ATTESTED.keyId}"}`;
  return postAttest(body, testDeps(ATTESTED));
}

/** One request of `path` through the shipped ROUTES with the live header beside an optional Bearer. */
async function drive(path: RouteName, bearer: string | null, flag: boolean, header: boolean) {
  quota = fakeQuotaNamespace();
  for (const who of [DEVICE, "unidentified"]) quota.seed(`device:${who}`, "daily", { day: "2026-10-06", plan: 3, loop: 1, trip: 1 });
  vi.stubGlobal("fetch", path === "/trip" ? tripRouter().fetchImpl : recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop())).fetchImpl);
  const e = { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "test-router-secret", CLOSURES: liveClosures(), SESSION_JWT_SECRET: SECRET, ...(flag ? { IDENTITY_HEADERS: "1" } : {}) };
  const headers: Record<string, string> = { "content-type": "application/json", "x-scenic-device": DEVICE,
    ...(header ? { [HEADER]: LIVE } : {}), ...(bearer === null ? {} : { authorization: `Bearer ${bearer}` }) };
  const req = new Request(`https://scenic-api.test${path}`, { method: "POST", headers, body: JSON.stringify(BODIES[path]) });
  const response = await ROUTES[path]!(req, e as unknown as Env, new URL(req.url));
  return { answer: { status: response.status, json: await response.json() }, state: quota.state(), logged: spies.flatMap((s) => s.mock.calls) };
}

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957)").run();
  await env.DB.prepare(`INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('${BIG_SUR.id}', ${BIG_SUR.lat}, ${BIG_SUR.lon})`).run();
  [KEY, ATTESTED] = [await testKey(), await attestation()];
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshTable();
  const row = { originalTransactionId: "1000", environment: "Production", productId: "scenic.pro.monthly", status: "active",
    notificationType: "SUBSCRIBED", subtype: null, signedDate: NOW - 60_000 } as const;
  await applyEntitlement(env.DB, { ...row, appAccountToken: LIVE, activeUntil: null });
  await applyEntitlement(env.DB, { ...row, originalTransactionId: "1001", appAccountToken: EXPIRED, activeUntil: NOW - 1 });
  spies = CONSOLE.map((name) => vi.spyOn(console, name));
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("the session carries the purchase; the Worker decides the tier (T-0322)", () => {
  it.each(Object.keys(PURCHASES) as Purchase[])("POST /attest and /attest/assert sign exactly the named purchase as act: %s", async (p) => {
    expect(await attestSession(p)).toEqual(await granted(p));
    expect(await assertSession(p)).toEqual(await granted(p));
    expect(spies.flatMap((s) => s.mock.calls)).toEqual([]);
  });

  it.each(ADMITTED_TOKENS)("POST /attest and /attest/assert admit an appAccountToken with %s and sign it lower-case as act", async (_, token) => {
    const head = `"appAccountToken":"${token}",`;
    const reference = { status: 200, json: { token: await mintJwt({ ...claims("none"), act: token.toLowerCase() }), expires_at: "2026-10-06T13:00:00.000Z" } };
    expect(await attestSession("none", head)).toEqual(reference);
    expect(await assertSession("none", head)).toEqual(reference);
  });

  type Held = "act live" | "act expired" | "no act" | "no session" | "another secret's act live";
  const HELD: Held[] = ["act live", "act expired", "no act", "no session", "another secret's act live"];
  const ROWS = ROUTE_NAMES.flatMap((path) => HELD.flatMap((held) => [true, false].map((flag) => [path, held, flag] as const)));

  async function bearerOf(held: Held): Promise<string | null> {
    if (held === "no session") return null;
    if (held === "another secret's act live") return mintJwt(claims("live"), "another-secret-0123456789abcdefXYZ");
    const p: Purchase = held === "act live" ? "live" : held === "act expired" ? "expired" : "none";
    return ((await assertSession(p)).json as { token: string }).token;
  }

  /** The reference each row must EQUAL - a function of (held, flag) only, never of the answer under test. */
  async function reference(path: RouteName, held: Held, flag: boolean) {
    const paid = held === "act live" || (held === "no session" && flag);
    if (paid) return drive(path, null, true, true);
    return held === "no session" || held === "another secret's act live" ? drive(path, null, false, false) : drive(path, null, true, false);
  }

  it.each(ROUTE_NAMES)("%s: the references differ - paid is routed, anon is 429 - and log nothing", async (path) => {
    const paid = await drive(path, null, true, true);
    const anon = await drive(path, null, true, false);
    expect(anon.answer.status).toBe(429);
    expect(paid.answer).not.toEqual(anon.answer);
    expect([paid.logged, anon.logged]).toEqual([[], []]);
  });

  it.each(ROWS)("%s with %s, IDENTITY_HEADERS on=%s, the live header beside it: the answer is the reference", async (path, held, flag) => {
    const bearer = await bearerOf(held);
    const got = await drive(path, bearer, flag, true);
    expect(got).toEqual(await reference(path, held, flag));
    expect(got.logged).toEqual([]);
  });
});
