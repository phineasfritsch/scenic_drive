---
id: T-0302
title: Worker /ledger - a signed-in device records which Surprise places it was shown (place id + H3-5 cell + UTC day) and reads back its last 90 days, so the 90-day no-repeat survives reinstall; nothing finer than H3-5 is ever stored
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T15:53:34Z
lease_expires_at: 2026-10-08T05:53:34Z
worktree: .worktrees/T-0302
branch: task/T-0302
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/migrations/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PRIV-04, P-PRIV-05, P-COST-01]
reviewer: null
depends_on: [T-0287, T-0278]
verify: [ops/check-pins]
acceptance:
  - "RULE FIRST in a dated Log entry: identity (the session JWT sub only - no session, no ledger: 401), the row shape (user, place_id, h3_5 cell, UTC day - migration 0008, no timestamp finer than a day, no coordinate), the 90-day window and retention (rows older than 90 days deleted on write), quota/kill-switch exemption (D1 only, no upstream - ruled like /waitlist T-0293 R8), and that DELETE /account removes every ledger row for the user (P-PRIV-04)"
  - "POST /ledger {place_id, cell} validates by whole-body whitelist (place id shape from the corpus, cell = a valid H3 resolution-5 id) and writes one row per (user, place, day) idempotently; GET /ledger returns exactly the caller's rows within 90 days by full equality; another user's rows never appear - table through worker.fetch with rows as functions of the user variant and a meta-test no row ignores it"
  - "Range table over the window: a row at exactly 90 days is returned, at 90 days + 1 is not and is deleted on the next write; every bound by the day boundary at 23:59:59.999Z / 00:00:00.000Z"
  - "P-PRIV-05 DDL test extended to the new table (seen red with a forbidden column); P-PRIV-04 deletion test extended (seen red with the ledger delete removed); every ROUTES-enumerating table extended for /ledger (memory parallel-worker-prs-conflict); new PINS.yaml values double-quoted (memory pins-yaml-strict)"
  - "A mutation population entry per validation branch, the window bound and the user scoping, with a literal floor; three MISSED before and CAUGHT by name after"
---
## Brief

Plan, Surprise Me: "Unlimited, 90-day no-repeat"; Worker list: "ledger (place ids + H3-5)". Today the no-repeat history
lives only on the device (Sources/ScenicKit/Surprise/SurpriseHistory.swift), so a reinstall forgets it. Privacy: the
server never holds a coordinate or anything finer than an H3-5 cell (plan, Telemetry and Worker rows).

