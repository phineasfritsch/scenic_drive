"""The mutation population for T-0239's menu: Sources/ScenicKit/Menu/RouteMenu.swift, MenuRow.swift,
RecordedAlternatives.swift and Sources/ScenicPlanCLI/MenuArguments.swift, MenuCommand.swift. The driver is menu.py and the runner menu_run.py.

## What the acceptance names, and where each lives

  * the FRONTIER COMPARISON - `RouteMenu.frontier`, entries 1-3 (inverted; the step halved-ish and raised);
  * the DEDUP THRESHOLD - `RouteMenu.sameRouteOverlap`, entries 6-7, killed by the printed-and-asserted
    distinct count (R3: on a time-then-fun frontier a near-duplicate is dropped anyway, so a threshold nobody
    can see is a threshold no test holds). Measured: the largest pairwise overlap among the six distinct
    routes is 0.794 (T1) and 0.803 (T4), so 0.8 merges two T4 routes and 1.01 merges nothing;
  * the FUN-KM THRESHOLD - `MenuRow.funScore`, entries 4-5;
  * the CAP - `RouteMenu.capMinutes`, its minutes-to-milliseconds conversion and `--max`'s path into it,
    entries 8-10 and 14-16.

Entries 11-12 hold R5 (the displayed extra minutes are a CEILING, rounded up) and entry 13 R8 (the roads).

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

MENU = ROOT / "Sources" / "ScenicKit" / "Menu" / "RouteMenu.swift"
ROW = ROOT / "Sources" / "ScenicKit" / "Menu" / "MenuRow.swift"
ARGS = ROOT / "Sources" / "ScenicPlanCLI" / "MenuArguments.swift"
CMD = ROOT / "Sources" / "ScenicPlanCLI" / "MenuCommand.swift"
READER = ROOT / "Sources" / "ScenicKit" / "Menu" / "RecordedAlternatives.swift"
SUBJECTS = (MENU, ROW, ARGS, CMD, READER)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "Menu" / "RouteMenuTests.swift",
              ROOT / "Tests" / "ScenicPlanCLITests" / "MenuCLITests.swift")

FRONTIER = "if route.funMeters >= best + Self.funStepMeters {"
STEP = "public static let funStepMeters = 2_000.0"
OVERLAP = "public static let sameRouteOverlap = 0.9"
CAP = "public static let capMinutes = 45.0"
LIMIT = "let limit = quickest + Int((minutes * 60_000).rounded(.down))"
LOWERED = "let minutes = min(maxMinutes, Self.capMinutes)"
QUICKEST = "let quickest = pool.map(\\.durationMilliseconds).min() ?? fastest.durationMilliseconds"
FUN_SCORE = "public static let funScore = 6"
ROAD_MIN = "public static let roadMinimumMeters = 300.0"
CEIL = "milliseconds <= 0 ? 0 : (milliseconds + 5_999) / 6_000"
MAX_GUARD = "guard minutes <= RouteMenu.capMinutes else {"
MAX_POSITIVE = "minutes.isFinite, minutes > 0 else {"
MAX_SET = "                maxMinutes = minutes\n"
BEST = "guard let best = rows.map(\\.funMeters).max() else {"
LADDER = "ladder: RouteMenu.ladder,"
IDENTITY = 'guard said == expected, field("algorithm").hasPrefix("alternative_route") == alternatives else {'
ENDPOINTS = 'guard near(field("from"), origin), near(field("to"), destination) else {'

T1 = "Topanga to Malibu: the menu rows to 0.1 min and 0.1 fun km"
T4 = "Zuma to Agoura: the menu rows to 0.1, and Latigo Canyon Road is on it"
DISTINCT = "alternative_route over the ladder yields 6 distinct routes per trip at Jaccard 0.9"
CEILING = "every menu row keeps ETA within fastest plus its displayed extra minutes"
MAX_CUT = "--max below a row drops that row and keeps every quicker one"
REFUSED = "--max above 45 and --router are refused by name"
BOUNDARY = "--max 0.1 below a row's displayed extra drops that row, and --max at it keeps it"
COUNTS = "ops/plan --menu reads every rung: candidates=25 distinct=6 on both trips"
MOST_FUN = "a slower route must add 2 fun km over the most fun km of every quicker row, not the highest share"
OTHER_TRIP = "a recording of another trip is refused, not replayed under these endpoints"
OTHER_RUNG = "a rung whose file carries another rung's recording is refused"
OWN_URL = ("each row's Apple Maps URL is its own route's: pairwise distinct, and T4's Latigo URL stops on "
           "Latigo Canyon Road")
ALGORITHM = "a recording whose algorithm is not its file's is refused, naming the algorithm"
FIRST_TENTH = "a route 1 ms over the fastest prints +0.1 min, and 6_001 ms over prints +0.2"

PINS = "PlanWaypoints.decisionPoints(table: row.table, path: row.path)"
ENDS = "AppleMapsDirections(source: arguments.origin, destination: arguments.destination,"
ORDER = "waypoints: waypoints).url()"
IN_ORDER = "every row's URL runs from the trip's origin to its destination, its waypoints in route order"

MUTATIONS = [
    # 1. The rule inverted - the red-first arm of acceptance 2: T1 [0.0, 7.1], T4 [0.0, 9.1, 10.5].
    ("the frontier rule inverted", MENU, FRONTIER,
     "if route.funMeters < best + Self.funStepMeters {", [T1, T4]),
    # 2. 1.5 km admits T1's +19.7 route (27.8 fun km, 1.6 over the +17.1 row's 26.2).
    ("the fun step 1.5 km instead of 2", MENU, STEP, "public static let funStepMeters = 1_500.0", [T1]),
    # 3. 5 km drops T4's +5.5 Snake row (4.9 fun km over the fastest's 10.6).
    ("the fun step 5 km instead of 2", MENU, STEP, "public static let funStepMeters = 5_000.0", [T4]),
    # 4-5. Fun is scenic_score >= 6: one class up and one down moves every fun-km figure on T1.
    ("fun at scenic_score 7 and above", ROW, FUN_SCORE, "public static let funScore = 7", [T1]),
    ("fun at scenic_score 5 and above", ROW, FUN_SCORE, "public static let funScore = 5", [T1]),
    # 6-7. The dedup threshold, both directions (0.803 is T4's closest distinct pair).
    ("the same-route overlap 0.8 instead of 0.9", MENU, OVERLAP,
     "public static let sameRouteOverlap = 0.8", [DISTINCT]),
    ("the same-route overlap above 1 - nothing is ever the same route", MENU, OVERLAP,
     "public static let sameRouteOverlap = 1.01", [DISTINCT]),
    # 8. The cap at 15 min: T1's +17.1 and T4's +16.6 Latigo rows fall off.
    ("the cap 15 minutes instead of 45", MENU, CAP, "public static let capMinutes = 15.0", [T1, T4]),
    # 9. The cap's unit: minutes read as hours, so --max 15 keeps T1's +17.1 row.
    ("the cap converted at 3_600_000 ms a minute", MENU, LIMIT,
     "let limit = quickest + Int((minutes * 3_600_000).rounded(.down))", [MAX_CUT]),
    # 10. --max ignored inside the menu.
    ("the caller's cap ignored, always 45", MENU, LOWERED, "let minutes = Self.capMinutes", [MAX_CUT]),
    # 11-12. R5: rounding to the NEAREST tenth prints +17.0 for 1_020_063 ms, under the real extra time.
    ("the extra minutes rounded to the nearest tenth", ROW, CEIL,
     "milliseconds <= 0 ? 0 : (milliseconds + 3_000) / 6_000", [CEILING]),
    ("the extra minutes floored", ROW, CEIL, "milliseconds <= 0 ? 0 : milliseconds / 6_000", [CEILING]),
    # 13. R8: a road is named at 300 m; at 3 km the Latigo row's short connectors vanish from its list.
    ("a road named only past 3 km", ROW, ROAD_MIN, "public static let roadMinimumMeters = 3_000.0", [T4]),
    # 14-16. --max: refused above 45, refused at 0, and actually used.
    ("--max accepted up to 60", ARGS, MAX_GUARD, "guard minutes <= 60 else {", [REFUSED]),
    ("--max 0 accepted", ARGS, MAX_POSITIVE, "minutes.isFinite, minutes >= 0 else {", [REFUSED]),
    ("--max parsed and dropped", ARGS, MAX_SET, "                maxMinutes = RouteMenu.capMinutes\n",
     [MAX_CUT]),
    # 17-18. The pre-review pass's M2a: slack in the cap. --max 15 / --max 10 leave >= 2.0 min before the next
    # row, so only the boundary test sees it; 100 ms is caught because T1's +17.1 row is 63 ms past 17.0.
    ("the cap a minute loose", MENU, LIMIT,
     "let limit = quickest + Int((minutes * 60_000).rounded(.down)) + 60_000", [BOUNDARY]),
    ("the cap 100 ms loose", MENU, LIMIT, "let limit = quickest + Int((minutes * 60_000).rounded(.down)) + 100",
     [BOUNDARY]),
    # 19. M1a: the SHIPPING load drops lambda 8 - candidates=21. Killed on MenuCommand.run's header.
    ("the shipping menu drops the ladder's top rung", CMD, LADDER, "ladder: Array(RouteMenu.ladder.dropLast()),",
     [COUNTS]),
    # 20. M2c: the step measured from the highest-SHARE quicker row (T4's Snake), not the most fun km.
    ("the frontier steps from the highest-share quicker row", MENU, BEST,
     "guard let best = rows.max(by: { $0.funShare < $1.funShare })?.funMeters else {", [MOST_FUN]),
    # 21-22. M3: the reader checks the recorded header - the rung (model) and the trip (from/to).
    ("a recording's model header not read", READER, IDENTITY,
     'guard said[0] == expected[0], field("algorithm").hasPrefix("alternative_route") == alternatives else {',
     [OTHER_RUNG]),
    ("a recording's endpoints not read", READER, ENDPOINTS,
     'guard !field("from").isEmpty, !field("to").isEmpty else {', [OTHER_TRIP]),
    # 23. rv1 B1: every row handed off on the FASTEST route's pins - 13 of 13 tests passed on it.
    ("the URLs built from row 0's route", CMD, PINS,
     "PlanWaypoints.decisionPoints(table: menu.rows[0].table, path: menu.rows[0].path)", [OWN_URL]),
    # 24-26. rv1 B2: the algorithm half of M3's header check, whole and each side alone.
    ("the recording's algorithm not read", READER, IDENTITY,
     "guard said == expected, alternatives || !alternatives else {", [ALGORITHM]),
    ("an alternatives file's algorithm not read", READER, IDENTITY,
     'guard said == expected, alternatives || !field("algorithm").hasPrefix("alternative_route") else {',
     [ALGORITHM]),
    ("fastest.json's algorithm not read", READER, IDENTITY,
     'guard said == expected, !alternatives || field("algorithm").hasPrefix("alternative_route") else {',
     [ALGORITHM]),
    # 27. rv1 R3: the first tenth of a minute printed as +0.0 - no recorded row is within 6 s of the fastest.
    ("the first tenth of a minute rounded to zero", ROW, CEIL,
     "milliseconds <= 6_000 ? 0 : (milliseconds + 5_999) / 6_000", [FIRST_TENTH]),
    # 28-29. rv2 M2 and M3: the URL's ends swapped and its pins reversed - the 16 menu tests before rv2 passed on each.
    ("the row URL's source and destination swapped", CMD, ENDS,
     "AppleMapsDirections(source: arguments.destination, destination: arguments.origin,", [IN_ORDER]),
    ("the row URL's waypoints reversed", CMD, ORDER, "waypoints: waypoints.reversed()).url()", [IN_ORDER]),
]

# `(name, path, old, new, witness)`: anything but MISSED fails the run.
EQUIVALENT = [
    ("the frontier step compared strictly", MENU, FRONTIER,
     "if route.funMeters > best + Self.funStepMeters {",
     "`>=` and `>` differ only for a route whose fun metres are EXACTLY 2_000.0 over the best quicker row. "
     "Over the two recordings the gains are, in duration order, T1: +1.5, +15.4, -2.7, +4.7, +1.6 km and "
     "T4: +4.9, -3.0, -8.2, +0.1, +4.2 km (fun metres are sums of haversine lengths over six-decimal "
     "coordinates, never a round 2000.0), so no input in the domain separates them; the step's VALUE is "
     "held by entries 2 and 3."),
    ("the reference taken from fastest.json instead of the pool's quickest", MENU, QUICKEST,
     "let quickest = fastest.durationMilliseconds",
     "The pool minimum IS fastest.json's time in both recordings - 1_075_693 ms (T1) and 1_099_444 ms (T4), "
     "equal to alternatives-fastest.json path 0 and every lambda-0 path 0 (record run, task Log) - so the "
     "two spellings agree on every recorded input. The minimum is kept because it can only make the "
     "ceiling stricter on a graph where some alternative beats car_fast's best."),
]

# Literal floors: the real counts. Adding a mutation means editing this number in the same diff.
MIN_MUTATIONS = 29
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 2
