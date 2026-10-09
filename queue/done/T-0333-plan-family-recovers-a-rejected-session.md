---
id: T-0333
title: Before IDENTITY_HEADERS closes, the plan family recovers a session the Worker cannot verify - the Worker signals an unverifiable Bearer (e.g. 401 session_rejected) on /plan, /trip and /loop, and the client drops the session, re-acquires once and retries, so a SESSION_JWT_SECRET rotation or SESSION_TTL_S change never downgrades a subscriber for the rest of the launch
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T10:41:55Z
lease_expires_at: 2026-10-09T20:41:55Z
worktree: .worktrees/T-0333
branch: task/T-0333
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-STORE-02, P-COST-01, P-COST-04]
reviewer: agent/rv2-t0333
depends_on: [T-0322]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 Worker table, through the SHIPPED ROUTES: sessionCarriesAct.test.ts's cross product /plan,/trip,/loop x Bearer {session act live, act expired, no act, expired, wrong secret, wrong TTL, malformed, absent} x IDENTITY_HEADERS {1, unset} x header {live, expired, absent} EQUALS the reference `ruled` picks, where ruled gains `rejected` exactly for the four unverifiable Bearers under unset; the rejected reference is the literal {401, {error: session_rejected}} with the SEEDED quota state, zero upstream fetches and nothing logged; the no-row-ignores-its-variant meta-test covers the new value. Plus `a rejected Bearer reserves nothing` over an EMPTY quota namespace: route x the four unverifiable Bearers x flag - unset is 401 with quota state {} and 0 fetches, 1 equals the header reference (the device bucket reserved). sessionIdentity.test.ts's flag-closed rows read 401 too. `npx vitest run test/sessionCarriesAct.test.ts test/sessionIdentity.test.ts test/requestReadSites.test.ts` green."
  - "A2 Client table, through the SHIPPING PlanClient (plan and reroute), TripClient and LoopClient over a REAL SessionStore and one ScriptedTransport: route x held {Keychain session (acquisition unspent), session acquired this launch (spent)} x Worker {200, 401 then 200, 401 then 401} - the WHOLE ordered request list (attest and route) EQUALS the list recomputed from the variant: 401 once -> the token handed back, ONE acquisition, the byte-identical body resent ONCE with the new Bearer; 401 twice -> exactly two route requests, never a third, no second re-acquisition; a request that carried no Bearer is never retried; meta-test that no row ignores held or Worker. `swift test --filter PlanSessionRetryTests` green."
  - "A3 RED first by name: every new or changed test FAILED by name before the code commit (quoted in the Log), then green."
  - "A4 Population: attestMutants.mjs gains the Worker 401 entries (no 401, 401 under the flag, 401 after the reservation, a 401 for an absent header) and ops/mutate/session_mutations.py the client entries (no retry, retry without the hand-back, re-grant every rejection, never re-grant, retry a Bearer-less request), each CAUGHT by name; floors raised; `python ops/lib/check-mutate-population.py` green."
  - "A5 Gates on the merged head: `python ops/lib/run-named-tests.py P-STORE-02` and `P-COST-04` all passed; digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt and every content pin over a touched file re-approved; check-pins-yaml; queue-check; apps/ios untouched (no Apple CI)."
---
## Brief

