import { describe, expect, it } from "vitest";
import { buildCustomModel, type ClosureCollection } from "../src/customModel";

/**
 * T-0244 pre-review B3. customModel.test.ts evaluates the minor clause exactly at lambda 0, 1, 2 and 8, and the
 * Swift parity golden is a recording that never re-runs this module, so a Worker-only change between those
 * lambdas failed nothing: (9/17) x the dullest band for lambda >= 4 matches at 8 and freezes the minor-to-
 * arterial ratio at 1.889 from 4 on, against ruling (a)'s ratio (1 + 2l) / (1 + l), which keeps rising.
 *
 * The expectations are TYPED OUT - 1/(1+2l) and 1/(1+l), serialised as the Worker must (6 decimals, trailing
 * zeros dropped) - never read from bandMultiplier or MINOR_SLOPE, and every step of 0.1 in the bracket is visited.
 *
 * T-0244 round 1 B2: and every one of them with closures live as well as with none. The closure branch builds on
 * the same priority array, so a write to the minor clause after the closure ids passed a null-only file. The
 * dullest band is the `else` clause, not the last element: with closures the last element is the closure clause.
 */
const STEPS = Array.from({ length: 81 }, (_, tenths) => tenths / 10);
const serialise = (value: number): string => Number(value.toFixed(6)).toString();
const square = (lon: number, lat: number) => ({
  type: "Feature" as const,
  geometry: {
    type: "Polygon" as const,
    coordinates: [[[lon, lat], [lon + 0.01, lat], [lon + 0.01, lat + 0.01], [lon, lat + 0.01], [lon, lat]]],
  },
  properties: {},
});
const CLOSURES: ClosureCollection = { type: "FeatureCollection", features: [square(-118.6, 34.09), square(-118.5, 34.05)] };
const FEEDS: Array<[string, ClosureCollection | null]> = [["no closures", null], ["two closures", CLOSURES]];
const clauses = (lambda: number, closures: ClosureCollection | null) =>
  buildCustomModel(lambda, closures).priority as unknown as Array<Record<string, string>>;
const dullest = (priority: Array<Record<string, string>>) => priority.filter((clause) => "else" in clause);

describe("(f) the minor clause at every lambda step of 0.1", () => {
  it("is 1/(1+2l) as serialised, and the dullest band 1/(1+l), at every step from 0 to 8, closures or none", () => {
    for (const [feed, closures] of FEEDS) {
      for (const lambda of STEPS) {
        const priority = clauses(lambda, closures);
        expect(priority[0].if, `${feed}, lambda ${lambda}`).toBe(
          "(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class == SERVICE) && scenic_score < 7",
        );
        expect(priority[0].multiply_by, `${feed}, minor at lambda ${lambda}`).toBe(serialise(1 / (1 + 2 * lambda)));
        const dull = dullest(priority);
        expect(dull.length, `${feed}, one else clause at lambda ${lambda}`).toBe(1);
        expect(dull[0].multiply_by, `${feed}, dullest at lambda ${lambda}`).toBe(serialise(1 / (1 + lambda)));
      }
    }
  });

  it("costs the minor clause strictly more against the dullest arterial at every step after 0, closures or none", () => {
    for (const [feed, closures] of FEEDS) {
      let previous = 1;
      for (const lambda of STEPS.slice(1)) {
        const priority = clauses(lambda, closures);
        const ratio = Number(dullest(priority)[0].multiply_by) / Number(priority[0].multiply_by);
        expect(ratio, `${feed}, minor / dullest cost at lambda ${lambda}`).toBeGreaterThan(previous);
        previous = ratio;
      }
    }
  });

  it("with closures live is the no-closure priority clause for clause, plus one closure clause at 0", () => {
    for (const lambda of STEPS) {
      const bare = clauses(lambda, null);
      const live = clauses(lambda, CLOSURES);
      expect(live.slice(0, bare.length), `lambda ${lambda}`).toEqual(bare);
      expect(live.slice(bare.length), `lambda ${lambda}`).toEqual([
        { if: "in_closure_1 || in_closure_2", multiply_by: "0" },
      ]);
    }
  });
});
