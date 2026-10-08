"""The mutation population for T-0310: the App Attest client and its reply table (Sources/ScenicAPIClient/
AttestClient.swift, AttestReplyReader.swift), the Keychain replace decisions (KeychainWrite.swift,
InstallIDDecision.swift, SessionRecord.swift), the session decision and store (SessionStep.swift, SessionStore.swift),
the ledger write (LedgerSurpriseSource.swift, LedgerClient.swift's 401 hand-back) and the shown-place record
(Sources/ScenicKit/Surprise/SurpriseShowing.swift). Driver session.py, runner session_run.py (ledger.py's shape).

  * THE CLIENT (1-6): the device header, its case, escaped slashes, the assert path, the assert body, offline;
  * THE READER (7-14): 400, the 429 body, 503, 405, an empty token, '+', the challenge expiry, the calls swapped;
  * THE KEYCHAIN (15-21): malformed added, a failed read written, the defaults copy, a valid id rewritten, the
    canonical check, escaped slashes, an empty token;
  * THE SESSION (22-31): the margin, the spent budget, a failed read, a malformed item, spent late, an unsupported
    attester, a rejected key kept, always add, another token's rejection, a rejection ignored;
  * THE LEDGER WRITE (32-36): another coordinate's cell, the read's nil, the 401 kept, the category, the feedback;
  * THE PRE-REVIEW HOLD-BACKS (37-39): MISSED before their rows landed (T-0310 Log), CAUGHT after;
  * THE PRE-REVIEW SURVIVOR (40): a place with no cell posted - MISSED before the no-cell place d landed, CAUGHT after.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

API = ROOT / "Sources" / "ScenicAPIClient"
CLIENT = API / "AttestClient.swift"
READER = API / "AttestReplyReader.swift"
WRITE = API / "KeychainWrite.swift"
INSTALL = API / "InstallIDDecision.swift"
RECORD = API / "SessionRecord.swift"
STEP = API / "SessionStep.swift"
STORE = API / "SessionStore.swift"
SOURCE = API / "LedgerSurpriseSource.swift"
LEDGER = API / "LedgerClient.swift"
SHOWING = ROOT / "Sources" / "ScenicKit" / "Surprise" / "SurpriseShowing.swift"
SUBJECTS = (CLIENT, READER, WRITE, INSTALL, RECORD, STEP, STORE, SOURCE, LEDGER, SHOWING)
MUTATED_FILES = SUBJECTS

TESTS = ROOT / "Tests" / "ScenicAPIClientTests"
TEST_FILES = (TESTS / "AttestClientTests.swift", TESTS / "KeychainDecisionTests.swift",
              TESTS / "SessionStoreTests.swift", TESTS / "SurpriseLedgerWriteTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "Surprise" / "SurpriseShowingTests.swift")

REQ = "Each App Attest request is exactly its URL, its one header and its sorted-key body"
TABLE = "Every Worker answer is one typed outcome after exactly one request - never a retry"
OFFLINE = "No reply at all is offline, after exactly one request"
REPLACE = "An item that exists is replaced - valid or malformed - an absent one added, a failed read left alone"
INSTALLID = "The install id's decision over every Keychain state, with and without a UserDefaults copy"
ITEM = "The session item is exactly {expires_at, key_id, token} and reads back as the record it was written from"
MALFORMED = "Any other item is malformed"
STEPS = "The session step over every stored state, spent and unspent"
FLOW = "Each stored state's token, requests and Keychain writes - and a second call adds no request"
REJECTED = "A rejected token is dropped and renewed once per launch; another token's rejection drops nothing"
SHOWINGS = "Each shown place is in the device history once, and posted with its own cell as the session allows"
PLACES = "The ledger's rows become the card's ledger places, in the Worker's order; any other answer is nil"
RECORDING = "A shown place is appended once a day, its category and corridor its own"

SORTED = "encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]"
MARGIN = "record.expiresAt.timeIntervalSince(now) > margin"

MUTATIONS = [
    ("1 the challenge without its device header", CLIENT,
     'headers: ["x-scenic-device": deviceID], body: Data()), call: .challenge)',
     "headers: [:], body: Data()), call: .challenge)", [REQ, FLOW]),
    ("2 the device id upper-case", CLIENT, "device.installID().uuidString.lowercased()",
     "device.installID().uuidString", [REQ]),
    ("3 the client's slashes escaped", CLIENT, SORTED, "encoder.outputFormatting = [.sortedKeys]", [REQ]),
    ("4 the assertion posted to /attest", CLIENT, 'appendingPathComponent("attest/assert")',
     'appendingPathComponent("attest")', [REQ]),
    ("5 the assertion body without keyId", CLIENT, '["assertion": assertion, "challenge": challenge, "keyId": keyId]',
     '["assertion": assertion, "challenge": challenge]', [REQ]),
    ("6 no reply read as unavailable", CLIENT, "return .offline", "return .unavailable", [OFFLINE]),
    ("7 a 400 unexpected", READER, "case 400: return .rejected", "case 400: return .unexpected(400)", [TABLE]),
    ("8 every 429 the challenge limit", READER,
     'failure?.error == "challenge_rate_limited" ? .rateLimited : .unexpected(429)', ".rateLimited", [TABLE]),
    ("9 a 503 unexpected", READER, "case 503: return .unavailable", "case 503: return .unexpected(503)", [TABLE]),
    ("10 a 405 a rejection", READER, "case 405: return .methodRefused", "case 405: return .rejected", [TABLE]),
    ("11 an empty token a session", READER,
     "decode(Session.self, from: body), !value.token.isEmpty,", "decode(Session.self, from: body),", [TABLE]),
    ("12 a challenge admits '+'", READER, "$0 == 45 || $0 == 95", "$0 == 45 || $0 == 95 || $0 == 43", [TABLE]),
    ("13 the challenge's expiry unread", READER,
     "isChallenge(value.challenge),\n              instant(value.expires_at) != nil else",
     "isChallenge(value.challenge) else", [TABLE]),
    ("14 the two calls' bodies swapped", READER, "call == .challenge ? challenge(reply.body)",
     "call == .session ? challenge(reply.body)", [TABLE]),
    ("15 a malformed item added over", WRITE, "case .valid, .malformed: return .update",
     "case .valid: return .update\n        case .malformed: return .add", [REPLACE, INSTALLID, FLOW]),
    ("16 a failed read written", WRITE, "case .failed: return .skip", "case .failed: return .add",
     [REPLACE, INSTALLID]),
    ("17 the UserDefaults copy ignored", INSTALL, "id: defaults ?? fresh", "id: fresh", [INSTALLID]),
    ("18 a valid id rewritten", INSTALL, "InstallIDDecision(id: id, write: .skip)",
     "InstallIDDecision(id: id, write: .update)", [INSTALLID]),
    ("19 the canonical check dropped", RECORD, "guard self.data == data else { return nil }", "", [MALFORMED]),
    ("20 the item's slashes escaped", RECORD, SORTED, "encoder.outputFormatting = [.sortedKeys]", [ITEM]),
    ("21 an empty token stored", RECORD, "!wire.key_id.isEmpty, !wire.token.isEmpty", "!wire.key_id.isEmpty",
     [MALFORMED]),
    ("22 no margin", STEP, MARGIN, "record.expiresAt.timeIntervalSince(now) > 0", [STEPS, FLOW]),
    ("23 the budget unread", STEP, "if spent { return .none }", "", [STEPS, FLOW, REJECTED, SHOWINGS]),
    ("24 a failed read attests", STEP, "case .absent, .malformed: return .attest\n        case .failed: return .none",
     "case .absent, .malformed, .failed: return .attest", [STEPS, FLOW]),
    ("25 a malformed item no session", STEP, "case .absent, .malformed: return .attest",
     "case .absent: return .attest\n        case .malformed: return .none", [STEPS, FLOW]),
    ("26 the acquisition never spent", STORE, "            spent = true\n", "", [FLOW, REJECTED, SHOWINGS]),
    ("27 an unsupported attester asks anyway", STORE, "guard attester.isSupported, case .challenge",
     "guard case .challenge", [FLOW]),
    ("28 a rejected key kept", STORE, "            storage.remove()\n", "", [FLOW]),
    ("29 every write an add", STORE, "KeychainWrite.replacing(over: keychain ?? .absent)", ".add", [FLOW, REJECTED]),
    ("30 another token's rejection drops", STORE, "current, record.token == token else { return }",
     "current else { return }", [REJECTED]),
    ("31 a rejection ignored", STORE,
     "current = .valid(SessionRecord(keyId: record.keyId, token: record.token, expiresAt: .distantPast))",
     "_ = record", [REJECTED, SHOWINGS]),
    ("32 another coordinate's cell", SOURCE, "cellOf(candidate.coordinate)",
     "cellOf(Coordinate(latitude: candidate.coordinate.latitude.rounded(), longitude: "
     "candidate.coordinate.longitude.rounded()))", [SHOWINGS]),
    ("33 a refused read an empty ledger", SOURCE, "await client.read() else { return nil }",
     "await client.read() else { return [] }", [PLACES]),
    ("34 a 401 kept", LEDGER, "if outcome == .unauthorized { await session.sessionRejected(token) }", "",
     [SHOWINGS]),
    ("35 the shown category fixed", SHOWING, "category: candidate.category,", "category: .park,",
     [RECORDING, SHOWINGS]),
    ("36 the feedback dropped", SHOWING, "feedback: history.feedback)", "feedback: [])", [RECORDING]),
    ("37 the challenge length a floor", READER, "bytes.count == 43", "bytes.count >= 43", [TABLE]),
    ("38 the margin inclusive", STEP, MARGIN, "record.expiresAt.timeIntervalSince(now) >= margin", [STEPS]),
    ("39 the same-day check ignores the day", SHOWING, "$0.candidateId == candidate.id && $0.date == date",
     "$0.candidateId == candidate.id", [RECORDING]),
    ("40 a place with no cell posted under a stand-in", SOURCE,
     "guard let cell = cellOf(candidate.coordinate) else { return }",
     'let cell = cellOf(candidate.coordinate) ?? "85283473fffffff"', [SHOWINGS]),
]

# (name, path, old, new, witness): cannot change behaviour, so anything but MISSED is a failure.
EQUIVALENT = [
    ("E1 the body's unreachable fallback", CLIENT, "(try? encoder.encode(fields)) ?? Data()",
     '(try? encoder.encode(fields)) ?? Data("{}".utf8)',
     "JSONEncoder throws only for a non-conforming float or a value that encodes nothing; a [String: String] is "
     "neither, so the fallback after `try?` is never evaluated"),
    ("E2 the Keychain belief kept after a refused write", STORE,
     "if storage.write(record, as: KeychainWrite.replacing(over: keychain ?? .absent)) { keychain = .valid(record) }",
     "_ = storage.write(record, as: KeychainWrite.replacing(over: keychain ?? .absent))
        keychain = .valid(record)",
     "keep is reached only from a .renew or .attest step, which sets spent before its one challenge, and SessionStep "
     "answers .none for both once spent; keychain is read only by sessionToken's first-call guard (non-nil before any "
     "acquisition) and by keep and renew, so after keep writes it no path in the same store reads it again, and the "
     "next launch is a new store that reads the real Keychain"),
]

MIN_MUTATIONS = 40
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 5
