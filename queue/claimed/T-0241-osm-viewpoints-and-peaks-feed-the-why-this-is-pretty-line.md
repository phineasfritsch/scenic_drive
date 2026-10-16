---
id: T-0241
title: OSM viewpoints and peaks feed the 'why this is pretty' line and the Surprise candidate pool - never the per-way score
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T13:33:30Z
lease_expires_at: 2026-10-17T13:33:30Z
worktree: .worktrees/T-0241
branch: task/T-0241
exclusive: []
touches: [services/etl/etl/landmarks.py, services/etl/tests/test_landmarks.py, services/etl/tests/test_landmarks_route.py, services/etl/tests/fixtures/, ops/mutate/landmarks.py, ops/lib/mutate_population_table.py, queue/backlog/T-0379-landmarks-table-in-the-corpus-and-the-explanation-line-on-the-route-card.md]
pins_affected: []
reviewer: null
depends_on: [T-0208]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 MEASURED before any predicate (Log 2026-10-16T13:43:29Z): LA region clip services/etl/work/la/la.osm.pbf sha256 3bb2d4a8...8f4e, osmium 1.16.0 in scenic-etl - tourism=viewpoint 303 nodes (102 named) + 3 ways (1 named) + 0 relations; natural=peak 335 nodes (187 named) + 0 ways + 0 relations; ele on peaks 301 bare numbers / 34 absent / 0 with units, on viewpoints 11 bare / 295 absent. T1 (Tests/Fixtures/t0239/topanga-malibu): the fastest path (PCH) has 0 NAMED landmarks within 300 m; the Stunt Road paths pass 'Stunt Road Viewpoint' at 14 m; Saddle Peak is 437 m away (R8). No count predicate over the region is written here (R1)."
  - "A2 services/etl/tests/test_landmarks.py: landmarks.select over the full input cross product (node / way / relation x viewpoint / peak / other x name present / missing / blank x ele absent / '851' / '1234 m' / '4000 ft' / garbage x access open / private) equals, by full equality, the expected list computed per row from the variant; a meta-test proves every dimension changes some row's output."
  - "A3 landmarks.elevation_m tabled at every bound: bare, m, ft, negative, decimal, whitespace, empty, None, units garbage, two numbers, comma thousands, nan/inf spellings."
  - "A4 services/etl/tests/test_landmarks_route.py: over the real LA landmarks near T1 (fixture t1_landmarks.osm.xml, cut from the measured clip) landmarks.explain names 'Stunt Road Viewpoint' on the recorded Stunt Road path and names nothing on the recorded fastest path; never more than two names; 300 m is inclusive and the next float above it is out; nearest_way_id is tabled at the same bound with ties to the lower id."
  - "A5 not scoring: a whitelist guard fails if any module under services/etl/etl/ other than landmarks.py names `landmark` in code (identifier or string); demonstrated RED by adding `from . import landmarks` to score.py, then GREEN."
  - "A6 ops/mutate/landmarks.py ships the population with MIN_MUTATIONS equal to it, every mutant caught, registered in DRIVERS; --prove-vacuity PROVED."
  - "A7 bare gates green on the merged head: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-line-cap, check-pins-yaml, check-exec-bits, queue-check; the touched ETL tests pass."
---
## Brief

The probe's recommendation: keep the extraction for destinations and explanation, not scoring. ops/sane's
'viewpoints >= 400' check (plan) will read this table.

