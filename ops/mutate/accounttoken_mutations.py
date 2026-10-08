"""The mutation population for T-0315: the one header set of every plan-family request (Sources/ScenicAPIClient/
IdentityHeaders.swift), the pick of the purchase token the app sends (AccountTokenCandidate.swift), and the two
call sites that attach it (PlanClient.swift, TripClient.swift,
LoopClient.swift). Driver accounttoken.py, runner accounttoken_run.py
(ledger's three-file shape).

  * THE HEADER SET (1-4, 12): the token never set, sent uppercase, misnamed, sent under the device header, and the
    device header dropped when a token is held;
  * THE CALL SITES (5-7, 13-15): each client dropping the purchase, and each reading the token before the device
    refusal (a refused request must read nothing);
  * THE PICK (8-11): the earliest purchase winning, equal instants keeping the first listed or the lesser token,
    and a later-or-equal purchase replacing the held one (order-dependent).

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_API = ROOT / "Sources" / "ScenicAPIClient"
IDENTITY = _API / "IdentityHeaders.swift"
CANDIDATE = _API / "AccountTokenCandidate.swift"
PLANCLIENT = _API / "PlanClient.swift"
TRIPCLIENT = _API / "TripClient.swift"
LOOPCLIENT = _API / "LoopClient.swift"
SUBJECTS = (IDENTITY, CANDIDATE, PLANCLIENT, TRIPCLIENT, LOOPCLIENT)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicAPIClientTests" / "AccountTokenHeaderTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "AccountTokenCandidateTests.swift")

PLAN = "every plan request carries exactly the device and the purchase's account token"
TRIP = "every trip request carries exactly the device and the account token, and the itinerary is the Worker's"
LOOP = "every loop request carries exactly the device and the account token, and the loop is the Worker's"
REFUSAL = "a request refused on the device reads no account token and sends nothing"
LATEST = "the latest purchase's token is the one sent, live or expired, in every StoreKit order"

SET_TOKEN = "if let account { headers[accountHeader] = account.uuidString.lowercased() }"
ATTACH = "let account = await accountToken?.accountToken()"
NO_INSTALL = "guard let installID else { throw .refusedOnDevice(.noInstallID) }"
# plan() and reroute() both open with NO_INSTALL (T-0319); this tail makes the anchor plan()'s alone.
PLAN_BODY = "\n        let body: PlanRequestBody"
LATER = "if candidate.purchased > held.purchased { best = candidate; continue }"
TIE = "if candidate.purchased == held.purchased, candidate.token!.uuidString > held.token!.uuidString {"

MUTATIONS = [
    ("1 the account header never set", IDENTITY, SET_TOKEN, "_ = account", [PLAN, TRIP]),
    ("2 the token sent uppercase, as Foundation prints it", IDENTITY, SET_TOKEN,
     SET_TOKEN.replace("account.uuidString.lowercased()", "account.uuidString"), [PLAN, TRIP]),
    ("3 the header misnamed", IDENTITY, 'accountHeader = "x-scenic-account-token"',
     'accountHeader = "x-scenic-account"', [PLAN, TRIP]),
    ("4 the token sent under the device header", IDENTITY, SET_TOKEN,
     SET_TOKEN.replace("headers[accountHeader]", "headers[deviceHeader]"), [PLAN, TRIP]),
    ("5 PlanClient drops the purchase", PLANCLIENT, ATTACH, "let account: UUID? = nil", [PLAN]),
    ("6 TripClient drops the purchase", TRIPCLIENT, ATTACH, "let account: UUID? = nil", [TRIP]),
    ("7 LoopClient drops the purchase", LOOPCLIENT, ATTACH, "let account: UUID? = nil", [LOOP]),
    ("8 the earliest purchase wins", CANDIDATE, LATER, LATER.replace(" > ", " < "), [LATEST]),
    ("9 equal instants keep the first listed", CANDIDATE, TIE, "if false {", [LATEST]),
    ("10 equal instants keep the lesser token", CANDIDATE, TIE,
     TIE.replace("uuidString > held", "uuidString < held"), [LATEST]),
    ("11 an equal-instant purchase replaces the held one", CANDIDATE, LATER, LATER.replace(" > ", " >= "),
     [LATEST]),
    ("12 the device header dropped when a token is held", IDENTITY, SET_TOKEN,
     "if let account { headers = [accountHeader: account.uuidString.lowercased()] }", [PLAN, TRIP]),
    ("13 PlanClient reads the token before the device refusal", PLANCLIENT, NO_INSTALL + PLAN_BODY,
     "_ = await accountToken?.accountToken()\n        " + NO_INSTALL + PLAN_BODY, [REFUSAL]),
    ("14 TripClient reads the token before the device refusal", TRIPCLIENT, NO_INSTALL,
     "_ = await accountToken?.accountToken()\n        " + NO_INSTALL, [REFUSAL]),
    ("15 LoopClient reads the token before the device refusal", LOOPCLIENT, NO_INSTALL,
     "_ = await accountToken?.accountToken()\n        " + NO_INSTALL, [REFUSAL]),
]

EQUIVALENT = [
    ("E1 the later purchase falls through to the tie test", CANDIDATE, LATER,
     "if candidate.purchased > held.purchased { best = candidate }",
     "`held` is bound before the assignment, so after `candidate.purchased > held.purchased` the tie test that "
     "follows compares the same two instants, is false, and assigns nothing: `continue` changes no outcome"),
]

MIN_MUTATIONS = 15
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 2
