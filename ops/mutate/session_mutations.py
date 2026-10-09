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
  * REVIEW ROUND 1 (41-56): every bound of the challenge's classes and its length (B1); the read's 401 and a 401
    assertion, over a real SessionStore (B2).
  * T-0322, THE SESSION CARRIES THE PURCHASE (57-76): the attest/assert body's appAccountToken (never, uppercase,
    misnamed, dropped by the store), the record's act (forgotten, off the wire, an empty one, unread), the step's act
    test, the per-value budget, a stale session sent; the plan family's Bearer (never set, no scheme, the header
    dropped beside it, each client dropping the session or asking for no purchase, a refused request acquiring).
  * T-0322 REVIEW ROUND 1, B1(b) (77-81): the expiry kept on the device's clock - the reply's instant kept instead,
    exp equal to iat read, the base64 padding dropped, the url alphabet unread, the fallback guessing an hour.
  * T-0333, THE PLAN FAMILY RECOVERS A REJECTED SESSION (82-90): the 401 unread, no hand-back, a Bearer-less resend,
    the second 401 kept, a third request, every or no rejection re-granted, the resend's purchase or renewal dropped.

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
IDENTITY = API / "IdentityHeaders.swift"
PLANCLIENT = API / "PlanClient.swift"
TRIPCLIENT = API / "TripClient.swift"
LOOPCLIENT = API / "LoopClient.swift"
FAMILY = API / "PlanFamilySend.swift"
SUBJECTS = (CLIENT, READER, WRITE, INSTALL, RECORD, STEP, STORE, SOURCE, LEDGER, SHOWING, IDENTITY, PLANCLIENT,
            TRIPCLIENT, LOOPCLIENT, FAMILY)
MUTATED_FILES = SUBJECTS

TESTS = ROOT / "Tests" / "ScenicAPIClientTests"
TEST_FILES = (TESTS / "AttestClientTests.swift", TESTS / "KeychainDecisionTests.swift",
              TESTS / "SessionStoreTests.swift", TESTS / "SurpriseLedgerWriteTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "Surprise" / "SurpriseShowingTests.swift",
              TESTS / "SessionAccountTests.swift", TESTS / "PlanBearerTests.swift", TESTS / "SessionSkewTests.swift",
              TESTS / "PlanSessionRetryTests.swift")

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
CHCLASS = "Every challenge position admits exactly 0-9, A-Z, a-z, '-' and '_', at both bounds of each class"
CHLEN = "A challenge is read at exactly 43 characters"
READ401 = "A GET /ledger 401 drops the session: the next POST carries the renewed token"
BODY = "attest and assert carry exactly the purchase's token, live or expired, or none"
WIRE = "the session record keeps its act on the wire, and an empty or null act is malformed"
STEPACT = "a live session is used only while its act is the device's purchase"
AFTER = "a session issued before the purchase renews once to carry it, then is used with no request"
SPENTAFTER = "a purchase made after the launch's first acquisition gets its own one try"
LEDGERACT = "the ledger's acquisition carries the store's purchase, and the plan family then uses that session"
NOSTALE = ("a failed renewal for the purchase is that token's one try: never the stale session, which still serves its "
           "own act")
ROWS = "every plan-family request names the purchase and carries the Bearer exactly when its act is that purchase"
STALE = "a session issued before the purchase is never sent: the header alone rides until it is renewed"
NOACQ = "a request refused on the device acquires no session"
RETRY = "a 401 hands the session back, re-acquires once and resends the same bytes once; never a third request"
PURCHASE = "the resend carries the same purchase: the renewal names it and the Bearer is the renewed session's"
SKEW = "a session is kept on the device's clock and used for exactly lifetime - margin seconds after receipt"
LIFE = "a token's lifetime is exactly exp - iat of its payload, at every bound"
FALLBACK = "a token with no readable lifetime keeps the reply's expires_at"

