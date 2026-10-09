/**
 * How pretty a whole route is - the port of Sources/ScenicKit/Scoring/RouteScore.swift (T-0332 R1/R2).
 *
 *     0.60 * mean + 0.25 * p90 - 0.15 * dudFraction + 0.10 * min(1, episodes / 3)
 *
 * Every statistic is over METRES, never over edges: the router may split or merge a way into any number of detail
 * runs and that must not move the score. The edges are planWaypoints.ts's tableRows (the PlanTable port) - every row
 * of positive metres with a scenic_score, score / 10 - so the Worker and ScenicKit score the same rows. Held to a
 * third, independent reading over every recorded router answer by the golden under Tests/Fixtures/t0332 (route-scores).
 */
import { tableRows } from "./planWaypoints";
import type { RoutePath } from "./routePath";

export const MEAN_WEIGHT = 0.6;
export const P90_WEIGHT = 0.25;
export const DUD_PENALTY = 0.15;
export const EPISODE_WEIGHT = 0.1;
export const EPISODE_THRESHOLD = 0.6;
export const EPISODE_MIN_LENGTH = 800;
export const EPISODE_TARGET = 3;
export const BOUNDARY_TOLERANCE = 1e-9;
export const DUD_THRESHOLD = 0.25;
/** RouteScore.honestFailureThreshold: below this the route has no scenic middle worth showing. */
export const HONEST_FAILURE_THRESHOLD = 0.45;
/** GraphHopper encodes scenic_score as an integer 0...10; RouteScore reads 0...1. */
export const ENCODED_SCORE_SCALE = 10;

export interface ScoredEdge {
  length: number;
  score: number;
}

export interface RouteScore {
  value: number;
  mean: number;
  p90: number;
  dudFraction: number;
  episodeCount: number;
  totalLength: number;
}

const valid = (e: ScoredEdge) =>
  Number.isFinite(e.length) && e.length > 0 && Number.isFinite(e.score) && e.score >= 0 && e.score <= 1;

/** RouteScore.lengthWeightedPercentile: ascending by score, ties at a boundary broken toward the lower score. */
function percentile(edges: ScoredEdge[], fraction: number): number {
  const sorted = [...edges].sort((a, b) => a.score - b.score);
  let cumulative = 0;
  const running = sorted.map((e) => (cumulative += e.length));
  const total = cumulative;
  const target = total * fraction;
  const tolerance = total * BOUNDARY_TOLERANCE;
  for (let i = 0; i < sorted.length; i += 1) if (running[i]! >= target - tolerance) return sorted[i]!.score;
  return sorted[sorted.length - 1]!.score;
}

/** RouteScore.episodes: maximal above-threshold runs accumulated ACROSS edge boundaries, at least 800 m long. */
function episodes(edges: ScoredEdge[]): number {
  let scale = 0;
  for (const e of edges) scale += e.length;
  const tolerance = scale * BOUNDARY_TOLERANCE;
  let count = 0;
  let run = 0;
  for (const e of edges) {
    if (e.score > EPISODE_THRESHOLD) {
      run += e.length;
    } else {
      if (run >= EPISODE_MIN_LENGTH - tolerance) count += 1;
      run = 0;
    }
  }
  if (run >= EPISODE_MIN_LENGTH - tolerance) count += 1;
  return count;
}

/** RouteScore(edges:): null for no edges or any invalid edge - "no road" is not a dull road. */
export function scoreEdges(edges: ScoredEdge[]): RouteScore | null {
  if (edges.length === 0 || !edges.every(valid)) return null;
  const total = edges.reduce((sum, e) => sum + e.length, 0);
  if (!(total > 0) || !Number.isFinite(total)) return null;
  const mean = edges.reduce((sum, e) => sum + e.score * e.length, 0) / total;
  const p90 = percentile(edges, 0.9);
  const dudFraction = edges.filter((e) => e.score <= DUD_THRESHOLD).reduce((sum, e) => sum + e.length, 0) / total;
  const episodeCount = episodes(edges);
  const raw = MEAN_WEIGHT * mean + P90_WEIGHT * p90 - DUD_PENALTY * dudFraction +
    EPISODE_WEIGHT * Math.min(1, episodeCount / EPISODE_TARGET);
  return { value: Math.min(1, Math.max(0, raw)), mean, p90, dudFraction, episodeCount, totalLength: total };
}

/** PlanTable.scoredEdges: the rows of positive metres that carry a scenic_score, as edges of score / 10. */
export function scoredEdges(path: RoutePath): ScoredEdge[] {
  return tableRows(path)
    .filter((row) => row.meters > 0 && row.scenicScore !== null)
    .map((row) => ({ length: row.meters, score: (row.scenicScore as number) / ENCODED_SCORE_SCALE }));
}

/** The score planScenic reads for the route it would ship. */
export function routeScoreOf(path: RoutePath): RouteScore | null {
  return scoreEdges(scoredEdges(path));
}

/** RouteScore.isHonestFailure, with an unscorable route an honest failure too (T-0332 R3: fail closed). */
export function isHonestFailure(score: RouteScore | null): boolean {
  return score === null || score.value < HONEST_FAILURE_THRESHOLD;
}
