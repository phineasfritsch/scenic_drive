/**
 * T-0292: the kill switch (P-COST-01) and GET /config on a SHARED-ENV worker. workerd hands one env object to every
 * request in an isolate, so a handler that writes to env changes every later request (rv5-t0288's recordable). R1: the
 * shipped default.fetch hands each handler a frozen per-request copy. R2: one env object per KILL source, built once
 * with bound fakes (D1, KV, Analytics Engine, the router, QUOTA, the session secret, the RO token), reused by every
 * request below. R3: the sweep includes AUTHENTICATED requests, so a patch gated on a verified caller fires. R4/R5: the
 * P-COST-01 kill table and the /config table run on those same objects after the sweep, by full equality.
 */
import { BASELINE, PARSE, STRINGIFY } from "./configOracle";
import { env as testEnv } from "cloudflare:test";
import { beforeAll, describe, expect, it, vi } from "vitest";
import worker, { ROUTES, type Env } from "../src/index";
import { signSession } from "../src/sessionJwt";
import { expected, KILLS } from "./configHarness";
import { ROWS } from "./configRows";
import { fakeKv, fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { changed, snapshot } from "./intrinsicsSnapshot";
import { freshAllTables } from "./siwaHarness";
import { DEVICE, get, NO_CREDENTIAL, REQUESTS, shuffled, signature, type Auth } from "./sweepRequests";

const SECRET = "t0292-shared-env-session-secret-0123456789abcdef";
const RO_TOKEN = "t0292-shared-env-ro-token";
const OPERATIONAL = ["/__health", "/__version", "/__ro", "/asn", "/entitlement", "/attest/challenge", "/attest", "/attest/assert",
  "/auth/apple", "/account", "/config", "/waitlist", "/ledger"];
const KILLABLE = ["/plan", "/loop", "/isochrone", "/trip", "/telemetry"];
const PAUSED: Record<string, unknown> = {
  "/plan": { status: 503, json: { error: "planning_paused" } },
  "/loop": { status: 503, json: { error: "planning_paused" } },
  "/isochrone": { status: 503, json: { error: "planning_paused" } },
  "/trip": { status: 503, json: { error: "planning_paused" } },
  "/telemetry": { status: 503, json: { error: "telemetry_paused" } },
};

type Rig = { name: string; killed: boolean; env: Env; quota: FakeQuota; writes: unknown[]; host: string };
const rig = ([name, source, killed]: (typeof KILLS)[number], i: number): Rig => {
  const quota = fakeQuotaNamespace();
  const writes: unknown[] = [];
  const host = `router-${i}.test`;
  const env = {
    DB: testEnv.DB, GIT_SHA: "test", BUILT_AT: "test", RO_TOKEN, QUOTA: quota.ns, ROUTER_URL: `https://${host}`,
    ROUTER_SECRET: "test-router-secret", GRAPH_VERSION: "t0292", SESSION_JWT_SECRET: SECRET, CLOSURES: fakeKv({}),
    CONFIG: fakeKv({}), TELEMETRY: { writeDataPoint: (p: unknown) => void writes.push(p) }, ...source,
  } as unknown as Env;
  return { name, killed, env, quota, writes, host };
};
const RIGS: Rig[] = KILLS.map(rig);
/** R2: each source's worker is its own module instance - its own isolate - so a first-call patch fires on each one. */
const ISOLATES: (typeof worker)[] = [];
beforeAll(async () => {
  await freshAllTables(); // the rig D1 holds every migrated table, waitlist (T-0293) among them
  for (const _ of RIGS) {
    vi.resetModules();
    ISOLATES.push((await import("../src/index")).default);
  }
});
const isolate = (r: Rig) => ISOLATES[RIGS.indexOf(r)]!;
const BEFORE = RIGS.map((r) => ({ ...r.env }) as Record<string, unknown>);
const hosts: string[] = [];

/** The router (and every other upstream) is the global fetch: recorded by host, always 500. */
async function withRouter<T>(fn: () => Promise<T>): Promise<T> {
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    hosts.push(new URL(input instanceof Request ? input.url : String(input)).host);
    return new Response(STRINGIFY({ message: "the shared-env worker answers no upstream request" }), { status: 500 });
  });
  try {
    return await fn();
  } finally {
    vi.unstubAllGlobals();
  }
}

