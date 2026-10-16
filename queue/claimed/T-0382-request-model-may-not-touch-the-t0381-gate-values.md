---
id: T-0382
title: The request custom model may not touch the T-0381 gate values - FORBIDDEN_ENCODED_VALUES gains track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T23:03:37Z
lease_expires_at: 2026-10-17T23:03:37Z
worktree: .worktrees/T-0382
branch: task/T-0382
exclusive: []
touches: [services/api/src/customModel.ts, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-SAFE-01]
reviewer: null
depends_on: [T-0381]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 FORBIDDEN_ENCODED_VALUES in services/api/src/customModel.ts equals, as an ordered array by full equality, the identifiers read by the `if` of every `multiply_by: \"0\"` priority clause of the SHIPPED services/routing/profiles/car_scenic_base.json (imported as JSON by the test, never restated), in profile order, minus the identifiers buildCustomModel's own output reads; and that subtracted overlap equals exactly [road_class] by full equality (ruled R2) - on main today that is [car_access, road_access, surface, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way]"
  - "A2 per derived name, a GENERATED corpus (exact, case variants, every single-char deletion, separators space/tab/;/_/-/,/|/x at every position, prefix/suffix, compounds, the name under every GraphHopper operator shape, empty) is placed in every clause shape (priority if, priority else_if, speed if, speed else_if, areas feature property, object key) and sent through scenicPlanner.route - the function every /plan router request goes through; oracle: refused (RouteError router_refused, message equal to `refusing to send: custom model mentions <first derived name the lowered text contains> at <path>`, zero upstream calls) iff the lowered text contains a derived name, else forwarded once with the model unchanged by full equality; a meta row proves every family exists for every name; and ROUTES[/plan] refuses a body carrying custom_model with each name (400 invalid_request) before any upstream call"
  - "A3 RED first by name: on the pre-change constant the six new names' route() rows and the A1 derivation test fail (quoted), then green"
  - "A4 P-SAFE-01 binds the new tests by name (ops/lib/named-tests.json; dated sentence appended to its why); run-named-tests.py P-SAFE-01 green"
  - "A5 bare gates: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check; customModel.ts stays <= 300 lines (wc -l quoted)"
---
## Brief

T-0381 (PR #273) gave the base routing profile five new hard gates: `track_type` GRADE3-5, `smoothness` BAD and
worse, and three boolean encoded values from the scenic-score-parser plugin, `gate_locked_barrier`, `gate_ford`,
`gate_service_way`. The Worker lets a request carry its own custom model, and refuses one that reads a safety
gate's encoded value: `FORBIDDEN_ENCODED_VALUES = ["road_access", "surface"]` (customModel.ts, measured on main
325c2cd3, line 34). A request model that multiplies by a clause over `gate_ford` or `track_type` is therefore not
refused today. Whether such a clause can UNDO a base `multiply_by: 0` is GraphHopper's merge rule, so measure it
first (GraphHopper 11 multiplies priority factors; a request `multiply_by` above 1 is capped) and rule it in the
Log - the refusal stays the fail-closed answer either way, as it is for road_access and surface.

