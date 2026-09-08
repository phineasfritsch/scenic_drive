"""Mutation harness for RouteScore. A catch requires a NAMED TEST to fail, not a non-zero exit.

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
SRC = ROOT / "Sources" / "ScenicKit" / "Scoring" / "RouteScore.swift"
TESTS = ROOT / "Tests" / "ScenicKitTests" / "RouteScoreTests.swift"
SCRATCH = ".build-mutate-routescore"

EMPTY_SUITE = ('import Testing\n'
               '@Suite("empty") struct EmptyRouteScoreSuite {\n'
               '    @Test("nothing") func nothing() { #expect(true) }\n'
               '}\n')

MUTATIONS = [
    # --- structural: the natural-but-wrong implementation -------------------------------------------
    ("mean over the edge list instead of over metres",
     "let mean = edges.reduce(0.0) { $0 + $1.score * $1.length } / total",
     "let mean = edges.reduce(0.0) { $0 + $1.score } / Double(edges.count)"),

    ("dud fraction over the edge list instead of over metres",
     "let dud = edges.filter { $0.score <= Self.dudThreshold }\n"
     "                       .reduce(0.0) { $0 + $1.length } / total",
     "let dud = Double(edges.filter { $0.score <= Self.dudThreshold }.count) / Double(edges.count)"),

    ("ask the episode question per edge",
     "        var count = 0\n        var run = 0.0\n        for e in edges {\n"
     "            if e.score > episodeThreshold {\n                run += e.length\n",
     "        var count = 0\n        var run = 0.0\n        for e in edges {\n"
     "            if e.score > episodeThreshold && e.length >= episodeMinLength {\n"
     "                count += 1\n            }\n            if false {\n                run += e.length\n"),

    ("forget the episode that the route ends on",
     "        if run >= episodeMinLength { count += 1 }\n        return count",
     "        return count"),

    ("add the dud fraction instead of subtracting it",
     "- Self.dudPenalty * dud",
     "+ Self.dudPenalty * dud"),

    ("drop the clamp and let a duds-only route score negative",
     "self.value = min(1.0, max(0.0, raw))",
     "self.value = raw"),

    ("score an empty route rather than refusing it",
     "        guard !edges.isEmpty, edges.allSatisfy(\\.isValid) else { return nil }\n"
     "        let total = edges.reduce(0.0) { $0 + $1.length }\n"
     "        guard total > 0, total.isFinite else { return nil }",
     "        guard edges.allSatisfy(\\.isValid) else { return nil }\n"
     "        let total = edges.reduce(0.0) { $0 + $1.length }"),

    # --- the percentile, where the shipped bug was --------------------------------------------------
    ("sort the percentile the other way, turning p90 into p10",
     "let sorted = edges.sorted { $0.score < $1.score }",
     "let sorted = edges.sorted { $0.score > $1.score }"),

    # The shipped regression, restored whole. A separate `reduce` is NOT independently a defect any more:
    # the boundary tolerance absorbs the discrepancy, so mutating only the reduce is a no-op. Either half of
    # the fix suffices on its own, which means the mutation that reproduces the bug has to remove BOTH -
    # exactly the shape the code had when the reviewer found it.
    ("restore the shipped bug: separate reduce AND no tolerance",
     "        let target = total * fraction\n"
     "        let tolerance = total * 1e-9",
     "        let separateTotal = sorted.reduce(0.0) { $0 + $1.length }\n"
     "        let target = separateTotal * fraction\n"
     "        let tolerance = 0.0"),

    ("drop the boundary tolerance",
     "        let tolerance = total * 1e-9",
     "        let tolerance = 0.0"),

    ("percentile by index instead of by length",
     "        var running: [Double] = []",
     "        return sorted[min(sorted.count - 1, Int(fraction * Double(sorted.count)))].score\n"
     "        var running: [Double] = []"),

    # --- numeric constants. A reviewer on T-0116 pointed out that every mutation in that harness was
    # --- structural and not one touched a number, which is exactly where such a suite is blind.
    ("use the seventieth percentile instead of the ninetieth",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.90)",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.70)"),

    ("move the dud threshold from 0.25 to 0.05",
     "public static let dudThreshold = 0.25",
     "public static let dudThreshold = 0.05"),

    ("halve the episode minimum length",
     "public static let episodeMinLength = 800.0",
     "public static let episodeMinLength = 400.0"),

    ("shift the episode threshold to 0.4",
     "public static let episodeThreshold = 0.6",
     "public static let episodeThreshold = 0.4"),

    ("reweight the mean and the p90",
     "public static let meanWeight = 0.60",
     "public static let meanWeight = 0.40"),

    ("move the honest-failure threshold so nothing is ever an honest failure",
     "public static let honestFailureThreshold = 0.45",
     "public static let honestFailureThreshold = 0.01"),

    # --- threshold strictness, which was stated only in doc comments ---------------------------------
    ("make the episode threshold non-strict, so a flat 0.6 becomes an episode",
     "            if e.score > episodeThreshold {",
     "            if e.score >= episodeThreshold {"),

    ("make the dud threshold strict, so a score of exactly 0.25 stops being a dud",
     "let dud = edges.filter { $0.score <= Self.dudThreshold }",
     "let dud = edges.filter { $0.score < Self.dudThreshold }"),

    ("require a run to EXCEED the episode minimum rather than reach it",
     "                if run >= episodeMinLength { count += 1 }",
     "                if run > episodeMinLength { count += 1 }"),
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
