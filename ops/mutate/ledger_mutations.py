"""The mutation population for T-0307: the /ledger client's requests and device refusals (Sources/ScenicAPIClient/
LedgerClient.swift, LedgerEntry.swift), the reply -> outcome table and the day parser (LedgerReplyReader.swift),
and the Surprise history merge (Sources/ScenicKit/Surprise/SurpriseHistoryMerge.swift). Driver ledger.py, runner
ledger_run.py (savedlist's three-file shape).

  * THE CLIENT (1-6): an empty token sent, the bearer prefix, a GET body, the refusal skipped, a retry, offline;
  * THE ENTRY (7-11): a leading zero, the Int64 bound, uppercase hex, a 14-digit cell, a signed place id;
  * THE READER (12-18): the 429 body, 401, recorded false, a bad row skipped, February, April, day zero;
  * THE MERGE (19-25): nil normalized, the earliest day kept, an unknown id kept, newest first, the tie by id,
    the feedback dropped, the ledger's day ignored;
  * THE PRE-REVIEW SURVIVORS (26-28): MISSED before their tests landed (T-0307 Log), CAUGHT after;
  * THE DEDUPE KEY (29-32): the merge keyed by anything but the place id - category, corridor, both, day.
  * THE CHARACTER CLASSES (33-44, review round 1 RV1/RV2): every bound of the cell's digit and lowercase classes,
    the second date separator, and both bounds of the day's digit class.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

CLIENT = ROOT / "Sources" / "ScenicAPIClient" / "LedgerClient.swift"
ENTRY = ROOT / "Sources" / "ScenicAPIClient" / "LedgerEntry.swift"
READER = ROOT / "Sources" / "ScenicAPIClient" / "LedgerReplyReader.swift"
MERGE = ROOT / "Sources" / "ScenicKit" / "Surprise" / "SurpriseHistoryMerge.swift"
SUBJECTS = (CLIENT, ENTRY, READER, MERGE)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicAPIClientTests" / "LedgerClientTests.swift",
              ROOT / "Tests" / "ScenicKitTests" / "Surprise" / "SurpriseHistoryMergeTests.swift")

POST = "POST /ledger is exactly the bearer, the content type and {cell, place_id}"
GET = "GET /ledger is exactly the bearer, no body, and its rows parse to the rows the body was built from"
UNREADABLE = "A GET body that is not {places: [{place_id, cell, day}]} with real days is unreadable"
TABLE = "Every Worker answer is one typed outcome after exactly one request - never a retry"
OFFLINE = "No reply at all is offline, after exactly one request"
NOSESSION = "Without a session nothing is sent"
REFUSED = "A place id or cell the Worker would refuse is refused on the device and nothing is sent"
MERGED = "The merged history is exactly the expected one, whatever the ledger's order"
CELLCLASS = "Every cell position admits exactly 0-9 and a-f, at both bounds of each class"
DAYCLASS = "Every day separator and digit position refuses its out-of-class neighbours"
DAYREAD = "A day with 0 or 9 at each digit position that can hold one is read as that day"
NINETY = "A ledger place shown 89 days ago is never picked; 90 days ago it is picked again"
# The merge's dedupe: both lines name the key, so a mutant swaps it in both.
KEY = ("if let held = latest[entry.candidateId], Surprise.days(entry.date, since: held.date) <= 0 { return }\n"
       "            latest[entry.candidateId] = entry")

# The cell's two classes and the day's digit class, each anchored on its whole expression.
CELL_CLASSES = "(48...57).contains($0) || (97...102).contains($0)"
DAY_CLASS = "(48...57).contains($0) } }"

MUTATIONS = [
    ("1 an empty token is a session", CLIENT,
     "guard let token = await session.sessionToken(), !token.isEmpty else { return nil }",
     "guard let token = await session.sessionToken() else { return nil }", [NOSESSION]),
    ("2 the bearer prefix lost", CLIENT, '"Bearer \\(token)",', '"\\(token)",', [POST]),
    ("3 GET sends a body", CLIENT, "body: Data()), isRead: true)", 'body: Data("{}".utf8)), isRead: true)', [GET]),
    ("4 the device refusal skipped", CLIENT,
     "guard let entry = LedgerEntry(placeId: placeId, cell: cell) else { return .refusedOnDevice }",
     'let entry = LedgerEntry(placeId: placeId, cell: cell) ?? LedgerEntry(placeId: "1", cell: "85283473fffffff")!',
     [REFUSED]),
    ("5 a 429 or a 401 retried once", CLIENT,
     "return LedgerReplyReader.read(try await transport.send(request), isRead: isRead)",
     "let first = LedgerReplyReader.read(try await transport.send(request), isRead: isRead)\n"
     "            if first == .dailyCap || first == .unauthorized {\n"
     "                return LedgerReplyReader.read(try await transport.send(request), isRead: isRead)\n"
     "            }\n"
     "            return first", [TABLE]),
    ("6 no reply read as unavailable", CLIENT, "return .offline", "return .unavailable", [OFFLINE]),
    ("7 a leading zero admitted", ENTRY, ", digits[0] != 48,", ",", [REFUSED]),
    ("8 the Int64 bound dropped", ENTRY, "Int64(placeId) != nil else", "true else", [REFUSED]),
    ("9 uppercase hex admitted", ENTRY, "(97...102).contains($0)", "(65...102).contains($0)", [REFUSED]),
    ("10 a 14-digit cell admitted", ENTRY, "hex.count == 15", "hex.count >= 14", [REFUSED]),
    ("11 a signed place id admitted", ENTRY, "digits.allSatisfy({ (48...57).contains($0) })",
     "digits.allSatisfy({ (43...57).contains($0) })", [REFUSED]),
    ("12 any 429 is the daily cap", READER, 'return error == "ledger_daily_cap" ? .dailyCap : .unexpected(429)',
     "return .dailyCap", [TABLE]),
    ("13 401 read as invalid", READER, "case 401: return .unauthorized", "case 401: return .invalidRequest",
     [TABLE]),
    ("14 recorded false accepted", READER, "?.recorded == true ? .recorded", "?.recorded != nil ? .recorded",
     [TABLE]),
    ("15 a bad row skipped", READER, "guard let day = civilDate(row.day) else { return .unreadable }",
     "guard let day = civilDate(row.day) else { continue }", [UNREADABLE]),
    ("16 February always 29 days", READER, "leap ? 29 : 28", "29", [UNREADABLE]),
    ("17 April 31 admitted", READER, "leap ? 29 : 28, 31, 30,", "leap ? 29 : 28, 31, 31,", [UNREADABLE]),
    ("18 day zero admitted", READER, "guard (1...lengths[month - 1]).contains(day)",
     "guard (0...lengths[month - 1]).contains(day)", [UNREADABLE]),
    ("19 no session normalized like an empty ledger", MERGE, "guard let ledger else { return device }",
     "let ledger = ledger ?? []", [MERGED]),
    ("20 the earliest day kept", MERGE, "<= 0 { return }", ">= 0 { return }", [MERGED]),
    ("21 an unknown id kept", MERGE, "guard let c = byID[place.candidateId] else { continue }",
     "guard let c = byID[place.candidateId] ?? candidates.first else { continue }", [MERGED]),
    ("22 newest first", MERGE, "gap != 0 ? gap < 0", "gap != 0 ? gap > 0", [MERGED]),
    ("23 a day tie by id reversed", MERGE, "$0.candidateId < $1.candidateId", "$0.candidateId > $1.candidateId",
     [MERGED]),
    ("24 the feedback dropped", MERGE, "feedback: device.feedback)", "feedback: [])", [MERGED]),
    ("25 the ledger's day ignored", MERGE, "corridor: c.corridor, date: place.date)",
     "corridor: c.corridor, date: CivilDate(year: 2000, month: 1, day: 1))", [MERGED, NINETY]),
    # 26-28: the pre-review pass's three survivors (T-0307 Log), each MISSED before its test landed.
    ("26 the 400-year leap rule dropped", READER, "(year % 100 != 0 || year % 400 == 0)", "year % 100 != 0",
     [GET]),
    ("27 the first date separator unchecked", READER, "b[4] == 45, ", "", [UNREADABLE]),
    ("28 a day tie handed to the ledger", MERGE, "<= 0 { return }", "< 0 { return }", [MERGED]),
    # 29-32: the pre-review pass's survivor M2 closed by class - every key that is not the place id.
    ("29 the merge keyed by category", MERGE, KEY, KEY.replace("entry.candidateId", "entry.category.rawValue"),
     [MERGED]),
    ("30 the merge keyed by corridor", MERGE, KEY, KEY.replace("entry.candidateId", "entry.corridor"), [MERGED]),
    ("31 the merge keyed by category and corridor", MERGE, KEY,
     KEY.replace("entry.candidateId", 'entry.category.rawValue + "/" + entry.corridor'), [MERGED]),
    ("32 the merge keyed by day", MERGE, KEY, KEY.replace("entry.candidateId", '"\\(entry.date)"'), [MERGED]),
    # 33-44: review round 1 RV1/RV2 closed by class - every bound of every character-class check.
    ("33 the cell's lowercase class admits g", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("102", "103"), [CELLCLASS]),
    ("34 the second date separator unchecked", READER, ", b[7] == 45", "", [DAYCLASS]),
    ("35 the cell's digit class admits a colon", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("57", "58"), [CELLCLASS]),
    ("36 the cell's digit class admits a slash", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("48", "47"), [CELLCLASS]),
    ("37 the cell's lowercase class admits a backtick", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("97", "96"),
     [CELLCLASS]),
    ("38 the day's digit class admits a colon", READER, DAY_CLASS, DAY_CLASS.replace("57", "58"), [DAYCLASS]),
    ("39 the cell's digit class refuses 0", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("48", "49"), [CELLCLASS]),
    ("40 the cell's digit class refuses 9", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("57", "56"), [CELLCLASS]),
    ("41 the cell's lowercase class refuses a", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("97", "98"), [CELLCLASS]),
    ("42 the cell's lowercase class refuses f", ENTRY, CELL_CLASSES, CELL_CLASSES.replace("102", "101"),
     [CELLCLASS]),
    ("43 the day's digit class refuses 0", READER, DAY_CLASS, DAY_CLASS.replace("48", "49"), [DAYREAD]),
    ("44 the day's digit class refuses 9", READER, DAY_CLASS, DAY_CLASS.replace("57", "56"), [DAYREAD]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 a 20-digit place id length admitted", ENTRY, "(1...19).contains(digits.count)",
     "(1...20).contains(digits.count)",
     "a 20-digit decimal with no leading zero is at least 10^19 > Int64.max, so Int64(placeId) is nil and the "
     "entry is refused by the next clause either way"),
]

MIN_MUTATIONS = 44
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 2
