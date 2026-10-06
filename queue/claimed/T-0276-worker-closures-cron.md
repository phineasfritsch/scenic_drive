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
