/**
 * The counting fakes every /plan test drives `handlePlan` with. Not a test file (vitest includes *.test.ts).
 *
 * The router fake answers from RECORDED bytes and refuses what it has no recording for, exactly as
 * Sources/ScenicKit/Plan/RecordedRouteSource does: a scenic request is matched to a recorded lambda by the
 * custom model it CARRIES, compared whole to buildCustomModel(lambda, null), so a request whose model is not
 * buildCustomModel's finds no recording and the plan fails (P-SAFE-01 seen at the wire, not in the builder).
 */
import { FRESH_EMPTY } from "./closuresFake";
import { buildCustomModel } from "../src/customModel";
import type { PlanDeps } from "../src/plan";
import type { Counters } from "../src/upstream";
import fastestRaw from "../../../Tests/Fixtures/t0221/santa-monica-topanga/fastest.json?raw";
import l0Raw from "../../../Tests/Fixtures/t0221/santa-monica-topanga/lambda-0.json?raw";
import l4Raw from "../../../Tests/Fixtures/t0221/santa-monica-topanga/lambda-4.json?raw";
import l6Raw from "../../../Tests/Fixtures/t0221/santa-monica-topanga/lambda-6.json?raw";
import l7Raw from "../../../Tests/Fixtures/t0221/santa-monica-topanga/lambda-7.json?raw";
import l75Raw from "../../../Tests/Fixtures/t0221/santa-monica-topanga/lambda-7.5.json?raw";
import l775Raw from "../../../Tests/Fixtures/t0221/santa-monica-topanga/lambda-7.75.json?raw";

export const ROUTER = "https://router.test";
export const NOW = new Date("2026-10-05T12:00:00Z");

/** The t0221 santa-monica-topanga recording, by the lambda its file name spells. */
export const SANTA_MONICA_TOPANGA_FILES = new Map<number, string>([
  [0, l0Raw], [4, l4Raw], [6, l6Raw], [7, l7Raw], [7.5, l75Raw], [7.75, l775Raw],
]);

/** What the router fake replays: the fastest body, and a scenic body for a custom model it recognises. */
export interface Recording {
  fastest: string;
  scenic(model: unknown): string | undefined;
}

/** A recorded lambda answers only the request whose model is buildCustomModel(lambda, null), compared whole. */
export function recorded(fastest: string, files: Map<number, string>): Recording {
  return {
    fastest,
    scenic(model) {
      for (const [lambda, text] of files) {
        if (JSON.stringify(model) === JSON.stringify(buildCustomModel(lambda, null))) return text;
      }
      return undefined;
    },
  };
}

export const SANTA_MONICA_TOPANGA = recorded(fastestRaw, SANTA_MONICA_TOPANGA_FILES);

/** Topanga, as the test's corpus answers the place id: the recording's own `to` (34.0676,-118.5957). */
export const PLACES: Record<string, { lat: number; lon: number }> = { "la:topanga": { lat: 34.0676, lon: -118.5957 } };

export interface Sent {
  url: string;
  body: Record<string, unknown>;
}

export interface Harness {
  deps: PlanDeps;
  sent: Sent[];
  events: string[];
  reserved: number[];
  maxInFlight: () => number;
}

export function harness(
  router: Recording,
  over: Partial<{ plansUsedToday: number; monthlyUpstreamCalls: number }> = {},
): Harness {
  const sent: Sent[] = [];
  const events: string[] = [];
  const reserved: number[] = [];
  let inFlight = 0;
  let peak = 0;
  const counters: Counters = {
    async read() {
      return { plansUsedToday: over.plansUsedToday ?? 0, monthlyUpstreamCalls: over.monthlyUpstreamCalls ?? 0 };
    },
    async reserve(_userId, upstreamCalls) {
      events.push("reserve");
      reserved.push(upstreamCalls);
    },
  };
  const fetchImpl = async (url: string, init?: RequestInit): Promise<Response> => {
    events.push("fetch");
    inFlight += 1;
    peak = Math.max(peak, inFlight);
    try {
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      sent.push({ url, body });
      await Promise.resolve();
      if (body.profile === "car_fast" && body.custom_model === undefined) return new Response(router.fastest);
      const text = body.profile === "car_scenic" ? router.scenic(body.custom_model) : undefined;
      if (text !== undefined) return new Response(text);
      return new Response(JSON.stringify({ message: "no recording for this request" }), { status: 400 });
    } finally {
      inFlight -= 1;
    }
  };
  const deps: PlanDeps = {
    upstream: { counters, fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async (id) => PLACES[id] ?? null,
    identify: () => ({ userId: "device-1", tier: "free" }),
    closures: async () => FRESH_EMPTY,
  };
  return { deps, sent, events, reserved, maxInFlight: () => peak };
}

/** A synthetic GraphHopper body: `points` evenly along a line, one osm_way_id run per way, and (T-0332 R3) one
 *  scenic_score run of 8 over the whole path unless `extra` names its own - so a synthetic route is a pretty one. */
export function syntheticPath(timeMs: number, ways: number[], extra: Record<string, unknown[]> = {}): string {
  const points = ways.length + 1;
  const coordinates = Array.from({ length: points }, (_, i) => [-118.5 + i * 0.01, 34.0 + i * 0.005]);
  const runs = ways.map((way, i) => [i, i + 1, way]);
  return JSON.stringify({
    paths: [{ time: timeMs, distance: 1000 * ways.length, points: { type: "LineString", coordinates },
      details: { osm_way_id: runs, scenic_score: [[0, ways.length, 8]], ...extra } }],
  });
}

/** A router over a duration curve: lambda -> ms, every scenic route on `scenicWays`. The lambda is read back
 *  from the model's dullest band (1 / (1 + lambda)) snapped to the bisection's lattice (multiples of 8 / 2^12),
 *  and the request is answered only if its model is buildCustomModel's at that lambda, compared whole. */
export function curveRouter(fastestMs: number, curve: (lambda: number) => number, fastestWays: number[],
  scenicWays: number[], extra: Record<string, unknown[]> = {}): Recording {
  const lattice = 8 / 4096;
  return {
    fastest: syntheticPath(fastestMs, fastestWays),
    scenic(model) {
      const priority = (model as { priority?: { else?: string; multiply_by: string }[] } | undefined)?.priority;
      const dullest = priority?.find((clause) => clause.else !== undefined);
      if (!dullest) return undefined;
      const lambda = Math.round((1 / Number(dullest.multiply_by) - 1) / lattice) * lattice;
      if (JSON.stringify(model) !== JSON.stringify(buildCustomModel(lambda, null))) return undefined;
      return syntheticPath(curve(lambda), scenicWays, extra);
    },
  };
}

export function planRequest(body: unknown, method = "POST"): Request {
  return new Request("https://scenic-api.test/plan", {
    method,
    headers: { "content-type": "application/json" },
    body: method === "GET" ? undefined : typeof body === "string" ? body : JSON.stringify(body),
  });
}

/** The body the device sends for Santa Monica -> Topanga +25: the origin rounded to 2 dp ON THE DEVICE. */
export const SANTA_MONICA_TOPANGA_BODY = {
  origin: { lat: 34.02, lon: -118.49 },
  destination: { place: "la:topanga" },
  budget_minutes: 25,
};
