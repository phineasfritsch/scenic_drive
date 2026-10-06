/**
 * T-0278 R5, R6 through the SHIPPED ROUTES["/plan"]: with SESSION_JWT_SECRET set, a session JWT that verifies is
 * the identity (sub the bucket, act's live entitlement the tier) and the bare headers are ignored; a Bearer that
 * does not verify is the unidentified bucket, anon - at every bound of iat and exp and for every defect of the
 * header, claims and signature; no Bearer reaches the header identity only under IDENTITY_HEADERS=1; without the
 * secret the identity is today's, unchanged. Every bucket is seeded at the anon plan limit, so anon answers 429 and
 * paid answers 200. The oracle is today's header identity (secret unset) for the expected caller: the answer and
 * the quota state are compared WHOLE.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { applyEntitlement } from "../src/entitlementStore";
import { ROUTES, type Env } from "../src/index";
import { UNIDENTIFIED_DEVICE } from "../src/routerDeps";
import { UNIDENTIFIED_SESSION } from "../src/sessionIdentity";
import { freshTable } from "./asnHarness";
import { HS256_HEADER, mintJwt, SECRET } from "./attestHarness";
import { b64url } from "./appleChain";
import { fakeQuotaNamespace, recordingRouter, type FakeQuota } from "./doFake";
import { loopPath, squareLoop } from "./loopHarness";
import { NOW, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const S = NOW.getTime() / 1000;
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const OTHER_DEVICE = "22222222-3333-4444-8555-666666666666";
const PAID = "6f1c2d3e-4a5b-4c6d-8e7f-0123456789ab";
const UNPAID = "11111111-2222-4333-8444-555555555555";
const UNKNOWN = "33333333-4444-4555-8666-777777777777";
/** Distinct seeds: DEVICE at the anon limit (anon 429, paid 200), the others below it, so every bucket is told apart. */
const SEEDS: [string, number][] = [[DEVICE, 3], [OTHER_DEVICE, 2], [UNIDENTIFIED_DEVICE, 1]];

type Headers = Record<string, string>;
let quota: FakeQuota;

async function plan(headers: Headers, e: Partial<Env>) {
  quota = fakeQuotaNamespace();
  for (const [b, plan] of SEEDS) quota.seed(`device:${b}`, "daily", { day: "2026-10-05", plan });
  vi.stubGlobal("fetch", recordingRouter(SANTA_MONICA_TOPANGA, loopPath(squareLoop())).fetchImpl);
  const env2 = { ...(env as unknown as Env), QUOTA: quota.ns, ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", ...e } as Env;
  const req = new Request("https://scenic-api.test/plan", { method: "POST", headers: { "content-type": "application/json", ...headers },
    body: JSON.stringify(SANTA_MONICA_TOPANGA_BODY) });
  const response = await ROUTES["/plan"]!(req, env2, new URL(req.url));
  return { status: response.status, json: await response.json(), state: quota.state() };
}

/** Today's identity (no secret) for `device` (null = no header) and `token`: the oracle. */
const today = (device: string | null, token?: string) => plan({ ...(device ? { "x-scenic-device": device } : {}),
  ...(token ? { "x-scenic-account-token": token } : {}) }, { SESSION_JWT_SECRET: undefined, IDENTITY_HEADERS: undefined });

const claims = (over: Record<string, unknown> = {}) => ({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600, ...over });
const bearer = (jwt: string) => ({ authorization: `Bearer ${jwt}` });
const WITH_SECRET = { SESSION_JWT_SECRET: SECRET, IDENTITY_HEADERS: "1" };
const LEGACY_HEADERS = { "x-scenic-device": OTHER_DEVICE, "x-scenic-account-token": PAID };

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957)").run();
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshTable();
  await applyEntitlement(env.DB, { originalTransactionId: "1000", appAccountToken: PAID, environment: "Production",
    productId: "scenic.pro.monthly", status: "active", activeUntil: null, notificationType: "SUBSCRIBED", subtype: null,
    signedDate: NOW.getTime() - 60_000 });
  await applyEntitlement(env.DB, { originalTransactionId: "2000", appAccountToken: UNPAID, environment: "Production",
    productId: "scenic.pro.monthly", status: "inactive", activeUntil: null, notificationType: "REFUND", subtype: null,
    signedDate: NOW.getTime() - 60_000 });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("a verified session JWT is the identity (R6)", () => {
  it("the unidentified bucket is one name in both modules", () => {
    expect([UNIDENTIFIED_SESSION, UNIDENTIFIED_DEVICE]).toEqual(["unidentified", "unidentified"]);
  });

  const VALID: [string, () => Promise<string>, Headers, string | null, string | undefined][] = [
    ["sub, no act: the sub's bucket, anon", () => mintJwt(claims()), {}, DEVICE, undefined],
    ["act with a live entitlement: paid", () => mintJwt(claims({ act: PAID })), {}, DEVICE, PAID],
    ["act with an inactive (REFUND) entitlement: anon", () => mintJwt(claims({ act: UNPAID })), {}, DEVICE, UNPAID],
    ["act with no entitlement row: anon", () => mintJwt(claims({ act: UNKNOWN })), {}, DEVICE, UNKNOWN],
    ["the headers beside a JWT are ignored (another device, a paid token)", () => mintJwt(claims()), LEGACY_HEADERS, DEVICE, undefined],
    ["the JWT's act wins over a header naming no purchase", () => mintJwt(claims({ act: PAID })), { "x-scenic-account-token": UNPAID }, DEVICE, PAID],
    ["iat = now is valid (bound)", () => mintJwt(claims()), {}, DEVICE, undefined],
    ["now = exp - 1 is valid (bound)", () => mintJwt(claims({ iat: S - 3599, exp: S + 1 })), {}, DEVICE, undefined],
    ["a 32-character secret serves (bound)", () => mintJwt(claims(), SECRET.slice(0, 32)), {}, DEVICE, undefined],
  ];
  for (const [name, jwt, headers, device, token] of VALID) {
    it(name, async () => {
      const secret = name.includes("32-character") ? SECRET.slice(0, 32) : SECRET;
      expect(await plan({ ...bearer(await jwt()), ...headers }, { ...WITH_SECRET, SESSION_JWT_SECRET: secret })).toEqual(await today(device, token));
    });
  }
});

