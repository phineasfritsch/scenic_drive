---
id: T-0276
title: the Worker's closures cron - Caltrans Lane Closure System (LCS) full closures for the LA district into KV as at most 50 polygons, a closures-version every route sends as areas and folds into its cache key; stale feed fails safe
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T07:59:18Z
lease_expires_at: 2026-10-06T19:59:18Z
worktree: .worktrees/T-0276
branch: task/T-0276
exclusive: []
touches: [services/api/, Tests/Fixtures/t0276/]
pins_affected: [P-SAFE-08, P-SAFE-01]
reviewer: null
depends_on: [T-0256, T-0262, T-0268]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST: fetch the public Caltrans LCS feed for District 7 (cwwp2.dot.ca.gov lcs JSON - quote URL, licence/terms page and fetch time in the Log; record one response under Tests/Fixtures/t0276/ verbatim) and count full closures vs lane closures, their geometry kinds and active windows BEFORE writing any predicate"
  - "a scheduled() handler (cron every 15 min in wrangler.jsonc) parses ONLY full closures active now, buffers each to a ruled polygon (<= 50 total, nearest-first or ruled cap order), and writes {version, fetched_at, geojson} to KV; parse is a table test over the recorded fixture by full equality, every malformed/missing field refused per row (range tables at every bound); no secret, no 511 key (511 needs the owner's key - a later task)"
  - "/plan, /loop, /isochrone, /trip pass the current closures as buildCustomModel areas (rejectCustomModel still applies) and include closures-version in every cache key; a KV read failure or a feed older than a ruled max age (P-SAFE-08: 30 min) never routes THROUGH a stale closure silently - rule fail-safe (serve with the last good set + a 'closures stale' hazard) and test it through ROUTES; KILL unaffected; a TS mutation population with a literal floor"
---
## Brief

Plan 'Closures: Worker cron every 15 min: 511 SF Bay Traffic Events (free key) + Caltrans LCS D4 -> KV closures/*.geojson
(<50 KB, <= 50 polygons); sent as areas in every request; client shows HazardFlag.closure; plan cache key includes
closures-version' and pin P-SAFE-08. The owner is in LA, so District 7 first (memory: user-lives-in-la). The custom
model already accepts closures (customModel.ts closureGeometries); nothing produces them. No deploy, no Cloudflare
resources.

## Log
- 2026-10-06T07:52:07Z filed by agent/claude-opus-5 (orchestrator) from the plan's lifecycle table (closures).
- 2026-10-06T07:59:18Z claimed by agent/claude-opus-5; lease until 2026-10-06T19:59:18Z
- 2026-10-06T08:18:21Z MEASURE (before any predicate). URL https://cwwp2.dot.ca.gov/data/d7/lcs/lcsStatusD07.json;
  docs https://cwwp2.dot.ca.gov/documentation/lcs/lcs.htm ("There is no charge for the use of this data"), which
  links the terms https://dot.ca.gov/conditions-of-use (linked, not read here - the owner reads them before deploy).
  Fetched once at 2026-10-06T08:06:07Z (date -u before curl): HTTP 200, 8553200 bytes, server Date 08:06:12 GMT,
  Last-Modified 08:04:20 GMT. Recorded VERBATIM at Tests/Fixtures/t0276/lcsStatusD07.json (ASCII, 0 CR bytes);
  the response headers at Tests/Fixtures/t0276/headers.txt with CRLF turned to LF (the hook refuses CR; metadata).
  Counts: 2808 records, every one with exactly {closure, index, location, recordTimestamp}. typeOfClosure: Full
  1708 (On Ramp 760, Off Ramp 615, Connector 299, Mainline 16, Collector 6, Conventional Hwy 4, HOV 3, Rest Area 3,
  HOV Connector 2), Lane 1028, Moving 50, One-Way Traffic 20, Traffic Break 2. Full by (code1097, code1098,
  code1022, start<=now<=end at 08:06:07Z): (f,f,f,out) 1333, (f,f,f,in) 99, (f,f,t,out) 30, (f,f,t,in) 162,
  (t,f,f,out) 1, (t,f,f,in) 63, (t,t,f,out) 11, (t,t,f,in) 9. Active Full under R3 below: 163, 64 of them 10-97.
  Geometry: begin/end lon/lat decimal STRINGS only, no polyline. Of the 163: begin==end 135, chord >500 m 10,
  >2000 m 6 (I-5 Paxton St 33.1 km, SR-2 east of Newcomb's Ranch 10.2 km, SR-14 Avenue F 8.0 km, SR-39 5.2 km,
  SR-14 Avenue J 3.5 km, SR-47 Ferry St 2.1 km). isClosureEndIndefinite "true" 20 rows (10 active);
  closureEndEpoch is never empty (2808/2808). Extent of all 5616 positions: lon -119.442216..-117.692511, lat
  33.735439..34.876668.