SORTED = "encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]"
MARGIN = "record.expiresAt.timeIntervalSince(now) > margin"
CHALLENGE = "(48...57).contains($0) || (65...90).contains($0) || (97...122).contains($0) || $0 == 45 || $0 == 95"

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
    ("26 the acquisition never spent", STORE, '            spent.insert(act ?? "")\n', "", [FLOW, REJECTED, SHOWINGS]),
    ("27 an unsupported attester asks anyway", STORE, "guard attester.isSupported, case .challenge",
     "guard case .challenge", [FLOW]),
    ("28 a rejected key kept", STORE, "            storage.remove()\n", "", [FLOW]),
    ("29 every write an add", STORE, "KeychainWrite.replacing(over: keychain ?? .absent)", ".add", [FLOW, REJECTED]),
    ("30 another token's rejection drops", STORE, "current, record.token == token else { return }",
     "current else { return }", [REJECTED]),
    ("31 a rejection ignored", STORE,
     "current = .valid(SessionRecord(keyId: record.keyId, token: record.token, expiresAt: .distantPast,\n"
     "                                       act: record.act))",
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
    # 41-54: review round 1 (rv1-t0310) B1 closed by class - every bound of the challenge's character classes.
    ("41 the challenge's lowercase class refuses a", READER, CHALLENGE, CHALLENGE.replace("(97...122)", "(98...122)"),
     [CHCLASS]),
    ("42 the challenge's lowercase class refuses z", READER, CHALLENGE, CHALLENGE.replace("(97...122)", "(97..<122)"),
     [CHCLASS]),
    ("43 the challenge's digit class admits a slash", READER, CHALLENGE, CHALLENGE.replace("(48...57)", "(47...57)"),
     [CHCLASS]),
    ("44 the challenge's digit class admits a colon", READER, CHALLENGE, CHALLENGE.replace("(48...57)", "(48...58)"),
     [CHCLASS]),
    ("45 the challenge's uppercase class admits @", READER, CHALLENGE, CHALLENGE.replace("(65...90)", "(64...90)"),
     [CHCLASS]),
    ("46 the challenge's uppercase class admits [", READER, CHALLENGE, CHALLENGE.replace("(65...90)", "(65...91)"),
     [CHCLASS]),
    ("47 the challenge's lowercase class admits a backtick", READER, CHALLENGE,
     CHALLENGE.replace("(97...122)", "(96...122)"), [CHCLASS]),
    ("48 the challenge's lowercase class admits {", READER, CHALLENGE, CHALLENGE.replace("(97...122)", "(97...123)"),
     [CHCLASS]),
    ("49 the challenge's digit class refuses 0", READER, CHALLENGE, CHALLENGE.replace("(48...57)", "(49...57)"),
     [CHCLASS]),
    ("50 the challenge's digit class refuses 9", READER, CHALLENGE, CHALLENGE.replace("(48...57)", "(48..<57)"),
     [CHCLASS]),
    ("51 the challenge's uppercase class refuses A", READER, CHALLENGE, CHALLENGE.replace("(65...90)", "(66...90)"),
     [CHCLASS]),
    ("52 the challenge's uppercase class refuses Z", READER, CHALLENGE, CHALLENGE.replace("(65...90)", "(65..<90)"),
     [CHCLASS]),
    ("53 the challenge length a ceiling", READER, "bytes.count == 43", "bytes.count <= 43", [TABLE, CHLEN]),
    ("54 the challenge's '_' refused", READER, "$0 == 45 || $0 == 95", "$0 == 45", [CHCLASS]),
    # 55-56: rv1-t0310 B2 closed by class - every path that can receive a 401, over a real SessionStore.
    ("55 the read's 401 kept", LEDGER,
     "body: Data()), isRead: true)\n        return await settled(outcome, token: token)",
     "body: Data()), isRead: true)\n        return outcome", [READ401]),
    ("56 a 401 assertion forgets the key", STORE, "if outcome == .rejected {",
     "if outcome == .rejected || outcome == .unexpected(401) {", [FLOW]),
    # 57-76: T-0322 - the session carries the purchase, and the plan family carries the session.
    ("57 the body never names the purchase", CLIENT, "guard let account else { return fields }",
     "guard let account, false else { return fields }", [BODY, AFTER, LEDGERACT, ROWS]),
    ("58 the purchase sent uppercase", CLIENT, '["appAccountToken": account.uuidString.lowercased()]',
     '["appAccountToken": account.uuidString]', [BODY]),
    ("59 the body key misnamed", CLIENT, '["appAccountToken": account', '["accountToken": account', [BODY]),
    ("60 the store attests without the purchase", STORE,
     "challenge: challenge,\n                                          account: account)",
     "challenge: challenge,\n                                          account: nil)", [LEDGERACT]),
    ("61 the store renews without the purchase", STORE, "assertion: assertion, challenge: challenge, account: account)",
     "assertion: assertion, challenge: challenge, account: nil)", [AFTER, ROWS, SPENTAFTER]),
    ("62 the record forgets its act", STORE, "act: account?.uuidString.lowercased())", "act: nil)",
     [AFTER, LEDGERACT]),
    ("63 the step ignores the act", STEP, ", record.act == act {", " {", [STEPACT, AFTER, ROWS, STALE]),
    ("64 one budget for every purchase", STORE, 'spent: spent.contains(act ?? "")', "spent: !spent.isEmpty",
     [SPENTAFTER]),
    ("65 the act off the wire", RECORD, "Wire(act: act, expires_at:", "Wire(act: nil, expires_at:", [WIRE]),
    ("66 an empty act read", RECORD, "wire.act?.isEmpty != true", "true", [WIRE]),
    ("67 the record read without its act", RECORD, ", act: wire.act)", ")", [WIRE]),
    ("68 the Bearer never set", IDENTITY, 'if let bearer { headers[authorizationHeader] = "Bearer " + bearer }',
     "_ = bearer", [ROWS]),
    ("69 the Bearer without its scheme", IDENTITY, '"Bearer " + bearer', "bearer", [ROWS]),
    ("70 the account header dropped beside a Bearer", IDENTITY, "if let account { headers[accountHeader]",
     "if let account, bearer == nil { headers[accountHeader]", [ROWS]),
    # 71-74 re-anchored by T-0333: the clients hand their session to PlanFamilySend, which asks it.
    ("71 PlanClient drops the session", PLANCLIENT, "account: account, session: session,",
     "account: account, session: nil,", [ROWS]),
    ("72 TripClient drops the session", TRIPCLIENT, "account: account, session: session,",
     "account: account, session: nil,", [ROWS]),
    ("73 LoopClient drops the session", LOOPCLIENT, "account: account, session: session,",
     "account: account, session: nil,", [ROWS]),
    ("74 the family send asks for no purchase", FAMILY, "let bearer = await session?.planSession(account: account)",
     "let bearer = await session?.planSession(account: nil)", [ROWS]),
    ("75 TripClient acquires before the device refusal", TRIPCLIENT,
     "guard let installID else { throw .refusedOnDevice(.noInstallID) }",
     "_ = await session?.planSession(account: nil)\n        guard let installID else { throw .refusedOnDevice(.noInstallID) }",
     [NOACQ]),
    ("76 a stale session sent when the renewal fails", STORE,
     "case .challenge(let challenge) = await client.challenge() else { return nil }",
     "case .challenge(let challenge) = await client.challenge() else {\n"
     "                if case .valid(let held) = current { return held.token }\n                return nil\n            }",
     [NOSTALE, ROWS, STALE]),
    # 77-81: T-0322 review round 1, B1(b) - the session's expiry on the device's clock.
    ("77 the reply's instant kept", STORE,
     "let expiry = SessionRecord.lifetime(of: token).map { now().addingTimeInterval($0) } ?? expiresAt",
     "let expiry = expiresAt", [SKEW]),
    ("78 exp equal to iat read", RECORD, "claims.exp > claims.iat", "claims.exp >= claims.iat", [LIFE]),
    ("79 the base64 padding dropped", RECORD,
     'payload += String(repeating: "=", count: (4 - payload.count % 4) % 4)', "_ = payload", [LIFE]),
    ("80 the url alphabet unread", RECORD,
     'var payload = parts[1].replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")',
     "var payload = String(parts[1])", [LIFE]),
    ("81 the fallback guesses an hour", STORE, "now().addingTimeInterval($0) } ?? expiresAt",
     "now().addingTimeInterval($0) } ?? now().addingTimeInterval(3600)", [FALLBACK]),
    # 82-90: T-0333 R3, R4 - the plan family recovers a rejected session, once.
    ("82 the 401 unread", FAMILY, "static let rejectedStatus = 401", "static let rejectedStatus = 0", [RETRY]),
    ("83 resent without the hand-back", FAMILY, "        await session.planSessionRejected(bearer)\n", "", [RETRY]),
    ("84 a Bearer-less request resent", FAMILY,
     "guard first.status == rejectedStatus, let bearer, let session else { return first }\n"
     "        await session.planSessionRejected(bearer)",
     "guard first.status == rejectedStatus, let session else { return first }\n"
     "        if let bearer { await session.planSessionRejected(bearer) }", [RETRY]),
    ("85 the second 401 keeps its token", FAMILY,
     "if second.status == rejectedStatus, let renewed { await session.planSessionRejected(renewed) }", "", [RETRY]),
    ("86 a third request", FAMILY, "        return second\n",
     "        guard second.status == rejectedStatus else { return second }\n"
     "        return try await transport.send(request(await session.planSession(account: account)))\n", [RETRY]),
    ("87 every rejection re-granted", STORE, "if regranted.insert(act).inserted { spent.remove(act) }",
     "spent.remove(act)", [RETRY]),
    ("88 never re-granted", STORE, "if regranted.insert(act).inserted { spent.remove(act) }",
     "_ = regranted.insert(act)", [RETRY]),
    ("89 the resend asks for no purchase", FAMILY, "let renewed = await session.planSession(account: account)",
     "let renewed = await session.planSession(account: nil)", [PURCHASE]),
    ("90 the resend skips the renewal", FAMILY, "let renewed = await session.planSession(account: account)",
     "let renewed: String? = nil", [RETRY]),
    ("91 the failed renewal resends the rejected token", FAMILY,
     "let second = try await transport.send(request(renewed))",
     "let second = try await transport.send(request(renewed ?? bearer))", [RETRY]),
]

