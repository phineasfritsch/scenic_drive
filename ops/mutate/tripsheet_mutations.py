"""The mutation population for T-0313's road trip in the app: the trip sheet's state machine (Sources/ScenicKit/
TripSheet/TripSheet.swift) and its failure lines, the /trip client (TripRequestBody, TripClient, TripReplyReader,
TripError, TripResponse, TripResponseDay, ClientTripPlanner under Sources/ScenicAPIClient) and the per-day Apple Maps
split (Sources/Handoff/TripDayHandoff.swift). Driver tripsheet.py, runner tripsheet_run.py (savedlist's shape).

  * THE MACHINE (1-16): the disclaimer gate, each bound of days and percent, each half of the clamp, the 2-dp cut
    per axis, edit from a failure, a stale finish, a second ticket in flight, edits during planning, the fields
    swapped, two failures sharing a line;
  * THE REQUEST (17-24, 30-32): each origin bound, the 2-dp check per axis, days and vehicle unchecked, the percent
    widened, the wire names, a retry, the path, the device header;
  * THE OUTCOMES (25-29, 33-38): a status mapped to the wrong case, the quota date, the 5xx band, the refusal's
    failure, the leg and the full flag lost, an unknown view, [lon, lat] swapped, a long point, the night dropped;
  * THE HANDOFF (39-43): the last vertex pinned, one step per pin, ten waypoints, the wrong split destination, a pin
    dropped at a split.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_KIT = ROOT / "Sources" / "ScenicKit" / "TripSheet"
_API = ROOT / "Sources" / "ScenicAPIClient"
SHEET = _KIT / "TripSheet.swift"
FAILURE = _KIT / "TripFailure.swift"
BODY = _API / "TripRequestBody.swift"
READER = _API / "TripReplyReader.swift"
ERROR = _API / "TripError.swift"
CLIENT = _API / "TripClient.swift"
PLANNER = _API / "ClientTripPlanner.swift"
RESPONSE = _API / "TripResponse.swift"
DAY = _API / "TripResponseDay.swift"
HANDOFF = ROOT / "Sources" / "Handoff" / "TripDayHandoff.swift"
SUBJECTS = (SHEET, FAILURE, BODY, READER, ERROR, CLIENT, PLANNER, RESPONSE, DAY, HANDOFF)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "TripSheet" / "TripSheetTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "TripClientRequestTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "TripClientOutcomeTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "TripSheetGateTests.swift",
              ROOT / "Tests" / "HandoffTests" / "TripDayHandoffTests.swift")

EVERY = "every state x every event lands whole"
GATE = "P-SAFE-03: no trip ticket before the disclaimer is accepted, one after"
GATE_WIRE = "P-SAFE-03: no trip request is made before the disclaimer is accepted"
DAYS = "days are held to 1...5 at every bound"
PERCENT = "the extra-time percent is held to 0...40 at every bound"
CUT = "P-PRIV-05: the ticket carries the start cut to 2 dp on each axis, and the chosen days and percent"
LINES = "every trip failure has its own calm line"
BOUNDS = "every bound: refused on the device with 0 requests, or sent once exactly as written"
WIRE = "the /trip request is exactly the whitelisted body, sent once"
OUTCOME = "every Worker answer is one typed outcome from one request"
OFFLINE = "an unreachable Worker is routingOffline after exactly one attempt"
MAPPING = "every trip error is the sheet's failure of the same name"
FULL = "a full answer carries each day's leg as its path"
PREVIEW = "a preview reaches the sheet as exactly its itinerary: no path, so no per-day handoff"
PINS = "a pin at the first vertex at or past each 20 km, never the ends"
LONG = "one long step past two multiples is one pin, and the next pin waits for the next multiple"
SPLIT = "a day splits into URLs of at most nine waypoints, chained end to start"

QUOTA_OLD = ("guard let text = body?.resetsAt, let resetsAt = PlanResponseReader.instant(text) else {\n"
             "                return .unexpectedResponse(status: status)\n            }\n"
             "            return .quotaExhausted(resetsAt: resetsAt)")
RETRY_OLD = "            reply = try await transport.send(request)\n        } catch {\n            throw .routingOffline\n        }"
RETRY_NEW = ("            reply = try await transport.send(request)\n        } catch {\n"
             "            guard let again = try? await transport.send(request) else { throw .routingOffline }\n"
             "            reply = again\n        }")

MUTATIONS = [
    ("1 a ticket without the disclaimer", SHEET, "guard disclaimerAccepted, let start, let destination",
     "guard let start, let destination", [GATE, GATE_WIRE]),
    ("2 days upper bound widened", SHEET, "dayRange = 1...5", "dayRange = 1...6", [DAYS]),
    ("3 days lower bound widened", SHEET, "dayRange = 1...5", "dayRange = 0...5", [DAYS]),
    ("4 percent upper bound widened", SHEET, "extraPercentRange = 0...40", "extraPercentRange = 0...41", [PERCENT]),
    ("5 percent lower bound widened", SHEET, "extraPercentRange = 0...40", "extraPercentRange = -1...40", [PERCENT]),
    ("6 the clamp drops its ceiling", SHEET, "min(max(value, range.lowerBound), range.upperBound)",
     "max(value, range.lowerBound)", [DAYS, PERCENT]),
    ("7 the clamp drops its floor", SHEET, "min(max(value, range.lowerBound), range.upperBound)",
     "min(value, range.upperBound)", [DAYS, PERCENT]),
    ("8 the latitude not cut to 2 dp", SHEET, "(coordinate.latitude * 100).rounded() / 100", "coordinate.latitude",
     [CUT]),
    ("9 the longitude not cut to 2 dp", SHEET, "(coordinate.longitude * 100).rounded() / 100",
     "coordinate.longitude", [CUT]),
    ("10 edit from a failure stays failed", SHEET, "case .itinerary, .failed: settle()",
     "case .itinerary: settle()\n        case .failed: return", [EVERY]),
    ("11 a stale ticket's answer lands", SHEET,
     "guard case .planning(let inFlight) = state, inFlight == ticket else { return }",
     "guard case .planning = state else { return }", [EVERY]),
    ("12 a second ticket while one is in flight", SHEET, "case .idle, .searching, .planning: return nil",
     "case .planning: break\n        case .idle, .searching: return nil", [EVERY]),
    ("13 days changed while planning", SHEET, "if case .planning = state { return }\n        days = Self.clamp",
     "days = Self.clamp", [EVERY]),
    ("14 a search while planning", SHEET,
     "if case .planning = state { return }\n        state = .searching(field, query)",
     "state = .searching(field, query)", [EVERY]),
    ("15 the chosen place lands in the other field", SHEET,
     "case .destination: destination = place\n        case .start: start = place",
     "case .destination: start = place\n        case .start: destination = place", [EVERY]),
    ("16 two failures share a line", FAILURE,
     'case .planRefused: return "We could not settle on a scenic way this time. Try again."',
     'case .planRefused: return "We could not find a road trip between these two places."', [LINES]),
    ("17 the latitude bound dropped", BODY, "guard (-90.0...90.0).contains(origin.latitude), ", "guard ",
     [BOUNDS]),
    ("18 the longitude bound dropped", BODY, ", (-180.0...180.0).contains(origin.longitude) else", " else",
     [BOUNDS]),
    ("19 the 2-dp check on the latitude only", BODY,
     "guard atTwoDecimals(origin.latitude), atTwoDecimals(origin.longitude) else",
     "guard atTwoDecimals(origin.latitude) else", [BOUNDS]),
    ("20 days unchecked on the device", BODY,
     "guard dayRange.contains(days) else { return .failure(.daysOutOfRange) }", "", [BOUNDS]),
    ("21 the percent ceiling widened on the device", BODY, "static let extraPercentRange = 0...40",
     "static let extraPercentRange = 0...41", [BOUNDS]),
    ("22 the percent under another wire name", BODY, 'case extraBudgetPercent = "extra_budget_pct"',
     'case extraBudgetPercent = "extra_budget_percent"', [WIRE, BOUNDS]),
    ("23 the vehicle not sent", BODY, "try top.encode(vehicle.rawValue, forKey: .vehicle)", "", [WIRE, BOUNDS]),
    ("24 the vehicle unchecked", BODY, "guard vehicle.isEnabled else { return .failure(.vehicleNotEnabled) }", "",
     [BOUNDS]),
    ("25 too_few_days read as no route", READER, 'case (422, "too_few_days"?):\n            return .tooFewDays',
     'case (422, "too_few_days"?):\n            return .noRoute', [OUTCOME]),
    ("26 planning_unavailable read as paused", READER,
     'case (503, "planning_unavailable"?):\n            return .routingOffline',
     'case (503, "planning_unavailable"?):\n            return .planningPaused', [OUTCOME]),
    ("27 a quota answer without its date", READER, QUOTA_OLD,
     "return .quotaExhausted(resetsAt: Date(timeIntervalSince1970: 0))", [OUTCOME]),
    ("28 every 4xx read as offline", READER, "case (500...599, _):", "case (400...599, _):", [OUTCOME]),
    ("29 a device refusal shown as an invalid request", ERROR, "case .refusedOnDevice: return .refusedOnDevice",
     "case .refusedOnDevice: return .invalidRequest", [MAPPING]),
    ("30 a retry after a transport failure", CLIENT, RETRY_OLD, RETRY_NEW, [OFFLINE]),
    ("31 the request sent to /plan", CLIENT, 'base.appendingPathComponent("trip")',
     'base.appendingPathComponent("plan")', [WIRE, BOUNDS]),
    ("32 the device header not lowercased", CLIENT, "installID.installID().uuidString.lowercased()",
     "installID.installID().uuidString", [WIRE, BOUNDS]),
    ("33 a full day's path dropped", PLANNER, "path: $0.leg)", "path: nil)", [FULL]),
    ("34 the full flag lost", PLANNER, "TripItinerary(isFull: response.isFull,", "TripItinerary(isFull: false,",
     [FULL]),
    ("35 an unknown view accepted", RESPONSE, 'guard view == "preview" || view == "full" else {',
     "guard !view.isEmpty else {", [OUTCOME]),
    ("36 [lon, lat] read as [lat, lon]", RESPONSE, "Coordinate(latitude: pair[1], longitude: pair[0])",
     "Coordinate(latitude: pair[0], longitude: pair[1])", [OUTCOME]),
    ("37 a three-number point accepted", RESPONSE, "guard pair.count == 2 else", "guard pair.count >= 2 else",
     [OUTCOME]),
    ("38 the night's stop dropped", DAY, "            overnight = true", "            overnight = false",
     [OUTCOME, PREVIEW]),
    ("39 the last vertex pinned", HANDOFF, "for index in 1..<(path.count - 1)", "for index in 1..<path.count",
     [PINS, SPLIT]),
    ("40 one multiple stepped per pin", HANDOFF, "while next <= walked { next += pinSpacingMeters }",
     "next += pinSpacingMeters", [LONG]),
    ("41 ten waypoints in a part", HANDOFF, "while remaining.count > cap {", "while remaining.count > cap + 1 {",
     [SPLIT]),
    ("42 a part ends at its ninth pin", HANDOFF, "let stop = remaining[remaining.startIndex + cap]",
     "let stop = remaining[remaining.startIndex + cap - 1]", [SPLIT]),
    ("43 a pin dropped at each split", HANDOFF, "remaining = remaining.dropFirst(cap + 1)",
     "remaining = remaining.dropFirst(cap + 2)", [SPLIT]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 a two-point path walked", HANDOFF, "guard path.count > 2 else { return [] }",
     "guard path.count >= 2 else { return [] }",
     "with exactly two points the loop runs over 1..<1, which is empty, so the pins are [] either way"),
]

MIN_MUTATIONS = 43
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 5
