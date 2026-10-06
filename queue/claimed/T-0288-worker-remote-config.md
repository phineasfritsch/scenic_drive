---
id: T-0288
title: the Worker serves GET /config - typed remote config (feature flags, quota display numbers, min app build, kill-switch mirror, supported regions) from KV with compiled-in defaults; any bad or missing KV value falls back to defaults, never to an unsafe value
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T20:26:08Z
lease_expires_at: 2026-10-07T06:26:08Z
worktree: .worktrees/T-0288
branch: task/T-0288
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01]
reviewer: null
depends_on: [T-0256]
verify: [ops/test, ops/check-pins]
acceptance:
  - "GET /config answers a closed JSON object (whitelisted keys only; RULE the key set from the plan: min_app_build, planning_paused mirror of KILL, supported_regions [la], feature flags for loop/trip/surprise, quota numbers read FROM quota.ts never retyped) built from compiled defaults overlaid by a KV 'config/v1' record; every field validated by a whitelist table at every bound; any invalid field drops to its default individually and the answer says which (config_warnings); KV unbound/throws -> pure defaults; the safety-relevant fields (planning_paused) can only be made MORE restrictive by KV, never less (a KV 'false' cannot unpause an env KILL=1)"
  - "cacheable (ruled max-age), no request read beyond the route (requestReadSites APPROVED extended by equality), KILL never blocks /config itself; tests through ROUTES by full equality with the cross-product discipline (KV absent / defaults / every field invalid / every field at its bounds); a TS mutation population with a literal floor"
---
## Brief

Plan Worker list: '/config' and lifecycle 'remote config'. The app needs one place to learn min build, which features
are on, the supported region and whether planning is paused (PlanError.planningPaused). No deploy; KV binding declared
only.

## Log
- 2026-10-06T20:22:31Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 remote config).
- 2026-10-06T20:26:08Z claimed by agent/claude-opus-5; lease until 2026-10-07T06:26:08Z
- 2026-10-06T20:33:14Z RULINGS (agent/claude-opus-5, before any code). R1 KEY SET, closed, in this order: `min_app_build`
  (integer), `planning_paused` (boolean), `supported_regions` (string[]), `feature_loop`, `feature_trip`,
  `feature_surprise` (booleans), `quota` ({anon,free,paid} x {plan,loop,surprise,trip}), `config_warnings` (string[]).
  Flat, not nested: one whitelist table, one key per row. Compiled defaults: 1, false, ["la"], true, true, true.
  `quota` is built by iterating the tiers of DAILY_PLAN_QUOTA and calling quota.ts's dailyQuota(kind, tier) - never a
  literal; telemetry is excluded (not a user feature). quota is NOT overridable by KV (a `quota` key in KV is unknown).
  R2 KV: optional binding `CONFIG` (Env), key `config/v1`, a JSON object. Declared in Env only, not bound in
  wrangler.jsonc (the owner creates the namespace, as for KILL_SWITCH). R3 PER-FIELD WHITELIST, every bound:
  min_app_build Number.isInteger and 1 <= n <= 2147483647 (Int32 max; 1e400 parses to Infinity and is refused);
  planning_paused and the three features `typeof === "boolean"` exactly (no "1", 1, "true", null); supported_regions a
  non-empty array of DISTINCT members of the compiled SUPPORTED_REGIONS ["la"] (KV can only narrow; the app must never
  be offered a region with no graph). An invalid field drops to its default ALONE and its name is appended to
  config_warnings in key order; any KV key outside the six is ignored and adds ONE `unknown_keys` (a closed vocabulary -
  KV text is never echoed). KV unbound or key absent -> pure defaults, warnings []; KV throws, value not JSON, or JSON
  not a plain object (null, array, string, number) -> pure defaults, warnings ["record"]. R4 MORE RESTRICTIVE ONLY:
  planning_paused = killSwitch(env) OR (KV planning_paused === true). killSwitch is the T-0256 R5 function (env KILL=1,
  KV KILL_SWITCH KILL=1, or a throwing KILL_SWITCH all pause), so a KV `false` cannot unpause an env KILL=1. A
  throwing CONFIG does not pause: the planning routes never read CONFIG, and the KILL mirror is unaffected by it.
  KV planning_paused:true is an app-side pause the Worker's routes do not enforce (they are guarded by KILL alone).
  min_app_build's floor is its default 1 and the features default on, so KV can only raise/turn off those too.
  R5 KILL NEVER BLOCKS /config: handleConfig(env) answers 200 under every KILL source; /config joins
  killSwitchRoutes.test.ts's OPERATIONAL_ROUTES (it makes no upstream call). The 26 P-COST-01 names are unchanged;
  pins/ and ops/lib/named-tests.json are outside touches: [services/api/], so no new name is bound - recorded, not
  silently skipped. R6 CACHE: `cache-control: public, max-age=300` (ruled 300 s: the planning routes read KILL per
  request, so a stale /config only delays the app's banner by <= 5 min; a transient `record` warning is cached as long).
  R7 NO REQUEST READ: handleConfig takes env only; the ROUTES line is `(_req, env) => handleConfig(env)`, which the
  requestReadSites SITE regex does not match (`_req` is one word), so APPROVED is unchanged and equality still holds;
  an explicit it() asserts src/config.ts has no site. Any method answers the same body (reading the method would be a
  request read). R8 TESTS through ROUTES['/config'], whole response (status, content-type, cache-control, body TEXT)
  by equality to an expectation built from test literals and quota.ts's exported tables; cross product of CONFIG rows
  x KILL sources with the meta-test that no row's expectation ignores the KILL variant (named exception: rows whose
  KV sets planning_paused true); per-field accept/refuse table at every bound over {no KILL, env KILL}; a whole-line
  WHITELIST of every src/config.ts line carrying a digit (so a retyped quota number is refused). R9 POPULATION:
  services/api/test/mutate/configMutants.mjs (the telemetryMutants.mjs shape) over src/config.ts and src/index.ts with
  a literal MIN_MUTATIONS; check-mutate-population.py reads Sources/ and services/etl/etl/ only, so the .mjs is it.
