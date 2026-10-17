---
id: T-0385
title: ops/plan's body gate (ScenicPlanCLI GraphHopperRouteSource.forbiddenEncodedValues) still lists only road_access and surface - bind it to the shipped base profile like the Worker
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T01:56:02Z
lease_expires_at: 2026-10-18T01:56:02Z
worktree: .worktrees/T-0385
branch: task/T-0385
exclusive: []
touches: [Sources/ScenicPlanCLI/, Tests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/mutate/]
pins_affected: [P-SAFE-01]
reviewer: null
depends_on: [T-0382]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 GraphHopperRouteSource.forbiddenEncodedValues equals, as an ordered array by full equality, the identifiers read by the `if` of every `multiply_by: \"0\"` priority clause of the SHIPPED services/routing/profiles/car_scenic_base.json (read by path from the repo root by the test, never restated), in profile order, minus the identifiers LambdaCustomModel.json(for:) reads at every lambda tenth 0...80 (the CLI's only model builder; ruled R2); that subtracted overlap equals exactly [road_class] by full equality - measured today: [car_access, road_access, surface, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way]"
  - "A2 per derived name, a GENERATED corpus (exact, case variants, every single-char deletion, separators space/tab/;/_/-/,/|/x at every position, prefix/suffix, compounds, the name under every GraphHopper operator shape, empty) is placed in every clause shape (priority if, priority else_if, speed if, speed else_if, areas feature property, object key), embedded by body(_:_:profile:model:) and sent through GraphHopperRouteSource.send(_:) - the one function fastest() and scenic() reach the socket through - at the `post` seam; oracle (over the profile-derived list, never the constant): throws PlanFailure.modelTouchesSafetyGate(<first derived name the lowered model text contains>) iff one occurs, else the transport receives the body unchanged by full equality; one array equality per name; a meta row proves every family exists for every name and that the model-free body mentions none"
  - "A3 RED first by name: on the pre-change constant the A1 derivation test and the six new names' A2 rows fail (quoted in the Log), then green; PlanCLIRequestBodyTests stays green (scenic() at every lambda tenth and fastest() still reach the transport past the wider gate)"
  - "A4 ops/mutate/plan.py gains the gate's mutants (a name dropped from each end of the list, case-sensitive comparison, only the first name checked), MIN_MUTATIONS 47 -> 51, the new test in TEST_FILES/SUITES; `python ops/mutate/plan.py --only cli/gate-` 4/4 caught"
  - "A5 digest row for Sources/ScenicPlanCLI/GraphHopperRouteSource.swift re-approved; bare gates exit 0: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check; the new test file and GraphHopperRouteSource.swift stay <= 300 lines (wc -l quoted)"
---
## Brief

T-0382 (PR #276) bound the Worker's FORBIDDEN_ENCODED_VALUES to the shipped car_scenic_base.json by full
equality: the identifiers of every multiply_by-0 clause minus the builder's own (road_class), which is eight names
(car_access, road_access, surface, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way).
Its author recorded the Swift copy left behind: Sources/ScenicPlanCLI/GraphHopperRouteSource.swift
`forbiddenEncodedValues = ["road_access", "surface"]`, the plan CLI's body gate, which still lacks six of them.

Bind the Swift list the same way. A Linux test reads the SHIPPED profile JSON, derives the list and asserts
equality, and the overlap with the CLI builder's identifiers must equal exactly what the builder reads. Drive a
generated near-miss corpus per name (memory generated-near-miss-corpus) through the CLI's shipping body gate:
refused iff the name occurs, forwarded unchanged otherwise. Show red before the list changes and green after.
Re-approve the digest row, and add mutation population entries if the gate is a numeric/decision module.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0382 stillOpen 1.
- 2026-10-17T01:56:02Z claimed by agent/claude-opus-5; lease until 2026-10-18T01:56:02Z
- 2026-10-17T02:00:49Z measured before ruling. car_scenic_base.json priority has nine `multiply_by: "0"`
  clauses, every one keyed `if`; their lower-case identifiers in order: car_access, road_access, surface,
  road_class, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way. The CLI's one model
  builder is LambdaCustomModel.json(for:) (no areas: the CLI sends no closures); its conditions are
  `minorCondition` (road_class, scenic_score) and `scenic_score >= n` bands, so it reads {road_class,
  scenic_score}; overlap = [road_class]. The gate is `refuseSafetyGates(in:)`, called first in `send(_:)`;
  fastest() and scenic() both reach the socket only through `send`. The constant today is
  `["road_access", "surface"]` - six names short. The non-model body text (points, "car_scenic"/"car_fast",
  details scenic_score/road_class/osm_way_id) contains none of the eight.
- 2026-10-17T02:00:49Z rulings, before code:
  R1 the Swift list becomes the eight derived names in profile order, the same order as the Worker's
     FORBIDDEN_ENCODED_VALUES; the substring, case-insensitive rule of refuseSafetyGates is unchanged.
  R2 "the builder" is LambdaCustomModel.json(for:) over every lambda tenth 0...80 (the bisection's bracket,
     LambdaSearch.maxLambda = 8); the Brief's "what the builder reads" is asserted as overlap == [road_class].
  R3 the shipping gate driven is GraphHopperRouteSource.send(_:) through the `post` seam (the same seam
     PlanCLIRequestBodyTests uses); scenic() cannot carry a corpus model, and both entry points pass through
     send first. The oracle reads the profile-derived list, never the constant under test.
  R4 no Package.swift change: the test reads the profile by #filePath from the repo root, like the existing
     PlanCLI tests read their fixtures.
  R5 GraphHopperRouteSource.swift is already a SUBJECT of ops/mutate/plan.py, so the gate's decisions get
     mutants there (not a new population); MIN_MUTATIONS rises by the count added.
  R6 P-SAFE-01's statement and its named-test row are Worker-only and pins/ + ops/lib/named-tests.json are
     outside touches: not edited here, recorded as still open.
  R7 the doc comments of GraphHopperRouteSource that say "the same two" are corrected in the same edit.
- 2026-10-17T02:23:34Z A3 RED, on the pre-change constant `["road_access", "surface"]`, new test file only
  (`swift test --filter PlanCLIGateValuesTests`, exit 1, "Test run with 3 tests in 1 suite failed ... with 7 issues"):
  the derivation test failed `(GraphHopperRouteSource.forbiddenEncodedValues -> ["road_access", "surface"]) ==
  (gates.filter { !builder.contains($0) } ...)`; send's corpus rows failed for exactly the six new names -
  car_access 222 of 720 rows differ, track_type 228 of 720, smoothness 222 of 720, gate_locked_barrier 222 of
  1206, gate_ford 222 of 666, gate_service_way 222 of 1044; road_access and surface rows and the corpus meta
  test passed. After the eight-name list (and the digest row re-approved,
  5fe37906b0e6cbcdcf478c47cecfd1d947ebcd585c88d537c546332567200133):
  `--filter "PlanCLIGateValuesTests|PlanCLIRequestBodyTests"` exit 0, "Test run with 9 tests in 2 suites passed".
