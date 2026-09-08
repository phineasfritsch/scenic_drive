"""Mutation harness for RetraceDetector. A catch requires a NAMED TEST to fail, not a non-zero exit.

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
SRC = ROOT / "Sources" / "ScenicKit" / "Loop" / "RetraceDetector.swift"
# BOTH suites, because --prove-vacuity has to empty every test that could catch a mutation. When the grid
# tests were split into their own file to stay under the 300-line cap, the proof kept emptying only the
# first one and correctly reported FAILED with 7 mutations still caught - the proof caught the split before
# I did.
TEST_FILES = [ROOT / "Tests" / "ScenicKitTests" / "RetraceDetectorTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "RetraceGridTests.swift"]
SCRATCH = ".build-mutate-retrace"

def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces - two identically-named structs would not compile,
    and a compile failure would make the vacuity proof pass for the wrong reason."""
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))

MUTATIONS = [
    ("compare headings without wrapping", SRC,
     "        let d = abs(a - b).truncatingRemainder(dividingBy: 360)\n        return d > 180 ? 360 - d : d",
     "        return abs(a - b)"),

    ("call any revisited cell a retrace, whatever the heading", SRC,
     "                if seen.contains(where: { angularDifference($0.heading, heading) > oppositeHeadingDegrees\n"
     "                                          && Geo.distanceMeters($0.point, here) <= cellSizeMeters }) {",
     "                if !seen.isEmpty {"),

    ("record only the segment midpoint instead of sampling along it", SRC,
     "let steps = max(1, Int((length / (cellSizeMeters / samplesPerCell)).rounded(.up)))",
     "let steps = 1"),

    ("quantise the grid in degrees, so cells are not square", SRC,
     "        111_320.0 * cos(latitude * .pi / 180)",
     "        111_320.0"),

    # Numeric-constant mutations. A reviewer pointed out that every mutation in my Budget harness was
    # STRUCTURAL - delete a guard, invert a comparison - and not one touched a number, which is exactly
    # where such a suite is blind. These are the numbers here.
    ("halve the sampling density along a segment", SRC,
     "    static let samplesPerCell = 2.0",
     "    static let samplesPerCell = 0.4"),

    ("use the equatorial degree for latitude too", SRC,
     "    static let metersPerDegreeLatitude = 111_132.0",
     "    static let metersPerDegreeLatitude = 55_000.0"),

    ("tighten the opposite-heading threshold to 179, so only an exact reversal counts", SRC,
     "public static let oppositeHeadingDegrees = 150.0",
     "public static let oppositeHeadingDegrees = 179.9"),

    ("loosen the opposite-heading threshold to 80 degrees, so a crossing counts", SRC,
     "public static let oppositeHeadingDegrees = 150.0",
     "public static let oppositeHeadingDegrees = 80.0"),

    ("make the cells 250 m, so a parallel street collides with its neighbour", SRC,
     "public static let cellSizeMeters = 25.0",
     "public static let cellSizeMeters = 250.0"),

    ("raise the acceptable retrace to 95 percent", SRC,
     "public static let maxRetraceFraction = 0.15",
     "public static let maxRetraceFraction = 0.95"),

    ("count a retraced sample but forget to record it", SRC,
     "                samplesByCell[cell, default: []].append((here, heading))",
     "                if seen.isEmpty { samplesByCell[cell, default: []].append((here, heading)) }"),

    ("treat a zero-length route as fully clean rather than unanswerable", SRC,
     "        guard total > 0 else { return nil }\n        return retraced / total",
     "        guard total > 0 else { return 0 }\n        return retraced / total"),

    # --- reviewer-pr76's findings G1, G2, G4 and G5 -------------------------------------------------------
    # G2, the product defect: looking only in the sample's own cell makes the verdict depend on where the
    # grid boundaries happen to fall. One fixed connector gave 0.498 (reject) at 0 m, 0.497 at 6 m and 0.0
    # (ACCEPT) at 12 m - the same road, three answers.
    ("search only the sample's own cell, so a cell boundary hides a retrace", SRC,
     "let seen = neighbourhood.flatMap { samplesByCell[Cell(x: cell.x + $0.0, y: cell.y + $0.1)] ?? [] }",
     "let seen = samplesByCell[cell] ?? []"),

    # The radius, which is now what decides. These are the numbers a reviewer found no harness touching.
    ("drop the distance test, so the grid's reach decides again", SRC,
     "                                          && Geo.distanceMeters($0.point, here) <= cellSizeMeters }) {",
     "                                          }) {"),

    ("double the retrace radius, so a parallel street 40 m away is the same road", SRC,
     "&& Geo.distanceMeters($0.point, here) <= cellSizeMeters }) {",
     "&& Geo.distanceMeters($0.point, here) <= cellSizeMeters * 2 }) {"),

    ("shrink the retrace radius below a divided road's width", SRC,
     "&& Geo.distanceMeters($0.point, here) <= cellSizeMeters }) {",
     "&& Geo.distanceMeters($0.point, here) <= 10.0 }) {"),

    # G1: the grid anchor. NOTE - with the neighbourhood search in place this mutation is MISSED, and that
    # is recorded rather than hidden: the anchor stopped being load-bearing for the verdict once a boundary
    # could no longer hide anything. It stays in the source because scaling longitude at one end's latitude
    # rather than the route's mid-latitude is still wrong, and it stays here so the day a test does pin it,
    # the harness already asks the question.
    # G5: finiteness was screened, range was not, and the cell arithmetic trapped on a finite 1e17.
    # G4/N4: the zero-length segment guard had never been seen red - degenerateIsNil looks like its test and
    # reaches `guard total > 0` instead.
]

