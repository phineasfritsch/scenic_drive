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
- 2026-10-06T21:46:57Z agent/claude-opus-5 (owner): PRE-REVIEW SURVIVORS S1-S3 (fable stage, worktree fm-t0288 at
  c53b1116) - all three BLOCKING, ruled as reported, no disagreement: S1 regions-prefix (isRegion loosened to a
  startsWith - no REFUSED row was a prefix/extension of a compiled region), S2 empty-text-as-absent (no ROWS entry
  stored a blank text; fakeKv serves "" as present), S3 method-unpause (the method test sent one POST; the T-0272 SITE
  regex did not see `_req` - no word boundary inside `_req` - nor `.method`). Closed by CLASS, tests through
  ROUTES['/config'], src untouched. POPULATION FIRST (RED): seven entries added - regions-prefix, regions-substring,
  regions-truncated (supported starts with the given name), blank-as-absent (`text.trim() === ""`), empty-as-absent
  (`!text`), route-method-unpause (the S3 line verbatim), route-options-empty (OPTIONS answers 204 empty);
  MIN_MUTATIONS 59 -> 66 (literal), `--prove-floor` real population quiet. Run on the pre-fix tests with
  `--only=<the seven>`: `baseline green tests=24`, MISSED regions-prefix, CAUGHT regions-substring (by the REFUSED
  row " la"), MISSED regions-truncated, MISSED blank-as-absent, MISSED empty-as-absent, MISSED route-method-unpause,
  MISSED route-options-empty, `RESULT caught=1 missed=6 trap=0 of 7`. FIX: configFields REFUSED gains
  supported_regions ["lax"] ["la2"] ["xla"] ["l"] [""] ["la","lax"] (each x {no KILL, env KILL=1}); configRoutes ROWS
  gain "empty text" configKv("") and "whitespace-only text" configKv("  \n\t ") -> defaults ["record"] under all five
  KILL sources (the no-row-ignores-its-variant meta-test covers both); the one-POST method test is replaced by METHODS
  [GET HEAD POST PUT DELETE OPTIONS PATCH] x KILLS, a non-default CONFIG and a hostile query/body, whole response
  (status, content-type, cache-control, body text) by equality to expected(); requestReadSites SITE now reads
  `\b_?(req|Request)\b` and the members .method .signal .referrer .clone .bodyUsed - the three `_req` lines of
  index.ts (health, version, the /config route as CONFIG_ROUTE) are APPROVED by whole-line equality, so ANY edit of the
  /config route line that names its request is a new site; a seen-red it() substitutes five method/signal/referrer/
  clone reads into the /config line (the S3 line among them) and asserts each is found as exactly that new site and
  the approved line gone. GREEN, `--only` on the seven plus route-method-gated and route-reads-request at 21:55:01Z:
  `baseline green tests=25`, CAUGHT regions-prefix / regions-substring / regions-truncated by "every refused value
  drops that field alone to its default and names it, under each KILL variant", CAUGHT blank-as-absent /
  empty-as-absent by "every CONFIG row x every KILL source answers 200 with the whole expected response (KILL never
  blocks /config)", CAUGHT route-method-unpause / route-options-empty / route-method-gated by "every method x every
  KILL source answers the GET response whole: the handler reads no request", CAUGHT route-reads-request by "the request
  sites under src are exactly the approved sites, file by file, line by line", `RESULT caught=9 missed=0 trap=0 of 9`;
  `git status --porcelain -- src` empty. Not re-run: the 57 untouched entries (faster verification in rounds). The
  non-blocking observations (unknown_keys vs field order in config_warnings; KILLS lacks "KV KILL_SWITCH bound, KILL
  absent") are recorded, not closed. wc -l: test/configFields.test.ts 100, test/configRoutes.test.ts 90,
  test/requestReadSites.test.ts 210, test/mutate/configMutants.mjs 217.
- 2026-10-06T22:20:53Z agent/claude-opus-5 (owner): MERGED HEAD 441d319d (git fetch origin; origin/main merged LAST - two queue
  renames, T-0283/T-0289 claimed, no src or test change): `cd services/api && npx vitest run` -> `Test Files  56 passed
  (56)`, `Tests  1708 passed (1708)` (one earlier run on this head printed 41/523 passed with no failure - a partial
  run, re-run once, the 56/1708 line is the measurement); `bash ops/queue-check` -> `QUEUE OK (280 tasks)`. Survivors
  S1-S3 closed as above; ready for the review round.
- 2026-10-06T22:59:31Z agent/claude-opus-5 (owner): rv1-t0288 FAIL (PR #177, head c53b111) B1 - fail-open: inserting
  `if (url.pathname === "/config" && url.search !== "") env = { ...env, KILL: undefined, KILL_SWITCH: undefined };` into
  default.fetch left 1708/1708 green (env KILL=1, GET /config?x=1 answered planning_paused false): the tables drove
  ROUTES['/config'] directly, and requestReadSites did not see a read through the derived `url`. RULINGS before code:
  (B1-R1) the shipped entry point is the default export's fetch; the new table calls `worker.fetch(request, env)` with
  fake env bindings, never ROUTES. (B1-R2) the Brief's variants include the path suffix `/config/`, which the router
  answered 404; RULED: the router strips ONE trailing slash from a pathname longer than "/" before the ROUTES lookup, for
  every route alike (a /plan/ reaches handlePlan and its own kill switch; `/config//` and `/configx` stay 404), so
  `/config/` answers the bare GET's response. (B1-R3) "derived" is request METADATA - a name bound on a line reading
  req.url/.headers/.method/.cf/.signal/.referrer, .searchParams, .pathname/.search/.hash, or naming an already-derived
  name, to a fixpoint per file; bindings are const/let/var, destructurings and statement-start (re)assignments; block-
  comment lines bind nothing. Body-parsed values are NOT derived (measured: seeding from body reads too grows the
  approved set 85 -> 471 lines across 17 files; metadata-only 85 -> 106 across five) - each POST route's body read is
  already its approved site. SITE also gains the members .pathname .search .hash.
  CLOSED: test/configWorker.test.ts - 16 request variants (bare GET; HEAD; POST without and with a JSON body; PUT and
  PATCH with a body; DELETE; OPTIONS; `?x=1`; `?planning_paused=false&kill=0&KILL=&unpause=1`; `/config?`; `/config/`;
  `/config/?x=1`; hostile headers x-scenic-unpause/-debug/-kill/-device/-account-token, authorization, cookie; one
  x-scenic-unpause header; every dimension at once) x the five KILL sources x the 19 CONFIG rows (moved verbatim to
  test/configRows.ts, shared with configRoutes.test.ts), whole response (status, content-type, cache-control, body text)
  by equality to expected() - 1520 worker calls; a planning_paused projection (never false through any variant under
  any of the three pausing KILL sources, KV false beside them); and the meta-test: every variant's (method, url, sorted
  headers, body text) differs from the bare GET's and from every other, and each dimension (all seven methods, a
  query, `/config?`, `/config/`, an x-scenic-* header, a body) is present. requestReadSites: derived() fixpoint; APPROVED
  gains the 21 derived lines it finds (index.ts: the RO_TOKEN check, the slash-stripping handler lookup, the 404 miss,
  the cron's `(url) => fetch(url)`, two comment lines naming token; accountTier/asn: the token uses; routerDeps: the
  raw use; telemetry: userId -> counter -> reserved); the seen-red it() inserts rv1's line and five siblings (handler +
  url.port; `const p = url.port` then `p`; `const h = req.headers` then `h.has`; `const m = req.method` then `m`;
  `const q = url.searchParams` then `q.size`) after the 404 line and asserts each is found as exactly its inserted
  lines, and that the pre-rv1 guard (derive off) misses at least one line of every sibling.
  SEEN RED, population (--only, floor 66 -> 70, configWorker.test.ts joins TESTS): `baseline green tests=29`; CAUGHT
  fetch-derived-url-unpause (rv1's mutant), fetch-header-unpause (x-scenic-unpause), fetch-method-unpause
  (OPTIONS/HEAD), fetch-trailing-slash-404 - each by "every request variant x every KILL source x every CONFIG row
  answers the bare GET's whole expected response"; `RESULT caught=4 missed=0 trap=0 of 4`; `git status --porcelain --
  src` empty. Not re-run: the 66 untouched entries (faster verification in rounds). THE GUARD ALONE (each mutant applied,
  `npx vitest run test/requestReadSites.test.ts`, restored): fetch-derived-url-unpause, fetch-header-unpause and
  fetch-method-unpause each exit=1 with "the request sites under src are exactly the approved sites, file by file, line
  by line" FAILED by name. Full suite on a1c2d23b: `Test Files  57 passed (57)`, `Tests  1712 passed (1712)`. wc -l:
  src/index.ts 120, test/configWorker.test.ts 95, test/configRows.ts 42, test/configRoutes.test.ts 56,
  test/requestReadSites.test.ts 289, test/mutate/configMutants.mjs 224.
- 2026-10-06T23:40:44Z agent/claude-opus-5 (owner): rv2-t0288 FAIL (PR #177, head 6c69f722) B1 - fail-open, same class as
  rv1: in default.fetch, after `const url = new URL(req.url);`, the line `if (Reflect.get(arguments[0], "cf")?.country ===
  "US") env = { ...env, KILL: undefined, KILL_SWITCH: undefined };` left 1712/1712 green (rv2's measurement); (a) VARIANTS
  had no cf dimension, (b) requestReadSites keys on SPELLINGS (req / .cf / derived names), so Reflect.get(arguments[0],
  "cf") is no site - a blacklist of spellings. RULINGS, before code:
  (R1) THE WHITELIST FOR REQUEST READS ON /config IS THE RUNTIME READ RECORDER, not the text guard. The text guard reads
  source and can only list spellings (req.x, derived names); `arguments[0]`, Reflect.get, destructuring, bracket keys,
  `in`, Object.keys are each one more spelling, and chasing them is the blacklist CLAUDE.md forbids (PR #101). The
  recorder sits on the OBJECT the shipped worker.fetch receives, so every read of it is seen whatever the source says:
  test/recordReads.ts wraps the Request in a Proxy with get/has/ownKeys/getOwnPropertyDescriptor traps; methods are bound
  to the real target (headers.get / clone / text keep working); objects read off it (headers, cf, body, signal) are
  wrapped too and logged under the parent path ("cf.country", "headers.get"). The text guard is KEPT AS IS (it still
  holds every other route's request sites); it is no longer what holds /config, and no spelling is added to it.
  (R2) APPROVED_READS = ["url"], by measurement: the recorder over all 20 variants x 5 KILL sources x 19 CONFIG rows logs
  exactly the one `new URL(req.url)` read; the /config handler is `(_req, env) => handleConfig(env)` and reads nothing.
  Asserted by full equality of the whole [row, kill, variant, reads] table (1900 calls), so a read ADDED anywhere on the
  /config path - cf, headers, method, body, signal, has:, ownKeys - is a named failure.
  (R3) env: the response is already asserted by full equality to expected(overrides, killed, warnings) over every KILL
  source, so a fresh env object that drops KILL/KILL_SWITCH is a behaviour failure; no env recorder is added (it would
  hold reads of a binding bag the handler legitimately reads, not the request property this class is about).
  (R4) P-COST-01's named-tests list is NOT extended. P-COST-01 is spend: KILL=1 -> zero upstream calls; /config makes no
  upstream call and its planning_paused is a client mirror - a wrongly unpaused mirror still meets a 503 at /plan, /loop,
  /isochrone (bound there). ops/lib/named-tests.json is also outside this task's touches (services/api/). The new tests
  are held by the configMutants population (TESTS includes configWorker.test.ts; the three new entries are caught).
  CLOSED: test/configWorker.test.ts - VARIANTS gains `cookie header alone`, `cf country US`, `cf colo LAX asn 13335`,
  `cf empty object`, and `every dimension at once` now carries cf {country: US} (20 variants with the bare GET); the
  meta-test's signature adds the request's cf, and its dimension list adds a cookie header and the exact cf set
  (`{"colo":"LAX","asn":13335}`, `{"country":"US"}` x2, `{}`); new it() `the shipped worker.fetch reads exactly
  APPROVED_READS off every request variant x KILL source x CONFIG row, any spelling`; new it() `the read recorder names
  every probe spelling and keeps the request working (headers.get answers through it)` - Reflect.get cf -> [cf,
  cf.country] "US", arguments[0] cookie -> [headers, headers.get] "planning_paused=false", destructured cf -> [cf,
  cf.country], bracket method -> [method] "POST", "cf" in q -> [has:cf] true, by full equality.
  SEEN RED, src/index.ts probes (each inserted after URL_LINE alone, `npx vitest run test/configWorker.test.ts`, json
  reporter; .build/rv2probe.py, restored byte-equal, `git status --porcelain -- services/api/src` empty):
    PROBE rv2 exact line: passed=2/5 - FAILED the behaviour table, the planning_paused projection, and `the shipped
      worker.fetch reads exactly APPROVED_READS off every request variant x KILL source x CONFIG row, any spelling`
    PROBE arguments cookie: passed=2/5 - the same three FAILED by name
    PROBE destructure cf: passed=2/5 - the same three FAILED by name
    PROBE read-only Reflect.get cf (no behaviour change), `void Reflect.get(arguments[0], "cf");`: passed=4/5 - FAILED
      only `the shipped worker.fetch reads exactly APPROVED_READS ... any spelling` - the read itself is seen, with no
      unpause to see.
  POPULATION (--only, floor 70 -> 73): fetch-reflect-cf-unpause (rv2's exact line), fetch-arguments-cookie-unpause,
  fetch-destructure-cf-unpause. `--prove-floor`: empty table, one short (72), a subject unmutated, a new subject - each
  REFUSED; real population quiet. `population mutations=73 (floor 73) ... ONLY=3`, `baseline green tests=31`, CAUGHT
  all three by "every request variant x every KILL source x every CONFIG row answers the bare GET's whole expected
  response", `RESULT caught=3 missed=0 trap=0 of 3`. Not re-run: the 70 untouched entries (faster verification in rounds).
  Full suite (pre-merge): `Test Files  57 passed (57)`, `Tests  1714 passed (1714)` (one earlier run under load printed
  52 files / 1683 and no failure; re-run once, as ruled for load flakes). wc -l: src/index.ts 120 (untouched),
  test/configWorker.test.ts 137, test/recordReads.ts 36, test/mutate/configMutants.mjs 233.
- 2026-10-07T00:28:46Z agent/claude-opus-5 (owner): rv3-t0288 FAIL (PR #177, head 91dc02e3) B1 - a request read through a
  NATIVE prototype getter (`Object.getOwnPropertyDescriptor(Object.getPrototypeOf(arguments[0]), "cf")?.get?.call(
  arguments[0])`, gated on country "CA", inserted after URL_LINE) left 1714/1714 green: the recorder's Proxy fails the
  native brand check (thrown, swallowed), the table has no CA row, the text guard keys on no identifier in the line.
  RULINGS (stop the spelling race; close the class structurally):
  (R5) Part 1 needs no code change, ruled by reading index.ts and config.ts: handleConfig(env: ConfigEnv) takes env
  only and reads no request; ROUTES' entry is `"/config": (_req, env) => handleConfig(env),` and default.fetch hands
  every handler the runtime's env unchanged. What rv3 exploited is that index.ts's bytes could change unseen - the
  dispatcher was already minimal; part 2 now freezes it.
  (R6) CONTENT PIN (T-0273's pattern: whole-file sha256, CRLF normalized), test/configAnswerPath.test.ts `the /config
  answer path is exactly the approved bytes` over index.ts (the dispatcher: default.fetch, ROUTES, Env), config.ts
  (the body), killSwitch.ts (planning_paused's source), quota.ts (the quota display's source). config.ts imports only
  killSwitch and quota; those two import nothing - the closure is complete. The hashes are of 91dc02e3's bytes (no src
  file changed this round). Any edit to the four, any spelling, fails by name; re-approving is a visible ANSWER_PATH
  change in the same diff.
  (R7) WHY THE REST OF src CANNOT CHANGE THE /config ANSWER (not pinned: pinning all 55 modules would make every
  unrelated Worker PR re-approve a hash, and a hash nobody reads is a rubber stamp). The rest of src runs on the /config
  path only as index.ts's imports, at module load, with no request in hand; no function of theirs runs while /config
  is answered (ROUTES' /config entry calls handleConfig alone). So it can reach the answer only by changing shared
  runtime state the pinned code uses: a mutable export of config/killSwitch/quota, an intrinsic or a global. Exports:
  ESM bindings are read-only to importers; config's DEFAULTS/FIELDS/SUPPORTED_REGIONS and quota's tables are objects
  a module could mutate at load, but with no request at load such a mutation is unconditional and the behaviour table
  (configHarness keeps its OWN literal DEFAULTS) answers it; quota tables are also the enforced quotas, held by their
  own tests. Intrinsics/globals: closed by BEHAVIOUR, spelling-independent - `loading the shipped worker leaves every
  global, intrinsic and prototype the /config answer runs on untouched` snapshots globalThis's own properties, theirs
  and their prototypes' (descriptor value/get/set/flags by identity, every [[Prototype]]; 1000+ entries), imports
  ../src/index, and requires zero change. Measured: one descriptor workerd answers fresh per lookup
  (navigator.languages) is compared by JSON (BY_VALUE). Meta-test: a computed-spelling patch
  (`String["proto" + "type"].endsWith = ...`) is named exactly, and restoring it empties the diff. Residual, recorded:
  the snapshot is depth 2 (a global's prototype's own members) and taken at load; a patch deeper than that, or one a
  load-time timer applies later, is not seen - R8 names the identifiers such code would need.
  (R8) WHITELIST, test/reflectionSites.test.ts: every src line (only //-leading lines skipped; block-comment lines
  compared like code) naming arguments, Reflect, getPrototypeOf, setPrototypeOf, getOwnPropertyDescriptor(s),
  defineProperty/ies, Proxy, __proto__, eval, Function, globalThis, self, constructor or prototype must equal an
  approved (file, whole trimmed line). Measured first (.build/t0288measure.py, 91dc02e3): 14 sites in 12 files - three
  `Object.prototype.hasOwnProperty.call(` lines (config, quota, telemetryPoint), ten class `constructor(` lines and
  customModel's JSDoc line naming the constructor, ro.ts's `--self-test` JSDoc line (self). self and constructor are
  added to rv3's list as the two remaining spellings of the global object / Function. Defence in depth: R6 and R7 are
  the closures; this one names the site.
  (R9) Part 4, configWorker.test.ts `a request whose cf and headers answer every key with a sentinel answers the bare
  GET's whole expected response`: the request (a Proxy over the real one) answers cf and headers with SENTINEL - a
  callable Proxy whose every key is itself, Symbol.toPrimitive "1", `in` true - through worker.fetch, ROWS x KILLS x
  {bare GET, every dimension at once}, by full equality; its meta-line checks the sentinel answers "1" for
  cf.country, cf.asn.x and headers.get(...). A strict-equality gate (`=== "CA"`) no finite value satisfies is R6/R8's.
  SEEN RED (.build/t0288rv3probe.py; each probe applied alone, vitest json over configAnswerPath, reflectionSites,
  configWorker, requestReadSites; restored, `src clean after restore: True`):
    PROBE rv3 exact line (index.ts): passed=16/18 FAILED ["the /config answer path is exactly the approved bytes",
      "every src line naming a reflection or indirection identifier is an approved site, by full equality per file"]
    PROBE read-only Reflect probe (plan.ts, `void Reflect.ownKeys({});`): passed=17/18 FAILED ["every src line naming a
      reflection or indirection identifier is an approved site, by full equality per file"]
    PROBE load-time intrinsic patch, computed spelling (plan.ts; String.prototype.endsWith + JSON.stringify, gated on a
      min_app_build no row has, so the behaviour table stays green): passed=16/18 FAILED ["loading the shipped worker
      leaves every global, intrinsic and prototype the /config answer runs on untouched", "every src line naming a
      reflection or indirection identifier is an approved site, by full equality per file"] (the second only by the
      probe's `as "prototype"` cast)
    PROBE loose cf gate (index.ts, `cf?.unpause == 1`): passed=12/18 FAILED [content pin, APPROVED_READS, the sentinel
      row by name, and the three requestReadSites tests]
  GREEN: the three files 11/11 before the probes.
  POPULATION (--only, floor 73 -> 75; TESTS += configAnswerPath, reflectionSites): fetch-proto-getter-cf-unpause (rv3's
  exact line), plan-load-intrinsic-patch-unpause (its sibling outside the pinned files, computed spelling). --prove-floor:
  empty, 74, a subject unmutated, a new subject - each REFUSED; real population quiet. `population mutations=75 (floor
  75) equivalent=1 subjects=2 tests=8 ONLY=2`, `baseline green tests=37`, CAUGHT fetch-proto-getter-cf-unpause by "the
  /config answer path is exactly the approved bytes", CAUGHT plan-load-intrinsic-patch-unpause by "loading the shipped
  worker leaves every global, intrinsic and prototype the /config answer runs on untouched", `RESULT caught=2 missed=0
  trap=0 of 2`. Not re-run: the 73 untouched entries (faster verification in rounds).
  MERGED HEAD: git fetch origin; origin/main d4726989 is already an ancestor of 985ba7b7 (nothing to merge). Full
  suite on it: `Test Files  59 passed (59)`, `Tests  1720 passed (1720)`, EXIT 0. `run-named-tests.py P-COST-01`: NAMED
  P-COST-01 passed=26/26. ops/queue-check: QUEUE OK (280 tasks). wc -l: test/configAnswerPath.test.ts 100,
  test/reflectionSites.test.ts 67, test/configWorker.test.ts 167, test/mutate/configMutants.mjs 248; src untouched.
