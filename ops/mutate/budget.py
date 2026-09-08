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
ERR = ROOT / "Sources" / "ScenicKit" / "Budget" / "BudgetError.swift"
# BOTH suites. reviewer-pr71's blocking finding: commit bc5e7f6 split ten tests into
# LambdaSearchBudgetUseTests.swift and --prove-vacuity kept emptying only the first file, so it reported
# "VACUITY PROOF FAILED: 8 mutations were reported caught" while the task log recorded OK. The harness's own
# message - "with no tests present" - was false; it was measuring the sibling test file. A demonstration
# that decayed at the last commit, and exactly the shape of defect this repository exists to catch.
TEST_FILES = [ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "LambdaSearchBudgetUseTests.swift"]
SCRATCH = ".build-mutate-budget"

def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces - two identically-named structs would not compile, and
    a compile failure would make the vacuity proof pass for the wrong reason."""
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))

MUTATIONS = [
    # --- structural: the author's original eight ------------------------------------------------------
    ("return the bracket instead of a measured candidate", SRC,
     "        return BudgetOutcome(\n            lambda: winner.lambda,\n"
     "            duration: winner.duration,",
     "        return BudgetOutcome(\n            lambda: lo,\n"
     "            duration: winner.duration,"),

    ("let the ceiling slip by one percent, on the guard that enforces it", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling * 1.01, best == nil || d > best!.duration"),

    ("among feasible routes, prefer the fastest instead of the most scenic", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration",
     "            if d <= ceiling, best == nil || d < best!.duration"),

    ("skip the lambda = 0 seed and start from the bisection", SRC,
     "        _ = try evaluate(0)",
     "        // seed removed"),

    ("trust the router's numbers", SRC,
     "            guard d.isFinite, d >= 0 else {\n"
     "                throw BudgetError.routerReturnedNonsense(lambda: lambda, duration: d)\n"
     "            }",
     "            // guard removed"),

    ("compare only consecutive samples for monotonicity", SRC,
     "        for a in samples {\n            for b in samples where b.lambda > a.lambda {\n"
     "                if b.duration < a.duration { return true }\n            }\n        }",
     "        for (a, b) in zip(samples, samples.dropFirst()) {\n"
     "            if b.lambda > a.lambda && b.duration < a.duration { return true }\n        }"),

    ("call the budget used whenever anything was found", SRC,
     "usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "usedBudget: true,"),

    ("keep the last feasible candidate rather than the best", SRC,
     "            if d <= ceiling, best == nil || d > best!.duration\n"
     "                || (d == best!.duration && lambda > best!.lambda) {",
     "            if d <= ceiling {"),

    # --- the six a reviewer found uncaught. Every mutation above is STRUCTURAL - delete a guard, invert a
    # --- comparison - and not one touches a number, which is exactly where this suite was blind.
    ("minBudgetUse 0.5 -> 0.05, so 90 seconds of a 25-minute budget counts as used", SRC,
     "public static let minBudgetUse = 0.5",
     "public static let minBudgetUse = 0.05"),

    ("minBudgetUse 0.5 -> 0.95, so almost nothing ever counts as used", SRC,
     "public static let minBudgetUse = 0.5",
     "public static let minBudgetUse = 0.95"),

    ("maxLambda 8 -> 16, sending four of six router requests into an infeasible region", SRC,
     "public static let maxLambda = 8.0",
     "public static let maxLambda = 16.0"),

    ("lambdaTolerance 0.05 -> 0.75, giving back a router request for nothing", SRC,
     "public static let lambdaTolerance = 0.05",
     "public static let lambdaTolerance = 0.75"),

    ("the ceiling is one second more generous than the budget", SRC,
     "    public var ceiling: TimeInterval { fastest + budget }",
     "    public var ceiling: TimeInterval { fastest + budget + 1 }"),

    ("accept a fractionally negative budget", SRC,
     "guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }",
     "guard budget.isFinite, budget > -1 else { throw BudgetError.notABudget(budget) }"),

    # --- and two more of my own in the same spirit ----------------------------------------------------
    ("default maxEvaluations from 6 to 2", SRC,
     "maxEvaluations: Int = 6",
     "maxEvaluations: Int = 2"),

    ("drop the tie-break, keeping whichever equally fast route was seen first", SRC,
     "                || (d == best!.duration && lambda > best!.lambda) {",
     "                || (d == best!.duration && lambda < best!.lambda) {"),

    # --- reviewer-pr71's findings F1 to F4 ----------------------------------------------------------------
    # F3: the "at least half the budget" boundary had no witness on either side.
    ("usedBudget becomes strict, so exactly half the budget stops counting", SRC,
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "            usedBudget: budget == 0 || winner.duration > fastest + Self.minBudgetUse * budget,"),

    ("a zero budget stops counting as used", SRC,
     "            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,",
     "            usedBudget: winner.duration >= fastest + Self.minBudgetUse * budget,"),

    # F2: the tolerance termination fired in no test at all, so deleting it was free - and widening it gave
    # back a router request for nothing, with the whole suite green.
    ("drop the lambdaTolerance termination, spending router requests for nothing", SRC,
     "        while evaluations < maxEvaluations, hi - lo > Self.lambdaTolerance {",
     "        while evaluations < maxEvaluations {"),

    # F4: BudgetError's whole CustomStringConvertible conformance had no behavioural coverage. These strings
    # reach a log and a bug report.
    ("the error message reports the lambda as the duration", ERR,
     '            return "router returned \\(duration) s at lambda \\(lambda)"',
     '            return "router returned \\(lambda) s at lambda \\(duration)"'),

    ("the no-feasible-lambda message loses the ceiling it was measured against", ERR,
     '            return "no lambda produced a route within the \\(ceiling) s ceiling in \\(evaluations) "',
     '            return "no lambda produced a route within the ceiling in \\(evaluations) "'),

    ("a bad budget is reported as a bad duration", SRC,
     "        guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }",
     "        guard budget.isFinite, budget >= 0 else { throw BudgetError.notADuration(budget) }"),
]

# Mutations this suite is KNOWN not to catch, asserted the other way round.
#
# A gap merely absent from the list is a gap nobody can see. Each entry names why, and the harness FAILS if
# one starts being caught - that means the gap closed and it should move up into MUTATIONS.
KNOWN_MISSED = [
    # reviewer-pr71's F7: the seed runs before the loop, so the clamp cannot change the number of
    # evaluations. No behaviour to assert; the clamp is defensive and stays.
    ("drop the max(1, ...) clamp on maxEvaluations", SRC,
     "max(1, maxEvaluations)", "maxEvaluations"),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE - a catch means a test has an opinion about
# how the code is WRITTEN rather than what it DOES.
EQUIVALENT = [
    ("start the evaluation counter from a different literal zero", SRC,
     "        var evaluations = 0",
     "        var evaluations = 0o0"),
]



FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build() -> int:
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(pristine, mutations):
    """Returns a verdict per mutation. SKIP is its own bucket, never folded into MISSED: a mutation that did
    not land tells you the harness is stale, which is the opposite of what MISSED means."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    for name, path, old, new in mutations:
        text = pristine[path].decode("utf-8")
        if old not in text:
            sys.stdout.write("SKIP        %-62s anchor not found - harness is stale\n" % name)
            out["skipped"].append(name)
            continue
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if path.read_bytes() == pristine[path]:
                sys.stdout.write("SKIP        %-62s mutation did not land\n" % name)
                out["skipped"].append(name)
                continue
            # Built twice before a compile failure is believed: other agents run swift builds on this box
            # concurrently and a transient scratch collision produced a false compile-only verdict once.
            if build() != 0 and build() != 0:
                verdict, code = "compile_only", 1
            else:
                code, txt = test()
                verdict = "caught" if FAIL_LINE.search(txt) else ("trapped" if code != 0 else "missed")
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        label = {"caught": "caught", "trapped": "trapped", "compile_only": "compile-only", "missed": "MISSED"}
        note = {"caught": "exit=%d" % code,
                "trapped": "non-zero exit, but NO named test failed - does not count",
                "compile_only": "a fact about Swift, not about these tests - does not count",
                "missed": "exit=0  no test objected"}
        sys.stdout.write("%-12s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = {f: f.read_bytes() for f in (SRC, ERR)}
    pristine_tests = {f: f.read_bytes() for f in TEST_FILES}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    known = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: the test file is replaced by an empty suite, so every\n"
                             "mutation must report MISSED - not merely 'not caught'.\n")
            for f in TEST_FILES:
                f.write_text(empty_suite(f), encoding="utf-8", newline="\n")

        if build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                              exit=%d\n" % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        r = run_all(pristine, MUTATIONS)

        if not prove:
            sys.stdout.write("\nKNOWN GAPS - asserted MISSED on purpose; a catch here means the gap closed\n")
            known = run_all(pristine, KNOWN_MISSED)
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        for f, b in pristine_tests.items():
            f.write_bytes(b)

    if any(f.read_bytes() != b for f, b in pristine.items()) or any(f.read_bytes() != b for f, b in pristine_tests.items()):
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2

    sys.stdout.write("\nrestored: " + ", ".join(hashlib.md5(f.read_bytes()).hexdigest()[:8] for f in pristine) + "\n")
    sys.stdout.write("caught by a named test: %d of %d   (trapped %d, compile-only %d, MISSED %d, skipped %d)\n"
                     % (len(r["caught"]), len(MUTATIONS), len(r["trapped"]), len(r["compile_only"]),
                        len(r["missed"]), len(r["skipped"])))
    for bucket, why in (("trapped", "detected, but by a crash and not an assertion - DOES NOT COUNT"),
                        ("compile_only", "a compile failure is not a test catch - DOES NOT COUNT"),
                        ("missed", "no test objected"),
                        ("skipped", "anchor missing - the harness is stale")):
        for n in r[bucket]:
            sys.stdout.write("  %s: %s (%s)\n" % (bucket.upper(), n, why))

    if prove:
        ok = len(r["caught"]) == 0 and len(r["missed"]) == len(MUTATIONS)
        sys.stdout.write("VACUITY PROOF %s: with no tests present, caught=%d (need 0) and MISSED=%d of %d\n"
                         "  (requiring MISSED to be complete, not just caught==0, is what stops a harness\n"
                         "   broken in the compile-only direction from proving its own non-vacuity)\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1

    known_ok = known is not None and len(known["missed"]) + len(known["trapped"]) == len(KNOWN_MISSED)
    if not known_ok and known is not None:
        sys.stdout.write("KNOWN-GAP ARM FAILED: %d of %d still uncaught. A gap that closed is good news - "
                         "move it into MUTATIONS.\n" % (len(known["missed"]) + len(known["trapped"]),
                                                        len(KNOWN_MISSED)))
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok and known_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