- 2026-10-06T20:37:57Z RED FIRST, by name, before src/config.ts exists: `npx vitest run test/configRoutes.test.ts test/configFields.test.ts
  test/requestReadSites.test.ts test/killSwitchRoutes.test.ts` -> `Test Files  3 failed | 1 passed (4)`,
  `Tests  8 failed | 8 passed (16)`; FAILED by name: configRoutes `ROUTES has a /config entry`, `every CONFIG row x
  every KILL source answers 200 with the whole expected response (KILL never blocks /config)`, `a KV planning_paused
  false cannot unpause an env KILL=1 or a KV KILL_SWITCH KILL=1`, `any method answers the same body: the handler reads
  no request`; configFields `every accepted value at its bound is answered, with no warning, under each KILL
  variant`, `every refused value drops that field alone to its default and names it, under each KILL variant`,
  `every line of src/config.ts carrying a digit is an approved whole line`; requestReadSites `src/config.ts reads no
  request: GET /config answers from env alone (T-0288 R7)`. Green while red: the two pure meta-tests (tables cover
  every field; no row ignores the KILL variant bar KV_PAUSES) and killSwitchRoutes (/config added to OPERATIONAL_ROUTES).
- 2026-10-06T21:15:29Z GREEN + POPULATION + FINAL GATES (agent/claude-opus-5). Code: src/config.ts (handleConfig(env), configAnswer,
  FIELDS whitelist, DEFAULTS, readRecord, overlay, quotaDisplay via dailyQuota); index.ts `CONFIG?: KVNamespace` in Env
  and ROUTES `"/config": (_req, env) => handleConfig(env)`; routes.test.ts gains /config in the enumeration and a
  SELF.fetch GET /config by whole-response equality. After the red run the digit whitelist was corrected to the module
  as written (the supported_regions line whole, plus `status: 200,` and the headers line - charset=utf-8 carries a
  digit). POPULATION, once, at 017e282: `node services/api/test/mutate/configMutants.mjs` -> `population mutations=59
  (floor 59) equivalent=1 subjects=2 tests=5`, `baseline green tests=24`, `RESULT caught=59 missed=0 trap=0 of 59`,
  exit 0. Notable catchers: quota-retyped by `every line of src/config.ts carrying a digit is an approved whole line`;
  route-reads-request by requestReadSites `the request sites under src are exactly the approved sites, file by file,
  line by line`; route-method-gated by `any method answers the same body: the handler reads no request`;
  paused-kv-false-unpauses, paused-kill-ignored, kill-blocks-config, route-kill-blind, route-kill-switch-blind all red.
  `--prove-floor`: four arms REFUSED, real population quiet, exit 0. `--prove-vacuity --only=quota-retyped,route-reads-request`
  -> `caught=0 missed=2`. EQUIVALENT field-own-to-in carries its witness. MERGED origin/main (git fetch origin; merge
  -> 93e0dda9), then on the merged head: `cd services/api && npx vitest run` -> `Test Files  56 passed (56)`, `Tests  1707
  passed (1707)`; `python ops/lib/run-named-tests.py P-COST-01` -> `NAMED P-COST-01 passed=26/26`;
  `python ops/lib/check-mutate-population.py` -> `P-PROC-06: every added module is covered or allowlisted; the floor of 67
  holds` (it reads Sources/ and services/etl/etl/ only - R9); `bash ops/queue-check` -> `QUEUE OK (280 tasks)`.
  wc -l: src/config.ts 106, src/index.ts 120, test/configHarness.ts 66, test/configRoutes.test.ts 75, test/configFields.test.ts 98, test/routes.test.ts 72, test/requestReadSites.test.ts 188, test/killSwitchRoutes.test.ts 110, test/mutate/configMutants.mjs 205. ACCEPTANCE re-quoted: (1) closed JSON, keys min_app_build, planning_paused, supported_regions,
  feature_loop/trip/surprise, quota (dailyQuota over tiers x plan/loop/surprise/trip, never retyped - digit whitelist),
  config_warnings - MET (configRoutes cross product, configFields both tables, routes SELF.fetch); KV config/v1 overlay,
  per-field whitelist at every bound, invalid field drops alone and is named - MET (configFields ACCEPTED/REFUSED x
  {no KILL, env KILL=1}); KV unbound/absent -> defaults [], throws -> defaults ["record"] - MET; planning_paused more
  restrictive only, KV false cannot unpause env KILL=1 or KV KILL_SWITCH - MET (cross product + named test). (2)
  cache-control `public, max-age=300` - MET; no request read, requestReadSites APPROVED equal and a config.ts it() -
  MET; KILL never blocks /config - MET (200 under all five KILL sources); ROUTES full equality with the cross product
  and the no-row-ignores-its-variant meta-test - MET; TS population with literal floor 59 - MET. GAPS, recorded: no
  P-COST-01 name was bound (pins/ and ops/lib/named-tests.json are outside touches); `npx tsc --noEmit` fails on this
  checkout BEFORE this change too (TS2688 cannot find @cloudflare/workers-types/2023-07-01 - seen on the stashed base);
  no wrangler KV binding (declared in Env only, R2); no deploy.
