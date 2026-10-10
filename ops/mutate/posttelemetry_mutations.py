"""The mutation population for T-0355: the device's POST /telemetry (Sources/Telemetry/TelemetryClient.swift) and its
body (TelemetryRequestBody.swift). Driver posttelemetry.py, runner posttelemetry_run.py (ledger's three-file shape).

  * THE BOUND (1-4): the capacity off the Worker's cap, the waiting bound off by one or gone, a batch of one;
  * THE WIRE (5-9): the path, the device header's case, the content type, the method, the body's key order;
  * FAIL-QUIET (10-13): a failed batch kept, a refused status kept, the in-flight guard gone, one post per record.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing function names (TelemetryClientTests has no display names), each must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

CLIENT = ROOT / "Sources" / "Telemetry" / "TelemetryClient.swift"
BODY = ROOT / "Sources" / "Telemetry" / "TelemetryRequestBody.swift"
SUBJECTS = (CLIENT, BODY)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "TelemetryTests" / "TelemetryClientTests.swift",)

EXACT = "everyEventPostsExactlyItsRequest()"
BOUND = "waitingBoundTable(waiting:)"
DROP = "everyOutcomeDropsTheBatch()"
CAP = "capacityIsTheWorkersCap()"
SEND = "_ = try? await transport.send(TelemetryRequest(url: url, method: \"POST\", headers: headers, body: body))"

MUTATIONS = [
    ("1 the capacity is not the Worker's cap", CLIENT, "public static let capacity = 20",
     "public static let capacity = 21", [CAP]),
    ("2 the waiting bound off by one", CLIENT, "guard waiting.count < Self.capacity else { return }",
     "guard waiting.count <= Self.capacity else { return }", [BOUND]),
    ("3 the waiting bound gone", CLIENT, "guard waiting.count < Self.capacity else { return }",
     "guard true else { return }", [BOUND]),
    ("4 a post carries one event and drops the rest", CLIENT, "let batch = waiting\n",
     "let batch = Array(waiting.prefix(1))\n", [BOUND]),
    ("5 the path", CLIENT, 'appendingPathComponent("telemetry")', 'appendingPathComponent("telemetry/v1")', [EXACT]),
    ("6 the device header keeps its case", CLIENT, "device.uuidString.lowercased()", "device.uuidString", [EXACT]),
    ("7 the content type gains a charset", CLIENT, '["content-type": "application/json",',
     '["content-type": "application/json; charset=utf-8",', [EXACT]),
    ("8 the method", CLIENT, 'method: "POST"', 'method: "PUT"', [EXACT]),
    ("9 the body's keys unsorted", BODY, "encoder.outputFormatting = [.sortedKeys]",
     "encoder.outputFormatting = []", [EXACT]),
    ("10 a thrown post keeps its batch", CLIENT, SEND,
     "if (try? await transport.send(TelemetryRequest(url: url, method: \"POST\", headers: headers, body: body))) "
     "== nil { waiting = batch + waiting; break }", [DROP]),
    ("11 a refused status keeps its batch", CLIENT, SEND,
     "if let code = try? await transport.send(TelemetryRequest(url: url, method: \"POST\", headers: headers, "
     "body: body)), code >= 400 { waiting = batch + waiting; break }", [DROP]),
    ("12 the in-flight guard gone", CLIENT, "guard !isSending else { return }", "guard true else { return }",
     [BOUND]),
    ("13 one post per record", CLIENT, SEND, SEND + "\n            break", [BOUND]),
]

# Equivalent: the body cannot fail to encode - TelemetryDataPoint holds Strings and Doubles that are whole numbers
# (TelemetryEvent.dataPoint writes Int-valued Doubles only), and JSONEncoder throws only for a non-finite Double -
# so the `else` branch is unreachable and leaving the loop there instead of continuing changes nothing.
EQUIVALENT = [
    ("E1 an unencodable batch ends the loop", CLIENT,
     "guard let body = try? TelemetryRequestBody.encode(batch) else { continue }",
     "guard let body = try? TelemetryRequestBody.encode(batch) else { break }", []),
]

MIN_MUTATIONS = 13
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 1