- 2026-10-06T08:18:21Z RULINGS (author rule; before code).
  R1 full vs lane: only typeOfClosure === "Full". Lane/Moving/One-Way Traffic/Traffic Break leave the road
  passable and are skipped WITHOUT reading their other fields (skipped, never refused).
  R2 active now: not code1022 (cancelled) and not code1098 (picked up) and (code1097 (placed) or start <= now and
  (indefinite or now <= end)). The union is the conservative side: 99 scheduled-not-yet-radioed and 1 overrunning
  placed closure are avoided. Bounds tested: start == now active, start == now+1 not; end == now active, end ==
  now-1 not.
  R3 per-row refusal (Full rows; every field the parse reads): index non-empty string; isCode1097/1098/1022
  exactly "true"|"false"; closureStartEpoch 1-10 digits; isClosureEndIndefinite "true"|"false"; closureEndEpoch
  1-10 digits (not read when indefinite); end < start refused; facility non-empty string; begin/end lon/lat
  decimal strings inside the D7 box lon [-119.5, -117.6], lat [33.7, 34.9] inclusive (the measured extent plus a
  margin; (0,0) and swapped pairs are refused). Each refused row is named {index, reason}.
  R4 buffer geometry: the feed has no road geometry. Local plane with LITERAL scales at lat 34.3 (box middle):
  110946 m/deg lat, 91961 m/deg lon (111320 cos 34.3 = 91961.26) - only + - * / sqrt, so the independent Python
  oracle recomputes bit-identically. B = 30 m. Chord <= 500 m: ONE rectangle, the chord extended B past each end
  and B either side (zero length: the 2B square). Chord > 500 m: TWO 2B gate squares, at begin and at end: a
  33 km chord rectangle would wall off every street the I-5 chord crosses; the gates stop travel THROUGH the closure
  at both ends. NOT MEASURED against OSM: whether 30 m catches the ramp an LCS point names and misses the mainline
  beside it - a follow-up measurement against the LA graph.
  R5 cap order: <= 50 polygons (customModel MAX_CLOSURE_POLYGONS). No user location exists at cron time, so not
  nearest-first: code1097 first, then facility rank Conventional Hwy, Mainline, HOV, Collector, Connector, HOV
  Connector, On Ramp, Off Ramp, Rest Area, any other last; then index ascending by code unit. Greedy fill: a
  closure's polygons stay whole; one that does not fit is dropped and counted. Measured 163 active > 50 - dropped
  is real today and is recorded in the KV record's stats.
  R6 KV: binding CLOSURES, NOT bound in wrangler.jsonc (creating it is the owner's step, as KILL_SWITCH); key
  "closures/lcs-d7"; value {version, fetched_at, geojson, stats}. version = "lcs-d7-" + 16 hex of SHA-256 over
  JSON.stringify(geojson): the same set keeps its version, so cache keys do not churn every 15 min. fetched_at =
  ISO of min(Last-Modified, cron now) - the FEED's age. Nothing is written (the last good record stays and ages
  into stale) when CLOSURES is unbound (no fetch either), the answer is not 200, has no parseable Last-Modified,
  is not JSON, `data` is not a non-empty array, or refused rows * 2 > Full rows. Cron "*/15 * * * *".
  R7 max age and fail-safe (P-SAFE-08, 30 min): per request, age = now - fetched_at; 0 <= age <= 30 min fresh;
  age > 30 min or < 0 STALE: route WITH the record's set (the last good) + hazard. UNAVAILABLE (unbound, a get
  that throws, no record, unparseable record, bad version/fetched_at, a geojson buildCustomModel refuses): route
  with no closures + hazard. Never refuse to route; the hazard is what makes it not silent. Hazard shape: every 200
  body of /plan, /loop, /isochrone (cache hit too) and /trip gains closures_hazard {state: "stale"|"unavailable",
  version, fetched_at} only when not fresh - absent when fresh, so fresh-path bodies are unchanged.
  R8 which requests carry the areas: every request whose route is DRIVEN - /plan's scenic search, /trip's scenic
  search and day legs, /loop's round trips (feed polygons first, then the retrace squares, truncated to 50).
  NOT the car_fast probe of /plan and /trip: it is never driven, its time only sets the ceiling, and a probe
  through a closure only lowers fastest (a tighter ceiling, never looser); and car_fast must not get
  buildCustomModel's distance_influence 0 band chain (customModel.ts is 299 of 300 lines, no second builder fits).
  /isochrone: Brief vs reality - GraphHopper 11's GET /isochrone has no body to carry a custom model; ruled out,
  its cache key carries the closures-version and its body the hazard. Follow-up if reach must honour closures.
  R9 cache keys: the only cache is /isochrone's reach cache; its key gains |closures-version ("none" when
  unavailable). /plan, /loop, /trip cache nothing.
  R10 KILL: the kill switch is read before the closures KV; KILL=1 makes zero closures reads (counted).
  R11 P-SAFE-08 is not a PINS.yaml row and pins/ is outside touches: - its by-name binding is a follow-up. No 511
  key, no secret, no resource.
