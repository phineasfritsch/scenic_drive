"""The mutation population for T-0249's road-trip day splitter: Sources/ScenicKit/RoadTrip/RoadTrip.swift and its
four value types RoadTripEdge.swift, RoadTripPlace.swift, RoadTripLimits.swift, RoadTripDay.swift. The driver is
roadtrip.py and the runner roadtrip_run.py (menu's three-file shape).

## What the acceptance names, and where each lives

  * the +40% BUDGET and its CEILING - entries 1-2 (R3);
  * the FORWARD PASS - max drive and max metres, each inclusive and each dropped (3-6), the even share (7),
    every day drives (8), the pass reaching B (9), the degenerate outcomes (10-11), the cumulative clock (12);
  * 2-4 CORRIDOR STOPS - the 5 km radius (13), stops only (14), day ownership (15-16), the cap of 4 (17),
    the ranking and its tie (18-19), route order (20);
  * the OVERNIGHT - the 15 km radius from both sides (21-22), nearest wins (23), rounding (24), no overnight on
    the arrival day (25);
  * the four value types' inits (26-30): the tests render a day's PROPERTIES, so a swapped field is seen.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "ScenicKit" / "RoadTrip"
TRIP = _DIR / "RoadTrip.swift"
EDGE = _DIR / "RoadTripEdge.swift"
PLACE = _DIR / "RoadTripPlace.swift"
LIMITS = _DIR / "RoadTripLimits.swift"
DAY = _DIR / "RoadTripDay.swift"
SUBJECTS = (TRIP, EDGE, PLACE, LIMITS, DAY)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "RoadTrip" / "RoadTripPlanTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "RoadTrip" / "RoadTripPropertyTests.swift")

A = "LA to Big Sur in 3 days at 4 h and 200 mi: the whole day plan"
B = "LA to Big Sur in 4 days at 2.5 h and 100 mi: the whole day plan, miles binding"
C = "LA to Big Sur in 3 days at 2.5 h is too few days, stopped at Lucia"
BUDGET = "the +40% budget is a ceiling: fastest 20_411 plans, 20_410 is over budget"
METRES = "a day may drive exactly its max metres, and one metre less moves the boundary"
SECONDS = "a day may drive exactly its max seconds, and one second less moves the boundary"
LIMITS_HOLD = "no day exceeds its max drive or max metres, and the days cover A to B edge for edge"
EVERY_DAY = "an edge spanning two even shares still leaves every day an edge, and no day is invented"
DEGENERATE = "zero days is too few days at vertex 0, and no edges is an empty plan"

LIMIT_LINE = "if seconds + edge.seconds > limits.maxDriveSeconds || meters + edge.meters > limits.maxMeters {"
SHARE = "if index > start && cumulative * limits.days >= day * total { break }"
RANK_TIE = "if a.vertex != b.vertex { return a.vertex < b.vertex }"
ROUTE_ORDER = "a.vertex != b.vertex ? a.vertex < b.vertex : a.place.name < b.place.name"
NEAREST = "if let held = best, held.meters < meters ||"

MUTATIONS = [
    ("1 budget percent 40 -> 41", TRIP, "public static let budgetPercent = 40",
     "public static let budgetPercent = 41", [BUDGET]),
    ("2 the ceiling made strict", TRIP, "guard total <= ceiling else {", "guard total < ceiling else {",
     [BUDGET, A]),
    ("3 max drive made strict", TRIP, LIMIT_LINE, LIMIT_LINE.replace("> limits.maxDriveSeconds",
                                                                     ">= limits.maxDriveSeconds"), [SECONDS]),
    ("4 max metres made strict", TRIP, LIMIT_LINE, LIMIT_LINE.replace("> limits.maxMeters", ">= limits.maxMeters"),
     [METRES]),
    ("5 max drive dropped", TRIP, LIMIT_LINE, LIMIT_LINE.replace("seconds + edge.seconds > limits.maxDriveSeconds || ",
                                                                 ""), [C, SECONDS]),
    ("6 max metres dropped", TRIP, LIMIT_LINE, LIMIT_LINE.replace(" || meters + edge.meters > limits.maxMeters", ""),
     [B, METRES]),
    ("7 the even share dropped: drive to the limits", TRIP, SHARE,
     SHARE.replace("day * total", "limits.days * total"), [A]),
    ("8 a day may take no edge", TRIP, SHARE, SHARE.replace("index > start && ", ""), [EVERY_DAY]),
    ("9 the pass need not reach B", TRIP, "guard reached == edges.count else {", "guard reached >= 0 else {", [C]),
    ("10 zero days reports vertex 1", TRIP, "guard limits.days >= 1 else { return .tooFewDays(days: limits.days, "
     "reachedVertex: 0) }", "guard limits.days >= 1 else { return .tooFewDays(days: limits.days, reachedVertex: 1) }",
     [DEGENERATE]),
    ("11 no edges is too few days", TRIP, "guard !edges.isEmpty else { return .plan([]) }",
     "guard !edges.isEmpty else { return .tooFewDays(days: limits.days, reachedVertex: 0) }", [DEGENERATE]),
    ("12 the share clock counts metres", TRIP, "cumulative += edge.seconds", "cumulative += edge.meters", [A]),
    ("13 corridor radius 5 km -> 6 km", TRIP, "public static let corridorMeters = 5_000.0",
     "public static let corridorMeters = 6_000.0", [A]),
    ("14 lodgings count as corridor stops", TRIP, "places.filter { $0.kind == .stop }.compactMap { place in",
     "places.compactMap { place in", [A]),
    ("15 a boundary stop goes to both days", TRIP, "let first = start == 0 ? 0 : start + 1", "let first = start",
     [A]),
    ("16 a boundary stop goes to the next day", TRIP, "$0.vertex >= first && $0.vertex <= end",
     "$0.vertex >= first && $0.vertex < end", [A]),
    ("17 stops capped at 3", TRIP, "public static let maxStopsPerDay = 4", "public static let maxStopsPerDay = 3",
     [A]),
    ("18 lowest score first", TRIP, "return a.place.score > b.place.score", "return a.place.score < b.place.score",
     [A]),
    ("19 a score tie goes to the later vertex", TRIP, RANK_TIE, RANK_TIE.replace("a.vertex < b.vertex",
                                                                               "a.vertex > b.vertex"), [A]),
    ("20 stops listed against route order", TRIP, ROUTE_ORDER, ROUTE_ORDER.replace("a.vertex < b.vertex",
                                                                                   "a.vertex > b.vertex"), [A]),
    ("21 overnight radius 15 km -> 14 km", TRIP, "public static let overnightRadiusMeters = 15_000.0",
     "public static let overnightRadiusMeters = 14_000.0", [B]),
    ("22 overnight radius 15 km -> 16.2 km", TRIP, "public static let overnightRadiusMeters = 15_000.0",
     "public static let overnightRadiusMeters = 16_200.0", [A]),
    ("23 the farthest lodging wins", TRIP, NEAREST, NEAREST.replace("held.meters < meters", "held.meters > meters"),
     [A]),
    ("24 lodging metres truncated", TRIP, "meters: Int(best.meters.rounded())", "meters: Int(best.meters)", [B]),
    ("25 the arrival day sleeps out", TRIP, "let last = index == spans.count - 1", "let last = index == spans.count",
     [A]),
    ("26 edge seconds read its metres", EDGE, "self.seconds = seconds", "self.seconds = meters", [A]),
    ("27 place score ignored", PLACE, "self.score = score", "self.score = 0", [A]),
    ("28 limits read metres as seconds", LIMITS, "self.maxDriveSeconds = maxDriveSeconds",
     "self.maxDriveSeconds = maxMeters", [C]),
    ("29 day seconds read its metres", DAY, "self.seconds = seconds", "self.seconds = meters", [A]),
    ("30 day end read as its start", DAY, "self.endVertex = endVertex", "self.endVertex = startVertex", [A]),
]

# Cannot change behaviour, so each must report MISSED; anything else is a FAILURE. `(name, path, old, new, witness)`.
EQUIVALENT = [
    ("E1 empty days kept in the pass", TRIP, "guard index > start else { break }",
     "guard index >= start else { break }",
     "a day takes no edge only when its first edge breaks a limit; every later day meets the same edge under the "
     "same limits and takes none either, so the spans' last end - the only thing read when the pass falls short "
     "- is the same vertex, and a pass that reaches B never makes an empty span (`guard index < edges.count`)"),
    ("E2 the cap clamped by hand", TRIP, "ranked.prefix(maxStopsPerDay)",
     "ranked.prefix(min(maxStopsPerDay, ranked.count))",
     "Array.prefix(n) already returns the whole array when n exceeds its count"),
]

MIN_MUTATIONS = 30
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 2
