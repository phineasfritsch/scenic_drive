/**
 * T-0288 rv4 B1: GET /config after EVERY route has run on the SAME worker. Handlers run at request time in the isolate
 * that answers /config, so a module outside the pinned answer path can patch an intrinsic on its first (or nth)
 * request and change every later /config answer. The sweep sends each ROUTES path a representative valid and an
 * invalid request under every KILL source, in a seeded order, twice; then the /config table runs on that worker by
 * full equality to an expectation built with the JSON.stringify captured before src loaded (configOracle), and the
 * intrinsics snapshot taken before src loaded must equal the one taken after the sweep. T-0292 R3: the representatives
 * live in sweepRequests.ts, shared with the authenticated shared-env sweep (sharedEnvWorker.test.ts).
 */
import { BASELINE, PARSE, STRINGIFY } from "./configOracle";
import { describe, expect, it } from "vitest";
import worker, { ROUTES, type Env } from "../src/index";
import { expected, KILLS } from "./configHarness";
import { ROWS } from "./configRows";
import { changed, snapshot } from "./intrinsicsSnapshot";
import { get, REQUESTS, shuffled, signature } from "./sweepRequests";

const KINDS = ["valid", "invalid"] as const;

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
          await (await worker.fetch(REQUESTS[c.path]![c.kind](), envOf(c.source))).arrayBuffer();
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
    const same: string[] = [];
    for (const [path, r] of Object.entries(REQUESTS)) if ((await signature(r.valid())) === (await signature(r.invalid()))) same.push(path);
    expect(same).toEqual([]);
    expect(STRINGIFY(KINDS)).toBe("[\"valid\",\"invalid\"]");
  });
});
