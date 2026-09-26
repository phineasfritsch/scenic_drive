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
- 2026-09-26T01:16:34Z STAGE 3 LANDED - the whole-LA import (clauses 2 and 3), counts quoted as the stage landed.
  Command (WSL, foreground inside the background job, redirect INSIDE WSL):

      wsl -e bash -lc "cd /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/.worktrees/T-0209 && bash services/routing/import-graph.sh /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/work/la/la-tagged.osm.pbf /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/services/routing/work/t0209/graph-la scenic-routing:t0209 > .../work/t0209/import-la.log 2>&1"

  Honest note: the FIRST import (01:06-01:10Z) had its log redirected on the Windows side of `wsl -e`, and
  stdout and stderr clobbered each other in the file (the pass1/pass2 lines were overwritten; kept as
  work/t0209/import-la-clobbered.log). Its end state was the same `GRAPH nodes=951816 edges=1194924`, but a count
  that cannot be quoted from its own log is not quoted: the import was RE-RUN with the redirect inside WSL, and
  every number below is from that second log and that second graph.

      == input ==
      -rwxrwxrwx 1 phineas phineas 45914107 Sep 19 14:55 .../services/etl/work/la/la-tagged.osm.pbf
      648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39  .../services/etl/work/la/la-tagged.osm.pbf
      == import: scenic-routing:t0209 -> .../services/routing/work/t0209/graph-la ==
      GraphHopper - version 11.0|2025-10-14T14:28:00Z (9,24,7,5,2,9)
      pass1 - finished, processed ways: 565,874, accepted ways: 560,210, way nodes: 2,563,043, relations: 311, totalMB:640, usedMB:326
      pass2 - finished, processed ways: 565,874, way nodes: 2,563,043, nodes with tags: 320,541, node tag capacity: 4,202,496, ignored barriers at junctions: 290
      Finished reading OSM file. pass1: 14s,  pass2: 43s,  total: 58s
      Finished reading OSM file: /data/la-tagged.osm.pbf, nodes: 951,816, edges: 1,194,924, zero distance edges: 70,743
      PrepareRoutingSubnetworks - car_scenic - Marked 690371 subnetworks (biggest: 354 edges) -> 3 components(s) remain (smallest: 446, biggest: 1676529 edges), total marked edges: 18529
      PrepareRoutingSubnetworks - car_fast - Marked 690371 subnetworks (biggest: 354 edges) -> 3 components(s) remain (smallest: 446, biggest: 1676529 edges), total marked edges: 18529
      GraphHopper - nodes: 951,816, edges: 1,194,924
      GraphHopper - flushing graph car|RAM_STORE|... bounds: -119.0609263,-117.7641001,33.6832753,34.4920674 ...
      SCENIC_EV present=true bits=4 max=10
      GRAPH nodes=951816 edges=1194924
      exit=0

  accepted ways 560,210 against the filtered clip's 560,208 (T-0224 Brief): +2, not reconciled here - the
  tagged PBF is T-0208's artifact, not la-filtered.osm.pbf, and 2 of 565,874 is recorded rather than explained.
  The graph's encoded values, from graph-la/properties.txt: `scenic_score bits:4 max_storable_value:15
  max_value:9` (the highest score the LA import encoded is 9) and `osm_way_id bits:31 max_value:1560236183`;
  `profiles=car_fast|-421433575,car_scenic|1913116034` (identical to T-0213's window: same config, same profiles);
  `datareader.import.date=2026-09-26T01:13:59Z`.

  THE GRAPH'S IDENTITY (R6 - there is no /info; this is what T-0221 compares). Path: MAIN checkout
  services/routing/work/t0209/graph-la (never under .worktrees/). Digest = sha256 of the manifest below
  (`<sha256>  <name>\n` per file, files sorted by name), computed by tools/route_la_pairs.py graph_digest():

      GRAPH_DIGEST sha256=eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb
      9358b40710ff04bf6e287c08795af9e0fc4e7e6f68cb9fb0266debf716b092ae  edgekv_keys
      678fdf7f4e194d8b0387012aff2ebd8b8d3cce6f2d0b14227bded36883709766  edgekv_vals
      0d17354d11436e32479d92d84e7037aa7dbe5924ebbe754f4ae36b49e2d60b66  edges
      9e6c1e3872b75c0a6bc710485dd80727bb87e80e78b1f005bdac42e671ec92cb  geometry
      747b818a0ff193e8fb1ed1c6369643fbd734c99d545d6b10cc97a951583637a0  location_index
      04bacbc54e155cac2ec119fdce485ac585534735321b98e558f78d3b62c963d1  nodes
      fb29845262227854ee5a08c99e7a20bdb550240773b9d13c726262eba91e5839  properties
      786867b0a998feefdf942193ef4d9619c499790481fb5050dd4bc80d3c5d53bb  properties.txt

  `properties` carries the import date, so a RE-import produces a different digest by construction: T-0221
  opens THIS directory, it does not rebuild it. P-PROD-04's three-way equality stays PENDING (no golden exists).
- 2026-09-26T01:28:46Z STAGES 4 AND 5 LANDED - the three pairs routed at car_fast and lambda {0,1,2,4,8} on the whole-LA
  graph, with path details (numbers only; the rulings follow in the next entry). One container run per pair:

      $ python services/routing/tools/route_la_pairs.py      # image scenic-routing:t0209, heap -Xmx6g,
        # graph/models/raw output under the MAIN checkout's services/routing/work/t0209/ (graph-la, models, routes)
      GRAPH_DIGEST sha256=eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb   (the stage-3 graph)
      PAIR westwood-malibu from=34.0669,-118.4399 to=34.0356,-118.6894
        ROUTE -              time_ms= 1667261 min=  27.79 distance_m=  26776.4 edges=308
        ROUTE lambda-0.json  time_ms= 1667261 min=  27.79 distance_m=  26776.4 edges=308
        ROUTE lambda-1.json  time_ms= 1667261 min=  27.79 distance_m=  26776.4 edges=308
        ROUTE lambda-2.json  time_ms= 1667261 min=  27.79 distance_m=  26776.4 edges=308
        ROUTE lambda-4.json  time_ms= 1667261 min=  27.79 distance_m=  26776.4 edges=308
        ROUTE lambda-8.json  time_ms= 3341893 min=  55.70 distance_m=  52301.5 edges=399
        T_NONDECREASING westwood-malibu True T=[1667261, 1667261, 1667261, 1667261, 3341893]
        W0 westwood-malibu seconds+30/km=[2470.55, 2470.55, 2470.55, 2470.55, 4910.94]
        BITE westwood-malibu T0=1667261 T8=3341893 spread=+100.44%
        RUNS (all six routes)  residential=0.0m living_street=0.0m service=0.0m mixed=0.0m minor_total=0.0m
      PAIR westwood-woodland-hills from=34.0669,-118.4399 to=34.1684,-118.6058
        ROUTE -              time_ms= 1208634 min=  20.14 distance_m=  28057.6 edges=163
        ROUTE lambda-0.json  time_ms= 1208634 min=  20.14 distance_m=  28057.6 edges=163
        ROUTE lambda-1.json  time_ms= 1201286 min=  20.02 distance_m=  28386.3 edges=139
        ROUTE lambda-2.json  time_ms= 1589597 min=  26.49 distance_m=  27907.3 edges=231
        ROUTE lambda-4.json  time_ms= 1589597 min=  26.49 distance_m=  27907.3 edges=231
        ROUTE lambda-8.json  time_ms= 1589597 min=  26.49 distance_m=  27907.3 edges=231
        T_NONDECREASING westwood-woodland-hills False T=[1208634, 1201286, 1589597, 1589597, 1589597]
        W0 westwood-woodland-hills seconds+30/km=[2050.36, 2052.88, 2426.82, 2426.82, 2426.82]
        BITE westwood-woodland-hills T0=1208634 T8=1589597 spread=+31.52%
        RUNS (all six routes)  residential=0.0m living_street=0.0m service=52.3m[1087155744,1087155743] mixed=52.3m['service'] minor_total=52.3m
      PAIR santa-monica-topanga from=34.0195,-118.4912 to=34.0676,-118.5957
        ROUTE -              time_ms= 1213650 min=  20.23 distance_m=  19299.9 edges=169
        ROUTE lambda-0.json  time_ms= 1213650 min=  20.23 distance_m=  19299.9 edges=169
        ROUTE lambda-1.json  time_ms= 1213650 min=  20.23 distance_m=  19299.9 edges=169
        ROUTE lambda-2.json  time_ms= 1213650 min=  20.23 distance_m=  19299.9 edges=169
        ROUTE lambda-4.json  time_ms= 1213650 min=  20.23 distance_m=  19299.9 edges=169
        ROUTE lambda-8.json  time_ms= 1274240 min=  21.24 distance_m=  19601.5 edges=178
        T_NONDECREASING santa-monica-topanga True T=[1213650, 1213650, 1213650, 1213650, 1274240]
        W0 santa-monica-topanga seconds+30/km=[1792.65, 1792.65, 1792.65, 1792.65, 1862.28(+res)]
        BITE santa-monica-topanga T0=1213650 T8=1274240 spread=+4.99%
        RUNS -  .. lambda-4 residential=0.0m living_street=0.0m service=174.8m[723963657] mixed=174.8m['service'][723963657] minor_total=223.6m
        RUNS lambda-8.json  residential=813.9m[121941230,384819177] living_street=0.0m service=174.8m[723963657] mixed=813.9m['residential'][121941230,384819177] minor_total=1037.5m
      SUMMARY monotone=2/3 bites=westwood-malibu:+100.44%,westwood-woodland-hills:+31.52%,santa-monica-topanga:+4.99%
      SUMMARY longest_mixed_minor_run westwood-malibu 0.0m model=- classes=[] ways=[]
      SUMMARY longest_mixed_minor_run westwood-woodland-hills 52.3m model=- classes=['service'] ways=[1087155744,1087155743]
      SUMMARY longest_mixed_minor_run santa-monica-topanga 813.9m model=lambda-8.json classes=['residential'] ways=[121941230,384819177]
      RUN_WAY_SCORE way=121941230 edges=15 scenic_score=4
      RUN_WAY_SCORE way=384819177 edges=1 scenic_score=2
      RUN_WAY_SCORE way=723963657 edges=1 scenic_score=0
      RUN_WAY_SCORE way=1087155743 edges=1 scenic_score=0
      RUN_WAY_SCORE way=1087155744 edges=2 scenic_score=0

  (RUNS rows that are identical across routes are folded onto one line here; route-la-pairs.txt has all 18.)
  REPLAYED: the whole run was executed twice (the second added the RUN_WAY_SCORE probe); the three raw
  route-details outputs are byte-identical between runs (`cmp` silent on all three; routes-run1/ kept). The
  first run's table is the one above minus the W0 and RUN_WAY_SCORE lines.
  What the run ways ARE, read out of the tagged PBF (T-0208's artifact, read-only):

      $ wsl -e bash -lc "docker run --rm -v .../services/etl/work/la:/data:ro scenic-etl:t0038 osmium getid /data/la-tagged.osm.pbf w121941230 w384819177 w723963657 w1087155744 w1087155743 -f opl"
      w121941230  highway=residential name=7th Street maxspeed=30 mph lanes=2 surface=asphalt scenic_score=4 (unit 0.3950)
      w384819177  highway=residential name=7th Street lanes=2 scenic_score=2 (unit 0.1960)
      w723963657  highway=service (no name) scenic_score=0
      w1087155743 highway=service (no name) scenic_score=0
      w1087155744 highway=service (no name) scenic_score=0

  The graph's encoded scores equal the PBF's tags on all five ways (4, 2, 0, 0, 0).
- 2026-09-26T01:30:38Z RULINGS FROM THE MEASUREMENT (R7, R8), written after the numbers above, and the verdicts they give.

  (V1) T(lambda) IS NOT NON-DECREASING ON WESTWOOD -> WOODLAND HILLS - clause 4 FAILS on that pair and is not
  re-worded. T(0) = 1,208,634 ms, T(1) = 1,201,286 ms: lambda 1 returns a route 7,348 ms (0.61 %) FASTER and
  328.7 m longer. Why, from the measured numbers and the model, not asserted: GraphHopper minimises WEIGHT,
  Sum(t_i / p_i) + distance_influence x km (car_scenic_base.json: 30 s/km), never T. The emitted bands are exactly
  linear in lambda in 1/p (mid 1/p = 1 + lambda/2: 1, 1.5, 2, 3, 5; low 1/p = 1 + lambda: 1, 2, 3, 5, 9), so weight
  = W0(route) + lambda x S(route) with W0 = Sum(t_i x r_i) + 30 x km (r_i = 2 on a residential edge scored < 7 -
  the emitted clause - else 1). For two lambdas l < l' with optimal routes R, R', adding the two optimality
  inequalities gives (l' - l)(S(R') - S(R)) <= 0, so S falls and W0 RISES with lambda: the model guarantees W0
  non-decreasing, NOT T. The measurement agrees exactly where it can be checked with no residential edge in
  play: W0 on this pair = 2050.36, 2052.88, 2426.82, 2426.82, 2426.82 - non-decreasing while T dips. At lambda 0
  the 20.14-min route wins on the 30 s/km term (2050.36 < 2052.88 for the 20.02-min route). So T-monotonicity
  can fail on real LA data by construction whenever distance_influence > 0; ScenicKit's BudgetOutcome already
  carries `monotonicityViolated` for exactly this. RULED: reported as a FAIL of clause 4 on 1 of 3 pairs; the
  fix (distance_influence 0 in the per-request model, or stating the property on W0) is a Worker/ScenicKit model
  change outside this task's touches - STILL OPEN, to be filed.

  (V2) THE LA BITE FLOOR, re-ruled from the measured spread (never Vermont's 5 %): T(8) >= 1.025 x T(0) on every
  named pair. Measured: westwood-malibu +100.44 %, westwood-woodland-hills +31.52 %, santa-monica-topanga
  +4.99 %. 2.5 % is half the smallest measured bite and about 4x the largest non-scenic swing measured (the -0.61 %
  distance-influence swap in V1), so a floor there separates "the scenic penalty moved the route" from
  "the objective's distance term reshuffled two near-equal routes". Vermont's 5 % copied would have FAILED
  santa-monica-topanga by 0.01 pp - the reason the brief forbids copying it. All three pairs clear 2.5 %: the
  penalty BITES. Observed, not ruled: on two pairs lambda 0..4 return the IDENTICAL route and only lambda 8
  moves it (Westwood -> Malibu doubles, 27.79 -> 55.70 min), so on LA the grid is a step; a bisection over it
  has one scenic option on those pairs.

  (V3) THE RAT-RUN THRESHOLD, ruled from the 18 measured routes and T-0224's table:
    A RAT-RUN is a maximal run of consecutive residential / living_street / service edges, every one scored
    scenic_score < 7, longer than 800 m, on any returned route at any lambda.
  Why 800 m: T-0224 measured 95.17 % of LA residential WAYS at or under 800 m (4.83 % over; p90 584.7 m, median
  170.7 m) and 99.52 % of service ways (0.48 % over; p90 190.8 m). A run over 800 m is therefore longer than
  about 19 of 20 whole residential ways - it is not explained by one ordinary way's geometry, which is the
  failure mode of a threshold at p90 (it would flag 1 in 10 single ways by length alone). The measured runs
  do not argue for a looser number: 17 of 18 routes carry 0 m of residential, and the service runs are 52.3 m
  and 174.8 m (both under service p90) - the arterial network served every pair at every lambda <= 4. Why the
  score < 7 qualifier: it is the emitted model's own exemption (`road_class == RESIDENTIAL && scenic_score < 7`),
  so a residential way the scorer rates high is a scenic road, not a rat-run, under the same line.

  (V4) VERDICT - ONE RAT-RUN, CLAUSE 5 FAILS: santa-monica-topanga at lambda 8, 813.9 m of highway=residential
  7th Street (Santa Monica), ways 121941230 (scenic_score 4, 15 edges) and 384819177 (scenic_score 2, 1 edge) -
  both < 7, run 813.9 m > 800 m. It exists ONLY at lambda 8: car_fast and lambda 0..4 carry 0 m residential on
  that pair. Mechanism, from the emitted model: the anti-rat-run factor is a constant x0.5 while the bands grow
  with lambda, so a score-4 residential edge costs 1/(0.2 x 0.5) = 10 s per second driven at lambda 8 against 9
  for a low-band (score < 4) arterial - the clause's relative bite shrinks from 2x at lambda 0 to 1.11x at
  lambda 8. No other run on any route reaches 800 m. STILL OPEN, to be filed: the clause should scale with
  lambda (or gate the residential band) - a Worker/ScenicKit model change outside this task's touches.

  (V5) THE RUN ARITHMETIC IS TESTED. tests/test_route_details_runs.py (no docker): parse + runs + longest_run +
  class_metres over typed rows. Written after tools/route_details.py, so it is shown red on a MUTANT instead of
  on absence: the trailing-run flush in runs() deleted from the working copy ->

      FAILED tests/test_route_details_runs.py::test_a_run_joins_consecutive_edges_of_one_class_across_ways
      FAILED tests/test_route_details_runs.py::test_a_run_that_ends_the_route_is_counted
      FAILED tests/test_route_details_runs.py::test_longest_run_per_class_and_mixed
      3 failed, 3 passed in 0.42s

  restored byte-for-byte (`git diff --stat` empty) -> `6 passed in 0.08s`.
- 2026-09-26T01:41:13Z FINAL PRE-REVIEW COMMIT - origin/main (dc58864) merged into this branch FIRST (a895867), then every
  gate re-run bare on the merged head and the acceptance block re-quoted.

      $ cd services/routing && SCENIC_ROUTING_IMAGE=scenic-routing:t0209 python -m pytest tests -rs
      SKIPPED [1] tests\test_lambda_monotone.py:127: no graph at ...\.worktrees\T-0209\services\routing\work\graph-cache
      SKIPPED [1] tests\test_lambda_monotone.py:138: (same)
      SKIPPED [1] tests\test_lambda_monotone.py:167: (same)
      32 passed, 3 skipped in 100.51s (0:01:40)

    The 32 include this task's 4 route-details tests (their own window import with scenic-routing:t0209, the
    shipping ENTRYPOINT through docker) and 6 run-arithmetic tests, and T-0213's 10 read-back tests pointed at
    scenic-routing:t0209 - so the new jar's import and --mode probe paths (an unknown --mode now throws; import
    now returns explicitly) were exercised, not assumed. The 3 skips are the Vermont slice's, as in T-0213.

      $ bash ops/lib/check-line-cap          P-SRC-02: 111 Swift files tracked (...), none over 300 lines      exit=0
      $ bash ops/lib/check-exec-bits         P-OPS-01: 98 files, 23 required present, all modes correct       exit=0
      $ bash ops/queue-check                 QUEUE OK (235 tasks)                                             exit=0
      $ bash ops/check-pins --source-only    PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only   exit=0
      $ python ops/lib/check-mutate-population.py   P-PROC-06: every added module is covered or allowlisted; the floor of 36 holds   exit=0
        (no numeric module under services/etl/etl/ or Sources/ is added: the run arithmetic lives in
        services/routing/tools/ and is covered by tests/test_route_details_runs.py, shown red on a mutant in V5.)

      $ wc -l  (every touched file, at this commit)
        74 RouteDetailsPrinter.java   177 ScenicRouterMain.java   121 tests/test_route_details.py
        62 tests/test_route_details_runs.py   91 tools/route_details.py   178 tools/route_la_pairs.py
        51 tools/geocode_la_places.py   48 README.md      (all Python/Java under 300; tools/ files are 100644:
        they are run with `python`, not by name)
    config.yml and profiles/*.json: NOT changed (R2). ops/deploy-routing: NOT changed, NOT run (R9).

  ACCEPTANCE, item by item:
    1. PATH DETAILS - MET. `--mode route-details` on the ENTRYPOINT prints road_class / osm_way_id / distance per
       edge from GraphHopper's own path details; RED on scenic-routing:t0213 (mode absent: 4 failed), GREEN on
       scenic-routing:t0209 (4 passed), both before any LA run. Pair coordinates typed (R4; the test's window
       pair is T-0224's 34.0387,-118.5836 -> 34.0938,-118.6045, reproduced at 526739 ms / 8230.4 m).
    2. GRAPH-CACHE IN THE MAIN CHECKOUT - MET, with the /info wording corrected (R6): path
       services/routing/work/t0209/graph-la in the MAIN checkout; there is no /info in this slice, so the graph's
       identity is GRAPH_DIGEST eb43090a0de52432756d5b6f98a0dad0f568838f8272ff339042344e920d18eb (per-file
       manifest quoted) plus properties sha256 fb29845262227854ee5a08c99e7a20bdb550240773b9d13c726262eba91e5839.
    3. THE WHOLE-LA IMPORT - MET. la-tagged.osm.pbf sha256 648fc3db...3d39 verified, digest-pinned GraphHopper
       11.0 through WSL: processed ways 565,874, accepted 560,210, nodes 951,816, edges 1,194,924, zero-distance
       edges 70,743, 3 components remain; SCENIC_EV present=true; graph hash recorded as in 2; P-PROD-04's
       three-way equality PENDING (no golden exists).
    4. T(lambda) NON-DECREASING AND THE BITE - FAILS ON ONE PAIR. Five durations per pair quoted (STAGES 4 AND 5).
       Non-decreasing on westwood-malibu and santa-monica-topanga; NOT on westwood-woodland-hills (T(1) is 7,348
       ms below T(0)) - V1 shows this follows from the model (W0, not T, is what lambda orders) and verifies W0
       non-decreasing on that pair. The bite MEETS the re-ruled LA floor (V2: T(8) >= 1.025 x T(0); measured
       +100.44 %, +31.52 %, +4.99 %).
    5. RUNS AND THE RAT-RUN RULING - FAILS. Runs measured and quoted for all 18 routes; threshold ruled after
       the measurement (V3: > 800 m of residential/living_street/service edges all scored < 7). One route breaks
       it: santa-monica-topanga at lambda 8, 813.9 m of 7th Street, ways 121941230 (score 4) and 384819177
       (score 2) - named, not hidden (V4).
    6. THE VPS HALF - RECORDED AS BLOCKED on the human's box credentials (R9): SCENIC_ROUTING_HOST/USER/KEY/ROOT
       are absent from this session's environment; nothing was rsynced, flipped or deployed, and nothing here
       implies otherwise.

  STILL OPEN (to be filed; none of it is fixed by this PR):
    - Clause 4's monotonicity: T is not what the weighting orders; the per-request model keeps distance_influence
      30 s/km. Either set it to 0 in the scenic request model or restate the property on W0 (V1). Worker and
      ScenicKit (LambdaCustomModel) own the model - outside this task's touches.
    - Clause 5's rat-run: T-0207's anti-rat-run factor is a constant x0.5 while the bands scale with lambda, so at
      lambda 8 a score-4 residential costs 10 vs 9 for a low-band arterial (V4). Same owners.
    - On two of three pairs lambda 0..4 return the identical route and only lambda 8 moves it (V2): the LA lambda
      grid is a step for the budget bisection.
    - The VPS: no host, no key, no serving surface (/info, /route) - ops/deploy-routing has never touched a box.
    - The refused-reads-as-0 semantic (T-0213 R2, R10 here) - unchanged.
    - accepted ways 560,210 vs the filtered clip's 560,208: +2, recorded, not reconciled.
- 2026-09-26T02:28:24Z PRE-REVIEW MUTANT PASS - three survivors, all BLOCKING, closed by three tests, each RED on its
  mutant and GREEN on the branch. No Java, tool, config.yml or profiles/*.json byte changed: only the two test
  files (tests/test_route_details.py 121 -> 184 lines, tests/test_route_details_runs.py 62 -> 91), so
  scenic-routing:t0209 (8adaf54d179f) is still this branch's image.

  RULINGS BEFORE ANY PREDICATE (the pass's own mutant diffs went with its removed worktree, so each mutant is
  RECONSTRUCTED from its reported signature; sources, sed lines and build log under the MAIN checkout's
  services/routing/work/t0209/mutants/, images built as scenic-routing:t0209-m1/-m2/-m2b and removed after):
    m1   RouteDetailsPrinter: `covering(ways, wayIndex, edge.getLast(), ...)` - osm_way_id aligned by the edge's
         LAST point, road_class still by its first. Reproduces the reported signature: way 456361103 printed as
         service and as trunk on the canyon pair.
    m2   ScenicRouterMain: every file in --models reads `modelFiles(...).get(0)` - the first file's model under
         every file's label. Reproduces the reported signature (all lambdas = lambda-0's time).
    m2b  ScenicRouterMain: every model file routed with `null` request model. A second reading of "the model
         loop"; built so the kill does not depend on which one the pass wrote.
    m3   tools/route_details.longest_run: `if run["edges"] > best["edges"]` (edge count, not metres).
  R-S1 (the population rule overturns the handed M2 kill as written). The handed kill was "lambda-0 equals
  car_fast and lambda-8 differs" on a measured pair. MEASURED on the test's own typed canyon pair, t0209 image,
  window graph imported fresh (work/t0209/measure_canyon_l0_l8.py, output work/t0209/canyon-l0-l8.txt):

      GRAPH nodes=21137 edges=24057
      ROUTE profile=car_fast model=- time_ms=526739 distance_m=8230.4
      ROUTE profile=car_scenic model=lambda-0.json time_ms=526739 distance_m=8230.4
      ROUTE profile=car_scenic model=lambda-8.json time_ms=526739 distance_m=8230.4
      VS_CAR_FAST lambda-8.json ... same_way_sequence=True

  lambda-8 does NOT differ there, so "lambda-8 differs" cannot be written on the typed pair. RULED: a second pair
  on the SAME window graph, chosen from a measurement (work/t0209/measure_canyon_pairs.py, log
  measure-canyon-pairs.log): a 3x3 grid inside the import's own bounds (-118.9663074,-118.5138948,
  34.0026669,34.172355), all 36 pairs, `--mode route`, lambda-0 + lambda-8 from the committed T-0213 template.
  8 of 36 exit 1 (every pair touching the grid centre 34.0875,-118.7401 - no road to snap to); of the 28 routed,
  28/28 have lambda-0 == car_fast (time and distance) and 20/28 have lambda-8 slower (+4.47 % .. +73.58 %), 8 at
  +0.00 %. Chosen, the largest spread:

      PAIR 34.0366,-118.7401 -> 34.0875,-118.6044 car_fast=1449345/23971.0 l0=1449345/23971.0 l8=2515815/36423.7 l0_is_fast=True l8_spread=+73.58%

  R-S2 (the M1 kill's population). MEASURED before the predicate, per route: ways printed with more than one
  road_class, and ways whose edges come back after another way. Canyon typed pair (3 routes: 60 edges, 26 ways,
  26 stretches each) and the 18 saved LA routes (routes/*.txt; 139..399 edges, 83..165 ways, stretches == ways
  on every one): multi_class={} and revisited=[] on 21 of 21. The predicate is asserted on the typed pair only
  (the loop pair's routes were not in that population).

  THE TESTS (shipping symbols: the image's ENTRYPOINT main() through docker for M1/M2; for M3 the report the Log's
  runs verdict is read from, route_la_pairs.report_pair, which main() calls under --reuse):
    - test_route_details.py::test_each_osm_way_prints_one_road_class_in_one_unbroken_stretch (M1)
    - test_route_details.py::test_every_model_file_routes_its_own_model (M2) - the fixture now loads lambda-0.json
      AND lambda-8.json, routes the typed pair and the loop pair over one imported window graph;
      test_route_details_mode_exists_and_prints_both_routes is renamed ..._prints_every_route (three ROUTEs).
    - test_route_details_runs.py::test_the_reported_longest_run_is_longest_in_metres_not_in_edges (M3) - three
      10 m service edges, then one 500 m edge; all six RUNS lines must read service=500.0m[21].

  RED, then GREEN (full logs work/t0209/survivors-<tag>.log):

      $ cd services/routing && SCENIC_ROUTING_IMAGE=scenic-routing:t0209-m1 python -m pytest tests/test_route_details.py -rA -s
      FAILED tests/test_route_details.py::test_each_osm_way_prints_one_road_class_in_one_unbroken_stretch
      E   AssertionError: model=-: osm_way_id printed with more than one road_class: {456361103: ['service', 'trunk'], 398142769: ['primary', 'trunk']}
      (the other 5 PASSED - the edge-sum, seq, road_class-name and way > 0 checks cannot see it, as the pass said)

      $ ... SCENIC_ROUTING_IMAGE=scenic-routing:t0209-m2 ...
      ROUTE profile=car_fast model=- time_ms=1449345 distance_m=23971.0
      ROUTE profile=car_scenic model=lambda-0.json time_ms=1449345 distance_m=23971.0
      ROUTE profile=car_scenic model=lambda-8.json time_ms=1449345 distance_m=23971.0
      FAILED tests/test_route_details.py::test_every_model_file_routes_its_own_model
      E   AssertionError: lambda-8 routed 1449345 ms / 23971.0 m, car_fast 1449345 ms - measured 2515815 ms against 1449345 ms; lambda-8.json was not the model routed under its label
      (the other 5 PASSED)

      $ ... SCENIC_ROUTING_IMAGE=scenic-routing:t0209-m2b ...
      (identical ROUTE lines: the car_scenic profile with no request model routes car_fast's 1449345 ms here)
      FAILED tests/test_route_details.py::test_every_model_file_routes_its_own_model   (same assertion; other 5 PASSED)

      $ ... SCENIC_ROUTING_IMAGE=scenic-routing:t0209 ...   (the branch's image)
      ROUTE profile=car_fast model=- time_ms=526739 distance_m=8230.4
      ROUTE profile=car_scenic model=lambda-0.json time_ms=526739 distance_m=8230.4
      ROUTE profile=car_scenic model=lambda-8.json time_ms=526739 distance_m=8230.4
      ROUTE profile=car_fast model=- time_ms=1449345 distance_m=23971.0
      ROUTE profile=car_scenic model=lambda-0.json time_ms=1449345 distance_m=23971.0
      ROUTE profile=car_scenic model=lambda-8.json time_ms=2515815 distance_m=36423.7
      6 PASSED, pytest exit=0

      $ (m3 applied with sed to tools/route_details.py, __pycache__ purged) python -m pytest tests/test_route_details_runs.py -rA
      E   AssertionError: RUNS -              residential=0.0m[] living_street=0.0m[] service=30.0m[11,12,13] mixed=30.0m['service'][11,12,13] minor_total=530.0m
      FAILED tests/test_route_details_runs.py::test_the_reported_longest_run_is_longest_in_metres_not_in_edges
      (the other 6 PASSED)
      $ git checkout -- tools/route_details.py (diff lines 0), __pycache__ purged, 1.1 s -> 7 PASSED

  Not changed by this entry: acceptance items 4 and 5 still FAIL as the final pre-review entry names them, and
  every STILL OPEN line there stands. The gates are re-run bare on the head after origin/main is merged, as the
  LAST step before the push; their lines are quoted in the PR, not back-dated into this entry.
- 2026-09-26T03:12:47Z ORCHESTRATOR RULING on rv1-t0209 B3 (agent/claude-opus-5, orchestrator hat): clauses 4 and 5 were measured and FAILED honestly - T(1) < T(0) on Westwood -> Woodland Hills (1,201,286 < 1,208,634 ms) and a 813.9 m residential rat-run on 7th Street, Santa Monica at lambda 8 (ways 121941230, 384819177). Both are defects of the per-request scenic model (distance_influence 30 s/km; T-0207's residential x0.5 constant while the bands scale with lambda), not of this graph, and both sit outside this task's touches:. Filed as T-0244 on main (be9a045) with these numbers as its measured population; T-0221 (the owner's first LA drive) now depends on T-0244, so no LA route reaches the owner through this model. This task closes WITH clauses 4 and 5 recorded as FAIL once rv1's B1 (edge alignment) and B2 (unknown --mode) are closed; its deliverables - the path-details mode, the whole-LA graph at services/routing/work/t0209/graph-la (GRAPH_DIGEST eb43090a...18eb), the measurements - stand.
- 2026-09-26T03:21:26Z RULING before code on rv1-t0209 B1 and B2 (agent/claude-opus-5, owner). B3 is ruled above and
  is not re-opened here.
  B1 (edge alignment has no oracle outside the details): AGREED. Every alignment assertion in
  test_route_details.py reads the EDGE rows against the same path details they were made from, so rv1's MA - in
  RouteDetailsPrinter.covering, `intervals.get(index).getLast() <= point) index++;` replaced by
  `intervals.get(index).getLast() < point) index++;` - shifts road_class and osm_way_id together by one edge at
  every way boundary and every existing test still passes. The kill is an oracle typed by hand:
  services/routing/tests/fixtures/two-ways.osm, an OSM XML file whose way A (id 900001, highway=secondary) is two
  edges (its middle node is a junction because a spur way meets it there) and whose way B (id 900002,
  highway=tertiary) is one edge, both carrying pillar nodes so an edge is more than two route points. The test
  (tests/test_route_details_fixture.py) has the image under test import that file into a fresh temp graph, routes
  A's first node to B's last node through the ENTRYPOINT with --mode route-details, and asserts for every ROUTE:
  the EDGE ways are [900001, 900001, 900002], the classes [secondary, secondary, tertiary], and each way's summed
  EDGE metres equal that way's own haversine length (R = 6371000 m, GraphHopper's DistanceCalcEarth) computed
  from the fixture's coordinates, within 0.5 m. MA prints [900001, 900001, 900001] and credits B's metres to A.
  Disagreement with the Brief ruled: "hand-typed" holds for A, B and the spur. GraphHopper 11 marks every
  component under prepare.min_network_size (default 200, which config.yml does not override) as a subnetwork
  that nothing snaps to, so a five-node file routes nothing under the SHIPPING config. The file therefore also
  carries a 15 x 15 residential lattice (225 nodes, 420 edges, ways 910000-910029) reached only through the
  spur at A's middle node; it cannot shorten A-start -> B-end, which has exactly one simple path. The lattice
  rows are written by a loop once and committed as data; the test reads the file and derives nothing from any
  route. The ruled alternative - a test-only config with min_network_size 0 - is refused: the config under test
  is the config that ships.
  B2 (the unknown --mode error has no test): AGREED. rv1's MB is the fall-through e5ddfaa removed: in
  ScenicRouterMain.main, `throw new IllegalArgumentException("unknown --mode " + mode + " (import, route,
  route-details, probe)");` replaced by `return;`, so `--mode details` exits 0 printing nothing. The kill runs
  `--mode details` through the ENTRYPOINT and asserts a non-zero exit, `unknown --mode details` in stderr and no
  ROUTE line. Disagreement with rv1 ruled: rv1 said "against the window graph"; the test runs against the
  fixture graph instead. The mode check sits after importOrLoad in the same main(), so either graph reaches it,
  and the fixture graph needs no read-only PBF - the window graph would SKIP this test in any checkout without
  services/etl/work/la/window-tagged-1.osm.pbf.
  Image: no file the Dockerfile copies (plugins/, config.yml, profiles/) changed after e5ddfaa, the commit
  scenic-routing:t0209 (sha256:8adaf54d179f...) was built from. It is rebuilt from this head through the
  shipping Dockerfile anyway; the image id before and after is quoted with the GREEN run. MA and MB are built
  from a copy of services/routing under the gitignored work/ with the one line changed, through the same
  Dockerfile in WSL, run, then removed with docker rmi. No Java changes in this round, so the three LA
  route-details outputs are not re-run.
