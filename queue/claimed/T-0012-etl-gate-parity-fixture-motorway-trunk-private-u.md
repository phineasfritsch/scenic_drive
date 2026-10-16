---
id: T-0012
title: ETL gate parity fixture: motorway/trunk/private/unpaved score 0.0 across ETL, router profile and ScenicKit.Gates (P-PROD-01)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T10:26:10Z
lease_expires_at: 2026-10-17T10:26:10Z
worktree: .worktrees/T-0012
branch: task/T-0012
exclusive: [services/routing/profiles/car_scenic_base.json]
touches: [services/etl/, services/routing/profiles/, Sources/ScenicKit/Scoring/, Tests/ScenicKitTests/GateParityFixtureTests.swift, services/routing/tests/test_profiles_static.py, pins/PINS.yaml, ops/lib/named-tests.json, ops/lib/run-named-tests.py, ops/lib/mutate_population_table.py, ops/mutate/profilegate.py, queue/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0024]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The same gating rule is written three times, in three languages, by three different tasks:

- **the ETL**, which computes `scenic_score` per way and writes it into the corpus and the tagged PBF
- **the routing profile**, `services/routing/profiles/car_scenic_base.json`, whose `priority` block zeroes
  `road_access == PRIVATE|NO`, the unpaved surfaces, and `road_class == TRACK`
- **ScenicKit**, whose `Gates` are what the app reasons about when it explains a route

Three copies of one rule drift. When they do, nothing fails: the ETL scores a way 0.4, the profile lets it
through, the app says it is fine, and a sedan ends up on a gated dirt track. Every layer is internally
consistent and the product is wrong. That is what P-PROD-01 exists to catch, and it is currently `pending`.

**One fixture set, through all three.** Build a small table of ways — real OSM ways from the Bay Area extract,
by id, so nobody can hand-tune the input — covering at minimum:

    motorway, motorway_link, trunk, trunk_link          score 0.0, NOT gated (penalised, never excluded)
    surface=gravel|dirt|ground|sand|unpaved|compacted|fine_gravel   GATED
    highway=track, tracktype>=grade3                    GATED
    access=private|no|permit|destination                GATED
    motor_vehicle=no, barrier=gate + locked=yes, ford=yes          GATED
    highway=service + service=driveway|parking_aisle    GATED
    surface absent on primary/secondary/tertiary        treated as paved
    surface absent on unclassified/residential          x0.8 and flagged surface_unknown

and assert every layer returns the same verdict for every row. Not "each layer has tests" — one fixture, three
consumers, one expected answer per row.

**The distinction that must not be lost.** Motorway and trunk score 0 and are PENALISED; they are not gated.
Almost every Bay Area commute over 15 km needs freeway shoulders around a scenic middle, and a "tidy-up" that
promotes them from score-0 to excluded makes those routes unroutable rather than unattractive. T-0024's
`tagfilter.problems()` already guards the extract side of this; the fixture must guard the scoring side.
Hard gates are SAFETY ONLY, on positive evidence.

**Demonstrate red three ways, one per layer**, because a parity check that has only been seen red in one place
has only been tested in one place:

1. change a gate in the profile JSON → fixture fails
2. change the equivalent rule in the ETL → fixture fails
3. change `ScenicKit.Gates` → fixture fails

and each failure must name which layer disagreed with which, not just "mismatch".

**Then land the P-PROD-01 assertion**, replacing its `pending:`. `pins/PINS.yaml` currently carries three
pending pins; one of them is this. A pin that stays pending past the task that was supposed to make it real is
the debt `ops/check-pins` is built to refuse.

Depends on T-0024 for the extract the fixture ways are drawn from.

