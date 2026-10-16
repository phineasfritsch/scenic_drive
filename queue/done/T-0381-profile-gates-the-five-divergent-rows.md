---
id: T-0381
title: The routing profile gates the five rows it cannot express today (tracktype>=grade3, locked barrier, ford, service values, rough smoothness) - encoded values in config.yml, clauses in car_scenic_base.json
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T19:37:33Z
lease_expires_at: 2026-10-17T19:37:33Z
worktree: .worktrees/T-0381
branch: task/T-0381
exclusive: [routing-profiles]
touches: [services/routing/config.yml, services/routing/profiles/, services/routing/tests/, services/routing/plugins/scenic-score-parser/, services/etl/etl/profilegate.py, services/etl/tests/, services/etl/tests/fixtures/gate_parity.json, ops/mutate/profilegate.py, pins/PINS.yaml]
pins_affected: [P-PROD-01, P-SAFE-01]
reviewer: agent/rv3-t-0381
depends_on: [T-0012, T-0188]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 cd services/etl && python -m pytest -q -p no:cacheprovider -o addopts= tests/test_gate_parity.py tests/test_profilegate.py -> all pass; test_only_the_typed_classes_diverge holds ZERO divergent rows"
  - "A2 cd services/routing && python -m pytest -q -p no:cacheprovider -o addopts= tests/test_profiles_static.py -> all pass, incl. every encoded value the base profile and profilegate read is in config.yml graph.encoded_values"
  - "A3 python ops/mutate/profilegate.py -> MUTATE OK caught=N/N, N == MIN_MUTATIONS > 53; --prove-vacuity -> VACUITY PROVED"
  - "A4 RED first by name: on the pre-change profile the five fixture rows fail test_profile_gives_the_fixture_verdict once their divergent records are removed (quoted), then green"
  - "A5 the one encoding table (plugins/scenic-score-parser/src/test/resources/gate_encoding.json) is read by test_profilegate (profilegate.encode) and by GateEncodingTest (GraphHopper 11's own OSMTrackTypeParser/OSMSmoothnessParser and GateFactParser) - the Java half counts only if `docker build` (mvn package runs the tests) ran here; otherwise UNVERIFIED in stillOpen"
  - "A6 swift test --filter GateParityFixtureTests green with the divergent records gone"
  - "A7 bare gates: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check"
---
## Brief

