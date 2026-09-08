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
  // The literal is deliberate and must NOT be derived from MAX_SQL_LENGTH. Building it from the constant
  // makes the statement grow with the cap, so the test can never fail for any value of it - and a raise
  // applied to BOTH src/ro.ts and ro_cases.json then passed the whole suite, where main went red. A bound
  // computed from the value it bounds is this repository's signature defect; this file introduced one and an
  // independent reviewer of PR #53 caught it. 6008 characters, fixed, is the magnitude bound.
  it("rejects anything over the length cap", () => {
    expect(readOnlyProblem("SELECT " + "1,".repeat(3000) + "1")).toMatch(/longer/);
  });
  // The same magnitudes, held as data in ops/lib/ro_cases.json and run by ops/lib/ro_grammar.py too. A
  // comment saying "must NOT be derived" is not a guard - CLAUDE.md line 27 - and it was the only thing
  // protecting the literal above. These numbers live in JSON, which has no expressions, so they cannot be
  // re-derived from MAX_SQL_LENGTH by any later edit to this file.
  for (const probe of cases.length_probes) {
    it(`${probe.expect}s a statement of exactly ${probe.chars} characters`, () => {
      const problem = readOnlyProblem("SELECT " + "1".repeat(probe.chars - 7));
      if (probe.expect === "reject") expect(problem).toMatch(/longer/);
      else expect(problem).toBeNull();
    });
  }
  it("keeps MAX_SQL_LENGTH inside the fixed probe bracket", () => {
    const under = cases.length_probes.filter((p) => p.expect === "accept").map((p) => p.chars);
    const over = cases.length_probes.filter((p) => p.expect === "reject").map((p) => p.chars);
    expect(under.length).toBeGreaterThan(0);
    expect(over.length).toBeGreaterThan(0);
    expect(Math.max(...under)).toBeLessThanOrEqual(MAX_SQL_LENGTH);
    expect(MAX_SQL_LENGTH).toBeLessThan(Math.min(...over));
  });
  // The cap is the one rule the shared case list cannot hold as a case, so it is held as a number and both
  // implementations check their own literal against it. ops/lib/ro_grammar.py asserts exactly this.
  it("agrees with ops/lib/ro_grammar.py about the cap", () => {
    expect(MAX_SQL_LENGTH).toBe(cases.max_sql_length);
  });
});
