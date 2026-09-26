---
id: T-0209
title: services/routing - the LA GraphHopper graph: T-0031's second half (the whole-LA tagged PBF imported with the scenic_score encoded value, T(lambda) monotone over LA pairs, the graph-cache handed to the box by rsync with the atomic symlink flip and N-1 kept)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T00:55:49Z
lease_expires_at: 2026-09-26T10:55:49Z
worktree: .worktrees/T-0209
branch: task/T-0209
exclusive: [routing-config, scenic-index]
touches: [services/routing/, ops/deploy-routing]
pins_affected: []
reviewer: null
depends_on: [T-0207, T-0208, T-0213]
verify: [ops/test, ops/check-pins]
acceptance:
  - "PATH DETAILS: T-0224 (PR #123) could not measure a single run because the t0213 image's ScenicRouterMain never calls getPathDetails and its shaded jar carries no graphhopper-web - this task adds a --mode route-details (or the web bundle) that prints road_class / osm_way_id / distance per edge for every routed pair, RED first (the mode absent) then green, BEFORE clause 3's runs are measured; the pair coordinates it routes are typed into the Log (T-0213 left its pair in prose; T-0224 typed 34.0387,-118.5836 -> 34.0938,-118.6045 and got 8230.4 m against 8121.6 m)"
  - "the whole-LA graph-cache is written under services/routing/work/t0209/ in the MAIN checkout (services/routing work dirs are gitignored and a worktree removal deletes them), never under .worktrees/T-0209 - the T-0213 precedent (work/t0213/graph-la-window, preserved in the main checkout, is what PR #124 recorded its golden from); its path and the /info graph hash quoted so T-0221 opens the same graph"
  - "the whole-LA tagged PBF (T-0208's region-normalised scores, T-0207's class cap in force) imported by the digest-pinned GraphHopper 11.0 image through WSL: the import log's way/edge counts quoted, SCENIC_EV present, /info's graph hash recorded (P-PROD-04's three-way equality named as pending until goldens exist)"
  - "T(lambda) non-decreasing over {0,1,2,4,8} on at least three LA origin-destination pairs the Log names (Westwood -> Malibu, Westwood -> Woodland Hills, Santa Monica -> Topanga) with the five durations quoted per pair, and the penalty BITES (the T-0031 bite floor re-ruled for LA from the measured spread, never copied from Vermont's 5%)"
  - "the residential and service RUNS on every returned route at every lambda on those pairs measured from path details and quoted per pair (longest run in m, its way ids, highway class); the no-rat-run threshold is RULED in the Log from that measurement and from the per-class way-length distribution (T-0224's numbers), never asserted first - a run the ruling names a rat-run FAILS the task and names the ways"
  - "the VPS half (rsync, symlink flip, N-1) either done with its transcript or recorded as blocked on the human's box credentials - never implied"
---
## Brief

From the 03:13 panel (STRATEGY, grounded): T-0031 closed as a Vermont slice whose Log rules 'the FIRST served graph
is LA' and leaves its second half unclaimed; the only graph task in the queue was T-0008 (Bay Area from R2). T-0182
(the CLI drive the owner takes) and T-0190 depended on T-0031, which is in done/, so the queue read them as
unblocked when nothing builds the graph they need. This is that task. Order ruled: #113 -> T-0207 (the class cap
moves scores) -> T-0208 (one region-wide normalisation) -> the whole-LA PBF -> this -> T-0182.