let auth: Auth | null = null;
async function credentials(): Promise<Auth> {
  auth ??= { session: (await signSession(SECRET, { sub: DEVICE }, Date.now())).token, ro: RO_TOKEN };
  return auth;
}

async function answer(req: Request, env: Env, w: typeof worker = worker) {
  const r = await w.fetch(req, env);
  const text = await r.text();
  let json: unknown = text;
  try {
    json = PARSE(text);
  } catch {
    // a non-JSON body is compared as its text
  }
  return { status: r.status, json };
}

const KINDS = ["valid", "invalid", "authenticated"] as const;
type Call = { path: string; kind: (typeof KINDS)[number]; rig: number };
const CALLS: Call[] = Object.keys(REQUESTS).flatMap((path) => KINDS.flatMap((kind) => RIGS.map((_, i) => ({ path, kind, rig: i }))));
const PASSES = [0x0292, 0x2920].map((seed) => shuffled(CALLS, seed));
const label = (c: Call) => `${c.path} ${c.kind} ${RIGS[c.rig]!.name}`;

describe("the shared-env worker after an authenticated sweep (T-0292, P-COST-01)", () => {
  it("the authenticated sweep sends every ROUTES path a valid, an invalid and an authenticated request on one env per KILL source, and no request throws", async () => {
    expect(Object.keys(REQUESTS).sort()).toEqual(Object.keys(ROUTES).sort());
    const a = await credentials();
    const outcomes: string[][] = [];
    await withRouter(async () => {
      for (const pass of PASSES) {
        const done: string[] = [];
        for (const c of pass) {
          const r = REQUESTS[c.path]!;
          const req = c.kind === "authenticated" ? r.authenticated(a) : r[c.kind]();
          try {
            await (await ISOLATES[c.rig]!.fetch(req, RIGS[c.rig]!.env)).arrayBuffer();
            done.push(`${label(c)} answered`);
          } catch (e) {
            done.push(`${label(c)} threw ${(e as Error).name}: ${(e as Error).message}`);
          }
        }
        outcomes.push(done);
      }
    });
    expect(outcomes.map((d) => [...d].sort())).toEqual(PASSES.map(() => CALLS.map((c) => `${label(c)} answered`).sort()));
    expect(CALLS.length).toBe(Object.keys(ROUTES).length * KINDS.length * KILLS.length);
    expect([new Set(ISOLATES).size, ISOLATES.includes(worker)]).toEqual([RIGS.length, false]);
  });

  it("after the sweep, every upstream route and /telemetry on the shared env answers the whole paused response under every killing source, and is served under every other", async () => {
    const a = await credentials();
    const killable = Object.keys(ROUTES).filter((k) => !OPERATIONAL.includes(k));
    expect(killable).toEqual(KILLABLE);
    const got: unknown[] = [];
    await withRouter(async () => {
      for (const r of RIGS) {
        for (const path of KILLABLE) {
          const body = await answer(REQUESTS[path]!.authenticated(a), r.env, isolate(r));
          got.push([r.name, path, r.killed || STRINGIFY(body) === STRINGIFY(PAUSED[path]) ? body : "served"]);
        }
      }
    });
    const row = (r: Rig, path: string) => [r.name, path, r.killed ? PAUSED[path] : "served"];
    expect(got).toEqual(RIGS.flatMap((r) => KILLABLE.map((path) => row(r, path))));
    // Over the WHOLE run (sweep + this table): a killed source reached no router, wrote no point, reserved nothing.
    const killed = RIGS.filter((r) => r.killed);
    expect(killed.map((r) => [r.name, hosts.filter((h) => h === r.host).length, r.writes.length, r.quota.state()]))
      .toEqual(killed.map((r) => [r.name, 0, 0, {}]));
    // Meta: the rows are functions of the source, and the fakes are reached when nothing kills.
    expect(RIGS.filter((r) => !r.killed).map((r) => [r.name, hosts.includes(r.host), r.writes.length > 0]))
      .toEqual(RIGS.filter((r) => !r.killed).map((r) => [r.name, true, true]));
    expect(KILLABLE.filter((path) => STRINGIFY(row(RIGS[0]!, path)[2]) === STRINGIFY(row(RIGS[2]!, path)[2]))).toEqual([]);
  });

  it("after the sweep, every CONFIG row x every KILL source answers the whole expected /config response on the shared env", async () => {
    const got: unknown[] = [];
    for (const row of ROWS) {
      for (const r of RIGS) {
        const e = r.env as unknown as Record<string, unknown>;
        const bound = e.CONFIG;
        e.CONFIG = row.config;
        try {
          const res = await isolate(r).fetch(get("/config"), r.env);
          got.push([row.name, r.name, { status: res.status, contentType: res.headers.get("content-type"),
            cacheControl: res.headers.get("cache-control"), text: await res.text() }]);
        } finally {
          e.CONFIG = bound;
        }
      }
    }
    expect(got).toEqual(ROWS.flatMap((row) => RIGS.map((r) => [row.name, r.name, expected(row.overrides, r.killed, row.warnings)])));
  });

  it("after the sweep, every global and intrinsic equals its snapshot from before src loaded, and every shared env holds exactly its bindings", () => {
    expect(changed(BASELINE, snapshot())).toEqual([]);
    const held = RIGS.map((r, i) => Object.keys(r.env).sort().map((k) => [k, Object.is((r.env as unknown as Record<string, unknown>)[k], BEFORE[i]![k])]));
    expect(held).toEqual(BEFORE.map((b) => Object.keys(b).sort().map((k) => [k, true])));
    expect(RIGS.map((r) => (r.env as { KILL?: string }).KILL)).toEqual(KILLS.map(([, s]) => s.KILL));
  });

  it("every route's authenticated representative differs from its valid one, except the routes that take no credential", async () => {
    const a = await credentials();
    const same: string[] = [];
    for (const [path, r] of Object.entries(REQUESTS)) if ((await signature(r.valid())) === (await signature(r.authenticated(a)))) same.push(path);
    expect(same).toEqual(NO_CREDENTIAL);
  });
});

