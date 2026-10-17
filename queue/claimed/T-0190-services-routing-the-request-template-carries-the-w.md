---
id: T-0190
title: services/routing - the request template carries the Worker's full clause set (the RESIDENTIAL anti-rat-run clause, plan line 108) and the five scenic_lambda_bands.json rows are asserted equal to customModel.ts's scenicBandMultipliers at MULTIPLIER_DECIMALS - red when either side moves
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T01:07:01Z
lease_expires_at: 2026-10-18T01:07:01Z
worktree: .worktrees/T-0190
branch: task/T-0190
exclusive: [routing-profiles]
touches: [services/routing/, services/api/test/customModelGolden.test.ts, Tests/Fixtures/custom-model/]
pins_affected: []
reviewer: null
depends_on: [T-0209]
verify: [ops/test, ops/check-pins]
acceptance:
  - "(1) ONE RECORD. Tests/Fixtures/custom-model/lambda-<l>.json for l in {0, 1, 2, 2.5, 4, 7.75, 8} is the only copy of the per-request model outside the Worker: services/api/test/customModelGolden.test.ts asserts every file BYTE-EQUAL to JSON.stringify(buildCustomModel(l, null), null, 2) + newline through the shipped builder, and the recorded file set EQUAL to exactly those seven lambdas (whole-set equality, so a file added or deleted is red too). The Worker is the source of truth; the fixture is the oracle record. RED BY NAME first, each run through vitest and quoted: (a) MULTIPLIER_DECIMALS 6 -> 4 in customModel.ts; (b) the MINOR_CONDITION clause dropped from buildCustomModel; (c) the second clause of lambda-4.json written `if` instead of `else_if`; (d) lambda-2.json deleted - then green."
  - "(2) NO HAND COPY LEFT. services/routing/profiles/car_scenic_request.json and services/routing/profiles/scenic_lambda_bands.json are deleted; test_lambda_monotone.py, test_route_details.py and measure_runs.py write the recorded lambda-<l>.json files into the models directory as-is (no placeholder substitution) through one helper, services/routing/tests/request_models.py; `git grep -n -E 'car_scenic_request|scenic_lambda_bands' -- services Tests Sources` prints nothing."
  - "(3) THE ORACLE'S VIEW. services/routing/tests/test_request_models_static.py (split from test_profiles_static.py for the 300-line cap; ruled 2026-10-17T01:27:05Z) reads the recorded models for the oracle lambdas {0, 1, 2, 4, 8} and asserts, each red by name first then green: the clause chain by KEY is one if, then else_if only, then one else - its length read off the record, not typed (a typed x7 would be a second copy of BAND_LADDER) - (the old _condition() read `if` and `else_if` alike, so a band written `if` passed - (c) above must be red here too); every multiplier is \"1\" at lambda 0 and none grows with lambda clause by clause; no condition names MOTORWAY or TRUNK; every identifier a model reads is in config.yml graph.encoded_values; no model reads an encoded value the base profile's zero gates read, other than road_class."
  - "(4) P-SAFE-01's JSON half. test_profiles_static.py compares car_scenic_base.json's priority list WHOLE to a typed literal of its nine zero clauses - RED BY NAME with `priority: []` (and with the TRACK clause dropped), then green."
  - "(5) ROUTED VERMONT RUN - UNVERIFIED IN THIS TASK, recorded as such: no GraphHopper run (workflow instruction; no graph in the worktree). The models now routed differ from the old template (9 clauses not 3, distance_influence 0 not the base's 30, slopes (7-s)/7 not 0/0.5/1), so the five T(lambda) durations and test_lambda_penalty_bites's measured +43% WILL move; the re-measure is named in stillOpen as its own task."
  - "(6) COUNTS AT THE FINAL COMMIT: services/routing pytest count line; the vitest count line for customModelGolden.test.ts; bash ops/check-pins --source-only, bash ops/queue-check and the bare gates, run on the merged head."
---
## Brief

From the 22:13 panel (CODE lens, grounded; the band-source-of-truth ruling). The Worker's buildCustomModel is the
only code that ever sends the per-request scenic penalty (config.yml loads car_scenic_base.json alone); the routing
JSONs have no runtime consumer - `git grep scenic_lambda_bands -- services/api` is empty. The five band rows agree
with customModel.ts to the digit, but by hand, at five points, with nothing cross-checking them; and the Vermont
oracle (plan lines 89, 225) exercises a three-clause template while production sends four - the RESIDENTIAL
anti-rat-run demotion has never met a real graph. Filed as its own task rather than widened into PR #105's round-2
fix (PROCESS ruling 6: no new blocking class on a fix pass in flight). Lands after #105 merges; T-0182 (the owner's
LA drive from the CLI) should run over the model production sends.

