"""Mutation harness for RouteScore. A catch requires a NAMED TEST to fail, not a non-zero exit.

Tracked in ops/ rather than .artifacts/, because .artifacts/ is gitignored and a task whose `acceptance:`
line names a file nobody else can run has no reproducible red evidence. Each mutation is built first: a
mutation that does not compile is reported `compile-only` and does not count, since a compiler error is a
fact about Swift and not about this suite.

THE PASS CONDITION IS `caught == len(MUTATIONS)`, full stop. It used to be
`caught + len(trapped) == len(MUTATIONS)`, which counted a crash as a pass while the docstring three lines
above said a crash is not a catch. That was filed against every harness in this repository (BLOCKING 6 on
PR #70) and demonstrated: break a harness's own FAIL_LINE regex with the subject pristine and every mutation
scores `trapped` and the run exits 0, so the harness cannot tell "the subject is covered" from "I am
broken". The corrected shape is ops/mutate/guidance.py on task/T-0129, and this file follows it:

  * a trap, a compile failure and a stale anchor each fail the run;
  * SKIP is its own bucket, never folded into MISSED - a mutation that did not land says the harness is
    stale, which is the opposite of what MISSED says;
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`. Requiring only `caught == 0`
    let a reviewer replace all 21 anchors with strings absent from the source and still print
    "VACUITY PROOF OK", because a mutation that never landed is indistinguishable from one that landed and
    was correctly not caught;
  * the EQUIVALENT arm requires its mutants to go MISSED specifically, not merely "not caught".
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "ScenicKit" / "Scoring" / "RouteScore.swift"
TESTS = (ROOT / "Tests" / "ScenicKitTests" / "RouteScoreTests.swift",
         ROOT / "Tests" / "ScenicKitTests" / "RouteScoreBoundaryTests.swift")
SCRATCH = ".build-mutate-routescore"

EMPTY_SUITE = ('import Testing\n'
               '@Suite("empty %(n)s") struct Empty%(n)sSuite {\n'
               '    @Test("nothing %(n)s") func nothing() { #expect(true) }\n'
               '}\n')

# The two places a run can be closed. Both need their own anchor, and both anchors carry the line ABOVE
# them: "        if run >= episodeMinLength - tolerance { count += 1 }" is a substring of the indented
# in-loop copy, so an 8-space anchor would silently mutate the wrong one.
EPISODE_INLOOP = ("            } else {\n"
                  "                if run >= episodeMinLength - tolerance { count += 1 }")
EPISODE_ATEND = ("        }\n"
                 "        if run >= episodeMinLength - tolerance { count += 1 }\n"
                 "        return count")

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
     EPISODE_ATEND, "        }\n        return count"),

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

    # --- the percentile, where the first shipped bug was ---------------------------------------------
    ("sort the percentile the other way, turning p90 into p10",
     "let sorted = edges.sorted { $0.score < $1.score }",
     "let sorted = edges.sorted { $0.score > $1.score }"),

    # The shipped regression, restored. It used to be listed as two mutations - "separate reduce AND no
    # tolerance" and "drop the tolerance" - under a comment claiming "either half of the fix suffices on
    # its own". A reviewer measured that claim and found it inverted, and measuring it again the other way
    # says why: `sorted.reduce { $0 + $1.length }` is a left fold over the same sequence, in the same
    # order, as the loop's own `cumulative`, so the two totals are bit-identical for every input (worst
    # difference over the fixture at k = 1...400: exactly 0.0). The separate reduce was never a defect and
    # never part of the fix. Dropping the tolerance IS the shipped bug, and there is one mutation for it.
    # The equivalence is not left as a claim either: it is EQUIVALENT[1] below, and the run fails if it is
    # ever caught.
    ("restore the shipped bug: drop the percentile boundary tolerance",
     "        let tolerance = total * Self.boundaryTolerance",
     "        let tolerance = 0.0"),

    ("flip the percentile boundary tolerance to the wrong side",
     "        for (i, c) in running.enumerated() where c >= target - tolerance {",
     "        for (i, c) in running.enumerated() where c >= target + tolerance {"),

    ("percentile by index instead of by length",
     "        var running: [Double] = []",
     "        return sorted[min(sorted.count - 1, Int(fraction * Double(sorted.count)))].score\n"
     "        var running: [Double] = []"),

    # --- numeric constants. A reviewer on T-0116 pointed out that every mutation in that harness was
    # --- structural and not one touched a number, which is exactly where such a suite is blind.
    ("use the seventieth percentile instead of the ninetieth",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.90)",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.70)"),

    # 0.89 and 0.91 are the two that matter: the suite used to pin the fraction only to (0.85, 0.90], so a
    # reviewer moved it to 0.86 and to 0.89 with every assertion green.
    ("use the eighty-ninth percentile instead of the ninetieth",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.90)",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.89)"),

    ("use the ninety-first percentile instead of the ninetieth",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.90)",
     "let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.91)"),

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

    ("widen the shared boundary tolerance to 4% of route length",
     "public static let boundaryTolerance = 1e-9",
     "public static let boundaryTolerance = 0.04"),

    ("raise the episode target from three to five",
     "public static let episodeTarget = 3.0",
     "public static let episodeTarget = 5.0"),

    ("drop the cap, so a route with eight episodes keeps being paid for them",
     "+ Self.episodeWeight * min(1.0, Double(episodes) / Self.episodeTarget)",
     "+ Self.episodeWeight * (Double(episodes) / Self.episodeTarget)"),

    # --- threshold strictness, which was stated only in doc comments ---------------------------------
    ("make the episode threshold non-strict, so a flat 0.6 becomes an episode",
     "            if e.score > episodeThreshold {",
     "            if e.score >= episodeThreshold {"),

    ("make the dud threshold strict, so a score of exactly 0.25 stops being a dud",
     "let dud = edges.filter { $0.score <= Self.dudThreshold }",
     "let dud = edges.filter { $0.score < Self.dudThreshold }"),

    ("make isHonestFailure non-strict, so a route exactly on the threshold is refused",
     "public var isHonestFailure: Bool { value < Self.honestFailureThreshold }",
     "public var isHonestFailure: Bool { value <= Self.honestFailureThreshold }"),

    # --- the episode boundary, which is an ACCUMULATED length and had no tolerance at all ------------
    # Four mutations, because there are two closing sites and two ways to break each: remove the tolerance
    # (the shipped defect - an 800 m episode returned as k intervals is thrown away for 99 of the first
    # 200 k) and put it on the wrong side (which throws it away for every k).
    # There is deliberately NO `>=` -> `>` mutation here any more. It used to be caught, and with the
    # tolerance present it is unobservable: at a run of exactly 800 m both `>=` and `>` clear
    # `800 - tolerance`. Measured, not assumed - it went MISSED when tried. Keeping it would report a gap
    # that is not one; the four below cover the same boundary and more of it.
    ("drop the episode tolerance where a dull stretch closes the run",
     EPISODE_INLOOP,
     "            } else {\n                if run >= episodeMinLength { count += 1 }"),

    ("drop the episode tolerance where the route ends on the run",
     EPISODE_ATEND,
     "        }\n        if run >= episodeMinLength { count += 1 }\n        return count"),

    ("flip the episode tolerance to the wrong side, mid-route",
     EPISODE_INLOOP,
     "            } else {\n                if run >= episodeMinLength + tolerance { count += 1 }"),

    ("flip the episode tolerance to the wrong side, at the end of the route",
     EPISODE_ATEND,
     "        }\n        if run >= episodeMinLength + tolerance { count += 1 }\n        return count"),
]

# Cannot change behaviour, so a catch here is a FAILURE and anything other than MISSED is a failure too.
EQUIVALENT = [
    # raw <= 0.60*1 + 0.25*1 - 0.15*0 + 0.10*1 = 0.95, because ScoredEdge.isValid pins every score to
    # 0...1, so the upper half of the clamp is unreachable. It stays for the reader and because it goes
    # live the moment the episode cap changes; it is not test coverage and is not counted as any.
    ("drop the unreachable upper half of the clamp",
     "self.value = min(1.0, max(0.0, raw))",
     "self.value = max(0.0, raw)"),

    # The half of the F1 "fix" that never did anything. `reduce` is a left fold over `sorted` in the same
    # order as the loop that produced `cumulative`, so the two are bit-identical for every input. This is
    # the assertion that keeps the corrected story honest: if a future change ever makes the two totals
    # differ, this mutant starts being caught and the run fails, which is the right way to find out.
    ("take the percentile total from a separate reduce, as the shipped code did",
     "        let total = cumulative\n",
     "        let total = sorted.reduce(0.0) { $0 + $1.length }\n"),
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
    """A verdict per mutation. SKIP is its own bucket: a mutation that did not land means the harness is
    stale, which is the opposite of what MISSED means."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    text = pristine.decode("utf-8")
    for name, old, new in mutations:
        if old not in text:
            sys.stdout.write("SKIP        %-62s anchor not found - harness is stale\n" % name)
            out["skipped"].append(name)
            continue
        code = 0
        try:
            SRC.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if SRC.read_bytes() == pristine:
                sys.stdout.write("SKIP        %-62s mutation did not land\n" % name)
                out["skipped"].append(name)
                continue
            # Built twice before a compile failure is believed: other agents run swift builds on this box
            # concurrently and a transient scratch collision produced a false compile-only verdict once.
            if build() != 0 and build() != 0:
                verdict = "compile_only"
            else:
                code, txt = test()
                verdict = "caught" if FAIL_LINE.search(txt) else ("trapped" if code != 0 else "missed")
        finally:
            SRC.write_bytes(pristine)
        out[verdict].append(name)
        label = {"caught": "caught", "trapped": "trapped", "compile_only": "compile-only",
                 "missed": "MISSED"}
        note = {"caught": "exit=%d" % code,
                "trapped": "non-zero exit, but NO named test failed - does not count",
                "compile_only": "a fact about Swift, not about these tests - does not count",
                "missed": "exit=0  no test objected"}
        sys.stdout.write("%-12s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = SRC.read_bytes()
    pristine_tests = {f: f.read_bytes() for f in TESTS}
    sys.stdout.write("pristine %s md5 %s\n" % (SRC.name, hashlib.md5(pristine).hexdigest()))

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: both test files are replaced by empty suites, so every\n"
                             "mutation must report MISSED - not merely 'not caught'.\n")
            for i, f in enumerate(TESTS):
                f.write_text(EMPTY_SUITE % {"n": i}, encoding="utf-8", newline="\n")

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
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
    finally:
        SRC.write_bytes(pristine)
        for f, b in pristine_tests.items():
            f.write_bytes(b)

    if SRC.read_bytes() != pristine or any(f.read_bytes() != b for f, b in pristine_tests.items()):
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2

    sys.stdout.write("\nrestored, md5 %s\n" % hashlib.md5(SRC.read_bytes()).hexdigest())
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
                         "  (requiring MISSED to be COMPLETE, not just caught==0, is what stops a harness\n"
                         "   whose anchors have all gone stale from proving its own non-vacuity)\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1

    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has\n"
                         "  an opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
