/**
 * T-0332 A1: the Worker's RouteScore equals a third, independent reading - Tests/Fixtures/t0332/oracle.py's golden -
 * over EVERY recorded router answer under Tests/Fixtures that carries scenic_score, through routeScoreOf (the function
 * planScenic calls). Swift's RouteScoreParityTests reads the same golden through RouteScore(edges:), so the two ports
 * are held to one file neither of them wrote.
 */
import { describe, expect, it } from "vitest";
import { HONEST_FAILURE_THRESHOLD, routeScoreOf, type RouteScore } from "../src/routeScore";
import { decodeRoutePath } from "../src/routePath";
import goldenRaw from "../../../Tests/Fixtures/t0332/route-scores.json?raw";

const PREFIX = "../../../Tests/Fixtures/";
const FIXTURES = import.meta.glob("../../../Tests/Fixtures/**/*.json", { query: "?raw", import: "default", eager: true }) as
  Record<string, string>;
const golden = JSON.parse(goldenRaw) as { threshold: number; scores: (RouteScore & { file: string })[] };
const TOLERANCE = 1e-9;
const FIELDS = ["value", "mean", "p90", "dudFraction", "totalLength"] as const;

function carriesScenicScore(raw: string): boolean {
  try {
    const details = (JSON.parse(raw) as { paths?: { details?: Record<string, unknown> }[] }).paths?.[0]?.details;
    return details !== undefined && details !== null && "scenic_score" in details;
  } catch {
    return false;
  }
}

describe("RouteScore parity, Worker vs the T-0332 oracle (A1)", () => {
  it("the golden lists exactly the recorded answers that carry scenic_score: 44, 24 below 0.45, 20 at or above", () => {
    const carrying = Object.entries(FIXTURES).filter(([, raw]) => carriesScenicScore(raw))
      .map(([name]) => name.slice(PREFIX.length)).sort();
    expect(golden.scores.map((row) => row.file)).toEqual(carrying);
    expect(golden.threshold).toBe(HONEST_FAILURE_THRESHOLD);
    expect(golden.scores).toHaveLength(44);
    expect(golden.scores.filter((row) => row.value < 0.45)).toHaveLength(24);
    expect(golden.scores.filter((row) => row.value >= 0.45)).toHaveLength(20);
  });

  it("routeScoreOf equals the golden on every file, field for field, to 1e-9", () => {
    const misses: unknown[] = [];
    for (const row of golden.scores) {
      const score = routeScoreOf(decodeRoutePath(FIXTURES[PREFIX + row.file]!));
      if (score === null) {
        misses.push({ file: row.file, score: null });
        continue;
      }
      const off = FIELDS.filter((field) => !(Math.abs(score[field] - row[field]) <= TOLERANCE));
      if (off.length > 0 || score.episodeCount !== row.episodeCount) misses.push({ file: row.file, off, score });
    }
    expect(misses).toEqual([]);
  });

  it("the westwood-malibu +25 route is the honest failure T-0327 measured (0.226, 0 episodes, half dud)", () => {
    const row = golden.scores.find((r) => r.file === "t0221/westwood-malibu/lambda-3.25.json")!;
    expect([row.value.toFixed(3), row.episodeCount, row.dudFraction.toFixed(3)]).toEqual(["0.226", 0, "0.500"]);
  });
});