T-0012 built one gate-parity fixture through the ETL, the routing profile and ScenicKit.Gates, and recorded five
rows as typed `divergent`: tracktype>=grade3 on a non-track road, barrier=gate+locked=yes, ford=yes,
service=driveway|parking_aisle (and T-0188's drive-through, emergency_access), where the profile answers
NOT_GATED. T-0188 (PR #268) closed the ETL half; ScenicKit and the ETL now refuse all five. The router is the
last layer that routes a sedan onto them, and the router is what actually chooses the road.

The profile cannot express these today: GraphHopper has no encoded value for them in services/routing/config.yml.
MEASURE first: which GraphHopper 11 encoded values exist for each (track_type, road_access is already there;
barrier/ford/service may need `graph.encoded_values` entries or a custom tag parser like the scenic_score plugin),
the cost of each (graph re-import, memory), and what etl.profilegate can evaluate. RULE the smallest set that
gates all five on positive evidence only (CLAUDE.md: hard gates are safety only; motorway/trunk stay penalised,
never excluded). Then each divergent row's profile half goes away and test_only_the_typed_classes_diverge holds
zero rows; profilegate learns the new clauses (refusing anything it cannot read, as T-0012 rv1 ruled).

Not deployed here: a config.yml change needs a graph re-import on the VPS, which is the owner's step. Record the
re-import command and the expected graph hash change in the Log.

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0012 stillOpen and T-0188 stillOpen (the profile half of the five divergent rows was never filed).
- 2026-10-16T19:37:33Z claimed by agent/claude-opus-5; lease until 2026-10-17T19:37:33Z
- 2026-10-16T19:42:22Z MEASURED (GraphHopper 11.0 = `graphhopper.version` in plugins/scenic-score-parser/pom.xml; sources
  fetched from github.com/graphhopper/graphhopper tag 11.0, core/src/main/java/com/graphhopper/routing/; no jar or graph on
  this box). DefaultImportRegistry 11.0 knows: roundabout get_off_bike road_class road_class_link road_environment
  foot_road_access bike_road_access road_access max_speed max_speed_estimated urban_density max_weight max_weight_except
  max_height max_width max_axle_load max_length orientation surface smoothness hgv toll track_type hazmat hazmat_tunnel
  hazmat_water lanes footway osm_way_id mtb_rating hike_rating horse_rating country state crossing ferry_speed curvature
  average_slope max_slope bus_access hov_access *_temporal_access. Per divergent class:
  - tracktype: `track_type` EXISTS. OSMTrackTypeParser.handleWayTags reads `readerWay.getTag("tracktype")` on EVERY way
    (no highway test) and `TrackType.find` is `TrackType.valueOf(Helper.toUpperCase(name))`, MISSING on empty/unknown;
    enum `MISSING, GRADE1, GRADE2, GRADE3, GRADE4, GRADE5`.
  - smoothness (the title's fifth class): `smoothness` EXISTS. OSMSmoothnessParser reads `smoothness`;
    `Smoothness.find` upper-cases, MISSING on empty, OTHER on unknown; enum `MISSING, EXCELLENT, GOOD, INTERMEDIATE,
    BAD, VERY_BAD, HORRIBLE, VERY_HORRIBLE, IMPASSABLE, OTHER`.
  - ford: only `road_environment`, and OSMRoadEnvironmentParser sets FORD on `readerWay.hasTag("ford") ||
    readerWay.hasTag("highway", "ford")` - ANY ford value, ford=no included - and only after the bridge/tunnel
    branches. CarAccessParser:130 blocks on `way.hasTag("ford")` only under `block_fords` (default false, :56).
  - locked barrier on a WAY: nothing. AbstractAccessParser:102 (`node.hasTag("locked", "yes")`) and the `barriers` set
    (CarAccessParser:58-68, gate not in it) read NODES only, through gh:barrier_edge.
  - service values: nothing reads `service` except CarAccessParser:103 (`"service".equals(highwayValue) &&
    "emergency_access".equals(way.getTag("service"))` -> car access false), which etl.profilegate holds TRUE (T-0012).
  Cost: a graph re-import (graph.encoded_values changes the edge layout); track_type 3 bits (6 values), smoothness 4
  bits (10), three booleans 1 bit each - 10 bits per edge, at most one more 4-byte int of edge flags. No query cost.
- 2026-10-16T19:42:22Z RULINGS (before code).
  R1 tracktype: the built-in `track_type`; clause `track_type == GRADE3 || track_type == GRADE4 || track_type ==
     GRADE5`. GraphHopper upper-cases, Gates.swift/assemble compare exactly, so `tracktype=Grade3` is GATED by the
     profile only - the fail-safe direction (same standing as T-0012's motor_vehicle=private rows), recorded, not fixed.
  R2 smoothness: the built-in `smoothness`; clause BAD|VERY_BAD|HORRIBLE|VERY_HORRIBLE|IMPASSABLE (Gates.refusedSmoothness).
     Same casing note. NO fixture row: Tests/ScenicKitTests/GateParityFixtureTests.swift:68 pins `rows.count == 33` and
     Tests/ is not this task's; smoothness is held by test_profilegate and the encoding table (R7) instead.
  R3 ford: road_environment == FORD is REFUSED - it gates ford=no, and the fixture's own near-miss rows ford=stepping_stones
     and ford=Yes (PAVED in every layer, T-0188 rv1) would go GATED. Not positive evidence. A custom boolean `gate_ford`
     (true iff the way's `ford` is exactly "yes").
  R4 locked barrier: a custom boolean `gate_locked_barrier` (way `barrier` in {gate} and `locked` exactly "yes").
     Node-level locked barriers are GraphHopper's own car-access concern and stay so.
  R5 service: a custom boolean `gate_service_way` (highway=service and `service` in {driveway, parking_aisle,
     drive-through, emergency_access}, exact - Gates.refusedServiceValues).
  R6 SCOPE: R3-R5 need Java, so services/routing/plugins/scenic-score-parser/ joins `touches:`. Smallest: ONE TagParser
     class (GateFactParser: a boolean encoded value set true when a predicate holds), ONE holder of the three predicates
     and their sets (GateFacts), three branches in ScenicScoreImportRegistry. Positive evidence only: no tag -> false.
     No Dockerfile change (it copies src/ whole).
  R7 ONE encoding table, src/test/resources/gate_encoding.json, read by GateEncodingTest (GraphHopper's real
     OSMTrackTypeParser + OSMSmoothnessParser and our GateFactParser, run by `mvn package` inside `docker build`) and by
     test_profilegate (etl.profilegate.encode). The Python restatement and the real parsers meet on one file.
  R8 etl.profilegate learns exactly: track_type, smoothness and the three booleans in `encode`, and two NEW refusals - a
     comparison to a constant outside the named value's enum, and `==`/`!=` on a boolean value - since GraphHopper
     refuses both at load and a misspelt GRADE_3 must not read as "does not fire".
  R9 the five rows lose `divergent`; test_only_the_typed_classes_diverge keeps its name (bound in
     ops/lib/named-tests.json) and asserts ZERO divergent rows.
  R10 OUT OF TOUCHES, to stillOpen: services/api customModel.ts FORBIDDEN_ENCODED_VALUES is ["road_access", "surface"];
     the five new gate values are not in it (a request model cannot raise a priority-0 edge, so defence in depth only);
     pins/PINS.yaml P-PROD-01 prose still describes five divergent rows.
  R11 owner re-import (VPS, not run here): `docker build -t scenic-routing:t0381 services/routing` then
     `bash services/routing/import-graph.sh <tagged LA pbf> <graph dir> scenic-routing:t0381`; the graph's
     `properties` sha256 (import-graph.sh:36) changes because graph.encoded_values gains track_type, smoothness,
     gate_locked_barrier, gate_ford, gate_service_way.
- 2026-10-16T20:02:58Z RED FIRST, by name (fixture `divergent` records removed, profile and profilegate unchanged):
  `FAILED test_profile_gives_the_fixture_verdict[tracktype=grade3 on tertiary]`, `[barrier=gate+locked=yes]`,
  `[ford=yes]`, `[service=driveway]`, `[service=parking_aisle]`, `FAILED test_etl_and_profile_agree_on_every_gate`,
  `FAILED test_only_the_typed_classes_diverge` - `7 failed, 64 passed`. Then the code (commit 80399262):
  car_scenic_base.json gains five priority-0 clauses (track_type GRADE3-5; smoothness BAD..IMPASSABLE;
  gate_locked_barrier; gate_ford; gate_service_way); config.yml graph.encoded_values gains the five names;
  GateFacts + GateFactParser + three ScenicScoreImportRegistry branches; profilegate encodes the five and refuses a
  comparison outside DOMAINS.
  GREEN at 80399262:
  A1 `tests/test_gate_parity.py tests/test_profilegate.py` -> `215 passed in 1.25s`; test_only_the_typed_classes_diverge
     asserts `divergent == {}`.
  A2 `tests/test_profiles_static.py` -> `7 passed`. RED by name with gate_ford deleted from config.yml:
     `FAILED test_every_encoded_value_the_base_profile_reads_is_configured`, `FAILED test_the_t0381_gates_are_read_and_built`
     (`2 failed, 5 passed`), restored -> `7 passed`.
  A3 `python ops/mutate/profilegate.py` -> `MUTATIONS: 78 caught, 0 missed, 0 skipped, of 78`, `MUTATE OK
     caught=78/78 equivalent_caught=0` (MIN_MUTATIONS 53 -> 78; 25 new: 9 on the shipped profile incl. "ford read off
     road_environment" and "INTERMEDIATE smoothness gated", 16 on profilegate). `--prove-vacuity` -> `VACUITY: 0
     caught, 78 missed, 0 skipped, of 78`, `VACUITY PROVED`.
  A5 VERIFIED HERE, not only restated: `wsl docker build -t scenic-routing:t0381 services/routing` (mvn package runs
     the Java tests) -> `Tests run: 2, Failures: 0 ... in com.scenicdrive.routing.GateEncodingTest`, `Tests run: 32,
     Failures: 0`, `BUILD SUCCESS` over the 34-row gate_encoding.json that test_profilegate also passes. RED by name:
     GateFacts FORD `YES.equals` -> `YES.equalsIgnoreCase` -> `GateEncodingTest.everyRowEncodesExactlyItsTable:86
     {"highway":"unclassified","ford":"Yes"} ==> expected: <{gate_ford=false, ...}> but was: <{gate_ford=true, ...`,
     `BUILD FAILURE`; restored -> green. GraphHopper 11 ACCEPTS the config and profile: `bash
     services/routing/import-graph.sh .../services/etl/work/la/window-tagged-1.osm.pbf services/routing/work/graph-t0381
     scenic-routing:t0381` -> `accepted ways: 11,740`, `nodes: 21,137, edges: 24,057`, both profiles' CustomWeighting
     built in PrepareRoutingSubnetworks, `EXIT=0`. Graph change measured on the same window: `graph.em.bytes_for_flags`
     12 (scenic-routing:t0213, the shipped image) -> 13 (+1 byte per edge); properties sha256
     a1abefe12204b4c8c2a7ede48ae717e7ecd48594335f4295aa7280adece83a6f -> 08fdf1c929f6753c3e4ce62bf51088207a7595d80d58a5317005e2caec2e93d0
     (properties also carries the import date, so the hash differs on every import; the graph.encoded_values entries
     for track_type, smoothness and gate_* are what to look for).
  A6 `swift test --filter GateParityFixtureTests` -> `Test run with 3 tests in 1 suite passed`, EXIT=0 (Swift reads
     an absent `divergent` as nil).
  OWNER RE-IMPORT (R11, VPS): `docker build -t scenic-routing:t0381 services/routing` then `bash
  services/routing/import-graph.sh <tagged LA pbf> <graph dir> scenic-routing:t0381`; expect bytes_for_flags +1 and
  the five new entries in graph.encoded_values; the served router must run the new image (the old jar cannot build
  gate_* and refuses the config).
- 2026-10-16T20:10:33Z A7 gates BARE at 80399262, each its own exit: check-safety-disclaimer=0, check-mutate-population.py=0 ("P-PROC-06:
  every added module is covered or allowlisted; the floor of 169 holds"), check-mutate-only.py=0 ("MUTATE-ONLY OK: 230
  of 230"), check-line-cap=0 ("682 Swift files tracked ... none over 300 lines"), check-pins-yaml.py=0 ("pins=52
  fields=418"), check-exec-bits=0 ("235 files ... all modes correct"), queue-check=0 ("QUEUE OK (371 tasks)").
  Measured files: profilegate.py 288 lines, test_profilegate.py 224, test_gate_parity.py 157, test_profiles_static.py
  200, ops/mutate/profilegate.py under 300. `git fetch origin` (main checkout): origin/main 325c2cd3 == this branch's
  base, nothing to merge. STILL OPEN (R10): services/api FORBIDDEN_ENCODED_VALUES lacks the five new names;
  pins/PINS.yaml P-PROD-01 prose still says five rows diverge; the case-variant rows (tracktype=Grade3,
  smoothness=Bad) are gated by the profile only (fail-safe direction).
- 2026-10-16T20:52:48Z rv1 FAIL (agent/rv1-t-0381, head 7a4a7035) B1 closed by CLASS. RULING: GraphHopper 11's
  TrackType/Smoothness find is valueOf(toUpperCase(name)) with no trim, and GateFacts.tag, Gates.swift and
  assemble.gate_reason compare exactly, so a padded value is NOT the fact; no oracle row padded any of the five, so
  a trim on either reader survived. RED at 99e5c24d (two mutants added, floor 78 -> 80, no rows yet): `python
  ops/mutate/profilegate.py --only "a padded enum tag trimmed" --only "a padded ford value trimmed"` -> `MISSED a
  padded enum tag trimmed (exit 0)`, `MISSED a padded ford value trimmed (exit 0)`, `MUTATE FAILED caught=0/2`.
  FIX at 9af64946: gate_encoding.json +10 padded rows (tracktype ' grade3'/'grade3 ', smoothness ' bad'/'bad ', ford
  ' yes'/'yes ', locked 'yes ' with barrier=gate, barrier ' gate' with locked=yes, service ' driveway'/'driveway '),
  34 -> 44 in GateEncodingTest and test_the_plugin_table_is_whole; GATED_BY_T0381 derives a leading and a trailing
  padded not-gated row from every gating literal (every non-highway key of every want=True row, +30 rows). GREEN:
  same command -> `caught a padded enum tag trimmed <- tests/test_profilegate.py::test_encoding_matches_the_plugin_table`,
  `caught a padded ford value trimmed <- ...test_encoding_matches_the_plugin_table`, `MUTATE OK caught=2/2`;
  `--prove-vacuity` same names -> `VACUITY PROVED`. Touched tests: test_profilegate.py + test_gate_parity.py -> `255
  passed`. JAVA (values confirmed by GraphHopper, not restated): `wsl docker build -t scenic-routing:t0381
  services/routing` -> `Tests run: 2, Failures: 0 ... in com.scenicdrive.routing.GateEncodingTest`, `Tests run: 32,
  Failures: 0`, `BUILD SUCCESS` over the 44 rows (smoothness ' bad' -> OTHER, tracktype ' grade3' -> MISSING, every
  padded fact false). Java twin RED: GateFacts.tag `(String) value` -> `((String) value).trim()` ->
  `GateEncodingTest.everyRowEncodesExactlyItsTable:86 {"highway":"unclassified","ford":" yes"} ==> expected:
  <{gate_ford=false, ...}> but was: <{gate_ford=true, ...}>`, `BUILD FAILURE`; restored (git diff empty).
  FOLLOW-UP FILED: T-0382 (main 334b1891) - FORBIDDEN_ENCODED_VALUES gains track_type, smoothness, gate_*; ids
  checked on origin/main and every origin/task/* branch first. NOT DONE HERE: gate_parity.json carries no padded
  row (it also runs Swift Gates and assemble.gate_reason; T-0181 touches it in parallel).
- 2026-10-16T21:55:37Z rv2 FAIL (agent/rv2-t-0381) B1 closed by a GENERATED corpus, not a third spelling family.
  RULINGS: (1) the orchestrator's oracle "gated iff value == L exactly" holds for the GateFacts literals (Java
  .equals / Set.contains, untrimmed, case-sensitive); for tracktype and smoothness it is value.upper() == L.upper(),
  because GraphHopper 11's TrackType.find / Smoothness.find is valueOf(Helper.toUpperCase(name)) - Grade3, GRADE3
  and gRADE3 ARE the enum (Java confirms below), so their profile gate is right. (2) The literals are parsed, never
  typed: barrier/locked/ford/highway/service from GateFacts.java's String and Set.of constants, tracktype/smoothness
  from the shipped profile's zero-priority track_type/smoothness clauses, lower-cased. 16 literals over 7 keys,
  highway=service included (context service=drive-through). (3) The rv1 padded derivation in GATED_BY_T0381 is
  replaced by the corpus (its rows are a subset). RED at ca48616b (four mutants, floor 80 -> 84, no rows): `python
  ops/mutate/profilegate.py --only "a padded service highway trimmed" --only "a cased service highway folded" --only
  "a service list split on semicolons" --only "a cased barrier folded"` -> `MISSED a padded service highway trimmed
  (exit 0)`, `MISSED a cased service highway folded (exit 0)`, `MISSED a service list split on semicolons (exit 0)`,
  `MISSED a cased barrier folded (exit 0)`, `MUTATE FAILED caught=0/4`. FIX at bcde5481 (+da3408fa tab escape):
  services/etl/tests/gate_near_miss.py generates per literal L, upper, title, swapcase, every single deletion, each
  of space/tab/;/_/-/x/|/, inserted at every position, L;L, L;paved, paved;L, Lx, xL, L[:-1], LL and "" ->
  `gate_encoding.json: 1395 rows (44 hand, 1351 generated; corpus 1463 before de-duplication)`; GateEncodingTest
  and test_the_plugin_table_is_whole count 1395 and the test holds the file to the generator's output;
  test_the_corpus_has_every_family_for_every_literal checks every family for every literal, the literal sets
  against profilegate's, no variant equal to L but the identity, and the oracle above;
  test_the_shipped_profile_gates_no_near_miss runs all 1463 through pg.gated over the shipped json and pg.encode.
  GREEN: same command plus the rv1 four -> `caught a padded service highway trimmed <- tests/test_profilegate.py::
  test_encoding_matches_the_plugin_table[{"highway": ...`, `caught a cased service highway folded <- ...`, `caught a
  service list split on semicolons <- ...`, `caught a cased barrier folded <- ...`, `MUTATE OK caught=8/8`;
  `--prove-vacuity` on the four -> `VACUITY PROVED`. Touched tests: test_profilegate.py + test_gate_parity.py ->
  `1593 passed`. JAVA: `wsl docker build -t scenic-routing:t0381 services/routing` -> `Tests run: 2, Failures: 0
  ... in com.scenicdrive.routing.GateEncodingTest`, `Tests run: 32, Failures: 0`, `BUILD SUCCESS` over the 1395
  rows. Java twin RED: GateFacts SERVICE_WAY `tag(way, "highway")` -> `tag(way, "highway").trim()` ->
  `GateEncodingTest.everyRowEncodesExactlyItsTable:86 {"service":"drive-through","highway":" service"} ==>
  expected: <{... gate_service_way=false ...}> but was: <{... gate_service_way=true ...}>`, `BUILD FAILURE`; restored
  (git diff empty). P-PROD-01 why_no_test_catches_it gains a dated T-0381 sentence (pins/PINS.yaml added to
  touches). NOT DONE HERE: gate_parity.json and Swift Gates.swift are not run over the corpus (the parity fixture
  is T-0181's in parallel; ScenicKit is outside this task's touches).
- 2026-10-16T22:48:57Z agent/rv3-t-0381 REVIEW round 3 PASS (PR #273, HEAD 8ae0d0c7 == origin/task/T-0381). Corpus: services/etl/tests/gate_near_miss.py parses barrier/locked/ford/highway=service/4 service values from GateFacts.java and grade3-5 + 5 smoothness constants from the shipped car_scenic_base.json (16 literals, 7 keys, none skipped, highway=service included); every ruled family per literal; exact-equality oracle for the GateFacts keys, upper-cased valueOf for the two enums (ruled in this Log, Java-confirmed). Touched tests: services/etl test_profilegate.py + test_gate_parity.py 1593 passed; services/routing test_profiles_static.py 7 passed. rv2 mutants by name via ops/mutate/profilegate.py --only: a padded service highway trimmed, a cased service highway folded, a service list split on semicolons, a cased barrier folded -> each caught by test_encoding_matches_the_plugin_table, MUTATE OK caught=4/4 (floor 84). Own widenings (uncommitted probe, pycache purged + 1.1 s between runs, subject restored): W1 service startswith RED 48 failed (test_encoding_matches_the_plugin_table, test_the_shipped_profile_gates_no_near_miss); W2 ford re.match RED 12 failed (same two tests); W5 locked casefold RED 3 failed (same two tests). Recorded, non-blocking (outside the ruled families, not plausible slips): W3 highway unicodedata NFKC survived 1593 passed (no non-ASCII row; OSM tag values are ASCII); W4 enum raw.upper().replace("-", "_") survived 1593 passed (a substitution family; a deliberate normalization feature, not a refactor slip) - a follow-up could add a '-'/'_' substitution family. PINS.yaml P-PROD-01 change is append-only (dated T-0381 sentence). Gates bare in the review worktree: check-safety-disclaimer 0, check-mutate-population 0, check-mutate-only 0, check-line-cap 0, check-pins-yaml 0, check-exec-bits 0, queue-check 0 (QUEUE OK 373). gh pr checks 273: core pass, pins-source-only pass. git merge-base --is-ancestor origin/main origin/task/T-0381 -> 0 (main 14e1aab2). Java not re-run by the reviewer; the owner's quoted docker build (Tests run: 2 GateEncodingTest, BUILD SUCCESS over 1395 rows) stands. routing-profiles.lock released.
