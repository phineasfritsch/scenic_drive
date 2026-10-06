/**
 * T-0288 rv1 B1: GET /config through the SHIPPED worker.fetch (the default export production runs), never ROUTES alone.
 * Every request variant - method, query string, path suffix, hostile headers, a body, all at once - crossed with every
 * KILL source and every CONFIG row answers the whole expected response, the one bare GET /config answers, by full
 * equality: no request property can unpause /config. The meta-test holds that no variant ignores its variant.
 */
import { describe, expect, it } from "vitest";
import worker, { type Env } from "../src/index";
import { configKv, expected, KILLS } from "./configHarness";
import { ROWS } from "./configRows";
import { type ReadLog, recordReads } from "./recordReads";

const BASE = "https://scenic-api.test";
const BODY = '{"planning_paused":false,"KILL":"0","kill_switch":false,"min_app_build":9}';
const HOSTILE: Record<string, string> = {
  "x-scenic-unpause": "1",
  "x-scenic-debug": "1",
  "x-scenic-kill": "0",
  "x-scenic-device": "6f1c1f0e-9b7a-4a8e-8f00-3c5d2e1a7b44",
  "x-scenic-account-token": "0b7e3c1a-2d4f-4e6a-9c8b-1f2e3d4c5b6a",
  authorization: "Bearer unpause",
  cookie: "planning_paused=false",
  "content-type": "application/json",
};

type Variant = { name: string; path: string; init: RequestInit & { cf?: Record<string, unknown> } };
const v = (name: string, path: string, init: RequestInit = {}): Variant => ({ name, path, init });
const BARE = v("bare GET /config", "/config", { method: "GET" });
const VARIANTS: Variant[] = [
  v("HEAD", "/config", { method: "HEAD" }),
  v("POST without a body", "/config", { method: "POST" }),
  v("POST with a JSON body", "/config", { method: "POST", body: BODY }),
  v("PUT with a body", "/config", { method: "PUT", body: BODY }),
  v("DELETE", "/config", { method: "DELETE" }),
  v("OPTIONS", "/config", { method: "OPTIONS" }),
  v("PATCH with a body", "/config", { method: "PATCH", body: BODY }),
  v("one query parameter", "/config?x=1"),
  v("unpausing query words", "/config?planning_paused=false&kill=0&KILL=&unpause=1"),
  v("empty query (/config?)", "/config?"),
  v("trailing slash (/config/)", "/config/"),
  v("trailing slash and a query", "/config/?x=1"),
  v("hostile x-scenic-* headers", "/config", { headers: HOSTILE }),
  v("one x-scenic-unpause header", "/config", { headers: { "x-scenic-unpause": "1" } }),
  v("cookie header alone", "/config", { headers: { cookie: "planning_paused=false" } }),
  v("cf country US", "/config", { cf: { country: "US" } }),
  v("cf colo LAX asn 13335", "/config", { cf: { colo: "LAX", asn: 13335 } }),
  v("cf empty object", "/config", { cf: {} }),
  v("every dimension at once", "/config/?planning_paused=false", { method: "POST", body: BODY, headers: HOSTILE, cf: { country: "US" } }),
];
const ALL = [BARE, ...VARIANTS];

const request = (x: Variant) => new Request(`${BASE}${x.path}`, x.init as RequestInit);
const envOf = (extra: Record<string, unknown>) => ({ DB: undefined, GIT_SHA: "test", BUILT_AT: "test", ...extra }) as unknown as Env;

async function viaWorker(x: Variant, extra: Record<string, unknown>) {
  const r = await worker.fetch(request(x), envOf(extra));
  return { status: r.status, contentType: r.headers.get("content-type"), cacheControl: r.headers.get("cache-control"), text: await r.text() };
}

/** rv2 B1 - the runtime whitelist: the ONE read the router makes off a /config request. Ruled by measurement. */
const APPROVED_READS = ["url"];

async function readsVia(x: Variant, extra: Record<string, unknown>): Promise<ReadLog> {
  const log: ReadLog = [];
  const r = await worker.fetch(recordReads(request(x), log), envOf(extra));
  const seen = [...log];
  await r.text();
  return seen;
}

/** Each probe reads a request property by a spelling the source guard does not key on; the recorder must name it. */
const PROBES: [string, (q: Request) => unknown, string[]][] = [
  ["Reflect.get cf", (q) => (Reflect.get(q, "cf") as { country?: string } | undefined)?.country, ["cf", "cf.country"]],
  ["arguments[0] cookie", function (this: unknown) { return (arguments[0] as Request).headers.get("cookie"); }, ["headers", "headers.get"]],
  ["destructured cf", (q) => { const { cf } = q as unknown as { cf: { country: string } }; return cf.country; }, ["cf", "cf.country"]],
  ["bracket method", (q) => q["method" as keyof Request], ["method"]],
  ["in cf", (q) => "cf" in q, ["has:cf"]],
];

