"""The mutation population for T-0294's plan sheet: the state machine and its gate (Sources/ScenicKit/PlanSheet/
PlanSheet.swift), the error-copy table, the preview's ETA arithmetic, the value types the tests read whole, and
ScenicAPIClient's two mappings into them (ClientPlanner, PlanError.failure). Driver plansheet.py, runner
plansheet_run.py (surprise's three-file shape).

  * THE GATE, P-SAFE-03 (1-4): the disclaimer dropped from it, a ticket from searching or planning, acceptance
    never recorded;
  * THE ORIGIN, P-PRIV-06 (5-8): rounding dropped, one axis unrounded, truncation for rounding;
  * THE MACHINE (9-14): a pick filling the wrong field, each half of the budget clamp, the bound itself, a stale
    reply landing, serials not advancing, a search during a plan;
  * THE COPY TABLE (15-18): a line, an action, a button's words, the case order the table is compared in;
  * THE PREVIEW (19-21): extra minutes below zero, truncation for rounding, the badge always on;
  * THE VALUE TYPES AND MAPPINGS (22-27): a ticket field, a place's coordinate, a hazard run's end, ClientPlanner's
    ETAs and hazard ends, one PlanError arm;
  * THE GATE ON EVERY PATH AND THE IN-FLIGHT FREEZE (28-30, pre-review survivors M1 and M3b): the disclaimer
    checked on only some launch states (failed, preview skip it), the budget moving while a plan is in flight.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "ScenicKit" / "PlanSheet"
SHEET = _DIR / "PlanSheet.swift"
COPY = _DIR / "PlanFailureCopy.swift"
ACTION = _DIR / "PlanFailureAction.swift"
FAILURE = _DIR / "PlanSheetFailure.swift"
PREVIEW = _DIR / "PlanPreview.swift"
TICKET = _DIR / "PlanTicket.swift"
PLACE = _DIR / "PlanPlace.swift"
HAZARD = _DIR / "PlanHazardRun.swift"
PLANNER = ROOT / "Sources" / "ScenicAPIClient" / "ClientPlanner.swift"
ERROR = ROOT / "Sources" / "ScenicAPIClient" / "PlanError.swift"
SUBJECTS = (SHEET, COPY, ACTION, FAILURE, PREVIEW, TICKET, PLACE, HAZARD, PLANNER, ERROR)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "PlanSheet" / "PlanSheetTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "PlanSheet" / "PlanFailureCopyTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "PlanSheetGateTests.swift")

GATE = "first launch: no ticket until the disclaimer is accepted, then one"
SAFE = "P-SAFE-03: from first launch no plan request is made before the disclaimer is accepted"
WHOLE = "the ticket is the typed start at 2 dp, the destination's id and the budget, whole"
PRIV = "P-PRIV-06: a typed start leaves as ONE coordinate at 2 dp, the body equal to its recomputation"
FIELD = "choosing fills the field being searched and keeps the other"
STATES = "no ticket from idle, searching or planning, nor without a start"
STALE = "a reply lands only on the ticket in flight; a stale one is dropped"
BOUNDS = "the extra time is clamped to 0...180 at every bound"
ETA = "the preview's ETA line against the fastest, rounded, never negative"
ROWS = "every PlanSheetFailure has its one copy line and one action"
ORDER = "the table covers all thirteen PlanError cases, in PlanError's order"
TITLES = "every action has its button words"
PREVIEWED = "a 200 reaches the sheet as the preview of exactly that response"
MAPPED = "every PlanError reaches the sheet as its own PlanSheetFailure"
PATHS = "the gate holds on every path: acceptance withdrawn, no ticket from chosen, failed or preview"
REPLAN = "P-SAFE-03: after a failure or a preview, no request once acceptance is withdrawn, through the planner"
FROZEN = "inputs are frozen while a plan is in flight: the budget, a search, a pick"

STATE_ARMS = "        case .chosen, .preview, .failed: break\n        case .idle, .searching, .planning: return nil"
GATE_HEAD = ("        guard disclaimerAccepted, let start, let destination else { return nil }\n        switch state {\n"
             "        case .chosen, .preview, .failed: break")
BUDGET_FREEZE = "        if case .planning = state { return }\n        budgetMinutes = min("

MUTATIONS = [
    ("1 the gate ignores the disclaimer", SHEET,
     "guard disclaimerAccepted, let start, let destination else { return nil }",
     "guard let start, let destination else { return nil }", [GATE, SAFE]),
    ("2 a ticket while searching", SHEET, STATE_ARMS,
     "        case .chosen, .preview, .failed, .searching: break\n        case .idle, .planning: return nil", [STATES]),
    ("3 a second ticket while one is in flight", SHEET, STATE_ARMS,
     "        case .chosen, .preview, .failed, .planning: break\n        case .idle, .searching: return nil", [STATES]),
    ("4 acceptance never recorded", SHEET, "disclaimerAccepted = accepted", "disclaimerAccepted = false",
     [GATE, SAFE]),
    ("5 the origin unrounded", SHEET, "origin: Self.twoDecimals(start.coordinate)", "origin: start.coordinate",
     [WHOLE, PRIV]),
    ("6 latitude unrounded", SHEET, "Coordinate(latitude: (coordinate.latitude * 100).rounded() / 100,",
     "Coordinate(latitude: coordinate.latitude,", [WHOLE, PRIV]),
    ("7 longitude unrounded", SHEET, "longitude: (coordinate.longitude * 100).rounded() / 100)",
     "longitude: coordinate.longitude)", [WHOLE, PRIV]),
    ("8 truncation for rounding", SHEET, "Coordinate(latitude: (coordinate.latitude * 100).rounded() / 100,",
     "Coordinate(latitude: (coordinate.latitude * 100).rounded(.towardZero) / 100,", [WHOLE, PRIV]),
    ("9 a start pick fills the destination", SHEET, "case .start: start = place", "case .start: destination = place",
     [FIELD]),
    ("10 no floor on the budget", SHEET, "budgetMinutes = min(max(minutes, 0), Self.maxBudgetMinutes)",
     "budgetMinutes = min(minutes, Self.maxBudgetMinutes)", [BOUNDS]),
    ("11 no ceiling on the budget", SHEET, "budgetMinutes = min(max(minutes, 0), Self.maxBudgetMinutes)",
     "budgetMinutes = max(minutes, 0)", [BOUNDS]),
    ("12 the ceiling one short", SHEET, "public static let maxBudgetMinutes = 180",
     "public static let maxBudgetMinutes = 179", [BOUNDS]),
    ("13 a stale reply lands", SHEET, "guard case .planning(let inFlight) = state, inFlight == ticket else { return }",
     "guard case .planning = state else { return }", [STALE]),
    ("14 a search during a plan", SHEET, "        if case .planning = state { return }\n        state = .searching",
     "        state = .searching", [STATES]),
    ("15 a copy line changed", COPY, "Couldn't reach that place by paved road.",
     "Couldn't reach that place.", [ROWS]),
    ("16 an action changed", COPY,
     'line: "Something went wrong on our side. Try again in a moment.", action: .tryAgain',
     'line: "Something went wrong on our side. Try again in a moment.", action: .close', [ROWS]),
    ("17 a button's words", ACTION, 'case .tryAgain: return "Try again"', 'case .tryAgain: return "Retry"', [TITLES]),
    ("18 two cases swapped", FAILURE, "    case regionUnsupported\n    case attestUnsupported",
     "    case attestUnsupported\n    case regionUnsupported", [ORDER]),
    ("19 extra minutes below zero", PREVIEW, "max(0, Int(((etaSeconds - fastestEtaSeconds) / 60).rounded()))",
     "Int(((etaSeconds - fastestEtaSeconds) / 60).rounded())", [ETA]),
    ("20 minutes truncated", PREVIEW, "Int((etaSeconds / 60).rounded())", "Int(etaSeconds / 60)", [ETA]),
    ("21 the badge always on", PREVIEW, "public var showsEstimateBadge: Bool { etaIsEstimate }",
     "public var showsEstimateBadge: Bool { true }", [ETA]),
    ("22 a ticket's serial is its budget", TICKET, "self.serial = serial", "self.serial = budgetMinutes", [WHOLE]),
    ("23 a place's axes swapped", PLACE, "self.coordinate = coordinate",
     "self.coordinate = Coordinate(latitude: coordinate.longitude, longitude: coordinate.latitude)", [WHOLE]),
    ("24 a hazard run ends where it starts", HAZARD, "self.toIndex = toIndex", "self.toIndex = fromIndex",
     [PREVIEWED]),
    ("25 the two ETAs swapped", PLANNER,
     "etaSeconds: response.etaSeconds,\n                    fastestEtaSeconds: response.fastestEtaSeconds,",
     "etaSeconds: response.fastestEtaSeconds,\n                    fastestEtaSeconds: response.etaSeconds,",
     [PREVIEWED]),
    ("26 a hazard's ends swapped", PLANNER, "fromIndex: $0.fromIndex, toIndex: $0.toIndex)",
     "fromIndex: $0.toIndex, toIndex: $0.fromIndex)", [PREVIEWED]),
    ("27 noRoute read as offline", ERROR, "case .noRoute: return .noRoute", "case .noRoute: return .routingOffline",
     [MAPPED]),
    ("28 the retry path skips the disclaimer", SHEET, GATE_HEAD,
     "        guard let start, let destination else { return nil }\n        switch state {\n"
     "        case .chosen, .preview: guard disclaimerAccepted else { return nil }\n        case .failed: break",
     [PATHS, REPLAN]),
    ("29 a re-plan from a preview skips the disclaimer", SHEET, GATE_HEAD,
     "        guard let start, let destination else { return nil }\n        switch state {\n"
     "        case .chosen, .failed: guard disclaimerAccepted else { return nil }\n        case .preview: break",
     [PATHS, REPLAN]),
    ("30 the budget moves while a plan is in flight", SHEET, BUDGET_FREEZE, "        budgetMinutes = min(",
     [FROZEN]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 zero extra read as at most zero", PREVIEW, "return extra == 0", "return extra <= 0",
     "extra is extraMinutes, which is max(0, ...): it is never below zero, so == 0 and <= 0 agree on every input"),
]

MIN_MUTATIONS = 30
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 3
