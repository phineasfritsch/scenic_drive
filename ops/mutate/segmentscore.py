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
  * SKIP is its own bucket and never folded into MISSED;
  * the BASELINE build is retried, like every mutation build - on this Windows checkout a first build into a
    fresh scratch directory can fail with an I/O 512 symlink error and succeed immediately after, which made
    a sibling harness announce "baseline does not build" having measured nothing;
  * a TRAPPED verdict is re-run once, for the same reason and no further: a trap is a non-zero exit with no
    named test failing, which is also what an infrastructure flake looks like. The green path still costs one
    `swift test`;
  * the SUBJECT must be byte-identical to `git show HEAD:` before anything is built. A sibling harness in this
    repository was pointed at a file that already carried a mutation, measured the mutant, printed
    "34 of 34 caught", exited 0, and its `finally` restored the mutant it had started from;
  * MIN_MUTATIONS and MIN_EQUIVALENT are the REAL population, not a round number under it. A floor that sits
    below the count it guards refuses nothing anyone would actually do - see the note on them below.
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
# Under .artifacts/, which .gitignore covers. `.build-mutate-segmentscore` did NOT match .gitignore's
# `.build/`, so every run left an untracked directory behind and `ops/sane` then counted this worktree as
# dirty - a harness that reports on a tree it has itself made un-sane.
SCRATCH = ".artifacts/mutate-segmentscore"

# EVERY test file that could catch a mutation, because --prove-vacuity has to empty all of them for its proof
# to mean anything: one catching file left standing turns "MISSED with no tests present" into a lie.
# Re-checked by grep, not by memory, each time this list changes: `grep -rln "SegmentScore\|SegmentTerms"
# Tests/ Sources/` returns these FOUR test files and the two sources and nothing else.
TEST_FILES = [ROOT / "Tests" / "ScenicKitTests" / "SegmentScoreTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "SegmentScoreValidationTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "SegmentScoreWeightTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "SegmentScoreThresholdTests.swift"]


def empty_suite(path: pathlib.Path) -> str:
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))


# Floors on the HARNESS's own population. Without them the pass condition, the EQUIVALENT arm and
# `--prove-vacuity` are all VACUOUSLY TRUE on empty lists: "caught by a named test: 0 of 0 ... exit 0" and
# "VACUITY PROOF OK ... MISSED=0 of 0", the proof certifying its own vacuity. Found by the sign-off reviewer
# of PR #73 against ops/mutate/gates.py, the file this one was copied from. A harness detects "my anchors
# rotted" without this; it does not detect "my population was deleted", and the second is what happens when a
# mutation is removed with a plausible reason and nothing says the count fell.
#
# These are set to the REAL population, not below it. At 28 against a population of 31 the floor refused
# nothing anyone would actually do: three mutations could be deleted one at a time, each with a plausible
# reason, and the floor stayed green while the comment above claimed it caught exactly that. A floor that
# does not refuse what it is documented to refuse is worse than no floor, because it is believed. Raising
# the population is a deliberate edit to these two numbers in the same commit.
MIN_MUTATIONS = 64
MIN_EQUIVALENT = 2

# The ten `0...1` terms, transcribed from SegmentTerms rather than imported from it, so that a term renamed
# in the source makes the anchor go SKIP - which this harness scores as a failure - instead of quietly
# shrinking the population. `SegmentTerms.unitTerms` is the list on trial; dropping one term from it used to
# be a single mutation that removed `water`, which happened to be one of the four terms any test probed.
UNIT_TERMS = ["curvature", "elevationGain", "speedFit", "sinuosity", "canopy",
              "relief", "impervious", "pointsOfInterest", "water", "furniture"]


