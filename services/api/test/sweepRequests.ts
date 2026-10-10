/**
 * T-0292 R3: the per-route representatives both sweeps send (configSweep.test.ts, sharedEnvWorker.test.ts). Keys must
 * equal ROUTES' keys - each sweep asserts it, so a new route without representatives fails closed. Not a test file.
 *
 * valid / invalid are T-0288 R10's pair (no credential that verifies). authenticated carries a credential the shared-env
 * worker verifies: a session JWT signed with its SESSION_JWT_SECRET, or its RO_TOKEN for /__ro. The three routes that
 * take no credential (NO_CREDENTIAL) repeat their valid request.
 */
import { STRINGIFY } from "./configOracle";
import { REACH_BODY } from "./isochroneHarness";
import { LOOP_BODY } from "./loopHarness";
import { SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { SEARCH_BODY } from "./searchHarness";
import { TRIP_BODY } from "./tripHarness";

export const B = "https://scenic-api.test";
export const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const TOKEN = "0b7e3c1a-2d4f-4e6a-9c8b-1f2e3d4c5b6a";
const JSON_HEADERS = { "content-type": "application/json", "x-scenic-device": DEVICE };
export const post = (path: string, body: unknown, headers: Record<string, string> = {}) =>
  new Request(`${B}${path}`, { method: "POST", headers: { ...JSON_HEADERS, ...headers }, body: STRINGIFY(body) });
export const get = (path: string, headers: Record<string, string> = {}) => new Request(`${B}${path}`, { method: "GET", headers });

/** The credentials an authenticated representative carries. */
export type Auth = { session: string; ro: string };
const bearer = (token: string) => ({ authorization: `Bearer ${token}` });

/** One accepted telemetry event (the killSwitchRoutes body): it reaches the caller's identity, unlike `events: []`. */
export const TELEMETRY_EVENT = { blobs: ["drive_started", "", ""], doubles: [0, 0], indexes: ["drive_started"] };
const ATTEST = { keyId: "a2V5", attestation: "YXR0", challenge: "Y2hh", device: DEVICE };
const ASSERT = { keyId: "a2V5", assertion: "YXNz", challenge: "Y2hh" };
const APPLE = { identityToken: "e30.e30.sig", authorizationCode: "c0de" };
/** One H3 resolution-5 cell (the configSweep representative T-0293 shipped); its upper-case spelling is refused. */
export const WAITLIST_CELL = "85283473fffffff";
/** One accepted /ledger entry (T-0302): a corpus place id and that cell. */
export const LEDGER_ENTRY = { place_id: "101", cell: WAITLIST_CELL };

export type Representatives = { valid: () => Request; invalid: () => Request; authenticated: (a: Auth) => Request };

export const REQUESTS: Record<string, Representatives> = {
  "/__health": { valid: () => get("/__health"), invalid: () => post("/__health", {}), authenticated: () => get("/__health") },
  "/__version": { valid: () => get("/__version"), invalid: () => post("/__version", {}), authenticated: () => get("/__version") },
  "/__ro": { valid: () => post("/__ro", { sql: "SELECT 1" }, bearer("sweep")), invalid: () => get("/__ro"),
    authenticated: (a) => post("/__ro", { sql: "SELECT 1" }, bearer(a.ro)) },
  "/plan": { valid: () => post("/plan", SANTA_MONICA_TOPANGA_BODY), invalid: () => post("/plan", { unknown_key: 1 }),
    authenticated: (a) => post("/plan", SANTA_MONICA_TOPANGA_BODY, bearer(a.session)) },
  "/loop": { valid: () => post("/loop", LOOP_BODY), invalid: () => post("/loop", { unknown_key: 1 }),
    authenticated: (a) => post("/loop", LOOP_BODY, bearer(a.session)) },
  "/isochrone": { valid: () => post("/isochrone", REACH_BODY), invalid: () => post("/isochrone", { unknown_key: 1 }),
    authenticated: (a) => post("/isochrone", REACH_BODY, bearer(a.session)) },
  "/trip": { valid: () => post("/trip", TRIP_BODY), invalid: () => post("/trip", { unknown_key: 1 }),
    authenticated: (a) => post("/trip", TRIP_BODY, bearer(a.session)) },
  "/search": { valid: () => post("/search", SEARCH_BODY), invalid: () => post("/search", { unknown_key: 1 }),
    authenticated: (a) => post("/search", SEARCH_BODY, bearer(a.session)) },
  "/asn": { valid: () => post("/asn", { signedPayload: "e30.e30.sig" }), invalid: () => get("/asn"),
    authenticated: (a) => post("/asn", { signedPayload: "e30.e30.sig" }, bearer(a.session)) },
  "/entitlement": { valid: () => get("/entitlement", { "x-scenic-account-token": TOKEN }), invalid: () => post("/entitlement", {}),
    authenticated: (a) => get("/entitlement", { "x-scenic-account-token": TOKEN, ...bearer(a.session) }) },
  "/attest/challenge": { valid: () => post("/attest/challenge", {}), invalid: () => get("/attest/challenge"),
    authenticated: (a) => post("/attest/challenge", {}, bearer(a.session)) },
  "/attest": { valid: () => post("/attest", ATTEST), invalid: () => post("/attest", []),
    authenticated: (a) => post("/attest", ATTEST, bearer(a.session)) },
  "/attest/assert": { valid: () => post("/attest/assert", ASSERT), invalid: () => get("/attest/assert"),
    authenticated: (a) => post("/attest/assert", ASSERT, bearer(a.session)) },
  "/telemetry": { valid: () => post("/telemetry", { events: [] }), invalid: () => get("/telemetry"),
    authenticated: (a) => post("/telemetry", { events: [TELEMETRY_EVENT] }, bearer(a.session)) },
  "/config": { valid: () => get("/config"), invalid: () => post("/config", { planning_paused: false }), authenticated: () => get("/config") },
  "/auth/apple": { valid: () => post("/auth/apple", APPLE, bearer("e30.e30.sig")), invalid: () => get("/auth/apple", bearer("e30.e30.sig")),
    authenticated: (a) => post("/auth/apple", APPLE, bearer(a.session)) },
  "/account": { valid: () => new Request(`${B}/account`, { method: "DELETE", headers: { "x-scenic-device": DEVICE, ...bearer("e30.e30.sig") } }),
    invalid: () => post("/account", {}, bearer("e30.e30.sig")),
    authenticated: (a) => new Request(`${B}/account`, { method: "DELETE", headers: { "x-scenic-device": DEVICE, ...bearer(a.session) } }) },

  "/waitlist": { valid: () => post("/waitlist", { cell: WAITLIST_CELL }), invalid: () => post("/waitlist", { cell: WAITLIST_CELL.toUpperCase() }),
    authenticated: (a) => post("/waitlist", { cell: WAITLIST_CELL }, bearer(a.session)) },
  "/ledger": { valid: () => post("/ledger", LEDGER_ENTRY, bearer("e30.e30.sig")),
    invalid: () => new Request(`${B}/ledger`, { method: "PUT", headers: JSON_HEADERS, body: STRINGIFY(LEDGER_ENTRY) }),
    authenticated: (a) => post("/ledger", LEDGER_ENTRY, bearer(a.session)) },
};

/** The routes whose authenticated representative is their valid one (they take no credential). */
export const NO_CREDENTIAL = ["/__health", "/__version", "/config"];

/** mulberry32: a literal seed gives the same order on every run. */
function rng(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function shuffled<T>(xs: T[], seed: number): T[] {
  const out = [...xs];
  const r = rng(seed);
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/** A request's whole signature: method, url, sorted headers, body text. */
export const signature = async (q: Request) => STRINGIFY([q.method, q.url, [...q.headers].sort(), await q.text()]);
