---
id: T-0188
title: ETL gate port - the unported Gates.verdict refusals (tracktype, smoothness, locked barrier, ford=yes, service values) into assemble.gate_reason with fixture rows and the enumeration pinned against Gates.swift
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T15:39:20Z
lease_expires_at: 2026-10-17T15:39:20Z
worktree: .worktrees/T-0188
branch: task/T-0188
exclusive: []
touches: [services/etl/etl/assemble.py, services/etl/tests/, ops/mutate/scenic_tags_mutations.py, ops/mutate/extractadapter.py, Tests/ScenicKitTests/GateParityFixtureTests.swift, queue/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0146]
verify: [ops/test, ops/check-pins]
acceptance:
  - "assemble.gate_reason refuses every rule Gates.verdict refuses (Sources/ScenicKit/Gates/Gates.swift): tracktype >= grade3, smoothness worse than intermediate, barrier=gate+locked=yes, ford=yes, highway=service with a driveway/parking_aisle service value, in addition to the three already ported; one fixture row per rule, each RED BY NAME before the rule exists; the rule COUNT and the reason names pinned against Gates.swift / GateReason.swift by a test that parses the Swift (the existing _swift_set pattern), red when either side gains a rule"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From rv1-pr102's review (RECORDABLE, T-0146 Log) via the 21:13 panel (grounded): ruling R5 ported three of the
plan's gates into the assembly and deliberately not five more; the "five" count was itself wrong at that head.
The corpus the device reads (T-0185) must honour the same gates ScenicKit does (P-PROD-01 gate parity), so the
port lands before the first corpus write; the routing profile's gates (T-0031's car_scenic_base) are the
router's own and are not this task.

## Log
- 2026-09-19T03:29:43Z filed by agent/claude-fable-5-1 from the 21:13 panel's grounded synthesis. Not started; after #102 merges.
- 2026-10-16T15:39:20Z claimed by agent/claude-opus-5; lease until 2026-10-17T15:39:20Z
- 2026-10-16T15:43:19Z MEASURED (before code). M1 GATES.SWIFT, read in the code: `Gates.verdict` has NINE
  `return .refused(` branches in this order - unpaved surface, highway=track, tracktype in refusedTracktypes
  {grade3,grade4,grade5}, smoothness in refusedSmoothness {bad,very_bad,horrible,very_horrible,impassable},
  access in closedAccess, motor_vehicle=no, barrier in refusableBarriers {gate} AND locked=yes, ford=yes,
  highway=service AND service in refusedServiceValues {driveway,parking_aisle,drive-through,emergency_access}.
  GateReason.swift has SEVEN cases: unpavedSurface, track, tooRough, noAccess, lockedBarrier, ford, serviceWay.
  `assemble.gate_reason` ports four branches (three reasons); test_assemble_wiring counts 4 + 5 unported.
  M2 LA CANYON WINDOW (services/etl/work/la/window-doc.json, main checkout, 11740 ways; script
  services/etl/work/t0188_measure.py, gitignored), each rule spelled from Gates.swift in its order vs today's
  `assemble.gate_reason`: `ways=11740 old_gated=5589 new_gated=7317`;
  `track(tracktype>=grade3) fires=42 first=0 newly_gated=0`; `too_rough fires=6 first=0 newly_gated=0`;
  `locked_barrier fires=0`; `ford fires=1 first=0 newly_gated=0`;
  `service_way fires=4667 first=1728 newly_gated=1728 isolated=1728`; `newly gated total=1728`.
  Near-misses present: tracktype on a non-track {grade2: 1} (on tracks grade3 32, grade2 22, grade1 9, grade4
  6, grade5 4); smoothness {good 5, bad 3, very_bad 2, horrible 1}; ford {yes 1}; no `locked` and no `barrier`
  tag on any way; highway=service by service {driveway 3427, none 2137, parking_aisle 1139, drive-through 53,
  emergency_access 48, alley 13, slipway 1}; service=driveway on highway=residential 1 and on highway=track 1.
  So on real data ONLY the service rule moves a verdict (1728 ways, all already 0.0 by T-0207's service class
  ceiling - the score does not move, `gate_reason`/`scenic_gate` and the `gated` count do); the other four are
  either absent or already gated by an earlier rule here, which is why their rows are synthetic.