## Log
- 2026-09-25T23:46:40Z filed by agent/claude-opus-5 (orchestrator) from the OSM POI probe.
- 2026-09-26T00:04:22Z views probe (orchestrator, .artifacts/data-probe/views/, 3DEP 30 m, 72 rays to 8 km): every viewshed metric points the WRONG way as a score term (pair AUC 0.34-0.47; PCH sees 5-40x the view of any back road), but ocean_any is a checkable fact per way (PCH 99.7%, Saddle Peak 57%, Encinal 48%, Latigo 45% of samples) - a candidate for this explanation line ('sea views from Saddle Peak'), not the score.
- 2026-10-16T13:33:30Z claimed by agent/claude-opus-5; lease until 2026-10-17T13:33:30Z
- 2026-10-16T13:43:29Z MEASURED (agent/claude-opus-5). Scripts .artifacts/T-0241/measure.sh (run in scenic-etl via WSL docker) and measure.py / measure_t1.py (host, over the image's export).
  - Region clip `services/etl/work/la/la.osm.pbf` sha256 `3bb2d4a827d5051df73fc16bda9d6b417969b4da729733121c8e15612a9d8f4e`, osmium version 1.16.0. `osmium tags-filter nwr/tourism=viewpoint nwr/natural=peak` -> `Number of nodes: 647 / ways: 2 / relations: 0`; export 642 features.
  - By kind / type / name: viewpoint node named 102, unnamed 201; viewpoint way named 1 (MultiPolygon), unnamed 2 (1 MultiPolygon, 1 LineString); peak node named 187, unnamed 148; no peak way, no relation of either kind.
  - ele: peak bare-number 301, absent 34, anything else 0; viewpoint bare-number 11, absent 295, anything else 0. No unit suffix occurs in LA.
  - Canyon window + 2 km (the 2026-09-25 probe's poi-raw.geojsonseq, same method): viewpoint 100 nodes (24 named), peak 73 nodes (44 named) - the filed acceptance's 100/73 counted unnamed features.
  - T1 recorded routes (Tests/Fixtures/t0239/topanga-malibu, 25 paths over 7 files, 5 geometries): fastest/PCH path (478 pts) - 0 named within 300 m, 3 unnamed (18, 41, 73 m), nearest named Parker Mesa 390 m; Stunt Road path (1145 pts) - Stunt Road Viewpoint 14 m, Saddle Peak (peak 358796572, ele 851) 437 m; 1393-pt path - 2 named within 300 m incl. Stunt Road Viewpoint; 866-pt path - 0 within 300 m (David M. Brown Overlook 520 m); 1215-pt path - Stunt Road Viewpoint 14 m, Saddle Peak 498 m.
- 2026-10-16T13:43:29Z RULINGS (plan vs Brief vs code vs reality), before code:
  - R1 "ops/sane will read viewpoints >= 400 from this table" is contradicted twice by reality. (a) ops/sane already reads viewpoints: T-0372's `corpus-viewpoints` counts `places` rows of class viewpoint (T-0266's placeallow) against LA's measured floor 76 of 102. (b) 400 is the plan's figure for sfbay (sfbay counts 739); LA's whole region clip holds 306 viewpoints, named or not. A >= 400 predicate over LA could never pass. No count predicate is written; sane's existing floor stands.
  - R2 "a landmark table lands in the OSM half of the corpus": that is schema.py (DDL, ODBL_TABLES, schema_version) plus corpuswriter.py plus the region build - none in touches, and the corpus schema is consumed by the iOS fallback corpus. STOPPED and filed as T-0379 (id = max over main and every origin/task/* branch, T-0378, + 1). This task ships the extraction and the explanation as a pure module that T-0379 wires in; the tests bind to `landmarks.select` and `landmarks.explain`, the two calls T-0379 makes.
  - R3 Which objects: bound ONCE to placeallow.ALLOWLIST (`placeallow.allow_row`), restricted to the classes viewpoint and peak - viewpoint node or way, peak node only, no relation. The places table and the landmarks can therefore never disagree on what a viewpoint is. Measured: 0 relations and 0 peak ways in LA, so nothing real is dropped.
  - R4 Names: unlike places, an unnamed viewpoint or peak IS kept, with name None (201 of 306 LA viewpoints are unnamed; a destination can be 'a viewpoint'). The explanation names only named ones. A blank name is None. access private/no is refused, by placeallow.REFUSED_ACCESS, the same binding.
  - R5 ele: OSM's convention is metres. A bare number or a number with `m` is metres; `ft` is x 0.3048; rounded to 0.1 m; anything else (garbage, two numbers, comma thousands, nan/inf) is None - never guessed. LA has no unit suffix today, so the unit rows are tabled from synthetic input only.
  - R6 Point: placeallow.locate's point (a way is the mean of its distinct nodes), rounded to 5 dp. An object whose nodes are missing is skipped.
  - R7 "within 300 m": recorded routes carry no OSM way ids, so `explain` measures landmark -> route polyline (geom.point_to_polyline_m), inclusive at 300.0. `nearest_way_id(point, ways)` returns the nearest way within 300 m inclusive, ties to the lower way id, None beyond - the column T-0379 stores.
  - R8 The filed example 'passes the Saddle Peak viewpoint' is contradicted by measurement: Saddle Peak is a PEAK 437 m (and 498 m) from T1's Stunt Road paths. The radius is NOT widened to rescue an example; A4 names the measured 'Stunt Road Viewpoint' (14 m).
  - R9 explain: up to two named landmarks within 300 m, ordered by where the route first comes nearest (segment index, then distance, then osm id); a name repeated (casefold) is said once. Output is the names list; the sentence is the app's (T-0379).
  - R10 Not scoring: score.py's inputs are built by many modules (terms, assemble, corpus), so a guard on score.py alone is a blacklist. A5 is a WHITELIST over every module under services/etl/etl/: the only file that may name `landmark` in code is landmarks.py itself. Comments are stripped by tokenize, so the guard anchors on identifiers and strings.
  - R11 Numeric module -> mutation population under ops/mutate/ (CLAUDE.md, P-PROC-06), which needs ops/mutate/landmarks.py and its DRIVERS entry in ops/lib/mutate_population_table.py: both added to touches (neither is serial-only). The 'Surprise candidate pool' in the title is not in any acceptance and is left to T-0379.