## Log
- 2026-09-18T18:53:49Z note from agent/claude-fable-5-1 (12:13 panel, grounded): services/routing/profiles/car_scenic_base.json stays this task's - it is in touches: here and P-PROD-01 is pending this task. The Worker half of the routing seam (the per-request custom model and its refusal) is split out as T-0158. Plan line 102 gates road_class TRACK in the base profile; P-PROD-01's statement (pins/PINS.yaml:117) names motorway/trunk/private/unpaved and omits track - carry it into the fixture, and into T-0149's split.
- 2026-10-16T10:26:10Z claimed by agent/claude-opus-5; lease until 2026-10-17T10:26:10Z
- 2026-10-16T10:38:02Z MEASURED on task/T-0012 at 96652610 (main + claim).
  M1 WHERE THE THREE LAYERS LIVE. ETL: `services/etl/etl/assemble.py` `gate_reason` (four branches: unpaved
  surface, highway=track, `accessrule.access_refused` = access in {private,no,permit,destination} or
  motor_vehicle=no), applied in `assemble.scored_row` (gated -> score 0.0, then `CLASS_SCORE_CEILING`
  residential/living_street 0.6499, service 0.0), which `assemble.assemble` maps every way through; the class
  zero and the x0.8 are `score.score` (`SCENIC_ZERO_CLASSES`, `UNSURVEYED_MULTIPLIER`). PROFILE:
  `services/routing/profiles/car_scenic_base.json` `priority`: `!car_access`, `road_access == PRIVATE ||
  road_access == NO`, the seven unpaved surfaces, `road_class == TRACK`, each `multiply_by: "0"`.
  SCENICKIT: `Sources/ScenicKit/Gates/Gates.swift` (not under Scoring/ as touches: said) - `Gates.decide`, NINE
  refusal branches; the zero class and the x0.8 are `Sources/ScenicKit/Scoring/SegmentScore.swift`
  (`dullClasses`, `unsurveyedClasses`, `score(for:)`, `raisesSurfaceUnknownFlag`).
  M2 HOW EACH IS EVALUATED ON ONE TAG ROW. ETL and ScenicKit: their shipping functions take a tag dict. The
  profile: nothing in the tree evaluates it (test_profiles_static.py greps the strings) - a GraphHopper-11
  encoding (pom.xml pins 11.0) plus an `if`-expression evaluator is new code, read over the SHIPPED json.
  M3 REAL WAYS. No Bay Area extract is on this box (memory: LA is the first graph). Committed fixtures (git
  ls-files services Tests, *.json/*.osm/*.osm.xml) hold 123 tagged ways, most synthetic ids. T-0206's LA canyon
  window (services/etl/work/la/window-doc.json, gitignored, bbox -118.95,33.98,-118.55,34.15) holds 11740 ways:
  motorway 48, motorway_link 73, trunk 251, trunk_link 13; surface gravel 6, dirt 23, ground 1, sand 0, unpaved
  39, compacted 1, fine_gravel 0; highway=track 988; tracktype grade3-5 on a non-track 0; access private 4863,
  no 73, permit 3, destination 22; motor_vehicle=no 64; barrier=gate+locked=yes on a WAY 0; ford=yes 1;
  service driveway 3427, parking_aisle 1139; no-surface primary 90, secondary 171, tertiary 263, unclassified
  63, residential 1382. ISOLATED (no gate fires but the class's own, so a deleted clause shows on that row
  alone): ground, sand, compacted, fine_gravel, tracktype-on-tertiary, locked barrier and ford have 0 - those 7
  rows are synthetic tag sets and say so in `source`; the other 23 are the lowest isolated way id, all tags.
  M4 DRIFT TODAY over the window, ETL `gate_reason` vs the profile under M2's encoding: 52 of 11740 disagree -
  22 access=destination (ETL gates, profile does not), 29 motor_vehicle=private and 1 motor_vehicle=permit
  (profile gates, ETL does not). With `|| road_access == DESTINATION` added: 30, the 22 gone, none new.
- 2026-10-16T10:38:02Z RULINGS (author rule, before code):
  R1 Brief "every layer returns the same verdict for every row" over NINE refusal classes vs reality: the ETL
  ports four of `Gates.verdict`'s branches by T-0146 R5 (test_assemble_wiring counts them) and T-0188
  (backlog) owns the port of the other five; the profile CANNOT express tracktype on a non-track, a locked
  barrier, a ford or a service value (no such encoded value in config.yml; adding one is config.yml + a graph
  re-import, serial-only and not this task). CLAUDE.md's hard gates are three. So the fixture carries those
  Brief classes (tracktype=grade3 on tertiary, barrier=gate+locked=yes, ford=yes, service=driveway,
  service=parking_aisle) with verdict GATED - ScenicKit's - and a `divergent` record of the ETL's and the
  profile's answer TODAY; each layer is held to that record, so T-0188 landing turns the row red until the
  record is deleted. A meta-test refuses a divergent row outside that typed set of five and any core class.
  R2 access=destination: the profile is brought into line (`road_access == DESTINATION` added, exclusive:
  declared) - M4 measured 22 fixed and 0 new. NOT deployed: the live GraphHopper picks it up on restart.
  R3 access=permit: GraphHopper's OSMRoadAccessParser maps `permit` to PRIVATE (restated in profilegate, not
  verifiable on this box - no GraphHopper jar here). If that is wrong the profile lets permit through; recorded.
  R4 car_access is held TRUE in the evaluator: the parity is over the clauses this repository writes, and
  modelling GraphHopper's own car-access parser would hide a deleted `road_access` clause. Fail closed.
  R5 Residual drift (M4: 30 ways, motor_vehicle=private|permit, the profile STRICTER - fail-safe) is outside the
  Brief's rows and is recorded, not fixed: GraphHopper folds motor_vehicle into road_access and the ETL/Swift
  rule refuses only motor_vehicle=no on purpose (accessrule.py). Still open.
  R6 Verdict vocabulary: GATED / ZERO_NOT_GATED / PAVED / UNKNOWN_X08. The profile answers only GATED or
  NOT_GATED (priority 0 or not); the three score verdicts are compared between the ETL (`assemble.scored_row`)
  and ScenicKit (`SegmentScore.score(for:)` + `raisesSurfaceUnknownFlag`), each against the same row with a
  paved surface. The cross-language join is the fixture: pytest holds the ETL and the profile to each row,
  `GateParityFixtureTests` holds ScenicKit to the same row, and each failure names the layer and what the
  others answer. No Sources/ change is needed, so no digest is re-approved.
  R7 P-PROD-01's statement says motorway/trunk/private/unpaved "score exactly 0.0" in all three; gated is not
  score 0 and the profile has no score. The statement is restated to what is asserted (gate verdicts in three
  layers, score verdicts in two, motorway/trunk score 0 and NOT gated in all three) and adds track.
  R8 run-named-tests.py binds vitest and swift only; it gains a `pytest` runner (junit xml, same MISSING /
  SKIPPED / FAILED verdicts) so P-PROD-01 binds its pytest names by NAME. touches: widened accordingly.
  R9 profilegate.py is a new evaluator module: ops/mutate/profilegate.py ships its population (subject the
  module AND the shipped profile json) with a literal floor.

## Acceptance
1. `cd services/etl && python -m pytest -q tests/test_gate_parity.py tests/test_profilegate.py` all pass;
   gate_parity.json has 30 rows, 23 real LA way ids, 7 synthetic, 5 divergent (R1's set).
2. `swift test --scratch-path .build/t0012 --filter GateParityFixtureTests` all pass.
3. `python ops/lib/run-named-tests.py P-PROD-01` prints `NAMED P-PROD-01 passed=N/N` (pytest + swift names).
4. RED three ways, each quoted with its message naming the layer: (a) the DESTINATION clause removed from
   car_scenic_base.json -> pytest names the profile against ETL and ScenicKit; (b) `access_refused` narrowed
   in the ETL -> pytest names the ETL; (c) a `Gates.swift` branch removed -> GateParityFixtureTests names
   ScenicKit. Each restored, `git status` clean.
5. `python ops/mutate/profilegate.py` -> `MUTATE OK caught=N/N`, N == MIN_MUTATIONS; `--prove-vacuity` PROVED.
6. pins/PINS.yaml P-PROD-01 has no `pending:`, assertion `run-named-tests.py P-PROD-01`;
   `bash ops/check-pins --source-only` exit 0.
7. Gates exit 0 on the merged head: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py,
   check-line-cap, check-pins-yaml.py, check-exec-bits, check-pins --source-only, queue-check.

## Log (work)
- 2026-10-16T11:01:47Z fixture built by `.build/t0012-measure/build_fixture.py` (gitignored, outside the
  tree's history; reads services/etl/work/la/window-doc.json): 30 rows, isolated counts per class e.g. motorway
  48, trunk_link 13, surface=dirt 12, highway=track 427, access=permit 1, access=destination 17,
  motor_vehicle=no 8, service=driveway 606, no-surface residential 1606; 7 synthetic (M3).
- 2026-10-16T11:01:47Z RED three ways (driver `.build/t0012-measure/red.py`; mutate one file, run, restore,
  sha256 of the restored file == HEAD's blob each time):
  (a) car_scenic_base.json without ` || road_access == DESTINATION` -> pytest exit 1, 2 failed / 63 passed:
  `access=destination (way 23014646): PROFILE (car_scenic_base.json) says NOT_GATED, expected GATED; ETL
  (assemble.scored_row) says GATED, ScenicKit (the fixture) says GATED` and `the ETL and the profile disagree:
  access=destination (way 23014646): ETL says GATED, profile says NOT_GATED`. This is also the state of main
  before this branch's profile edit - the drift M4 measured, now seen by the test.
  (b) accessrule.py CLOSED_ACCESS without "destination" -> pytest exit 1, 2 failed / 63 passed:
  `access=destination (way 23014646): ETL (assemble.scored_row) says ZERO_NOT_GATED, expected GATED; profile
  (car_scenic_base.json) says GATED, ScenicKit (the fixture) says GATED`.
  (c) Gates.swift without `if tags["highway"] == "track" { return .refused(.track) }` -> swift test exit 1:
  `highway=track (way 10715427): ScenicKit (Gates.decide + SegmentScore) says PAVED, expected GATED; the ETL
  is held to GATED and the profile (car_scenic_base.json) to GATED for this row by test_gate_parity.py`.
- 2026-10-16T11:01:47Z GREEN: pytest test_gate_parity.py + test_profilegate.py 65 + 53 passed; swift
  GateParityFixtureTests 2/2; `run-named-tests.py P-PROD-01` -> `NAMED P-PROD-01 passed=118/118` (before the
  two refusal rows were added; re-run at the final commit below).
- 2026-10-16T11:01:35Z acquired lock(s) services/routing/profiles/car_scenic_base.json for agent/claude-opus-5
- 2026-10-16T11:54:29Z ACCEPTANCE re-run on the merged head 6b75ca2a (origin/main fbeb99b8 merged; still its tip at 2026-10-16T11:54:29Z):
  1. pytest test_gate_parity.py + test_profilegate.py: 65 + 56 passed; fixture 30 rows, 23 real, 7 synthetic,
     5 divergent (R1's set).
  2. swift GateParityFixtureTests 2/2 passed (run inside 3).
  3. `run-named-tests.py P-PROD-01` -> `NAMED P-PROD-01 passed=123/123` (121 pytest + 2 swift).
  4. RED three ways: quoted above (a) profile, (b) ETL, (c) ScenicKit, each naming its layer.
  5. `python ops/mutate/profilegate.py` -> `MUTATE OK  caught=43/43 equivalent_caught=0` (first run 42/43:
     `an unknown encoded value reads false` MISSED; three refusal rows added, re-run caught by
     `test_an_unreadable_expression_refuses['!max_speed']`); `--prove-vacuity` -> `VACUITY PROVED` (0/43 caught).
  6. P-PROD-01 has no pending:; CI on PR #262 core `PINS ok=49 skipped=0 pending=2 expired=0 failed=0 tier=linux`
     (pending 3 -> 2), pins-source-only `PINS ok=22 skipped=28 pending=1 expired=0 failed=0 tier=linux source-only`.
  7. Gates, bare, on the merged head: check-safety-disclaimer 0, check-mutate-population.py 0 (`floor of 166
     holds`), check-mutate-only.py 0, check-line-cap 0, check-pins-yaml.py 0 (`pins=51`), check-exec-bits 0,
     queue-check `QUEUE OK (368 tasks)`. Local `ops/check-pins --source-only` did not finish within 40 min on
     this box (swift contention); CI's pins-source-only job on the same head passed (quoted in 6).
  Line counts: profilegate.py 188, test_gate_parity.py 156, test_profilegate.py 117, GateParityFixtureTests.swift
  91, ops/mutate/profilegate.py 153, run-named-tests.py 199.
- 2026-10-16T12:41:53Z rv1 B1 ruled: reviewer is right - `gated()` read only `priority`, and GraphHopper never routes an
  edge of speed 0, so a `speed` exclusion of motorway/trunk was invisible (rv1 quoted 121 + 39 passed with it). Same
  class in services/routing/tests/test_profiles_static.py (read `priority` only) - fixed there too; that path added
  to `touches:`. Fix by class: profilegate reads the WHOLE model (`model()`, `speed_excludes()`): a firing speed
  rule with limit_to 0 / multiply_by 0 is GATED; a top-level key outside speed/priority/distance_influence, a
  distance_influence that is not a number >= 0, a speed rule other than `if` + one value, a speed value that is
  neither a number >= 0 nor `car_average_speed` all refuse.
  RED on the old evaluator (fe24a897, mutants committed first): `python ops/mutate/profilegate.py --only speed
  --only "top-level key"` -> `MISSED profile: motorway and trunk speed limited to 0 (exit 0)`, `MISSED profile:
  motorway and trunk speed multiplied by 0 (exit 0)`, `MISSED profile: a top-level key the evaluator cannot read
  (exit 0)`; the six evaluator mutants SKIP (their anchors are the fix). `MUTATE FAILED caught=0/9`.
  GREEN (b930bcc6): the same run plus `distance_influence`, `a low priority read as gated`, `any rule shape read`
  -> `MUTATE OK caught=12/12 equivalent_caught=0`; `--prove-vacuity` on the 10 new -> `VACUITY PROVED` (0/10).
  Driver `.build/t0012-rv1-red.py` (profile mutated, run, restored, sha256 equal): limit_to and multiply_by each
  -> etl `7 failed, 126 passed` naming `test_profile_gives_the_fixture_verdict[motorway]`, `[motorway_link]`,
  `[trunk]`, `[trunk_link]`, `test_etl_and_profile_agree_on_every_gate`,
  `test_motorway_and_trunk_score_zero_and_are_routable_in_every_layer`; routing `1 failed, 4 passed` naming
  `test_no_profile_hard_excludes_motorway_or_trunk`. Unmutated: etl 133 passed, routing 39 passed 3 skipped;
  `run-named-tests.py P-PROD-01` -> `NAMED P-PROD-01 passed=135/135` (133 pytest + 2 swift; 12 names added).
  MIN_MUTATIONS 43 -> 53. P-PROD-01 why_no_test_catches_it appended (dated text untouched). Line counts:
  profilegate.py 236, test_profilegate.py 159, test_profiles_static.py 165, ops/mutate/profilegate.py 172.
- 2026-10-16T15:01:02Z agent/claude-opus-5 (orchestrator): rv2 FAIL was ancestry only (T-0377's P-PRIV-05 lines, then T-0371/T-0183). Merged origin/main twice; the second merge conflicted only in ops/lib/mutate_population_table.py DRIVERS (union: curated.py from main + profilegate.py from this branch). On the merged head: test_gate_parity + test_profilegate 133 passed, services/routing 39 passed 3 skipped; bare gates all exit 0 (check-safety-disclaimer, check-mutate-population, check-mutate-only, check-telemetry-emit-sites, check-store-links, check-ios-compile-guardrails, ios_screenshot_pinned, check-line-cap, check-pins-yaml, check-exec-bits, queue-check).
