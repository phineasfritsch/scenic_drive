/**
 * The counting fakes every /loop test drives `handleLoop` with. Not a test file (vitest includes *.test.ts).
 *
 * The router fake answers the n-th request with `answers[n]` (a GraphHopper body) and refuses a request it has
 * no answer for. Every fetch is COUNTED and every body kept, so a test asserts about the calls themselves.
 */
import type { LoopDeps } from "../src/loop";
import type { Counters } from "../src/upstream";

export const ROUTER = "https://router.test";
export const NOW = new Date("2026-10-05T12:00:00Z");
export const START = { lat: 34.07, lon: -118.45 };
export const LOOP_BODY = { start: START, minutes: 45 };

export interface Sent {
  url: string;
  body: Record<string, unknown>;
}

export interface LoopHarness {
  deps: LoopDeps;
  sent: Sent[];
  events: string[];
  reserved: number[];
}

export function loopHarness(answers: string[],
  over: Partial<{ plansUsedToday: number; monthlyUpstreamCalls: number }> = {}): LoopHarness {
  const sent: Sent[] = [];
  const events: string[] = [];
  const reserved: number[] = [];
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
    sent.push({ url, body: JSON.parse(String(init?.body)) as Record<string, unknown> });
    const answer = answers[sent.length - 1];
    if (answer !== undefined) return new Response(answer);
    return new Response(JSON.stringify({ message: "no answer for this request" }), { status: 400 });
  };
  const deps: LoopDeps = {
    upstream: { counters, fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    identify: () => ({ userId: "device-1", tier: "free" }),
  };
  return { deps, sent, events, reserved };
}

/** A straight run of `count` points `spacing` metres apart on a bearing, as [lat, lon]. */
export function line(start: [number, number], bearing: number, spacing: number, count: number): [number, number][] {
  const rad = (bearing * Math.PI) / 180;
  const dLat = (Math.cos(rad) * spacing) / 111_132.0;
  const dLon = (Math.sin(rad) * spacing) / (111_320.0 * Math.cos((start[0] * Math.PI) / 180));
  return Array.from({ length: count }, (_, i) => [start[0] + dLat * i, start[1] + dLon * i] as [number, number]);
}

const begin: [number, number] = [START.lat, START.lon];

/** A clean 4 km square loop from the start: north, east, south, west. */
export function squareLoop(): [number, number][] {
  let pts = line(begin, 0, 50, 21);
  for (const bearing of [90, 180, 270]) pts = pts.concat(line(pts[pts.length - 1]!, bearing, 50, 21).slice(1));
  return pts;
}

/** Out `meters` north and the same road back: retrace ~0.5. */
export function outAndBack(meters: number): [number, number][] {
  const out = line(begin, 0, 20, Math.round(meters / 20) + 1);
  return out.concat(out.slice().reverse().slice(1));
}

/** A `meters` dead-end spur west of the start, driven out and back, then the clean square: retrace ~1/6. */
export function spurThenSquare(meters: number): [number, number][] {
  const spur = line(begin, 270, 20, Math.round(meters / 20) + 1);
  return spur.concat(spur.slice().reverse().slice(1), squareLoop().slice(1));
}

/** A GraphHopper body over [lat, lon] points, one road_class / osm_way_id run per segment. */
export function loopPath(points: [number, number][], timeMs = 2_700_000): string {
  const coordinates = points.map(([lat, lon]) => [lon, lat]);
  const runs = (value: (i: number) => string | number) => points.slice(1).map((_, i) => [i, i + 1, value(i)]);
  return JSON.stringify({
    paths: [{ time: timeMs, distance: 4000, points: { type: "LineString", coordinates },
      details: { osm_way_id: runs((i) => 1000 + Math.floor(i / 20)), road_class: runs((i) => (Math.floor(i / 20) % 2 ? "secondary" : "tertiary")) } }],
  });
}

export function loopRequest(body: unknown, method = "POST"): Request {
  return new Request("https://scenic-api.test/loop", {
    method,
    headers: { "content-type": "application/json" },
    body: method === "GET" ? undefined : typeof body === "string" ? body : JSON.stringify(body),
  });
}