## Log
- 2026-09-19T10:46:00Z filed by agent/claude-fable-5-1 (03:13 panel, grounded). Not started.
- 2026-09-19T11:43:44Z depends_on += T-0213 by agent/claude-fable-5-1 (04:13 panel; grounded 8 of 14 - only the grounded items applied): the import mechanics over a real tagwriter PBF and ops/deploy-routing move to T-0213 (index-free, startable now); this task keeps the whole-LA import, T(lambda) over LA pairs, the LA bite floor and the 800 m no-rat-run measurement.
- 2026-09-19T15:26:14Z by agent/claude-fable-5-1 (orchestrator; 06:13 panel STRATEGY, grounded on the T-0208/T-0209 texts): clause 1's 'whole-LA tagged PBF' is now WRITTEN AND RETAINED by T-0208 (fourth acceptance line there); this task imports that artifact by sha256 and scores nothing. Lock order scenic-index: T-0208 -> T-0209 -> T-0216.
- 2026-09-19T20:26:45Z by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0): clause 3 was a predicate ('no run over 800 m') over an unmeasured population - CLAUDE.md 74615e0 forbids it; T-0112 measured the top-200 LA ways' MEDIAN length at 0.60 km, so an ordinary hillside way trips 800 m on geometry alone. Rewritten as the measurement; the threshold is ruled after T-0224's numbers exist. touches shed services/etl/etl/ per the 15:26:14Z ruling (this task imports T-0208's artifact and scores nothing). scenic-index KEPT: the lock order T-0208 -> T-0209 -> T-0216 is what holds the corpus shrink behind the routed drive.
- 2026-09-19T20:54:38Z by agent/claude-fable-5-1 (orchestrator, from T-0224's STILL OPEN 1-2): a path-details clause added first - clause 3's run measurement is impossible on the t0213 image (no getPathDetails, no graphhopper-web; T-0224 demonstrated --mode details prints nothing). T-0224's per-class way-length table (residential median 170.7 m, p90 584.7 m, 4.83 % of ways over 800 m; service median 59.9 m, 0.48 % over 800 m; three classes combined 1.53 %) is the population clause 3's ruling reads.
- 2026-09-19T21:54:54Z by agent/claude-opus-5[1m] (14:13 panel, grounded on pins/floor_*.txt, T-0203 Log :34, queue.py:541-548, RouteScore.swift:92-94): a graph-preservation clause added (the graph-cache lives in the MAIN checkout's services/routing/work/t0209/, never in the worktree). T-0221 is NOT folded in: it depends on T-0182, and folding would make the LA graph hostage to PR #124's review.
- 2026-09-26T00:55:31Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0208 merged (PR #129, la-tagged.osm.pbf sha256 648fc3dbb80c8e84...3d39 at services/etl/work/la/, 45,914,107 B) and T-0207 is done; scenic-index is free.
- 2026-09-26T00:55:49Z claimed by agent/claude-opus-5; lease until 2026-09-26T10:55:49Z
- 2026-09-26T01:04:07Z RULINGS, before any code (author rule), by agent/claude-opus-5. Read first: this file (six
  acceptance lines, every Brief/Log entry), T-0213's Log (import recipe, R2 probe, R5 no-/info, the refused-
  reads-as-0 note left for this task), T-0224's Log (the per-class table, the typed pair, R1 "no path details"),
  services/routing/ entire (ScenicRouterMain.java 166, import-graph.sh, Dockerfile, config.yml, profiles/*.json,
  tests/*), Sources/ScenicPlanCLI/main.swift (`--emit-model`). INPUT verified where it lies, read-only, MAIN
  checkout:

      $ sha256sum services/etl/work/la/la-tagged.osm.pbf
      648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39 *services/etl/work/la/la-tagged.osm.pbf
      -rw-r--r-- 45914107 bytes

  which is the promoted artifact (648fc3dbb80c8e84...3d39, 45,914,107 B) byte for byte.

  (R1) THE PATH-DETAILS MODE (clause 1). `--mode route-details` on ScenicRouterMain - the image ENTRYPOINT, the
  same main() that imports - takes route's arguments and, after each `ROUTE profile= model= time_ms= distance_m=`
  line, prints one row per routed edge:
      EDGE model=<label> seq=<i> road_class=<rc> osm_way_id=<id> distance_m=<3 decimals>
  The rows are GraphHopper's OWN path details (GHRequest.setPathDetails(road_class, osm_way_id, distance) -
  the same `details=` the served /route answers), not a second walk of the graph: `distance` is emitted once
  per edge, road_class/osm_way_id are point intervals aligned to each edge by its first point. New type
  RouteDetailsPrinter.java (one type per file). No graphhopper-web: the details live in graphhopper-core, so the
  shaded jar needs no new dependency (T-0224 R1 read the missing web jar as the blocker; it is not - the missing
  CALL was). Also ruled: an UNKNOWN --mode becomes an IllegalArgumentException; today it falls through to a
  silent exit 0, which is exactly how T-0224's `--mode details` looked like a route with no rows.
  THE TEST: services/routing/tests/test_route_details.py. It imports the canyon window
  (services/etl/work/la/window-tagged-1.osm.pbf, sha256 compared to 06046be0...0090 - T-0213's S1 rule: the
  test builds its own graph with the image under test, never a pre-built one) and routes T-0224's TYPED pair
  34.0387,-118.5836 -> 34.0938,-118.6045 with --mode route-details, car_fast plus one lambda-8 model. Asserts per
  ROUTE: at least one EDGE row; the rows' distance_m sums to the ROUTE's distance_m within 0.5 m; every
  road_class is one of GraphHopper's RoadClass names; every osm_way_id > 0; the rows are seq 0..n-1 in order.
  RED = the mode absent: SCENIC_ROUTING_IMAGE=scenic-routing:t0213 (main's jar, no route-details) - then GREEN on
  scenic-routing:t0209. Both BEFORE any LA run is measured.

  (R2) IMAGE TAG scenic-routing:t0209, built from this branch (`docker build -t scenic-routing:t0209
  services/routing` in WSL). config.yml and profiles/*.json are NOT edited (this task holds routing-config but
  needs no change: road_class and osm_way_id are already in graph.encoded_values), so a t0209 graph has t0213's
  format. The image is passed explicitly as import-graph.sh's third argument; no default elsewhere moves (the
  existing tests name the image their own red/green was recorded against).

  (R3) HEAP: -Xmx6g for the import (import-graph.sh's own JAVA_TOOL_OPTIONS; WSL has 15 GB, 14 GB free, 12
  cores; input 45.9 MB) and -Xmx6g for every routed run (the whole graph is loaded into RAM_STORE).

  (R4) THE PAIRS, geocoded ONCE each with Nominatim, 1.1 s apart, by services/routing/tools/geocode_la_places.py
  (first hit, rounded to 4 decimals):

      PLACE Westwood lat=34.0669 lon=-118.4399 osm=node/3833103042 display=Westwood, Los Angeles, Los Angeles County, California, 90095, United States
      PLACE Malibu lat=34.0356 lon=-118.6894 osm=relation/3492156 display=Malibu, Los Angeles County, California, 90265, United States
      PLACE Woodland Hills lat=34.1684 lon=-118.6058 osm=node/150946719 display=Woodland Hills, Woodland Hills-Warner Center Neighborhood Council District, Los Angeles, Los Angeles County, California, 91364, United States
      PLACE Santa Monica lat=34.0195 lon=-118.4912 osm=relation/3353288 display=Santa Monica, Los Angeles County, California, United States
      PLACE Topanga lat=34.0676 lon=-118.5957 osm=relation/10993757 display=Topanga, Los Angeles County, California, 90290, United States

  Typed pairs (the literals services/routing/tools/route_la_pairs.py carries):
      westwood-malibu          34.0669,-118.4399 -> 34.0356,-118.6894
      westwood-woodland-hills  34.0669,-118.4399 -> 34.1684,-118.6058
      santa-monica-topanga     34.0195,-118.4912 -> 34.0676,-118.5957
  A relation's point is Nominatim's centroid, not a road; GraphHopper snaps each to the nearest routable edge.

  (R5) LAMBDA SET {0,1,2,4,8}; each model is `ops/plan --emit-model <lambda>` byte for byte (ScenicKit's
  LambdaCustomModel - the Worker's model, the bytes the engine sends), written to work/t0209/models/lambda-<l>.json
  (MAIN checkout), sha256 prefixes 0:a3ca54ce5d14 1:2ea18dc1b15f 2:3fcf7e6af6f2 4:8dccac165a8c 8:38fbbb3f8994.
  (The first background `swift build --scratch-path .build/t0209` exited 1 on a Windows index-store "permission
  denied"; ops/plan's own foreground build then succeeded and every emit exited 0.) DISAGREEMENT RULED: these
  are NOT T-0213's models (profiles/car_scenic_request.json + scenic_lambda_bands.json). The emitted model
  carries T-0207's anti-rat-run clause `road_class == RESIDENTIAL && scenic_score < 7 -> multiply_by 0.5` at
  EVERY lambda, lambda 0 included. So lambda 0 is not car_fast by construction; car_fast is quoted beside the
  five and the bite is measured lambda 0 -> 8 (both carry the clause, so the spread is the scenic penalty's).
  The emitted model is ruled the right one: it is what the product sends.

  (R6) THE GRAPH HASH. There is no /info (T-0213 R5: no HTTP surface in services/routing, and this task adds
  none). Recorded instead, as T-0213 did: the graph dir's `properties` in part + its sha256, AND a whole-graph
  digest = sha256 of the `sha256sum` manifest of every file in the graph dir in sorted name order (the exact
  command quoted with the value), so T-0221 can prove it opened the same bytes. P-PROD-04's three-way
  equality is PENDING until goldens exist - no golden is recorded here.

  (R7) THE BITE FLOOR is NOT set now. It is ruled from the measured spread over the three pairs, after the
  runs, never copied from Vermont's 5%.

  (R8) THE RAT-RUN THRESHOLD is NOT set now. Per route per lambda the measurement reports the longest run of
  each class (residential, living_street, service; a run = consecutive EDGE rows of one class, T-0224's
  definition) with its metres and way ids, plus the longest mixed residential/living_street/service run. The
  threshold is ruled after, from that and T-0224's table (residential median 170.7 m, p90 584.7 m, 4.83 % over
  800 m; service median 59.9 m, p90 190.8 m, 0.48 % over 800 m). A run the ruling names a rat-run FAILS this
  task and is reported by way id.

  (R9) THE VPS HALF (clause 6). `env | grep -c SCENIC_ROUTING_` = 0: none of SCENIC_ROUTING_HOST/USER/KEY/ROOT is
  set in this session. Recorded as BLOCKED ON THE HUMAN'S BOX CREDENTIALS; they were neither asked for nor
  searched for; ops/deploy-routing is not run against any box and nothing is deployed.

  (R10) CARRIED FROM T-0213 R2, not fixed here: a scenic_refused=1 way encodes 0 (the `low` band). Fixing it
  touches the profiles and the encoded value; this task changes neither, so it stays STILL OPEN.

  (R11) WHERE THINGS LIVE: graph -> MAIN checkout services/routing/work/t0209/graph-la (clause 2); raw route
  output, models and logs -> MAIN checkout services/routing/work/t0209/; nothing under .worktrees/T-0209/.../work
  except the test's own temp window graph, which it deletes. services/routing/work/t0213/ and .artifacts/routes/
  (T-0239's) are not touched.
- 2026-09-26T01:10:19Z CLAUSE 1 - RED, then GREEN, before any LA run (R1). Code: RouteDetailsPrinter.java (new, 74
  lines), ScenicRouterMain.java (166 -> 177: `--mode route-details`, route(..., details) sets
  RouteDetailsPrinter.DETAILS on the GHRequest and prints the rows after the ROUTE line; an unknown --mode now
  throws), tests/test_route_details.py (121), tools/route_details.py (91: parse + runs, the parser the test and
  the LA measurement share), tools/geocode_la_places.py (51, R4's provenance), README.md (+6).
  RED - the same test file, pointed at main's image, which has no route-details mode:

      $ cd services/routing && SCENIC_ROUTING_IMAGE=scenic-routing:t0213 python -m pytest tests/test_route_details.py -rs
      SCENIC_EV present=true bits=4 max=10
      GRAPH nodes=21137 edges=24057
      E       AssertionError: scenic-routing:t0213 --mode route-details printed routes []
      E       AssertionError: scenic-routing:t0213 printed no ROUTE line for --mode route-details   (x3)
      4 failed in 113.94s (0:01:53)

  (the window import itself succeeded - nodes 21,137 / edges 24,057, T-0213's counts - and main() then exited 0
  printing nothing, which is the T-0224 blocker reproduced by name.)
  IMAGE scenic-routing:t0209 built from this branch in WSL (`docker build -t scenic-routing:t0209
  services/routing`): ScenicScoreParserTest `Tests run: 30, Failures: 0, Errors: 0, Skipped: 0`, BUILD SUCCESS,
  image id sha256:8adaf54d179fde6338055044f2356e8e7c526a6643dcedeedaf10e507d83f8f3.
  GREEN - the same file, default image:

      $ cd services/routing && python -m pytest tests/test_route_details.py -rs -s
      (the test prints the LAST 6000 characters of stdout, so the car_fast ROUTE line is cut off above these)
      EDGE model=- seq=53 road_class=primary osm_way_id=13404086 distance_m=7.634
      EDGE model=- seq=54 road_class=primary osm_way_id=13404086 distance_m=156.099
      EDGE model=- seq=55 road_class=primary osm_way_id=832312534 distance_m=65.753
      ...
      ROUTE profile=car_scenic model=lambda-8.json time_ms=526739 distance_m=8230.4
      (its EDGE rows follow; the four tests assert over BOTH routes)
      4 passed in 26.37s

  526739 ms / 8230.4 m is T-0224's number for this typed pair, reproduced on a graph the test imported itself.
