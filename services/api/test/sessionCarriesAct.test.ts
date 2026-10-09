/**
 * T-0322 R1, R5, R6 through the SHIPPED routes: the session carries the purchase, and the Worker - never the client -
 * decides the tier. POST /attest and /attest/assert take the app's exact sorted-key body over {no purchase, live,
 * expired} and answer a session whose token EQUALS a JWT minted here from the ruled claims (act exactly when a token
 * was named; no entitlement is read to sign it). Then /plan, /trip and /loop run the cross product of the Bearer
 * (those sessions, an expired one, another secret's, another TTL's, a malformed one, none) x IDENTITY_HEADERS ("1",
 * unset) x the x-scenic-account-token header (live, expired, absent), and every answer, quota state and console record
 * EQUALS the reference `ruled` picks from the rule (T-0322 B1): a verified Bearer is its sub and its act's tier; any
 * other Bearer reads exactly as none - the header path under "1", the unidentified bucket without. The device and the
 * unidentified bucket sit at the anon limit, so anon is 429 and paid is routed.
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
/** The x-scenic-account-token header beside the Bearer: the live purchase, the expired one, or none. */
const HEADERS = { live: LIVE, expired: EXPIRED, absent: undefined } as const;
type Header = keyof typeof HEADERS;

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

/** A fresh quota: both buckets at the anon limit (`seeded`), or empty - where a reservation shows in the state (T-0333 R2). */
function freshQuota(seeded: boolean): FakeQuota {
  const q = fakeQuotaNamespace();
  if (seeded) for (const who of [DEVICE, "unidentified"]) q.seed(`device:${who}`, "daily", { day: "2026-10-06", plan: 3, loop: 1, trip: 1 });
  return q;
}

/** One request of `path` through the shipped ROUTES with the `header` purchase beside an optional Bearer. */
async function drive(path: RouteName, bearer: string | null, flag: boolean, header: Header, seeded = true) {
  quota = freshQuota(seeded);
  const router = path === "/trip" ? tripRouter().fetchImpl : recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop())).fetchImpl;
  let fetches = 0;
  vi.stubGlobal("fetch", (url: string, init?: RequestInit) => { fetches += 1; return router(url, init); });
  const e = { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "test-router-secret", CLOSURES: liveClosures(), SESSION_JWT_SECRET: SECRET, ...(flag ? { IDENTITY_HEADERS: "1" } : {}) };
  const account = HEADERS[header];
  const headers: Record<string, string> = { "content-type": "application/json", "x-scenic-device": DEVICE,
    ...(account ? { [HEADER]: account } : {}), ...(bearer === null ? {} : { authorization: `Bearer ${bearer}` }) };
  const req = new Request(`https://scenic-api.test${path}`, { method: "POST", headers, body: JSON.stringify(BODIES[path]) });
  const response = await ROUTES[path]!(req, e as unknown as Env, new URL(req.url));
  return { answer: { status: response.status, json: await response.json() }, state: quota.state(), fetches,
    logged: spies.flatMap((s) => s.mock.calls) };
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

/** Every Bearer the app can send or a caller can forge; the last five never verify. */
const BEARERS = ["session act live", "session act expired", "session no act", "expired", "wrong secret", "wrong TTL",
  "malformed", "absent"] as const;
type Bearer = (typeof BEARERS)[number];
const FLAGS = ["1", "unset"] as const;
type Flag = (typeof FLAGS)[number];
const HEADER_NAMES = Object.keys(HEADERS) as Header[];
type Ruled = "paid" | "device anon" | "unidentified anon" | "rejected";

/** The rule (T-0322 B1, T-0333 R1), from its text: a verified Bearer is the device and its act's tier; under "1" any other
 *  reads as none; with the flag closed an unverifiable Bearer is rejected and no Bearer is the unidentified bucket. */
