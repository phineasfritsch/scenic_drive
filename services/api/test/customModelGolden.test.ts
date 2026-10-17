import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";

/**
 * T-0190. Tests/Fixtures/custom-model/ is the ONE record of the per-request model outside this Worker: the Swift
 * port (LambdaCustomModelParityTests) is held to its bytes, and the routing oracle (services/routing/tests,
 * request_models.py) routes those bytes as-is through GraphHopper. Before this file nothing re-ran the shipped
 * builder against the record, so a clause added, dropped or re-weighted here left every consumer green on a
 * model production no longer sends.
 *
 * Whole equality, bytes: the record is JSON.stringify(buildCustomModel(lambda, null), null, 2) plus a newline,
 * the T-0182 emitter's exact printing. GraphHopper reads multiply_by as a string and the Swift port compares
 * bytes, so "the same numbers" is not the property - the same text is.
 *
 * The file set is compared WHOLE too: a recorded lambda deleted, or a stray one added, is red by name.
 */
const RECORDED = import.meta.glob("../../../Tests/Fixtures/custom-model/lambda-*.json", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

const LAMBDAS = ["0", "1", "2", "2.5", "4", "7.75", "8"];
const FILE = /\/lambda-([0-9.]+)\.json$/;

const byLambda = new Map(
  Object.entries(RECORDED).map(([path, text]) => [FILE.exec(path)?.[1] ?? path, text] as const),
);

describe("the custom-model record is the shipped builder's output (T-0190)", () => {
  it("records exactly the seven lambdas the Swift port and the routing oracle read", () => {
    expect([...byLambda.keys()].sort((a, b) => Number(a) - Number(b))).toEqual(LAMBDAS);
  });

  for (const lambda of LAMBDAS) {
    it(`lambda-${lambda}.json is byte-equal to buildCustomModel(${lambda}, null)`, () => {
      const shipped = JSON.stringify(buildCustomModel(Number(lambda), null), null, 2) + "\n";
      expect(byLambda.get(lambda)).toBe(shipped);
    });
  }
});
