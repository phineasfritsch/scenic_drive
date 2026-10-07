---
id: T-0302
title: Worker /ledger - a signed-in device records which Surprise places it was shown (place id + H3-5 cell + UTC day) and reads back its last 90 days, so the 90-day no-repeat survives reinstall; nothing finer than H3-5 is ever stored
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T15:53:34Z
lease_expires_at: 2026-10-08T05:53:34Z
worktree: .worktrees/T-0302
branch: task/T-0302
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/migrations/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PRIV-04, P-PRIV-05, P-COST-01]
reviewer: agent/rv1-t0302
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
- 2026-10-07T16:59:57Z MUTATION POPULATION, agent/claude-opus-5. services/api/test/mutate/ledgerMutants.mjs: 40 entries,
  MIN_MUTATIONS = 40 literal, SUBJECTS src/ledger.ts, src/index.ts, src/accountStore.ts, migrations/0008_surprise_ledger.sql;
  14 body-validation branches, 5 gate entries, 8 window/day/order/idempotence entries, 3 user-scoping entries (read,
  write, purge), 2 D1-failure entries, 2 ROUTES entries, 2 deletion entries, 4 column/key entries; EQUIVALENT = [].
  `--prove-floor`: empty table, one short, a subject unmutated and a new subject each REFUSED; the real population quiet;
  exit=0. Added `--tests=` (run against named test files instead of TESTS) for the before half.
  BEFORE (src at fc19b4dc, `--only=read-ignores-user,window-91,place-max-dropped
  --tests=test/routes.test.ts,test/killSwitchRoutes.test.ts,test/sharedEnvWorker.test.ts,test/configSweep.test.ts` - the
  route-enumerating tests, which send /ledger requests but hold none of its semantics): `baseline green tests=21`,
  `MISSED place-max-dropped`, `MISSED window-91`, `MISSED read-ignores-user`, `RESULT caught=0 missed=3 trap=0 of 3`.
  AFTER (full TESTS): `baseline green tests=36`; `CAUGHT place-max-dropped by "every other POST body is 400
  invalid_request with its detail and the table unchanged, for each caller"`, `CAUGHT window-91 by "every row through
  worker.fetch answers the model's answers and leaves the model's whole table, for each caller"`, `CAUGHT
  read-ignores-user by "every row through worker.fetch answers ..."`; account-ledger-delete-dropped CAUGHT by "every user
  row is gone and every other row is unchanged; both refresh tokens revoked" (P-PRIV-04 seen red with the ledger delete
  removed); `RESULT caught=40 missed=0 trap=0 of 40`, exit=0. The two column mutants were first caught by accountDelete's
  positional seed insert, so they were re-run against migrationColumns.test.ts alone (P-PRIV-05 seen red with a forbidden
  column): `CAUGHT ledger-address-column by "no column of any table the shipped migrations create names home, address,
  breadcrumb, trail or speed (P-PRIV-05)"`, `CAUGHT ledger-lat-column by "the surprise ledger table is exactly (user_id,
  place_id, cell, day): ..."`, `RESULT caught=2 missed=0 trap=0 of 2`.
  Bindings: ops/lib/named-tests.json P-PRIV-05 +5 (migrationColumns ledger columns; ledger.test.ts meta, access table,
  refusals; ledgerWindow bounds) -> 25 vitest + 12 swift = 37; P-COST-01 +1 (ledger KILL exemption) -> 38; P-PRIV-04 no
  new name (the bound accountDelete tests now cover surprise_ledger). PINS.yaml: one appended dated sentence per row, no
  double quote; `python ops/lib/check-pins-yaml.py` -> `PINS-YAML ok pins=44 fields=355`.
- 2026-10-07T17:07:21Z ACCEPTANCE RE-RUN on c3c3af47 after `git fetch origin` + `git merge origin/main` (Already up to
  date; origin/main = e43d7465), agent/claude-opus-5:
  1. RULE FIRST: the 16:27:38Z entry rules identity (R1, sub only, 401/503), row shape (R2, 0008, day only, no
     coordinate), the window and retention (R4, R5), the quota/kill-switch exemption (R7, as T-0293 R8) and DELETE
     /account (R8, P-PRIV-04) before any src/ or migration change (fc19b4dc came after it).
  2. POST/GET table: ledger.test.ts - whole-body whitelist (32 refusal rows x 2 callers, table whole), corpus place id
     bounds 1 and 9223372036854775807 accepted, 2^63 refused, one row per (user, place, day), GET by full equality to the
     model, rows as functions of the caller with the meta-test `no row ignores the caller` - all through worker.fetch.
  3. Range table: ledgerWindow.test.ts - exactly 90 days returned and kept, 91 not returned and deleted on the next
     write (for both users), at 2026-10-04T23:59:59.999Z / 2026-10-05T00:00:00.000Z / 2026-10-05T23:59:59.999Z /
     2026-10-06T00:00:00.000Z.
  4. P-PRIV-05 DDL test extended (seen red: ledger-address-column and ledger-lat-column, 16:59:57Z entry); P-PRIV-04
     deletion test extended (seen red: account-ledger-delete-dropped); /ledger in routes, killSwitchRoutes,
     sharedEnvWorker, sweepRequests, requestReadSites and the configAnswerPath index.ts digest; PINS.yaml added values
     are inside existing double-quoted strings.
  5. Population 40 >= floor 40, 40/40 CAUGHT; three MISSED before and CAUGHT by name after (16:59:57Z entry).
  Gates: `npx vitest run` -> `Test Files  73 passed (73)`, `Tests  2118 passed (2118)`, exit=0.
  `run-named-tests.py P-PRIV-04` -> `NAMED P-PRIV-04 passed=51/51` exit=0; `P-COST-01` -> `passed=38/38` exit=0;
  `P-PRIV-05` -> `passed=36/37` exit=1, the one RED `PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail():
  MISSING` - GRDB-gated, does not build on the Windows box (T-0175 R2, recorded in the P-PRIV-05 row since T-0290); every
  vitest binding of the row, the five new ones among them, passed; CI's Linux core job runs it.
  `check-pins-yaml.py` -> `PINS-YAML ok pins=44 fields=355`; `ops/queue-check` -> `QUEUE OK (293 tasks)`.
  wc -l: src/ledger.ts 107, test/ledger.test.ts 172, test/ledgerHarness.ts 91, test/ledgerWindow.test.ts 59,
  test/mutate/ledgerMutants.mjs 192 (all under 300). NOT CLOSED: no per-user write cap (R9 note); the client half
  (the Keychain install id, the app calling /ledger) is M6 Apple-package work, not this task.