## Log
- 2026-09-19T04:34:10Z filed by agent/claude-fable-5-1 from the 22:13 panel's grounded synthesis. Not started; after #105 merges.
- 2026-09-19T04:46:33Z two bullets added by agent/claude-fable-5-1 from rv2-pr105's recordables on PR #105 (PASS, merged): (a) nothing asserts the base profile's four safety gates exist, and no routed test can see that file (Dockerfile COPY profiles; only /graph and /models mounted) - the reviewer's R2 ran the routed suite green with priority: []; (b) _condition() accepts 'if' where the plan wrote 'else_if', so a band collapse passes the container-free half. Both belong with the clause-set cross-check this task already owns.
- 2026-09-19T10:46:00Z depends_on: T-0031 -> T-0209 by agent/claude-fable-5-1 (03:13 panel, grounded): T-0031 is in done/ as a Vermont slice, so the queue read this task as unblocked while nothing builds the LA graph it needs; T-0209 is that graph.
- 2026-10-17T01:07:01Z claimed by agent/claude-opus-5; lease until 2026-10-18T01:07:01Z
- 2026-10-17T01:14:25Z MEASURED by agent/claude-opus-5 before any code (worktree at 45285278, main).
  WHAT THE WORKER SENDS. services/api/src/customModel.ts buildCustomModel(lambda, null) (299 lines - at the cap, so
  this task does not edit it): distance_influence 0 and NINE clauses - `if` MINOR_CONDITION
  "(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class == SERVICE) && scenic_score < 7" at
  1/(1+2*lambda) (T-0244's anti-rat-run clause, now FIRST and three classes wide, not plan :108's RESIDENTIAL-only
  0.5), then `else_if scenic_score >= s` for s = 7,6,5,4,3,2,1 at 1/(1+((7-s)/7)*lambda), then `else` at
  1/(1+lambda); with closures a tenth clause `if in_closure_1 || ...` -> "0" plus `areas`. Multipliers are
  Number(x.toFixed(MULTIPLIER_DECIMALS=6)).toString(). T-0382's refusals: FORBIDDEN_ENCODED_VALUES = car_access,
  road_access, surface, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way.
  Recorded at the oracle lambdas with node v26.3.0 (`node .build/t0190/emit.mts <l>`, the T-0244 emitter):
    l=0  9 clauses  ['1','1','1','1','1','1','1','1','1']
    l=1  9 clauses  ['0.333333','1','0.875','0.777778','0.7','0.636364','0.583333','0.538462','0.5']
    l=2  9 clauses  ['0.2','1','0.777778','0.636364','0.538462','0.466667','0.411765','0.368421','0.333333']
    l=4  9 clauses  ['0.111111','1','0.636364','0.466667','0.368421','0.304348','0.259259','0.225806','0.2']
    l=8  9 clauses  ['0.058824','1','0.466667','0.304348','0.225806','0.179487','0.148936','0.127273','0.111111']
  WHAT THE ROUTING SIDE HOLDS. profiles/car_scenic_request.json: THREE clauses (if >=7 ${high}, else_if >=4 ${mid},
  else ${low}), no distance_influence (so GraphHopper keeps the base's 30). profiles/scenic_lambda_bands.json: the
  pre-T-0244 three-band table high 1 / mid 1/(1+0.5l) / low 1/(1+l). Both are stale against the Worker in clause
  count, thresholds, slopes and distance_influence; they agree with nothing production sends. Consumers:
  test_lambda_monotone.py (_write_request_models, test_band_multipliers_match_the_plan), test_route_details.py
  (_lambda_model), measure_runs.py (write_models), test_profiles_static.py (EXPECTED_BANDS / EXPECTED_THRESHOLDS
  typed by hand, test_request_model_bands_are_the_plan_thresholds, test_band_table_matches_the_plan_literals,
  test_band_multipliers_never_grow_with_lambda), README.md row; ops/mutate/profilegate.py names
  car_scenic_request.json as a mutant's replacement path (the "request profile read instead" mutant).
  Tests/Fixtures/custom-model/lambda-{0,1,2.5,7.75,8}.json (T-0182/T-0244 golden): all five reproduced by the
  emitter today with cmp silent. Its consumer is Swift only (LambdaCustomModelParityTests, explicit list of five);
  PROVENANCE.txt itself records that NOTHING re-runs the TypeScript against it. HAND COMPARISONS found: the
  routing EXPECTED_BANDS literal, test_band_multipliers_match_the_plan's formula, customModelMinorClause.test.ts's
  typed formulas, customModel.test.ts's grid - none ties the routing oracle's inputs to the builder's output.
  CI: ops/test runs services/etl pytest and the api vitest; services/routing pytest runs NOWHERE in CI (grep of
  ops/test and .github/workflows for routing/pytest). Baseline routing pytest: 41 passed, 3 skipped in 52.36s.
  The base profile (car_scenic_base.json) has NINE zero clauses since T-0381, not the four this task was filed on.
- 2026-10-17T01:14:25Z RULINGS by agent/claude-opus-5 (owner), before code:
  R1 Source of truth is the shipped builder, recorded once. Not acceptance (1) as filed (a Python test scraping
     buildCustomModel's TS source): that guards a spelling, not the output (memories full-equality-oracle,
     source-guards-fail-closed), and the identifier it names, scenicBandMultipliers, no longer exists. Instead the
     existing golden directory becomes THE record, a vitest compares every file WHOLE (bytes) to the builder, and
     the routing tests consume those bytes. ops/test runs the vitest, so CI carries the check the routing pytest
     cannot.
  R2 Acceptance (2) as filed (bands 1/(1+0.5l), 1/(1+l)) is ruled OBSOLETE: T-0244 replaced the three-band model;
     the Worker no longer has a 0.5 slope. The template and the band table are DELETED rather than updated -
     updating them would be a fourth hand copy. The MULTIPLIER_DECIMALS mutant survives as (1a).
  R3 Plan :108's 'road_class == RESIDENTIAL && scenic_score < 7 -> 0.5' is superseded by T-0244's MINOR_CONDITION
     at 1/(1+2l); the Worker wins, the oracle routes what the Worker sends.
  R4 Two new golden files (lambda-2, lambda-4) are added; no existing golden byte changes (cmp above). This is not
     a snapshot re-record (CLAUDE.md): the five existing files are untouched and the vitest proves all seven
     against the builder, so none is trusted on provenance. The Swift parity list stays at its five (T-0218 is in
     flight on ScenicKit; not widened here).
  R5 Acceptance (3) (routed Vermont run) is UNVERIFIED in this task by instruction: no GraphHopper run. The
     models change materially (R2/R3, distance_influence 30 -> 0), so the durations and BITE_FLOOR's measured +43%
     are stale until re-measured; named in stillOpen.
  R6 Acceptance (4) four gates -> the base's NINE clauses, compared whole. The ETL profilegate population already
     kills per-gate deletions on the ETL side; this pins the routing side the same way, by whole equality.
  R7 Acceptance (5) (_condition if/else_if): the chain is asserted by KEY, so a band written `if` is red here and
     in the vitest.
  R8 ops/mutate/profilegate.py's "request profile read instead" mutant will now point at a missing file (killed
     by FileNotFoundError, not by a gate test). Out of this task's touches; named in stillOpen, not widened.
  R9 depends_on T-0209 (LA graph) is in queue/done. Not needed for this container-free task.
  Acceptance rewritten to (1)-(6) above; the filed bullets are superseded by R1-R7.
