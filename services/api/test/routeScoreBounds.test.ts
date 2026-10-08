/**
 * T-0332 A2: every bound the Worker's RouteScore turns on, through the functions production runs - isHonestFailure
 * (planScenic's predicate), scoreEdges (what routeScoreOf scores with) and routeScoreOf itself. Each row states its
 * expected result whole; nothing is recomputed through the module under test.
 */
import { describe, expect, it } from "vitest";
import { isHonestFailure, routeScoreOf, scoreEdges, type RouteScore, type ScoredEdge } from "../src/routeScore";
import type { RoutePath } from "../src/routePath";

/** The adjacent double: +1 toward +infinity, -1 toward -infinity (positive finite x only). */
function adjacent(x: number, direction: 1 | -1): number {
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, x);
  view.setBigUint64(0, view.getBigUint64(0) + BigInt(direction));
  return view.getFloat64(0);
}

/** One edge of `length` at `score`, with the dud and episode verdicts the row asserts. */
function single(length: number, score: number, dud: 0 | 1, episodes: 0 | 1): RouteScore {
  const raw = 0.6 * score + 0.25 * score - 0.15 * dud + 0.1 * (episodes / 3);
  return { value: Math.min(1, Math.max(0, raw)), mean: score, p90: score, dudFraction: dud, episodeCount: episodes,
    totalLength: length };
}

describe("RouteScore bounds (T-0332 A2)", () => {
  const score = (value: number): RouteScore => ({ value, mean: 0, p90: 0, dudFraction: 0, episodeCount: 0, totalLength: 1 });
  it.each([
    ["exactly 0.45 is not an honest failure", score(0.45), false],
    ["the next double below 0.45 is", score(adjacent(0.45, -1)), true],
    ["an unscorable route (null) is", null, true],
  ] as [string, RouteScore | null, boolean][])("isHonestFailure: %s", (_n, input, expected) => {
    expect(isHonestFailure(input)).toBe(expected);
  });

  it.each([
    ["0.25 is a dud", 1000, 0.25, 1, 0],
    ["the next double above 0.25 is not", 1000, adjacent(0.25, 1), 0, 0],
    ["0.6 over 1000 m is not an episode", 1000, 0.6, 0, 0],
    ["the next double above 0.6 over 1000 m is", 1000, adjacent(0.6, 1), 0, 1],
    ["0.9 over exactly 800 m is an episode", 800, 0.9, 0, 1],
    ["0.9 over 799.999 m is not (1 mm short; the tolerance is 1e-9 of the route, 8e-7 m)", 799.999, 0.9, 0, 0],
    ["0.9 over 800 m less 4e-7 m is, inside the tolerance", 800 - 4e-7, 0.9, 0, 1],
    ["score 0 is valid and a dud", 1000, 0, 1, 0],
    ["score 1 is valid", 1000, 1, 0, 1],
  ] as [string, number, number, 0 | 1, 0 | 1][])("scoreEdges: %s", (_n, length, s, dud, episodes) => {
    expect(scoreEdges([{ length, score: s }])).toEqual(single(length, s, dud, episodes));
  });

  it.each([
    ["no edges", []],
    ["a score above 1", [{ length: 1000, score: adjacent(1, 1) }]],
    ["a negative score", [{ length: 1000, score: -Number.MIN_VALUE }]],
    ["a zero length", [{ length: 0, score: 0.5 }]],
    ["a NaN score", [{ length: 1000, score: Number.NaN }]],
    ["an infinite length", [{ length: Number.POSITIVE_INFINITY, score: 0.5 }]],
  ] as [string, ScoredEdge[]][])("scoreEdges: %s is null", (_n, edges) => {
    expect(scoreEdges(edges)).toBeNull();
  });

  it("the 90th-percentile boundary on [9000 m @ 0.1, 1000 m @ 0.9] is 0.1 for every split k = 1..12", () => {
    const p90s = Array.from({ length: 12 }, (_, i) => {
      const k = i + 1;
      const edges = [...Array.from({ length: k }, () => ({ length: 9000 / k, score: 0.1 })),
        ...Array.from({ length: k }, () => ({ length: 1000 / k, score: 0.9 }))];
      return scoreEdges(edges)!.p90;
    });
    expect(p90s).toEqual(Array.from({ length: 12 }, () => 0.1));
  });
});

describe("routeScoreOf reads the router's scenic_score (T-0332 A2)", () => {
  const LINE: [number, number][] = [[-118.5, 34.0], [-118.49, 34.005], [-118.48, 34.01]];
  const path = (details: Record<string, [number, number, number | string | null][]>, coordinates = LINE): RoutePath => ({
    timeMs: 60_000, distanceM: 2000, coordinates, details: Object.fromEntries(Object.entries(details).map(([k, runs]) =>
      [k, runs.map(([from, to, value]) => ({ from, to, value }))])),
  });
  it.each([
    ["no scenic_score detail", path({ osm_way_id: [[0, 2, 7]] })],
    ["an empty scenic_score detail", path({ scenic_score: [] })],
    ["every scored row 0 m long", path({ scenic_score: [[0, 2, 8]] }, [[-118.5, 34], [-118.5, 34], [-118.5, 34]])],
    ["an encoded score of 11", path({ scenic_score: [[0, 1, 8], [1, 2, 11]] })],
    ["an encoded score of -1", path({ scenic_score: [[0, 1, 8], [1, 2, -1]] })],
  ] as [string, RoutePath][])("%s is null, never clamped", (_n, input) => {
    expect(routeScoreOf(input)).toBeNull();
  });

  it("encoded 10 and 0 are the ends of the scale; unscored metres are left out", () => {
    const scored = routeScoreOf(path({ scenic_score: [[0, 1, 10], [1, 2, null]] }))!;
    expect([scored.mean, scored.p90, scored.dudFraction]).toEqual([1, 1, 0]);
    const dull = routeScoreOf(path({ scenic_score: [[0, 2, 0]] }))!;
    expect([dull.value, dull.mean, dull.dudFraction]).toEqual([0, 0, 1]);
  });
});
