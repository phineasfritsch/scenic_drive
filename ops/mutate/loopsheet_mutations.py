"""The mutation population for T-0314's loop in the app: the loop sheet's state machine (Sources/ScenicKit/LoopSheet/
LoopSheet.swift) and its failure lines, the /loop client (LoopRequestBody, LoopClient, LoopReplyReader, LoopError,
LoopResponse, ClientLoopPlanner under Sources/ScenicAPIClient) and the Apple Maps handoff (Sources/Handoff/
LoopHandoff.swift). Driver loopsheet.py, runner loopsheet_run.py (tripsheet's shape).

  * THE MACHINE (1-17): the disclaimer gate, a second ticket in flight, each bound of the dial and each half of the
    clamp, the init unclamped, the default, the 2-dp cut per axis, edit from a failure, a stale finish, edits while
    planning, the start not kept, a preview delivered as a failure, two failures sharing a line;
  * THE REQUEST (18-30): each start bound, the 2-dp check per axis, minutes and vehicle unchecked, the minutes floor,
    the wire names, the axes swapped, the vehicle not sent, a retry, the path, the device header;
  * THE OUTCOMES (31-44): a status mapped to the wrong case, the quota date, the 5xx band, the detail, [lon, lat]
    swapped, a long point, the waypoint cap each way, the waypoint axes, the error-to-failure map;
  * THE PREVIEW (45-49): the device's retrace check dropped or inverted, the server's fraction shown, the estimate
    badge hidden, the ticket's minutes not sent;
  * THE HANDOFF (50-53): the loop ending at its last pin, no source, pins cut to nine, pins reversed.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_KIT = ROOT / "Sources" / "ScenicKit" / "LoopSheet"
_API = ROOT / "Sources" / "ScenicAPIClient"
SHEET = _KIT / "LoopSheet.swift"
FAILURE = _KIT / "LoopFailure.swift"
BODY = _API / "LoopRequestBody.swift"
READER = _API / "LoopReplyReader.swift"
ERROR = _API / "LoopError.swift"
CLIENT = _API / "LoopClient.swift"
PLANNER = _API / "ClientLoopPlanner.swift"
RESPONSE = _API / "LoopResponse.swift"
HANDOFF = ROOT / "Sources" / "Handoff" / "LoopHandoff.swift"
SUBJECTS = (SHEET, FAILURE, BODY, READER, ERROR, CLIENT, PLANNER, RESPONSE, HANDOFF)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "LoopSheet" / "LoopSheetTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "LoopClientRequestTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "LoopClientOutcomeTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "LoopSheetGateTests.swift",
              ROOT / "Tests" / "HandoffTests" / "LoopHandoffTests.swift")

TABLE = "every state x every event lands whole"
GATE = "P-SAFE-03: no loop ticket before the disclaimer is accepted, one after"
DIAL = "the minutes dial is held to 10...180 at every bound, 45 by default"
PRIV = "P-PRIV-05: the ticket carries the start cut to 2 dp on each axis, and the dial's minutes"
LINES = "every loop failure has its own calm line"
REQUEST = "the /loop request is exactly the whitelisted body, one coordinate at 2 dp, sent once"
BOUNDS = "every bound: refused on the device with 0 requests, or sent once exactly as written"
OUTCOME = "every Worker answer is one typed outcome from one request"
OFFLINE = "an unreachable Worker is routingOffline after exactly one attempt"
MAPPING = "every loop error is the sheet's failure of the same name"
WIRE_GATE = "P-SAFE-03: no loop request is made before the disclaimer is accepted"
PREVIEW = "a clean loop reaches the sheet as exactly its preview, with the device's retrace fraction"
RETRACED = "a loop the device finds retraced is not shown: noCleanLoop"
FAILURES = "a spent day and a refused loop reach the sheet as their failures"
URL = "one URL from the start back to the start through the pins, in order"
TEN = "ten pins are refused, never cut to nine"

_CATCH = "            reply = try await transport.send(request)\n        } catch {\n            throw .routingOffline\n        }"
_RETRY = ("            reply = try await transport.send(request)\n        } catch {\n"
          "            guard let again = try? await transport.send(request) else { throw .routingOffline }\n"
          "            reply = again\n        }")
_QUOTA = ("            guard let text = body?.resetsAt, let resetsAt = PlanResponseReader.instant(text) else {\n"
          "                return .unexpectedResponse(status: status)\n            }")
_PIN = ("waypoints.append(Coordinate(latitude: try pin.decode(Double.self, forKey: .lat),\n"
        "                                        longitude: try pin.decode(Double.self, forKey: .lon)))")
_CHECK = ("guard let fraction = RetraceDetector.retraceFraction(response.route),\n"
          "              fraction <= RetraceDetector.maxRetraceFraction else { return .failure(.noCleanLoop) }")
_DIRECTIONS = "AppleMapsDirections(source: start, destination: start, waypoints: waypoints)"

MUTATIONS = [
    ("1 a ticket without the disclaimer", SHEET, "guard disclaimerAccepted, let start else { return nil }",
     "guard let start else { return nil }", [GATE, WIRE_GATE]),
    ("2 a second ticket while one is in flight", SHEET, "case .idle, .searching, .planning: return nil",
     "case .idle, .searching: return nil\n        case .planning: break", [TABLE]),
    ("3 the dial's floor at 9", SHEET, "public static let minuteRange = 10...180",
     "public static let minuteRange = 9...180", [DIAL]),
    ("4 the dial's ceiling at 181", SHEET, "public static let minuteRange = 10...180",
     "public static let minuteRange = 10...181", [DIAL]),
    ("5 the clamp's floor dropped", SHEET, "min(max(value, minuteRange.lowerBound), minuteRange.upperBound)",
     "min(value, minuteRange.upperBound)", [DIAL]),
    ("6 the clamp's ceiling dropped", SHEET, "min(max(value, minuteRange.lowerBound), minuteRange.upperBound)",
     "max(value, minuteRange.lowerBound)", [DIAL]),
    ("7 the init unclamped", SHEET, "self.minutes = Self.clamp(minutes)", "self.minutes = minutes", [DIAL]),
    ("8 the default at 60", SHEET, "public static let defaultMinutes = 45", "public static let defaultMinutes = 60",
     [DIAL, TABLE]),
    ("9 the latitude sent uncut", SHEET, "Coordinate(latitude: (coordinate.latitude * 100).rounded() / 100,",
     "Coordinate(latitude: coordinate.latitude,", [PRIV, GATE]),
    ("10 the longitude cut toward zero", SHEET, "longitude: (coordinate.longitude * 100).rounded() / 100)",
     "longitude: (coordinate.longitude * 100).rounded(.towardZero) / 100)", [PRIV]),
    ("11 edit from a failure stays", SHEET, "case .preview, .failed: settle()",
     "case .preview: settle()\n        case .failed: return", [TABLE]),
    ("12 a stale finish accepted", SHEET, "guard case .planning(let inFlight) = state, inFlight == ticket else { return }",
     "guard case .planning = state else { return }", [TABLE]),
    ("13 the dial moves while planning", SHEET,
     "        if case .planning = state { return }\n        minutes = Self.clamp(value)",
     "        minutes = Self.clamp(value)", [TABLE]),
    ("14 a search while planning", SHEET, "        if case .planning = state { return }\n        state = .searching(query)",
     "        state = .searching(query)", [TABLE]),
    ("15 the chosen start not kept", SHEET, "        start = place\n        settle()", "        settle()", [TABLE]),
    ("16 a preview delivered as a failure", SHEET, "case .preview(let preview): state = .preview(ticket, preview)",
     "case .preview: state = .failed(ticket, .noCleanLoop)", [PREVIEW]),
    ("17 two failures share a line", FAILURE,
     'case .noRoute: return "We could not find a loop from this start. Try another place."',
     'case .noRoute: return "We could not reach the planner. Check your connection and try again."', [LINES]),
    ("18 the latitude bound dropped", BODY,
     "guard (-90.0...90.0).contains(start.latitude), (-180.0...180.0).contains(start.longitude) else {",
     "guard (-180.0...180.0).contains(start.longitude) else {", [BOUNDS]),
    ("19 the longitude bound widened", BODY, "(-180.0...180.0).contains(start.longitude)",
     "(-181.0...181.0).contains(start.longitude)", [BOUNDS]),
    ("20 the latitude's 2 dp unchecked", BODY, "guard atTwoDecimals(start.latitude), atTwoDecimals(start.longitude) else {",
     "guard atTwoDecimals(start.longitude) else {", [BOUNDS]),
    ("21 the longitude's 2 dp unchecked", BODY,
     "guard atTwoDecimals(start.latitude), atTwoDecimals(start.longitude) else {",
     "guard atTwoDecimals(start.latitude) else {", [BOUNDS]),
    ("22 minutes unchecked", BODY, "guard minuteRange.contains(minutes) else { return .failure(.minutesOutOfRange) }",
     "", [BOUNDS]),
    ("23 the wire's minutes floor at 9", BODY, "static let minuteRange = 10...180", "static let minuteRange = 9...180",
     [BOUNDS]),
    ("24 the vehicle unchecked", BODY, "guard vehicle.isEnabled else { return .failure(.vehicleNotEnabled) }", "",
     [BOUNDS]),
    ("25 minutes under another wire name", BODY, "case start, lat, lon, minutes, vehicle",
     'case start, lat, lon, vehicle\n        case minutes = "duration_min"', [REQUEST, BOUNDS]),
    ("26 the longitude sent as lat", BODY, "try from.encode(start.latitude, forKey: .lat)",
     "try from.encode(start.longitude, forKey: .lat)", [REQUEST]),
    ("27 the vehicle not sent", BODY, "try top.encode(vehicle.rawValue, forKey: .vehicle)", "", [REQUEST]),
    ("28 a retry after a transport throw", CLIENT, _CATCH, _RETRY, [OFFLINE]),
    ("29 posted to /plan", CLIENT, 'base.appendingPathComponent("loop")', 'base.appendingPathComponent("plan")',
     [REQUEST, BOUNDS]),
    ("30 the device header uppercased", CLIENT, '"x-scenic-device": installID.installID().uuidString.lowercased()],',
     '"x-scenic-device": installID.installID().uuidString],', [REQUEST]),
    ("31 no_clean_loop read as noRoute", READER, "            return .noCleanLoop", "            return .noRoute",
     [OUTCOME, FAILURES]),
    ("32 region_unsupported unread", READER,
     'case (422, "region_unsupported"?):\n            return .regionUnsupported',
     'case (422, "region_unsupported"?):\n            return .unexpectedResponse(status: status)', [OUTCOME]),
    ("33 a 429 without a date accepted", READER, _QUOTA,
     "            let resetsAt = body?.resetsAt.flatMap { PlanResponseReader.instant($0) } ?? Date(timeIntervalSince1970: 0)",
     [OUTCOME]),
    ("34 the 5xx band unexpected", READER, "case (500...599, _):\n            return .routingOffline",
     "case (500...599, _):\n            return .unexpectedResponse(status: status)", [OUTCOME]),
    ("35 planning_paused read as offline", READER, 'case (503, "planning_paused"?):\n            return .planningPaused',
     'case (503, "planning_paused"?):\n            return .routingOffline', [OUTCOME]),
    ("36 the 400's detail dropped", READER, 'return .invalidRequest(detail: body?.detail ?? "")',
     'return .invalidRequest(detail: "")', [OUTCOME]),
    ("37 [lon, lat] read as [lat, lon]", RESPONSE, "points.append(Coordinate(latitude: pair[1], longitude: pair[0]))",
     "points.append(Coordinate(latitude: pair[0], longitude: pair[1]))", [OUTCOME, PREVIEW]),
    ("38 a three-number point accepted", RESPONSE, "guard pair.count == 2 else", "guard pair.count >= 2 else", [OUTCOME]),
    ("39 ten waypoints accepted", RESPONSE, "guard waypoints.count <= PlanWaypoints.maximum else",
     "guard waypoints.count <= PlanWaypoints.maximum + 1 else", [OUTCOME]),
    ("40 nine waypoints refused", RESPONSE, "guard waypoints.count <= PlanWaypoints.maximum else",
     "guard waypoints.count < PlanWaypoints.maximum else", [OUTCOME]),
    ("41 a waypoint's axes swapped", RESPONSE, _PIN,
     _PIN.replace("forKey: .lat)", "forKey: .TMP)").replace("forKey: .lon)", "forKey: .lat)").replace("forKey: .TMP)",
                                                                                                    "forKey: .lon)"),
     [OUTCOME, PREVIEW]),
    ("42 the waypoints decoded without the cap", RESPONSE,
     "guard waypoints.count <= PlanWaypoints.maximum else {",
     "guard waypoints.count <= PlanWaypoints.maximum || waypoints.count > 0 else {", [OUTCOME]),
    ("43 noCleanLoop shown as noRoute", ERROR, "case .noCleanLoop: return .noCleanLoop",
     "case .noCleanLoop: return .noRoute", [MAPPING, FAILURES]),
    ("44 a spent day shown as paused", ERROR, "case .quotaExhausted: return .quotaExhausted",
     "case .quotaExhausted: return .planningPaused", [MAPPING, FAILURES]),
    ("45 the device's retrace check dropped", PLANNER, _CHECK,
     "let fraction = RetraceDetector.retraceFraction(response.route) ?? response.retraceFraction", [RETRACED]),
    ("46 the retrace limit inverted", PLANNER, "fraction <= RetraceDetector.maxRetraceFraction",
     "fraction >= RetraceDetector.maxRetraceFraction", [PREVIEW, RETRACED]),
    ("47 the server's fraction shown", PLANNER, "retraceFraction: fraction,",
     "retraceFraction: response.retraceFraction,", [PREVIEW]),
    ("48 the estimate badge hidden", PLANNER, "etaIsEstimate: response.etaIsEstimate))", "etaIsEstimate: false))",
     [PREVIEW]),
    ("49 the ticket's minutes not sent", PLANNER, "client.loop(from: ticket.start, minutes: ticket.minutes)",
     "client.loop(from: ticket.start, minutes: LoopSheet.defaultMinutes)", [PREVIEW]),
    ("50 the loop ends at its last pin", HANDOFF, _DIRECTIONS,
     "AppleMapsDirections(source: start, destination: waypoints.last ?? start, waypoints: waypoints)", [URL]),
    ("51 the loop has no source", HANDOFF, _DIRECTIONS, "AppleMapsDirections(destination: start, waypoints: waypoints)",
     [URL]),
    ("52 the pins cut to nine", HANDOFF, _DIRECTIONS,
     "AppleMapsDirections(source: start, destination: start, waypoints: Array(waypoints.prefix(9)))", [TEN]),
    ("53 the pins reversed", HANDOFF, _DIRECTIONS,
     "AppleMapsDirections(source: start, destination: start, waypoints: waypoints.reversed())", [URL]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 edit's no-op cases as default", SHEET, "case .idle, .searching, .chosen, .planning: return",
     "default: return",
     "the switch over LoopSheetState already names .preview and .failed; the other four are exactly what default covers"),
]

MIN_MUTATIONS = 53
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 5
