"""The mutation population for T-0359: the /search client's request (Sources/ScenicAPIClient/SearchClient.swift), the
device's query check and 2 dp rounding (SearchRequestBody.swift), the reply -> outcome table and the fail-closed
results read (SearchReplyReader.swift) and the result row (SearchResult.swift). Driver search.py, runner search_run.py
(ledger's three-file shape). SearchOutcome.swift is a case list with no code: allowlisted with that reason.

  * THE ROUNDING (1-5): dropped, toward zero, -0 kept, three decimals, the lat limit widened;
  * THE BOUNDS (6-8): the lower bound opened, the upper bound opened, the upper bound dropped;
  * THE QUERY (9-14): 101 units, characters for UTF-16 units, DEL admitted, the C0 bound narrowed, U+FEFF as text,
    the whitespace check dropped;
  * THE REQUEST (15-18): slashes escaped, the device header dropped, the path, a retry;
  * THE READER (19-28): the row limit, the count check, a blank label, each coordinate bound, the 429/502/503 bodies
    ignored, lat and lon swapped;
  * THE ROW (29): the coordinate stored swapped.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

CLIENT = ROOT / "Sources" / "ScenicAPIClient" / "SearchClient.swift"
BODY = ROOT / "Sources" / "ScenicAPIClient" / "SearchRequestBody.swift"
READER = ROOT / "Sources" / "ScenicAPIClient" / "SearchReplyReader.swift"
RESULT = ROOT / "Sources" / "ScenicAPIClient" / "SearchResult.swift"
SUBJECTS = (CLIENT, BODY, READER, RESULT)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicAPIClientTests" / "SearchClientTests.swift",)

REQUEST = "POST /search is exactly the content type, the device and the sorted-key body, the bias at 2 dp"
REFUSED = "A query or bias the Worker would refuse is refused on the device and nothing is sent"
TABLE = "Every Worker answer is one typed outcome after exactly one request - never a retry"
OFFLINE = "No reply at all is offline, after exactly one request"

ROUND = "return (value * 100).rounded() / 100 + 0.0"
SEND = "return SearchReplyReader.read(try await transport.send(request))"

MUTATIONS = [
    ("1 the 2 dp rounding dropped", BODY, ROUND, "return value + 0.0", [REQUEST]),
    ("2 rounding toward zero", BODY, ROUND, "return (value * 100).rounded(.towardZero) / 100 + 0.0", [REQUEST]),
    ("3 -0 kept", BODY, ROUND, "return (value * 100).rounded() / 100", [REQUEST]),
    ("4 three decimals", BODY, ROUND, "return (value * 1000).rounded() / 1000 + 0.0", [REQUEST]),
    ("5 the latitude limit widened to 180", BODY, "twoDecimals(near.latitude, limit: 90)",
     "twoDecimals(near.latitude, limit: 180)", [REFUSED]),
    ("6 the lower bound opened", BODY, "value >= -limit,", "value > -limit,", [REQUEST]),
    ("7 the upper bound opened", BODY, "value <= limit else", "value < limit else", [REQUEST]),
    ("8 the upper bound dropped", BODY, ", value <= limit else", " else", [REFUSED]),
    ("9 101 units admitted", BODY, "static let maxQueryUnits = 100", "static let maxQueryUnits = 101", [REFUSED]),
    ("10 characters counted, not UTF-16 units", BODY, "let units = query.utf16.count", "let units = query.count",
     [REFUSED]),
    ("11 DEL admitted", BODY, "$0.value < 0x20 || $0.value == 0x7F", "$0.value < 0x20", [REFUSED]),
    ("12 the C0 bound narrowed to 0x1F", BODY, "$0.value < 0x20 ||", "$0.value < 0x1F ||", [REFUSED]),
    ("13 U+FEFF read as text", BODY, "$0.properties.isWhitespace || $0.value == 0xFEFF",
     "$0.properties.isWhitespace", [REFUSED]),
    ("14 the whitespace-only check dropped", BODY,
     "return !scalars.allSatisfy { $0.properties.isWhitespace || $0.value == 0xFEFF }", "return true", [REFUSED]),
    ("15 slashes escaped", CLIENT, "[.sortedKeys, .withoutEscapingSlashes]", "[.sortedKeys]", [REQUEST]),
    ("16 the device header dropped", CLIENT, "IdentityHeaders.json(device: device, account: nil, bearer: nil)",
     '["content-type": "application/json"]', [REQUEST]),
    ("17 the path", CLIENT, 'appendingPathComponent("search")', 'appendingPathComponent("plan")', [REQUEST]),
    ("18 a retry", CLIENT, SEND, "_ = try? await transport.send(request)\n            " + SEND, [TABLE, OFFLINE]),
    ("19 nine rows admitted", READER, "static let limit = 8", "static let limit = 9", [TABLE]),
    ("20 the row count unchecked", READER, ", answer.results.count <= limit else {", " else {", [TABLE]),
    ("21 a blank label admitted", READER, "guard !row.label.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,",
     "guard !row.label.isEmpty,", [TABLE]),
    ("22 lat above 90 admitted", READER, "row.lat <= 90,", "row.lat <= 91,", [TABLE]),
    ("23 lat -90 refused", READER, "row.lat >= -90,", "row.lat > -90,", [TABLE]),
    ("24 lon below -180 admitted", READER, "row.lon >= -180,", "row.lon >= -181,", [TABLE]),
    ("25 lon 180 refused", READER, "row.lon <= 180 else", "row.lon < 180 else", [TABLE]),
    ("26 any 429 is the quota", READER, 'error(reply.body) == "quota_exhausted" ? .quotaExhausted : .unexpected(429)',
     ".quotaExhausted", [TABLE]),
    ("27 any 502 is search_failed", READER, 'error(reply.body) == "search_failed" ? .failed : .unexpected(502)',
     ".failed", [TABLE]),
    ("28 any other 503 is paused", READER, "default: return .unexpected(503)", "default: return .paused", [TABLE]),
    ("29 lat and lon swapped in the read", READER, "Coordinate(latitude: row.lat, longitude: row.lon)",
     "Coordinate(latitude: row.lon, longitude: row.lat)", [TABLE]),
    ("30 the row stores the coordinate swapped", RESULT, "self.coordinate = coordinate",
     "self.coordinate = Coordinate(latitude: coordinate.longitude, longitude: coordinate.latitude)", [TABLE]),
]

# Cannot change behaviour: anything but MISSED is a FAILURE. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 the isFinite guard dropped", BODY, "guard value.isFinite, value >= -limit", "guard value >= -limit",
     "NaN fails `value >= -limit`, +infinity fails `value <= limit` and -infinity fails `value >= -limit`: the two "
     "bounds already refuse every non-finite double"),
    ("E2 the one-unit floor dropped", BODY, "guard units >= 1, units <= maxQueryUnits", "guard units <= maxQueryUnits",
     "the only zero-unit string is empty, its scalars are empty, and allSatisfy over nothing is true - the "
     "whitespace-only check refuses it"),
]

MIN_MUTATIONS = 30
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 1