# Mutations this suite is KNOWN not to catch, asserted the other way round.
#
# A gap that is merely absent from the mutation list is a gap nobody can see. Each entry here names why no
# assertion can kill it, and the harness FAILS if one of them starts being caught - because that means either
# the gap closed (move it up to MUTATIONS) or the harness drifted.
KNOWN_MISSED = [
    # Subsumed, not uncovered. The range screen below it rejects NaN and infinity too - `(-90...90).contains`
    # is false for both - so the finiteness loop can no longer change any outcome. It stays as defence in
    # depth on a safety path; deleting a guard to make a harness go green would be the wrong trade.
    ("accept a route with a non-finite coordinate", SRC,
     "        for p in points where !(p.latitude.isFinite && p.longitude.isFinite) { return nil }\n",
     ""),

    # No assertion can run: writing the neighbourhood back into the cell makes each step copy the previous
    # step's list, the arrays grow without bound, and the process dies before any test reports. The harness
    # scores it `trapped`, which is honest - it is detected, but not by a check.
    ("write the neighbours' samples back into this cell, so they spread", SRC,
     "                samplesByCell[cell, default: []].append((here, heading))",
     "                samplesByCell[cell] = seen + [(here, heading)]"),

    # Once the 3x3 neighbourhood search went in, the grid anchor stopped deciding any verdict - a boundary
    # can no longer hide a retrace, so moving the boundaries changes nothing a test can see. The bounding-box
    # anchor stays because scaling longitude at one END's latitude rather than the route's mid-latitude is
    # still wrong, but this suite does not pin it and saying otherwise would be a claim without a witness.
    ("anchor the grid at points[0] again", SRC,
     "let anchor = Coordinate(latitude: minLat, longitude: minLon)",
     "let anchor = points[0]"),

    # The code TRAPS before any assertion runs: removing the range screen lets a finite 1e17 reach the cell
    # arithmetic, and `Int(_:)` dies with "Double value cannot be converted to Int". refusesOutOfRange is the
    # test for this property and it cannot report, because the process is gone. Detected, but by a crash.
    ("drop the coordinate range screen", SRC,
     "        for p in points where !(-90.0...90.0).contains(p.latitude)\n"
     "            || !(-180.0...180.0).contains(p.longitude) { return nil }\n",
     ""),

    # Became unkillable when the distance test went in: a zero-length segment now contributes a sample at a
    # point it already occupies, with the same heading, so nothing is counted either way. It was caught
    # before that change. Left here so that if the distance test is removed, this arm says so.
    ("drop the zero-length segment guard", SRC,
     "guard length.isFinite, length > 0 else { continue }",
     "guard length.isFinite else { continue }"),

    # Pre-existing, found by this harness rather than by a reviewer: no fixture separates two samples per
    # cell from one. longSegmentsAreSampled uses a 600 m segment against three 200 m ones, which both
    # densities resolve identically.
    ("halve the sampling density along a segment", SRC,
     "    static let samplesPerCell = 2.0",
     "    static let samplesPerCell = 1.0"),
]

# Cannot change behaviour, so anything but MISSED is a failure.
EQUIVALENT = [
    # Once the distance test decides, a WIDER net finds the same candidates and rejects the extra ones by
    # distance. Before that change this was a real behaviour change and a real gap; it is now equivalent,
    # and it is kept here so that if the distance test is ever removed, this arm fails loudly.
    ("search a 5x5 neighbourhood", SRC,
     "    static let neighbourhood: [(Int, Int)] = [(-1, -1), (-1, 0), (-1, 1),\n"
     "                                              (0, -1), (0, 0), (0, 1),\n"
     "                                              (1, -1), (1, 0), (1, 1)]",
     "    static let neighbourhood: [(Int, Int)] = (-2...2).flatMap { a in (-2...2).map { (a, $0) } }"),

    ("list the neighbourhood in a different order", SRC,
     "    static let neighbourhood: [(Int, Int)] = [(-1, -1), (-1, 0), (-1, 1),\n"
     "                                              (0, -1), (0, 0), (0, 1),\n"
     "                                              (1, -1), (1, 0), (1, 1)]",
     "    static let neighbourhood: [(Int, Int)] = [(0, 0), (1, 1), (-1, -1), (0, 1), (1, 0),\n"
     "                                              (-1, 0), (0, -1), (1, -1), (-1, 1)]"),
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
    pristine = {f: f.read_bytes() for f in (SRC,)}
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