T-0322 owner stillOpen 1 / rv2-t0322 note (PR #212): while IDENTITY_HEADERS is "1" an unverifiable Bearer now falls
back to the header (no downgrade). After the owner closes the flag (T-0322 R5 step 3), a Bearer the Worker cannot
verify reads anon, and PlanClient / TripClient / LoopClient have no 401 path, so nothing recovers within the launch.
This must land BEFORE step 3. MEASURE FIRST (what each route answers today for an unverifiable Bearer; whether a 401
costs a quota reservation - it must not; how many re-acquisitions per launch the session budget allows; P-COST-04's
request cap per plan), then write the acceptance: a full-equality table over {Bearer valid, expired, rotated secret,
wrong TTL, malformed} x {flag 1, closed} for the Worker answer, and for the client {401 once -> re-acquire + one retry,
401 twice -> no loop}.

## Log
- 2026-10-08T20:50:40Z filed by agent/claude-opus-5 (orchestrator) from T-0322 stillOpen 1.
- 2026-10-09T10:41:55Z claimed by agent/claude-opus-5; lease until 2026-10-09T20:41:55Z
- 2026-10-09T10:58:00Z MEASURED (agent/claude-opus-5, worktree at 322d5ed0). A scratch vitest probe (deleted, never
  committed) drove ROUTES /plan, /trip, /loop with SESSION_JWT_SECRET set, x-scenic-device DEVICE, no account header,
  an EMPTY fake quota, each unverifiable Bearer {expired, wrong secret, wrong TTL, malformed} x flag {1, unset}. All 24
  rows answer 200 routed. Flag "1": billed to the device bucket (`device:0f8b6d5e-...` plan:1 / trip:1 / loop:1).
  Flag unset: billed to the SHARED bucket, e.g.
  `PROBE /plan | wrong secret | flag unset | 200 routed | fetches 7 | quota {"device:unidentified":{"daily":{"day":"2026-10-06","plan":1,"loop":0}},"global":{"monthly":{"month":"2026-10","calls":12}}}`
  `PROBE /trip | malformed | flag unset | 200 routed | fetches 7 | quota {"device:unidentified":{"daily":{"day":"2026-10-06","plan":0,"loop":0,"trip":1}},"global":{"monthly":{"month":"2026-10","calls":12}}}`
  `PROBE /loop | expired | flag unset | 200 routed | fetches 1 | quota {"device:unidentified":{"daily":{"day":"2026-10-06","plan":0,"loop":1}},"global":{"monthly":{"month":"2026-10","calls":3}}}`
  and the same per route for every unverifiable kind. So TODAY a closed flag plus a rotated secret silently downgrades
  a subscriber to the shared anon bucket AND spends a reservation there (7 / 7 / 1 upstream requests). Client today:
  PlanClient, TripClient and LoopClient hand any status to their reader; a 401 is the reader's default (no retry);
  SessionStore spends ONE acquisition per purchase value per launch (`spent`), so a session acquired this launch and
  then rejected cannot be renewed within it. Budgets: ATTEST_CHALLENGES_PER_DEVICE_HOUR = 10 and
  ATTEST_CHALLENGES_PER_DAY = 10000 (attestStore.ts); P-COST-04 caps upstream requests PER PLAN at PLAN_UPSTREAM_COST
  12 / LOOP_UPSTREAM_COST 3 / TRIP_UPSTREAM_COST 12, reserved in guardedPlan before the first fetch.
- 2026-10-09T10:58:00Z RULED before code:
  R1 Worker: with SESSION_JWT_SECRET set and IDENTITY_HEADERS not "1", a /plan, /trip or /loop request whose
     `authorization` header is present but yields no verified claims (expired, another secret, another TTL, malformed,
     or not the Bearer scheme) is 401 {"error":"session_rejected"}. The order up to the identity is unchanged (kill,
     method, body, region, deps, place); the 401 is answered right after identify and BEFORE any plan-token recall,
     reservation, upstream request or log. Under "1" T-0322's fallback stands (the header identity). No header:
     unchanged. Without the secret: unchanged, never 401. Only the plan family: a new identifySession returns the
     rejection; identifyCaller (telemetry, waitlist) maps it to today's unidentified anon, unchanged; routerDeps'
     identify marks the identity `rejected`, which the three handlers answer.
  R2 Cost: a 401 reserves nothing and makes zero upstream requests - shown on a bucket at its limit (the table) AND on
     an empty quota (where a reserve-then-401 would show in the state). P-COST-04 is per plan and unchanged: the
     resent request is its own plan with its own reservation; per user action at most one plan reserves.
  R3 Client: PlanSessionProvider gains planSessionRejected(_ token:). A reply with status 401 to a plan-family request
     that CARRIED a Bearer hands that token back, asks planSession(account:) again for the same purchase, and resends
     the byte-identical body ONCE with the answer (a Bearer, or none); that reply is final and read by the route's
     reader whatever it is. Never a third request; a 401 to a Bearer-less request is not retried. The resend carries
     the same single 2-dp coordinate in identical bytes, refused unused the first time, so the server learns no second
     coordinate: CLAUDE.md's one-coordinate-per-user-action invariant holds.
  R4 Budget: SessionStore.planSessionRejected drops the session as sessionRejected does and, the FIRST time in a launch
     for that purchase value, returns the value's acquisition (un-spends it), so the next ask acquires once more; a
     second plan-family rejection for the same value in the launch drops without granting. At most 2 acquisitions
     (challenges) per purchase value per launch, under the 10 per device-hour limit. A token no longer current is
     ignored. The ledger's sessionRejected is unchanged (no re-grant).
  R5 The Brief's "e.g. 401 session_rejected" is ruled as exactly that literal. The Brief's client table {401 once,
     401 twice} is crossed with held {unspent, spent}, because the spent case is the one today's store cannot recover.
- 2026-10-09T11:12:00Z R6 (ruled with the tests, before code): the second 401 hands its token back too (no re-grant -
  R4 already spent it), so the launch's next action sends no known-rejected Bearer; the reply is still final.
- 2026-10-09T11:12:00Z RED by name, before any src/ or Sources/ change (tests only in the tree):
  `npx vitest run test/sessionCarriesAct.test.ts test/sessionIdentity.test.ts` -> `Tests  72 failed | 146 passed (218)`:
  36 = sessionCarriesAct `<route>, Bearer <expired|wrong secret|wrong TTL|malformed>, IDENTITY_HEADERS unset, header
  <live|expired|absent>: the answer is the ruled reference` (3 x 4 x 3); 12 = `<route>, Bearer <4>, IDENTITY_HEADERS
  unset, EMPTY quota: a rejected Bearer reserves nothing (T-0333 R2)`; 24 = sessionIdentity's 22 INVALID rows, the
  `1 ms past the second S` row and `a lower-case bearer scheme and a Basic credential are not a session`. Every flag-"1"
  row passed (T-0322's fallback, unchanged). `swift test --filter PlanSessionRetryTests` -> `Test run with 2 tests in 1
  suite failed ... with 16 issues`: `a 401 hands the session back, re-acquires once and resends the same bytes once;
  never a third request` FAILED for exactly the 16 rows {plan, reroute, trip, loop} x {keychain, acquired} x
  {rejectsOnce, rejectsAlways}; its 20 answers / noSession rows and the meta-test passed (today's behaviour). The
  later `the resend carries the same purchase` test calls only shipped API but was written after the code; its red is
  mutant 89.
- 2026-10-09T12:05:00Z GREEN and POPULATION. `npx vitest run test/sessionCarriesAct.test.ts test/sessionIdentity.test.ts
  test/requestReadSites.test.ts test/telemetry*.test.ts test/waitlist*.test.ts test/plan*.test.ts test/loop*.test.ts
  test/trip*.test.ts` -> `Test Files  26 passed (26)`, `Tests  504 passed (504)`. `swift test --filter
  "PlanSessionRetryTests|PlanBearerTests|SessionAccountTests|SessionStoreTests|SessionSkewTests|AccountTokenHeaderTests|PlanRerouteWireTests"`
  -> `Test run with 29 tests in 7 suites passed`. Worker population (attestMutants.mjs, floor 85 -> 92, subjects + plan.ts,
  trip.ts, loop.ts, tests + sessionCarriesAct.test.ts): `--only` the 7 new entries and the re-anchored deps-bearer-not-read
  -> all 8 CAUGHT by name (reject-never, reject-plan/trip/loop-unanswered by `<route>, Bearer expired, IDENTITY_HEADERS
  unset, header live: the answer is the ruled reference`; reject-under-flag by the IDENTITY_HEADERS 1 row; reject-absent-
  header by `with the secret and IDENTITY_HEADERS unset or 0, no Bearer is the unidentified bucket, anon`; reject-unmarked
  and deps-bearer-not-read by the request-sites whitelist). Swift population (session_mutations.py, floor 81 -> 90, test
  files 8 -> 9, FAMILY subject; 71-74 re-anchored on the clients' `session: session` and the family send): MISSED BEFORE -
  the runner's FILTER lacked PlanSessionRetryTests and 82-88 were `MISSED exit=0 no test objected` (71-74 caught); with
  the suite in FILTER, `--only 82..90` -> `caught by the test that names it: 9 of 9 (wrong killer 0, trapped 0,
  compile-only 0, MISSED 0, skipped 0)`. check-mutate-population first refused PlanFamilySend.swift (no SUBJECT_MODULES
  entry), then `every added module is covered or allowlisted; the floor of 144 holds` once session.py declared it.
  Digests: 5 Sources rows re-approved from the committed blobs, PlanFamilySend.swift added. P-STORE-02's named table
  binds 28 more names (246, sha256 190b9ca64c61...), `NAMED-TABLE P-STORE-02 ok - 246 distinct names`.
- 2026-10-09T12:59:44Z RULED (agent/claude-opus-5, owner) on rv1-t0333 FAIL (PR #225, head 20358065), before any change:
  B1 accepted by class. R3's "(a Bearer, or none)" has a none branch no row reached: every row's renewal succeeded.
  R7: PlanSessionRetryTests gains a Renewal variant {renews, assertRejected (/attest/assert answers 400 -> the store
  forgets the session), budgetSpent (/attest/challenge answers 429 challenge_rate_limited after this launch's first
  challenge)} crossed with route x held x Worker (108 rows). The expected whole request list is recomputed from it: a
  failed renewal after a 401 is `send(T), challenge, [renew(key)], send(nil)` and the next action is `send(nil)` (the
  acquisition stays spent); Worker answers never asks for a renewal, so there the variant is moot by construction. The
  meta-test gains the renewal-variant pair and the rule that a failed renewal's rows carry the rejected Bearer on
  exactly one route request. session_mutations.py gains "91 the failed renewal resends the rejected token"
  (`request(renewed)` -> `request(renewed ?? bearer)`), MISSED at 20358065 by the reviewer (116/116), CAUGHT by name
  now; MIN_MUTATIONS 90 -> 91. No Sources/ file changes, so no digest is re-approved; no new test function, so
  P-STORE-02's named table and count are unchanged.
  B2 accepted: A4 named "401 after the reservation". attestMutants.mjs gains "reject-plan-after-reservation" - plan.ts
  answers the 401 only after guardedPlan has reserved (a body that fetches nothing), so status, body and fetch count
  match the reference and only the quota state differs; it must be CAUGHT by name by the EMPTY-quota rows (R2);
  MIN_MUTATIONS 92 -> 93.
- 2026-10-09T13:16:08Z FIX ROUND 1 and ACCEPTANCE RE-QUOTED (agent/claude-opus-5) on head f73ecf64. `git fetch origin`
  then `git merge-base --is-ancestor origin/main HEAD` -> exit 0 (main has not moved since 20358065's merge; no merge
  commit needed), so f73ecf64 IS the merged head. Since 20358065 only PlanSessionRetryTests.swift, session_mutations.py,
  attestMutants.mjs and this file changed; no Sources/ or apps/ios file, so no digest row moves.
  B1: `python ops/mutate/session.py --only 91` at 0c233e4d (population committed, table not yet) -> `MISSED 91 the
  failed renewal resends the rejected token exit=0 no test objected`, `MUTATE FAILED caught=0/1`; at f73ecf64 (the
  renewal variant in the table) -> `caught by the test that names it: 1 of 1 (wrong killer 0, trapped 0, compile-only
  0, MISSED 0, skipped 0)`, `MUTATE OK caught=1/1`. Floor 90 -> 91; `--prove-floor` -> `FLOOR PROOF OK: 7 of 7 arms
  refused and the control did not`.
  B2: `node services/api/test/mutate/attestMutants.mjs --only=reject-plan-after-reservation` -> `population
  mutations=93 (floor 93)`, `CAUGHT reject-plan-after-reservation by "/plan, Bearer expired, IDENTITY_HEADERS unset,
  header live: the answer is the ruled reference"`, `RESULT caught=1 missed=0 trap=0 of 1`; `--prove-floor` -> every
  arm REFUSED (population 92 is below the floor 93, ...), real population quiet.
  A1 `npx vitest run test/sessionCarriesAct.test.ts test/sessionIdentity.test.ts test/requestReadSites.test.ts` ->
  `Test Files 3 passed (3)`, `Tests 225 passed (225)`.
  A2 `swift test --filter "PlanSessionRetryTests|SessionStoreTests|SessionAccountTests|PlanBearerTests"` -> `Test run
  with 17 tests in 4 suites passed`; PlanSessionRetryTests alone: `a 401 hands the session back, ... never a third
  request" with 108 test cases passed`, `the resend carries the same purchase ... with 4 test cases passed`, `no row
  ignores its variant: held, Worker and renewal each change some row's requests, and every action is bounded passed`.
  A3 the changed table's red by name is mutant 91 above (MISSED before the table changed, CAUGHT by
  rejectedSessionRecovers after); the earlier RED-first entries (2026-10-09T11:12:00Z) stand.
  A4 Worker population 93 (reject-never, reject-under-flag, reject-plan-after-reservation, reject-absent-header,
  reject-unmarked, reject-{plan,trip,loop}-unanswered); Swift population 91 (82-91). `python
  ops/lib/check-mutate-population.py` -> `P-PROC-06: every added module is covered or allowlisted; the floor of 147
  holds`, exit 0.
  A5 `python ops/lib/run-named-tests.py P-STORE-02` -> `NAMED P-STORE-02 passed=246/246` (no new test function, so the
  named table and its count are unchanged); `P-COST-04` -> `NAMED P-COST-04 passed=27/27`; `python
  ops/lib/check-pins-yaml.py` -> `PINS-YAML ok pins=49 fields=395`; `bash ops/queue-check` -> `QUEUE OK (332 tasks)`;
  `git diff --name-only origin/main...HEAD -- apps/ios` -> 0 files.
  Not closed here (rv1 RECORDABLE 2): the `record.token == token` guard in planSessionRejected has no EQUIVALENT entry.
- 2026-10-09T13:41:43Z REVIEW PASS round 2 (agent/rv2-t0333, not the owner) on clean head 275f7968 == origin/task/T-0333.
  Touched rows only. B1: rv1's mutant (PlanFamilySend.swift `request(renewed)` -> `request(renewed ?? bearer)`)
  re-applied -> `swift test --filter "PlanSessionRetryTests|SessionStoreTests|SessionAccountTests|PlanBearerTests"`
  RED by name, "a 401 hands the session back, re-acquires once and resends the same bytes once; never a third
  request" with 108 test cases failed with 32 issues (rows {plan,reroute,...} x {keychain,acquired} x
  {rejectsOnce,rejectsAlways} x {assertRejected,budgetSpent}). Reviewer's own mutant in the same class (a failed
  renewal sends nothing: `guard renewed != nil else { return first }` before the resend) -> RED by the same test,
  32 issues on the failed-renewal rows. Unmutated control: 17 tests in 4 suites passed. Source restored, tree clean.
  B2: `node test/mutate/attestMutants.mjs --only=reject-plan-after-reservation` -> `population mutations=93 (floor
  93)`, `CAUGHT reject-plan-after-reservation by "/plan, Bearer expired, IDENTITY_HEADERS unset, header live: the
  answer is the ruled reference"`, `RESULT caught=1 missed=0 trap=0 of 1`.
  Gates: `gh pr checks 225` core pass (6m39s), pins-source-only pass (2m50s); `python ops/lib/run-named-tests.py
  P-STORE-02` -> `NAMED P-STORE-02 passed=246/246` exit 0; `python ops/lib/check-mutate-population.py` -> floor 147
  holds, exit 0; `bash ops/queue-check` -> `QUEUE OK (332 tasks)`. The 13:16:08Z entry re-quotes the acceptance
  block on f73ecf64; f73ecf64..275f7968 changes only this file. `git merge-base --is-ancestor origin/main
  origin/task/T-0333` (origin/main e3567a6e) -> exit 0, no drift.
  Recordable, not blocking: rv1 RECORDABLE 2 (no EQUIVALENT entry with a witness for the `record.token == token`
  guard) and RECORDABLE 4 (the user-visible error after a second 401 is unpinned) stay open as follow-ups.