def drop_from_validation(term):
    """`term` leaves SegmentTerms.unitTerms, so nothing checks that it is in 0...1."""
    # "furniture" closes the array literal, so it is the one entry with no trailing comma of its own. The
    # others are taken WITH their comma but WITHOUT a trailing space, because `speedFit` and `impervious`
    # each end a line in that literal and are followed by a newline. A first draft included the space and
    # those two anchors matched nothing; the harness scores an unmatched anchor as SKIP and fails on it, so
    # this would have been loud rather than silent - but the fix is to anchor on what is actually there.
    anchor = ', ("%s", %s)' % (term, term) if term == "furniture" else '("%s", %s),' % (term, term)
    return ("%s drops out of validation, so nothing checks its range" % term, TERMS, anchor, "")


MUTATIONS = [drop_from_validation(t) for t in UNIT_TERMS] + [
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

    # A REAL swap: the previous entry under this name moved canopy 0.24 -> 0.12 and never touched water, so
    # sum(E) fell to 0.88 and it was behaviourally the same mutation as the one above it. Anchored across the
    # six contiguous E-weight declarations, which carry no comment between them.
    ("canopy and water weights really swapped, E still summing to one", SCORE,
     "    public static let canopyWeight = 0.24\n    public static let reliefWeight = 0.22\n"
     "    public static let openGroundWeight = 0.16\n    public static let poiWeight = 0.14\n"
     "    public static let waterWeight = 0.12",
     "    public static let canopyWeight = 0.12\n    public static let reliefWeight = 0.22\n"
     "    public static let openGroundWeight = 0.16\n    public static let poiWeight = 0.14\n"
     "    public static let waterWeight = 0.24"),

    # --- the weights AT THE POINT OF USE ---------------------------------------------------------------
    # `weightSetsSumToOne` pins all ten weights as literals, so any mutation of the DECLARATIONS is caught by
    # those literals whatever else is true. These move the effective weights in the formula instead, leaving
    # every literal green, which is the only way to ask whether the behavioural claims hold.
    #
    # There were two of them, and a reviewer measured that between them they asked about ONE weight out of
    # ten: curvature's. The three sum-preserving swaps below - open ground with points of interest, canopy
    # with water, elevation gain with sinuosity - each kept its set at 1.00 exactly and passed the whole
    # suite. `SegmentScoreWeightTests` asserts the full rank of both sets through the score, which is what
    # can see them - and, since round 4, their full VALUE as well. Rank is the weaker claim: a SHIFT that
    # moves two weights in opposite directions preserves both the sum and the order, so the rank assertions
    # cannot see it. The last two entries in this section are those shifts, and both survived at e2b77f5.
    ("a coordinated pair of effective weights: the saturated product is still one, "
     "neither set sums to one", SCORE,
     "        let m = curvatureWeight * t.curvature\n"
     "            + elevationGainWeight * t.elevationGain\n"
     "            + speedFitWeight * t.speedFit\n"
     "            + sinuosityWeight * t.sinuosity\n"
     "\n"
     "        var e = canopyWeight * t.canopy\n"
     "            + reliefWeight * t.relief",
     "        let m = 0.50 * t.curvature\n"
     "            + elevationGainWeight * t.elevationGain\n"
     "            + speedFitWeight * t.speedFit\n"
     "            + sinuosityWeight * t.sinuosity\n"
     "\n"
     "        var e = 0.214070469967848 * t.canopy\n"
     "            + reliefWeight * t.relief"),

    ("elevationGain overtakes curvature in M, which still sums to one", SCORE,
     "        let m = curvatureWeight * t.curvature\n"
     "            + elevationGainWeight * t.elevationGain",
     "        let m = 0.16 * t.curvature\n"
     "            + 0.49 * t.elevationGain"),

    ("elevation gain and sinuosity swap effective weights, M still summing to one", SCORE,
     "        let m = curvatureWeight * t.curvature\n"
     "            + elevationGainWeight * t.elevationGain\n"
     "            + speedFitWeight * t.speedFit\n"
     "            + sinuosityWeight * t.sinuosity",
     "        let m = curvatureWeight * t.curvature\n"
     "            + 0.15 * t.elevationGain\n"
     "            + speedFitWeight * t.speedFit\n"
     "            + 0.20 * t.sinuosity"),

    ("canopy and water swap effective weights, E still summing to one", SCORE,
     "        var e = canopyWeight * t.canopy\n"
     "            + reliefWeight * t.relief\n"
     "            + openGroundWeight * (1 - t.impervious)\n"
     "            + poiWeight * t.pointsOfInterest\n"
     "            + waterWeight * t.water",
     "        var e = 0.12 * t.canopy\n"
     "            + reliefWeight * t.relief\n"
     "            + openGroundWeight * (1 - t.impervious)\n"
     "            + poiWeight * t.pointsOfInterest\n"
     "            + 0.24 * t.water"),

    ("open ground and points of interest swap effective weights, E still summing to one", SCORE,
     "            + openGroundWeight * (1 - t.impervious)\n"
     "            + poiWeight * t.pointsOfInterest",
     "            + 0.14 * (1 - t.impervious)\n"
     "            + 0.16 * t.pointsOfInterest"),

    # A SHIFT, not a swap: the three above exchange two weights, which reverses their order and is what a rank
    # assertion sees. These move both weights of a pair in opposite directions by 0.01, so the set still totals
    # 1.00 exactly AND the declared order is untouched - 0.25 > 0.21 > 0.16 > 0.14 > 0.12 == 0.12, and
    # 0.46 > 0.20 == 0.20 > 0.14. Every literal, `weightSetsSumToOne`, `curvatureDominatesM` and both rank
    # tests stay green, and every non-uniform way in the corpus scores differently. Both survived all 39 tests
    # at e2b77f5; only a VALUE assertion can see them.
    ("the effective E weights shift by 0.01, E still summing to one and the rank preserved", SCORE,
     "        var e = canopyWeight * t.canopy\n"
     "            + reliefWeight * t.relief",
     "        var e = 0.25 * t.canopy\n"
     "            + 0.21 * t.relief"),

    ("the effective M weights shift by 0.01, M still summing to one and the rank preserved", SCORE,
     "        let m = curvatureWeight * t.curvature\n"
     "            + elevationGainWeight * t.elevationGain\n"
     "            + speedFitWeight * t.speedFit\n"
     "            + sinuosityWeight * t.sinuosity",
     "        let m = 0.46 * t.curvature\n"
     "            + elevationGainWeight * t.elevationGain\n"
     "            + speedFitWeight * t.speedFit\n"
     "            + 0.14 * t.sinuosity"),

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

    # The class rule on the axis no fixture varied. Every test that exercised it left `surface` at its nil
    # default, so the CLAUDE.md invariant "motorway/trunk carry scenic_score = 0" was pinned only for ways
    # carrying no surface tag - which for a motorway in OSM is the minority. Survived all 39 tests at e2b77f5.
    ("a dull class stops scoring zero once the way carries a surface tag", SCORE,
     "        if dullClasses.contains(t.highway) { return 0 }",
     "        if dullClasses.contains(t.highway), t.surface == nil { return 0 }"),

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

    # WHERE each of these two thresholds SITS, to the last representable Double. The four entries around them
    # move a threshold by a factor of ten or flip its strictness, which an integer probe at 301 or 149 can
    # see. These move it by HALF A METRE, which an integer probe cannot: both survived all 39 tests at
    # e2b77f5, so a 300.4 m tunnel took no penalty and a way 149.8 m from a motorway took no x0.7 while the
    # two tests named after those exact claims passed. Same defect, and the same fix, as the two guard floors
    # in round 3 - and the comment that said these two were already done is struck above.
    ("the tunnel threshold slips half a metre, so a 300.4 m tunnel is not penalised", SCORE,
     "    public static let tunnelThresholdMeters = 300.0",
     "    public static let tunnelThresholdMeters = 300.5"),

    ("the motorway-proximity threshold slips half a metre, so a way 149.8 m away hears nothing", SCORE,
     "    public static let motorwayProximityMeters = 150.0",
     "    public static let motorwayProximityMeters = 149.5"),

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

    ("a primary road stops being assumed paved", SCORE,
     '    public static let unsurveyedClasses: Set<String> = ["unclassified", "residential"]',
     '    public static let unsurveyedClasses: Set<String> = ["unclassified", "residential", "primary"]'),

    # The mirror image of "only motorway scores zero" on the other class list. It was not written, and
    # `absentSurfaceRule` exercised `residential` only, so every unclassified road in the graph could lose
    # both the x0.8 and the driver-facing flag in silence.
    ("unclassified stops taking the absent-surface penalty and the flag", SCORE,
     '    public static let unsurveyedClasses: Set<String> = ["unclassified", "residential"]',
     '    public static let unsurveyedClasses: Set<String> = ["residential"]'),

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
     "        if bywayBonusEarned > 0 { e = min(1, e + bywayBonusEarned) }",
     "        if bywayBonusEarned > 0 { e = e + bywayBonusEarned }"),

    ("the byway bonus is dropped", SCORE,
     "    public static let bywayBonus = 0.15", "    public static let bywayBonus = 0.0"),

    # Its VALUE and its FORM, not only its sign and its cap. 0.0 above is the single value the suite refused,
    # because the only two byway fixtures sat at and above saturation where the cap is all that shows - so
    # 0.25, 0.11 and "not an addition at all" were three survivors behind a 49-of-49 sheet.
    ("the byway bonus is 0.25 instead of 0.15", SCORE,
     "    public static let bywayBonus = 0.15", "    public static let bywayBonus = 0.25"),

    ("the byway bonus is 0.11 instead of 0.15", SCORE,
     "    public static let bywayBonus = 0.15", "    public static let bywayBonus = 0.11"),

    ("the byway bonus scales E by 1.15 instead of adding 0.15 to it", SCORE,
     "        if bywayBonusEarned > 0 { e = min(1, e + bywayBonusEarned) }",
     "        if bywayBonusEarned > 0 { e = min(1, e * (1 + bywayBonusEarned)) }"),

    ("out-of-range terms are clamped instead of refused", SCORE,
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.0).contains(term.value)) {\n"
     "            return nil\n        }",
     "        // validation removed"),

    # --- the validation window, at its edges ---------------------------------------------------------------
    # This window is one of FIVE numeric thresholds in this file, not the third of three. What stood here from
    # round 2 until round 4 was "The third threshold in this file. The other two (tunnel 300/301, proximity
    # 150/149) were pinned on both sides from the start" - STRUCK, because it was false, and because it is the
    # sentence a later agent reads when deciding which thresholds still need mutations. The round-3 Log
    # declared it false and struck it in the Log and in the PR body; this copy, the one that actually steers
    # the harness, was missed and stood verbatim at e2b77f5.
    #
    # The five: tunnel 300, motorway proximity 150, this window, and the two guard FLOORS at zero. The floors
    # were probed at -1.0 only until round 3. Tunnel and proximity were probed at 301 and 149 - the nearest
    # INTEGERS - until round 4, when `300.0 -> 300.5` and `150.0 -> 149.5` were both measured as survivors of
    # all 39 tests. Every one of the five is probed at the last representable Double either side now, and
    # every one carries its own mutation below. This window itself was probed only at 1.5 and -0.1 until
    # round 2, far enough outside that it could move a quarter of its own width without any test noticing.
    ("the 0...1 validation window is widened to 0...1.25", SCORE,
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.0).contains(term.value)) {",
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.25).contains(term.value)) {"),

    ("the validation window excludes its own top, so a term of exactly 1 is refused", SCORE,
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.0).contains(term.value)) {",
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0..<1.0).contains(term.value)) {"),

    # --- the two non-unit inputs, each guarded by its own rule ---------------------------------------------
    ("a negative tunnel length is accepted", SCORE,
     "        guard t.tunnelMeters.isFinite, t.tunnelMeters >= 0 else { return nil }",
     "        guard t.tunnelMeters.isFinite else { return nil }"),

    ("an infinite tunnel length is accepted", SCORE,
     "        guard t.tunnelMeters.isFinite, t.tunnelMeters >= 0 else { return nil }",
     "        guard t.tunnelMeters >= 0 else { return nil }"),

    ("the motorway-distance guard is deleted entirely", SCORE,
     "        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway >= 0 else { return nil }",
     "        // motorway-distance guard removed"),

    ("a negative motorway distance is accepted, silently applying the x0.7 penalty", SCORE,
     "        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway >= 0 else { return nil }",
     "        guard !t.metersToNearestMotorway.isNaN else { return nil }"),

    # WHERE each floor SITS, not merely that it is there. The two above delete the `>= 0` clause outright,
    # which -1.0 catches; these move the floor by one unit, which -1.0 cannot see. Both are thresholds in the
    # same sense as tunnel 300 and proximity 150, and both were probed on one side only.
    ("the tunnel floor slips from 0 down to -1, accepting a broken measurement of -0.5", SCORE,
     "        guard t.tunnelMeters.isFinite, t.tunnelMeters >= 0 else { return nil }",
     "        guard t.tunnelMeters.isFinite, t.tunnelMeters > -1 else { return nil }"),

    ("the motorway-distance floor slips from 0 down to -1, penalising a way that is nowhere near one", SCORE,
     "        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway >= 0 else { return nil }",
     "        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway > -1 else { return nil }"),

    # The DEFAULT the guard above is asymmetric for. `motorwayDistanceIsValidated` turns on `.infinity` being
    # this field's default and meaning "no motorway anywhere near", and nothing asserted the default itself:
    # 1000 is outside the 150 m window, so every fixture that relies on the default scores identically and
    # this survived all 39 tests at e2b77f5. A way built without an explicit distance would then claim a
    # motorway exactly 1 km away.
    ("SegmentTerms' default motorway distance stops being infinite", TERMS,
     "                metersToNearestMotorway: Double = .infinity) {",
     "                metersToNearestMotorway: Double = 1000) {"),

    # --- the ORDER of the shortcut and the validation ------------------------------------------------------
    # A motorway carrying a broken ETL term must still be REFUSED. With the shortcut moved above the checks it
    # scores a confident 0 and the bad measurement never surfaces, which is the exact failure the nil return
    # exists to prevent. No fixture put a dull class and an illegal term in the same way, so it survived.
    ("the dull-class shortcut jumps the validation block", SCORE,
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.0).contains(term.value)) {\n"
     "            return nil\n"
     "        }\n"
     "        guard t.tunnelMeters.isFinite, t.tunnelMeters >= 0 else { return nil }\n"
     "        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway >= 0 else { return nil }\n"
     "\n"
     "        if dullClasses.contains(t.highway) { return 0 }",
     "        if dullClasses.contains(t.highway) { return 0 }\n"
     "\n"
     "        for term in t.unitTerms where !(term.value.isFinite && (0.0...1.0).contains(term.value)) {\n"
     "            return nil\n"
     "        }\n"
     "        guard t.tunnelMeters.isFinite, t.tunnelMeters >= 0 else { return nil }\n"
     "        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway >= 0 else { return nil }"),
]