- 2026-10-06T08:45:18Z ORACLE: `python Tests/Fixtures/t0276/oracle.py` (independent Python, R1-R6) -> rows=2808
  full=1708 active=163 refused=0 kept=42 dropped=121 polygons=50 version=lcs-d7-e3526af4d59aaad9 at now_s
  1791273972 (the response's Date). So today the cap drops 121 of 163 active Full closures (R5's order keeps every
  10-97 one that fits): nearest-first per request would need KV to hold > 50 polygons - a follow-up, ruled out here.
  RED FIRST by name, before the routes and index were wired (`npx vitest run test/closuresFeed.test.ts
  test/closuresCron.test.ts test/closuresRoutes.test.ts`): 73 failed, among them "writes the oracle's record under
  closures/lcs-d7, once, from one fetch of the D7 feed" (TypeError: default.scheduled is not a function), "wrangler.jsonc
  runs the cron every 15 minutes and binds no CLOSURES namespace", "/plan: 200 with no closures_hazard; every model
  carries the areas and the zero clause, gate-clean; no car_fast model", "/trip, a record 30 min + 1 ms old: 200 with
  closures_hazard stale, routed around the record's set" (expected [200, undefined] to equal [200, {state: stale}]).
  GREEN after wiring + harness deps (every hand-built deps gains closures: FRESH_EMPTY; every shipped-ROUTES env
  gains CLOSURES: liveClosures(), a record fetched at the fake clock's now - the fresh empty set, so earlier bodies
  are unchanged) + two approved feed-response sites in requestReadSites.test.ts by full equality: `npx vitest run`
  Test Files 39 passed (39), Tests 716 passed (716). tsc --noEmit cannot run in this checkout (TS2688
  @cloudflare/workers-types/2023-07-01 missing, not this change).
- 2026-10-06T09:44:42Z MUTATION POPULATION services/api/test/mutate/closuresMutants.mjs (13 subjects: lcsFeed,
  closuresStore, closuresCron, index, routerDeps, reachCache, plan, scenicPlanner, loop, loopPlanner, trip,
  tripPlanner, isochrone; tests closuresFeed/Cron/Routes/Driven). Added test/closuresDriven.test.ts first (a loop's
  reseed and retrace attempts keep the set, feed first, never 51; a paid trip's 5 legs carry it - 11 car_scenic
  requests). Run 1 (84 entries, floor 60): `RESULT caught=80 missed=4 trap=0 of 84`, baseline green tests=140.
  MISSED feed-end-refusal-first (no row had both positions bad) -> two rows added, the begin's reason named.
  MISSED store-max-age-60: closuresRoutes.test.ts took its ages FROM the module's own CLOSURES_MAX_AGE_MS, so the
  bound moved with the mutant (the CLAUDE.md "table compared to itself" defect) -> the test now holds the ruled
  literal MAX_AGE_MS = 1_800_000 and adds a 45-min row. MISSED cron-any-ok (`!response.ok`): the only non-200 2xx
  row was a 204 with no body -> a 203 carrying the whole feed added. MISSED feed-long-at-500 (`>` -> `>=`): differs
  only at a chord of exactly 500.0 m; a search of 28572 8-decimal begin latitudes x 20 end offsets of a lat-only
  chord near 500 m found NONE equal to 500.0 (`[]`), and the 499.9992 / 500.0003 m rows bracket the threshold
  1.1 mm apart -> moved to EQUIVALENT with that witness. Floor set to the population, literal 83.
  Re-run of the three changed (owner-approved faster verification): `--only=feed-end-refusal-first,store-max-age-60,
  cron-any-ok` -> `RESULT caught=3 missed=0 trap=0 of 3` (baseline green tests=147). --prove-floor: all four arms
  REFUSED, the real population quiet. NOT RUN: --prove-vacuity (83 runs; follow-up if the reviewer wants it).
  wc -l: closuresCron.ts 72, closuresStore.ts 87, lcsFeed.ts 190, closuresCron.test.ts 112, closuresDriven.test.ts
  58, closuresFake.ts 56, closuresFeed.test.ts 202, closuresRoutes.test.ts 174, closuresMutants.mjs 225 - all
  under 300.
