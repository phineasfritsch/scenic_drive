---
id: T-0359
title: Photon address search, everything but the deploy - services/search (pinned image, California index config), a Worker /search proxy that sends at most one 2-dp coordinate, and a ScenicAPIClient search client, all tested locally
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-10T03:37:26Z
lease_expires_at: 2026-10-10T11:37:26Z
worktree: .worktrees/T-0359
branch: task/T-0359
exclusive: []
touches: [services/search/, services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-COST-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 Spend through the SHIPPED ROUTES['/search'] (P-COST-01): services/api/test/searchCost.test.ts - env KILL=1 and KV KILL_SWITCH KILL=1 each answer 503 planning_paused BEFORE the body is read (a body stream that throws when read), with zero upstream requests and the quota fake untouched; the daily search allowance and ONE monthly call are reserved before the one Photon request (call log order); an exhausted daily allowance is 429 {error: quota_exhausted, resets_at} and a tripped monthly counter 503 planning_paused, both with zero upstream requests; a missing SEARCH_URL, SEARCH_SECRET or QUOTA is 503 search_unavailable with zero requests. Every enumerating table gains /search (routes.test.ts, killSwitchRoutes UPSTREAM_ROUTES, sharedEnvWorker KILLABLE/PAUSED, sweepRequests REQUESTS, requestReadSites APPROVED, configAnswerPath hashes) and the new tests are bound by name under P-COST-01 in ops/lib/named-tests.json; `python ops/lib/run-named-tests.py P-COST-01` passes."
  - "A2 Privacy through the SHIPPED route (P-PRIV-05): services/api/test/searchShape.test.ts - every bound of the body whitelist is a 400 invalid_request with zero upstream requests and no reservation (q length 0, whitespace-only, 101 UTF-16 units, U+001F and U+007F; near.lat/lon at 3 dp, just outside +-90/+-180, non-numbers; any extra key at the top and inside near; near with one key), while q at 1 and 100 units, near at exactly +-90/+-180 and at 2 dp are accepted; for every accepted body the ONE upstream request equals by full string equality the URL recomputed in the test from the ruled template (R4) and carries exactly the x-scenic-search-secret header and nothing that identifies the caller. Bound by name under P-PRIV-05; `python ops/lib/run-named-tests.py P-PRIV-05` passes."
  - "A3 Answer, fail-closed (R6): services/api/test/searchAnswer.test.ts - for a table of Photon bodies (house number + street, a named place, a street only, more than SEARCH_LIMIT features, zero features) the WHOLE /search answer equals {results:[{label,lat,lon}]} recomputed in the test; every malformed Photon answer (not JSON, no features, a non-Point geometry, a coordinate out of range or non-finite, a feature with no usable label, a non-object property bag) and every non-200 or thrown upstream is 502 search_failed by full equality."
  - "A4 Client (Sources/ScenicAPIClient Search*): Tests/ScenicAPIClientTests/SearchClientTests.swift - the request equals a typed PlanHTTPRequest literal byte for byte (url, POST, content-type + x-scenic-device, sorted-key body) with and without a bias; a bias at 3+ dp is rounded to 2 dp on the device (both coordinates, -0 normalized); a query or bias the Worker would refuse is refusedOnDevice with ZERO requests at every bound; every Worker status/body maps to one SearchOutcome (200 results / unreadable at every fail-closed bound, 400, 401, 405, 429 quota_exhausted vs other, 502, 503 planning_paused vs search_unavailable vs other, thrown = offline), each after exactly one request. `swift test --filter SearchClientTests` green natively."
  - "A5 Mutation population (CLAUDE.md numeric module rule): ops/mutate/search.py over the new Sources/ScenicAPIClient Search* files - `python ops/mutate/search.py` MUTATE OK caught=N/N, `--prove-vacuity` VACUITY PROOF OK, `--prove-floor` FLOOR PROOF OK; registered in ops/lib/mutate_population_table.py; check-mutate-population and check-mutate-only green."
  - "A6 services/search (R1, R10): Dockerfile and compose.yaml pin every image by @sha256 digest and the Photon jar by ADD --checksum=sha256; `python ops/lib/check-search-pins.py` exits 0, and its --prove-red mutants (a tag-only FROM, a tag-only compose image, the jar checksum dropped) each exit 1, quoted in the Log. README carries the owner's deploy steps; no secret value in the tree (the secret is read from the environment)."
  - "A7 RED first: the three new vitest files and SearchClientTests run against the tree before the code commit fail (no /search route -> 404; no SearchClient symbol -> compile failure), quoted in the Log; then green."
  - "A8 On the merged head: the touched vitest files and the Swift filter green; check-safety-disclaimer (Sources digests re-approved), check-mutate-population, check-mutate-only, check-line-cap, check-pins-yaml, check-exec-bits and queue-check all exit 0, each quoted."
---
## Brief

Survey 2026-10-10 (M4 "corpus FTS5 + Photon"; P-PRIV-06 typed address): services/ holds api, etl, routing, tiles -
no search; PlanPlaceSearch.swift says "Photon is not deployed and typed street addresses are a later task". The VPS
deploy is the owner's; everything else is buildable.

MEASURE FIRST: Photon's request/response shape at a pinned version (cite the source, pin the image by digest),
the Worker's existing proxy pattern for the router (secret header, quota decrement before upstream, kill switch,
route table enumerations - see memory parallel-worker-prs-conflict), and how the app's plan sheet would call it.
RULE: the query the Worker forwards (the typed text plus at most one bias coordinate at 2 decimals - CLAUDE.md
privacy invariant), quota/kill behaviour (P-COST-01: every route in the router table), the answer the client decodes
(fail-closed), and what stays out (the app wiring is a follow-up task if apps/ios digests are refused). Tests:
Worker vitest through the shipping handler with a fake upstream; client whole-body equality; P-COST-01's table gains
/search. Do NOT deploy or create Cloudflare/VPS resources.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-5).
- 2026-10-10T03:37:26Z claimed by agent/claude-opus-5; lease until 2026-10-10T11:37:26Z
- 2026-10-10T03:50:03Z MEASURED (agent/claude-opus-5).
  * Photon: newest release 1.3.0 (gh api repos/komoot/photon/releases, published 2026-08-07T16:05:01Z), one asset
    photon-1.3.0.jar 98219380 bytes, digest sha256:a89707c0045e4807b2a1180e132e68e108d998709f48b6c94b98a6e281f571a5.
    README at tag 1.3.0 line 43: "photon requires Java, version 21+"; line 113 `java -jar photon-*.jar serve`, line 116
    default http://localhost:2322. docs/usage.md@1.3.0: -listen-ip/-listen-port, -max-results (default 50, the limit
    parameter is silently trimmed to it), -default-language, -query-timeout (default 7 s), CORS off by default.
  * Photon API (docs/api-v1.md@1.3.0): GET /api?q=...; location bias `lat`,`lon` (+ zoom, location_bias_scale);
    `bbox=minLon,minLat,maxLon,maxLat`; `limit`; `lang` (one language). Answer: GeoJSON {features:[{type:"Feature",
    geometry:{type:"Point",coordinates:[lon,lat]}, properties:{name, housenumber, street, postcode, city, state,
    country, countrycode, osm_key, osm_value, osm_type, osm_id, extent?}}]}.
  * Data (download1.graphhopper.com/public, HEAD only, nothing pulled): north-america/usa/ lists only usa extracts -
    there is NO California extract. photon-db-usa-1.0-latest.tar.bz2 Content-Length 10501884940, Last-Modified
    2026-10-06T20:29:10Z, md5 65bc3094891a108a554e35c4fbb72b3f; photon-dump-usa-1.0-latest.jsonl.zst 5112204903 bytes.
    "1.0" is the newest non-master db format and the one README@1.3.0 line 83 names.
  * Base images (registry-1.docker.io HEAD, anonymous token): eclipse-temurin:21-jre index digest
    sha256:cff19e6215689161eb6162c11b86b0c60ddf802164f2eaf48d570f8fb79a36c5; caddy:2.10-alpine
    sha256:4c6e91c6ed0e2fa03efd5b44747b625fec79bc9cd06ac5235a779726618e530d.
  * Worker pattern (services/api/src): isochrone.ts order kill -> method -> body whitelist -> deps null 503 ->
    guardedPlan(kind, budget) (upstream.ts: killed, counters.read, checkQuota, reserve, THEN call); routerDeps.ts
    routerBase() refuses non-https and *.invalid; secret header set inside fetchImpl; loop.ts answers 401
    session_rejected on `who.rejected`. Enumerating tables (memory parallel-worker-prs-conflict): routes.test.ts,
    killSwitchRoutes, sharedEnvWorker, sweepRequests, requestReadSites APPROVED, configAnswerPath hashes of index.ts
    and quota.ts. planRequest.ts exports atMostTwoDecimals (toFixed(2) round trip).
  * App: apps/ios/.../FeaturePlanSheet/PlanPlaceSearch.swift says Photon is not deployed; /plan refuses a destination
    carried as a coordinate (P-PRIV-05 planPrivacy test "refuses a destination carried as a coordinate").
