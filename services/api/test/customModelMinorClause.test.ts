import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";

/**
 * T-0244 pre-review B3. customModel.test.ts evaluates the minor clause exactly at lambda 0, 1, 2 and 8, and the
 * Swift parity golden is a recording that never re-runs this module, so a Worker-only change between those
 * lambdas failed nothing: (9/17) x the dullest band for lambda >= 4 matches at 8 and freezes the minor-to-
 * arterial ratio at 1.889 from 4 on, against ruling (a)'s ratio (1 + 2l) / (1 + l), which keeps rising.
 *
 * The expectations are TYPED OUT - 1/(1+2l) and 1/(1+l), serialised as the Worker must (6 decimals, trailing
 * zeros dropped) - never read from bandMultiplier or MINOR_SLOPE, and every step of 0.1 in the bracket is visited.
 */
const STEPS = Array.from({ length: 81 }, (_, tenths) => tenths / 10);
const serialise = (value: number): string => Number(value.toFixed(6)).toString();
const clauses = (lambda: number) =>
  buildCustomModel(lambda, null).priority as unknown as Array<Record<string, string>>;

describe("(f) the minor clause at every lambda step of 0.1", () => {
  it("is 1/(1+2l) as serialised, and the dullest band 1/(1+l), at every step from 0 to 8", () => {
    for (const lambda of STEPS) {
      const priority = clauses(lambda);
      expect(priority[0].if, `lambda ${lambda}`).toBe(
        "(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class == SERVICE) && scenic_score < 7",
      );
      expect(priority[0].multiply_by, `minor at lambda ${lambda}`).toBe(serialise(1 / (1 + 2 * lambda)));
      expect(priority[priority.length - 1].multiply_by, `dullest at lambda ${lambda}`).toBe(
        serialise(1 / (1 + lambda)),
      );
    }
  });

  it("costs the minor clause strictly more against the dullest arterial at every step after 0", () => {
    let previous = 1;
    for (const lambda of STEPS.slice(1)) {
      const priority = clauses(lambda);
      const ratio = Number(priority[priority.length - 1].multiply_by) / Number(priority[0].multiply_by);
      expect(ratio, `minor / dullest cost at lambda ${lambda}`).toBeGreaterThan(previous);
      previous = ratio;
    }
  });
});
