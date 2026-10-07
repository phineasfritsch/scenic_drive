---
id: T-0296
title: POST /waitlist counts one device once per cell per day - a rate limit so anyone cannot inflate a cell's count
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T09:30:08Z
lease_expires_at: 2026-10-07T21:30:08Z
worktree: .worktrees/T-0296
branch: task/T-0296
exclusive: []
touches: [services/api/src/waitlist.ts, services/api/test/, services/api/migrations/, ops/lib/named-tests.json, pins/PINS.yaml, queue/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0293]
verify: [ops/check-pins]
acceptance:
  - "RULE FIRST: the identity a waitlist write is bound to (the attested session / install id the quota already uses), and how a per-device-per-cell-per-day dedupe is stored without keeping the device id next to the cell (e.g. a keyed hash that expires daily) - P-PRIV-05 DDL test extended"
  - "Through worker.fetch: the same device posting the same cell twice in one UTC day increments once; a second device increments again; the next day increments again - full-equality table"
  - "Population entries for the dedupe key and the day boundary, MISSED before and CAUGHT by name after"
---
## Brief

T-0293 author stillOpen 4 (PR #182): /waitlist has no rate limit, so anyone can inflate a cell's count. The waitlist
must stay free of personal data (memory user-lives-in-la; plan Launch scope).

## Log
- 2026-10-07T07:17:54Z filed by agent/claude-opus-5 (orchestrator) from T-0293's stillOpen 4.
- 2026-10-07T09:30:08Z claimed by agent/claude-opus-5; lease until 2026-10-07T21:30:08Z
- 2026-10-07T09:38:35Z RULINGS (author rule, before any code):
  - R1 identity. A waitlist write is bound to identifyCaller's userId - the bucket /telemetry and the quota use
    (sessionIdentity.ts): the verified session JWT's sub when SESSION_JWT_SECRET is set, the x-scenic-device install
    bucket (routerDeps deviceIdentity) only on the legacy/IDENTITY_HEADERS=1 path. The tier is never read. Every caller
    without a valid identity shares UNIDENTIFIED_SESSION and so counts as ONE device: at most +1 per cell per day for
    all of them together. LIMIT (recorded, not closed): while IDENTITY_HEADERS=1 a header id is as forgeable for the
    waitlist as it is for the quota; with the secret set and the flag unset only an attested session counts.
  - R2 key. day = now.toISOString().slice(0, 10) (the UTC day, the quota's dayKey). K_day =
    HMAC-SHA256(SESSION_JWT_SECRET, "scenic-waitlist/v1/" + day), computed per request, never stored, logged or
    returned. tag = lowercase hex HMAC-SHA256(K_day, userId + "\n" + cell) - 64 chars. The cell is IN the message, so two
    cells of one device give unrelated tags; the day is in the KEY, so one device's tags on two days are unrelated.
    The secret is read through sessionSecret() (>= 32 chars, MIN_SECRET_LENGTH); reusing SESSION_JWT_SECRET is ruled
    over a new owner secret: the domain prefix separates the uses, and identity is attested only when it is set anyway.
  - R3 fail closed. sessionSecret(env.SESSION_JWT_SECRET) === null (unbound, empty, 31 chars) is 503
    waitlist_unavailable with NO write - never an unlimited count. Checked after the body is valid (400s unchanged).
  - R4 storage. New migration 0007_waitlist_seen.sql (0006 is shipped; a D1 migration once applied is never re-run):
    waitlist_seen (tag TEXT PRIMARY KEY CHECK length 64, day TEXT CHECK length 10). No device, account, cell or instant
    column. Every accepted write first runs DELETE FROM waitlist_seen WHERE day <> today, so no tag outlives its UTC
    day; then INSERT ... ON CONFLICT (tag) DO NOTHING; the waitlist count moves only when that insert's
    meta.changes === 1. Two statements, not one transaction: a failure between them under-counts by one, the safe
    direction. The answer is 200 {waitlisted: true} whether or not the count moved (no membership oracle).
  - R5 kill-switch and quota exemption by ruling unchanged (no upstream, no quota touch). The deletion whitelist
    (accountDelete.test.ts TABLES) gains waitlist_seen as not user-keyed (a tag cannot be mapped back to a device
    without the day key and the cell, and is gone at the next UTC day).
  - R6 tests. New waitlistDedupe.test.ts through worker.fetch: a sequence table (same device same cell twice; second
    device; second cell; unidentified twice; next day; the day bound at 23:59:59.999Z / 00:00:00.000Z) over the
    empty and holding variants, waitlist AND waitlist_seen compared WHOLE against an independent WebCrypto oracle of
    the tag; secret unbound / "" / 31 chars -> 503 with both tables unchanged, 32 chars accepted. The T-0293 tests keep
    their names (P-PRIV-06 binds them); their bodies send with a session and use two devices where they counted two.
    migrationColumns.test.ts gains `waitlist_seen is exactly (tag, day)` for P-PRIV-05's DDL clause.
  - R7 touches widened by ruling to ops/lib/named-tests.json and pins/PINS.yaml: binding the new tests BY NAME under
    P-PRIV-05 / P-PRIV-06 is the only way the acceptance's "P-PRIV-05 DDL test extended" is enforced.
- 2026-10-07T10:11:42Z RED, GREEN, POPULATION (commit e3097fd9; vitest from services/api):
  - RED 1 (before 0007 existed): `npx vitest run test/migrationColumns.test.ts` -> Tests 1 failed | 2 passed (3);
    FAILED `the waitlist dedupe table is exactly (tag, day): no column can hold a device, a cell or an instant (T-0296, P-PRIV-05)`.
  - RED 2 (0007 present, T-0293's handler): `npx vitest run test/waitlistDedupe.test.ts` -> Tests 3 failed | 1 passed (4);
    FAILED `same device same cell same day counts once; ...`, `the dedupe table holds no device id and no cell, ...`,
    `without a usable SESSION_JWT_SECRET the route fails closed: ...` (the fourth, the variants-differ meta test, is pure).
  - Found on the way: the fail-closed test first passed `undefined` into a defaulted parameter, so the "unbound" row
    sent the real secret (the full run showed 200 where 503 was ruled); the row now uses an explicit null sentinel.
    requestReadSites.test.ts (the whitelist of request readers) refused the new identify/tag lines by name and now
    approves exactly those four lines; accountDelete.test.ts TABLES gains waitlist_seen (R5).
  - GREEN: the five touched files 34/34 passed.
  - POPULATION regionMutants.mjs (MIN_MUTATIONS 52 -> 66, SUBJECTS + migrations/0007_waitlist_seen.sql, TESTS +
    waitlistDedupe.test.ts), `--only=` the fourteen T-0296 ids:
    BEFORE (waitlistDedupe.test.ts moved aside, migrationColumns.test.ts at 4d19c994): `RESULT caught=3 missed=11 trap=0 of 14`
    - MISSED tag-ignores-cell, tag-ignores-day, day-one-ms-early, day-one-ms-late, purge-dropped, purge-inverted,
      seen-ignored, secret-absent-unlimited, secret-length-unchecked, seen-device-column, seen-cell-column; CAUGHT
      tag-ignores-device, identity-constant, identity-header-only by the T-0293 test `a valid cell is 200 waitlisted ...`
      (its second send now comes from a second device, so a key that ignores who undercounts there).
    AFTER: `RESULT caught=14 missed=0 trap=0 of 14` - the dedupe key and day-boundary entries CAUGHT by
    `same device same cell same day counts once; ...`, the secret entries by `without a usable SESSION_JWT_SECRET ...`,
    the 0007 column entries by `the waitlist dedupe table is exactly (tag, day) ...`.
  - Bound by name: P-PRIV-05 + the DDL test and the dedupe-table test (32 tests); P-PRIV-06 + the four waitlistDedupe tests (11).
- 2026-10-07T10:31:05Z FINAL GATES on 56309f23 (git fetch origin; merge origin/main afa0dd15: "Already up to date"):
  - `npx vitest run` -> Tests 1 failed | 2101 passed (2102), 278 s on the contended box: the one failure is
    configAnswerPath.test.ts `loading the shipped worker leaves every global ...` "Test timed out in 5000ms"; alone
    it is 3 passed (3), and the run before the merge (61 s) passed it - load, not this diff.
  - `run-named-tests.py P-PRIV-06` -> NAMED P-PRIV-06 passed=11/11; `P-COST-01` -> NAMED P-COST-01 passed=33/33.
  - `run-named-tests.py P-PRIV-05` -> REFUSED: swift test wrote no xunit report (PlaceStore's GRDB does not build on
    this Windows box - the row's recorded limit; CI's Linux core job runs it). Its vitest half through the runner's own
    vitest_results/verdicts: 20/20 passed, the two new T-0296 names among them.
  - `ops/queue-check` -> QUEUE OK (287 tasks).
  - ACCEPTANCE re-quoted:
    1. RULE FIRST - R1-R7 above (09:38:35Z), before any code; the DDL test extended (migrationColumns, P-PRIV-05). MET.
    2. Through worker.fetch, same device same cell same UTC day once, second device again, next day again - the
       thirteen-step full-equality table over two variants, both tables whole after every step. MET.
    3. Population entries for the dedupe key (tag-ignores-device/-cell/-day) and the day boundary (day-one-ms-early/
       -late, purge-*): MISSED before (bar tag-ignores-device, CAUGHT before by the edited T-0293 test) and CAUGHT by name after. MET.
- 2026-10-07T11:24:33Z rv1-t0296 FAIL (PR #185 at 4a985fb3) B1 - ruled and closed by class:
  - RULING: B1 stands. identifyCaller returns a bucket from three sources - the session sub, the legacy x-scenic-device
    header (secret set, IDENTITY_HEADERS "1", no Bearer) and the shared unidentified bucket - and the sequence table ran
    only with IDENTITY_HEADERS unset, so the legacy source was never a variant. No disagreement with R1: the fix is test-only.
  - FIX (waitlistDedupe.test.ts, test names unchanged so the P-PRIV-06 bindings hold): the sequence is now the cross
    product {empty, holding} x {session-only, legacy-headers}; each step's bucket is bucket(mode, who) and every expected
    row is computed from it. Five steps added on 2026-10-06 (18 total): a malformed Bearer beside a C header
    (unidentified in both modes; a repeat), C header no Bearer (C under the flag, unidentified without), C again (repeat),
    D header (counts under the flag), C at the other cell, a C header with a valid Bearer for A at the other cell (A's
    bucket; a header bucket would be a repeat under the flag). The meta-test now asserts the four traces pairwise
    distinct and that the steps whose bucket the mode moves are exactly the header-only steps (4). The no-device-id test
    runs every step in both modes and forbids DEVICE_C/DEVICE_D too.
  - RED: the oracle's bucket made mode-blind (`return UNIDENTIFIED;` for header steps) -> 3 failed | 1 passed (4), the
    meta-test among them; restored -> the four touched files 20/20 passed.
  - POPULATION regionMutants.mjs MIN_MUTATIONS 66 -> 68: legacy-identity-constant (rv1's mutant: the deviceIdentity
    fallback replaced by a constant unidentified) and malformed-bearer-falls-to-header (sibling: a Bearer that fails the
    BEARER shape is passed to identifyCaller as absent, so under the flag it falls through to the header).
    BEFORE (test at 4a985fb3): `RESULT caught=0 missed=2 trap=0 of 2` - MISSED legacy-identity-constant, MISSED
    malformed-bearer-falls-to-header.
    AFTER `--only=` those two + identity-constant, identity-header-only: `RESULT caught=4 missed=0 trap=0 of 4` - the two
    new ones CAUGHT by `same device same cell same day counts once; ...`.
- 2026-10-07T11:41:44Z rv1 FINAL GATES on 53f03298 (git fetch origin; merge origin/main bringing T-0292 PR #183 -
  sweepRequests.ts, sharedEnvWorker.test.ts, P-COST-01 at 36, configAnswerPath's index.ts hash; auto-merged, no
  conflict in PINS.yaml or named-tests.json; `git merge-base --is-ancestor origin/main HEAD` -> ANCESTOR):
  - `npx vitest run` -> Test Files 71 passed (71), Tests 2108 passed (2108), exit 0.
  - `run-named-tests.py P-COST-01` -> NAMED P-COST-01 passed=36/36; `P-PRIV-06` -> NAMED P-PRIV-06 passed=11/11.
  - `run-named-tests.py P-PRIV-05` -> NAMED P-PRIV-05 passed=31/32: the one RED is the swift half
    PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail() MISSING - expected on this Windows box
    (PlaceStore's GRDB does not build here; CI's Linux core job runs it); every vitest name passed.
  - `ops/queue-check` -> QUEUE OK (288 tasks).
  - ACCEPTANCE re-quoted: 1 RULE FIRST - MET (R1-R7; rv1 B1 ruled above before the fix). 2 Through worker.fetch, the
    dedupe sequence (now 18 steps) over {empty, holding} x {session-only, legacy-headers}, both tables whole after
    every step - MET. 3 Population entries MISSED before and CAUGHT by name after - MET, now including
    legacy-identity-constant and malformed-bearer-falls-to-header (floor 68). All else as at 4a985fb3.
