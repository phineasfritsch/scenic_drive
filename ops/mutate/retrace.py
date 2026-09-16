"""Mutation harness for RetraceDetector. A catch requires a NAMED TEST to fail, not a non-zero exit.

Tracked in ops/ rather than .artifacts/, because .artifacts/ is gitignored and a task whose `acceptance:`
line names a file nobody else can run has no reproducible red evidence. Each mutation is built first: a
mutation that does not compile is reported `compile-only` and does not count, since a compiler error is a
fact about Swift and not about this suite.

Run `--prove-vacuity` to check the harness itself: it replaces the test file with an empty suite and
requires every mutation to report MISSED. A harness that still reports catches with no tests present is
measuring the compiler.

The subject and every test file must match `git show HEAD:` before anything is built. That is why the run
REFUSES while you have uncommitted work in them: a sibling harness in this repository measured a file that
was ALREADY mutated, printed "34 of 34 caught", exited 0, and restored the mutant. Commit first, then
measure - a number that describes a tree nobody else can check out is not evidence.
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
              ROOT / "Tests" / "ScenicKitTests" / "RetraceGridTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "RetraceIndexTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "RetraceDiagonalTests.swift"]
# Kept honest by grep, not by memory: `git grep -l Retrace -- Tests/` must list exactly these four files.
# Any other file that mentions RetraceDetector could catch a mutation, and the vacuity proof would then be
# emptying less than the suite.
#
# These files share ONE probe - RetraceDiagonalTests calls RetraceIndexTests.point, so that "place a point
# N true metres away by bisecting on the decider" has a single definition rather than two that can drift.
# The consequence for this list is worth knowing before you debug it: emptying RetraceIndexTests.swift while
# leaving RetraceDiagonalTests.swift in place does not compile, so dropping the diagonal file from TEST_FILES
# makes --prove-vacuity report "baseline does not build" and exit 2. Nothing reads as green either way -
# measured both directions, in the task log - but the message you get names the build, not the omission.
SCRATCH = ".build-mutate-retrace"

def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces - two identically-named structs would not compile,
    and a compile failure would make the vacuity proof pass for the wrong reason."""
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))

# Floors on the HARNESS's own population. reviewer-pr76 emptied the three lists and got
# "caught by a named test: 0 of 0 ... exit 0" and "VACUITY PROOF OK ... MISSED=0 of 0" - a clean bill of
# health over nothing examined. ops/lib/check-exec-bits (MIN_FILES = 17) and ops/lib/check-line-cap
# (MIN_FILES = 5) both carry this guard, and their headers say it is because this repository has already
# shipped that defect twice.
#
# MIN_MUTATIONS IS THE REAL COUNT, not a round number below it. At 16 against a population of 21 this floor refused an empty
# list but NOT a deletion - five mutations could be dropped and it still read as a clean sheet, which is the
# exact failure the floor was added to prevent. The reviewer of PR #82 demonstrated that on a sibling by
# deleting both motorway mutations and getting "18 of 18 ... exit 0". Adding a mutation means bumping this.
#
# EVERY arm carries its own floor, and each floor is the REAL count. reviewer-sg-pr76 deleted one of the two
# EQUIVALENT mutants against `MIN_EQUIVALENT = 1` and the run sailed past the check into the baseline; then
# emptied KNOWN_MISSED, which had no floor at all, and got `caught by a named test: 1 of 1 ... MISSED 0`,
# exit 0 - a clean sheet with all four recorded gaps deleted. `known_ok` was comparing 0 == 0. An arm that
# exists so a gap is not invisible must not be silently deletable.
MIN_MUTATIONS = 25
MIN_EQUIVALENT = 2
MIN_KNOWN_MISSED = 7

