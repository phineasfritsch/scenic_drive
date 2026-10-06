/**
 * The counting router every /trip test drives (T-0268). Not a test file (vitest includes *.test.ts).
 *
 * A straight 40-edge road from ORIGIN to BIG_SUR, every edge EDGE_M metres. The router fake answers by request:
 *   car_fast                          -> the fastest path, FASTEST_MS (360_000 ms an edge)
 *   car_scenic over the A->B points   -> the 1st (lambda 0) is the fastest path again; every later one is the scenic
 *                                        path, SCENIC_MS (450_000 ms an edge) - so the search spends all 6 evaluations
 *   car_scenic over any other points  -> a day LEG: its two points looked up on the road, timed (b - a) x 450_000 ms
 *                                        unless `legMs` says otherwise
 * Every request is COUNTED with its parsed body, so a test asserts about the calls themselves.
 */
import type { Counters } from "../src/upstream";

export const NOW = new Date("2026-10-05T12:00:00Z");
export const ROUTER = "https://router.test";
export const ORIGIN = { lat: 34.02, lon: -118.49 };
export const BIG_SUR = { id: "la:big-sur", lat: 36.27, lon: -121.81 };
export const TRIP_BODY = { origin: ORIGIN, destination: { place: BIG_SUR.id }, days: 5 };
export const EDGES = 40;
export const EDGE_M = 10_000;
export const FAST_EDGE_MS = 360_000;
export const SCENIC_EDGE_MS = 450_000;
export const FASTEST_MS = EDGES * FAST_EDGE_MS;
export const SCENIC_MS = EDGES * SCENIC_EDGE_MS;

/** The road's 41 points as [lon, lat], GeoJSON order. */
export const ROAD: [number, number][] = Array.from({ length: EDGES + 1 }, (_, i) =>
  [ORIGIN.lon + ((BIG_SUR.lon - ORIGIN.lon) * i) / EDGES, ORIGIN.lat + ((BIG_SUR.lat - ORIGIN.lat) * i) / EDGES]);

export interface Sent {
  url: string;
  body: Record<string, unknown>;
}

/** A GraphHopper body: per-edge `time` (ms) and `distance` (m) runs over `points`, unless `details` replaces them. */
export function tripPath(points: [number, number][], edgeMs: number, details?: Record<string, unknown>, timeMs?: number): string {
  const edges = points.length - 1;
  const runs = (value: number) => Array.from({ length: edges }, (_, i) => [i, i + 1, value]);
  return JSON.stringify({
    paths: [{ time: timeMs ?? edges * edgeMs, distance: edges * EDGE_M, points: { type: "LineString", coordinates: points },
      details: details ?? { time: runs(edgeMs), distance: runs(EDGE_M) } }],
  });
}

export interface RouterOptions {
  /** The scenic answer (every car_scenic A->B request after the first). */
  scenic?: string;
  /** A day leg's time from its road vertices; the default is (b - a) x SCENIC_EDGE_MS. */
  legMs?: (leg: number, from: number, to: number) => number;
  /** The fastest path's per-edge ms (also the lambda-0 answer); FAST_EDGE_MS by default. */
  fastEdgeMs?: number;
  /** Called before each request is answered (to snapshot the quota at the first). */
  onFetch?: () => void;
}

export function tripRouter(options: RouterOptions = {}) {
  const sent: Sent[] = [];
  let scenic = 0;
  let legs = 0;
  const vertex = (p: unknown) => ROAD.findIndex(([lon, lat]) => JSON.stringify([lon, lat]) === JSON.stringify(p));
  const fetchImpl = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    options.onFetch?.();
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push({ url: String(input instanceof Request ? input.url : input), body });
    const points = body.points as unknown[];
    const fast = tripPath(ROAD, options.fastEdgeMs ?? FAST_EDGE_MS);
    if (body.profile === "car_fast") return new Response(fast);
    if (JSON.stringify(points) === JSON.stringify(sent[0]!.body.points)) {
      scenic += 1;
      return new Response(scenic === 1 ? fast : options.scenic ?? tripPath(ROAD, SCENIC_EDGE_MS));
    }
    const [a, b] = [vertex(points[0]), vertex(points[1])];
    legs += 1;
    const ms = options.legMs ? options.legMs(legs, a, b) : (b - a) * SCENIC_EDGE_MS;
    return new Response(tripPath(ROAD.slice(a, b + 1), SCENIC_EDGE_MS, {}, ms));
  };
  return { sent, fetchImpl };
}

