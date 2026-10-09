"""The mutation population for T-0317's drive session (Sources/ScenicKit/Drive): the off-route rule, the reroute's
contents, the online/offline request counts and the motion gate. Driver drive.py, runner drive_run.py
(tripsheet's three-file shape).

  * THE GATE (1-6): each half of the speed predicate, the bound's literal, the surface before a fix, the surface
    an unusable fix leaves (6, R4 of round 2);
  * OFF-ROUTE (7-10, 26-30): the 50 m comparison, the 5 s comparison, the dwell restart, asking again while a
    reroute is out, the fix's position and time checks, the dwell kept across a landed reroute, the cosine;
  * ONLINE AND OFFLINE (11-13, 19-20, 31): offline asking, the online edge, guiding asking, the rejoin, the
    failure, the lost edge while a reroute is out;
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
CONTROLLER = _KIT / "DriveController.swift"
LEG = _KIT / "DriveLeg.swift"
UNAVAILABLE = _KIT / "RerouteUnavailable.swift"
DISPLAY = _KIT / "DriveDisplay.swift"
# T-0328: the plan token's way through the app - the reply value, the preview, the sender, the preview's mapping.
REPLY = _KIT / "RerouteReply.swift"
PREVIEW = ROOT / "Sources" / "ScenicKit" / "PlanSheet" / "PlanPreview.swift"
CONTINUATION = ROOT / "Sources" / "ScenicKit" / "PlanSheet" / "PlanContinuation.swift"
REROUTER = ROOT / "Sources" / "ScenicAPIClient" / "PlanRerouter.swift"
PLANNER = ROOT / "Sources" / "ScenicAPIClient" / "ClientPlanner.swift"
VOICE = _KIT / "DriveVoice.swift"
SUBJECTS = (SESSION, LINE, SURFACE, FIX, REQUEST, CONTROLLER, LEG, UNAVAILABLE, DISPLAY, REPLY, PREVIEW, CONTINUATION,
            REROUTER, PLANNER, VOICE)
# NavAdapter (T-0321 R10) is mutated only by EQUIVALENT entries: apps/ios is not compiled on Linux, so those
# mutants are MISSED here by construction and only a device run observes them.
NAVIGATOR = ROOT / "apps" / "ios" / "Packages" / "ScenicApp" / "Sources" / "NavAdapter" / "DriveNavigator.swift"
MUTATED_FILES = SUBJECTS + (NAVIGATOR,)

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "Drive"
TEST_FILES = (_TESTS / "DriveSessionTests.swift", _TESTS / "DriveRerouteTests.swift",
              _TESTS / "DriveMotionGateTests.swift", _TESTS / "DriveControllerTests.swift",
              _TESTS / "DriveLegTests.swift", _TESTS / "DriveDisplayTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "DriveReplanTests.swift", _TESTS / "DriveTokenTakeTests.swift",
              _TESTS / "DriveVoiceTests.swift")

C_FIX = "T-0321: every fix reaches the session whole; off-route online is one send under ticket 1"
C_LOST = "T-0321: losing the connection with a reroute out cancels its ticket; with none out it cancels nothing"
C_REPLY = "T-0321: a late reply from before the drop is dropped; the reconnect's own reply is taken"
C_FAIL = "T-0321: a late failure from before the drop is dropped; the reconnect's own failure is rejoin mode"
C_IDLE = "T-0321: an answer with nothing in flight changes nothing, and a ticket is answered once"
C_SENDER = "T-0321: until T-0319 the sender asks nothing and fails, so an online off-route drive rejoins"
L_INNER = "T-0321: the legs cut the line at each inner pin, end at each pin, and the last arrives"
L_END = "T-0321: no pin, or a pin on the first or last vertex, cuts nothing - no leg is a single point"
L_REROUTE = "T-0321: a landed reroute's legs are cut at its own pins"
L_LEN = "T-0321: a leg's length is the sum of Geo's distances between its consecutive vertices"
D_TABLE = "P-SAFE-09: the drive screen shows the typed display for every surface and mode, compared whole"
D_LARGE = "P-SAFE-09: moving shows only the one large action - 60 pt, no details - in every mode"
D_SESSION = ("P-SAFE-09: the session's display is the table's row for its own surface and mode, before and "
             "after fixes")

R_TOKEN = "T-0328: token x first pin - the one 2-dp request and the taken answer, whole; no token, no request"
R_DRAWN = "T-0328: the answer DriveController takes is the Worker's line, pins and token, and the map draws it"
R_LATE = ("T-0328: the offline edge mid-flight cancels; the late answer is dropped by ticket and its token never "
          "taken")
R_OFFLINE = "T-0328: offline, an off-route drive sends nothing - zero commands, zero requests"
T_TAKE = ("T-0328: an answer's line, pins and token are taken together or none, whole, and the next "
          "request agrees")
R_PREVIEW = ("T-0328: the preview keeps /plan's token with the ticket's place and budget, only when sent, never "
             "saved")

V_TABLE = "P-SAFE-09: every mode change says the typed line or nothing, compared whole"
V_CUE = "P-SAFE-09: the leg cue at every distance bound, on a pin's leg and on the last leg, compared whole"
V_LEGEND = "P-SAFE-09: the leg end is the next pin past the progress, else the last vertex, measured along the line"
V_DRIVE = ("P-SAFE-09: a drive says each leg's approach once, the destination's approach, then the arrival - "
           "nothing else")
V_ARRIVAL = "P-SAFE-09: arriving first says only the arrival, and nothing after it"
V_QUIET = "P-SAFE-09: off the route the leg is quiet; leaving, failing and coming back each say their line once"
V_OFFLINE = ("P-SAFE-09: offline says head back; the reconnect is quiet; a landed reroute is a new line with its own "
             "cues")
V_ONLINE = "P-SAFE-09: a fix exactly 50 m from the line is on a leg; the next distance above it is on none"
V_ROUND = ("P-SAFE-09: a mode round trip on the same line repeats no cue - after a pin's approach, the "
           "destination's, or the arrival, online or offline")
V_PINLEG = ("P-SAFE-09: with a pin at every interior vertex, or none, only the pin's leg says the next stop and only "
            "the last says the destination")
V_LANDED = ("P-SAFE-09: a landed reroute after a pin's approach, the destination's, or the arrival says the new line's "
            "cues, online or offline")
V_BENT = ("P-SAFE-09: on a bent line the approach is measured along the line - quiet just above 400 m along it, "
          "though the crow flies under 400")

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
MINIMAL = "P-SAFE-09: an unusable fix is an unknown speed - the minimal surface, whatever it carries or followed"
RESTART = "P-NAV-01: a landed reroute restarts the dwell - the first fix away from the new line waits 5 s again"
EAST = ("P-NAV-01: against a north-south segment at latitude 34, 50 m east is on, the next distance up is away, "
        "42 m east is on")
LOST = "P-NAV-01: connectivity lost while a reroute is out is rejoin mode; the next online edge asks exactly once"

GATE_OLD = "speed >= 0 && speed <= Self.motionGateMetersPerSecond"
USABLE = "guard fix.isUsable else {\n            surface = .minimal\n            return nil\n        }"
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
    ("6 an unusable fix keeps the surface", SESSION, USABLE, "guard fix.isUsable else { return nil }", [MINIMAL]),
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
    ("16 the session sends a fixed lambda", SESSION, "destination: line.destination, lambda: lambda,",
     "destination: line.destination, lambda: 0.5,", [REMAINING]),
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
    ("30 the cosine dropped", LINE, "let scale = cos(point.latitude * Double.pi / 180) * Self.metersPerDegree",
     "let scale = Self.metersPerDegree", [EAST]),
    ("31 the lost edge keeps rerouting", SESSION, "        if !online, mode == .rerouting { mode = .rejoining }\n",
     "", [LOST]),
    ("32 the lost edge cancels nothing", CONTROLLER, "            commands.append(.cancel(ticket: lost))\n", "",
     [C_LOST, C_REPLY]),
    ("33 the lost edge keeps the ticket", CONTROLLER, "            inFlight = nil\n            commands.append(",
     "            commands.append(", [C_LOST]),
    ("34 a late reply taken", CONTROLLER,
     "        guard ticket == inFlight else { return false }\n        inFlight = nil\n        return session",
     "        inFlight = nil\n        return session", [C_REPLY]),
    ("35 a late failure taken", CONTROLLER,
     "        guard ticket == inFlight else { return false }\n        inFlight = nil\n        session.rerouteFailed()",
     "        inFlight = nil\n        session.rerouteFailed()", [C_FAIL, C_IDLE]),
    ("36 an arrival keeps the ticket", CONTROLLER, "        inFlight = nil\n        return session.rerouteArrived",
     "        return session.rerouteArrived", [C_REPLY]),
    ("37 a failure keeps the ticket", CONTROLLER, "        inFlight = nil\n        session.rerouteFailed()",
     "        session.rerouteFailed()", [C_FAIL]),
    ("38 tickets are not new", CONTROLLER, "        lastTicket += 1\n", "", [C_FIX]),
    ("39 a send leaves nothing in flight", CONTROLLER, "        inFlight = lastTicket\n", "", [C_FIX]),
    ("40 a fix not forwarded to the session", CONTROLLER, "guard let request = session.observe(fix) else",
     "guard let request = Optional<RerouteRequest>.none else", [C_FIX]),
    ("41 an online report cancels too", CONTROLLER, "if !online, let lost = inFlight {",
     "if let lost = inFlight {", [C_LOST]),
    ("42 the sender until the wire answers", UNAVAILABLE, "        throw self\n",
     "        return RerouteReply(line: [], waypoints: [])\n", [C_SENDER]),
    ("43 a pin on the first vertex cuts", LEG, "where cut > 0 && cut < last", "where cut >= 0 && cut < last",
     [L_END]),
    ("44 a pin on the last vertex cuts", LEG, "where cut > 0 && cut < last", "where cut > 0 && cut <= last",
     [L_END]),
    ("45 every leg starts at the start", LEG, "            start = cut\n", "", [L_INNER]),
    ("46 the last leg ends at a pin", LEG, "maneuver: GuidanceMapping.maneuver(for: .finish)",
     "maneuver: GuidanceMapping.maneuver(for: .reachedVia)", [L_INNER, L_END]),
    ("47 the legs ignore the pins", SESSION, "DriveLeg.split(line, at: pinVertices)", "DriveLeg.split(line, at: [])",
     [L_INNER, L_REROUTE]),
    ("48 a leg's length keeps the longest hop", LEG, "{ $0 + Geo.distanceMeters($1.0, $1.1) }",
     "{ max($0, Geo.distanceMeters($1.0, $1.1)) }", [L_LEN]),
    ("49 inner legs arrive", LEG, "maneuver: GuidanceMapping.maneuver(for: .reachedVia)))",
     "maneuver: GuidanceMapping.maneuver(for: .finish)))", [L_INNER]),
    # T-0324 R8: what the drive screen shows (DriveDisplay).
    ("50 the large action at the ordinary height", DISPLAY,
     "actionMinHeight = moving ? Self.largeActionHeight : Self.actionHeight", "actionMinHeight = Self.actionHeight",
     [D_TABLE, D_LARGE, D_SESSION]),
    ("51 moving shows the details", DISPLAY, "showsDetails = !moving", "showsDetails = true",
     [D_TABLE, D_LARGE, D_SESSION]),
    ("52 the surfaces swapped", DISPLAY, "let moving = surface == .minimal", "let moving = surface == .full",
     [D_TABLE, D_LARGE, D_SESSION]),
    ("53 rerouting captioned as rejoining", DISPLAY, 'case .rerouting: status = moving ? "Finding a new way"',
     'case .rerouting: status = moving ? "Head back to your route"', [D_TABLE, D_SESSION]),
    ("54 guiding carries a status", DISPLAY, "case .guiding: status = nil",
     'case .guiding: status = "Finding a new way"', [D_TABLE, D_SESSION]),
    ("55 the session's display ignores its surface", DISPLAY,
     "self.init(surface: session.surface, mode: session.mode,", "self.init(surface: .full, mode: session.mode,",
     [D_SESSION]),
    ("56 the session's display ignores its mode", DISPLAY,
     "self.init(surface: session.surface, mode: session.mode,", "self.init(surface: session.surface, mode: .guiding,",
     [D_SESSION]),
    ("57 the large action's literal", DISPLAY, "public static let largeActionHeight = 60.0",
     "public static let largeActionHeight = 44.0", [D_TABLE, D_LARGE, D_SESSION]),
    # T-0328: the app reroutes through the plan token (DriveReplanTests).
    ("58 the request drops the plan's token", SESSION, "lambda: lambda,\n" + " " * 30 + "planToken: planToken)",
     "lambda: lambda,\n" + " " * 30 + "planToken: nil)", [R_TOKEN, R_DRAWN, R_LATE]),
    ("59 a taken answer keeps the old token", SESSION,
     "        pinVertices = vertices\n        self.planToken = planToken", "        pinVertices = vertices",
     [R_TOKEN, R_LATE]),
    ("60 the session starts with no token", SESSION,
     "        self.isOnline = online\n        self.planToken = planToken", "        self.isOnline = online",
     [R_TOKEN, R_DRAWN, R_LATE]),
    ("61 the controller drops the answer's token", CONTROLLER, "planToken: reply.planToken)", "planToken: nil)",
     [R_TOKEN, R_LATE]),
    ("62 the reply value drops its token", REPLY, "self.planToken = planToken", "self.planToken = nil",
     [R_TOKEN, R_LATE]),
    ("63 the request value drops its token", REQUEST, "self.planToken = planToken", "self.planToken = nil",
     [R_TOKEN]),
    ("64 the sender asks without a token", REROUTER,
     "guard let token = request.planToken else { throw RerouteUnavailable() }",
     'let token = request.planToken ?? "00000000-0000-4000-8000-000000000000"', [R_TOKEN]),
    ("65 the sender asks with a fixed budget", REROUTER, "budgetMinutes: budgetMinutes)\n        return Self.reply",
     "budgetMinutes: 30)\n        return Self.reply", [R_TOKEN, R_LATE]),
    ("66 the sender's answer drops a vertex", REROUTER, "RerouteReply(line: response.route,",
     "RerouteReply(line: Array(response.route.dropFirst()),", [R_TOKEN, R_DRAWN]),
    ("67 the sender's answer drops its token", REROUTER, "planToken: response.planToken)", "planToken: nil)",
     [R_TOKEN, R_DRAWN]),
    ("68 the preview drops the token", PLANNER, "continuation: response.planToken.map {",
     "continuation: Optional<String>.none.map {", [R_PREVIEW]),
    ("69 the preview keeps a fixed budget", PLANNER,
     "PlanContinuation(token: $0, place: place, budgetMinutes: budgetMinutes)",
     "PlanContinuation(token: $0, place: place, budgetMinutes: 30)", [R_PREVIEW]),
    ("70 the planner hands the preview no place", PLANNER, "place: ticket.place, budgetMinutes: ticket.budgetMinutes))",
     "place: 0, budgetMinutes: ticket.budgetMinutes))", [R_PREVIEW]),
    ("71 the continuation drops its place", CONTINUATION, "self.place = place", "self.place = 0", [R_PREVIEW]),
    ("72 the display draws the plan's line", DISPLAY, "line: session.line.coordinates)", "line: [])",
     [R_DRAWN, D_SESSION]),
    ("73 the preview drops its continuation", PREVIEW, "self.continuation = continuation", "self.continuation = nil",
     [R_PREVIEW]),
    ("74 offline asks, through the sender", SESSION, OFFLINE_OLD, "        if !isOnline { mode = .rejoining }",
     [R_OFFLINE]),
    ("75 no token falls back to a fresh plan from the fix", REROUTER,
     "guard let token = request.planToken else { throw RerouteUnavailable() }",
     "guard let token = request.planToken else {\n            return Self.reply(of: try await client.plan("
     "from: request.origin, to: place, budgetMinutes: budgetMinutes))\n        }", [R_TOKEN]),
    # rv1-t0328: line, pins and token are taken together or none (DriveTokenTakeTests), at every take/refuse site.
    ("76 an answer with no token keeps the old token", SESSION,
     "        self.planToken = planToken\n        progressSegment = 0",
     "        self.planToken = planToken ?? self.planToken\n        progressSegment = 0", [T_TAKE]),
    ("77 a malformed answer's token is taken past the mode guard", SESSION,
     "        guard mode == .rerouting else { return false }\n",
     "        guard mode == .rerouting else { return false }; self.planToken = planToken\n", [T_TAKE]),
    ("78 a malformed answer's token is taken as it is refused", SESSION,
     "            mode = .rejoining\n            return false",
     "            mode = .rejoining\n            self.planToken = planToken\n            return false", [T_TAKE]),
    ("79 an answer's token is taken while not rerouting", SESSION,
     "guard mode == .rerouting else { return false }",
     "guard mode == .rerouting else { self.planToken = planToken; return false }", [T_TAKE]),
    ("80 a stale ticket's answer reaches the session", CONTROLLER,
     "        guard ticket == inFlight else { return false }\n        inFlight = nil\n        return session",
     "        guard ticket == inFlight else {\n            return session.rerouteArrived(line: reply.line, "
     "waypoints: reply.waypoints, planToken: reply.planToken)\n        }\n        inFlight = nil\n        return session",
     [C_REPLY, T_TAKE]),
    ("81 the controller keeps the old token for an untokened answer", CONTROLLER, "planToken: reply.planToken)",
     "planToken: reply.planToken ?? session.planToken)", [T_TAKE]),
    # T-0329 R2/R3/R8: what the drive says and when (DriveVoice, DriveSession.legEnd).
    ("82 the approach bound strict", VOICE, "guard meters <= approachMeters else", "guard meters < approachMeters else",
     [V_CUE]),
    ("83 the approach literal", VOICE, "public static let approachMeters = 400.0",
     "public static let approachMeters = 401.0", [V_CUE]),
    ("84 the arrival bound strict", VOICE, "if lastLeg, meters <= arrivalMeters", "if lastLeg, meters < arrivalMeters",
     [V_CUE]),
    ("85 the arrival on every leg", VOICE, "if lastLeg, meters <= arrivalMeters", "if meters <= arrivalMeters",
     [V_CUE]),
    ("86 the arrival literal", VOICE, "public static let arrivalMeters = 30.0", "public static let arrivalMeters = 31.0",
     [V_CUE]),
    ("87 every approach is a pin's", VOICE, "return lastLeg ? destinationLine : nextStopLine", "return nextStopLine",
     [V_CUE, V_DRIVE, V_OFFLINE]),
    ("88 the reconnect speaks", VOICE, "case (.rejoining, .rerouting): return nil",
     'case (.rejoining, .rerouting): return "Finding a new way."', [V_TABLE, V_OFFLINE]),
    ("89 the transition read backwards", VOICE, "Self.transition(from: mode, to: session.mode)",
     "Self.transition(from: session.mode, to: mode)", [V_QUIET, V_OFFLINE]),
    ("90 a leg spoken while rerouting", VOICE, "guard session.mode == .guiding, !arrived,", "guard !arrived,",
     [V_QUIET]),
    ("91 a landed reroute keeps the old cues", VOICE, "approached = []", "approached.formUnion([Int]())", [V_OFFLINE]),
    ("92 an approach repeated", VOICE, "} else if approached.insert(end.vertex).inserted {",
     "} else if approached.insert(end.vertex).inserted || true {", [V_DRIVE, V_QUIET]),
    ("93 speaking after the arrival", VOICE, "guard session.mode == .guiding, !arrived,",
     "guard session.mode == .guiding,", [V_DRIVE, V_ARRIVAL]),
    ("94 the leg's on-line bound strict", SESSION,
     "line.distanceMeters(from: at) <= Self.awayThresholdMeters else { return nil }",
     "line.distanceMeters(from: at) < Self.awayThresholdMeters else { return nil }", [V_ONLINE]),
    ("95 a leg end while away", SESSION,
     "guard let at = latest?.coordinate, line.distanceMeters(from: at) <= Self.awayThresholdMeters else",
     "guard let at = latest?.coordinate else", [V_ONLINE, V_QUIET]),
    ("96 the next pin skipped", SESSION, "pinVertices.first { $0 > progressSegment }",
     "pinVertices.first { $0 > progressSegment + 1 }", [V_LEGEND]),
    ("97 the segments to the leg end not summed", SESSION, "for vertex in (progressSegment + 1)..<end {",
     "for vertex in (progressSegment + 1)..<(progressSegment + 1) {", [V_LEGEND]),
    ("98 measured from the vertex behind", SESSION,
     "var meters = Geo.distanceMeters(at, line.coordinates[progressSegment + 1])",
     "var meters = Geo.distanceMeters(at, line.coordinates[progressSegment])", [V_LEGEND]),
    ("99 the arrival never said", VOICE, "if lastLeg, meters <= arrivalMeters {",
     "if lastLeg, meters <= arrivalMeters, meters > approachMeters {", [V_CUE, V_DRIVE, V_ARRIVAL]),
    # T-0329 pre-review: an utterance in a quiet state (a mode round trip on the SAME line) and the last-leg bound.
    ("100 a mode change forgets the approaches", VOICE,
     "if let change = Self.transition(from: mode, to: session.mode) { said.append(change) }",
     "if let change = Self.transition(from: mode, to: session.mode) { said.append(change); approached = [] }",
     [V_ROUND]),
    ("101 a mode change forgets the arrival", VOICE,
     "if let change = Self.transition(from: mode, to: session.mode) { said.append(change) }",
     "if let change = Self.transition(from: mode, to: session.mode) { said.append(change); arrived = false }",
     [V_ROUND]),
    ("102 the last leg one vertex early", VOICE, "lastLeg: end.vertex == session.line.segmentCount)",
     "lastLeg: end.vertex >= session.line.segmentCount - 1)", [V_PINLEG]),
    # rv1-t0329: the other half of a landed reroute's reset (RV1-M1), and the leg end on a bent line (RV1-M2).
    ("103 a landed reroute keeps the arrival", VOICE, "            approached = []\n            arrived = false\n",
     "            approached = []\n", [V_LANDED]),
    ("104 legEnd as the crow flies", SESSION, "        return (end, meters)\n",
     "        return (end, Geo.distanceMeters(at, line.coordinates[end]))\n", [V_BENT]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 a zero-length segment by inequality", LINE, "let t = length2 > 0 ?", "let t = length2 != 0 ?",
     "length2 is dx*dx + dy*dy over finite metres (every vertex and fix is checked finite and in range), so it is "
     "never negative and never NaN; > 0 and != 0 agree on every value it can take"),
    ("E2 (device-only) a fix not forwarded by the tap", NAVIGATOR,
     "tap.onLocations = { [weak self] locations in self?.forward(locations) }",
     "tap.onLocations = { _ in }", "apps/ios is never compiled on Linux, so this mutant is MISSED here by construction - it is NOT equivalent in behaviour; only a device or simulator run can observe it (T-0321 R10). What bounds it: the adapter line it edits is a one-line forward to DriveController, whose half is CAUGHT above (C_FIX, entry 40)"),
    ("E3 (device-only) the cancel not carried out", NAVIGATOR, "reroutes.removeValue(forKey: ticket)?.cancel()",
     "_ = reroutes.removeValue(forKey: ticket)", "apps/ios is never compiled on Linux, so this mutant is MISSED here by construction - it is NOT equivalent in behaviour; only a device or simulator run can observe it (T-0321 R10). What bounds it: the adapter line it edits is a one-line forward to DriveController, whose half is CAUGHT above (C_LOST, entries 32-33; a late answer is still dropped by ticket, entry 34)"),
    ("E4 (device-only) a late reply handed back under the ticket in flight", NAVIGATOR,
     "self?.arrived(ticket: ticket, reply: reply)",
     "self?.arrived(ticket: self?.controller.inFlight ?? ticket, reply: reply)", "apps/ios is never compiled on Linux, so this mutant is MISSED here by construction - it is NOT equivalent in behaviour; only a device or simulator run can observe it (T-0321 R10). What bounds it: the adapter line it edits is a one-line forward to DriveController, whose half is CAUGHT above (C_REPLY, entry 34)"),
    ("E6 (device-only) the navigator never speaks", NAVIGATOR,
     "for text in voice.utterances(after: controller.session) { speak(text) }", "_ = controller.session",
     "apps/ios is never compiled on Linux, so this mutant is MISSED here by construction - it is NOT equivalent in behaviour; only a device run hears it (T-0329). What bounds it: ops/lib/check-drive-voice.py (P-SAFE-09's row) allows exactly this whole line and refuses its removal by name ('the navigator never asks DriveVoice'), and what DriveVoice returns is CAUGHT above (entries 82-99)"),
]

MIN_MUTATIONS = 104
EQUIVALENT.append(
    ("E5 (device-only) the navigator's session starts without the preview's token", NAVIGATOR,
     "online: true, planToken: preview.continuation?.token)", "online: true)",
     "apps/ios is never compiled on Linux, so this mutant is MISSED here by construction - it is NOT equivalent in "
     "behaviour; only a device or simulator run can observe it (T-0328 R1). What bounds it: the adapter line it edits "
     "hands DriveSession the preview's token, whose session half is CAUGHT above (entry 60) and whose preview half is "
     "CAUGHT above (entries 68-71, 73)"))

MIN_EQUIVALENT = 6
MIN_TEST_FILES = 9