MUTATIONS = [
    ("compare headings without wrapping", SRC,
     "        let d = abs(a - b).truncatingRemainder(dividingBy: 360)\n        return d > 180 ? 360 - d : d",
     "        return abs(a - b)"),

    ("call any revisited cell a retrace, whatever the heading", SRC,
     "                if seen.contains(where: { angularDifference($0.heading, heading) > oppositeHeadingDegrees\n"
     "                                          && Geo.distanceMeters($0.point, here) <= retraceRadiusMeters }) {",
     "                if !seen.isEmpty {"),

    ("record only the segment midpoint instead of sampling along it", SRC,
     "let steps = max(1, Int((length / (retraceRadiusMeters / samplesPerCell)).rounded(.up)))",
     "let steps = 1"),

    ("quantise the grid in degrees, so cells are not square", SRC,
     "        111_320.0 * cos(latitude * .pi / 180)",
     "        111_320.0"),

    # Numeric-constant mutations. A reviewer pointed out that every mutation in my Budget harness was
    # STRUCTURAL - delete a guard, invert a comparison - and not one touched a number, which is exactly
    # where such a suite is blind. These are the numbers here.
    #
    # EVERY NAME IN THIS LIST MUST DESCRIBE THE EDIT BESIDE IT. reviewer-fn-pr76 found two that did not, and
    # the cost is not cosmetic: the acceptance evidence is "23 of 23 caught BY NAME", so a name that
    # describes a change the harness never applied certifies a catch that never happened. The first of the
    # two below said "halve" while applying 2.0 -> 0.4 (a fifth), under the SAME NAME as the real halving in
    # KNOWN_MISSED - so one run printed that string twice, once as `caught` and once as `MISSED`.
    ("cut the sampling density to a fifth along a segment", SRC,
     "    static let samplesPerCell = 2.0",
     "    static let samplesPerCell = 0.4"),

    # The second: this said "use the equatorial degree for latitude too" while applying 55_000.0, which is
    # not the equatorial degree (111_320.0) or any other degree - it is a caricature, and it is caught. The
    # slip the old name described, 111_132.0 -> 111_320.0, SURVIVES the whole suite and is recorded in
    # KNOWN_MISSED where a gap belongs.
    ("halve the latitude metre, so grid rows cover twice the ground", SRC,
     "    static let metersPerDegreeLatitude = 111_132.0",
     "    static let metersPerDegreeLatitude = 55_000.0"),

    ("tighten the opposite-heading threshold to 179, so only an exact reversal counts", SRC,
     "public static let oppositeHeadingDegrees = 150.0",
     "public static let oppositeHeadingDegrees = 179.9"),

    ("loosen the opposite-heading threshold to 80 degrees, so a crossing counts", SRC,
     "public static let oppositeHeadingDegrees = 150.0",
     "public static let oppositeHeadingDegrees = 80.0"),

    ("widen the retrace radius to 250 m, so a parallel street is the same road", SRC,
     "public static let retraceRadiusMeters = 25.0",
     "public static let retraceRadiusMeters = 250.0"),

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
     "                                          && Geo.distanceMeters($0.point, here) <= retraceRadiusMeters }) {",
     "                                          }) {"),

    ("double the retrace radius, so a parallel street 40 m away is the same road", SRC,
     "&& Geo.distanceMeters($0.point, here) <= retraceRadiusMeters }) {",
     "&& Geo.distanceMeters($0.point, here) <= retraceRadiusMeters * 2 }) {"),

    ("shrink the retrace radius below a divided road's width", SRC,
     "&& Geo.distanceMeters($0.point, here) <= retraceRadiusMeters }) {",
     "&& Geo.distanceMeters($0.point, here) <= 10.0 }) {"),

    # G1: the grid anchor. NOTE - with the neighbourhood search in place this mutation is MISSED, and that
    # is recorded rather than hidden: the anchor stopped being load-bearing for the verdict once a boundary
    # could no longer hide anything. It stays in the source because scaling longitude at one end's latitude
    # rather than the route's mid-latitude is still wrong, and it stays here so the day a test does pin it,
    # the harness already asks the question.
    # G5: finiteness was screened, range was not, and the cell arithmetic trapped on a finite 1e17.
    # G4/N4: the zero-length segment guard had never been seen red - degenerateIsNil looks like its test and
    # reaches `guard total > 0` instead.

    # reviewer-pr76's F2a and F2b. Both of these sat in KNOWN_MISSED with a reason that measurement showed to
    # be FALSE - the arm was recording closable gaps as facts, which is the thing that arm is most dangerous
    # for. They are ordinary mutations now, each with a named test.
    #
    # F2a: the stated reason was that a zero-length segment "contributes a sample at a point it already
    # occupies, with the same heading". Geo.initialBearingDegrees(from: a, to: a) is 0.0, not the segment's
    # heading, so a repeated coordinate plants a due-north sample on a southbound road.
    ("drop the zero-length segment guard", SRC,
     "guard length.isFinite, length > 0 else { continue }",
     "guard length.isFinite else { continue }"),

    # F2b: the stated reason was that the test "cannot report, because the process is gone". True only
    # because the 1e17 case shared a @Test with the ordinary out-of-range cases and trapped before they ran.
    # Splitting them made this killable, which it always was.
    ("drop the coordinate range screen", SRC,
     "        for p in points where !(-90.0...90.0).contains(p.latitude)\n"
     "            || !(-180.0...180.0).contains(p.longitude) { return nil }\n",
     ""),

    # F5-prior: the opposite-heading threshold was bracketed at 80 and 179.9 and nowhere between, so a shift
    # to 105 degrees survived - present in neither MUTATIONS nor KNOWN_MISSED, which is exactly what that
    # arm's own header says must not happen.
    ("relax the opposite-heading threshold to 105 degrees, so a switchback counts as a retrace", SRC,
     "public static let oppositeHeadingDegrees = 150.0",
     "public static let oppositeHeadingDegrees = 105.0"),

    # F1: the index cell must exceed the retrace radius, or a pair inside the radius can land two cells apart
    # and escape the 3x3 search. This is the defect reviewer-pr76 measured at a 24.99 m separation.
    ("shrink the index cell back to the retrace radius", SRC,
     "    static let indexCellMeters = 2 * retraceRadiusMeters",
     "    static let indexCellMeters = retraceRadiusMeters"),

    ("give the index cell too little margin for the scale error", SRC,
     "    static let indexCellMeters = 2 * retraceRadiusMeters",
     "    static let indexCellMeters = 1.002 * retraceRadiusMeters"),

    # reviewer-sg-pr76's B1. The FOUR CORNERS of the 3x3 index had no witness anywhere - not in the suite,
    # not here, not in KNOWN_MISSED, not in EQUIVALENT - and they are the only part of the neighbourhood
    # that is load-bearing for a road which is not due north or due east. A pair separated along an axis
    # differs on ONE cell axis; only a diagonal separation differs on both at once, and no fixture here ever
    # separated a pair inside the radius along a diagonal - so the plus below passed all 41 tests at exit 0
    # while a divided road on bearing 045 lost up to a third of its retrace, at some grid phases and not
    # others.
    ("shrink the neighbourhood to a plus, dropping the four diagonal cells", SRC,
     "    static let neighbourhood: [(Int, Int)] = [(-1, -1), (-1, 0), (-1, 1),\n"
     "                                              (0, -1), (0, 0), (0, 1),\n"
     "                                              (1, -1), (1, 0), (1, 1)]",
     "    static let neighbourhood: [(Int, Int)] = [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]"),

    # And one corner, because a suite can pin "nine cells" without pinning WHICH nine - counting is not
    # covering. This one is caught only by the index test, and it names the cell: "a pair 25.0 m apart on
    # bearing 75 landed at cell offset (1, 1), which the index does not search".
    ("drop ONE diagonal cell from the neighbourhood", SRC,
     "    static let neighbourhood: [(Int, Int)] = [(-1, -1), (-1, 0), (-1, 1),\n"
     "                                              (0, -1), (0, 0), (0, 1),\n"
     "                                              (1, -1), (1, 0), (1, 1)]",
     "    static let neighbourhood: [(Int, Int)] = [(-1, -1), (-1, 0), (-1, 1),\n"
     "                                              (0, -1), (0, 0), (0, 1),\n"
     "                                              (1, -1), (1, 0)]"),

    # reviewer-fn-pr76's N3 and finding 5. Both of these survived the entire suite at exit 0 with zero
    # failing test names while being real behaviour flips, and both were in neither MUTATIONS nor
    # KNOWN_MISSED - which is the state that arm's own header says must not exist.
    #
    # The threshold: `<=` is the product decision (the plan's property table says "<= 0.15") and the test
    # named for it asserted `0.15 <= maxRetraceFraction`, a restatement of the line above it. No route
    # fixture can close this - no geometry here yields a fraction of exactly 0.15 - so the subject now
    # exposes `isAcceptable(fraction:)` and the boundary is asserted on the predicate itself.
    ("accept only strictly below the threshold, so exactly 15 percent is refused", SRC,
     "    static func isAcceptable(fraction f: Double) -> Bool {\n        f <= maxRetraceFraction\n    }",
     "    static func isAcceptable(fraction f: Double) -> Bool {\n        f < maxRetraceFraction\n    }"),

    # The arity guard: `degenerateIsNil` asks about ONE point and about two IDENTICAL ones, which reaches
    # the zero-length guard, not this one. A two-point route goes from Optional(0.0)/acceptable to
    # nil/not-acceptable under this change, and nothing objected.
    ("refuse a two-point route, so the shortest real segment is unanswerable", SRC,
     "        guard points.count >= 2 else { return nil }",
     "        guard points.count >= 3 else { return nil }"),
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

    # TWO FALSE REASONS USED TO STAND HERE, and they are struck rather than moved again. reviewer-fn-pr76's
    # finding 2: when the two entries they belonged to - "drop the coordinate range screen" and "drop the
    # zero-length segment guard" - were promoted into MUTATIONS in ffdb8f9, the ENTRIES moved and the
    # COMMENTS did not, so they were left reading as the justification for the gap below them. Both were
    # already measured FALSE in the 2026-09-09 Log, and both describe mutations this suite demonstrably
    # KILLS: every run prints `caught  drop the coordinate range screen` and `caught  drop the zero-length
    # segment guard`. The sentences were "refusesOutOfRange ... cannot report, because the process is gone"
    # and "a zero-length segment now contributes a sample at a point it already occupies, with the same
    # heading" - the second is false because `Geo.initialBearingDegrees(from: a, to: a)` is 0.0, which is
    # what made it killable in the first place. Neither has anything to do with sampling density.
    #
    # The real reason for THIS gap, measured and not inherited: nothing in the suite has an opinion about
    # the density. Halving it leaves the whole suite green - exit 0, zero failing test names - because every
    # fixture that samples a long segment is asserted against a band far wider than the shift. The closest
    # thing to a witness is `longSegmentsAreSampled`, and its 600 m leg against three 200 m ones is resolved
    # the same way at 24 samples as at 48. Closing it needs a fixture built so that ONE cell is crossed
    # between consecutive samples at 1.0 and not at 2.0, which is a different fixture from any here.
    ("halve the sampling density along a segment", SRC,
     "    static let samplesPerCell = 2.0",
     "    static let samplesPerCell = 1.0"),

    # reviewer-fn-pr76's finding 4(b): the slip the MUTATIONS entry above USED to be named for. 111_320.0 is
    # the equatorial degree and a plausible copy-paste from `metersPerDegreeLongitude` two declarations
    # away, so it is the realistic version of that mistake - and it survives. It is verdict-neutral under
    # the 2x margin rather than harmless in principle: a north-south pair a radius apart reads as 0.500561
    # cells instead of 0.499716, still under one, so the guarantee holds and no assertion moves. What it
    # would break is the ASYMMETRY RetraceDetector.swift's own documentation rests on ("Only the EAST axis
    # can break it"), and nothing witnesses that - which is why it is recorded here rather than left out.
    ("use the equatorial degree for latitude too", SRC,
     "    static let metersPerDegreeLatitude = 111_132.0",
     "    static let metersPerDegreeLatitude = 111_320.0"),

    # reviewer-fn-pr76's finding 5, and G4 from the first review round. Scaling longitude at the route's
    # SOUTHERN end instead of its mid-latitude is wrong in principle, and measurably invisible here: the
    # longest fixture in this suite is a 1.95 km north-south leg, over which the two scales differ by
    # 0.01035%, moving a 25 m pair by 0.0000429 of a cell. There is no fixture, and no fixture of a sane
    # size, that turns that into a different cell index across the 2x margin. The sibling of "anchor the
    # grid at points[0] again" above: both are properties of the grid that stopped deciding any verdict
    # once the distance test became the measurement.
    ("scale longitude at the route's southern end, not its mid-latitude", SRC,
     "        let mPerLon = metersPerDegreeLongitude(at: (minLat + maxLat) / 2)",
     "        let mPerLon = metersPerDegreeLongitude(at: minLat)"),

    # reviewer-fn-pr76's finding 5. Sampling at the segment's START rather than its midpoint shifts every
    # sample by half a step - a real change, and one no fixture separates, because each of them is asserted
    # against a band wider than half a sample. The reviewer explicitly declined to call it a defect and so
    # do I: it is an untested shift, recorded so it is not invisible.
    ("sample at the start of each step instead of its midpoint", SRC,
     "                let t = (Double(i) + 0.5) / Double(steps)",
     "                let t = Double(i) / Double(steps)"),
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