describe("a Bearer that does not verify is the unidentified bucket, anon - no fallthrough to the headers (R5, R6)", () => {
  const head = (json: string) => b64url(json);
  const INVALID: [string, () => Promise<string>][] = [
    ["now = exp (bound)", () => mintJwt(claims({ iat: S - 3600, exp: S }))],
    ["iat = now + 1 (bound)", () => mintJwt(claims({ iat: S + 1, exp: S + 3601 }))],
    ["exp - iat = 3601", () => mintJwt(claims({ exp: S + 3601 }))],
    ["exp - iat = 3599", () => mintJwt(claims({ exp: S + 3599 }))],
    ["a fractional iat", () => mintJwt(claims({ iat: S + 0.5, exp: S + 3600.5 }))],
    ["iat as a string", () => mintJwt(claims({ iat: String(S) }))],
    ["alg none", async () => (await mintJwt(claims(), SECRET, head('{"alg":"none","typ":"JWT"}'))).replace(/[^.]+$/, "")],
    ["alg HS512 in the header", () => mintJwt(claims(), SECRET, head('{"alg":"HS512","typ":"JWT"}'))],
    ["the HS256 header with a space", () => mintJwt(claims(), SECRET, head('{"alg": "HS256","typ":"JWT"}'))],
    ["signed with another secret", () => mintJwt(claims(), `${SECRET}x`)],
    ["a signature cut to 31 bytes", async () => { const t = await mintJwt(claims()); return `${t.slice(0, t.lastIndexOf(".") + 1)}${b64url(new Uint8Array(31))}`; }],
    ["a signature of another body", async () => { const [h, , s] = (await mintJwt(claims())).split("."); return `${h}.${b64url(JSON.stringify(claims({ sub: OTHER_DEVICE })))}.${s}`; }],
    ["four parts", async () => `${await mintJwt(claims())}.x`],
    ["an extra claim", () => mintJwt(claims({ tier: "paid" }))],
    ["iss absent", () => mintJwt(Object.fromEntries(Object.entries(claims()).filter(([k]) => k !== "iss")))],
    ["iss another issuer", () => mintJwt(claims({ iss: "scenic-app" }))],
    ["sub upper-case", () => mintJwt(claims({ sub: DEVICE.toUpperCase() }))],
    ["sub not a UUID", () => mintJwt(claims({ sub: "unidentified" }))],
    ["act malformed", () => mintJwt(claims({ act: PAID.slice(1) }))],
    ["act null", () => mintJwt(claims({ act: null }))],
    ["claims an array", () => mintJwt(JSON.stringify([claims()]))],
    ["claims not JSON", () => mintJwt("{sub")],
  ];
  for (const [name, jwt] of INVALID) {
    it(name, async () => {
      expect(await plan({ ...bearer(await jwt()), ...LEGACY_HEADERS }, WITH_SECRET)).toEqual(await today(null));
    });
  }

  it("1 ms past the second S, iat = S + 1 is still in the future (now is the clock floored, bound)", async () => {
    vi.setSystemTime(NOW.getTime() + 1);
    const jwt = await mintJwt(claims({ iat: S + 1, exp: S + 3601 }));
    expect(await plan({ ...bearer(jwt), ...LEGACY_HEADERS }, WITH_SECRET)).toEqual(await today(null));
  });

  it("999 ms past the second S, exp = S + 1 is still valid: the sub's bucket (now is the clock floored, bound)", async () => {
    vi.setSystemTime(NOW.getTime() + 999);
    const jwt = await mintJwt(claims({ iat: S - 3599, exp: S + 1 }));
    expect(await plan(bearer(jwt), WITH_SECRET)).toEqual(await today(DEVICE));
  });

  it("a lower-case bearer scheme and a Basic credential are not a session", async () => {
    const jwt = await mintJwt(claims());
    expect([await plan({ authorization: `bearer ${jwt}`, ...LEGACY_HEADERS }, WITH_SECRET),
      await plan({ authorization: "Basic dXNlcjpwYXNz", ...LEGACY_HEADERS }, WITH_SECRET)]).toEqual([await today(null), await today(null)]);
  });
});

