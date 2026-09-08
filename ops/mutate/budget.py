"""Mutation harness for LambdaSearch. A catch requires a NAMED TEST to fail, not a non-zero exit.

Tracked in ops/ rather than .artifacts/, because .artifacts/ is gitignored and a task whose `acceptance:`
line names a file nobody else can run has no reproducible red evidence. Each mutation is built first: a
mutation that does not compile is reported `compile-only` and does not count, since a compiler error is a
fact about Swift and not about this suite.

Run `--prove-vacuity` to check the harness itself: it replaces the test file with an empty suite and
requires every mutation to report MISSED. A harness that still reports catches with no tests present is
measuring the compiler.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "ScenicKit" / "Budget" / "LambdaSearch.swift"
TESTS = ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchTests.swift"
SCRATCH = ".build-mutate-budget"

EMPTY_SUITE = ('import Testing\n'
               '@Suite("empty") struct EmptyBudgetSuite {\n'
               '    @Test("nothing") func nothing() { #expect(true) }\n'
               '}\n')

MUTATIONS = [
    # --- structural: the author's original eight ------------------------------------------------------
    ("return the bracket instead of a measured candidate",
     "        return BudgetOutcome(\n            lambda: winner.lambda,\n"
     "            duration: winner.duration,",
     "        return BudgetOutcome(\n            lambda: lo,\n"
     "            duration: winner.duration,"),

    ("let the ceiling slip by one percent, on the guard that enforces it",
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling * 1.01, best == nil || d > best!.duration"),

    ("among feasible routes, prefer the fastest instead of the most scenic",
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling, best == nil || d < best!.duration"),

    ("skip the lambda = 0 seed and start from the bisection",
     "        _ = try evaluate(0)",
     "        // seed removed"),

    ("trust the router's numbers",
     "            guard d.isFinite, d >= 0 else {\n"
     "                throw BudgetError.routerReturnedNonsense(lambda: lambda, duration: d)\n"
     "            }",
     "            // guard removed"),

    ("compare only consecutive samples for monotonicity",
     "        for a in samples {\n            for b in samples where b.lambda > a.lambda {\n"
     "                if b.duration < a.duration { return true }\n            }\n        }",
     "        for (a, b) in zip(samples, samples.dropFirst()) {\n"
     "            if b.lambda > a.lambda && b.duration < a.duration { return true }\n        }"),

    ("call the budget used whenever anything was found",
     "usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "usedBudget: true,"),

    ("keep the last feasible candidate rather than the best",
     "            if d <= ceiling, best == nil || d > best!.duration\n"
     "                || (d == best!.duration && lambda > best!.lambda) {",
     "            if d <= ceiling {"),

    # --- the six a reviewer found uncaught. Every mutation above is STRUCTURAL - delete a guard, invert a
    # --- comparison - and not one touches a number, which is exactly where this suite was blind.
    ("minBudgetUse 0.5 -> 0.05, so 90 seconds of a 25-minute budget counts as used",
     "public static let minBudgetUse = 0.5",
     "public static let minBudgetUse = 0.05"),

    ("minBudgetUse 0.5 -> 0.95, so almost nothing ever counts as used",
     "public static let minBudgetUse = 0.5",
     "public static let minBudgetUse = 0.95"),

    ("maxLambda 8 -> 16, sending four of six router requests into an infeasible region",
     "public static let maxLambda = 8.0",
     "public static let maxLambda = 16.0"),

    ("lambdaTolerance 0.05 -> 0.75, giving back a router request for nothing",
     "public static let lambdaTolerance = 0.05",
     "public static let lambdaTolerance = 0.75"),

    ("the ceiling is one second more generous than the budget",
     "    public var ceiling: TimeInterval { fastest + budget }",
     "    public var ceiling: TimeInterval { fastest + budget + 1 }"),

    ("accept a fractionally negative budget",
     "guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }",
     "guard budget.isFinite, budget > -1 else { throw BudgetError.notABudget(budget) }"),

    # --- and two more of my own in the same spirit ----------------------------------------------------
    ("default maxEvaluations from 6 to 2",
     "maxEvaluations: Int = 6",
     "maxEvaluations: Int = 2"),

    ("drop the tie-break, keeping whichever equally fast route was seen first",
     "                || (d == best!.duration && lambda > best!.lambda) {",
     "                || (d == best!.duration && lambda < best!.lambda) {"),
]


FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build():
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(text, pristine):
    caught, compile_only, missed, trapped = 0, [], [], []
    for name, old, new in MUTATIONS:
        if old not in text:
            sys.stdout.write("SKIP        %-56s anchor not found - harness stale\n" % name)
            missed.append(name)
            continue
        try:
            SRC.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if SRC.read_bytes() == pristine:
                sys.stdout.write("SKIP        %-56s mutation did not land\n" % name)
                missed.append(name)
                continue
            # Build twice before believing a compile failure. Other agents run swift builds on this box
            # concurrently and a transient scratch-directory collision produced a false compile-only
            # verdict for a mutation that compiles fine - checked by hand, exit 0.
            if build() != 0 and build() != 0:
                verdict, code = "compile-only", 1
            else:
                code, out = test()
                if FAIL_LINE.search(out):
                    verdict = "caught"
                elif code != 0:
                    # Non-zero with no named failure means the test process died - a Swift trap. The suite
                    # DID detect the mutation (a test drove the code into it), but not through an assertion,
                    # so it is reported separately rather than counted as a named-test catch. Calling a crash
                    # a passing check would be the kind of flattery this harness exists to avoid.
                    verdict = "trapped"
                else:
                    verdict = "MISSED"
        finally:
            SRC.write_bytes(pristine)

        if verdict == "caught":
            caught += 1
            sys.stdout.write("caught      %-56s exit=%d\n" % (name, code))
        elif verdict == "trapped":
            trapped.append(name)
            sys.stdout.write("trapped     %-56s the code trapped; no assertion fired\n" % name)
        elif verdict == "compile-only":
            compile_only.append(name)
            sys.stdout.write("%-11s %-56s NOT a test catch\n" % (verdict, name))
        else:
            missed.append(name)
            sys.stdout.write("MISSED      %-56s exit=0  no test objected\n" % name)
    return caught, compile_only, missed, trapped


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = SRC.read_bytes()
    pristine_tests = TESTS.read_bytes()
    sys.stdout.write("pristine %s md5 %s\n" % (SRC.name, hashlib.md5(pristine).hexdigest()))

    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: replacing the test file with an empty suite.\n"
                             "Every mutation must now report MISSED; a catch here would mean the harness is\n"
                             "measuring the Swift compiler rather than these tests.\n")
            TESTS.write_text(EMPTY_SUITE, encoding="utf-8", newline="\n")

        if build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                      exit=%d\n" % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        caught, compile_only, missed, trapped = run_all(pristine.decode("utf-8"), pristine)
    finally:
        SRC.write_bytes(pristine)
        TESTS.write_bytes(pristine_tests)

    if SRC.read_bytes() != pristine or TESTS.read_bytes() != pristine_tests:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2
    sys.stdout.write("\nrestored, md5 %s\n" % hashlib.md5(SRC.read_bytes()).hexdigest())
    sys.stdout.write("caught by a named test: %d   trapped: %d   compile-only: %d   MISSED: %d   of %d\n"
                     % (caught, len(trapped), len(compile_only), len(missed), len(MUTATIONS)))
    for n in trapped:
        sys.stdout.write("  trapped (detected, but by a crash and not an assertion): %s\n" % n)
    for n in compile_only:
        sys.stdout.write("  compile-only: %s\n" % n)
    for n in missed:
        sys.stdout.write("  MISSED: %s\n" % n)

    if prove:
        ok = caught == 0
        sys.stdout.write("VACUITY PROOF %s: with no tests present, %d mutations were reported caught\n"
                         % ("OK" if ok else "FAILED", caught))
        return 0 if ok else 1
    return 0 if caught + len(trapped) == len(MUTATIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