- 2026-10-17T01:27:05Z RED BY NAME, then green, by agent/claude-opus-5 (driver .build/t0190/mutants.py: one mutant
  applied, `npx vitest run test/customModelGolden.test.ts` and `pytest tests/test_profiles_static.py
  tests/test_request_models_static.py` run, file restored; __pycache__ purged and 1.1 s python-sleep per run):
    (1a) MULTIPLIER_DECIMALS 6 -> 4 in customModel.ts: vitest exit=1, 6 failed | 2 passed (8) - lambda-1, -2, -2.5,
         -4, -7.75, -8 "is byte-equal to buildCustomModel(l, null)"; pytest 10 passed (it reads records, by design).
    (1b) MINOR_CONDITION clause line dropped from buildCustomModel: vitest exit=1, 7 failed | 1 passed (8) - every
         lambda-<l>.json byte-equality; pytest 10 passed (by design).
    (1c)=(3) lambda-4.json second clause written `if`: vitest 1 failed (lambda-4.json is byte-equal...); pytest
         2 failed - test_the_clause_chain_is_one_if_then_else_ifs_then_one_else,
         test_no_clause_multiplier_grows_with_lambda.
    (1d) lambda-2.json deleted: vitest 2 failed - "records exactly the seven lambdas the Swift port and the routing
         oracle read", lambda-2.json byte-equality; pytest 5 failed (recorded() refuses the missing lambda).
    (4)  base `priority: []`: vitest 8 passed; pytest 3 failed - test_base_profile_priority_is_the_nine_safety_gates,
         test_the_t0381_gates_are_read_and_built, test_every_value_a_model_reads_is_built_and_none_is_a_gate_value.
    (4)  base TRACK clause dropped: pytest 1 failed - test_base_profile_priority_is_the_nine_safety_gates.
    (3)  lambda-8 dullest band 0.111111 -> 0.6: vitest 1 failed; pytest test_no_clause_multiplier_grows_with_lambda.
    (3)  lambda-0 minor clause + `&& road_access == YES`: vitest 1 failed; pytest
         test_every_value_a_model_reads_is_built_and_none_is_a_gate_value (+ the shared-shape check).
    (3)  lambda-2 threshold 3 -> 6 (dead band): vitest 1 failed; pytest test_the_band_thresholds_strictly_descend.
    RESTORED: vitest exit=0 8 passed (8); pytest exit=0 10 passed. Full routing suite: 43 passed, 3 skipped
    (baseline 41 passed, 3 skipped: -4 template/band tests deleted with their files, +1 base pin, +5 record checks).
  Also rewired, no assertion change: test_route_details.py / test_route_details_fixture.py (lambda-0, -8) and
  measure_runs.py route the record through request_models.write_models. Tests/Fixtures/custom-model/PROVENANCE.txt
  appended (no earlier line edited).