describe("the secret and the migration flag (R6)", () => {
  it("without the secret a valid JWT is ignored and today's header identity serves", async () => {
    const jwt = await mintJwt(claims());
    expect(await plan({ ...bearer(jwt), ...LEGACY_HEADERS }, { SESSION_JWT_SECRET: undefined, IDENTITY_HEADERS: "1" }))
      .toEqual(await today(OTHER_DEVICE, PAID));
  });

  it("a 31-character secret counts as absent: today's header identity, even under a JWT it signed", async () => {
    const short = SECRET.slice(0, 31);
    expect(await plan({ ...bearer(await mintJwt(claims(), short)), ...LEGACY_HEADERS }, { SESSION_JWT_SECRET: short }))
      .toEqual(await today(OTHER_DEVICE, PAID));
  });

  it("with the secret and IDENTITY_HEADERS=1, no Bearer is today's header identity", async () => {
    expect(await plan(LEGACY_HEADERS, WITH_SECRET)).toEqual(await today(OTHER_DEVICE, PAID));
  });

  it("with the secret and IDENTITY_HEADERS unset or 0, no Bearer is the unidentified bucket, anon", async () => {
    expect([await plan(LEGACY_HEADERS, { SESSION_JWT_SECRET: SECRET, IDENTITY_HEADERS: undefined }),
      await plan(LEGACY_HEADERS, { SESSION_JWT_SECRET: SECRET, IDENTITY_HEADERS: "0" })]).toEqual([await today(null), await today(null)]);
  });

  it("the oracle itself: anon is 429 in the bucket at its limit, paid is 200, and the four callers leave four quota states", async () => {
    const [anon, paid, other, nobody] = [await today(DEVICE), await today(DEVICE, PAID), await today(OTHER_DEVICE), await today(null)];
    expect([anon.status, paid.status, other.status, nobody.status]).toEqual([429, 200, 200, 200]);
    expect(new Set([anon, paid, other, nobody].map((x) => JSON.stringify(x.state))).size).toBe(4);
    expect(Object.keys(paid.state).sort()).toEqual(
      ["device:0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab", "device:22222222-3333-4444-8555-666666666666", "device:unidentified", "global"]);
    expect(HS256_HEADER).toBe(b64url('{"alg":"HS256","typ":"JWT"}'));
  });
});