- 2026-10-07T17:33:04Z REVIEW PASS (round 1), agent/rv1-t0302 (not the owner), PR #191 at 99c82b54 (= origin/task/T-0302;
  `git merge-base --is-ancestor origin/main origin/task/T-0302` exit 0). Acceptance, line by line:
  1. RULE FIRST: the 16:27:38Z entry rules R1 identity (sub only; 503 auth_unavailable, 401), R2 row shape (0008, day
     only, no coordinate), R4/R5 window and retention, R7 the /waitlist-style exemption and R8 DELETE /account; it comes
     before fc19b4dc, the first src/ and migrations/ change. Met.
  2. ledger.test.ts: 32 whole-body refusals x 2 callers with the table compared whole; the access table runs through
     worker.fetch per caller and is compared by full equality to the model; the meta-test `no row ignores the caller`
     is there. Met.
  3. ledgerWindow.test.ts: 90 days returned and kept, 91 not returned and deleted for both users on the next write, at
     23:59:59.999Z / 00:00:00.000Z on each side of two midnights. Met.
  4. migrationColumns asserts the surprise_ledger columns exactly. accountDelete TABLES names surprise_ledger.
     /ledger appears in routes, killSwitchRoutes, sharedEnvWorker, sweepRequests, requestReadSites and the
     configAnswerPath digest. The PINS.yaml additions sit inside existing quoted values. Met.
  5. ledgerMutants.mjs has 40 entries against a literal floor of 40, and the MISSED-then-CAUGHT trio is quoted in the
     16:59:57Z entry. Met.
  Gates, each run bare on the review worktree at 99c82b54:
  - `npx vitest run`: `Tests  2 failed | 2116 passed (2118)`. Both failures are authAppleFields.test.ts timeouts at
    5000 ms on the contended box; this PR does not touch that file. Re-run alone: `Tests  232 passed (232)`.
  - `run-named-tests.py`: `NAMED P-PRIV-04 passed=51/51` and `NAMED P-COST-01 passed=38/38`, both exit 0.
    `NAMED P-PRIV-05 passed=36/37` exit 1. The one red is the GRDB-gated `noColumnNamesAPlaceOrATrail(): MISSING`,
    which cannot build on the Windows box (T-0175 R2); CI's core job runs it.
  - `check-pins-yaml.py`: `PINS-YAML ok pins=44 fields=355`. `ops/queue-check`: `QUEUE OK (293 tasks)`.
  - `gh pr checks 191`: core pass, pins-source-only pass.
  Reviewer mutants (not in the population; run over the ledger, ledgerWindow, accountDelete, requestReadSites,
  reflectionSites, migrationColumns, routes and killSwitchRoutes tests; source restored, `git status` clean afterwards):
  - rv-user-is-apple-claim. caller returns `claims?.apple ?? claims?.sub`, so a signed-in user's rows would be keyed by
    the Apple sub, which DELETE_LEDGER's device list never matches. CAUGHT by requestReadSites.test.ts "every line
    under src that reads the request is an approved site ... file by file, line by line" (44 passed / 1 failed).
  - rv-raw-secret-no-min-length. ledgerDepsFromEnv uses `env.SESSION_JWT_SECRET ?? null` instead of sessionSecret.
    CAUGHT by ledger.test.ts "no verified session is 401 and no usable secret is 503, for GET and POST, with the table
    unchanged" (44 passed / 1 failed).
  Recorded, not blocking:
  (a) R1's "sub only" is held behaviourally against the bare header, but only structurally against an `apple` or `act`
      claim and against a valid Bearer sent with x-scenic-device. No row signs a session that carries an apple claim,
      and no row sends a Bearer together with the legacy header. Both rv-user-is-apple-claim and the pre-review's
      get-scoped-by-legacy-device-header are caught only by the requestReadSites line whitelist. A cheap follow-up: a
      row signing {sub: USER_A, apple: ...} plus x-scenic-device: USER_B that must answer USER_A's rows.
  (b) POST /ledger has no per-user write cap; the author records this as NOT CLOSED. It should be filed as its own task.
  (c) ORDER BY place_id is text order ("101" sorts before "99"), and the model uses the same order. That is consistent;
      the client must not assume numeric order.
