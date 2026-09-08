#!/usr/bin/env python3
"""Mutation harness for the per-way scenic score. A catch requires a NAMED TEST to fail, not a non-zero exit.

Most mutations here move a NUMBER, because this is a file of thirteen weights and two exponents and a
structural-only mutation set would be blind exactly where it matters. A reviewer made that finding against an
earlier harness in this repository whose every mutation was structural.

The one that matters most is `arithmetic mean instead of geometric`. The plan chose the geometric mean to
keep a curvy industrial road apart from a straight redwood one, and the substitution is what a later agent
reaches for while tidying - it agrees with the real formula whenever M and E are close, which is most
fixtures.

Contract (see ops/mutate/gates.py, T-0132):
  * pass condition `caught == len(MUTATIONS)`; a trap, a compile failure and a stale anchor each FAIL;
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)` over EVERY test file that could
    catch a mutation, each replaced by an empty suite named after the file it stands in;
  * the EQUIVALENT arm requires MISSED specifically;
  * the BASELINE build is retried, like every mutation build - on this Windows checkout a first build into a
    fresh scratch directory can fail with an I/O 512 symlink error and succeed immediately after, which made
    a sibling harness announce "baseline does not build" having measured nothing.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCORE = ROOT / "Sources" / "ScenicKit" / "Scoring" / "SegmentScore.swift"
TERMS = ROOT / "Sources" / "ScenicKit" / "Scoring" / "SegmentTerms.swift"
SCRATCH = ".build-mutate-segmentscore"

TEST_FILES = [ROOT / "Tests" / "ScenicKitTests" / "SegmentScoreTests.swift"]


def empty_suite(path: pathlib.Path) -> str:
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))


MUTATIONS = [
    # --- THE MEAN -----------------------------------------------------------------------------------------
    ("arithmetic mean instead of geometric, the tidy-up the plan warns about", SCORE,
     "        var score = pow(m, driveExponent) * pow(e, sceneryExponent)",
     "        var score = driveExponent * m + sceneryExponent * e"),

    ("plain geometric mean, dropping the exponents entirely", SCORE,
     "        var score = pow(m, driveExponent) * pow(e, sceneryExponent)",
     "        var score = (m * e).squareRoot()"),

    ("multiply the two axes instead of taking a mean of them", SCORE,
     "        var score = pow(m, driveExponent) * pow(e, sceneryExponent)",
     "        var score = m * e"),

    # --- the exponents ------------------------------------------------------------------------------------
    # Expressed at the point of USE rather than by rewriting both declarations. The declarations are separated
    # by a doc comment, and CLAUDE.md forbids anchoring on a comment - an anchor that spans one goes stale the
    # moment somebody rewords it, which is how this mutation first scored SKIP.
    ("swap the exponents, making it a motorcycle product", SCORE,
     "        var score = pow(m, driveExponent) * pow(e, sceneryExponent)",
     "        var score = pow(m, sceneryExponent) * pow(e, driveExponent)"),

    ("nudge alpha from 0.35 to 0.40", SCORE,
     "    public static let driveExponent = 0.35", "    public static let driveExponent = 0.40"),

    ("exponents that no longer sum to one, so the score leaves 0...1", SCORE,
     "    public static let sceneryExponent = 0.65", "    public static let sceneryExponent = 0.75"),

    # --- M's weights --------------------------------------------------------------------------------------
    ("curvature stops dominating M", SCORE,
     "    public static let curvatureWeight = 0.45", "    public static let curvatureWeight = 0.15"),

    ("swap curvature and sinuosity weights", SCORE,
     "    public static let curvatureWeight = 0.45\n    public static let elevationGainWeight = 0.20\n"
     "    public static let speedFitWeight = 0.20\n    public static let sinuosityWeight = 0.15",
     "    public static let curvatureWeight = 0.15\n    public static let elevationGainWeight = 0.20\n"
     "    public static let speedFitWeight = 0.20\n    public static let sinuosityWeight = 0.45"),

    ("M's weights no longer sum to one", SCORE,
     "    public static let speedFitWeight = 0.20", "    public static let speedFitWeight = 0.25"),

    # --- E's weights --------------------------------------------------------------------------------------
    ("E's weights no longer sum to one", SCORE,
     "    public static let canopyWeight = 0.24", "    public static let canopyWeight = 0.34"),

    ("water and canopy weights swapped", SCORE,
     "    public static let canopyWeight = 0.24", "    public static let canopyWeight = 0.12"),

    # --- the inverted terms -------------------------------------------------------------------------------
    ("impervious ground counts FOR the score", SCORE,
     "            + openGroundWeight * (1 - t.impervious)", "            + openGroundWeight * t.impervious"),

    ("street furniture counts FOR the score", SCORE,
     "            + quietRoadsideWeight * (1 - t.furniture)",
     "            + quietRoadsideWeight * t.furniture"),

    # --- THE OTHER INVARIANT ------------------------------------------------------------------------------
    ("a motorway stops scoring zero", SCORE,
     '        if dullClasses.contains(t.highway) { return 0 }', "        // motorway rule removed"),

    ("only motorway scores zero, so trunk keeps its score", SCORE,
     '    public static let dullClasses: Set<String> = ["motorway", "motorway_link", "trunk", "trunk_link"]',
     '    public static let dullClasses: Set<String> = ["motorway", "motorway_link"]'),

    ("secondary roads are dull too, which would delete the scenic middle", SCORE,
     '    public static let dullClasses: Set<String> = ["motorway", "motorway_link", "trunk", "trunk_link"]',
     '    public static let dullClasses: Set<String> = ["motorway", "motorway_link", "trunk", "trunk_link",\n'
     '                                                  "secondary"]'),

    # --- the soft multipliers -----------------------------------------------------------------------------
    ("the tunnel threshold becomes non-strict, so exactly 300 m is penalised", SCORE,
     "        if t.tunnelMeters > tunnelThresholdMeters { score *= tunnelMultiplier }",
     "        if t.tunnelMeters >= tunnelThresholdMeters { score *= tunnelMultiplier }"),

    ("the tunnel threshold moves to 30 m, penalising every underpass", SCORE,
     "    public static let tunnelThresholdMeters = 300.0",
     "    public static let tunnelThresholdMeters = 30.0"),

    ("a tunnel costs almost nothing", SCORE,
     "    public static let tunnelMultiplier = 0.15", "    public static let tunnelMultiplier = 0.95"),

    ("the motorway-proximity test becomes non-strict at 150 m", SCORE,
     "        if t.metersToNearestMotorway < motorwayProximityMeters",
     "        if t.metersToNearestMotorway <= motorwayProximityMeters"),

    ("motorway proximity reaches 1500 m instead of 150", SCORE,
     "    public static let motorwayProximityMeters = 150.0",
     "    public static let motorwayProximityMeters = 1500.0"),

    ("the soft multipliers replace one another instead of compounding", SCORE,
     "        if t.tunnelMeters > tunnelThresholdMeters { score *= tunnelMultiplier }\n"
     "        if t.metersToNearestMotorway < motorwayProximityMeters { score *= motorwayProximityMultiplier }",
     "        if t.tunnelMeters > tunnelThresholdMeters { score = score * tunnelMultiplier }\n"
     "        else if t.metersToNearestMotorway < motorwayProximityMeters {\n"
     "            score *= motorwayProximityMultiplier\n        }"),

    # --- absent surface -----------------------------------------------------------------------------------
    ("an absent surface tag penalises a tertiary road too", SCORE,
     '    public static let unsurveyedClasses: Set<String> = ["unclassified", "residential"]',
     '    public static let unsurveyedClasses: Set<String> = ["unclassified", "residential", "tertiary"]'),

    ("the absent-surface penalty applies even when a surface tag is present", SCORE,
     "        if t.surface == nil, unsurveyedClasses.contains(t.highway) { score *= unsurveyedMultiplier }",
     "        if unsurveyedClasses.contains(t.highway) { score *= unsurveyedMultiplier }"),

    ("the surface-unknown flag stops depending on the surface tag", SCORE,
     "        t.surface == nil && unsurveyedClasses.contains(t.highway)",
     "        unsurveyedClasses.contains(t.highway)"),

    ("the absent-surface penalty is dropped", SCORE,
     "    public static let unsurveyedMultiplier = 0.8",
     "    public static let unsurveyedMultiplier = 1.0"),

    # --- byway and the range ------------------------------------------------------------------------------
    ("the byway bonus is uncapped, so the score can exceed one", SCORE,
     "        if t.isByway { e = min(1, e + bywayBonus) }",
     "        if t.isByway { e = e + bywayBonus }"),

    ("the byway bonus is dropped", SCORE,
     "    public static let bywayBonus = 0.15", "    public static let bywayBonus = 0.0"),

    ("out-of-range terms are clamped instead of refused", SCORE,
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.0).contains(term.value)) {\n"
     "            return nil\n        }",
     "        // validation removed"),

    ("a negative tunnel length is accepted", SCORE,
     "        guard t.tunnelMeters.isFinite, t.tunnelMeters >= 0 else { return nil }",
     "        guard t.tunnelMeters.isFinite else { return nil }"),

    ("one term drops out of validation, so nothing checks it", TERMS,
     '         ("pointsOfInterest", pointsOfInterest), ("water", water), ("furniture", furniture)]',
     '         ("pointsOfInterest", pointsOfInterest), ("furniture", furniture)]'),
]

EQUIVALENT = [
    ("write the product in the other order", SCORE,
     "        var score = pow(m, driveExponent) * pow(e, sceneryExponent)",
     "        var score = pow(e, sceneryExponent) * pow(m, driveExponent)"),
]

KNOWN_MISSED = []

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
    pristine = {f: f.read_bytes() for f in (SCORE, TERMS)}
    pristine_tests = {f: f.read_bytes() for f in TEST_FILES}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    known = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: EVERY test file is replaced by an empty suite, so every\n"
                             "mutation must report MISSED - not merely 'not caught'.\n")
            for f in TEST_FILES:
                f.write_text(empty_suite(f), encoding="utf-8", newline="\n")

        # Built TWICE before the baseline is declared broken, for the same reason each mutation is. On this
        # Windows checkout a first build into a fresh scratch directory can fail with "unable to create
        # symbolic link ... I/O error (code: 512)" and succeed immediately after. The mutation loop already
        # allowed for that; the baseline did not, so a transient failure aborted the whole run with
        # "baseline does not build" and nothing was ever measured. That happened on this harness's first run.
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

    known_ok = not KNOWN_MISSED or (
        known is not None and len(known["missed"]) + len(known["trapped"]) == len(KNOWN_MISSED))
    if not known_ok and known is not None:
        sys.stdout.write("KNOWN-GAP ARM FAILED: a gap that closed is good news - move it into MUTATIONS.\n")
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok and known_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