- 2026-10-16T15:43:19Z RULINGS (author rule, before code):
  R1 Brief/acceptance "a driveway/parking_aisle service value" vs Gates.swift's FOUR refusedServiceValues:
  the Swift wins (P-PROD-01 is parity with it) - drive-through (53) and emergency_access (48) are ported too.
  R2 CLAUDE.md "Hard gates are safety only: unpaved, private/no access, track" vs Gates.verdict's nine: the ETL
  ports what ScenicKit already refuses; a corpus less strict than the device's gate is the drift P-PROD-01
  forbids. Motorway/trunk stay ungated (no rule here reads them; the parity motorway test stays).
  R3 Reason names: the snake_case of GateReason's cases - too_rough, locked_barrier, ford, service_way - and the
  tracktype rule returns `track`, as Swift returns `.track` for both. GATE_REASONS becomes the seven in
  GateReason.swift's order, pinned by parsing GateReason.swift.
  R4 Order is behaviour (GatesOrderTests): the ETL tries the nine in Gates.verdict's order. Pinned by an
  ordered-pairs table whose expected reason per witness is read from Gates.swift's `return .refused(.x)` lines.
  R5 The pin "red when either side gains a rule": count `return .refused(` in Gates.swift code lines (9) and
  the ETL's rules (gate_reason's `return GATE_` lines, with the `access_refused` call counted as its two
  clauses) and assert equal, plus a witness table of exactly that many rows. RED shown by a temporary
  uncommitted extra branch on each side.
  R6 Fixture: the five divergent records drop their `etl` key (the ETL answers GATED); the record stays typed
  for the profile gap (car_scenic_base.json has no track_type/barrier/ford/service encoded value - out of
  scope). test_only_the_typed_classes_diverge asserts no `etl` key. GateParityFixtureTests.swift reads
  `divergent?["etl"] ?? verdict`, so it needs no edit; Sources/ is untouched (no digest row).
  R7 300-line cap: assemble.py is 293; its docstring's "NINE ... FOUR ported, FIVE deliberately absent"
  paragraph is now false and is cut to make room. test_assemble.py is 299, so the new tables live in a new
  tests/test_gate_port.py; test_assemble_wiring's unported-count test is deleted (its count moves there, 9/0).
  R8 Touches widened: the mutation population (ops/mutate/scenic_tags_mutations.py, which already holds
  assemble.py as a subject; floor 48 raised by the new entries, test_gate_port.py and test_gate_parity.py
  added to EMPTIED) and ops/mutate/extractadapter.py, whose GATE_ORDER anchor spells today's four-rule body
  verbatim and would SKIP (fail) once two rules sit inside it - re-anchored on the first line only.
  ACCEPTANCE:
  A1 test_gate_port.py RED BY NAME on this commit's code, then green: every refusal value read from the Swift
     sets gates with the Swift reason; near-misses ungated (tracktype grade1/grade2, smoothness intermediate/
     good, barrier=gate with locked=no/absent, barrier=bollard+locked=yes, ford=no/absent, highway=service
     with service alley/slipway/absent, service=driveway on highway=residential); ordered pairs; the count pin.
  A2 test_gate_parity.py: the five divergent rows answer GATED in the ETL with no `etl` key; 30 rows pass.
  A3 python ops/mutate/scenic_tags.py -> `MUTATE OK caught=N/N`, N = 48 + the new entries, floor = N.
  A4 python services/etl/work/t0188_measure.py on the final head -> `old_gated=7317 new_gated=7317` and
     `newly gated total=0` (the shipped gate_reason gates exactly what the Swift-spelled rules gate).
  A5 cd services/etl && python -m pytest tests -rs -p no:cacheprovider -o addopts= -> count line, 0 skipped.
  A6 swift test --filter GateParityFixtureTests green on the edited fixture.
  A7 bare gates exit 0: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-line-cap,
     check-pins-yaml, check-exec-bits, queue-check.
