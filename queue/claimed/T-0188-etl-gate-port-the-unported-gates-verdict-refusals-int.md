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
touches: [services/etl/etl/assemble.py, services/etl/tests/, ops/mutate/scenic_tags_mutations.py, ops/mutate/extractadapter.py, queue/]
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
