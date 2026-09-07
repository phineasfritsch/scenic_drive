import { describe, expect, it } from "vitest";
import cases from "../../../ops/lib/ro_cases.json";
import { readOnlyProblem } from "../src/ro";

describe("read-only SQL grammar (shared cases with ops/lib/ro_grammar.py)", () => {
  for (const sql of cases.accept) {
    it(`accepts ${JSON.stringify(sql)}`, () => {
      expect(readOnlyProblem(sql)).toBeNull();
    });
  }
  for (const sql of cases.reject) {
    it(`rejects ${JSON.stringify(sql)}`, () => {
      expect(readOnlyProblem(sql)).not.toBeNull();
    });
  }
  it("rejects anything over the length cap", () => {
    expect(readOnlyProblem("SELECT " + "1,".repeat(3000) + "1")).toMatch(/longer/);
  });
});