# (name, path, old, new, witness): cannot change behaviour, so anything but MISSED is a failure.
EQUIVALENT = [
    ("E1 the body's unreachable fallback", CLIENT, "(try? encoder.encode(fields)) ?? Data()",
     '(try? encoder.encode(fields)) ?? Data("{}".utf8)',
     "JSONEncoder throws only for a non-conforming float or a value that encodes nothing; a [String: String] is "
     "neither, so the fallback after `try?` is never evaluated"),
    ("E2 the Keychain belief kept after a refused write", STORE,
     "if storage.write(record, as: KeychainWrite.replacing(over: keychain ?? .absent)) { keychain = .valid(record) }",
     "_ = storage.write(record, as: KeychainWrite.replacing(over: keychain ?? .absent))\n        keychain = .valid(record)",
     "keep is reached only from a .renew or .attest step, which sets spent before its one challenge, and SessionStep "
     "answers .none for both once spent; keychain is read only by sessionToken's first-call guard (non-nil before any "
     "acquisition) and by keep and renew, so after keep writes it no path in the same store reads it again, and the "
     "next launch is a new store that reads the real Keychain"),
    ("E3 a rejected session forgets its act", STORE,
     "expiresAt: .distantPast,\n                                       act: record.act))",
     "expiresAt: .distantPast,\n                                       act: nil))",
     "the rejected record's expiry is .distantPast, so SessionStep never answers .use for it whatever its act; .renew "
     "takes only its keyId and the act ASKED FOR, and keep writes a new record - the dropped record's act is never read"),
]

MIN_MUTATIONS = 91
MIN_EQUIVALENT = 3
MIN_TEST_FILES = 9