function ruled(bearer: Bearer, flag: Flag, header: Header): Ruled {
  if (bearer === "session act live") return "paid";
  if (bearer === "session act expired" || bearer === "session no act") return "device anon";
  if (flag !== "1") return bearer === "absent" ? "unidentified anon" : "rejected";
  return header === "live" ? "paid" : "device anon";
}

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

  const ROWS = ROUTE_NAMES.flatMap((path) => BEARERS.flatMap((bearer) => FLAGS.flatMap((flag) =>
    HEADER_NAMES.map((header) => [path, bearer, flag, header] as const))));

  async function bearerOf(bearer: Bearer): Promise<string | null> {
    if (bearer === "absent") return null;
    if (bearer === "malformed") return "not-a-session";
    if (bearer === "expired") return mintJwt({ ...claims("live"), iat: S - 3600, exp: S });
    if (bearer === "wrong secret") return mintJwt(claims("live"), "another-secret-0123456789abcdefXYZ");
    if (bearer === "wrong TTL") return mintJwt({ ...claims("live"), exp: S + 3601 });
    const p: Purchase = bearer === "session act live" ? "live" : bearer === "session act expired" ? "expired" : "none";
    return ((await assertSession(p)).json as { token: string }).token;
  }

  /** T-0333 R1, R2: the literal 401, the quota exactly as seeded (nothing reserved), no upstream request, nothing logged. */
  const rejected = (seeded: boolean) => ({ answer: { status: 401, json: { error: "session_rejected" } }, state: freshQuota(seeded).state(),
    fetches: 0, logged: [] });

  /** The reference each row must EQUAL - a function of `ruled` only, never of the answer under test. */
  async function reference(path: RouteName, r: Ruled) {
    if (r === "rejected") return rejected(true);
    if (r === "paid") return drive(path, null, true, "live");
    return r === "device anon" ? drive(path, null, true, "absent") : drive(path, null, false, "absent");
  }

  it("no row ignores its variant: every value of every dimension changes some row's tier when it alone changes", () => {
    const tier = (r: Ruled) => (r === "paid" ? "paid" : r === "rejected" ? "rejected" : "anon");
    const dims = [[...BEARERS], [...FLAGS], HEADER_NAMES] as const;
    const rows = BEARERS.flatMap((b) => FLAGS.flatMap((f) => HEADER_NAMES.map((h) => [b, f, h] as [Bearer, Flag, Header])));
    const at = (row: [Bearer, Flag, Header]) => tier(ruled(...row));
    const silent = dims.flatMap((values, d) => values.filter((v) => !rows.some((row) => row[d] === v &&
      values.some((w) => { const moved = [...row] as [Bearer, Flag, Header]; moved[d] = w as never; return at(moved) !== at(row); })))
      .map((v) => `${d}:${v}`));
    expect(silent).toEqual([]);
  });

  it.each(ROUTE_NAMES)("%s: the references differ - paid is routed, anon is 429 - and log nothing", async (path) => {
    const paid = await drive(path, null, true, "live");
    const anon = await drive(path, null, true, "absent");
    expect(anon.answer.status).toBe(429);
    expect(paid.answer).not.toEqual(anon.answer);
    expect([paid.logged, anon.logged]).toEqual([[], []]);
  });

  it.each(ROWS)("%s, Bearer %s, IDENTITY_HEADERS %s, header %s: the answer is the ruled reference", async (path, bearer, flag, header) => {
    const got = await drive(path, await bearerOf(bearer), flag === "1", header);
    expect(got).toEqual(await reference(path, ruled(bearer, flag, header)));
    expect(got.logged).toEqual([]);
  });

  const UNVERIFIABLE = BEARERS.filter((b) => ruled(b, "unset", "absent") === "rejected");
  const EMPTY_ROWS = ROUTE_NAMES.flatMap((path) => UNVERIFIABLE.flatMap((bearer) => FLAGS.map((flag) => [path, bearer, flag] as const)));

  it("the rejected Bearers are exactly the four that never verify, and an empty quota is not the seeded one", () => {
    expect(UNVERIFIABLE).toEqual(["expired", "wrong secret", "wrong TTL", "malformed"]);
    expect([freshQuota(false).state(), freshQuota(true).state()].map((s) => Object.keys(s).length)).toEqual([0, 2]);
  });

  it.each(EMPTY_ROWS)("%s, Bearer %s, IDENTITY_HEADERS %s, EMPTY quota: a rejected Bearer reserves nothing (T-0333 R2)", async (path, bearer, flag) => {
    const got = await drive(path, await bearerOf(bearer), flag === "1", "absent", false);
    expect(got).toEqual(flag === "1" ? await drive(path, null, true, "absent", false) : rejected(false));
  });
});