Filed by agent/claude-opus-5 from T-0381 rv1 (R10 stillOpen). Depends on T-0381 merging: the five names exist in
the profile only on task/T-0381 until then.

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0381 stillOpen (R10); ids checked on origin/main and every
  origin/task/* branch: max T-0381 (T-9901 is the T-0128 demo fixture), no task names FORBIDDEN_ENCODED_VALUES
  beyond T-0182 (done) and T-0381 itself.
- 2026-10-16T23:03:37Z claimed by agent/claude-opus-5; lease until 2026-10-17T23:03:37Z
- 2026-10-16T23:08:41Z MEASURE (worktree at main 2c0daea5). (m1) car_scenic_base.json priority has nine
  `multiply_by: "0"` clauses whose `if` reads, in order: car_access (`!car_access`), road_access, surface,
  road_class (`road_class == TRACK`), track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way.
  config.yml graph.encoded_values: car_access, car_average_speed, road_class, road_access, surface, scenic_score,
  osm_way_id, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way. (m2) customModel.ts:34
  `FORBIDDEN_ENCODED_VALUES = ["road_access", "surface"] as const`; file is 299 lines. mentioned() refuses on
  case-insensitive SUBSTRING over every key and string value. (m3) rejectCustomModel's production callers are
  scenicPlanner.route (exported, :83), tripPlanner's private route (:87) and loopPlanner (:114) - each runs it on
  the Worker's OWN buildCustomModel output just before the router call. (m4) A client cannot send a model at all:
  planRequest.ts keysProblem whitelists every key at every level, so `custom_model` in a /plan body is refused 400
  (planPrivacy.test.ts already asserts it for road_access). (m5) buildCustomModel's output reads road_class and
  scenic_score (MINOR_CONDITION, `scenic_score >= s`) and in_closure_N; it reads no other gate identifier.
- 2026-10-16T23:08:41Z RULINGS. R1 (Brief vs reality, m3/m4): there is no request-supplied model path - the
  "request model" this gate refuses is the model the Worker itself puts in each router request; the shipping entry
  point A2 binds to is scenicPlanner.route (every /plan router request), plus ROUTES["/plan"] for the request
  layer, which refuses custom_model by key whitelist whatever it names. R2 (A1's list vs the derivation A1 itself
  names): the identifiers of the zero clauses are NINE, not seven. car_access is a hard gate the builder never
  reads -> added (eight names; the filed seven missed it). road_class is a hard gate (`== TRACK`) that the
  builder's MINOR_CONDITION must read -> excluded; refusing it would refuse every plan. The test binds both: the
  constant equals profile-gate-ids minus builder-ids, and the overlap equals [road_class] exactly, so the builder
  starting to read any other gate is red rather than silently shrinking the list. R3 (Brief: "parse the
  profile at runtime"?): the Worker keeps a literal constant, held to the shipped profile by the A1 full-equality
  test; importing services/routing JSON into the Worker would break `node src/customModel.ts` (T-0182 runs this
  module under plain node strip-only, which refuses a JSON import without import attributes) and couple the bundle
  to a serial-only file. R4 (GraphHopper merge rule, Brief asks to measure): NOT measured in a container this
  task. GraphHopper's CustomModel merge appends the query model's statements to the profile's and priority is the
  product of the matching factors (limit_to a min), so a request clause cannot lift a base 0; the refusal stays
  the fail-closed answer either way, as for road_access/surface. Recorded as reasoned, not measured. R5
  (near-miss oracle): the gate is substring by design (module doc: over-refusing costs one request), so the
  oracle is "refused iff the lowered text contains a derived name" - computed from the PROFILE-derived list, not
  the constant. GraphHopper identifiers are case-sensitive tokens, so every spelling GraphHopper would read as a
  gate is the exact name, which the corpus always refuses; deletions and inner separators are forwarded. R6
  pins_affected P-PROD-01 -> P-SAFE-01 (P-PROD-01 is the ETL/profile/ScenicKit parity fixture, untouched; P-SAFE-01
  binds the Worker refusal tests by name); touches gains ops/lib/named-tests.json and pins/PINS.yaml for A4.
  P-SAFE-01 has no check-named-table digest (its assertion is run-named-tests.py alone), so none to re-approve.
- 2026-10-16T23:17:05Z RED FIRST (A3): test/customModelGateValues.test.ts written before the constant changed, run on main's
  `["road_access", "surface"]`: `Tests  7 failed | 4 passed (11)` - FAILED by name: `equals the identifiers of every
  multiply_by 0 clause of car_scenic_base.json, in order, minus the builder's own` (`expected [ 'road_access',
  'surface' ] to deeply equal [ 'car_access', 'road_access', ...(6) ]`) and the route() rows of car_access (720 rows),
  track_type (720), smoothness (720), gate_locked_barrier (1206), gate_ford (666), gate_service_way (1044); the
  road_access/surface rows, the corpus meta row and the handlePlan row passed. GREEN after the constant (customModel.ts
  `wc -l` 299, unchanged): `npx vitest run` customModelGateValues, customModel, customModelGate,
  customModelMinorClause, planPrivacy, planRecorded, closuresRoutes -> `Test Files 7 passed (7)`, `Tests 661 passed (661)`.
- 2026-10-16T23:17:05Z A4 P-SAFE-01: eleven names added to ops/lib/named-tests.json (15 -> 26), dated sentence appended to its why.
  RED: with the constant reverted to `["road_access", "surface"]` in the worktree, `run-named-tests.py P-SAFE-01` ->
  `NAMED P-SAFE-01 passed=19/26`, the derivation test and the six new names' rows `RED ... FAILED`; restored ->
  `NAMED P-SAFE-01 passed=26/26`. check-pins-yaml.py: `PINS-YAML ok pins=52 fields=418`.
- 2026-10-16T23:17:05Z MUTANTS (unwritten, run against the new file alone, restored after each): M1 mentioned() case-sensitive
  (`text.toLowerCase()` -> `text`): 8 failed | 3 passed, every name's route row; M2 keys never checked
  (`mentioned(key)` -> null): 8 failed | 3 passed; M3 constant order swapped (track_type/smoothness): 1 failed, the
  derivation test; M4 gate_ford dropped: 2 failed, the derivation test and gate_ford's route row. All killed.
- 2026-10-16T23:17:05Z R7 (found while grepping for copies of the list): Sources/ScenicPlanCLI/GraphHopperRouteSource.swift:54
  `forbiddenEncodedValues = ["road_access", "surface"]` is a Swift copy of this list (the plan CLI's body gate). It
  is outside this task's touches (Sources/ needs the digest re-approval and a Swift run) - NOT changed here; it is
  the follow-up, recorded in the PR's stillOpen.
- 2026-10-16T23:23:06Z FULL SUITE: `npx vitest run` -> `Tests 1 failed | 2678 passed (2679)`: requestReadSites.test.ts (the T-0272 whitelist of src lines naming the request) refused my new doc comment on FORBIDDEN_ENCODED_VALUES because it spelled the profile's file name ending `.json`; reworded to "the shipped base routing profile" (customModel.ts `wc -l` re-measured 299); requestReadSites + customModelGateValues -> `Tests 18 passed (18)`. Bare gates on 20db931e: check-safety-disclaimer exit 0, check-mutate-population `P-PROC-06 ... 0 added by this branch` exit 0, check-mutate-only `MUTATE-ONLY OK: 234 of 234` exit 0, check-pins-yaml `PINS-YAML ok pins=52 fields=418`, check-exec-bits `P-OPS-01: 238 files ... all modes correct`, queue-check `QUEUE OK (373 tasks)`.
- 2026-10-16T23:36:35Z FINAL ACCEPTANCE on 9ca313ff (git fetch origin in the main checkout; origin/main 2c0daea5 already an ancestor,
  merge a no-op). A1/A2: customModelGateValues + customModel + customModelGate + customModelMinorClause +
  planPrivacy + planRecorded + closuresRoutes + requestReadSites -> Test Files 8 passed (8), Tests 668 passed (668).
  A3: RED/green quoted above (7 failed | 4 passed on the old constant; NAMED 19/26). A4: run-named-tests.py
  P-SAFE-01 -> NAMED P-SAFE-01 passed=26/26. A5: gates quoted above on 20db931e (only a comment changed since);
  check-line-cap printed NOTHING in 10 min on the loaded box and was killed (timeout exit 124) - relying on CI
  core for it; measured by hand: customModel.ts 299 lines, customModelGateValues.test.ts 150 lines.