- 2026-09-26T03:37:27Z rv1-t0209 B1 and B2 closed, RED then GREEN (agent/claude-opus-5, owner). Files:
  services/routing/tests/fixtures/two-ways.osm (58 lines, sha256 e40caf32...9de7) and
  services/routing/tests/test_route_details_fixture.py (149 lines, 4 tests). No Java, Dockerfile, config.yml or
  profile changed, so the three LA route-details outputs are not re-run.
  The fixture graph as the image imports it: `GRAPH nodes=229 edges=424` - the 4 tower nodes of A/B/spur plus 225
  lattice nodes (A's and B's pillars are not towers), 420 lattice edges plus A's 2, B's 1 and the spur's 1.
  A = 443.862 m, B = 243.881 m by haversine over the file's coordinates; route A-start -> B-end 687.7 m.
  Mutants, each a copy of services/routing under work/ with one line changed (work/apply_mutants.py asserts the
  old text occurs exactly once), built through the shipping Dockerfile in WSL:
    MA RouteDetailsPrinter.covering: `getLast() <= point) index++;` -> `getLast() < point) index++;`
       scenic-routing:t0209-ma sha256:236b35d5a725...
    MB ScenicRouterMain.main: `throw new IllegalArgumentException("unknown --mode " + mode + " (import, route,
       route-details, probe)");` -> `return;`   scenic-routing:t0209-mb sha256:6ab2aad01e81...
  RED, MA:
    $ SCENIC_ROUTING_IMAGE=scenic-routing:t0209-ma python -m pytest tests/test_route_details_fixture.py -rA -s
    EDGE model=- seq=0 road_class=secondary osm_way_id=900001 distance_m=228.384
    EDGE model=- seq=1 road_class=secondary osm_way_id=900001 distance_m=215.478
    EDGE model=- seq=2 road_class=secondary osm_way_id=900001 distance_m=243.881
    E   AssertionError: model=-: EDGE rows [(900001, 'secondary'), (900001, 'secondary'), (900001, 'secondary')],
        the fixture's one path is [(900001, 'secondary'), (900001, 'secondary'), (900002, 'tertiary')]
    E   AssertionError: model=-: way 900001's EDGE rows sum to 687.743 m, its own length is 443.862 m
    FAILED test_edge_rows_name_the_way_and_class_of_each_fixture_edge_in_order
    FAILED test_each_fixture_way_prints_its_own_length_in_metres
    2 failed, 2 passed in 117.59s
  RED, MB:
    $ SCENIC_ROUTING_IMAGE=scenic-routing:t0209-mb python -m pytest tests/test_route_details_fixture.py -rA
    E   AssertionError: scenic-routing:t0209-mb --mode details exited 0:
    E     SCENIC_EV present=true bits=4 max=10
    E     GRAPH nodes=229 edges=424
    FAILED test_an_unknown_mode_exits_non_zero_and_names_the_mode
    1 failed, 3 passed in 91.11s
  $ docker rmi scenic-routing:t0209-ma scenic-routing:t0209-mb -> both Untagged and Deleted; work/mut-* removed.
  GREEN: scenic-routing:t0209 REBUILT from this head through the shipping Dockerfile (docker build -q -t
  scenic-routing:t0209 .): before sha256:8adaf54d179f..., after sha256:03707be60f4f... - the id moved although no
  input the Dockerfile copies changed since e5ddfaa (the jar layer was rebuilt, not reused from cache), so every
  routing result from here on is quoted against 03707be60f4f.
    $ SCENIC_ROUTING_IMAGE=scenic-routing:t0209 python -m pytest tests/test_route_details_fixture.py -rA -s
    EDGE model=- seq=0 road_class=secondary osm_way_id=900001 distance_m=228.384
    EDGE model=- seq=1 road_class=secondary osm_way_id=900001 distance_m=215.478
    EDGE model=- seq=2 road_class=tertiary osm_way_id=900002 distance_m=243.881
    (lambda-0.json and lambda-8.json print the same three rows; all three ROUTEs 44191 ms / 687.7 m)
    4 passed in 94.29s
  The whole routing suite, check-line-cap, check-exec-bits, queue-check and check-pins --source-only are re-run
  bare on the head after origin/main is merged, as the LAST step before the push; their lines are quoted in the
  PR, not back-dated into this entry. Acceptance items 4 and 5 still FAIL as the B3 ruling above records.
