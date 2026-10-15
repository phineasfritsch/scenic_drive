"""The mutation population for T-0360: the /waitlist client (Sources/ScenicAPIClient/WaitlistClient.swift), its
reply -> answer table (WaitlistReplyReader.swift) and the answers' copy (Sources/ScenicKit/PlanSheet/
WaitlistAnswer.swift). Driver waitlist.py, runner waitlist_run.py (ledger's three-file shape).

  * THE START'S BOUNDS (1-11): each half-bound deleted, widened by one ulp, made exclusive, checked after rounding;
  * THE TWO DECIMALS (12-16): no rounding, three decimals, banker's, truncation, the axes swapped;
  * THE CELL TEXT (17-26): the length check, each bound of both classes widened and narrowed, uppercase admitted;
  * ONCE PER CELL (27-29): the memory unread, remembered on every answer, never remembered;
  * THE REQUEST (30-35): the device id's case, an extra header, an extra body key, the path, the method, a retry;
  * THE ANSWERS (36-42): offline, 503, waitlisted false, any 200, the default, every 5xx, and two copy lines.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

CLIENT = ROOT / "Sources" / "ScenicAPIClient" / "WaitlistClient.swift"
READER = ROOT / "Sources" / "ScenicAPIClient" / "WaitlistReplyReader.swift"
ANSWER = ROOT / "Sources" / "ScenicKit" / "PlanSheet" / "WaitlistAnswer.swift"
SUBJECTS = (CLIENT, READER, ANSWER)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicAPIClientTests" / "WaitlistClientTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "PlanSheet" / "WaitlistAnswerTests.swift")

REQ = "POST /waitlist is exactly the content type, the device and {cell}"
ANS = "Every Worker answer is one WaitlistAnswer after exactly one request, remembered only when joined"
OFF = "No reply at all is offline, after exactly one request, and nothing is remembered"
BOUND = "Every bound of the start: exact bounds reach cellOf, anything outside is refused with zero requests"
TWO = "The cell is computed from the start at two decimals, half away from zero"
CELLREF = "A cell the Worker would refuse on its first test is refused on the device and nothing is sent"
CLASS = "Every hex position admits 0, 9, a and f - the bounds of both classes"
ONCE = ("Once per cell per install: a joined cell sends nothing again, another cell sends, "
        "a failed cell sends again")
LINES = "every WaitlistAnswer has its one line, whole"

GUARD = "guard start.latitude >= -90, start.latitude <= 90, start.longitude >= -180, start.longitude <= 180 else {"
CELL_CALL = "cellOf(Self.twoDecimals(start.latitude), Self.twoDecimals(start.longitude))"
CLASSES = "(48...57).contains($0) || (97...102).contains($0)"
SEND = "answer = WaitlistReplyReader.read(try await transport.send(request))"
BODY = r'Data("{\"cell\":\"\(cell)\"}".utf8)'


def cls(digits: str, lower: str) -> str:
    return "(%s).contains($0) || (%s).contains($0)" % (digits, lower)


MUTATIONS = [
    ("1 the latitude's lower bound deleted", CLIENT, "guard start.latitude >= -90, ", "guard ", [BOUND]),
    ("2 the latitude's upper bound deleted", CLIENT, "start.latitude <= 90, ", "", [BOUND]),
    ("3 the longitude's lower bound deleted", CLIENT, "start.longitude >= -180, ", "", [BOUND]),
    ("4 the longitude's upper bound deleted", CLIENT, ", start.longitude <= 180 else", " else", [BOUND]),
    ("5 the latitude's lower bound one ulp wide", CLIENT, "start.latitude >= -90,",
     "start.latitude >= (-90.0).nextDown,", [BOUND]),
    ("6 the latitude's upper bound one ulp wide", CLIENT, "start.latitude <= 90,",
     "start.latitude <= (90.0).nextUp,", [BOUND]),
    ("7 the longitude's lower bound one ulp wide", CLIENT, "start.longitude >= -180,",
     "start.longitude >= (-180.0).nextDown,", [BOUND]),
    ("8 the longitude's upper bound one ulp wide", CLIENT, "start.longitude <= 180 else",
     "start.longitude <= (180.0).nextUp else", [BOUND]),
    ("9 the latitude's lower bound exclusive", CLIENT, "start.latitude >= -90,", "start.latitude > -90,", [BOUND]),
    ("10 the longitude's upper bound exclusive", CLIENT, "start.longitude <= 180 else",
     "start.longitude < 180 else", [BOUND]),
    ("11 the range checked after rounding", CLIENT, GUARD,
     "guard Self.twoDecimals(start.latitude) >= -90, Self.twoDecimals(start.latitude) <= 90, "
     "Self.twoDecimals(start.longitude) >= -180, Self.twoDecimals(start.longitude) <= 180 else {", [BOUND]),
    ("12 the start sent to cellOf unrounded", CLIENT, CELL_CALL, "cellOf(start.latitude, start.longitude)", [TWO]),
    ("13 three decimals", CLIENT, "(degrees * 100).rounded() / 100", "(degrees * 1000).rounded() / 1000", [TWO]),
    ("14 banker's rounding", CLIENT, "(degrees * 100).rounded() / 100",
     "(degrees * 100).rounded(.toNearestOrEven) / 100", [TWO]),
    ("15 truncation", CLIENT, "(degrees * 100).rounded() / 100", "(degrees * 100).rounded(.towardZero) / 100",
     [TWO]),
    ("16 the axes swapped", CLIENT, CELL_CALL,
     "cellOf(Self.twoDecimals(start.longitude), Self.twoDecimals(start.latitude))", [TWO]),
    ("17 the cell's length unchecked", CLIENT, "hex.count == 15 && ", "", [CELLREF]),
    ("18 fourteen to sixteen digits admitted", CLIENT, "hex.count == 15 &&", "(14...16).contains(hex.count) &&",
     [CELLREF]),
    ("19 the digit class's lower bound wide", CLIENT, CLASSES, cls("47...57", "97...102"), [CELLREF]),
    ("20 the digit class's upper bound wide", CLIENT, CLASSES, cls("48...58", "97...102"), [CELLREF]),
    ("21 the letter class's lower bound wide", CLIENT, CLASSES, cls("48...57", "96...102"), [CELLREF]),
    ("22 the letter class's upper bound wide", CLIENT, CLASSES, cls("48...57", "97...103"), [CELLREF]),
    ("23 the digit class's lower bound narrow", CLIENT, CLASSES, cls("49...57", "97...102"), [CLASS]),
    ("24 the digit class's upper bound narrow", CLIENT, CLASSES, cls("48...56", "97...102"), [CLASS]),
    ("25 the letter class's lower bound narrow", CLIENT, CLASSES, cls("48...57", "98...102"), [CLASS]),
    ("26 the letter class's upper bound narrow", CLIENT, CLASSES, cls("48...57", "97...101"), [CLASS]),
    ("27 the memory unread", CLIENT, "if memory.hasJoined(cell) { return .alreadyJoined }", "", [ONCE]),
    ("28 remembered on every answer", CLIENT, "if answer == .joined { memory.rememberJoined(cell) }",
     "memory.rememberJoined(cell)", [ANS]),
    ("29 never remembered", CLIENT, "if answer == .joined { memory.rememberJoined(cell) }", "", [ONCE]),
    ("30 the device id's case kept", CLIENT, "installID.installID().uuidString.lowercased()",
     "installID.installID().uuidString", [REQ]),
    ("31 an account header beside it", CLIENT, '"content-type": "application/json",',
     '"content-type": "application/json", IdentityHeaders.accountHeader: "",', [REQ]),
    ("32 a coordinate beside the cell", CLIENT, BODY, r'Data("{\"cell\":\"\(cell)\",\"lat\":34.02}".utf8)', [REQ]),
    ("33 another path", CLIENT, 'appendingPathComponent("waitlist")', 'appendingPathComponent("waitlist/join")',
     [REQ]),
    ("34 another method", CLIENT, 'method: "POST"', 'method: "PUT"', [REQ]),
    ("35 a retry", CLIENT, SEND, "_ = try? await transport.send(request)\n            " + SEND, [ANS]),
    ("36 no reply read as failed", CLIENT, "return .offline", "return .failed", [OFF]),
    ("37 503 read as failed", READER, "case 503: return .unavailable", "case 503: return .failed", [ANS]),
    ("38 waitlisted false accepted", READER, "?.waitlisted == true ? .joined", "?.waitlisted != nil ? .joined",
     [ANS]),
    ("39 any 200 joined", READER, "case 200:\n", "case 200: return .joined\n        case 201:\n", [ANS]),
    ("40 the default unavailable", READER, "default: return .failed", "default: return .unavailable", [ANS]),
    ("41 every 5xx unavailable", READER, "case 503: return .unavailable", "case 500...599: return .unavailable",
     [ANS]),
    ("42 the already-joined line claims less", ANSWER, "counted this area. Nothing new was sent.",
     "counted this area. Nothing was sent.", [LINES]),
    ("43 the offline line claims more", ANSWER, "so this area may not be counted.", "so this area was not counted.",
     [LINES]),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 rounded() spelled with its rule", CLIENT, "(degrees * 100).rounded() / 100",
     "(degrees * 100).rounded(.toNearestOrAwayFromZero) / 100",
     "FloatingPoint.rounded() is documented as rounded(.toNearestOrAwayFromZero)"),
    ("E2 the length read from the string's view", CLIENT, "hex.count == 15 &&", "cell.utf8.count == 15 &&",
     "hex is Array(cell.utf8): the two counts are the same number"),
]

MIN_MUTATIONS = 43
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 2
