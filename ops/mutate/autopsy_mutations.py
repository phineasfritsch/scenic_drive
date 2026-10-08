"""The mutation population for T-0327's ops/route-autopsy (Sources/ScenicPlanCLI/Autopsy*.swift and
TracingRouteSource.swift). The runner is autopsy.py; the machinery is autopsy_run.py - menu.py's three-file
shape, under CLAUDE.md's 300-line cap.

## The subjects

Six files, every one edited by at least one entry (autopsy.py's floor refuses a subject nothing mutates):
the report (every number the autopsy prints is formatted there), the command (which planner, which source),
the fixture writer (what a pinned negative fixture is and what it refuses), the terms reader (how a file
becomes `SegmentTerms`), the arguments (which flags reach the command) and the tracer (the lambda trace).
`SegmentScore.axes(for:)` is NOT a subject here: it is `SegmentScore.swift`, whose population is
ops/mutate/segmentscore.py, and T-0327 kept its anchors verbatim (Log R3).

## Each entry

`(name, path, old, new, killers)`. `old` must appear VERBATIM in the pristine file or the run reports SKIP
and FAILS. No anchor is a comment. `killers` are display names of tests that MUST go red; other tests going
red as well is allowed, a named killer staying green is WRONG KILLER and fails the run.

## The one EQUIVALENT entry, and its witness

`index < widths.count` against `index <= widths.count - 1` over `Int`: `widths` is a non-empty literal, so
`widths.count - 1` cannot overflow, and for integers `a < b` holds exactly when `a <= b - 1`. No input to
`AutopsyReport.row` can tell the two apart.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

CLI = ROOT / "Sources" / "ScenicPlanCLI"
REPORT = CLI / "AutopsyReport.swift"
CMD = CLI / "AutopsyCommand.swift"
FIXTURE = CLI / "AutopsyFixture.swift"
TERMS = CLI / "AutopsyTerms.swift"
ARGS = CLI / "AutopsyArguments.swift"
TRACER = CLI / "TracingRouteSource.swift"
SUBJECTS = (REPORT, CMD, FIXTURE, TERMS, ARGS, TRACER)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicPlanCLITests" / "RouteAutopsyGoldenTests.swift",
              ROOT / "Tests" / "ScenicPlanCLITests" / "RouteAutopsyFixtureTests.swift")

GOLDEN = "the autopsy of westwood-malibu equals its golden, every line"
TRACE = "every trace step is a lambda the search measured, at the raw time of its recording"
TERMS_ROWS = "each way in the terms file prints its gate, M, E and score from ScenicKit"
DASHES = "a way the terms file does not carry prints dashes, never a default"
WRITES = "--fixture writes the traced recordings, the terms, fixture.json and an autopsy that replays"
REFUSES = "--fixture refuses outside Tests/, over an existing directory, and without --recorded"

MUTATIONS = [
    ("a step fits when it OVERSHOOTS the ceiling", REPORT,
     '(step.duration <= plan.ceiling ? "yes" : "no")', '(step.duration > plan.ceiling ? "yes" : "no")',
     [GOLDEN, TRACE]),
    ("the router's 0..10 score read as 0..100", REPORT,
     "static let encodedScoreScale = 10.0", "static let encodedScoreScale = 100.0", [GOLDEN]),
    ("M and E printed in each other's column", REPORT,
     "ScenicPlan.fixed(axes.drive, 3), ScenicPlan.fixed(axes.scenery, 3)",
     "ScenicPlan.fixed(axes.scenery, 3), ScenicPlan.fixed(axes.drive, 3)", [GOLDEN, TERMS_ROWS]),
    ("a refused way printed as allowed", REPORT,
     'case let .refused(reason): gate = "refused:\\(reason.rawValue)"', 'case .refused: gate = "allowed"',
     [GOLDEN, TERMS_ROWS]),
    ("a way with no terms printed as zeros", REPORT,
     'guard let way else { return ["-", "-", "-", "-"] }',
     'guard let way else { return ["-", "0.000", "0.000", "0.000"] }', [GOLDEN, DASHES]),
    ("the trace numbered from 0", REPORT,
     "Self.pad(String(index + 1), 4)", "Self.pad(String(index), 4)", [GOLDEN]),
    ("the evaluation cap not passed through", CMD,
     "ScenicPlanner(source: tracer, maxEvaluations: arguments.plan.maxEvaluations)",
     "ScenicPlanner(source: tracer, maxEvaluations: 5)", [GOLDEN, TRACE]),
    ("the planner given the untraced source", CMD,
     "ScenicPlanner(source: tracer,", "ScenicPlanner(source: source,", [GOLDEN, TRACE]),
    ("the trace records metres as seconds", TRACER,
     "steps.append(Step(lambda: lambda, duration: path.duration))",
     "steps.append(Step(lambda: lambda, duration: path.distanceMeters))", [GOLDEN, TRACE]),
    ("a fixture written outside Tests/", FIXTURE,
     'guard directory.standardizedFileURL.pathComponents.contains("Tests") else {', "guard true else {",
     [REFUSES]),
    ("a pinned fixture overwritten", FIXTURE,
     "guard !files.fileExists(atPath: directory.path) else {", "guard true else {", [REFUSES]),
    ("autopsy.txt replayed against the source recording, not the fixture", FIXTURE,
     "router: .recorded(directory),", "router: .recorded(recording),", [WRITES]),
    ("the FIXTURE line miscounts its files", FIXTURE,
     "let count = names.count + (replayTerms == nil ? 0 : 1) + 2",
     "let count = names.count + (replayTerms == nil ? 0 : 1) + 1", [WRITES]),
    ("a null motorway distance read as zero metres", TERMS,
     "case is NSNull: motorway = .infinity", "case is NSNull: motorway = 0", [GOLDEN]),
    ("curvature and elevation gain read from each other's key", TERMS,
     'curvature: unit["curvature"]!, elevationGain: unit["elevationGain"]!',
     'curvature: unit["elevationGain"]!, elevationGain: unit["curvature"]!', [GOLDEN, TERMS_ROWS]),
    ("--terms parsed and dropped", ARGS,
     "terms = URL(fileURLWithPath: value)", "terms = nil", [GOLDEN]),
    ("--fixture accepted with a live router", ARGS,
     "if fixture != nil, case .http = plan.router {", "if fixture == nil, case .http = plan.router {",
     [REFUSES]),
]

EQUIVALENT = [
    ("index < count as index <= count - 1", REPORT,
     "index < widths.count ? pad(cell, widths[index]) : cell",
     "index <= widths.count - 1 ? pad(cell, widths[index]) : cell",
     "widths is a non-empty literal, so count - 1 cannot overflow, and over Int a < b holds exactly when "
     "a <= b - 1: no row can tell the two apart"),
]

# Literal floors: the population as written above. Lowering one is a reviewed edit, never a quiet one.
MIN_MUTATIONS = 17
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 2
