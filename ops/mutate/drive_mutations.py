"""The mutation population for T-0317's drive session (Sources/ScenicKit/Drive): the off-route rule, the reroute's
contents, the online/offline request counts and the motion gate. Driver drive.py, runner drive_run.py
(tripsheet's three-file shape).

  * THE GATE (1-6): each half of the speed predicate, the bound's literal, the surface before a fix, the surface
    set by an unusable fix;
  * OFF-ROUTE (7-10, 26-28): the 50 m comparison, the 5 s comparison, the dwell restart, asking again while a
    reroute is out, the fix's position and time checks;
  * ONLINE AND OFFLINE (11-13, 19-20): offline asking, the online edge, guiding asking, the rejoin, the failure;
  * THE REQUEST (14-18, 21-25): a pin counted passed one segment early, the lambda dropped in the value and in the
    session, an arrival taken while guiding, a bad arrival kept, a non-finite lambda, a loop's closing leg, the
    projection's sign, a repeated pin, a one-point line.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_KIT = ROOT / "Sources" / "ScenicKit" / "Drive"
SESSION = _KIT / "DriveSession.swift"
LINE = _KIT / "DriveLine.swift"
SURFACE = _KIT / "DriveSurface.swift"
FIX = _KIT / "DriveFix.swift"
REQUEST = _KIT / "RerouteRequest.swift"
SUBJECTS = (SESSION, LINE, SURFACE, FIX, REQUEST)
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "Drive"
TEST_FILES = (_TESTS / "DriveSessionTests.swift", _TESTS / "DriveRerouteTests.swift",
              _TESTS / "DriveMotionGateTests.swift")

THRESHOLD = "P-NAV-01: 50 m exactly is on the line; the smallest distance above 50 m is away"
DWELL = "P-NAV-01: off-route needs 5 s away exactly; one ulp less is not; an on-line fix restarts the dwell"
ONCE = "P-NAV-01: online off-route asks exactly once; nothing more while the reroute is out"
OFFLINE = "P-NAV-01: offline off-route is rejoin mode with zero requests, for as long as it lasts"
GUIDING = "P-NAV-01: back online while guiding asks nothing"
FAILED = "P-NAV-01: a failed reroute is rejoin mode, not retried until the next offline-to-online edge"
UNUSABLE = "a fix that is not a real position or a real time changes nothing; each bound itself is a fix"
REMAINING = "P-NAV-01: the reroute carries exactly the pins not yet passed and the same lambda, over both variants"
OFFLINE_REMAINING = "P-NAV-01: offline, the same drive asks nothing; back online it asks for the same remaining pins"
ARRIVAL = "P-NAV-01: a landed reroute replaces the line and pins and keeps the lambda; the next reroute carries them"
BAD_ARRIVAL = "P-NAV-01: an unusable reroute reply is a failure - rejoin mode, line and pins kept"
INIT = "a session is built only over a real line whose pins are its vertices, in order, with a finite lambda"
LOOP = "P-NAV-01: a loop's closing leg beside its start does not count the pins as passed"
SPEED = "P-SAFE-09: above 4.5 m/s, or at an unknown speed, the drive shows only the one large action and voice"
BEFORE = "P-SAFE-09: before the first fix the drive shows the minimal surface"
EACH = "P-SAFE-09: each fix sets the surface by itself - no hysteresis is ruled"
MODES = "P-SAFE-09: the bound is the same off the line, offline in rejoin mode and while a reroute is out"
KEEPS = "P-SAFE-09: an unusable fix leaves the surface where it was"
RESTART = "P-NAV-01: a landed reroute restarts the dwell - the first fix away from the new line waits 5 s again"

GATE_OLD = "speed >= 0 && speed <= Self.motionGateMetersPerSecond"
SURFACE_SET = "surface = DriveSurface(speedMetersPerSecond: fix.speedMetersPerSecond)"
USABLE = "guard fix.isUsable else { return nil }"
OFFLINE_OLD = "        guard isOnline else {\n            mode = .rejoining\n            return nil\n        }"
BAD_OLD = "            mode = .rejoining\n            return false\n        }\n        line = next"

MUTATIONS = [
    ("1 a negative speed is a known one", SURFACE, GATE_OLD, "speed <= Self.motionGateMetersPerSecond",
     [SPEED, EACH]),
    ("2 exactly 4.5 m/s is moving", SURFACE, GATE_OLD, "speed >= 0 && speed < Self.motionGateMetersPerSecond",
     [SPEED, EACH, MODES]),
    ("3 the bound moved to 4.6", SURFACE, "motionGateMetersPerSecond: Double = 4.5",
     "motionGateMetersPerSecond: Double = 4.6", [SPEED, EACH]),
    ("4 a standstill is moving", SURFACE, GATE_OLD, "speed > 0 && speed <= Self.motionGateMetersPerSecond",
     [SPEED, EACH, MODES]),
    ("5 the full surface before any fix", SESSION, "var surface: DriveSurface = .minimal",
     "var surface: DriveSurface = .full", [BEFORE]),
    ("6 an unusable fix sets the surface", SESSION, USABLE + "\n        " + SURFACE_SET,
     SURFACE_SET + "\n        " + USABLE, [KEEPS]),
    ("7 exactly 50 m is away", SESSION, "fix.coordinate) <= Self.awayThresholdMeters",
     "fix.coordinate) < Self.awayThresholdMeters", [THRESHOLD]),
    ("8 exactly 5 s is not off-route", SESSION, "fix.timestamp - since >= Self.offRouteDwellSeconds",
     "fix.timestamp - since > Self.offRouteDwellSeconds", [DWELL, THRESHOLD, REMAINING]),
    ("9 an on-line fix keeps the dwell", SESSION, "            awaySince = nil\n            progressSegment = line",
     "            progressSegment = line", [DWELL]),
    ("10 asking again while a reroute is out", SESSION, "guard mode == .guiding else { return nil }",
     "guard mode != .rejoining else { return nil }", [ONCE]),
    ("11 offline asks", SESSION, OFFLINE_OLD, "        if !isOnline { mode = .rejoining }",
     [OFFLINE, OFFLINE_REMAINING]),
    ("12 online without an edge asks", SESSION, "guard online, !wasOnline, mode == .rejoining",
     "guard online, mode == .rejoining", [FAILED]),
    ("13 back online while guiding asks", SESSION, "mode == .rejoining, let latest", "mode != .rerouting, let latest",
     [GUIDING]),
    ("14 a pin passed one segment early", SESSION, "pinVertices.firstIndex { $0 > progressSegment }",
     "pinVertices.firstIndex { $0 >= progressSegment }", [REMAINING, OFFLINE_REMAINING]),
    ("15 the value drops the lambda", REQUEST, "self.lambda = lambda", "self.lambda = 0.5", [REMAINING]),
    ("16 the session sends a fixed lambda", SESSION, "destination: line.destination, lambda: lambda)",
     "destination: line.destination, lambda: 0.5)", [REMAINING]),
    ("17 an arrival taken while guiding", SESSION, "guard mode == .rerouting else { return false }",
     "guard mode != .rejoining else { return false }", [ARRIVAL]),
    ("18 a bad arrival keeps rerouting", SESSION, BAD_OLD,
     "            return false\n        }\n        line = next", [BAD_ARRIVAL]),
    ("19 back on the line stays rejoining", SESSION, "if mode == .rejoining { mode = .guiding }",
     "if mode == .rerouting { mode = .guiding }", [OFFLINE]),
    ("20 a failed reroute stays rerouting", SESSION, "if mode == .rerouting { mode = .rejoining }",
     "if mode == .rejoining { mode = .rejoining }", [FAILED]),
    ("21 an infinite lambda accepted", SESSION, "guard lambda.isFinite,", "guard !lambda.isNaN,", [INIT]),
    ("22 progress jumps to a loop's closing leg", LINE, "guard d <= threshold else { break }",
     "guard d <= threshold else { next += 1; continue }", [LOOP]),
    ("23 the projection's sign flipped", LINE, "-(ax * dx + ay * dy) / length2", "(ax * dx + ay * dy) / length2",
     [REMAINING]),
    ("24 a repeated pin matches one vertex", LINE, "from = found + 1", "from = found", [INIT]),
    ("25 a one-point line", LINE, "coordinates.count >= 2", "coordinates.count >= 1", [INIT]),
    ("26 longitude 180 is not a fix", FIX, "(-180...180).contains(coordinate.longitude)",
     "(-180..<180).contains(coordinate.longitude)", [UNUSABLE]),
    ("27 a non-finite time is a fix", FIX, " && timestamp.isFinite", "", [UNUSABLE]),
    ("28 a line vertex past the pole", LINE, "(-90...90).contains(c.latitude)", "(-90...90.5).contains(c.latitude)",
     [INIT]),
    ("29 a landed reroute keeps the dwell", SESSION, "        progressSegment = 0\n        awaySince = nil\n",
     "        progressSegment = 0\n", [RESTART]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 a zero-length segment by inequality", LINE, "let t = length2 > 0 ?", "let t = length2 != 0 ?",
     "length2 is dx*dx + dy*dy over finite metres (every vertex and fix is checked finite and in range), so it is "
     "never negative and never NaN; > 0 and != 0 agree on every value it can take"),
]

MIN_MUTATIONS = 28
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 3