def head_blob(path: pathlib.Path) -> bytes | None:
    """The committed bytes of `path`, or None if git cannot produce them."""
    rel = path.relative_to(ROOT).as_posix()
    p = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def refuse_if_not_head(paths) -> str | None:
    """The reason to refuse, or None. Checked BEFORE any build, because a harness that measures a file
    somebody already edited reports on a tree that does not exist anywhere else.

    The harness does NOT certify itself this way. A modified retrace.py could delete this function, and the
    reviewer's technique - import the module and override its globals in memory - never touches the file at
    all. What this closes is the accident: a mutant left on disk by a killed run, or an uncommitted edit to
    the subject, being measured and reported as a score."""
    for f in paths:
        head = head_blob(f)
        if head is None:
            return "%s: git show HEAD:%s failed - refusing to measure an unverifiable tree" % (
                f.name, f.relative_to(ROOT).as_posix())
        if f.read_bytes() != head:
            return ("%s differs from git show HEAD:%s\n"
                    "  on disk %s   committed %s" % (f.name, f.relative_to(ROOT).as_posix(),
                                                     hashlib.md5(f.read_bytes()).hexdigest(),
                                                     hashlib.md5(head).hexdigest()))
    return None


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
    if (len(MUTATIONS) < MIN_MUTATIONS or len(EQUIVALENT) < MIN_EQUIVALENT
            or len(KNOWN_MISSED) < MIN_KNOWN_MISSED):
        sys.stdout.write("REFUSING: %d mutations, %d equivalent mutants and %d known gaps, expected at "
                         "least %d, %d and %d.\n"
                         "A harness that examines nothing exits 0 and proves nothing.\n"
                         % (len(MUTATIONS), len(EQUIVALENT), len(KNOWN_MISSED),
                            MIN_MUTATIONS, MIN_EQUIVALENT, MIN_KNOWN_MISSED))
        return 2
    stale = refuse_if_not_head([SRC] + TEST_FILES)
    if stale is not None:
        sys.stdout.write("REFUSING: %s\n"
                         "A harness that measures an edited tree reports a number nobody can reproduce, and\n"
                         "a sibling here measured an already-mutated file, printed '34 of 34 caught' and\n"
                         "restored the mutant. Commit, then measure.\n" % stale)
        return 2
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

        # Built TWICE before the baseline is declared broken, exactly as each mutation build already is.
        # On this Windows checkout a first build into a fresh scratch directory can fail with "unable to
        # create symbolic link ... I/O error (code: 512)" and succeed immediately after; a single attempt
        # turns that into "baseline does not build" with nothing measured. T-0132's second defect.
        if build() != 0 and build() != 0:
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

    # Against HEAD, not against the bytes read at the start: those two agree only because the run REFUSED
    # unless they did, and re-deriving the comparison from git is what makes "restored" mean the committed
    # file rather than whatever this process happened to load.
    left_dirty = refuse_if_not_head([SRC] + TEST_FILES)
    if left_dirty is not None:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine: %s\n" % left_dirty)
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
