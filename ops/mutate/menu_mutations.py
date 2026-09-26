"""The mutation population for T-0239's menu: Sources/ScenicKit/Menu/RouteMenu.swift, MenuRow.swift and
Sources/ScenicPlanCLI/MenuArguments.swift. The driver is menu.py and the runner menu_run.py.

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
SUBJECTS = (MENU, ROW, ARGS)
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

T1 = "Topanga to Malibu: the menu rows to 0.1 min and 0.1 fun km"
T4 = "Zuma to Agoura: the menu rows to 0.1, and Latigo Canyon Road is on it"
DISTINCT = "alternative_route over the ladder yields 6 distinct routes per trip at Jaccard 0.9"
CEILING = "every menu row keeps ETA within fastest plus its displayed extra minutes"
MAX_CUT = "--max below a row drops that row and keeps every quicker one"
REFUSED = "--max above 45 and --router are refused by name"

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
MIN_MUTATIONS = 16
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 2