## Log
- 2026-10-07T15:50:09Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 ledger).
- 2026-10-07T15:53:34Z claimed by agent/claude-opus-5; lease until 2026-10-08T05:53:34Z
- 2026-10-07T16:27:38Z RULINGS (author rule, before any code), agent/claude-opus-5:
  - R1 identity. The ledger user is the verified session JWT's `sub` (the install UUID, sessionJwt.ts verifySession)
    and nothing else: the Authorization Bearer is read at ONE site in src/ledger.ts. SESSION_JWT_SECRET unbound or
    shorter than MIN_SECRET_LENGTH -> 503 auth_unavailable (account.ts's answer); no Bearer, a malformed one or one that
    does not verify -> 401 unauthorized. NOT identifyCaller: its legacy x-scenic-device path and its shared
    `unidentified` bucket would let a header-only or unverified caller read or write a shared ledger. The `act` and
    `apple` claims are not read. Reinstall survival rests on the install UUID living in the Keychain, which iOS keeps
    across a reinstall; Sources/ScenicAPIClient/InstallIDProvider.swift says that keychain is the Apple package's (M6)
    - this task does not touch Sources/ and does not prove the client half.
  - R2 row shape. migrations/0008_surprise_ledger.sql creates surprise_ledger (user_id, place_id, cell, day), PRIMARY KEY
    (user_id, place_id, day); cell CHECK length 15, day CHECK length 10 (YYYY-MM-DD, the UTC day). No instant finer
    than a day, no coordinate, no corridor: the device history's corridor (SurprisePlaceMapping corridorCellE7, a 0.1
    degree cell, finer than H3-5) is never sent. The place id names a public corpus place, not the caller's position.
  - R3 body. POST /ledger takes exactly {place_id, cell} (whole-body key whitelist, the waitlist.ts shape). place_id is
    the corpus place id as the device holds it: SurprisePlaceMapping.candidate's `String(placeID)` of an Int64 that
    services/etl/etl/segid.py place_id makes `(fnv1a64 & MASK63) or 1` - a JSON string, canonical decimal, 1 ...
    9223372036854775807 (no sign, no leading zero, no padding). planRequest.ts PLACE_ID is NOT reused: it admits
    `34.0212_-118.4912`, a coordinate in a place id. cell is isResolution5Cell (h3Res5.ts, the /telemetry and
    /waitlist rule). Anything else -> 400 invalid_request with a detail, nothing written.
  - R4 write. One row per (user, place, UTC day): INSERT ... ON CONFLICT (user_id, place_id, day) DO NOTHING, so a
    repeat the same day is 200 {recorded: true} with the first row (its cell) kept. Before the insert, every row of
    EVERY user dated before the window's first day is deleted (retention; the waitlist_seen purge shape). D1 missing or
    any D1 throw -> 503 ledger_unavailable.
  - R5 window. today = now's UTC day; first = today - 90 days (UTC calendar). GET /ledger returns exactly the caller's
    rows with day >= first as {places: [{place_id, cell, day}]}, ordered day DESC then place_id ASC. So a row dated
    today-90 is returned and today-91 is not, and at T 23:59:59.999Z vs T+1 00:00:00.000Z the row dated T-90 flips
    from returned to not-returned (and is deleted by the next write). GET writes nothing.
  - R6 methods. GET or POST only; anything else 405 {error: "GET or POST only"} before any secret, session or D1 read.
    Order: method, secret (503), session (401), body (400, POST), D1 (503).
  - R7 cost. D1 only, no upstream, no Analytics Engine: /ledger is OPERATIONAL - outside the quota and the kill switch -
    ruled exactly as /waitlist T-0293 R8. Every ROUTES-enumerating table gets /ledger (routes, killSwitchRoutes
    OPERATIONAL_ROUTES, sharedEnvWorker OPERATIONAL, sweepRequests REQUESTS, requestReadSites APPROVED,
    configAnswerPath index.ts digest).
  - R8 deletion (P-PRIV-04). DELETE /account deletes every surprise_ledger row whose user_id is one of the user's
    devices (accountStore USER_DEVICES: the session device plus every device bound to the user's Apple subs), in the
    same one batch; accountDelete.test.ts TABLES gets surprise_ledger as user-keyed.
  - R9 privacy (P-PRIV-05). migrationColumns.test.ts asserts the surprise_ledger columns are exactly (user_id,
    place_id, cell, day), read from D1.
  - NOT CLOSED (ruled out of scope, to be filed): no per-user write cap - a signed-in device can write many distinct
    place ids per day; the GET answer is bounded only by the window. Unlike /waitlist, nothing upstream is spent.
- 2026-10-07T16:41:42Z RED then GREEN, agent/claude-opus-5. Tests first (ledger.test.ts, ledgerWindow.test.ts,
  ledgerHarness.ts; migrationColumns, accountDelete, routes, killSwitchRoutes, sharedEnvWorker, sweepRequests extended),
  run before any src/ or migration change: `npx vitest run` over those eight files printed
  `Tests  25 failed | 22 passed (47)`, exit=1 - FAILED by name: all five ledger.test.ts route tests (the meta-test
  `no row ignores the caller` is green without code, as it should be), both ledgerWindow.test.ts tests, migrationColumns
  `the surprise ledger table is exactly (user_id, place_id, cell, day): ...` (no such table), every accountDelete test
  (the TABLES whitelist names surprise_ledger, which no migration created; the seed insert fails), routes `every route
  is enumerable`, configSweep's and sharedEnvWorker's sweeps (REQUESTS has /ledger, ROUTES not). Then
  migrations/0008_surprise_ledger.sql, src/ledger.ts, the ROUTES entry, accountStore DELETE_LEDGER in the deletion batch,
  configAnswerPath's index.ts digest (5dbcb7fa...) and requestReadSites' approved ledger.ts sites: the same files plus
  configAnswerPath, requestReadSites and reflectionSites printed `Test Files  11 passed (11)` `Tests  59 passed (59)`,
  exit=0. A first full run timed out 14 tests at 5000 ms on the contended box (authApple*, regionGateOrder, waitlist*,
  one ledger table); the ledger seed now applies only 0008 in one batch and the three table tests take 60 s.