# Mutations that CANNOT change behaviour. Anything but MISSED here means a test has an opinion about how the
# code is WRITTEN rather than what it DOES, which is the failure mode that makes a suite impossible to
# refactor against. Each one carries the proof that it is equivalent.
EQUIVALENT = [
    ("write the product in the other order", SCORE,
     "        var score = pow(m, driveExponent) * pow(e, sceneryExponent)",
     "        var score = pow(e, sceneryExponent) * pow(m, driveExponent)"),

    # PROOF: every IEEE 754 comparison with NaN is false, so `NaN >= 0` is false and the remaining clause
    # already refuses NaN. The `!isNaN` clause is documentation, not a guard. It was tempting to bank this as
    # a coverage hole next to the two real ones above - a reviewer listed it as MISSED - but a survivor that
    # cannot change behaviour is not a missing test, so it is asserted the other way instead: if a test ever
    # CATCHES this, that test is reading the source rather than the behaviour.
    ("a NaN motorway distance stops being refused by name, only by the >= 0 comparison", SCORE,
     "        guard !t.metersToNearestMotorway.isNaN, t.metersToNearestMotorway >= 0 else { return nil }",
     "        guard t.metersToNearestMotorway >= 0 else { return nil }"),
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


def head_bytes(path: pathlib.Path):
    """The file exactly as HEAD carries it, or None when git cannot produce it."""
    rel = path.relative_to(ROOT).as_posix()
    p = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=ROOT, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def drift_from_head(paths) -> str:
    """'' when every subject is byte-identical to HEAD's blob, otherwise which one is not and how.

    `.gitattributes` forces `eol=lf` over the whole tree and `core.autocrlf` is false, so a clean working
    file and its blob are the same bytes on Windows as on Linux. This is a comparison, not an invocation of
    `git status`: a file can be listed as unmodified by a stale index and still differ.
    """
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        blob = head_bytes(path)
        if blob is None:
            return "cannot read HEAD:%s - this harness only measures a committed tree" % rel
        disk = path.read_bytes()
        if blob != disk:
            return ("%s is not what HEAD says it is (on disk md5 %s, HEAD md5 %s)"
                    % (rel, hashlib.md5(disk).hexdigest()[:8], hashlib.md5(blob).hexdigest()[:8]))
    return ""


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
                # A TRAPPED verdict is re-run once, and only a trapped one. A trap is a non-zero exit with no
                # named test failing - which is also exactly what an infrastructure flake looks like on this
                # box: a --prove-vacuity run scored one mutation TRAPPED against EMPTY suites, where there is
                # no assertion that could have failed. `build()` was already retried for that reason and
                # `test()` was not. Re-running only this branch leaves the green path at one `swift test`,
                # and a real trap is still a trap after the second run.
                if code != 0 and not FAIL_LINE.search(txt):
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
    if len(MUTATIONS) < MIN_MUTATIONS or len(EQUIVALENT) < MIN_EQUIVALENT:
        sys.stdout.write("REFUSING: %d mutations and %d equivalent mutants, expected at least %d and %d.\n"
                         "A harness that examines nothing exits 0 and proves nothing.\n"
                         % (len(MUTATIONS), len(EQUIVALENT), MIN_MUTATIONS, MIN_EQUIVALENT))
        return 2

    # The subject has to be what HEAD says it is, checked BEFORE anything is built. Every number this prints
    # is about the bytes on disk, so if those bytes are not the reviewed ones the whole run measures something
    # nobody is reviewing - and the `finally` then restores THAT, leaving the mutant in place and looking
    # clean. A sibling harness in this repository did exactly that: it measured an already-mutated file,
    # printed "34 of 34 caught", exited 0, and restored the mutant.
    drift = drift_from_head([SCORE, TERMS] + TEST_FILES)
    if drift:
        sys.stdout.write("REFUSING: %s\n"
                         "A harness measuring an already-modified subject reports the MUTANT's coverage and\n"
                         "then restores the mutant. Commit or restore the tree and run it again.\n" % drift)
        return 2

    pristine = {f: f.read_bytes() for f in (SCORE, TERMS)}
    pristine_tests = {f: f.read_bytes() for f in TEST_FILES}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
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

    # The KNOWN_MISSED arm this file inherited from ops/mutate/gates.py was removed rather than left in
    # place: `known` was never assigned, so the arm never ran, and with an empty KNOWN_MISSED its guard was
    # true for the wrong reason. A dead arm reads, to the next agent, like a third bucket that is being
    # checked. There is no known gap on this subject to declare; if one appears it goes in MUTATIONS and the
    # harness goes red until it is closed, which is the point.
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
