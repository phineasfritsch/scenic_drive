/**
 * T-0248 R7: src/planWaypoints.ts ports PlanTable's row cutting and PlanWaypoints.decisionPoints. The t0221
 * recording's nine pins survived two table mutants (the first population run's pins-closed-run and
 * pins-merge-roads), because its nine longest road changes do not sit on those boundaries; these routes do.
 */
import { describe, expect, it } from "vitest";
import { decisionPoints } from "../src/planWaypoints";
import type { DetailRun, RoutePath } from "../src/routePath";

const line: [number, number][] = [[-118.5, 34.0], [-118.49, 34.0], [-118.48, 34.0], [-118.47, 34.0], [-118.46, 34.0]];

function path(details: Record<string, DetailRun[]>): RoutePath {
  return { timeMs: 60_000, distanceM: 4000, coordinates: line, details };
}

describe("decisionPoints - the PlanTable / PlanWaypoints port", () => {
  it("a run names the segment that STARTS at its first point (half-open [from, to))", () => {
    const route = path({
      osm_way_id: [{ from: 0, to: 2, value: 100 }, { from: 2, to: 4, value: 200 }],
      road_class: [{ from: 0, to: 4, value: "primary" }],
    });
    expect(decisionPoints(route)).toEqual([{ lat: 34.0, lon: -118.48 }]);
  });

  it("a change of road class alone, on the same way and score, is a decision point", () => {
    const route = path({
      osm_way_id: [{ from: 0, to: 4, value: 100 }],
      road_class: [{ from: 0, to: 2, value: "primary" }, { from: 2, to: 4, value: "secondary" }],
      scenic_score: [{ from: 0, to: 4, value: 5 }],
    });
    expect(decisionPoints(route)).toEqual([{ lat: 34.0, lon: -118.48 }]);
  });

  it("a change of scenic score alone is a decision point; origin and destination never are", () => {
    const route = path({
      osm_way_id: [{ from: 0, to: 4, value: 100 }],
      scenic_score: [{ from: 0, to: 1, value: 2 }, { from: 1, to: 4, value: 6 }],
    });
    expect(decisionPoints(route)).toEqual([{ lat: 34.0, lon: -118.49 }]);
    expect(decisionPoints(path({}))).toEqual([]);
  });
});
