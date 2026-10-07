---
id: T-0292
title: Handlers get a frozen env and the kill-switch tables run on a shared-env worker after an authenticated sweep - request-time shared-state patches cannot unpause anything
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T08:07:28Z
lease_expires_at: 2026-10-07T20:07:28Z
worktree: .worktrees/T-0292
branch: task/T-0292
exclusive: []
touches: [services/api/src/index.ts, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01]
reviewer: null
depends_on: [T-0288]
verify: [ops/check-pins]
acceptance:
  - "default.fetch hands every handler a frozen env (Object.freeze of a per-request copy, or the binding object frozen once); a test through worker.fetch shows a handler's attempt to delete or assign env.KILL throws or has no effect on the next request, by name"
  - "the P-COST-01 kill table and the /config table run on ONE worker sharing ONE env object after a sweep that includes authenticated requests with bound fakes (D1, KV, Analytics Engine, the router), under every KILL source - full equality"
  - "population entries: a handler that deletes env.KILL on its first call, and one gated on an authenticated path - MISSED before, CAUGHT by name after"
---
## Brief

rv5-t0288 recordable (PR #177 sign-off): the sweep builds a new env per call, but workerd hands one env object to every
request in an isolate, so a handler that mutates env is never exercised; and the sweep's well-formed requests are not
authenticated, so a patch gated on an authenticated or bound-env path never fires (owner residual R10). Memory
runtime-read-recorder.

## Log
- 2026-10-07T02:08:18Z filed by agent/claude-opus-5 (orchestrator) from rv5-t0288's recordable on PR #177.
- 2026-10-07T08:07:28Z claimed by agent/claude-opus-5; lease until 2026-10-07T20:07:28Z
- 2026-10-07T08:16:50Z agent/claude-opus-5 (owner): RULINGS, before code (plan, Brief, code and reality):
  (R1) FREEZE: default.fetch hands every handler `Object.freeze({ ...env })` - a per-request frozen COPY, not the
  binding object frozen once. The binding object belongs to the platform (and in the tests to the harness, which swaps
  a CONFIG binding between rows); a copy leaves it untouched. src is ES modules (strict), so a handler's `delete
  env.KILL` or `env.KILL = "0"` throws TypeError; nothing it does to its copy reaches the next request, whose copy is
  made from the untouched binding object. SHALLOW: the binding objects themselves (KILL_SWITCH, CONFIG, CLOSURES, DB,
  QUOTA, TELEMETRY) are shared and not frozen - a handler assigning `env.KILL_SWITCH.get` is NOT closed here (freezing
  workerd's binding wrappers is a production change no test here can run). Recorded as residual R-A for a follow-up.
  (R2) SHARED-ENV WORKER: the new test file test/sharedEnvWorker.test.ts builds ONE env object per KILL source (the 5
  of configHarness.KILLS), once, with bound fakes - D1 (cloudflare:test env.DB), KV (CLOSURES empty, CONFIG, the
  source's KILL_SWITCH), Analytics Engine (a per-source writeDataPoint recorder), the router (a per-source ROUTER_URL
  host on the stubbed global fetch), QUOTA (a per-source fakeQuotaNamespace), SESSION_JWT_SECRET and RO_TOKEN - and
  every request of the sweep and of both tables goes through worker.fetch with that same object. workerd hands one env
  per isolate; one object per source models five deployments, each with its own isolate.
  (R3) AUTHENTICATED SWEEP: the representatives move from configSweep.test.ts to a harness (test/sweepRequests.ts) so
  both sweeps share ONE table keyed by ROUTES (fail closed). Kinds are valid, invalid and authenticated: authenticated
  carries `authorization: Bearer <session JWT signed with the shared secret>` (planning routes, /telemetry, /entitlement,
  /auth/apple, /account, /attest/*) or `Bearer <RO_TOKEN>` (/__ro); /__health, /__version, /config take no credential
  and repeat their valid request. Two seeded passes as in T-0288 R10. The sweep FAILS on any rejected worker.fetch (a
  handler that writes to its frozen env throws - that is how a write becomes red by name), and records every outcome.
  (R4) P-COST-01 TABLE on the shared envs after the sweep: every upstream route and /telemetry, authenticated, under
  every KILL source. A killed source's row is the WHOLE paused response (status + body, full equality); an unkilled
  source's row is the literal "served" - its answer depends on the router fake and quota state the sweep consumed, and
  what this pin holds is the kill decision. Rows are functions of the source (meta-test: the killed and unkilled
  expectations differ). Plus, per killed source over the WHOLE run (sweep + table): zero requests to its router host,
  zero Analytics Engine writes, quota state {} - full equality.
  (R5) /config TABLE on the same envs after the sweep: ROWS x KILLS; the harness assigns the row's CONFIG binding onto
  the shared object between rows (a binding change, as a deploy makes) and restores it; expectation from configHarness
  (the pre-load STRINGIFY oracle), full equality; plus the intrinsics snapshot vs BASELINE, and each shared env's own
  properties after the run equal to before (KILL still "1").
  (R6) FREEZE TEST by name through worker.fetch: a hostile handler is installed under a test-only ROUTES key for the
  test's duration (ROUTES is the shipped dispatch table; installing into it exercises the shipped default.fetch),
  tries delete / assign / defineProperty of env.KILL on the KILL=1 env, records each as threw-TypeError, then POST
  /plan on the same env object is 503 planning_paused. RED before R1.
  (R7) POPULATION (configMutants.mjs, floor 77 -> 79, TESTS += sharedEnvWorker.test.ts): attest.ts attestDepsFromEnv
  deletes env.KILL on its first call (an operational route, never killed, so the delete runs under KILL=1 and unpauses
  every later request of a shared env); telemetry.ts, after identifyCaller, only when the caller is AUTHENTICATED
  (SESSION_JWT_SECRET bound and a verified session), replaces JSON.stringify once to write planning_paused false.
  Each is shown MISSED under the pre-change tests, then CAUGHT by name.
  (R8) touches += ops/lib/named-tests.json, pins/PINS.yaml: pins_affected is P-COST-01, and an unbound test can be
  deleted silently; the freeze test and the shared-env kill table are bound into P-COST-01 by name.
  (R9) T-0293 (PR #182, open) adds /waitlist to ROUTES and edits configSweep/killSwitchRoutes: on the final merge the
  shared REQUESTS table gains /waitlist's representatives (it fails closed on ROUTES' keys), and the operational list
  in the new kill table follows killSwitchRoutes'.
- 2026-10-07T09:00:27Z agent/claude-opus-5 (owner): RED, CODE, GREEN, POPULATION.
  RED FIRST (tests only, index.ts unchanged): `npx vitest run test/sharedEnvWorker.test.ts test/configSweep.test.ts`
  `Tests 1 failed | 9 passed (10)`, exit 1 - FAILED by name `handlers get a frozen env (T-0292 R1, P-COST-01) > a handler
  that deletes, assigns or redefines env.KILL through worker.fetch throws TypeError, and the next POST /plan on the same
  env object is 503 planning_paused` (received `delete: no throw`, ...). The sweep, both tables and the snapshot were
  green on the unmutated tree (the sweep found no throwing request with bound fakes).
  MISSED BEFORE (configMutants.mjs, pre-change TESTS list of 9 files, pre-change index.ts): `--only=attest-first-call-
  deletes-kill`: `baseline green tests=41`, `MISSED attest-first-call-deletes-kill`; `--only=session-authenticated-
  stringify-unpause`: `baseline green tests=41`, `MISSED session-authenticated-stringify-unpause`. (A first spelling gated
  in telemetry.ts on `userId` was CAUGHT by requestReadSites - userId is a request-derived name - so the authenticated
  entry gates inside identifyCaller after verifySession, on `claims`, which no request read derives.)
  CODE: index.ts default.fetch `return handler(req, Object.freeze({ ...env }), url);` plus one header line; the
  configAnswerPath content pin re-approves index.ts (a19976c5...) and requestReadSites re-approves the one changed site.
  RULING R2 AMENDED: the first --only run after the code had the attest entry MISSED - all five sources ran on ONE module
  instance, so the mutant's single first call landed on a source without KILL, where deleting an absent property of a
  frozen object is a silent no-op. workerd gives each deployment its own isolate, so each KILL source now gets its own
  module instance (vi.resetModules + dynamic import of src/index, asserted 5 distinct and none the static one).
  CAUGHT AFTER: `population mutations=81 (floor 81) equivalent=1 subjects=2 tests=10 ONLY=2`, `baseline green tests=47`,
  `CAUGHT attest-first-call-deletes-kill by "the authenticated sweep sends every ROUTES path a valid, an invalid and an
  authenticated request on one env per KILL source, and no request throws"`, `CAUGHT session-authenticated-stringify-
  unpause by "after the sweep, every CONFIG row x every KILL source answers the whole expected /config response on the
  shared env"`, `RESULT caught=2 missed=0 trap=0 of 2`. Index entries (before the isolate change, src unchanged since):
  `CAUGHT fetch-env-shared` and `CAUGHT fetch-env-copy-unfrozen`, both by "the /config answer path is exactly the
  approved bytes". Floor 77 -> 81; TESTS += test/sharedEnvWorker.test.ts.
  RESIDUAL R-A (R1, not closed): the freeze is shallow; a write to a shared binding object (env.KILL_SWITCH.get = ...)
  reaches later requests. Proposed follow-up, not filed by this task.
- 2026-10-07T09:19:39Z agent/claude-opus-5 (owner): FINAL GATES on 63b79328 (origin/main 92e3fc8b fetched and merged:
  already up to date; PR #182 still OPEN, so no /waitlist in ROUTES yet - R9 stands for whoever merges second).
  `cd services/api && npx vitest run`: `Test Files 66 passed (66)`, `Tests 2087 passed (2087)`, exit 0.
  `python ops/lib/run-named-tests.py P-COST-01`: `NAMED P-COST-01 passed=29/29`, exit 0. `bash ops/queue-check`:
  `QUEUE OK (287 tasks)`. `ops/check-pins --source-only` did not finish inside 300 s on the contended box (killed, no
  verdict); CI's pins-source-only is the record. wc -l: src/index.ts 125, test/sharedEnvWorker.test.ts 213,
  test/sweepRequests.ts 94, test/configSweep.test.ts 78, test/mutate/configMutants.mjs 278.
  ACCEPTANCE RE-QUOTED: (1) frozen env - default.fetch `Object.freeze({ ...env })`; `handlers get a frozen env (T-0292
  R1, P-COST-01) > a handler that deletes, assigns or redefines env.KILL through worker.fetch throws TypeError, and the
  next POST /plan on the same env object is 503 planning_paused` red before, green after. (2) one env object per KILL
  source (5), bound fakes D1/KV/AE/router/QUOTA, authenticated sweep, then the P-COST-01 kill table and the /config table
  on those same objects, full equality - 6/6 green, bound into P-COST-01. (3) population: attest-first-call-deletes-kill
  and session-authenticated-stringify-unpause MISSED before, CAUGHT by name after (quoted above); floor 81.
- 2026-10-07T10:33:47Z agent/claude-opus-5 (owner): rv1-t0292 B1 (FAIL on 83b7993f: branch behind main; T-0293 merged
  /waitlist). RULINGS before the code: (a) /waitlist is OPERATIONAL in sharedEnvWorker.test.ts - it reads D1 only,
  calls no router and is outside the kill switch and the quota by T-0293 R8 (src/waitlist.ts; killSwitchRoutes.test.ts
  on main already lists it operational), so KILLABLE stays exactly /plan, /loop, /isochrone, /trip, /telemetry and the
  `killable == KILLABLE` equality holds on the merged ROUTES. (b) configSweep.test.ts keeps this PR's shape (REQUESTS
  live in sweepRequests.ts); main's inline /waitlist pair moves there as valid `{cell: "85283473fffffff"}`, invalid
  its upper-case spelling, and authenticated the valid body with the session bearer (the route ignores credentials,
  but it is not on NO_CREDENTIAL, whose equality test compares only the three routes whose authenticated request IS
  their valid one). (c) the rig's D1 is testEnv.DB, which held no tables: beforeAll now runs siwaHarness
  freshAllTables, so the waitlist table (migrations/0006) is there and the sweep's /waitlist valid and authenticated
  requests write a count instead of answering 503 waitlist_unavailable. (d) index.ts's approved hash in
  configAnswerPath.test.ts is re-approved on the merged bytes: d61c2a29...25cb (sha256 of the merged src/index.ts,
  127 lines). (e) P-COST-01's count: T-0293's sentence says 31, but main's ops/lib/named-tests.json binds 33 (its
  regionGateOrder.test.ts two, added in T-0293 rv1 B1, were not counted in the prose); the merged row binds 36 = 33 +
  this task's three, recorded as a merge sentence in PINS.yaml (this task's 29/29 sentence is a dated record and
  stays). MERGE: origin/main afa0dd15 merged at 4be2a06d; conflicts were pins/PINS.yaml (P-COST-01),
  configAnswerPath.test.ts (index.ts hash) and configSweep.test.ts (REQUESTS), all three resolved as above.
  ACCEPTANCE RE-RUN ON THE MERGED HEAD 4be2a06d: `cd services/api && npx vitest run`: `Test Files 70 passed (70)`,
  `Tests 2103 passed (2103)`, exit 0. `python ops/lib/run-named-tests.py P-COST-01`: `NAMED P-COST-01 passed=36/36`,
  exit 0. Touched mutants, `node test/mutate/configMutants.mjs --only=fetch-env-shared,fetch-env-copy-unfrozen,
  attest-first-call-deletes-kill,session-authenticated-stringify-unpause`: `population mutations=81 (floor 81)
  equivalent=1 subjects=2 tests=10 ONLY=4`, `baseline green tests=47`, `CAUGHT attest-first-call-deletes-kill by "the
  authenticated sweep sends every ROUTES path a valid, an invalid and an authenticated request on one env per KILL
  source, and no request throws"`, `CAUGHT session-authenticated-stringify-unpause by "after the sweep, every CONFIG row
  x every KILL source answers the whole expected /config response on the shared env"`, `CAUGHT fetch-env-shared` and
  `CAUGHT fetch-env-copy-unfrozen` both by "the /config answer path is exactly the approved bytes", `RESULT caught=4
  missed=0 trap=0 of 4`. (1) frozen env, (2) one env per KILL source with the authenticated sweep and both tables by
  full equality, now over 17 ROUTES keys, and (3) both population entries CAUGHT by name - all three hold on the merged
  head. wc -l: src/index.ts 127, test/sharedEnvWorker.test.ts 215, test/sweepRequests.ts 99, test/configSweep.test.ts
  78, test/configAnswerPath.test.ts 62.
