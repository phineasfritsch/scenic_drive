---
id: T-0304
title: /ledger holds the "session sub only" identity by behaviour (not only by the request-read whitelist) and caps each user's writes per day
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T17:44:56Z
lease_expires_at: 2026-10-08T05:44:56Z
worktree: .worktrees/T-0304
branch: task/T-0304
exclusive: []
touches: [services/api/src/ledger.ts, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PRIV-04, P-COST-01]
reviewer: agent/rv2-t0304
depends_on: [T-0302]
verify: [ops/check-pins]
acceptance:
  - "Behaviour rows through worker.fetch: a session signed {sub: USER_A, apple: X} answers USER_A's rows; the same session plus x-scenic-device: USER_B answers USER_A's rows; an act claim changes nothing - full equality; rv1-t0302's rv-user-is-apple-claim and fm-t0302's get-scoped-by-legacy-device-header are CAUGHT by these rows by name, not only by requestReadSites"
  - "RULE then implement a per-user daily write cap on POST /ledger (a number with its reason, e.g. the paid tier's Surprise ceiling); the cap+1th write answers 429 with the table unchanged; range table at cap-1, cap, cap+1 and across the UTC midnight"
  - "Population entries for both, MISSED before and CAUGHT by name after; new PINS.yaml text double-quoted (memory pins-yaml-strict)"
---
## Brief

rv1-t0302 recordables (a) and (b) on PR #191: identity is held only by the exact-line whitelist against an apple/act
claim or a header beside a valid Bearer; and POST /ledger has no per-user write cap (author marked NOT CLOSED).

