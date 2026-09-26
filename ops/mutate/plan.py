"""Mutation population for Sources/ScenicKit/Plan - the ops/plan engine. A catch requires a NAMED TEST.

CLAUDE.md, Verification: *a new numeric module under Sources/ ships its mutation population under
ops/mutate/ with a literal floor*. T-0182 adds six numeric modules - the Jaccard difference, the band
multipliers, the table's interval arithmetic, the waypoint spacing, the ceiling and difference guards, and
the report's own number formatting - and this is their population. The CLI's minutes -> seconds conversion
joined them at the pre-review fix: it is arithmetic on the shipping path and it moves the ceiling.

WHAT COUNTS. A mutation is CAUGHT only when a named test records an issue. A non-zero exit with no named
failure is a TRAP and does not count; a mutation that does not compile is COMPILE-ONLY and does not count,
because a compiler error is a fact about Swift and not about this suite; a mutation whose anchor is gone is
SKIPPED, which says the harness is stale and is the opposite of MISSED. The pass condition is
`caught == len(MUTATIONS)`, full stop - ops/mutate/handoff.py's docstring records what happens when a
harness folds any other bucket into its total.

THE FLOOR is literal: MIN_MUTATIONS, plus the rule that every module in SUBJECT_MODULES is mutated by at
least one entry. An empty table passes `caught == len(MUTATIONS)` trivially, which is the vacuous green
this repository keeps finding. `--prove-floor` demonstrates both refusals without touching the tree.

THE SCRATCH PATH is `.build-mutate-plan` by default and may be pointed at a WARM one with
SCENIC_MUTATE_SCRATCH: CLAUDE.md requires every swift build on this box to pass its own scratch path, and a
cold one costs several minutes before the first verdict. Either way it is a scratch path, never the default.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# The modules this population covers, read as TEXT by ops/lib/check-mutate-population.py - which reads the
# declaration with a regex, so nothing goes INSIDE these parentheses but paths.
#
# The last of them is the CLI's minutes-to-seconds conversion, which was allowlisted with a reason that
# named the arithmetic and then excused it; multiplying by 3600 there shipped a 25-hour ceiling with every
# test green, so the entry is withdrawn and the module is a subject here (T-0182 R8).
SUBJECT_MODULES = (
    "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
    "Sources/ScenicKit/Plan/PlanTable.swift",
    "Sources/ScenicKit/Plan/PlanWaypoints.swift",
    "Sources/ScenicKit/Plan/RouteDifference.swift",
    "Sources/ScenicKit/Plan/RoutePath.swift",
    "Sources/ScenicKit/Plan/ScenicPlan.swift",
    "Sources/ScenicKit/Plan/ScenicPlanner.swift",
    "Sources/ScenicPlanCLI/GraphHopperRouteSource.swift",
    "Sources/ScenicPlanCLI/PlanArguments.swift",
)

TEST_FILES = (
    "Tests/ScenicKitTests/ScenicPlannerMetaTests.swift",
    "Tests/ScenicKitTests/LambdaCustomModelParityTests.swift",
    "Tests/ScenicKitTests/LambdaCustomModelRatRunTests.swift",
    "Tests/ScenicKitTests/CustomModelChain.swift",
    "Tests/ScenicKitTests/PlanCeilingOverLATests.swift",
    "Tests/HandoffTests/ScenicPlanGoldenTests.swift",
    "Tests/ScenicPlanCLITests/PlanCLIBudgetTests.swift",
    "Tests/ScenicPlanCLITests/PlanCLIRequestBodyTests.swift",
)

SUITES = ("ScenicPlannerMetaTests|LambdaCustomModelParityTests|ScenicPlanGoldenTests"
          "|PlanCLIBudgetTests|PlanCLIRequestBodyTests|LambdaCustomModelRatRunTests|PlanCeilingOverLATests")
SCRATCH = os.environ.get("SCENIC_MUTATE_SCRATCH", ".build-mutate-plan")

MIN_MUTATIONS = 31

# name, module, old, new
MUTATIONS = [
    ("difference/threshold-let-everything-through", "Sources/ScenicKit/Plan/RouteDifference.swift",
     "public static let maximumOverlap = 0.6", "public static let maximumOverlap = 1.1"),
    ("difference/empty-sets-read-as-different", "Sources/ScenicKit/Plan/RouteDifference.swift",
     "if union.isEmpty { return 1.0 }", "if union.isEmpty { return 0.0 }"),
    ("difference/intersection-becomes-union", "Sources/ScenicKit/Plan/RouteDifference.swift",
     "return Double(a.intersection(b).count) / Double(union.count)",
     "return Double(a.union(b).count) / Double(union.count)"),
    # T-0244: the per-request model's three rulings - (a) the minor clause, (b) distance_influence 0, (c) the ladder.
    ("custom-model/band-ignores-lambda", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     "return 1 / (1 + slope * lambda)", "return 1 / (1 + slope)"),
    ("custom-model/minor-slope-no-steeper-than-the-dullest-band", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     "public static let minorSlope = 2.0", "public static let minorSlope = 1.0"),
    ("custom-model/minor-clause-residential-only", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     '"(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class == SERVICE) && scenic_score < 7"',
     '"road_class == RESIDENTIAL && scenic_score < 7"'),
    ("custom-model/distance-influence-back-to-the-base", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     '"distance_influence": 0,', '"distance_influence": 30,'),
    ("custom-model/ladder-collapses-to-two-bands", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     "public static let ladder = [6, 5, 4, 3, 2, 1, 0]", "public static let ladder = [4, 0]"),
    ("custom-model/slope-steeper-by-one-step", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     "Double(highBand - score) / Double(highBand)", "Double(highBand - score) / Double(highBand - 1)"),
    ("custom-model/four-decimals-instead-of-six", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     "public static let multiplierDecimals = 6", "public static let multiplierDecimals = 4"),
    ("custom-model/trailing-zeros-survive", "Sources/ScenicKit/Plan/LambdaCustomModel.swift",
     'while digits.hasSuffix("0") { digits.removeLast() }', "// trailing zeros kept"),
    # T-0244 pre-review B1: the bytes scenic(from:to:lambda:) - the entry point ops/plan runs - puts on the wire.
    ("cli/scenic-request-ignores-lambda", "Sources/ScenicPlanCLI/GraphHopperRouteSource.swift",
     "let model = try LambdaCustomModel.json(for: lambda)", "let model = try LambdaCustomModel.json(for: 8)"),
    ("cli/scenic-request-changes-distance-influence", "Sources/ScenicPlanCLI/GraphHopperRouteSource.swift",
     "let model = try LambdaCustomModel.json(for: lambda)",
     'let model = try LambdaCustomModel.json(for: lambda)'
     '.replacingOccurrences(of: "\\"distance_influence\\": 0", with: "\\"distance_influence\\": 30")'),
    # T-0244 round 1 B1 (P-SAFE-04): fastest(from:to:) is the baseline the budget is a ceiling over.
    ("cli/fastest-request-uses-the-scenic-profile", "Sources/ScenicPlanCLI/GraphHopperRouteSource.swift",
     "profile: fastProfile, model: nil", "profile: scenicProfile, model: nil"),
    ("cli/fastest-request-carries-a-custom-model", "Sources/ScenicPlanCLI/GraphHopperRouteSource.swift",
     "profile: fastProfile, model: nil", "profile: fastProfile, model: try LambdaCustomModel.json(for: 0)"),
    # T-0244 round 2 B1-points (P-SAFE-04): the baseline and the scenic leg are the SAME trip, origin first.
    ("cli/fastest-request-swaps-origin-and-destination", "Sources/ScenicPlanCLI/GraphHopperRouteSource.swift",
     "try send(body(origin, destination, profile: fastProfile, model: nil))",
     "try send(body(destination, origin, profile: fastProfile, model: nil))"),
    ("cli/scenic-request-swaps-origin-and-destination", "Sources/ScenicPlanCLI/GraphHopperRouteSource.swift",
     "let body = body(origin, destination, profile: scenicProfile, model: model)",
     "let body = body(destination, origin, profile: scenicProfile, model: model)"),
    # T-0244 pre-review B2 (mutant C): the recorded route's class set narrowed in the test's own derivation;
    # the numeric scenic_score column and the measured 174.815 m run are the witnesses that must object.
    ("oracle/rat-run-class-set-drops-service", "Tests/ScenicKitTests/LambdaCustomModelRatRunTests.swift",
     '.components(separatedBy: "road_class == ").dropFirst()',
     '.components(separatedBy: "road_class == ").dropFirst().dropLast()'),
    ("table/detail-runs-match-at-both-ends", "Sources/ScenicKit/Plan/PlanTable.swift",
     "for run in runs where run.from <= index && index < run.to { return run.value }",
     "for run in runs where run.from <= index && index <= run.to { return run.value }"),
    ("table/segment-length-always-zero", "Sources/ScenicKit/Plan/PlanTable.swift",
     "meters += Geo.distanceMeters(points[index], points[index + 1])",
     "meters += Geo.distanceMeters(points[index], points[index])"),
    ("waypoints/one-pin-over-the-cap", "Sources/ScenicKit/Plan/PlanWaypoints.swift",
     ".prefix(limit)", ".prefix(limit + 1)"),
    ("waypoints/keep-the-shortest-stretches", "Sources/ScenicKit/Plan/PlanWaypoints.swift",
     "left.meters == right.meters ? left.fromIndex < right.fromIndex : left.meters > right.meters",
     "left.meters == right.meters ? left.fromIndex < right.fromIndex : left.meters < right.meters"),
    ("planner/ceiling-guard-always-passes", "Sources/ScenicKit/Plan/ScenicPlanner.swift",
     "guard chosen.duration <= ceiling else {", "guard true else {"),
    ("planner/ceiling-is-twice-the-budget", "Sources/ScenicKit/Plan/ScenicPlanner.swift",
     "let ceiling = fastest.duration + budget", "let ceiling = fastest.duration + budget * 2"),
    ("planner/actually-different-guard-always-passes", "Sources/ScenicKit/Plan/ScenicPlanner.swift",
     "guard overlap < RouteDifference.maximumOverlap else {", "guard true else {"),
    ("planner/ceiling-refuses-a-route-exactly-on-it", "Sources/ScenicKit/Plan/ScenicPlanner.swift",
     "guard chosen.duration <= ceiling else {", "guard chosen.duration < ceiling else {"),
    ("budget/minutes-are-multiplied-into-hours", "Sources/ScenicPlanCLI/PlanArguments.swift",
     "public var budget: TimeInterval { budgetMinutes * 60 }",
     "public var budget: TimeInterval { budgetMinutes * 3600 }"),
    ("decode/geojson-lon-lat-read-in-app-order", "Sources/ScenicKit/Plan/RoutePath.swift",
     "return Coordinate(latitude: position[1], longitude: position[0])",
     "return Coordinate(latitude: position[0], longitude: position[1])"),
    ("decode/milliseconds-read-as-seconds", "Sources/ScenicKit/Plan/RoutePath.swift",
     "public var duration: TimeInterval { Double(durationMilliseconds) / 1000 }",
     "public var duration: TimeInterval { Double(durationMilliseconds) }"),
    ("report/eta-rounds-down-instead-of-to-nearest", "Sources/ScenicKit/Plan/ScenicPlan.swift",
     "let whole = Int(seconds.rounded())", "let whole = Int(seconds.rounded(.down))"),
    ("report/fixed-drops-the-fraction", "Sources/ScenicKit/Plan/ScenicPlan.swift",
     "let scaled = (value * Double(scale)).rounded()",
     "let scaled = (value * Double(scale)).rounded(.down)"),
]

FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def head_blob(rel: str) -> bytes | None:
    p = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT, capture_output=True)
    return p.stdout if p.returncode == 0 else None


def refuse_if_not_head(paths) -> str | None:
    """A harness that measures an edited tree reports a number nobody can reproduce."""
    for rel in paths:
        head = head_blob(rel)
        if head is None:
            return "git show HEAD:%s failed - refusing to measure an unverifiable tree" % rel
        if (ROOT / rel).read_bytes() != head:
            return "%s differs from HEAD (on disk %s, committed %s)" % (
                rel, hashlib.md5((ROOT / rel).read_bytes()).hexdigest(), hashlib.md5(head).hexdigest())
    return None


def floor_problem(mutations, subjects) -> str | None:
    if len(mutations) < MIN_MUTATIONS:
        return "%d mutations, expected at least %d" % (len(mutations), MIN_MUTATIONS)
    for module in subjects:
        if not any(m[1] == module for m in mutations):
            return "%s is declared a subject and mutated by nothing" % module
    return None


def build() -> int:
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH, "--filter", SUITES],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(mutations) -> dict:
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    for name, module, old, new in mutations:
        path = ROOT / module
        pristine = path.read_bytes()
        text = pristine.decode("utf-8")
        if old not in text:
            sys.stdout.write("SKIP        %-56s anchor not found - the harness is stale\n" % name)
            out["skipped"].append(name)
            continue
        code = 0
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if build() != 0 and build() != 0:
                verdict = "compile_only"
            else:
                code, log = test()
                verdict = "caught" if FAIL_LINE.search(log) else ("trapped" if code != 0 else "missed")
        finally:
            path.write_bytes(pristine)
        out[verdict].append(name)
        note = {"caught": "a named test failed (exit=%d)" % code,
                "trapped": "non-zero exit, no named failure - does not count",
                "compile_only": "a fact about Swift, not about these tests - does not count",
                "missed": "exit=0, no test objected"}
        sys.stdout.write("%-12s%-56s %s\n" % (verdict.replace("_", "-").upper(), name, note[verdict]))
    return out


def prove_floor() -> int:
    """The floor, seen red - a check nobody has watched refuse is untested."""
    cases = [
        ("an empty population", [], SUBJECT_MODULES),
        ("one mutation", MUTATIONS[:1], SUBJECT_MODULES),
        # PlanFailure.swift is allowlisted rather than populated, so nothing in the table names it - which
        # is exactly the shape of the defect this arm refuses: a module declared into coverage.
        ("a subject nothing mutates", MUTATIONS,
         SUBJECT_MODULES + ("Sources/ScenicKit/Plan/PlanFailure.swift",)),
        ("the shipped table", MUTATIONS, SUBJECT_MODULES),
    ]
    failures = 0
    for label, mutations, subjects in cases:
        problem = floor_problem(mutations, subjects)
        expected = label != "the shipped table"
        ok = (problem is not None) == expected
        failures += 0 if ok else 1
        sys.stdout.write("%-28s %s   %s\n" % (label, "REFUSED" if problem else "accepted",
                                              problem or ""))
    return 0 if failures == 0 else 1


def main(argv) -> int:
    if "--prove-floor" in argv:
        return prove_floor()
    selected = MUTATIONS
    if "--only" in argv:
        # A comma-separated list of name fragments. The whole table is one run of tens of minutes on this
        # box, and a run that has to be abandoned halfway reports nothing at all; a slice reports its own
        # verdicts and the Log carries both halves.
        needles = argv[argv.index("--only") + 1].split(",")
        selected = [m for m in MUTATIONS if any(n in m[0] for n in needles)]
    problem = floor_problem(MUTATIONS, SUBJECT_MODULES)
    if problem is not None:
        sys.stdout.write("REFUSING: %s\nA harness that examines nothing exits 0 and proves nothing.\n"
                         % problem)
        return 2
    stale = refuse_if_not_head(list(SUBJECT_MODULES) + list(TEST_FILES))
    if stale is not None:
        sys.stdout.write("REFUSING: %s\nCommit, then measure.\n" % stale)
        return 2
    if build() != 0:
        sys.stdout.write("REFUSING: the pristine tree does not build; nothing measured here would mean "
                         "anything.\n")
        return 2
    sys.stdout.write("population %d mutations over %d modules, scratch %s%s\n"
                     % (len(MUTATIONS), len(SUBJECT_MODULES), SCRATCH,
                        "" if selected is MUTATIONS else " (running %d selected)" % len(selected)))
    out = run_all(selected)
    sys.stdout.write("caught %d of %d   trapped %d   compile-only %d   MISSED %d   skipped %d\n"
                     % (len(out["caught"]), len(selected), len(out["trapped"]),
                        len(out["compile_only"]), len(out["missed"]), len(out["skipped"])))
    return 0 if len(out["caught"]) == len(selected) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
