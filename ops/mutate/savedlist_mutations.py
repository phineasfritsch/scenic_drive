"""The mutation population for T-0306's saved drives: the Saved list's state machine (Sources/ScenicKit/Saved/
SavedList.swift), the replay's destination pick (SavedReplay.swift), the PlanResponse -> SavedDraft -> SavedDrive
conversion (ClientPlanner.swift, SavedDraft.swift, PlaceStore's SavedDrive.unresolved and SavedSegment.unplaced),
the row's shown line (SavedRow.swift) and the replay through the plan sheet's gate (PlanSheet.replay). Driver
savedlist.py, runner savedlist_run.py (plansheet's three-file shape).

  * THE MACHINE (1-12): order, the tie, a rename from the wrong state, trimming, both name bounds, delete, cancel
    from a replay, a needs-replan drive replayed, the start not cut to 2 dp, the copy line, the cap;
  * THE DESTINATION (13-18): each reach bound, the longitude ignored, the cosine dropped, the tie, the farthest;
  * THE CONVERSION (19-23, 28-30): truncation and flooring for rounding, the ends dropped, lambda unrounded, the
    scale, the unplaced id, lambda dropped at the PlaceStore hop, the waypoints dropped by ClientPlanner;
  * THE ROW AND THE GATE (24-27): the re-plan note never shown, a rename losing its name, a replay while one is in
    flight, the budget unclamped.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "ScenicKit" / "Saved"
LIST = _DIR / "SavedList.swift"
DRAFT_SRC = _DIR / "SavedDraft.swift"
REPLAY = _DIR / "SavedReplay.swift"
ROW = _DIR / "SavedRow.swift"
SHEET = ROOT / "Sources" / "ScenicKit" / "PlanSheet" / "PlanSheet.swift"
DRIVE = ROOT / "Sources" / "PlaceStore" / "SavedDrive.swift"
SEGMENT = ROOT / "Sources" / "PlaceStore" / "SavedSegment.swift"
PLANNER = ROOT / "Sources" / "ScenicAPIClient" / "ClientPlanner.swift"
SUBJECTS = (LIST, DRAFT_SRC, REPLAY, ROW, SHEET, DRIVE, SEGMENT, PLANNER)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "Saved" / "SavedListTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "Saved" / "SavedReplayTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "SavedDraftTests.swift",
              ROOT / "Tests" / "PlaceStoreTests" / "SavedDriveUnresolvedTests.swift")

TRANSITIONS = "every state x every event lands whole: the moves as written, everything else unchanged and quiet"
NEWEST = "rows are kept newest first, a tie broken by the higher id first"
RENAME = "a rename commits the trimmed name of 1...60 characters and nothing else"
COPY = "a refused replay has its own calm copy line"
NOENDS = "a drive missing either saved end cannot be replayed and is shown as needing a re-plan"
PRIV = ("P-PRIV-05: the Saved list never shows an address - a row holds no address and draws only its name and "
        "detail")
REACH = "the destination is found within 0.01 degrees on each axis, every bound inclusive, nothing past it"
NEAREST = ("the nearest place wins, distance east-west scaled by the latitude, a tie to the lower id, none from "
           "none")
TICKET = "P-SAFE-03: a replay is one ticket through the sheet's gate - the start at 2 dp, the place, the budget"
CLAMP = "a replay's budget is clamped to 0...180 at every bound, and a start off 2 dp leaves at 2 dp"
DRAFT = "PlanResponse -> preview -> SavedDraft by full equality: >5 dp rounded once, 5 dp kept, the ends, empty"
STORED = "5-dp points become unplaced segments in order, the whole drive and its integers equal"
REFUSED = "more than 5 dp is refused by field, never rounded a second time"

SORT = "self.rows = rows.sorted { ($0.createdAt, $0.id) > ($1.createdAt, $1.id) }"
RANGE = "guard (1...Self.maxNameLength).contains(name.count) else { return nil }"
CANCEL = ("        case .renaming, .confirmDelete, .needsReplan: state = .list\n"
          "        case .loading, .list, .replaying: return")
BOUNDS = "guard abs(dLat) <= reach, abs(dLon) <= reach else { continue }"
ROUND = "(value * scale).rounded() / scale"
CLAMPED = "budgetMinutes = min(max(saved.budgetMinutes, 0), Self.maxBudgetMinutes)"

MUTATIONS = [
    ("1 rows kept as they came", LIST, SORT, "self.rows = rows", [TRANSITIONS, NEWEST]),
    ("2 a tie to the lower id", LIST, SORT,
     "self.rows = rows.sorted { ($0.createdAt, -$0.id) > ($1.createdAt, -$1.id) }", [NEWEST]),
    ("3 a rename begun from any state", LIST, "guard case .list = state, let row = row(id) else { return }\n"
     "        state = .renaming(id, row.name)", "guard let row = row(id) else { return }\n"
     "        state = .renaming(id, row.name)", [TRANSITIONS]),
    ("4 a rename kept untrimmed", LIST, "let name = text.trimmingCharacters(in: .whitespacesAndNewlines)",
     "let name = text", [TRANSITIONS, RENAME]),
    ("5 one character past the cap", LIST, RANGE,
     "guard (1...Self.maxNameLength + 1).contains(name.count) else { return nil }", [RENAME]),
    ("6 an empty name kept", LIST, RANGE, "guard (0...Self.maxNameLength).contains(name.count) else { return nil }",
     [RENAME]),
    ("7 delete keeps only the deleted", LIST, "rows.removeAll { $0.id == id }", "rows.removeAll { $0.id != id }",
     [TRANSITIONS]),
    ("8 cancel ends a replay", LIST, CANCEL,
     "        case .renaming, .confirmDelete, .needsReplan, .replaying: state = .list\n"
     "        case .loading, .list: return", [TRANSITIONS]),
    ("9 a needs-replan drive replayed", LIST, "guard !row.needsReplan, let start = row.start",
     "guard let start = row.start", [TRANSITIONS]),
    ("10 the replay start not cut to 2 dp", LIST, "start: PlanSheet.twoDecimals(start)", "start: start",
     [TRANSITIONS]),
    ("11 the refused line changed", LIST, "Plan it fresh from the plan sheet.", "Plan it again.", [COPY]),
    ("12 the name cap at 80", LIST, "maxNameLength = 60", "maxNameLength = 80", [RENAME]),
    ("13 the latitude bound exclusive", REPLAY, BOUNDS, "guard abs(dLat) < reach, abs(dLon) <= reach else { continue }",
     [REACH]),
    ("14 the longitude ignored", REPLAY, BOUNDS, "guard abs(dLat) <= reach else { continue }", [REACH]),
    ("15 east-west unscaled", REPLAY, "let scale = cos(point.latitude * Double.pi / 180)", "let scale = 1.0",
     [NEAREST]),
    ("16 a tie to the higher id", REPLAY, "current.place.id < place.id", "current.place.id > place.id", [NEAREST]),
    ("17 the farthest wins", REPLAY, "current.distance < distance", "current.distance > distance", [NEAREST]),
    ("18 the reach doubled", REPLAY, "reach: Double = 0.01", "reach: Double = 0.02", [REACH]),
    ("19 truncation for rounding", DRAFT_SRC, ROUND, "(value * scale).rounded(.towardZero) / scale", [DRAFT]),
    ("20 flooring for rounding", DRAFT_SRC, ROUND, "(value * scale).rounded(.down) / scale", [DRAFT]),
    ("21 the route ends dropped", DRAFT_SRC, "([first] + preview.waypoints + [last])",
     "([first] + preview.waypoints)", [DRAFT]),
    ("22 lambda unrounded", DRAFT_SRC, "lambda: fiveDecimals(preview.lambda)", "lambda: preview.lambda", [DRAFT]),
    ("23 four decimals", DRAFT_SRC, "scale: Double = 100_000", "scale: Double = 10_000", [DRAFT]),
    ("24 the re-plan note never shown", ROW, "needsReplan ? \"Needs a re-plan", "false ? \"Needs a re-plan",
     [PRIV]),
    ("25 a rename loses its name", ROW, "SavedRow(id: id, name: newName,", "SavedRow(id: id, name: name,",
     [TRANSITIONS, RENAME]),
    ("26 a replay while one is in flight", SHEET,
     "        if case .planning = state { return nil }\n        start = PlanPlace(id: 0",
     "        start = PlanPlace(id: 0", [TICKET]),
    ("27 the replay budget unclamped", SHEET, CLAMPED, "budgetMinutes = saved.budgetMinutes", [CLAMP]),
    ("28 the unplaced id a real one", SEGMENT, "unplaced: Int64 = -1", "unplaced: Int64 = 0", [STORED]),
    ("29 lambda dropped at the store hop", DRIVE, "segments: segments, lambda: lambda,", "segments: segments, lambda: 0,",
     [STORED, REFUSED]),
    ("30 the waypoints dropped", PLANNER, "waypoints: response.waypoints,", "waypoints: [],", [DRAFT]),
    # 31-33: the pre-review pass's three unwritten mutants (T-0306 Log), each MISSED before its test row landed.
    ("31 a missing start replayed from the end", LIST, "let start = row.start, let end = row.end",
     "let start = row.start ?? row.end, let end = row.end", [NOENDS]),
    ("32 a half-way tie rounded to even", DRAFT_SRC, ROUND, "(value * scale).rounded(.toNearestOrEven) / scale",
     [DRAFT]),
    ("33 the name cap counted in scalars", LIST, "contains(name.count)", "contains(name.unicodeScalars.count)",
     [RENAME]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 an empty route checked twice", DRAFT_SRC,
     "guard let first = preview.route.first, let last = preview.route.last else { return nil }",
     "guard !preview.route.isEmpty, let first = preview.route.first, let last = preview.route.last else { return nil }",
     "route.first and route.last are non-nil exactly when route is non-empty, so the added clause decides nothing"),
]

MIN_MUTATIONS = 33
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 4