## Log
- 2026-10-07T17:44:38Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0302's recordables.
- 2026-10-07T17:44:56Z claimed by agent/claude-opus-5; lease until 2026-10-08T05:44:56Z
- 2026-10-07T17:48:06Z RULINGS before code, agent/claude-opus-5.
  - R1 the cap. LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid, BY REFERENCE (200 today; never a second literal in src;
    the tests carry the literal 200 so a moved reference fails them). Reason: a ledger row records one place a Surprise
    answer showed, and the most Surprise reaches any tier is allowed per UTC day is the paid figure (quota.ts: the plan
    table's "Unlimited" is the paid PLAN cap by reference). An honest paid day fits; one user's table is bounded at
    200 rows a day, 200 x 91 days at most. Cache hits spend no Surprise quota, so the cap is a storage bound, not a
    quota mirror: more than 200 distinct places shown in one day is ruled beyond honest use.
  - R2 what counts. Rows, not requests: the caller's rows dated today (UTC), counted inside the write. A POST is
    ADMITTED when the caller holds fewer than the cap's rows today OR already holds this place today (the idempotent
    repeat of T-0302 R4 stays 200 at the cap and adds nothing). A POST not admitted is 429 {error: "ledger_daily_cap"}
    and writes NOTHING - no insert and no purge; the table is unchanged. Other users' rows, and the caller's rows of
    earlier days, never count and never admit. The day turns at 00:00:00.000Z.
  - R3 atomic, no race ruling needed. One D1 batch (one transaction, statements in order): SELECT the admission, then
    the purge and the insert each guarded by the same admission predicate (one SQL fragment). Concurrent POSTs from one
    user cannot overshoot. Order stays method, secret (503), session (401), body (400), D1 (503), admission (429).
  - R4 identity by behaviour (rv1-t0302 recordable a). Through worker.fetch, every combination of caller sub (A, B),
    claims ({}, {apple}, {act = the other user's id}, {apple, act}), x-scenic-device (absent, the other user) and
    IDENTITY_HEADERS (unset, "1") answers GET, POST, GET exactly as the T-0302 model for the sub, with the seed holding
    rows keyed by the other user and by the apple id. Expectations are a function of the sub; a meta-test holds no
    row's expectation is the same for both subs.
  - R5 population. New entries in ledgerMutants.mjs, each MISSED with --tests= the T-0302 TESTS list and CAUGHT by name
    with the new test file added: rv-user-is-apple-claim, rv-user-is-act-claim, get-scoped-by-legacy-device-header,
    post-scoped-by-legacy-device-header, and the cap's every bound and branch. T-0302 anchors that the new SQL moves
    are re-anchored to the same intent. MIN_MUTATIONS rises to the new count.
- 2026-10-07T17:59:45Z RED then GREEN, population, agent/claude-opus-5.
  - RED before any src change: `npx vitest run test/ledgerIdentity.test.ts test/ledgerCap.test.ts` printed
    `Tests  1 failed | 3 passed (4)`, exit=1 - FAILED by name: ledgerCap.test.ts `at cap-2, cap-1 and cap rows held
    and across the UTC midnight, the write answers 200 or 429 ledger_daily_cap and leaves exactly the expected table,
    for each writer` (every 429 row answered 200). ledgerIdentity.test.ts is green before code, as it should be: the
    shipped handler already keys by the sub; its red is the population's (below), the behaviour that was only
    held by the requestReadSites whitelist.
  - GREEN after src/ledger.ts (LEDGER_DAILY_CAP, ADMIT/PURGE/INSERT under one ADMITTED predicate, one batch):
    ledgerIdentity, ledgerCap, ledger, ledgerWindow, requestReadSites, accountDelete: `Tests  33 passed (33)`.
    requestReadSites' APPROVED lines for ledger.ts are unchanged (no new request read).
  - Population (ledgerMutants.mjs, 59 entries, floor 59; `--prove-floor`: four arms REFUSED, real population quiet).
    BEFORE, `--only=<19 new ids> --tests=<the T-0302 TESTS list>`: `baseline green tests=36`, every one MISSED,
    `RESULT caught=0 missed=19 trap=0 of 19`. AFTER, default TESTS (+ ledgerIdentity, ledgerCap), the 19 new ids
    plus the six re-anchored T-0302 entries (purge-bound-inclusive, purge-dropped, written-day-is-first,
    write-other-user, purge-caller-only, write-failure-answers-200): `baseline green tests=40`,
    `RESULT caught=25 missed=0 trap=0 of 25`. CAUGHT by name: rv-user-is-apple-claim, rv-user-is-act-claim,
    get-scoped-by-legacy-device-header, post-scoped-by-legacy-device-header by ledgerIdentity `an apple or act claim
    and an x-scenic-device header beside a valid Bearer change nothing: ...`; cap-unbounded, cap-plus-one,
    cap-minus-one, cap-free-tier, cap-inclusive, cap-counts-every-day, cap-counts-every-user, cap-refuses-held,
    cap-held-any-user, cap-held-any-day, cap-refusal-answers-200, cap-admission-ignored, cap-purge-unguarded,
    cap-insert-unguarded, cap-today-is-first by ledgerCap `at cap-2, cap-1 and cap rows held ...`; the six
    re-anchored ones by ledger.test.ts as before. One stale anchor (cap-refuses-held spanned the + concatenation)
    was refused by the driver's STALE check and re-anchored before any run counted.
  - Named tests: P-PRIV-04 binds ledgerIdentity's two (53), P-COST-01 ledgerCap's two (40); PINS.yaml text appended
    inside the existing double-quoted fields; `check-pins-yaml.py`: `PINS-YAML ok pins=44 fields=355`.
- 2026-10-07T18:07:12Z GATES, agent/claude-opus-5, each run bare. origin/main merged twice (63e8f670, then 4ece8567: T-0294's
  Sources/, apps/ios and ops/ only - nothing under services/api, pins/ or named-tests.json, so the Worker gates
  below hold on the merged head f6c76bdf).
  - `npx vitest run` (services/api): `Test Files  75 passed (75)`, `Tests  2122 passed (2122)`, exit 0.
  - `run-named-tests.py`: `NAMED P-PRIV-04 passed=53/53` and `NAMED P-COST-01 passed=40/40`, both exit 0.
  - `check-pins-yaml.py`: `PINS-YAML ok pins=44 fields=355`. `ops/queue-check`: `QUEUE OK (295 tasks)`.
  - Acceptance: (1) identity rows by full equality through worker.fetch, rv-user-is-apple-claim and
    get-scoped-by-legacy-device-header CAUGHT by name by ledgerIdentity (plus the act and POST variants) - MET.
    (2) cap ruled (R1, 200 = DAILY_SURPRISE_QUOTA.paid), the (cap+1)th write 429 with the table unchanged, range rows
    at cap-2/cap-1/cap held and both sides of 00:00:00.000Z - MET. (3) population MISSED before (0/19) and CAUGHT
    by name after (25/25); PINS.yaml text inside the double-quoted fields, strict check ok - MET.
  - Line counts: ledger.ts 122, ledgerCap.test.ts 99, ledgerIdentity.test.ts 79, ledgerMutants.mjs 217.
- 2026-10-07T18:38:42Z rv1-t0304 FAIL (PR #192, head 9899e514) closed, agent/claude-opus-5. RULINGS before code.
  - B1 (R2: a refusal writes nothing, no purge). Every REFUSED row seeded only the OTHER user's stale row, so a purge
    of the writer's own expired rows on refusal survived. Ruled: ledgerCap's rows are functions of (writer, stale
    owner), the stale owner ranging over {writer, other} in EVERY row, REFUSED and RECORDED; full-table equality as
    before; meta-tests: no row ignores the writer, no row ignores the stale owner, and both owners occur under both
    answers.
  - S1 (stillOpen: D1 returning no admission row). Ruled: the answer turns on the batch's first result alone; 200
    only when `admitted` is exactly the number 1; no batch result, an empty admission result, a row without
    `admitted`, null, 0, "1", true or 2 is 429 ledger_daily_cap (fail closed, never 200 and never 503 - the batch
    returned, so it is not a D1 failure). One row per shape through worker.fetch over a D1 stub; full equality.
  - Population: rv-refusal-purges-own-stale (`WHERE day < ?5 AND ${ADMITTED}` -> `... AND (user_id = ?1 OR
    ${ADMITTED})`) and rv-no-admission-row-admits (`admit?.results[0]?.admitted` -> `... ?? 1`); MIN_MUTATIONS
    59 -> 61.
  - BEFORE (old tests): `--only=rv-refusal-purges-own-stale,rv-no-admission-row-admits`: `baseline green
    tests=40`, `MISSED rv-refusal-purges-own-stale`, `MISSED rv-no-admission-row-admits`, `RESULT caught=0 missed=2
    trap=0 of 2`.
  - AFTER: `--only=` the two plus the touched purge entries cap-purge-unguarded, purge-caller-only: `baseline green
    tests=43`, `RESULT caught=4 missed=0 trap=0 of 4`; rv-refusal-purges-own-stale CAUGHT by "at cap-2, cap-1 and
    cap rows held ..."; rv-no-admission-row-admits CAUGHT by "the answer turns on D1's admission row alone: only
    admitted exactly 1 records, every other batch result shape is 429". `--prove-floor`: real population quiet.
  - Named tests: the three new ledgerCap tests bound to P-COST-01. Line counts: ledgerCap.test.ts 142,
    ledgerMutants.mjs 220.
- 2026-10-07T18:40:09Z GATES on 704c66e5, agent/claude-opus-5, each run bare. `git fetch origin` + merge origin/main: `Already up
  to date` (origin/main 4ece8567 is already an ancestor).
  - `npx vitest run` (services/api): `Test Files  75 passed (75)`, `Tests  2125 passed (2125)`, exit 0.
  - `run-named-tests.py`: `NAMED P-PRIV-04 passed=53/53` and `NAMED P-COST-01 passed=43/43`, both exit 0.
  - `check-pins-yaml.py`: `PINS-YAML ok pins=44 fields=355`. `ops/queue-check`: `QUEUE OK (295 tasks)`.
  - Acceptance: (1) identity rows unchanged - MET. (2) cap rows now range over the stale owner; the (cap+1)th write is
    429 with the table unchanged whoever owns the stale row; no admission row is 429 - MET. (3) population 61/61 floor;
    the rv1-t0304 pair MISSED before (0/2), CAUGHT by name after (4/4 with the touched purge entries) - MET.
- 2026-10-07T18:48:09Z agent/rv2-t0304 REVIEW round 2 PASS (PR #192, head e0fb89df). Re-applied rv-refusal-purges-own-stale through
  ledgerMutants.mjs --only: CAUGHT by "at cap-2, cap-1 and cap rows held and across the UTC midnight, the write answers
  200 or 429 ledger_daily_cap and leaves exactly the expected table, for each writer" (caught=1 of 1). Own mutant
  rv2-purge-binds-window-start-as-today (PURGE_LEDGER bound with the window start as ?3, so its admission count reads an
  empty day and a refusal purges): CAUGHT by the same test (1 failed, 14 passed). vitest 75 files 2125/2125, exit 0.
  ops/queue-check bare: QUEUE OK (295 tasks). gh pr checks 192: pins-source-only pass, core pending (not confirmed).
  origin/main 4ece8567 is an ancestor of the head. Signed off; not merged.
