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
SUBJECTS = (LEARNER, HOUR, RATIO, ROUTE, SLOT, CELL, EDGE)
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "Traffic"
TEST_FILES = (_TESTS / "LearnedCorridorSpeedsTests.swift", _TESTS / "HourOfWeekTests.swift",
              _TESTS / "LearnedSpeedsPrivacyTests.swift")

BADGE = "the estimate badge: on at 0 and 4 samples, off at 5 and 6, and on whenever another edge is unlearned"
EMPTY = "an empty route is an estimate with no edges"
EWMA = "the EWMA: the first sample seeds the ratio, the second moves it by alpha 0.25"
CLAMP = "the ratio clamp at 0.3 and 1.0, one ulp either side of each bound"
REFUSE = "NaN, infinite, zero and negative times are refused and change nothing"
CROSS = "departsAt: an edge entered after Sunday 23:59 reads Monday 00:00's ratio, and the hour shifts the ratio"
INIT = "HourOfWeek(_:) holds 0...167 and refuses -1, 168 and the Int extremes"
WRAP = "Sunday 23:00 is 167 and wraps to Monday 00:00 = 0; the zone decides the hour"
PRIVATE = "no learned-speed type is Encodable or Decodable"

_CLAMP = "min(Self.ceilingRatio, max(Self.floorRatio, freeFlowSeconds / actualSeconds))"
_EWMA = "(1 - Self.alpha) * prior.ratio + Self.alpha * observed"
_RETIME_HOUR = "HourOfWeek.of(departsAt.addingTimeInterval(elapsed), in: timeZone)"
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
]

EQUIVALENT = [
    ("E1 the clamp applied ceiling first", LEARNER, _CLAMP,
     "max(Self.floorRatio, min(Self.ceilingRatio, freeFlowSeconds / actualSeconds))",
     "floorRatio 0.3 < ceilingRatio 1.0 and the quotient is never NaN (both operands passed the finite, positive "
     "guard), so min-then-max and max-then-min clamp every value to the same number"),
]

MIN_MUTATIONS = 33
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 3
