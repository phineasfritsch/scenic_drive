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