/** In-memory counters that record the order of reservations against fetches. */
export function tripCounters(events: string[], over: Partial<{ plansUsedToday: number; monthlyUpstreamCalls: number }> = {}) {
  const reserved: unknown[][] = [];
  const counters: Counters = {
    async read() {
      return { plansUsedToday: over.plansUsedToday ?? 0, monthlyUpstreamCalls: over.monthlyUpstreamCalls ?? 0 };
    },
    async reserve(userId, upstreamCalls, _now, kind, tier) {
      events.push("reserve");
      reserved.push([userId, upstreamCalls, kind, tier]);
    },
  };
  return { counters, reserved };
}

export function tripRequest(body: unknown, path = "/trip"): Request {
  return new Request(`https://scenic-api.test${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: typeof body === "string" ? body : JSON.stringify(body),
  });
}

/**
 * The ORACLE: the whole /trip answer recomputed from T-0268 R3-R7 over this road, independently of src/. Every edge
 * of the chosen path is `edgeMs`; day d ends at the first vertex k with k x days >= d x EDGES (the even share, R4 of
 * T-0249 - the limits never bind on this road); a day's ceiling is floor(ceiling x day / total) (R7). `edgesMs`, when
 * given, replaces the uniform `edgeMs` edge by edge, and day d then ends at the first k with cum(k) x days >= d x total.
 */
export function expectedTrip(o: { days: number; pct?: number; edgeMs: number; lambda: number; full: boolean;
  legMs?: (leg: number, from: number, to: number) => number; edgesMs?: number[] }) {
  const pct = o.pct ?? 40;
  const budgetMs = Math.floor((FASTEST_MS * pct) / 100);
  const ceilingMs = FASTEST_MS + budgetMs;
  const edgeMs = o.edgesMs ?? Array<number>(EDGES).fill(o.edgeMs);
  const cum = (k: number) => edgeMs.slice(0, k).reduce((sum, ms) => sum + ms, 0);
  const totalMs = cum(EDGES);
  const at = (i: number) => ({ lat: ROAD[i]![1], lon: ROAD[i]![0] });
  const days = [];
  let start = 0;
  let legSumMs = 0;
  for (let d = 1; d <= o.days; d++) {
    let end = start + 1;
    while (cum(end) * o.days < d * totalMs) end += 1;
    const dayMs = cum(end) - cum(start);
    const legMs = o.legMs ? o.legMs(d, start, end) : (end - start) * SCENIC_EDGE_MS;
    legSumMs += legMs;
    days.push({
      day: d, start: at(start), end: at(end), drive_s: dayMs / 1000, distance_m: (end - start) * EDGE_M,
      ceiling_s: Number((BigInt(ceilingMs) * BigInt(dayMs)) / BigInt(totalMs)) / 1000, stops: [],
      overnight: d === o.days ? null : { kind: "not_searched" },
      leg: o.full ? { coordinates: ROAD.slice(start, end + 1), eta_s: legMs / 1000, distance_m: (end - start) * EDGE_M } : null,
    });
    start = end;
  }
  const eta = o.full ? legSumMs : totalMs;
  return {
    view: o.full ? "full" : "preview",
    route: { coordinates: ROAD, distance_m: EDGES * EDGE_M },
    eta_s: eta / 1000, fastest_eta_s: FASTEST_MS / 1000, ceiling_s: ceilingMs / 1000, budget_s: budgetMs / 1000,
    extra_budget_pct: pct, lambda: o.lambda, evaluations: 6, eta_is_estimate: true, places_searched: false, days,
  };
}
