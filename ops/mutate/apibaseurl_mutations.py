"""The mutation population for Sources/ScenicAPIClient/APIBaseURL.swift. The runner is apibaseurl.py.

APIBaseURL.resolve is the one rule every app client's base URL is built from (T-0394): a refusal it loses is
a request sent to a server nobody chose, and an acceptance it loses is routingOffline on every launch. Each
entry deletes or weakens ONE clause of that rule.

`(name, path, old, new, killers)`. `old` must appear VERBATIM in the pristine file or the run reports SKIP
and FAILS. No anchor is a comment. `killers` names the tests that MUST go red, as Swift Testing prints them;
an entry caught only by some other test is WRONG KILLER and fails the run.

M1 and M2 are agent/rv1-t0394's survivors (B2, B3) against the suite at 1d0f5076, kept verbatim as entries
1 and 2. M2's killer is the GENERATED near-miss corpus (every whitespace character at every position of every
accepted seed), so the whitespace clause, not whichever spellings URLComponents happens to refuse, carries
every refusal; entries 3 and 4 are the same class narrowed (only a space; only a newline).
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SUBJECT = ROOT / "Sources/ScenicAPIClient/APIBaseURL.swift"
TEST_DIR = ROOT / "Tests/ScenicAPIClientTests"
TEST_FILE = TEST_DIR / "APIBaseURLTests.swift"
MUTATED_FILES = (SUBJECT,)

TABLE = "resolveMatchesTheTableRowByRow()"
CORPUS = "whitespaceInsertedAnywhereInAnAcceptedBaseIsRefused()"
COMPOSE = "everyAcceptedBaseComposesThePlanPathExactly()"
KEYS = "theKeysAreTheShippedSpellings()"
SHIPPED = "shippedInfoPlistResolvesToThePilot()"

HOST = "let host = parts.host, !host.isEmpty, parts.user"
SPACE = "guard var text, !text.contains(where: { $0.isWhitespace })"
SCHEME = 'parts.scheme == "https"'
USER = "parts.user == nil, parts.password"
QUERY = "parts.query == nil, parts.fragment"
FRAGMENT = "parts.fragment == nil, let url"
SLASH = 'while text.hasSuffix("/") { text.removeLast() }'
OVERRIDE = "if let override { return parse(override) }"
PLIST_KEY = 'infoPlistKey = "SCENIC_API_BASE_URL"'
OVERRIDE_KEY = 'overrideKey = "plan.base.url"'

MUTATIONS = [
    ("M1 the empty-host clause dropped (rv1 B2)", SUBJECT, HOST, "let host = parts.host, parts.user", [TABLE]),
    ("M2 the whitespace clause dropped (rv1 B3)", SUBJECT, SPACE, "guard var text", [CORPUS]),
    ("the whitespace clause narrowed to a space", SUBJECT, SPACE,
     'guard var text, !text.contains(" ")', [CORPUS]),
    ("the whitespace clause narrowed to newlines", SUBJECT, SPACE,
     "guard var text, !text.contains(where: { $0.isNewline })", [CORPUS]),
    ("any scheme accepted", SUBJECT, SCHEME, "parts.scheme != nil", [TABLE]),
    ("the scheme compared case-insensitively", SUBJECT, SCHEME, 'parts.scheme?.lowercased() == "https"', [TABLE]),
    ("a user accepted", SUBJECT, USER, "parts.password", [TABLE]),
    ("a query accepted", SUBJECT, QUERY, "parts.fragment", [TABLE]),
    ("a fragment accepted", SUBJECT, FRAGMENT, "let url", [TABLE]),
    ("trailing slashes kept", SUBJECT, SLASH, "", [TABLE, COMPOSE]),
    ("one trailing slash dropped, not every one", SUBJECT, SLASH,
     'if text.hasSuffix("/") { text.removeLast() }', [TABLE, COMPOSE]),
    ("an invalid override falls back to the bundled server", SUBJECT, OVERRIDE,
     "if let override, let url = parse(override) { return url }", [TABLE]),
    ("the override ignored", SUBJECT, OVERRIDE, "if let override, override.isEmpty { return nil }", [TABLE]),
    ("the Info.plist key respelled", SUBJECT, PLIST_KEY, 'infoPlistKey = "SCENIC_API_BASE"', [KEYS, SHIPPED]),
    ("the override key respelled", SUBJECT, OVERRIDE_KEY, 'overrideKey = "plan.base"', [KEYS]),
]

# (name, path, old, new, witness): edits that cannot change what resolve returns. Anything but MISSED fails.
EQUIVALENT = [
    ("the password clause dropped", SUBJECT, "parts.user == nil, parts.password == nil,", "parts.user == nil,",
     "a password needs a userinfo `@`, and URLComponents reports a user (\"\" when empty) whenever an `@` is "
     "present, so the user clause refuses every input the password clause refuses: `https://:pw@host` has "
     "user \"\" and is in the table as a refusal under both"),
]

MIN_MUTATIONS = 15
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 1
