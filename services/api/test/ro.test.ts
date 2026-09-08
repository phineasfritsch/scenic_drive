import { describe, expect, it } from "vitest";
import cases from "../../../ops/lib/ro_cases.json";
import { MAX_SQL_LENGTH, readOnlyProblem } from "../src/ro";

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
    expect(readOnlyProblem("SELECT " + "1,".repeat(MAX_SQL_LENGTH) + "1")).toMatch(/longer/);
  });
  // The cap is the one rule the shared case list cannot hold as a case, so it is held as a number and both
  // implementations check their own literal against it. ops/lib/ro_grammar.py asserts exactly this.
  it("agrees with ops/lib/ro_grammar.py about the cap", () => {
    expect(MAX_SQL_LENGTH).toBe(cases.max_sql_length);
  });
});