- 2026-10-06T09:59:36Z FINAL (author rule): `git fetch origin` (main checkout) and merged origin/main (6e81a38) as
  the last step -> 63188b7; `git merge-base --is-ancestor origin/main HEAD` true. Gates on the merged head:
  `npx vitest run` Test Files 40 passed (40), Tests 726 passed (726); `python ops/lib/check-mutate-population.py`
  exit 0 ("every added module is covered or allowlisted; the floor of 67 holds"); `bash ops/queue-check` QUEUE OK
  (269 tasks). ops/test not run (orchestrator instruction).
  ACCEPTANCE, re-quoted:
  1 MEASURE FIRST - MET: URL, docs/terms links and fetch time quoted 08:18:21Z; one response recorded verbatim
    (lcsStatusD07.json, 8553200 bytes, sha256 48e1586ed290b085c10815a4f574cb0652ec189a8ccf091ca55a9ce1376ee7f3);
    Full vs Lane, geometry kinds and active windows counted before any predicate.
  2 scheduled() cron - MET: wrangler.jsonc triggers {crons: ["*/15 * * * *"]} (held by test); only Full closures
    active now; each buffered per R4; <= 50 in R5's ruled cap order; {version, fetched_at, geojson} (+ stats) to KV
    key closures/lcs-d7; the parse held WHOLE to the independent oracle over the recorded fixture; every field the
    parse reads refused by name per row; ranges and windows tabled at every bound (the 500 m chord bracketed
    499.9992 / 500.0003, exact 500.0 EQUIVALENT with witness); no secret, no 511 key.
  3 routes - MET for /plan, /loop, /trip (areas on every driven request, gate-clean through rejectCustomModel);
    /isochrone PARTIAL by ruling R8: closures-version in its cache key and the hazard in its body, but NO areas -
    GraphHopper's GET /isochrone has no body for a custom model (Brief vs reality). Fail-safe through ROUTES: stale
    (> 30 min, or future) routes with the last good set + closures_hazard; unavailable routes without + hazard;
    KILL=1 makes zero closures reads; mutation population closuresMutants.mjs, literal floor 83.
  OPEN for follow-up tasks: /isochrone areas; P-SAFE-08 as a PINS.yaml row (pins/ outside touches:); nearest-first
  per request (today the cap drops 121 of 163 active Full closures); the 30 m buffer measured against the LA graph;
  --prove-vacuity not run; https://dot.ca.gov/conditions-of-use read by the owner; creating and binding CLOSURES.
- 2026-10-06T10:37:58Z PRE-REVIEW SURVIVORS (2, BLOCKING) closed, both on the cron's clock line
  `parseLcsFeed(data, Math.floor(nowMs / 1000))`: S1 cron-now-is-last-modified (R2 judged at the feed's
  Last-Modified) and S2 cron-now-ceil both survived 726 tests because every clock was a whole second and no row's
  window started or ended between Last-Modified and now. CLASS closed: test/closuresCron.test.ts gains a 10-row
  table through scheduled() ("the cron's clock"), full equality on stats, at every bound - a window opening/ending
  between Last-Modified (1791273860) and now (1791273972); opening at now's second and one after; ending at now's
  second and one before; now at .500 and .999 with end == floor(now), start == floor(now), start == floor(now)+1.
  Population +3 (cron-now-is-last-modified, cron-now-ceil, cron-now-round), floor literal 83 -> 86.
  GREEN unmutated: `npx vitest run test/closuresCron.test.ts` 27 passed. RED by name (faster verification):
  `--only=cron-now-ms-as-s,cron-now-is-last-modified,cron-now-ceil,cron-now-round` -> CAUGHT cron-now-is-last-modified
  by "a window opening between Last-Modified and now (...1791273900..1791277000) is active"; CAUGHT cron-now-ceil and
  cron-now-round by "a window ending at now's second, now at .500 (...1791273000..1791273972) is active"; CAUGHT
  cron-now-ms-as-s; `RESULT caught=4 missed=0 trap=0 of 4` (baseline green tests=157). --prove-floor: all four arms
  REFUSED at floor 86, real population quiet. wc -l: closuresCron.test.ts 144, closuresMutants.mjs 228.