/** Everything a handler could read off the request: method, url, every header, the body text. */
async function signature(x: Variant): Promise<string> {
  const r = request(x);
  return JSON.stringify([r.method, r.url, [...r.headers].sort(), (r as { cf?: unknown }).cf ?? null, await r.text()]);
}

describe("GET /config through the shipped worker.fetch over request variants (T-0288 rv1 B1)", () => {
  it("every request variant x every KILL source x every CONFIG row answers the bare GET's whole expected response", async () => {
    const got: [string, string, string, unknown][] = [];
    for (const r of ROWS) for (const [kill, source] of KILLS) for (const x of ALL) got.push([r.name, kill, x.name, await viaWorker(x, { ...source, CONFIG: r.config })]);
    expect(got).toEqual(ROWS.flatMap((r) => KILLS.flatMap(([kill, , killed]) =>
      ALL.map((x) => [r.name, kill, x.name, expected(r.overrides, killed, r.warnings)]))));
  });

  it("planning_paused is never false through any variant while any KILL source is set, even when the KV says false", async () => {
    const config = configKv('{"planning_paused":false}');
    const paused: [string, string, unknown][] = [];
    for (const [kill, source, killed] of KILLS) if (killed) for (const x of ALL) {
      paused.push([kill, x.name, JSON.parse((await viaWorker(x, { ...source, CONFIG: config })).text).planning_paused]);
    }
    expect(paused).toEqual(KILLS.filter(([, , killed]) => killed).flatMap(([kill]) => ALL.map((x) => [kill, x.name, true])));
    expect(paused.length).toBe(3 * ALL.length);
  });

  it("the shipped worker.fetch reads exactly APPROVED_READS off every request variant x KILL source x CONFIG row, any spelling", async () => {
    const got: [string, string, string, ReadLog][] = [];
    for (const r of ROWS) for (const [kill, source] of KILLS) for (const x of ALL) got.push([r.name, kill, x.name, await readsVia(x, { ...source, CONFIG: r.config })]);
    expect(got).toEqual(ROWS.flatMap((r) => KILLS.flatMap(([kill]) => ALL.map((x) => [r.name, kill, x.name, APPROVED_READS]))));
  });

  it("the read recorder names every probe spelling and keeps the request working (headers.get answers through it)", () => {
    const x = ALL[ALL.length - 1];
    const got = PROBES.map(([name, probe]) => { const log: ReadLog = []; const value = probe(recordReads(request(x), log)); return [name, value, log]; });
    expect(got).toEqual([
      ["Reflect.get cf", "US", PROBES[0][2]], ["arguments[0] cookie", "planning_paused=false", PROBES[1][2]],
      ["destructured cf", "US", PROBES[2][2]], ["bracket method", "POST", PROBES[3][2]], ["in cf", true, PROBES[4][2]],
    ]);
  });

  it("no variant ignores its variant: each request differs from the bare GET and from every other, and every dimension is varied", async () => {
    const bare = await signature(BARE);
    const sigs = await Promise.all(VARIANTS.map(signature));
    expect(VARIANTS.filter((_, i) => sigs[i] === bare).map((x) => x.name)).toEqual([]);
    expect(new Set([bare, ...sigs]).size).toBe(ALL.length);
    const reqs = ALL.map(request);
    const urls = reqs.map((r) => new URL(r.url));
    expect([...new Set(reqs.map((r) => r.method))].sort()).toEqual(["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]);
    expect([
      urls.some((u) => u.search !== ""),
      reqs.some((r) => r.url === `${BASE}/config?`),
      urls.some((u) => u.pathname === "/config/"),
      reqs.some((r) => [...r.headers.keys()].some((k) => k.startsWith("x-scenic-"))),
      VARIANTS.some((x) => typeof x.init.body === "string" && x.init.body.length > 0),
      reqs.some((r) => [...r.headers.keys()].includes("cookie")),
      reqs.map((r) => JSON.stringify((r as { cf?: unknown }).cf ?? null)).filter((c) => c !== "null").sort(),
    ]).toEqual([true, true, true, true, true, true, ['{"colo":"LAX","asn":13335}', '{"country":"US"}', '{"country":"US"}', "{}"]]);
  });
});