- 2026-10-17T01:55:02Z FINAL PRE-REVIEW by agent/claude-opus-5. `git fetch origin` (main checkout): origin/main 45285278,
  `git merge origin/main` on task/T-0190: Already up to date. Acceptance re-run on that head (dcbbb2a5 + this Log):
    (1) `npx vitest run test/customModelGolden.test.ts`: Test Files 1 passed (1), Tests 8 passed (8). Red by name
        for (1a)-(1d): the 01:27:05Z entry. Wider vitest (customModelGolden, customModel, customModelMinorClause,
        customModelGate, customModelGateValues, asnRootPin): Test Files 6 passed (6), Tests 77 passed (77).
    (2) `git grep -n -E 'car_scenic_request|scenic_lambda_bands' -- services Tests Sources`: nothing (exit 1). The one
        hit left in the repo is ops/mutate/profilegate.py:88 (R8, outside touches, stillOpen).
    (3)+(4) routing pytest: 43 passed, 3 skipped in 45.50s. Red by name: the 01:27:05Z entry.
    (5) UNVERIFIED: no GraphHopper run (R5).
    (6) bare gates: check-safety-disclaimer exit 0; check-mutate-population exit 0 (0 added by this branch);
        check-mutate-only exit 0; check-pins-yaml exit 0 (pins=52); check-exec-bits exit 0; queue-check QUEUE OK
        (375 tasks). check-line-cap: `timeout 600` exit 124 on the loaded box - CI core is relied on; the largest
        file this branch touches is 182 lines (measure_runs.py), the new ones 123 (test_request_models_static.py) / 36 (request_models.py) / 41 (customModelGolden.test.ts), measured with wc -l. `bash ops/check-pins
        --source-only`: `timeout 900` exit 143 with no output on this box - CI is relied on for it.
- 2026-10-17T03:18:16Z agent/claude-opus-5 (orchestrator): rv1 FAIL was ancestry only (T-0218 landed). Merged origin/main (clean). On the merged head: customModelGolden vitest 8 passed; routing test_request_models_static + test_profiles_static 10 passed; bare gates exit 0 (check-safety-disclaimer, check-mutate-population, check-mutate-only, check-pins-yaml, check-exec-bits, queue-check).
- 2026-10-17T03:34:50Z agent/claude-opus-5 (orchestrator): rv2 FAIL was ancestry only (T-0384 merged during its CI wait; apps/ios + check-safety-disclaimer tables, no overlap). Merged origin/main again (clean); check-safety-disclaimer, check-mutate-population, check-pins-yaml, queue-check exit 0 on the merged head.
