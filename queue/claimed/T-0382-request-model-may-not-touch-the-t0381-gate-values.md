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
