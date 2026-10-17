---
id: T-0390
title: Bind the production KV namespaces (PLANS, CONFIG, KILL_SWITCH, CLOSURES) in services/api/wrangler.jsonc - the owner created them 2026-10-17
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T07:52:44Z
lease_expires_at: 2026-10-18T07:52:44Z
worktree: .worktrees/T-0390
branch: task/T-0390
exclusive: []
touches: [services/api/wrangler.jsonc, services/api/test/, services/api/src/index.ts, pins/PINS.yaml]
pins_affected: [P-SAFE-08, P-COST-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The owner authorised the pilot backend on 2026-10-17. The orchestrator then created these Cloudflare KV namespaces
on the owner's account. The ids are not secrets.
- scenic-plans       33e411b3b03246a19cda166c0c05cfd6  -> binding PLANS
- scenic-config      8dd224a7fb554dc4a270f67162d28bb6  -> binding CONFIG
- scenic-kill-switch 8946404cc991458196d195c65ea15d7b  -> binding KILL_SWITCH
- scenic-closures    5e3eb553f16c4e4ba4d5297e001ef5ea  -> binding CLOSURES
It also created the R2 bucket scenic-data. That bucket is for tiles and corpus published by ops/publish-*, and the Worker does not bind it.
D1 'scenic' has every migration through 0010 applied remotely. The secrets SESSION_JWT_SECRET, ROUTER_SECRET,
SEARCH_SECRET and RO_TOKEN are set. ROUTER_URL stays the placeholder until the VPS router exists (separate step).

Bind the four namespaces in wrangler.jsonc using exactly these ids and binding names: the binding names the shipped
src/index.ts Env reads.
- Update closuresCron.test.ts. It currently asserts that CLOSURES is NOT bound. It should now assert that the CLOSURES
  binding exists with this id and that the cron is still every 15 minutes.
- Update every comment and pin sentence that says "not bound in wrangler.jsonc". In PINS.yaml, append a dated
  sentence. Never edit dated text.
- Add one test that reads wrangler.jsonc and checks the binding set against the Env bindings the shipped Worker
  reads. Compare whole: a binding added or dropped on either side must fail.

No deploy in this task. The deploy is T-0391, holding exclusive [prod].

## Log
- 2026-10-17 filed by agent/claude-opus-5 after the owner authorised backend setup.
- 2026-10-17T07:52:44Z claimed by agent/claude-opus-5; lease until 2026-10-18T07:52:44Z
- 2026-10-17T08:07:55Z MEASURED on the branch head 258650b7 (== main e41a7170's services/api and pins).
  - `export interface Env` in services/api/src/index.ts (lines 30-52) declares 21 fields. Non-string (binding)
    fields, 7: DB `D1Database`, KILL_SWITCH `KillSwitchRead`, QUOTA `DurableObjectNamespace<QuotaCounter>`,
    CLOSURES `KVNamespace`, CONFIG `KVNamespace`, TELEMETRY `AnalyticsEngineDataset`, PLANS `KVNamespace`.
    String fields, 14 (vars + secrets): GIT_SHA BUILT_AT RO_TOKEN KILL ROUTER_URL ROUTER_SECRET ASN_ALLOW_SANDBOX
    SESSION_JWT_SECRET IDENTITY_HEADERS APP_ATTEST_ALLOW_DEVELOP APPLE_CLIENT_SECRET GRAPH_VERSION SEARCH_URL
    SEARCH_SECRET.
  - services/api/wrangler.jsonc binds 3: d1_databases DB, durable_objects QUOTA, analytics_engine_datasets
    TELEMETRY; no `kv_namespaces` key; vars GIT_SHA BUILT_AT ROUTER_URL IDENTITY_HEADERS (all Env string fields).
    Missing against Env: exactly KILL_SWITCH, CLOSURES, CONFIG, PLANS - the Brief's four.
  - "not bound" sites: index.ts Env comments on KILL_SWITCH (l.36), CLOSURES (l.41), CONFIG (l.45), PLANS (l.48);
    wrangler.jsonc comments (the closures cron "which the owner creates and binds"; "The KILL_SWITCH KV namespace is
    NOT bound here"); closuresCron.test.ts header (l.4) and its test `wrangler.jsonc runs the cron every 15 minutes
    and binds no CLOSURES namespace` (l.140-142, asserts kv_namespaces undefined; NOT in ops/lib/named-tests.json).
    PINS.yaml: P-PRIV-04 ("PLANS is not bound in wrangler.jsonc (owner)"), P-SAFE-08 ("The owner has not created or
    bound the CLOSURES KV namespace (wrangler.jsonc binds none, held by test)"), P-NAV-01 ("production binds no
    PLANS (wrangler.jsonc)"). src/isochrone.ts l.36 "not bound" is about the router, not wrangler.
  - services/api/test/configAnswerPath.test.ts content-pins `../src/index.ts` at sha256 10d032ee...087ae, and
    `sed 's/\r$//' src/index.ts | sha256sum` = 10d032ee7b1dab7a01082dcf90ded19fcb91af098f13d601b3a61cc1c2e087ae.
- 2026-10-17T08:07:55Z RULINGS.
  - R1 (Brief vs code): the Brief's four binding names equal the four Env binding fields wrangler lacks (measured).
    Bound with exactly the Brief's ids; no preview_id (local dev/vitest never read wrangler's KV ids).
  - R2 (KILL_SWITCH type): Env types it `KillSwitchRead`, not `KVNamespace` (the frozen reader, T-0297). The new
    test's type table maps `KillSwitchRead` to kv_namespaces; any type not in that table is an unknown kind that
    matches no wrangler section, so it fails (fail closed).
  - R3 (anchor): the new test parses the Env DECLARATIONS (identifier + type), never their comments: each line
    between `export interface Env {` and its `}` is blank, a `//` line, or must match `NAME?: TYPE;` (trailing `//`
    comment dropped) - any other line fails the test (source-guards-fail-closed). Env is type-only, so the source
    is the only shipped artifact that carries it. wrangler.jsonc is parsed as today's test does (drop //-leading
    lines, JSON.parse - an inline comment makes it throw, fail closed).
  - R4 (whole compare): {binding name -> wrangler section} from wrangler.jsonc (d1_databases, kv_namespaces,
    durable_objects.bindings, analytics_engine_datasets, r2_buckets, services, queues.producers, any other array of
    {binding|name}) toEqual {Env non-string field -> section by type}. Also the kv_namespaces array toEqual the four
    {binding,id} pairs, and every wrangler var is an Env string field. A binding added/dropped on either side fails.
  - R5 (index.ts comments): editing the four Env comments changes index.ts bytes, so configAnswerPath.test.ts's
    ANSWER_PATH row for index.ts is re-approved in the same diff (comment-only change; reviewer sees both).
  - R6 (PINS.yaml): dated text is never edited; a `T-0390 (2026-10-17): ...` sentence is appended to P-PRIV-04,
    P-SAFE-08, P-NAV-01 (each states a now-false "not bound") and P-COST-01 (pins_affected: KILL_SWITCH is now
    bound, so the KV key KILL is a live production pause). isochrone.ts l.36 is out of scope (router, not KV).
  - R7: the closuresCron test is renamed to `wrangler.jsonc runs the cron every 15 minutes and binds CLOSURES to
    the scenic-closures namespace` (the old name states a falsehood; it is not bound by name anywhere).
- ACCEPTANCE (written before code):
  - A1 `cd services/api && npx vitest run test/wranglerBindings.test.ts test/closuresCron.test.ts
    test/configAnswerPath.test.ts` - all pass.
  - A2 RED first by name on the unbound wrangler.jsonc: the new wranglerBindings tests and the renamed closuresCron
    test FAIL by name; then green. Plus scratch mutants (restored): Env gains `R2X?: R2Bucket;` -> FAIL; wrangler
    drops CONFIG -> FAIL; Env drops PLANS -> FAIL; an Env line `PLANS?: KVNamespace` without `;` -> FAIL.
  - A3 `git grep -n "not bound in wrangler\|NOT bound here\|binds no CLOSURES" -- services/api/src
    services/api/wrangler.jsonc services/api/test` - empty.
  - A4 `cd services/api && npx vitest run` - the whole Worker suite passes.
  - A5 `python ops/lib/run-named-tests.py P-SAFE-08` and `... P-COST-01` - pass.
  - A6 bare gates: check-pins-yaml.py, queue-check, check-exec-bits, check-safety-disclaimer,
    check-mutate-population.py, check-mutate-only.py - each exit 0; on the merged head after `git merge origin/main`.
- 2026-10-17T08:13:42Z RED first by name (tests written, wrangler.jsonc still unbound): `npx vitest run
  test/wranglerBindings.test.ts test/closuresCron.test.ts` -> `Tests 3 failed | 27 passed (30)`, FAILED by name:
  `the binding set of wrangler.jsonc equals the Env's non-string fields, each in its type's section` (expected
  { QUOTA: 'durable_objects', ...(2) } to deeply equal { DB: 'd1_databases', ...(6) }), `the four KV namespaces are
  bound by the shipped names to the owner's ids` (expected undefined), `wrangler.jsonc runs the cron every 15 minutes
  and binds CLOSURES to the scenic-closures namespace`.
- 2026-10-17T08:15:42Z GREEN: wrangler.jsonc binds the four; index.ts's four Env comments now say `bound in
  wrangler.jsonc (T-0390)`; index.ts sha256 (CRLF-normalized) cad5390fc02d5f035f2802ed9318c590f176375ef1ff66838b66b1c82a67a5aa
  re-approved in configAnswerPath.test.ts (R5). The three-file run once showed configAnswerPath's intrinsics test at
  5015 ms (the 5 s timeout, cold pool); alone it passed 3/3 on the branch and on the base - a timing flake, not this diff.
- 2026-10-17T08:18:43Z scratch mutants (scratchpad mutants.py, each restored): env-gains-r2-binding,
  env-gains-kv-binding, env-drops-plans, env-plans-no-semicolon, env-kv-retyped-r2, wrangler-drops-config,
  wrangler-adds-r2 each CAUGHT by `the binding set of wrangler.jsonc equals ...` (no-semicolon also by `every wrangler
  var is a string field of Env`; drops-config also by `the four KV namespaces ...`). wrangler-closures-moved-to-r2
  first used bucket_name "x", which the vitest pool's wrangler validation refused before any test ran (red, not by
  name); with "scenic-data" it is CAUGHT by all three binding tests. 8/8.
- 2026-10-17T08:24:34Z RULING R8 (found by A4): the full suite then read `Tests 29 failed | 2661 passed (2690)`, all
  29 in sessionIdentity.test.ts: @cloudflare/vitest-pool-workers builds the test `env` from wrangler.jsonc, so the
  pool's env now carries a local PLANS and each /plan answer mints a fresh plan_token, which that suite's
  full-equality oracle compares between two calls. The suite is about identity, not plans: its env2 now sets
  `PLANS: undefined`, the env it was written against. Then 40/40. No other suite changed (CONFIG, KILL_SWITCH,
  CLOSURES bound locally are empty, and every test that needs one injects its own).
- 2026-10-17T08:42:25Z named pins on 0c53e560: `NAMED P-SAFE-08 passed=836/836`, `NAMED P-COST-01 passed=55/55`,
  `NAMED P-PRIV-04 passed=83/83`, `NAMED P-NAV-01 passed=44/44`.
- 2026-10-17T09:06:24Z ACCEPTANCE re-run on the merged head e724ea79 (origin/main merged; it brought only 4 queue
  files, no code): A1 `Test Files 3 passed (3)`, `Tests 33 passed (33)`. A2 above. A3 git grep exit 1 (empty).
  A4 `Test Files 100 passed (100)`, `Tests 2690 passed (2690)`. A5 above (unchanged code since). A6: PINS-YAML ok
  pins=52 fields=418; QUEUE OK (385 tasks); P-OPS-01 244 files, all modes correct; check-safety-disclaimer exit 0;
  P-PROC-06 floor of 171 holds (check-mutate-population exit 0); queue-check and check-mutate-only re-run bare at
  the push.