- 2026-10-10T03:50:03Z RULINGS (agent/claude-opus-5).
  * R1 Image: Photon 1.3.0 jar fetched by Dockerfile `ADD --checksum=sha256:a897...` onto eclipse-temurin:21-jre@sha256
    (index digest above); a Caddy 2.10-alpine@sha256 front door holds the secret check. No image is built or pulled
    here (no deploy, no VPS); the owner builds on the VPS.
  * R2 "California index": no California extract exists, so the owner unpacks the US 1.0 db (10.5 GB compressed,
    md5 published beside it) and California is enforced AT QUERY TIME by a fixed bbox in services/search/california.json
    (-124.48,32.53,-114.13,42.01), which the Worker imports - one value, no second literal. The bbox is a constant,
    not a user coordinate.
  * R3 Worker contract: POST /search, body exactly {q} or {q, near:{lat,lon}}. q: a string, 1..100 UTF-16 units, not
    whitespace-only, no C0 control or DEL. near: finite numbers, lat in [-90,90], lon in [-180,180], atMostTwoDecimals
    (planRequest's, reused). Any other key at any level, or near missing a key, is 400 invalid_request.
  * R4 What goes upstream (CLAUDE.md privacy invariant): ONE GET `${SEARCH_URL}/api?q=<q>&limit=8&lang=en&bbox=<R2>`
    plus `&lat=<toFixed(2)>&lon=<toFixed(2)>` only when near was sent, built by URLSearchParams in that key order;
    headers exactly x-scenic-search-secret (SEARCH_SECRET). Never the device id, the account, the session or a
    second coordinate. SEARCH_URL passes routerBase's test (https, not .invalid) or the route is 503.
  * R5 Order and spend: kill (env or KV) -> 503 planning_paused BEFORE the body (the app already maps that token);
    non-POST 405; body 400; deps null 503 search_unavailable; identity rejected 401 session_rejected; then
    guardedPlan kind "search", budget SEARCH_UPSTREAM_COST = 1: the daily search allowance and one monthly call are
    reserved before the one Photon request. DAILY_SEARCH_QUOTA = {anon 30, free 30, paid DAILY_PLAN_QUOTA.paid by
    reference}: a planner submits a few searches per plan and plans are 3/10 a day. quota_exhausted -> 429 with
    resets_at; any other refusal -> 503 planning_paused. quota.ts changes, so configAnswerPath's hash is re-approved.
  * R6 Answer: Photon non-200 or a thrown fetch -> 502 search_failed. Fail-closed decode: an object with a features
    array; every feature an object whose geometry is a Point with finite [lon,lat] in range and whose properties
    object yields a non-empty label; ANY bad feature refuses the WHOLE answer (502 search_failed) - a half-read
    answer is not shown. label = [name, "housenumber street" (or street), city, state] - non-empty trimmed strings,
    a repeat of the previous part dropped - joined ", ". 200 {results:[{label,lat,lon}]}, sliced to SEARCH_LIMIT 8.
    Result coordinates flow server -> device only.
  * R7 Client: SearchClient(base, transport, device) in ScenicAPIClient: POST base/search with content-type and
    x-scenic-device (the quota bucket; without it every device shares "unidentified"), body sorted-key JSON. The
    bias is rounded on the device to 2 dp ((x*100).rounded()/100, -0 -> 0) after a finite/range check; the query
    is checked against R3 on the device - a refusal sends nothing. Reply -> SearchOutcome by status then body;
    results decoded fail-closed (wrong type, empty label, out-of-range or > SEARCH_LIMIT rows -> unreadable).
    No account token or session rides on search in this task: the paid allowance is wiring, a follow-up.
  * R8 Population: the Search* Swift files are new modules under Sources/ -> ops/mutate/search.py (ledger's
    three-file shape). The Worker's TS is outside P-PROC-06's roots; its bounds are table-tested in A2/A3.
  * R9 OUT: the app wiring (PlanPlaceSearch) and how a searched address reaches /plan, which today refuses a
    destination coordinate (P-PRIV-05) - that is a ruling of its own, filed as a follow-up; the deploy (owner).
  * R10 services/search/: Dockerfile, compose.yaml (photon on an internal network only, caddy on 127.0.0.1 or the
    owner's tunnel), Caddyfile (refuses 401 without x-scenic-search-secret == {env.SEARCH_SECRET}, forwards only
    GET /api and /status), california.json, README (owner steps). ops/lib/check-search-pins.py guards the digests.
