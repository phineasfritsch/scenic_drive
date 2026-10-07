---
id: T-0304
title: /ledger holds the "session sub only" identity by behaviour (not only by the request-read whitelist) and caps each user's writes per day
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T17:44:56Z
lease_expires_at: 2026-10-08T05:44:56Z
worktree: .worktrees/T-0304
branch: task/T-0304
exclusive: []
touches: [services/api/src/ledger.ts, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PRIV-04, P-COST-01]
reviewer: null
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