describe("handlers get a frozen env (T-0292 R1, P-COST-01)", () => {
  it("a handler that deletes, assigns or redefines env.KILL through worker.fetch throws TypeError, and the next POST /plan on the same env object is 503 planning_paused", async () => {
    const shared = rig(KILLS[2]!, 9).env;
    expect((shared as { KILL?: string }).KILL).toBe("1");
    const tried: string[] = [];
    const HOSTILE = "/__t0292_hostile";
    const attempts: [string, (e: Record<string, unknown>) => void][] = [
      ["delete", (e) => void delete e.KILL],
      ["assign", (e) => void (e.KILL = "0")],
      ["defineProperty", (e) => void Object.defineProperty(e, "KILL", { value: "0" })],
      ["unbind KILL_SWITCH", (e) => void (e.KILL_SWITCH = undefined)],
    ];
    ROUTES[HOSTILE] = async (_req, e) => {
      for (const [name, act] of attempts) {
        try {
          act(e as unknown as Record<string, unknown>);
          tried.push(`${name}: no throw`);
        } catch (x) {
          tried.push(`${name}: ${(x as Error).name}`);
        }
      }
      return new Response(null, { status: 204 });
    };
    let after: unknown;
    try {
      expect((await worker.fetch(get(HOSTILE), shared)).status).toBe(204);
      after = await withRouter(async () => answer(REQUESTS["/plan"]!.authenticated(await credentials()), shared));
    } finally {
      delete ROUTES[HOSTILE];
    }
    expect(tried).toEqual(attempts.map(([name]) => `${name}: TypeError`));
    expect([after, (shared as { KILL?: string }).KILL]).toEqual([PAUSED["/plan"], "1"]);
  });
});

