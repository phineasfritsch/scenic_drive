"""The mutation population for T-0320's on-device corridor learner (Sources/ScenicKit/Traffic/*.swift). Driver
traffic.py, runner traffic_run.py (plansheet's three-file shape).

  * THE BADGE, P-SAFE-07 (1-4): the 5-sample bound moved or made strict, an unlearned edge not clearing the
    all-learned flag, an empty route read as learned;
  * THE EWMA (5-8): the weight, the weights swapped, the first sample not seeding, the count not advancing;
  * THE CLAMP (9-12): each bound moved one ulp outward, each side of the clamp dropped;
  * THE REFUSALS (13-15): zero accepted, each isFinite dropped;
  * THE HOUR (16-22): elapsed time not re-timed or not advancing, the weekday offset, the zone ignored, the
    HourOfWeek(_:) bounds, the slot keyed on a fixed hour;
  * RETIME AND THE VALUE TYPES (23-27): a ratio multiplied in, the ETA sum, a cell or a free-flow time not kept;
  * PRIVACY, P-PRIV-05 (28-29): a Codable conformance added to a learned-speed type.
  * PER SLOT AND IN THE LEARNER'S ZONE (30-33, T-0320 pre-review M1/M3): the badge counted over a cell's every
    hour or any learned hour of the cell, retime reading the hour in UTC or in the device's zone.
  * THE CLAMP AFTER THE EWMA (34-35, rv1-t0320 B1): the observation left raw and the STORED ratio clamped instead,
    at both record sites (the seed and the EWMA) or at the EWMA only.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "ScenicKit" / "Traffic"
LEARNER = _DIR / "LearnedCorridorSpeeds.swift"
HOUR = _DIR / "HourOfWeek.swift"
RATIO = _DIR / "CorridorRatio.swift"
ROUTE = _DIR / "RetimedRoute.swift"
SLOT = _DIR / "CorridorSlot.swift"
CELL = _DIR / "CorridorCell.swift"
EDGE = _DIR / "CorridorEdge.swift"
TIME_RUN = _DIR / "CorridorTimeRun.swift"
CROUTE = _DIR / "CorridorRoute.swift"
CLOCK = _DIR / "CorridorClock.swift"
PREVIEW = _DIR / "RetimedPreview.swift"
H3_BASE = _DIR / "H3BaseCells.swift"
H3_IJK = _DIR / "H3CoordIJK.swift"
H3_FACE = _DIR / "H3FaceProjection.swift"
H3_INDEX = _DIR / "H3IndexBuilder.swift"
SUBJECTS = (LEARNER, HOUR, RATIO, ROUTE, SLOT, CELL, EDGE, TIME_RUN, CROUTE, CLOCK, PREVIEW, H3_BASE, H3_IJK, H3_FACE,
            H3_INDEX)
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "Traffic"
TEST_FILES = (_TESTS / "LearnedCorridorSpeedsTests.swift", _TESTS / "HourOfWeekTests.swift",
              _TESTS / "LearnedSpeedsPrivacyTests.swift", _TESTS / "CorridorCellTests.swift",
              _TESTS / "CorridorRouteTests.swift", _TESTS / "CorridorClockTests.swift", _TESTS / "RetimedPreviewTests.swift")

BADGE = "the estimate badge: on at 0 and 4 samples, off at 5 and 6, and on whenever another edge is unlearned"
EMPTY = "an empty route is an estimate with no edges"
EWMA = "the EWMA: the first sample seeds the ratio, the second moves it by alpha 0.25"
CLAMP = "the ratio clamp at 0.3 and 1.0, one ulp either side of each bound"
REFUSE = "NaN, infinite, zero and negative times are refused and change nothing"
CROSS = "departsAt: an edge entered after Sunday 23:59 reads Monday 00:00's ratio, and the hour shifts the ratio"
INIT = "HourOfWeek(_:) holds 0...167 and refuses -1, 168 and the Int extremes"
WRAP = "Sunday 23:00 is 167 and wraps to Monday 00:00 = 0; the zone decides the hour"
PRIVATE = "no learned-speed type is Encodable or Decodable"
# T-0325: the H3-8 cell, the corridor route, the clock and the preview.
CELLS = "every reference point's cell equals h3-py's latlng_to_cell at resolution 8, and at 5 as Telemetry's"
BOUNDS = "latitude -90 and 90 and longitude -180 and 180 are cells; one ulp outside, NaN and infinities are nil"
TILE = "runs tile the route edge for edge into corridor edges; every bound of the tiling refused"
SEGMENT = "a segment's edge is the last edge starting at or before it"
DRIVES = "a clean drive teaches every edge once; a skip, a detour, a late start, no arrival and a reroute do not"
COUNTS = "a fix after arrival teaches nothing more, and observe answers how many edges each fix taught"
PREVIEW_BADGE = "the badge: on at 0 and 4 samples, off at 5 and 6, on with one edge unlearned, and kept without runs"
FIVE = "five completed drives clear the badge and four do not"
_OFF_LINE = "            enteredAt = nil\n            previousOnLine = false\n"
_FINISH = "            finished = true\n        }\n        return taught"

_CLAMP = "min(Self.ceilingRatio, max(Self.floorRatio, freeFlowSeconds / actualSeconds))"
_EWMA = "(1 - Self.alpha) * prior.ratio + Self.alpha * observed"
_RETIME_HOUR = "HourOfWeek.of(departsAt.addingTimeInterval(elapsed), in: timeZone)"
_RECORD = "\n".join([
    "        let observed = min(Self.ceilingRatio, max(Self.floorRatio, freeFlowSeconds / actualSeconds))",
    "        let slot = CorridorSlot(cell: cell, hour: hourOfWeek)",
    "        if let prior = slots[slot] {",
    "            let ratio = (1 - Self.alpha) * prior.ratio + Self.alpha * observed",
    "            slots[slot] = CorridorRatio(ratio: ratio, samples: prior.samples + 1)",
    "        } else {",
    "            slots[slot] = CorridorRatio(ratio: observed, samples: 1)"])
_STORED_CLAMP = "min(Self.ceilingRatio, max(Self.floorRatio, %s))"
_RAW = _RECORD.replace(_CLAMP, "freeFlowSeconds / actualSeconds")
_GUARD = "guard actualSeconds.isFinite, freeFlowSeconds.isFinite, actualSeconds > 0, freeFlowSeconds > 0 else {"

MUTATIONS = [
    ("1 learned at 4 samples", LEARNER, "learnedSamples = 5", "learnedSamples = 4", [BADGE]),
    ("2 learned only above 5", LEARNER, "learned.samples >= Self.learnedSamples",
     "learned.samples > Self.learnedSamples", [BADGE]),
    ("3 an unlearned edge leaves the flag", LEARNER, "everyEdgeLearned = false", "_ = everyEdgeLearned", [BADGE]),
    ("4 an empty route is learned", LEARNER, "var everyEdgeLearned = !edges.isEmpty", "var everyEdgeLearned = true",
     [EMPTY]),
    ("5 alpha 0.3", LEARNER, "alpha = 0.25", "alpha = 0.3", [EWMA]),
    ("6 the EWMA weights swapped", LEARNER, _EWMA, "Self.alpha * prior.ratio + (1 - Self.alpha) * observed",
     [EWMA]),
    ("7 the first sample blended with free flow", LEARNER, "CorridorRatio(ratio: observed, samples: 1)",
     "CorridorRatio(ratio: (1 - Self.alpha) * Self.ceilingRatio + Self.alpha * observed, samples: 1)",
     [EWMA, CLAMP]),
    ("8 the count does not advance", LEARNER, "samples: prior.samples + 1", "samples: prior.samples", [EWMA, BADGE]),
    ("9 the floor one ulp lower", LEARNER, "floorRatio = 0.3", "floorRatio = 0.3.nextDown", [CLAMP]),
    ("10 the ceiling one ulp higher", LEARNER, "ceilingRatio = 1.0", "ceilingRatio = 1.0.nextUp", [CLAMP]),
    ("11 the ceiling dropped", LEARNER, _CLAMP, "max(Self.floorRatio, freeFlowSeconds / actualSeconds)", [CLAMP]),
    ("12 the floor dropped", LEARNER, _CLAMP, "min(Self.ceilingRatio, freeFlowSeconds / actualSeconds)", [CLAMP]),
    ("13 a zero actual time accepted", LEARNER, _GUARD,
     _GUARD.replace("actualSeconds > 0", "actualSeconds >= 0"), [REFUSE]),
    ("14 an infinite actual time accepted", LEARNER, _GUARD,
     _GUARD.replace("actualSeconds.isFinite, ", ""), [REFUSE]),
    ("15 an infinite free-flow time accepted", LEARNER, _GUARD,
     _GUARD.replace("freeFlowSeconds.isFinite, ", ""), [REFUSE]),
    ("16 elapsed advances by free flow", LEARNER, "elapsed += time", "elapsed += edge.freeFlowSeconds", [CROSS]),
    ("17 elapsed never advances", LEARNER, "elapsed += time", "elapsed += 0", [CROSS]),
    ("18 the weekday offset by one", HOUR, "((parts.weekday ?? 2) + 5) % 7", "((parts.weekday ?? 2) + 6) % 7",
     [WRAP, CROSS]),
    ("19 the zone ignored", HOUR, "calendar.timeZone = timeZone", "calendar.timeZone = TimeZone(secondsFromGMT: 0)!",
     [WRAP]),
    ("20 HourOfWeek admits 168", HOUR, "value < Self.count", "value <= Self.count", [INIT]),
    ("21 HourOfWeek admits -1", HOUR, "value >= 0", "value >= -1", [INIT]),
    ("22 the record slot on a fixed hour", LEARNER, "CorridorSlot(cell: cell, hour: hourOfWeek)",
     "CorridorSlot(cell: cell, hour: HourOfWeek(0)!)", [EWMA, CROSS]),
    ("23 the ratio multiplied in", LEARNER, "edge.freeFlowSeconds / learned.ratio",
     "edge.freeFlowSeconds * learned.ratio", [BADGE, CROSS]),
    ("24 the ETA drops the last edge", ROUTE, "edgeSeconds.reduce(0, +)", "edgeSeconds.dropLast().reduce(0, +)",
     [CROSS]),
    ("25 a slot keeps no hour", SLOT, "self.hour = hour", "self.hour = HourOfWeek(0)!", [CROSS]),
    ("26 every cell the same", CELL, "self.index = index", "self.index = 0", [BADGE]),
    ("27 the free-flow time doubled", EDGE, "self.freeFlowSeconds = freeFlowSeconds",
     "self.freeFlowSeconds = freeFlowSeconds * 2", [BADGE, CROSS]),
    ("28 CorridorRatio is Codable", RATIO, "CorridorRatio: Equatable, Sendable {",
     "CorridorRatio: Equatable, Sendable, Codable {", [PRIVATE]),
    ("29 RetimedRoute is Codable", ROUTE, "RetimedRoute: Equatable, Sendable {",
     "RetimedRoute: Equatable, Sendable, Codable {", [PRIVATE]),
    ("30 the badge counts a cell over every hour", LEARNER, "learned.samples >= Self.learnedSamples",
     "slots.filter({ $0.key.cell == edge.cell }).reduce(0, { $0 + $1.value.samples }) >= Self.learnedSamples",
     [BADGE]),
    ("31 the badge counts any learned hour of the cell", LEARNER, "learned.samples >= Self.learnedSamples",
     "slots.contains(where: { $0.key.cell == edge.cell && $0.value.samples >= Self.learnedSamples })", [BADGE]),
    ("32 retime reads the hour in UTC", LEARNER, _RETIME_HOUR,
     _RETIME_HOUR.replace("in: timeZone", "in: TimeZone(secondsFromGMT: 0)!"), [CROSS]),
    ("33 retime reads the device's zone", LEARNER, _RETIME_HOUR,
     _RETIME_HOUR.replace("in: timeZone", "in: TimeZone.current"), [CROSS]),
    ("34 the clamp after the EWMA at both record sites", LEARNER, _RECORD,
     _RAW.replace("CorridorRatio(ratio: ratio,", "CorridorRatio(ratio: " + _STORED_CLAMP % "ratio" + ",")
     .replace("CorridorRatio(ratio: observed,", "CorridorRatio(ratio: " + _STORED_CLAMP % "observed" + ","), [EWMA]),
    ("35 the clamp after the EWMA only, the seed raw", LEARNER, _RECORD,
     _RAW.replace("CorridorRatio(ratio: ratio,", "CorridorRatio(ratio: " + _STORED_CLAMP % "ratio" + ","),
     [EWMA, CLAMP]),
    # T-0325 (36-62): the H3-8 copy, CorridorRoute's tiling, CorridorClock's transitions, RetimedPreview.
    ("36 corridors at resolution 9", CELL, "public static let resolution = 8", "public static let resolution = 9",
     [CELLS, BOUNDS]),
    ("37 latitude 90 refused", CELL, "(-90...90).contains(latitudeDegrees)", "(-90..<90).contains(latitudeDegrees)",
     [BOUNDS]),
    ("38 longitude one ulp past 180 accepted", CELL, "(-180...180).contains(longitudeDegrees)",
     "(-180...180.0.nextUp).contains(longitudeDegrees)", [BOUNDS]),
    ("39 the Class III rotation never applied", H3_FACE, "if resolution % 2 == 1 {", "if resolution % 2 == 2 {",
     [CELLS]),
    ("40 sin 60 rounded", H3_IJK, "static let sin60 = 0.8660254037844386467637231707529361834714",
     "static let sin60 = 0.866", [CELLS]),
    ("41 the base cell rotation dropped", H3_BASE, "return (value / 8, value % 8)", "return (value / 8, 0)", [CELLS]),
    ("42 the resolution field shifted", H3_INDEX, "UInt64(resolution) << 52", "UInt64(resolution) << 51",
     [CELLS, BOUNDS]),
    ("43 a run from == to accepted", CROUTE, "run.to > run.from,", "run.to >= run.from,", [TILE]),
    ("44 a negative time accepted", CROUTE, "run.milliseconds >= 0 else", "run.milliseconds >= -1 else", [TILE]),
    ("45 runs past the last vertex accepted", CROUTE, "guard at == route.count - 1,", "guard at >= route.count - 1,",
     [TILE]),
    ("46 an all-zero route accepted", CROUTE, "timeRuns.contains(where: { $0.milliseconds > 0 })",
     "timeRuns.contains(where: { $0.milliseconds >= 0 })", [TILE]),
    ("47 a run's cell from its last vertex", CROUTE, "let cell = cells[run.from]", "let cell = cells[run.to]", [TILE]),
    ("48 adjacent runs in one cell never merge", CROUTE, "if let last = grouped.last, last.cell == cell {",
     "if let last = grouped.last, last.cell == cell, run.from < 0 {", [TILE, SEGMENT]),
    ("49 milliseconds read as centiseconds", CROUTE, "Double($0.milliseconds) / 1000", "Double($0.milliseconds) / 100",
     [TILE]),
    ("50 a segment at an edge's first vertex is the edge before", CROUTE, "firstVertices.lastIndex { $0 <= segment }",
     "firstVertices.lastIndex { $0 < segment }", [SEGMENT, DRIVES]),
    ("51 an entry after an off-line fix counted", CLOCK, "let clean = previousOnLine && now == current + 1",
     "let clean = now == current + 1", [DRIVES]),
    ("52 a skipped edge's neighbour counted", CLOCK, "let clean = previousOnLine && now == current + 1",
     "let clean = previousOnLine && now > current", [DRIVES]),
    ("53 an off-line fix does not spoil the edge", CLOCK, _OFF_LINE, "            previousOnLine = false\n", [DRIVES]),
    ("54 the first fix enters any edge", CLOCK, "enteredAt = now == 0 ? date : nil", "enteredAt = date", [DRIVES]),
    ("55 arrival at twice the threshold", CLOCK, "end.meters <= DriveSession.awayThresholdMeters",
     "end.meters <= 2 * DriveSession.awayThresholdMeters", [DRIVES]),
    ("56 a reroute ignored", CLOCK, "guard session.line.coordinates == route.coordinates else {", "guard true else {",
     [DRIVES]),
    ("57 the hour of the exit", CLOCK, "HourOfWeek.of(start, in: speeds.timeZone)",
     "HourOfWeek.of(stop, in: speeds.timeZone)", [DRIVES, COUNTS, FIVE]),
    ("58 arrival does not finish the drive", CLOCK, _FINISH, "        }\n        return taught", [COUNTS]),
    ("59 the badge stays the server's", PREVIEW, "etaIsEstimate: retimed.isEstimate",
     "etaIsEstimate: preview.etaIsEstimate", [PREVIEW_BADGE, FIVE]),
    ("60 the ETA stays the server's", PREVIEW, "etaSeconds: retimed.etaSeconds", "etaSeconds: preview.etaSeconds",
     [PREVIEW_BADGE, FIVE]),
    ("61 the hazards dropped", PREVIEW, "hazards: preview.hazards", "hazards: []", [PREVIEW_BADGE, FIVE]),
    ("62 a time run's milliseconds doubled", TIME_RUN, "self.milliseconds = milliseconds",
     "self.milliseconds = milliseconds * 2", [TILE]),
    # rv1-t0325 B1: only the last vertex arrives; a pin inside the last corridor edge is a leg end, not arrival.
    ("63 arrival ignores the last-vertex check", CLOCK,
     "let arrived = end.vertex == route.coordinates.count - 1 && end.meters <= DriveSession.awayThresholdMeters",
     "let arrived = end.meters <= DriveSession.awayThresholdMeters", [DRIVES, FIVE]),
]

EQUIVALENT = [
    ("E1 the clamp applied ceiling first", LEARNER, _CLAMP,
     "max(Self.floorRatio, min(Self.ceilingRatio, freeFlowSeconds / actualSeconds))",
     "floorRatio 0.3 < ceilingRatio 1.0 and the quotient is never NaN (both operands passed the finite, positive "
     "guard), so min-then-max and max-then-min clamp every value to the same number"),
]

MIN_MUTATIONS = 63
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 7