- 2026-10-06T10:46:08Z FINAL (round fix): `git fetch origin` (main checkout); origin/main 6e81a38 already an ancestor of c42064d
  (`git merge-base --is-ancestor origin/main HEAD` true; nothing to merge). Gates on that head: `npx vitest run` Test
  Files 40 passed (40), Tests 736 passed (736); `python ops/lib/check-mutate-population.py` exit 0; `bash
  ops/queue-check` QUEUE OK (269 tasks). ops/test not run (orchestrator instruction).
- 2026-10-06T11:28:04Z rv1-t0276 B1 (P-SAFE-08 fail-open) CLOSED as a CLASS. rv1: deleting `if (r.geojson === null) return
  null;` from record() left 736/736 green - a fresh {version, fetched_at: now, geojson: null} passed every check,
  buildCustomModel accepts null, and /plan /loop /trip routed with no areas and no closures_hazard. RULINGS, per
  field record() reads (the record, version, fetched_at, geojson) x shape: missing, null, a number, true, "", [],
  {} are each UNAVAILABLE for every field; the record itself as "", JSON null, a number, a string, an array, {} is
  UNAVAILABLE; version off CLOSURES_VERSION (15 hex, 17 hex, upper-case hex, another district, a trailing newline,
  wrapped in an array) UNAVAILABLE; fetched_at not ISO_INSTANT (a space form, a +00:00 offset, epoch ms, wrapped in an
  array) or not a date (month 13, hour 25) UNAVAILABLE; geojson a string, one Feature, a FeatureCollection with no
  features / features {} / features null / no type, 51 polygons, a Point UNAVAILABLE. ACCEPTED by ruling (a new
  table "read, by ruling", fresh: 200, no hazard, areas exactly the record's): a FeatureCollection with ZERO features
  - R6 writes it when nothing is active (the cron refuses only an empty FEED `data`, not an empty active set), so
  refusing it would turn every quiet night into a hazard; an unknown extra key - the reader is not strict, `stats`
  already rides beside the three fields and an extra key changes nothing routed; a version that is not
  sha256(geojson) - the version is the /isochrone cache key (R9), never a gate: the areas come from geojson itself,
  so a mismatch cannot route through a closure, and refusing it would DROP an honoured set for an unavailable one
  (TEST_VERSION lcs-d7-00000000000000aa already is such a record in every fresh row).
  test/closuresRoutes.test.ts: the unavailable table through ROUTES (/plan /loop /trip /isochrone) grows 9 -> 50
  rows (x4 paths = 200 tests), each `[status, closures_hazard, models with areas]` toEqual `[200, {state:
  "unavailable", version: "none", fetched_at: null}, 0]`; the ruled table 3 rows x /plan /loop /trip, toEqual
  `[200, undefined, true, the record's areas per model]`. wc -l 222. GREEN unmutated: `npx vitest run
  test/closuresRoutes.test.ts` Tests 247 passed (247).
  Population +5, one per guard line deleted (store-record-shape-unchecked, store-version-unchecked,
  store-fetched-at-unchecked, store-ms-unchecked, store-null-geojson-unchecked = rv1's); floor literal 86 -> 91.
  --prove-floor: four arms REFUSED at floor 91, real population quiet. RED by name (faster verification):
  `--only=store-null-geojson-unchecked,store-record-shape-unchecked,store-version-unchecked,store-fetched-at-unchecked,
  store-ms-unchecked,store-geojson-unchecked,store-version-loose,store-instant-loose` (baseline green tests=338) ->
  CAUGHT store-null-geojson-unchecked by "/plan, geojson null: 200 with closures_hazard unavailable and no areas";
  CAUGHT store-record-shape-unchecked by "/plan, a record that is JSON null: ..."; CAUGHT store-version-unchecked by
  "/plan, version missing: ..."; CAUGHT store-fetched-at-unchecked by "/plan, a fetched_at that is not an instant:
  ..."; CAUGHT store-ms-unchecked by "/plan, a fetched_at in month 13: ..."; CAUGHT store-geojson-unchecked by
  "/plan, geojson missing: ..."; CAUGHT store-version-loose, store-instant-loose; `RESULT caught=8 missed=0 trap=0 of
  8`. src/closuresStore.ts unchanged (the guard rv1 deleted was already there; the defect was the missing row).
- 2026-10-06T11:35:01Z FINAL (rv1 B1 fix). CORRECTION to the 11:28:04Z entry: the unavailable table grows 9 -> 52 rows
  (+44 new, the "no geojson" row renamed "geojson missing"), x4 paths = 208 tests, not 50 / 200; the suite delta is
  43 x 4 + 9 ruled = 181 (736 -> 917), which is how it was caught. `git fetch origin` (main checkout); origin/main
  1e41953 merged LAST as dc7914a (queue/claimed/T-0279 only). Gates on the merged head: `npx vitest run` Test Files 40
  passed (40), Tests 917 passed (917); `python ops/lib/check-mutate-population.py` exit 0 (P-PROC-06 floor holds);
  `bash ops/queue-check` QUEUE OK (270 tasks). ops/test not run (orchestrator instruction).
- 2026-10-06T12:09:40Z rv2 B2 (P-SAFE-08 fail-open) closed as a CLASS. Ruling: rv2 is right - every unavailable row
  and every stale row built its record over TWO_CLOSURES, none over EMPTY_CLOSURES, the record R6 writes most often
  (nothing active), so a guard skipped on an empty set (rv2: the version guard under `features?.length !== 0`) and
  `fresh = features.length === 0 || in-window` left the routes table green; the second was caught only by the one
  /isochrone cache test. test/closuresRoutes.test.ts: a SETS table {two closures -> AREAS, no closures -> undefined};
  the stale table is ages x SETS x /plan /loop /trip /isochrone (4 x 2 x 4 = 32), full equality
  `[status, closures_hazard, models present, areas per model]`; the unavailable table is its 52 rows x SETS x the
  four routes (416), the base record carrying the set (raw rows that embed a record take it too). wc -l 230.
  GREEN unmutated: `npx vitest run test/closuresRoutes.test.ts` Tests 471 passed (471) (247 + 224).
  Population +3: store-version-unchecked-on-empty (rv2 B2, verbatim), store-fetched-at-unchecked-on-empty,
  store-empty-never-stale; floor literal 91 -> 94. --prove-floor: four arms REFUSED at floor 94, real population
  quiet. RED by name, new entries only: `--only=store-version-unchecked-on-empty,store-fetched-at-unchecked-on-empty,
  store-empty-never-stale` (baseline green tests=562) -> CAUGHT store-version-unchecked-on-empty by "/plan, version
  an empty string over no closures: 200 with closures_hazard unavailable and no areas"; CAUGHT
  store-fetched-at-unchecked-on-empty by "/plan, a fetched_at that is not an instant over no closures: ..."; CAUGHT
  store-empty-never-stale by "/plan, a record 30 min + 1 ms old over no closures: 200 with closures_hazard stale,
  routed around the record's set"; `RESULT caught=3 missed=0 trap=0 of 3`. src/ unchanged (the defect was the
  missing rows).
- 2026-10-06T12:23:33Z FINAL (rv2 B2 fix). `git fetch origin` (main checkout); origin/main bd5f8cf (T-0278 App Attest +
  session JWT) merged LAST. Four conflicts, both sides kept: src/index.ts (the attest import beside runClosuresCron;
  CLOSURES beside SESSION_JWT_SECRET / IDENTITY_HEADERS / APP_ATTEST_ALLOW_DEVELOP in Env), src/routerDeps.ts
  (closures: after main`s identifyCaller identify), test/requestReadSites.test.ts (attest.ts and closuresCron.ts
  entries), wrangler.jsonc (the cron triggers and main`s vars with IDENTITY_HEADERS "1"). Gates on the merged head:
  `npx vitest run` Test Files 43 passed (43), Tests 1281 passed (1281); every closuresMutants anchor occurs exactly
  once (95 checked, 0 stale); `python ops/lib/check-mutate-population.py` exit 0 (floor 67 holds); `bash
  ops/queue-check` QUEUE OK (271 tasks). ops/test not run (orchestrator instruction).
