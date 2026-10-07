/**
 * T-0288 rv4 B1: GET /config after EVERY route has run on the SAME worker. Handlers run at request time in the isolate
 * that answers /config, so a module outside the pinned answer path can patch an intrinsic on its first (or nth)
 * request and change every later /config answer. The sweep sends each ROUTES path a representative valid and an
 * invalid request under every KILL source, in a seeded order, twice; then the /config table runs on that worker by
 * full equality to an expectation built with the JSON.stringify captured before src loaded (configOracle), and the
 * intrinsics snapshot taken before src loaded must equal the one taken after the sweep.
 */
import { BASELINE, PARSE, STRINGIFY } from "./configOracle";
import { describe, expect, it } from "vitest";
import worker, { ROUTES, type Env } from "../src/index";
import { expected, KILLS } from "./configHarness";
import { ROWS } from "./configRows";
import { changed, snapshot } from "./intrinsicsSnapshot";
import { REACH_BODY } from "./isochroneHarness";
import { LOOP_BODY } from "./loopHarness";
import { SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { TRIP_BODY } from "./tripHarness";

const B = "https://scenic-api.test";
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const TOKEN = "0b7e3c1a-2d4f-4e6a-9c8b-1f2e3d4c5b6a";
const JSON_HEADERS = { "content-type": "application/json", "x-scenic-device": DEVICE };
const post = (path: string, body: unknown, headers: Record<string, string> = {}) =>
  new Request(`${B}${path}`, { method: "POST", headers: { ...JSON_HEADERS, ...headers }, body: STRINGIFY(body) });
const get = (path: string, headers: Record<string, string> = {}) => new Request(`${B}${path}`, { method: "GET", headers });

/** Per route: [the well-formed request it accepts, a request it refuses]. Keys must equal ROUTES' keys (fail closed). */
const REQUESTS: Record<string, [() => Request, () => Request]> = {
  "/__health": [() => get("/__health"), () => post("/__health", {})],
  "/__version": [() => get("/__version"), () => post("/__version", {})],
  "/__ro": [() => post("/__ro", { sql: "SELECT 1" }, { authorization: "Bearer sweep" }), () => get("/__ro")],
  "/plan": [() => post("/plan", SANTA_MONICA_TOPANGA_BODY), () => post("/plan", { unknown_key: 1 })],
  "/loop": [() => post("/loop", LOOP_BODY), () => post("/loop", { unknown_key: 1 })],
  "/isochrone": [() => post("/isochrone", REACH_BODY), () => post("/isochrone", { unknown_key: 1 })],
  "/trip": [() => post("/trip", TRIP_BODY), () => post("/trip", { unknown_key: 1 })],
  "/asn": [() => post("/asn", { signedPayload: "e30.e30.sig" }), () => get("/asn")],
  "/entitlement": [() => get("/entitlement", { "x-scenic-account-token": TOKEN }), () => post("/entitlement", {})],
  "/attest/challenge": [() => post("/attest/challenge", {}), () => get("/attest/challenge")],
  "/attest": [() => post("/attest", { keyId: "a2V5", attestation: "YXR0", challenge: "Y2hh", device: DEVICE }), () => post("/attest", [])],
  "/attest/assert": [() => post("/attest/assert", { keyId: "a2V5", assertion: "YXNz", challenge: "Y2hh" }), () => get("/attest/assert")],
  "/telemetry": [() => post("/telemetry", { events: [] }), () => get("/telemetry")],
  "/config": [() => get("/config"), () => post("/config", { planning_paused: false })],
  "/auth/apple": [() => post("/auth/apple", { identityToken: "e30.e30.sig", authorizationCode: "c0de" }, { authorization: "Bearer e30.e30.sig" }),
    () => get("/auth/apple", { authorization: "Bearer e30.e30.sig" })],
  "/account": [() => new Request(`${B}/account`, { method: "DELETE", headers: { "x-scenic-device": DEVICE, authorization: "Bearer e30.e30.sig" } }),
    () => post("/account", {}, { authorization: "Bearer e30.e30.sig" })],
};
const KINDS = ["valid", "invalid"] as const;

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
function shuffled<T>(xs: T[], seed: number): T[] {
  const out = [...xs];
  const r = rng(seed);
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

type Call = { path: string; kind: (typeof KINDS)[number]; kill: string; source: Record<string, unknown> };
const CALLS: Call[] = Object.keys(REQUESTS).flatMap((path) => KINDS.flatMap((kind) =>
  KILLS.map(([kill, source]) => ({ path, kind, kill, source }))));
const SEEDS = [0x7288, 0x2887];
const PASSES = SEEDS.map((seed) => shuffled(CALLS, seed));
const label = (c: Call) => `${c.path} ${c.kind} ${c.kill}`;
const envOf = (extra: Record<string, unknown>) => ({ DB: undefined, GIT_SHA: "test", BUILT_AT: "test", ...extra }) as unknown as Env;

async function viaWorker(req: Request, extra: Record<string, unknown>) {
  const r = await worker.fetch(req, envOf(extra));
  return { status: r.status, contentType: r.headers.get("content-type"), cacheControl: r.headers.get("cache-control"), text: await r.text() };
}

describe("GET /config after every route has run on the same worker (T-0288 rv4 B1)", () => {
  it("the sweep sends every ROUTES path a valid and an invalid request under every KILL source, in two seeded orders", async () => {
    expect(Object.keys(REQUESTS).sort()).toEqual(Object.keys(ROUTES).sort());
    const swept: string[][] = [];
    for (const pass of PASSES) {
      const done: string[] = [];
      for (const c of pass) {
        try {
          await (await worker.fetch(REQUESTS[c.path]![KINDS.indexOf(c.kind)]!(), envOf(c.source))).arrayBuffer();
        } catch {
          // A route that throws on a binding-less env still ran its request-time code; the sweep only needs it to run.
        }
        done.push(label(c));
      }
      swept.push(done);
    }
    expect(swept.map((d) => [...d].sort())).toEqual(PASSES.map(() => CALLS.map(label).sort()));
    expect(CALLS.length).toBe(Object.keys(ROUTES).length * KINDS.length * KILLS.length);
    expect([PASSES[0].map(label).join() === CALLS.map(label).join(), PASSES[0].map(label).join() === PASSES[1].map(label).join()])
      .toEqual([false, false]);
  });

  it("after the sweep, every CONFIG row x every KILL source answers the whole expected response through worker.fetch", async () => {
    const got: [string, string, unknown][] = [];
    for (const r of ROWS) for (const [kill, source] of KILLS) got.push([r.name, kill, await viaWorker(get("/config"), { ...source, CONFIG: r.config })]);
    expect(got).toEqual(ROWS.flatMap((r) => KILLS.map(([kill, , killed]) => [r.name, kill, expected(r.overrides, killed, r.warnings)])));
    const paused = KILLS.filter(([, , killed]) => killed);
    const seen: unknown[] = [];
    for (const [kill, source] of paused) seen.push([kill, PARSE((await viaWorker(get("/config"), source)).text).planning_paused]);
    expect(seen).toEqual(paused.map(([kill]) => [kill, true]));
  });

  it("after the sweep, every global, intrinsic and prototype equals its snapshot from before src loaded", () => {
    const after = snapshot();
    expect(BASELINE.size).toBeGreaterThan(1000);
    expect(after.size).toBeGreaterThan(1000);
    expect(changed(BASELINE, after)).toEqual([]);
  });

  it("every route's valid and invalid representatives differ (meta: no row ignores its kind)", async () => {
    const sig = async (q: Request) => STRINGIFY([q.method, q.url, [...q.headers].sort(), await q.text()]);
    const same: string[] = [];
    for (const [path, [valid, invalid]] of Object.entries(REQUESTS)) if ((await sig(valid())) === (await sig(invalid()))) same.push(path);
    expect(same).toEqual([]);
  });
});
