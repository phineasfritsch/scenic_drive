/**
 * T-0262 rv1 B1 (R5, P-COST-01): EVERY refusal the shipped deps can raise before a router request - checkQuota's three
 * reasons on the read, and countersFromNamespace's two on a reserve that lost the race - through the SHIPPED
 * ROUTES["/isochrone"], ROUTES["/plan"] and ROUTES["/loop"] over the QuotaCounter fake. Each answer is asserted WHOLE,
 * /isochrone's must EQUAL /plan's and /loop's for the same counter state (so the three failure() mappings cannot drift
 * apart), the router sees zero requests and the counter state is asserted whole. guardedPlan's own killed() verdict is
 * unreachable here: the shipped deps' killed is `() => false` (KILL is answered by killSwitch before the body).
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import { ROUTES, type Env } from "../src/index";
import type { QuotaKind } from "../src/quota";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { DEVICE, isochroneRouter, NOW, REACH_BODY, reachEnv } from "./isochroneHarness";
import { LOOP_BODY } from "./loopHarness";
import { SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const DAY = "2026-10-05";
const MONTH = "2026-10";
const TRIPPED = 225_000;
const DEVICE_KEY = `device:${DEVICE}`;
const EXHAUSTED = { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } };
const PAUSED = { status: 503, json: { error: "planning_paused" } };

/** The same count for every kind, so one seed is the same verdict on all three routes (anon: plan 3, loop 1, surprise 3). */
const daily = (n: unknown) => ({ day: DAY, plan: n, loop: n, surprise: n });
const monthly = (calls: number) => ({ month: MONTH, calls });

interface Row {
  verdict: string;
  seed: (q: FakeQuota) => void;
  /** A read that lost the race to another request: what readDaily / readMonthly report while storage says otherwise. */
  stale?: { daily?: number; monthly?: number };
  answer: { status: number; json: Record<string, unknown> };
  after: (kind: QuotaKind) => Record<string, unknown>;
}

const ROWS: Row[] = [
  { verdict: "quota_exhausted on the read (the day's allowance spent)", seed: (q) => q.seed(DEVICE_KEY, "daily", daily(3)),
    answer: EXHAUSTED, after: () => ({ [DEVICE_KEY]: { daily: daily(3) }, global: {} }) },
  { verdict: "upstream_paused on the read (a tripped month)", seed: (q) => q.seed("global", "monthly", monthly(TRIPPED)),
    answer: PAUSED, after: () => ({ [DEVICE_KEY]: {}, global: { monthly: monthly(TRIPPED) } }) },
  { verdict: "invalid_state on the read (a negative count)", seed: (q) => q.seed(DEVICE_KEY, "daily", daily(-1)),
    answer: PAUSED, after: () => ({ [DEVICE_KEY]: { daily: daily(-1) }, global: {} }) },
  { verdict: "invalid_state on the read (a fractional count)", seed: (q) => q.seed(DEVICE_KEY, "daily", daily(1.5)),
    answer: PAUSED, after: () => ({ [DEVICE_KEY]: { daily: daily(1.5) }, global: {} }) },
  { verdict: "quota_exhausted on the reserve (the daily reservation refuses)", seed: (q) => q.seed(DEVICE_KEY, "daily", daily(3)),
    stale: { daily: 0 }, answer: EXHAUSTED, after: () => ({ [DEVICE_KEY]: { daily: daily(3) }, global: {} }) },
  { verdict: "upstream_paused on the reserve (the monthly reservation refuses)",
    seed: (q) => q.seed("global", "monthly", monthly(TRIPPED)), stale: { monthly: 0 }, answer: PAUSED,
    after: (kind) => ({ [DEVICE_KEY]: { daily: { day: DAY, plan: 0, loop: 0, [kind]: 1 } }, global: { monthly: monthly(TRIPPED) } }) },
];

const ROUTE_KINDS = [["/isochrone", "surprise", REACH_BODY], ["/plan", "plan", SANTA_MONICA_TOPANGA_BODY],
  ["/loop", "loop", LOOP_BODY]] as const;

let router: ReturnType<typeof isochroneRouter>;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957)").run();
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  router = isochroneRouter();
  vi.stubGlobal("fetch", router.fetchImpl);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

/** The fake namespace with its reads answering `stale` - every other method (the reservations) the shipped one. */
function withStaleReads(q: FakeQuota, stale: { daily?: number; monthly?: number }): unknown {
  const ns = q.ns as unknown as { idFromName(name: string): unknown; get(id: unknown): object };
  return {
    idFromName: (name: string) => ns.idFromName(name),
    get: (id: unknown) => {
      const view = Object.create(ns.get(id)) as Record<string, unknown>;
      if (stale.daily !== undefined) view.readDaily = async () => stale.daily;
      if (stale.monthly !== undefined) view.readMonthly = async () => stale.monthly;
      return view;
    },
  };
}

async function send(path: string, e: Env, body: unknown) {
  const req = new Request(`https://scenic-api.test${path}`, {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(body),
  });
  const response = await ROUTES[path]!(req, e, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

describe("ROUTES['/isochrone'] answers every quota refusal exactly as /plan and /loop do (R5, P-COST-01)", () => {
  for (const row of ROWS) {
    it(`${row.verdict}: the whole answer, equal on all three routes, zero router requests`, async () => {
      const answers: Record<string, unknown> = {};
      for (const [path, kind, body] of ROUTE_KINDS) {
        const quota = fakeQuotaNamespace();
        row.seed(quota);
        const over = row.stale ? { QUOTA: withStaleReads(quota, row.stale) } : {};
        answers[path] = await send(path, reachEnv(quota, over), body);
        expect([path, quota.state()]).toEqual([path, row.after(kind)]);
      }
      expect(answers["/isochrone"]).toEqual(row.answer);
      expect(answers).toEqual({ "/isochrone": answers["/plan"], "/plan": answers["/loop"], "/loop": row.answer });
      expect(router.calls).toEqual([]);
    });
  }
});