- 2026-10-16T15:59:13Z RED FIRST, on 73cafb11's assemble.py with the new tests on disk (A1, A2):
  `pytest tests/test_gate_port.py` -> `13 failed, 20 passed`: FAILED test_the_etl_has_exactly_the_swift_rule_count,
  test_the_reason_names_are_gate_reasons_cases, test_each_rule_refuses_with_the_swift_reason[2] [3] [6] [7] [8],
  test_the_sets_are_the_swift_literals, test_every_value_of_every_swift_set_is_refused[refusedTracktypes]
  [refusedSmoothness] [refusableBarriers] [refusedServiceValues], test_every_ordered_pair_answers_the_earlier_swift_rule
  (the 20 that passed: 14 near-misses, witnesses 0 1 4 5, unpavedSurfaces and closedAccess - the four ported).
  `pytest tests/test_gate_parity.py` (no `etl` key) -> `5 failed, 60 passed`: FAILED test_etl_gives_the_fixture_verdict
  [tracktype=grade3 on tertiary] [barrier=gate+locked=yes] [ford=yes] [service=driveway] [service=parking_aisle].
  GREEN after the port: gate_port + gate_parity + assemble + assemble_wiring -> `120 passed`; whole ETL suite
  `pytest tests -rs` -> `1906 passed in 110.03s`, no skip line. assemble.py 299 lines, test_gate_port.py 162,
  scenic_tags_mutations.py 300, extractadapter.py (ops/mutate) 294.
  THE COUNT PIN SEEN RED (services/etl/work/t0188_red.py, uncommitted edit then restored byte-for-byte):
  `RED[Swift gains a branch] exit=1` FAILED test_the_etl_has_exactly_the_swift_rule_count,
  test_each_rule_refuses_with_the_swift_reason[8]; `RED[GateReason gains a case] exit=1` FAILED
  test_the_reason_names_are_gate_reasons_cases; `RED[the ETL gains a rule] exit=1` FAILED
  test_the_etl_has_exactly_the_swift_rule_count; restored -> `34 passed`.
  A4 on the ported tree: `ways=11740 old_gated=7317 new_gated=7317`, `newly gated total=0`.
- 2026-10-16T16:33:04Z ACCEPTANCE RE-RUN on f536aac6 (git fetch origin + merge origin/main: already up to date,
  so the tested tree is the pushed one):
  A1/A2 green as quoted above (`120 passed` over the four gate files; test_gate_port alone `34 passed`).
  A3 `python ops/mutate/scenic_tags.py` -> `MUTATIONS: 71 caught, 0 missed, 0 skipped, of 71`,
     `EQUIVALENT: 0 caught, 3 missed`, `MUTATE OK  caught=71/71 equivalent_caught=0`, exit=0; every T-0188 entry
     caught by test_gate_port.py (near-miss rows killed the locked/ford/any-highway loosenings). The
     re-anchored driver: `python ops/mutate/extractadapter.py` -> `MUTATE OK  caught=27/27 equivalent_caught=0`.
  A4 `old_gated=7317 new_gated=7317`, `newly gated total=0`.
  A5 `cd services/etl && python -m pytest tests -rs -p no:cacheprovider -o addopts=` -> `1906 passed in 110.03s`,
     no skip line.
  A6 `swift test --filter GateParityFixtureTests` -> `Test run with 2 tests in 1 suite passed`.
  A7 bare, each exit=0: check-safety-disclaimer; check-mutate-population (`the floor of 168 holds`);
     check-mutate-only (`NAME-PAIRS OK`); check-line-cap (`none over 300 lines`); check-pins-yaml (`pins=51`);
     check-exec-bits (`all modes correct`); queue-check (`QUEUE OK (368 tasks)`).
  STILL OPEN: the routing profile half of the five divergent rows (no track_type/barrier/ford/service encoded
  value in config.yml) - typed in the fixture, not this task's scope, not yet filed.