describe("the kill read is not reachable through a shared binding (T-0297, P-COST-01)", () => {
  type Kv = Record<string, unknown>;
  /** One fresh real-shaped binding per KV killing source (get on the prototype), so a landed write stays in this test. */
  const KV_SOURCES: [string, () => KVNamespace][] = [
    ["KV KILL_SWITCH KILL=1", () => fakeKv({ KILL: "1" })],
    ["KV KILL_SWITCH throws", () => fakeKv({}, true)],
  ];
  const patch = async () => null;
  // What the handler holds (its env.KILL_SWITCH): every write is REFUSED.
  const REFUSED: [string, (k: Kv) => void][] = [
    ["assign env.KILL_SWITCH.get", (k) => void (k.get = patch)],
    ["defineProperty env.KILL_SWITCH get", (k) => void Object.defineProperty(k, "get", { value: patch })],
    ["assign the inherited get", (k) => void ((Object.getPrototypeOf(k) as Kv).get = patch)],
  ];
  // The shared binding object itself and its class (no handler holds them; the test does): every write LANDS, harmlessly.
  const LANDED: [string, (raw: Kv) => void][] = [
    ["assign the shared binding's own get", (raw) => void (raw.get = patch)],
    ["assign the binding class's prototype get", (raw) => void ((Object.getPrototypeOf(raw) as Kv).get = patch)],
  ];

  it("a handler that assigns env.KILL_SWITCH.get = async () => null on its first call through worker.fetch does not unpause any later request: every upstream route and /telemetry on the shared env answers the whole paused response under every KV killing source", async () => {
    expect(KV_SOURCES.map(([name]) => name)).toEqual(KILLS.filter(([, s]) => "KILL_SWITCH" in s).map(([name]) => name));
    const HOSTILE = "/__t0297_hostile";
    const a = await credentials();
    const got: unknown[] = [];
    const live: unknown[] = [];
    for (const [i, [name, make]] of KV_SOURCES.entries()) {
      const raw = make() as unknown as Kv;
      const proto = Object.getPrototypeOf(raw) as Kv;
      const genuine = proto.get;
      const r = rig([name, { KILL_SWITCH: raw }, true], 20 + i);
      const tried: string[] = [];
      let calls = 0;
      ROUTES[HOSTILE] = async (_req, e) => {
        if (calls++ === 0) {
          const held = (e as unknown as { KILL_SWITCH: Kv }).KILL_SWITCH;
          for (const [what, act] of REFUSED) {
            try {
              act(held);
              tried.push(`${what}: no throw`);
            } catch (x) {
              tried.push(`${what}: ${(x as Error).name}`);
            }
          }
          for (const [what, act] of LANDED) {
            act(raw);
            tried.push(`${what}: landed`);
          }
        }
        return new Response(null, { status: 204 });
      };
      try {
        const first = (await worker.fetch(get(HOSTILE), r.env)).status;
        const second = (await worker.fetch(get(HOSTILE), r.env)).status;
        live.push([name, await (raw.get as (k: string) => Promise<string | null>)("KILL")]);
        const rows: unknown[] = [];
        await withRouter(async () => {
          for (const path of KILLABLE) rows.push([path, await answer(REQUESTS[path]!.authenticated(a), r.env)]);
        });
        got.push([name, first, second, tried, rows, hosts.filter((h) => h === r.host).length, r.writes.length, r.quota.state()]);
      } finally {
        proto.get = genuine;
        delete ROUTES[HOSTILE];
      }
    }
    expect(got).toEqual(KV_SOURCES.map(([name]) => [name, 204, 204,
      [...REFUSED.map(([what]) => `${what}: TypeError`), ...LANDED.map(([what]) => `${what}: landed`)],
      KILLABLE.map((path) => [path, PAUSED[path]]), 0, 0, {}]));
    // Meta: the landed patch is live on the shared binding - a kill read through it would answer null and unpause.
    expect(live).toEqual(KV_SOURCES.map(([name]) => [name, null]));
  });
});