- 2026-10-16T17:56:16Z rv1 FAIL (agent/rv1-t-0188, head bc0fb172) B1/B2 - ruled before code: both findings stand.
  Gates.swift's verdict compares ford and locked to the ONE literal "yes" (`tags["ford"] == "yes"`,
  `tags["locked"] == "yes"`); the near-miss table held one spelling per key (ford=no, locked=no), a blacklist, so
  `ford not in (None, "no")` and `locked in (YES, "true", "1")` survived (reviewer: 1906 passed each). Fixed by
  CLASS in test_gate_port.py: `swift_equalities()` parses every `tags["k"] == "v"` of `Gates.verdict`'s body
  (comment lines dropped; fails closed when the body's `==` count differs from what it read or any `!=`
  appears) -> five conjuncts: highway==track, motor_vehicle==no, locked==yes, ford==yes, highway==service.
  Each is tried over VALUE_SPACE (yes/no/true/false/1/0/unknown/stepping_stones/boat/permissive/private/
  designated/residential/"") plus its literal, on a way satisfying the branch's other conjuncts; expected refused
  with the branch's reason iff value == the PARSED literal (`refused_under(value, literal)`); meta-tests: every
  parsed conjunct has a way that puts the value under the parsed key, and no row's expectation survives a
  change of literal. Measured the LA canyon window (services/etl/work/la/window-doc.json, 11740 ways): ford
  occurs once (=yes), no way carries locked or barrier; motor_vehicle no=64 private=68 yes=12 permissive=4
  permit=1. So gate_parity.json gains two SYNTHETIC rows, ford=stepping_stones and barrier=gate+locked=true
  (tertiary, asphalt, verdict PAVED, no divergent: the profile cannot see either key); fixture 30 -> 32 rows in
  test_gate_parity.py and GateParityFixtureTests.swift (touches: gains that file), which gains the named test
  "a ford or a lock spelled other than yes is not gated by ScenicKit". scenic_tags_mutations.py gains both
  mutants, MIN_MUTATIONS 71 -> 73 (docstring condensed to hold the 300-line cap: 300).
  RED (each mutant applied by hand to assemble.py, __pycache__ purged, 1.1 s sleep, `python -m pytest tests`):
    B1 -> `FAILED tests/test_gate_parity.py::test_etl_gives_the_fixture_verdict[ford=stepping_stones]`,
       `FAILED tests/test_gate_parity.py::test_etl_and_profile_agree_on_every_gate`,
       `FAILED tests/test_gate_port.py::test_each_equality_conjunct_refuses_its_swift_literal_and_no_other_value[ford==yes]`,
       `3 failed, 1914 passed`.
    B2 -> `FAILED ...test_etl_gives_the_fixture_verdict[barrier=gate+locked=true]`, `FAILED
       ...test_etl_and_profile_agree_on_every_gate`, `FAILED ...test_each_equality_conjunct_refuses_its_swift_
       literal_and_no_other_value[locked==yes]`, `3 failed, 1914 passed`.
    meta (refused_under made to ignore the literal: `value == "yes"`) -> `FAILED
       tests/test_gate_port.py::test_no_equality_row_ignores_the_parsed_literal` plus the highway==track,
       motor_vehicle==no and highway==service rows, `4 failed, 37 passed`.
  GREEN (pristine): `python -m pytest tests` -> `1917 passed in 83.30s`; `swift test --filter
    GateParityFixtureTests` -> `Test run with 3 tests in 1 suite passed` (new test passed by name).
- 2026-10-16T18:11:09Z rv1 fix re-run on the merged head (84bd3cb0 + git fetch origin, merge origin/main -> 0e38b16b,
  clean; main brought landmarks.py and ScenicKit Plan/ changes):
  `cd services/etl && python -m pytest tests -rs` -> `2002 passed in 72.83s`, no skip line.
  `swift test --filter GateParityFixtureTests` -> `Test run with 3 tests in 1 suite passed`.
  Gates bare, each exit=0: check-safety-disclaimer; check-mutate-population (`the floor of 169 holds`);
  check-mutate-only (`NAME-PAIRS OK`); check-line-cap (`none over 300 lines`); check-pins-yaml (`pins=51`);
  check-exec-bits (`all modes correct`); queue-check (`QUEUE OK (369 tasks)`). scenic_tags_mutations.py
  `wc -l` 300. Mutants re-run: only the two touched (B1, B2), by hand as quoted above - both caught; the full
  73-mutant driver was not re-run (faster-verification rule).
- 2026-10-16T18:45:58Z rv2 B3 (agent/rv2-t-0188 on 77c649eb): `if (tags.get("ford") or "").lower() == YES:`
  survived the whole ETL suite. Ruling: Gates.swift:169 is `tags["ford"] == "yes"` and ConsideredTags does
  not normalise, so ScenicKit routes ford=Yes/YES/" yes"; the ETL must too. The hole is the CLASS - VALUE_SPACE
  held no case or padding spelling of any parsed literal - so it covers all five conjuncts (ford, locked,
  motor_vehicle, highway==track, highway==service). Fix: test_gate_port.py `literal_variants(literal)` derives
  `{literal.upper(), literal.capitalize(), " "+literal, literal+" ", "\t"+literal+"\n"}` from EACH parsed
  literal into `equality_rows` (expected refused iff value == literal exactly); the meta test asserts five
  variants, none the literal, all rows, each `.strip().lower()` back to the literal. gate_parity.json gains
  synthetic row `ford=Yes` (highway=tertiary, surface=asphalt) as a NEAR_MISS PAVED class: 32 -> 33 rows in
  test_gate_parity.py and GateParityFixtureTests.swift, whose near-miss test now filters three rows.
  scenic_tags_mutations.py gains the casefold and strip mutants, MIN_MUTATIONS 73 -> 75 (docstring condensed,
  `wc -l` 300). test_gate_port.py `wc -l` 240, test_gate_parity.py 159, GateParityFixtureTests.swift 102.
  RED on the rv2 head's tests (both mutants by hand, __pycache__ purged, 1.1 s sleep, whole suite
  `python -m pytest`, driver .build/t-0188-drv/two_mutants.py):
    `casefold the ford value: MISSED  [2002 passed in 82.62s (0:01:22)]`
    `strip the ford value: MISSED  [2002 passed in 75.43s (0:01:15)]`
  GREEN on the fixed tests (same driver over tests/test_gate_port.py tests/test_gate_parity.py):
    `casefold the ford value: CAUGHT  [3 failed, 109 passed in 0.89s]` -
      `tests/test_gate_parity.py::test_etl_and_profile_agree_on_every_gate`,
      `tests/test_gate_parity.py::test_etl_gives_the_fixture_verdict[ford=Yes]`,
      `tests/test_gate_port.py::test_each_equality_conjunct_refuses_its_swift_literal_and_no_other_value[ford==yes]`
    `strip the ford value: CAUGHT  [1 failed, 111 passed in 1.51s]` -
      `tests/test_gate_port.py::test_each_equality_conjunct_refuses_its_swift_literal_and_no_other_value[ford==yes]`
  Pristine: test_gate_port.py + test_gate_parity.py `112 passed in 0.70s`; `swift test --filter
  GateParityFixtureTests` -> `Test run with 3 tests in 1 suite passed` (ford=Yes row PAVED through
  Gates.decide in everyRowGetsTheFixtureVerdict and fordAndLockOtherThanYesAreNotGated). Only the two new
  mutants were re-run (faster-verification rule); the 75-mutant driver was not.
