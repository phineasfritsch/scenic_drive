---
id: T-0146
title: the ETL emits no scenic_score and no rank-normalised terms, so ScenicKit's SegmentTerms has no producer
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T23:04:04Z
lease_expires_at: 2026-09-19T07:04:04Z
worktree: .worktrees/T-0146
branch: task/T-0146
exclusive: []
touches: [services/etl/etl/, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0154, T-0024, T-0025, T-0026, T-0027, T-0162, T-0163]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED BY NAME, then green, both runs quoted: over the committed way-record fixture a CLOSED-LOOP row ranks as the region's straightest road until the assembler sets `sinuosity_declined` (imported as `way_record.SINUOSITY_DECLINED_FLAG`) from a closed-way predicate; the predicate is `sinuosity.is_closed_way` once T-0161 is on main and, until then, the assembler's own endpoint-gap check with the same 10 m constant, swapped in one line (STILL OPEN names it)"
  - "the four `ops/sane` check-4 gate assertions over the fixture, each red by name first: no NULL score; motorway, trunk, private and unpaved ways exactly 0.0; every term in [0,1]; ScenicKit parity to 1e-6 against Tests/Fixtures/scoring"
  - "cd services/etl && python -m pytest tests -rs -> the count line and zero skips at the final commit; every `wc -l` quoted re-measured there"
---
## Brief

Panel CODE lens, grounded: 17 modules / 2,101 lines under services/etl/etl/ are all input-side (fetch, dem,
landcover, curvature, terrain, snap, tagfilter, byways). `git grep scenic_score -- services/etl/` returns no
code hit; rank-normalisation appears once, as a comment (byways.py:108). Meanwhile
Sources/ScenicKit/Scoring/SegmentTerms.swift's contract is "every term is rank-normalised or scaled by the
ETL before it arrives" and SegmentScore.score returns nil rather than clamping - wire the two today and every
way scores nil. ScoredEdge.swift cites `score.py` and "the gate-parity fixture"; neither exists.

This is M2's core. Do: `services/etl/etl/score.py` computing the plan's terms per way (M = curv, elev_gain,
speed_fit, sinuosity; E = canopy, relief, 1-impervious, poi, water, 1-furniture; byway bonus capped), rank-
normalising each within the region, applying the GATE (the plan's positive-evidence list; motorway/trunk
score 0 and stay routable), and writing `scenic_score` 0..10 plus the terms to the tagged output. Tests:
motorway/trunk/private/unpaved score exactly 0.0; every term in [0,1] after normalisation; ScenicKit's
SegmentScore over the same fixture agrees within 1e-6 (the gate-parity fixture T-0012 names, made real).
Unblocks T-0029 (rank-order) and P-PROD-01. Depends on T-0024..T-0027 leaving queue/review/.

## Log
- 2026-09-18T03:05:00Z filed by agent/claude-fable-5-1 from the hourly panel's grounded synthesis (.artifacts/panel/last.md). ops/new-task allocated T-9902 again ([[T-0138]]); renamed by hand.
- 2026-09-18T18:00:58Z amended by agent/claude-fable-5-1 from the 11:13 panel: depends_on now carries what the brief said in prose (T-0024..T-0027) plus T-0154, the pure scorer contract split out of this task. Measured at this commit: ls services/etl/etl/*.py | wc -l prints 19 and cat services/etl/etl/*.py | wc -l prints 3138 (the brief's 17 / 2,101 predates PR #68 and PR #69 and is left as written). Terms with no producer under services/etl/etl today: speedFit, sinuosity, pointsOfInterest, furniture, tunnelMeters, metersToNearestMotorway. This task's remainder after T-0154: the region rank-normaliser for the raw-unit terms, those six producers, and the scenic_score 0..10 column.
- 2026-09-18T19:52:17Z SPLIT by agent/claude-fable-5-1 (13:13 panel, grounded). Three disjoint tasks, each claimable now because
  they need only main's `score.py`, `snap.py` and `tagfilter.py`: T-0161 (geometry terms: sinuosity, tunnel
  metres, metres to the nearest motorway), T-0162 (tag-table terms: speed_fit, furniture), T-0163 (the way
  record and the region normaliser, with the ruling on which terms are ranked). `points_of_interest` (Commons
  photo density, 50 km-local rank, network) is T-0164, later. THIS task shrinks to ASSEMBLY: run the
  producers over an extract, normalise, score, write `scenic_score` 0..10 onto the tagged output, and the
  gate tests the plan's `ops/sane` check 4 needs (no NULL scores; motorway/trunk/private/unpaved exactly
  0.0). HAZARD recorded by the grounding pass: `origin/task/T-0029` carries its OWN `services/etl/etl/score.py`,
  unmerged - it collides with T-0154's, which is the reviewed one on main.
- 2026-09-18T20:57:28Z SCOPE CUT AT THE OSMIUM SEAM by agent/claude-fable-5-1 (14:13 panel, DIRECTION lens, grounded). This task is
  now the FIXTURE HALF only: pure-python assembly (the producers' outputs -> way records -> `normalise` ->
  `score.score`) plus the four gate assertions the plan's `ops/sane` check 4 needs - no NULL score; motorway,
  trunk, private and unpaved ways exactly 0.0; every term in [0,1]; ScenicKit parity to 1e-6 - over a COMMITTED
  JSON way-record fixture, run with native Python on the dev box, demonstrated red then green. Grounded facts
  behind the cut: `services/etl/pyproject.toml` declares no dependencies, `score.py` imports only `math` and
  local modules, the Dockerfile installs `osmium-tool` (a subprocess, never a Python import), every fixture is
  JSON, and the score tests already pass natively here. "Write `scenic_score` 0..10 onto the tagged output" is
  REMOVED from this task and is T-0168, which needs docker through WSL. What a hand-written fixture cannot
  surprise its author with - real tag coverage, NULLs from missing DEM samples, the plan's "8/10 top-scored
  ways are roads you'd drive" - moves to T-0168 with it, on purpose and stated.
- 2026-09-18T21:23:07Z NOTE for the assembly, by agent/claude-fable-5-1 (from PR #94's and #93's round-1 reviews): T-0161's
  `way_sinuosity` returns the floor 1.0 for a CLOSED way (ruling R4 there) - the same value as a straight
  two-node way - and exposes `is_closed_way` so a caller can tell the two apart; T-0163's fixer gives
  `WayRecord` an explicit `sinuosity_declined: bool` that keeps such ways OUT of the sinuosity rank population
  and passes them through at the floor. THIS task's assembly must set `sinuosity_declined` from
  `sinuosity.is_closed_way` for every way, with a fixture row that is a closed loop, red when the flag is not
  set (the loop ranks as the straightest road in the region), then green. The score-scale question those
  reviews raised is T-0171, not this task.
- 2026-09-18T23:04:01Z PROMOTED to ready/ and T-0161 dropped from depends_on by agent/claude-fable-5-1 (16:13 panel, STRATEGY,
  grounded): #93 put the whole assembly seam on main (way_record.py `SINUOSITY_DECLINED_FLAG` and
  `sinuosity_declined`, normalise.py `DECLINED_FIELD`, a declined fixture row, `expected_score` on every row),
  and this task's fixture half reads a COMMITTED JSON fixture whose sinuosity, tunnel and motorway numbers are
  typed literals that #94's remaining round (the values on bent polylines) never touches. The RED in the
  21:23:07Z NOTE is now the first acceptance line. T-0168 keeps T-0161 as a dependency - the real extract needs
  the real numbers.
- 2026-09-18T23:04:04Z claimed by agent/claude-opus-5; lease until 2026-09-19T07:04:04Z
- 2026-09-18T23:16:41Z RULINGS BEFORE CODE by agent/claude-opus-5 (owner, author). Read end to end first: this
  Brief with every dated entry (the 20:57:28Z osmium cut, the 21:23:07Z closed-way NOTE, the 23:04:01Z
  promotion), CLAUDE.md, `services/etl/etl/score.py`, `way_record.py`, `normalise.py`, `speedfit.py`,
  `furniture.py`, `tagfilter.py`, `landcover.py`, `curvature.py`, `terrain.py`, `byways.py`, `snap.py`,
  `tests/fixtures/way_records_fixture.json` + `generate_way_records.py` + `plan_oracle.py`,
  `Tests/Fixtures/scoring/segment_terms.json` + `generate.py`, `Tests/ScenicKitTests/SegmentScoreContractTests.swift`,
  `Sources/ScenicKit/Gates/Gates.swift` + `GateReason.swift`, `Sources/ScenicKit/Scoring/ScoredEdge.swift`, and
  `git show origin/task/T-0161:services/etl/etl/sinuosity.py` (PR #94, not on main).

  R1 THE INPUT SHAPE. One committed JSON document, `tests/fixtures/assembly_fixture.json`: `ways: [...]`,
  each row carrying the way's TAGS plus the producers' own RAW INPUTS (`coords`, `elevation_profile`,
  `landcover_codes`, `furniture_nodes`), and a document-level `byways: [...]` overlay because
  `byways.match` (byways.py:194) is a region-level lookup and not a per-way value. NOT a PBF: the 20:57:28Z
  cut removed osmium and the real extract to T-0168.

  R2 WHICH PRODUCER FEEDS WHICH FIELD, per field, because the Brief's two lists are not the whole record.
  INVOKED FOR REAL, from main: `curvature` <- `curvature.way_curvature(coords, way_id)` (curvature.py:172);
  `speed_fit` <- `speedfit.speed_fit_for_tags(highway=, maxspeed=)` (speedfit.py:144); `furniture` <-
  `furniture.furniture_per_km(nodes=, length_m=snap.length_m(coords))` (furniture.py:85, snap.py:106);
  `canopy`/`impervious`/`water` <- `landcover.fractions(landcover_codes)` (landcover.py:122, the landcover
  verdict); `byway_status` <- `byways.match(coords, byways, way_ref=tags.get("ref"))["status"]`.
  TYPED LITERALS IN THE FIXTURE, because their producer is on PR #94 and not on main: `sinuosity`,
  `tunnel_meters`, `meters_to_nearest_motorway`. Each of the three is named in the fixture's own
  `literal_fields` key and in `assemble.py`'s docstring, so no reader has to infer which numbers were
  measured here.
  DISAGREEMENT RULED: the Brief's task line names five real producers and three literals and says nothing
  about `elevation_gain` and `relief`. `terrain.elevation_gain` (terrain.py:85) and `terrain.relief`
  (terrain.py:112) are pure functions over a DEM PROFILE - a `list[float | None]` of metres - and open no
  raster, so the assembler INVOKES them from a fixture-carried `elevation_profile`. The DEM sampling that
  would produce that profile is `dem.py` and is T-0168's. They are producers, not literals.

  R3 THE CLOSED-WAY PREDICATE, and the one line that swaps it. `sinuosity.is_closed_way` does not exist on
  main (`ls services/etl/etl/` has no `sinuosity.py`); on `origin/task/T-0161` it is
  `endpoint_gap_m(coords) <= CLOSED_ENDPOINT_M` with `CLOSED_ENDPOINT_M = 10.0` and `endpoint_gap_m` =
  `snap.length_m([coords[0], coords[-1]])`. `assemble.py` therefore carries `CLOSED_ENDPOINT_M = 10.0` and
  `is_closed_way`, the SAME constant, the same `<=` and the same length model (it imports `snap.length_m`,
  so there is no second earth radius). When T-0161 lands, `assemble.is_closed_way` becomes
  `from .sinuosity import is_closed_way` and both local definitions are deleted - one line in, two out.
  STILL OPEN names it.

  R4 THE OUTPUT COLUMN IS `score`, NOT `scenic_score`. `Sources/ScenicKit/Scoring/ScoredEdge.swift:15` says
  "The ETL writes `scenic_score` as `0...10` onto the way for the router's encoded value", and the 20:57:28Z
  cut REMOVED that column from this task (it is T-0168's, with the scale question T-0171's). Emitting a
  0..1 number under the name a downstream consumer reads as 0..10 is exactly the drift this repository
  exists to catch. The assembled table's column is `score`, which is `score.score`'s own range and name.

  R5 THE SAFETY GATES. CLAUDE.md: "Hard gates are safety only: unpaved (positive evidence), private/no
  access, track". `score.py:29-31` says they live in `ScenicKit.Gates` and never in the scorer, and nothing
  under `services/etl/etl/` gates on tags today. So the assembler applies THREE gates and no more - unpaved
  surface, closed access, `highway=track` - AFTER the score, forcing `score = 0.0` with a named
  `gate_reason`. `Gates.verdict` (Gates.swift:152-175) has five further rules (`refusedTracktypes`,
  `refusedSmoothness`, `refusableBarriers` + `locked=yes`, `ford=yes`, `refusedServiceValues`) that are NOT
  implemented here: a second full gate in Python is how two answers for one road reach the corpus, and the
  port is its own task. STILL OPEN names it. The two sets that ARE restated (`UNPAVED_SURFACES`,
  `CLOSED_ACCESS`) are pinned by `test_assemble.py` against the literals parsed out of
  `Gates.swift:80-89`, and the three reason names against the `case`s of `GateReason.swift`, so neither can
  drift silently.

  R6 A GATED WAY STAYS IN THE RANK POPULATION. `normalise.population_of` takes out the zero classes and
  nothing else (normalise.py). A gravel road's curvature and relief are measurements of a real road, and
  there are not 15k of them setting the curve; taking them out would be a change to T-0163's reviewed
  module, which this task does not touch. The gate is a ROUTING refusal applied to the score, not a claim
  that the measurement is absent. STILL OPEN records the question.

  R7 MOTORWAY AND TRUNK ARE NOT GATED. They score 0.0 by class inside `score.score` (score.py:139) and stay
  routable (CLAUDE.md product invariants; Gates.swift:9-10 and GateReason.swift:9 both say there is
  deliberately no motorway case). `gate_reason` is None for them and the test asserts that alongside the
  0.0, so a later edit cannot make them 0.0 by gating them.

  R8 THIS FIXTURE CARRIES NO `expected_score`, unlike `way_records_fixture.json`. Its ranked terms come out
  of `way_curvature` and `terrain.relief` over real geometry, and a hand-computed expectation for those
  would be a second implementation of the producer rather than an oracle. What this fixture pins is the
  ASSEMBLY - which producer feeds which field, the declined flag, the gates, the zero classes, the ranks -
  and the sinuosity ranks it pins are typed out with the arithmetic shown. The score ARITHMETIC is pinned
  by `Tests/Fixtures/scoring/segment_terms.json`, whose oracle was transcribed by hand from plan:78-87 by
  neither scorer, and that is what the parity gate asserts.

  R9 WHAT "ScenicKit parity to 1e-6" MEANS HERE. The four check-4 gates are gates over THIS assembler, so
  the parity gate drives `Tests/Fixtures/scoring/segment_terms.json`'s 1000 rows through
  `assemble.score_record` - the record -> `score_kwargs()` -> `score.score` seam this task builds - and
  compares to the fixture's `expected` within 1e-6, reporting by row id.
  `Tests/ScenicKitTests/SegmentScoreContractTests.swift` asserts the same rows of the same file at the same
  tolerance, which is what makes it parity and not a self-comparison; it is run ONCE here and quoted, not
  re-implemented. `tests/test_score_contract.py` already drives bare `score.score` over the same file; the
  gate here is the SEAM (a term inverted, swapped or dropped between the record and the scorer), which that
  test cannot see.

  R10 `furniture_per_km` RETURNS None for a way with no usable length (furniture.py:85-95). The assembler
  REFUSES that way by way_id and field name rather than substituting 0.0, which `furniture.py` says would
  state "this way is rural". Same for a landcover buffer with no valid sample (`fractions` returns
  `{"coverage": 0.0}` and no terms) and for a `highway` tag that is absent.
- 2026-09-18T23:39:52Z BUILT AND DEMONSTRATED RED, by agent/claude-opus-5. Three new files, all untracked
  before this task: `services/etl/etl/assemble.py`, `services/etl/tests/test_assemble.py`,
  `services/etl/tests/fixtures/assembly_fixture.json`. Pristine at 6c0472b; each mutation below was applied
  ALONE to `assemble.py`, run with `__pycache__` purged first, then restored with `git checkout --` after a
  1.2 s sleep, `git status --short` empty between mutations. Green before and after: `python -m pytest
  tests/test_assemble.py -rs` -> `14 passed in 0.21s`.

  RED 1 - THE CLOSED LOOP, acceptance line 1. Mutation: `sinuosity_declined=is_closed_way(coords)` ->
  `sinuosity_declined=False`, i.e. the assembler never sets the flag. `3 failed, 11 passed in 0.31s`:
    FAILED tests/test_assemble.py::test_the_closed_loop_declines_sinuosity_instead_of_ranking_as_the_straightest_road
    FAILED tests/test_assemble.py::test_the_answering_ways_take_the_ranks_of_a_population_of_five
    FAILED tests/test_assemble.py::test_the_count_line_names_every_absence
  and verbatim:
    E       AssertionError: way 800000005 holds sinuosity=0.08333333333333333 and scores 0.2154490136401879: that is a RANK, so the loop is in the population and is the region's straightest road (the lowest rank in a population of six is (0 + 0.5*1)/6)
    E       AssertionError: {800000006: 0.25, 800000004: 0.4166666666666667, 800000003: 0.5833333333333334, 800000008: 0.75, ...}
    E         - _declined=1 points_of_interest_absent=8 null_score=0
    E         + _declined=0 points_of_interest_absent=8 null_score=0
  THAT IS THE RED THE 21:23:07Z NOTE ASKED FOR: 0.08333333333333333 is the lowest sinuosity rank in the
  region, so the roundabout IS the region's straightest road, and all five other ways move (0.25,
  0.4166666666666667, 0.5833333333333334, 0.75, 0.9166666666666666 over a population of six, against 0.1,
  0.3, 0.5, 0.7, 0.9 over a population of five). GREEN with the flag set: the loop holds
  `way_record.DECLINED_RANK`, which is exactly 0.0 - a value `normalise`'s estimator can never produce for
  a ranked way, because its extremes are `0.5/n` and `1 - 0.5/n` - and `flags()` carries
  `sinuosity_declined`.

  RED 2 - NO NULL SCORE (gate 1 of 4). Mutation: `scored_row` returns `None` for a gated way instead of
  `GATE_SCORE`. `3 failed, 11 passed in 0.38s`:
    FAILED tests/test_assemble.py::test_gate_no_row_has_a_null_score
    FAILED tests/test_assemble.py::test_gate_private_and_unpaved_ways_score_exactly_zero
    FAILED tests/test_assemble.py::test_the_count_line_names_every_absence
    E       AssertionError: rows with a NULL score: [800000003, 800000004]
    E       AssertionError: assert 'ASSEMBLE way... null_score=2' == 'ASSEMBLE way... null_score=0'

  RED 3 - MOTORWAY AND TRUNK EXACTLY 0.0 (gate 2a). Mutation: the `highway` value is title-cased in
  `record_from_row`, so `"Motorway"` is not in `byways.SCENIC_ZERO_CLASSES` and the way is ranked like any
  other. `3 failed, 11 passed in 0.33s`:
    FAILED tests/test_assemble.py::test_gate_motorway_and_trunk_score_exactly_zero_and_are_not_gated
    FAILED tests/test_assemble.py::test_the_answering_ways_take_the_ranks_of_a_population_of_five
    FAILED tests/test_assemble.py::test_the_count_line_names_every_absence
    E           AssertionError: way 800000001 scored 0.231131387248525
    E           assert 0.231131387248525 == 0.0

  RED 4 - PRIVATE AND UNPAVED EXACTLY 0.0 (gate 2b), and the Gates.swift drift guard with it. Mutation:
  `"private"` removed from `CLOSED_ACCESS`. `3 failed, 11 passed in 0.38s`:
    FAILED tests/test_assemble.py::test_gate_private_and_unpaved_ways_score_exactly_zero
    FAILED tests/test_assemble.py::test_the_gate_sets_are_the_ones_scenickit_gates_on
    FAILED tests/test_assemble.py::test_the_count_line_names_every_absence
    E       AssertionError: {'way_id': 800000003, 'highway': 'residential', 'score': 0.36157016686766563, 'gate_reason': None, ...}
    E       AssertionError: assert {'destination...no', 'permit'} == {'destination...t', 'private'}
    E         - ASSEMBLE ways=8 zero_class=2 gated=2 sinuosit
    E         + ASSEMBLE ways=8 zero_class=2 gated=1 sinuosit

  RED 5 - EVERY TERM IN 0..1 (gate 3). Mutation: `unit_terms` reports `getattr(record, name)` instead of
  what `score_kwargs()` handed the scorer, so the table carries the record's `points_of_interest` - None
  until T-0164 - rather than `way_record.POI_ABSENT`. `1 failed, 13 passed in 0.35s`:
    FAILED tests/test_assemble.py::test_gate_every_term_is_in_the_unit_interval
    E       AssertionError: way 800000001: points_of_interest=None is not a number; way 800000002: points_of_interest=None is not a number; way 800000003: points_of_interest=None is not a number; way 800000004: points_of_interest=None is not a number; way 800000005: points_of_interest=None is not a number; way 800000006: points_of_interest=None is not a number; way 800000007: points_of_interest=None is not a number; way 800000008: points_of_interest=None is not a number

  RED 6 - SCENICKIT PARITY TO 1e-6 (gate 4). Mutation: `score_record` inverts `impervious` once more before
  calling the scorer - the exact failure `way_record.py`'s docstring says no single-module test would ever
  see, because `score.scenery_mean` already enters it as `(1 - x)` and two inversions cancel. `1 failed,
  13 passed in 0.41s`:
    FAILED tests/test_assemble.py::test_gate_scenickit_parity_to_1e_6_over_the_shared_scoring_fixture
    E       AssertionError: 606 of 1000 rows disagree with the oracle by >= 1e-06: term-impervious-0.0: got 0.4464281177068813, oracle 0.5506399249251752; term-impervious-1.0: got 0.5506399249251752, oracle 0.4464281177068813; uniform-1.0: got 0.9202667627287333, oracle 0.8077298313366432; axis-scenery-zero-none: got 0.30386311717294956, oracle 0.0; axis-scenery-zero-eligible: got 0.37374444165670445, oracle 0.16061951594470017

  THE SWIFT SIDE OF THE PARITY, run ONCE on the same bytes, not re-implemented:
    swift test --scratch-path .build/T0146 --filter SegmentScoreContract
    Suite "SegmentScore contract (shared fixture)" passed after 0.147 seconds.
    Test run with 5 tests in 1 suite passed after 0.147 seconds.
  including `every fixture row scores within 1e-6 of the oracle`. Both scorers are held to
  `Tests/Fixtures/scoring/segment_terms.json`, whose expectations were transcribed by hand from plan:78-87
  and computed by neither of them.

  THE CLI, over the committed fixture:
    python -m etl.assemble --input tests/fixtures/assembly_fixture.json --out ../../.artifacts/T-0146-scores.json
    ASSEMBLE ways=8 zero_class=2 gated=2 sinuosity_declined=1 points_of_interest_absent=8 null_score=0
- 2026-09-18T23:45:11Z ACCEPTANCE BLOCK RE-RUN AT THE FINAL PRE-REVIEW COMMIT, by agent/claude-opus-5. Every
  gate below run BARE, never piped into `tail`/`head`/`grep` before a `&&`. The three measured files are
  final at this commit and were not touched after being measured; the only edit after these runs is this
  Log entry's own text, which no gate reads except `ops/queue-check`, which was re-run after it.

  ACCEPTANCE 1 - the closed-loop RED then green, both runs quoted: see the 23:39:52Z entry, RED 1. Red by
  name (`test_the_closed_loop_declines_sinuosity_instead_of_ranking_as_the_straightest_road`,
  `test_the_answering_ways_take_the_ranks_of_a_population_of_five`,
  `test_the_count_line_names_every_absence`), the loop's rank 0.08333333333333333 and score
  0.2154490136401879 quoted verbatim, green with the flag set from the predicate. The flag is
  `way_record.SINUOSITY_DECLINED_FLAG`, imported and asserted by that name. The predicate is the
  assembler's own `is_closed_way` with `CLOSED_ENDPOINT_M = 10.0`, the same constant and comparison as
  T-0161's; STILL OPEN names the one-line swap.

  ACCEPTANCE 2 - the four `ops/sane` check-4 gates, each red by name first: RED 2 (`test_gate_no_row_has_a_
  null_score`), RED 3 (`test_gate_motorway_and_trunk_score_exactly_zero_and_are_not_gated`), RED 4
  (`test_gate_private_and_unpaved_ways_score_exactly_zero`), RED 5 (`test_gate_every_term_is_in_the_unit_
  interval`), RED 6 (`test_gate_scenickit_parity_to_1e_6_over_the_shared_scoring_fixture`), all in the
  23:39:52Z entry with their verbatim output. The parity gate is against
  `Tests/Fixtures/scoring/segment_terms.json`; the Swift half of that contract was run once and quoted
  there.

  ACCEPTANCE 3 - the whole ETL suite and the `wc -l` figures, at this commit:
    cd services/etl && python -m pytest tests -rs
    848 passed in 184.71s (0:03:04)
  no `short test summary info` section, so zero skips (`-rs` would list them; `-r` reports are what
  pyproject's `-q` suppresses otherwise).
    wc -l services/etl/etl/assemble.py services/etl/tests/test_assemble.py services/etl/tests/fixtures/assembly_fixture.json
      261 services/etl/etl/assemble.py
      266 services/etl/tests/test_assemble.py
       92 services/etl/tests/fixtures/assembly_fixture.json
      619 total
  All three under the 300-line cap.

  THE OTHER GATES, bare:
    bash ops/lib/check-line-cap
    P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines
    (exit 0. NOTE: this gate is SWIFT-ONLY - it says so in its own output and T-0058 is the open task for
    it - so it did not measure the two Python files this task adds. Their 261 and 266 are the `wc -l`
    above, not this gate's finding.)

    bash ops/queue-check
    QUEUE OK (169 tasks)
    queue-check exit=0

    bash ops/check-pins --source-only
    PINS ok=11 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
    check-pins exit=0

  STILL OPEN, none of it fixed here:
  * THE ONE-LINE SWAP. `assemble.CLOSED_ENDPOINT_M` and `assemble.is_closed_way` exist only because
    `services/etl/etl/sinuosity.py` is on PR #94 and not on main. When T-0161 lands, delete both and add
    `from .sinuosity import is_closed_way` - one line in, two out - and
    `test_the_closed_way_predicate_uses_the_same_constant_as_the_sinuosity_producer` becomes the assertion
    that the two agree. Nothing enforces that swap today: the constant is duplicated, and a change to
    T-0161's 10.0 would not be noticed here.
  * THE GATE IS A THIRD OF `Gates.verdict`. Unpaved surface, `highway=track` and closed access are
    implemented; `refusedTracktypes`, `refusedSmoothness`, a locked `refusableBarriers` gate, `ford=yes`
    and `refusedServiceValues` are not (ruling R5). `test_the_gate_sets_are_the_ones_scenickit_gates_on`
    pins the two sets that ARE restated and the three reason names, and pins NOTHING about the five
    missing rules - a way with `ford=yes` is scored here and refused by ScenicKit. A real port of
    `Gates.verdict` to Python, with `ConsideredTags`'s discipline, is its own task.
  * A GATED WAY IS STILL IN THE RANK POPULATION (ruling R6). `normalise.population_of` takes out the zero
    classes and nothing else, so a private or gravel way's curvature and relief set the curve for the roads
    that are actually routable. Defensible at this scale and wrong at some other; deciding it is a change
    to T-0163's module.
  * THE FIXTURE IS HAND-WRITTEN AND CANNOT SURPRISE ITS AUTHOR. No real tag coverage, no NULL from a
    missing DEM sample, no "8/10 top-scored ways are roads you'd drive". That is T-0168's, on purpose and
    stated in the 20:57:28Z cut. `expected_score` is absent from this fixture for ruling R8's reason.
  * `points_of_interest` IS ABSENT ON ALL EIGHT WAYS (`points_of_interest_absent=8`), so the POI term is
    `way_record.POI_ABSENT` everywhere in this table and the parity gate is the only thing exercising a
    non-zero one. T-0164.
  * NO `scenic_score` 0..10 COLUMN and no corpus write. T-0168, with the scale question T-0171's.
  * `ops/test` AND FULL `ops/check-pins` WERE NOT RUN, as instructed for this task; `--source-only` was.
  * THE THREE LITERAL FIELDS. `sinuosity`, `tunnel_meters` and `meters_to_nearest_motorway` are typed into
    the fixture. Nothing checks those literals against the producers on PR #94, and when T-0161 lands the
    fixture's sinuosity column should be regenerated from `way_sinuosity` over the same coordinates - at
    which point the hand-typed ranks in `test_assemble.py` have to be re-derived.
- 2026-09-19T01:03:54Z THE TEMPORARY PREDICATE COPY NOW HAS A TRIPWIRE, by agent/claude-opus-5 (fixer for the
  owner, from the hourly panel's grounded synthesis, before the review is bought). Six lines of test, no module
  code. `test_the_temporary_predicate_copy_must_be_deleted_the_day_t_0161_lands` sits next to the literal
  assertion in `tests/test_assemble.py`: it imports `etl.sinuosity` in a `try` and RETURNS on `ImportError` -
  it does NOT `pytest.skip`, so the suite stays skip-free and `-rs` keeps printing no summary section - and,
  once that module exists, asserts `assemble.is_closed_way is sinuosity.is_closed_way and
  assemble.CLOSED_ENDPOINT_M is sinuosity.CLOSED_ENDPOINT_M` with the message `T-0161 landed: do the one-line
  swap in assemble.py`. This closes the first STILL OPEN bullet of the 23:45:11Z entry ("Nothing enforces that
  swap today: the constant is duplicated, and a change to T-0161's 10.0 would not be noticed here") - that
  entry is not edited; this one corrects it. Until #94 lands the assertion is unreachable by construction, so
  the literal assertion in `test_the_closed_way_predicate_uses_the_same_constant_as_the_sinuosity_producer`
  stays: it pins 10.0 on the one side that exists today.

  RED 7 - THE DAY T-0161 LANDS. Demonstrated on a COPY under `.artifacts/` (gitignored, deleted after the
  run), never on the head: `services/etl` copied whole, plus `Sources/ScenicKit/Gates/Gates.swift`,
  `GateReason.swift` and `Tests/Fixtures/scoring/segment_terms.json` at the same relative depth so the test
  module's `ROOT = HERE.parents[2]` still resolves, and `etl/sinuosity.py` taken VERBATIM from the branch
  (`git show origin/task/T-0161:services/etl/etl/sinuosity.py`, 83 lines, `CLOSED_ENDPOINT_M = 10.0` and
  `is_closed_way` at its lines 46 and 68) - the state after #94 merges, not a hand-written imitation.
  `__pycache__` purged before the run. `1 failed, 14 passed in 0.75s`:
    FAILED tests/test_assemble.py::test_the_temporary_predicate_copy_must_be_deleted_the_day_t_0161_lands
    E       AssertionError: T-0161 landed: do the one-line swap in assemble.py
    E       assert (<function is_closed_way at 0x0000022718C51F30> is <function is_closed_way at 0x0000022718C53F40>)
    E        +  where <function is_closed_way at 0x0000022718C51F30> = assemble.is_closed_way
    E        +  and   <function is_closed_way at 0x0000022718C53F40> = <module 'etl.sinuosity' from
    E              '...\.artifacts\T-0146-red\services\etl\etl\sinuosity.py'>.is_closed_way
  The other 14 tests pass in that copy, so the tripwire is the only thing that turns red when the module
  arrives - and it names the swap rather than reporting a rank that moved. GREEN at the head with the copy
  deleted, `__pycache__` purged and `ls etl/sinuosity.py` printing `No such file or directory`:
    cd services/etl && python -m pytest tests/test_assemble.py -rs
    15 passed in 0.37s

  ACCEPTANCE BLOCK RE-RUN AT THIS COMMIT, renumbered; the 23:45:11Z block's runs stand except where re-quoted
  here. Every gate bare, never piped into `tail`/`head`/`grep` before a `&&`. The measured files are final at
  this commit; the only edit after these runs is this Log entry's own text, which no gate reads except
  `ops/queue-check`, re-run after it.

  ACCEPTANCE 1 - the closed-loop RED then green, both runs quoted: unchanged, the 23:39:52Z entry's RED 1 and
  the 23:45:11Z entry's ACCEPTANCE 1. TOUCHED here only in this line's tail - "the predicate is
  `sinuosity.is_closed_way` once T-0161 is on main and, until then, the assembler's own endpoint-gap check
  with the same 10 m constant, swapped in one line (STILL OPEN names it)" - which is now enforced by a test
  that fails the day the swap is due: RED 7 above, red by name over the post-#94 module, green at the head.
  Re-run at this commit, bare:
    cd services/etl && python -m pytest tests/test_assemble.py -rs
    15 passed in 0.37s
  14 before this change. No `short test summary info` section, so zero skips.

  ACCEPTANCE 2 - the four `ops/sane` check-4 gates, each red by name first: unchanged, RED 2 through RED 6 in
  the 23:39:52Z entry with the Swift half quoted there. No module code changed here; all four gate tests are
  among the 15 above.

  ACCEPTANCE 3 - the whole ETL suite and the `wc -l` figures, RE-MEASURED at this commit:
    cd services/etl && python -m pytest tests -rs
    849 passed in 81.43s (0:01:21)
  848 before this change, +1 for the new test. No `short test summary info` section, so zero skips (`-rs`
  would list them; `-r` reports are what pyproject's `-q` suppresses otherwise).
    wc -l services/etl/etl/assemble.py services/etl/tests/test_assemble.py services/etl/tests/fixtures/assembly_fixture.json
      261 services/etl/etl/assemble.py
      281 services/etl/tests/test_assemble.py
       92 services/etl/tests/fixtures/assembly_fixture.json
      634 total
  `test_assemble.py` is 266 -> 281 (+15), still under the 300-line cap; the other two are untouched and
  re-measured anyway.

  THE OTHER GATES, bare:
    bash ops/check-pins --source-only
    PINS ok=11 skipped=12 pending=1 expired=0 failed=0 tier=linux source-only
    check-pins exit=0

    bash ops/queue-check
    QUEUE OK (169 tasks)
    queue-check exit=0

  `ops/test` and the full `ops/check-pins` were NOT run, as instructed for this correction; `--source-only`
  was. Every other STILL OPEN bullet of the 23:45:11Z entry is untouched and still open, the three literal
  fixture fields included: this tripwire pins that the two predicates are ONE object, and says nothing about
  the hand-typed `sinuosity` column, which still has to be regenerated from `way_sinuosity` when #94 lands.
- 2026-09-19T02:18:41Z THE SWAP IS DONE: T-0161 LANDED AND THE TEMPORARY PREDICATE COPY IS DELETED, by
  agent/claude-opus-5 (fixer for the owner). `git fetch origin && git merge --no-edit origin/main` - a MERGE,
  not a rebase - brings PR #94 in: origin/main is `c6a7a45` (Merge pull request #94 from
  phineasfritsch/task/T-0161) and the merge commit on this branch is `232fef3`. No conflict, in the task file
  or anywhere else. `services/etl/etl/sinuosity.py` (83 lines) is now on the branch, with `CLOSED_ENDPOINT_M =
  10.0` at its line 46, `endpoint_gap_m` at 62 and `is_closed_way` at 68 - the module ruling R3 was waiting for.

  RED 8 - THE TRIPWIRE FIRED ON THE REAL MERGE. At `232fef3`, `__pycache__` purged, BEFORE any module edit.
  This is the red that RED 7's `.artifacts/` copy anticipated, now on the head itself:
    cd services/etl && python -m pytest tests/test_assemble.py -rs
    1 failed, 14 passed in 0.61s
    FAILED tests/test_assemble.py::test_the_temporary_predicate_copy_must_be_deleted_the_day_t_0161_lands
    E       AssertionError: T-0161 landed: do the one-line swap in assemble.py
    E       assert (<function is_closed_way at 0x0000010FDB53AB00> is <function is_closed_way at 0x0000010FDB558AF0>)
    E        +  where <function is_closed_way at 0x0000010FDB53AB00> = assemble.is_closed_way
    E        +  and <function is_closed_way at 0x0000010FDB558AF0> = <module 'etl.sinuosity' from
    E              '...\.worktrees\T-0146\services\etl\etl\sinuosity.py'>.is_closed_way
  The other 14 pass, so the tripwire is the only thing the merge turned red, and it named the fix.

  THE SWAP. `etl/assemble.py` now carries `from .sinuosity import CLOSED_ENDPOINT_M, endpoint_gap_m,
  is_closed_way` and its own `CLOSED_ENDPOINT_M = 10.0`, `endpoint_gap_m` and `is_closed_way` are DELETED -
  eleven lines out, one import in. `endpoint_gap_m` is public on `sinuosity`, so no local helper survives;
  `MIN_COORDINATES` stays because `coordinates()` still uses it for the row-level check, and `snap.length_m`
  stays because `record_from_row` passes it to `furniture.furniture_per_km`. An `__all__` names the three
  re-exported objects, so a reader of `assemble.CLOSED_ENDPOINT_M` can see it is `sinuosity`'s object and not
  a second copy. The R3 paragraph of the module docstring is rewritten to the state that now exists. Behaviour
  is unchanged by construction: `sinuosity_declined=is_closed_way(coords)` is the same call against the same
  10.0 m and the same `snap` length model, which is what the fixture's ranks pin.

  ACCEPTANCE BLOCK RE-RUN AT THIS COMMIT, renumbered; every gate bare, never piped into `tail`/`head`/`grep`
  before a `&&`. The measured files are final at this commit; the only edit after these runs is this Log
  entry's own text, which no gate reads except `ops/queue-check`, re-run after it.

  ACCEPTANCE 1 - the closed-loop RED then green, both runs quoted: the 23:39:52Z entry's RED 1 and the
  23:45:11Z entry's ACCEPTANCE 1 stand - no rank moved here. The acceptance line's tail, "the predicate is
  `sinuosity.is_closed_way` once T-0161 is on main", is now literally true, and its "swapped in one line
  (STILL OPEN names it)" is spent: RED 8 above is the red by name, green after the swap:
    cd services/etl && python -m pytest tests/test_assemble.py -rs
    15 passed in 0.33s
  No `short test summary info` section, so zero skips.

  ACCEPTANCE 2 - the four `ops/sane` check-4 gates, each red by name first: unchanged, RED 2 through RED 6 in
  the 23:39:52Z entry. No gate code changed here; all four gate tests are among the 15 above.

  ACCEPTANCE 3 - the whole ETL suite and the `wc -l` figures, RE-MEASURED at this commit:
    cd services/etl && python -m pytest tests -rs
    985 passed in 55.58s
  849 on this branch before the merge; the +136 are T-0161's own tests arriving with it (`test_sinuosity.py`,
  `test_proximity.py`, `test_proximity_bends.py`, `test_proximity_interior.py`), not new here. No `short test
  summary info` section, so zero skips.
    wc -l services/etl/etl/assemble.py services/etl/tests/test_assemble.py \
          services/etl/tests/fixtures/assembly_fixture.json services/etl/etl/sinuosity.py
      250 services/etl/etl/assemble.py
      281 services/etl/tests/test_assemble.py
       92 services/etl/tests/fixtures/assembly_fixture.json
       83 services/etl/etl/sinuosity.py
      706 total
  `assemble.py` is 261 -> 250 (-11), under the 300-line cap. `test_assemble.py` and the fixture are untouched
  by this correction and re-measured anyway; `sinuosity.py` is quoted because the swap now depends on it.

  THE OTHER GATES, bare:
    bash ops/lib/check-line-cap
    P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines
    check-line-cap exit=0

    bash ops/queue-check
    QUEUE OK (175 tasks)
    queue-check exit=0

    bash ops/check-pins --source-only
    PINS ok=11 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only
    check-pins exit=0
  169 -> 175 tasks and skipped=12 -> 13 are the merge's, not this change's.

  `ops/test` and the full `ops/check-pins` were NOT run, as instructed for this correction; `--source-only`
  was.

  THE 23:45:11Z ENTRY'S FIRST STILL OPEN BULLET IS CLOSED - by this dated line, not by an edit to it. "THE
  ONE-LINE SWAP ... Nothing enforces that swap today: the constant is duplicated, and a change to T-0161's
  10.0 would not be noticed here" no longer describes the tree: there is ONE `CLOSED_ENDPOINT_M` under
  `services/etl/`, `sinuosity`'s, `assemble` imports it, and
  `test_the_temporary_predicate_copy_must_be_deleted_the_day_t_0161_lands` now asserts that identity for real
  instead of returning on `ImportError`. `test_the_closed_way_predicate_uses_the_same_constant_as_the_
  sinuosity_producer` keeps its 10.0 literal: with one definition left it pins the VALUE, and the tripwire
  pins that only one object carries it.

  STILL OPEN, none of it fixed here - every bullet of the 23:45:11Z entry except the swap stands as written,
  and the merge makes one of them due:
  * THE THREE LITERAL FIXTURE FIELDS, NOW ACTIONABLE. `sinuosity`, `tunnel_meters` and
    `meters_to_nearest_motorway` are still hand-typed into `assembly_fixture.json` and `LITERAL_FIELDS` still
    names them, although `sinuosity.way_sinuosity` and `proximity` are on the branch as of `232fef3`.
    Regenerating the fixture's `sinuosity` column from `way_sinuosity` over the same coordinates re-derives
    the hand-typed ranks in `test_assemble.py`, so it is a fixture change with its own red - not this
    correction, which is the one swap the tripwire named. It belongs to T-0168 or a follow-up task.

- 2026-09-19T03:03:09Z REVIEW FAIL by agent/rv1-pr102 (reviewer, not the owner agent/claude-opus-5, not a fixer,
  not the orchestrator). Reviewed at eff7f3c == origin/task/T-0146 in a detached worktree (.worktrees/rv1-pr102,
  removed at the end; `git status --short` empty there throughout and in the main worktree). `gh pr checks 102`:
  core pass 2m12s, pins-source-only pass 1m10s.

  THE ACCEPTANCE BLOCK RE-RUN AT THIS HEAD, every gate bare, every number reproduced: `python -m pytest tests
  -rs` -> `985 passed in 97.05s (0:01:37)` with no short-test-summary section (zero skips); `python -m pytest
  tests/test_assemble.py -rs` -> `15 passed in 0.61s`; `wc -l` -> 250 assemble.py / 281 test_assemble.py / 92
  assembly_fixture.json / 83 sinuosity.py; `bash ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift files tracked
  (Sources=26, Tests=37, apps/ios=8), none over 300 lines`, exit 0; `bash ops/queue-check` -> `QUEUE OK (175
  tasks)`, exit 0; `bash ops/check-pins --source-only` -> `PINS ok=11 skipped=13 pending=1 expired=0 failed=0
  tier=linux source-only`, exit 0; `swift test --scratch-path .build/rv1-pr102 --filter SegmentScoreContract`
  -> `Test run with 5 tests in 1 suite passed after 0.152 seconds`, including `every fixture row scores within
  1e-6 of the oracle`; the CLI over the committed fixture -> `ASSEMBLE ways=8 zero_class=2 gated=2
  sinuosity_declined=1 points_of_interest_absent=8 null_score=0`. NO CLAIM IN THE 02:18:41Z BLOCK WAS FALSE.
  Two arithmetics re-done by hand: the loop's would-be rank (0 + 0.5*1)/6 = 0.08333333333333333 against
  DECLINED_RANK = 0.0, which the estimator cannot produce (extremes 0.5/n and 1 - 0.5/n); and the five answering
  ranks 0.1/0.3/0.5/0.7/0.9 over the distinct literals 1.02/1.15/1.30/1.45/1.80 in a population of five (8 ways
  - 2 zero classes - 1 declined). Both correct, and matched by the delivered table.

  THREE MUTANTS, EACH ALONE, ON THE REVIEW WORKTREE, restored with `git checkout --` after 1.2 s, `git status
  --short` empty between. TWO SURVIVED.
  M1 `elevation_gain=terrain.relief(profile)` / `relief=terrain.elevation_gain(profile)` -> `15 passed in
  0.50s`, while way 800000005 moves 0.2125223515064957 -> 0.23162315252218243 and way 800000006
  0.18404512257119796 -> 0.1745245026413249.
  M2 gate_reason also refusing `motorway` -> `2 failed`, FAILED
  test_gate_motorway_and_trunk_score_exactly_zero_and_are_not_gated, `AssertionError: way 800000001 was GATED:
  'track'`. The CLAUDE.md invariant IS pinned.
  M3 `DEFAULT_MOTORWAY_DISTANCE_M = 0.0` -> `15 passed in 0.40s`, while the region's best way 800000007 falls
  0.8401112524548593 -> 0.5880778767184015.

  BLOCKING 1 - a RANKED term can be read off the wrong producer with the suite green (M1). Ruling R2 makes
  "which producer feeds which field" the module, and test_the_mapped_terms_are_what_their_producers_return
  names this exact hazard in its docstring ("invisible once it is a rank") while asserting only the four MAPPED
  terms, which are never ranked. curvature, elevation_gain, relief and furniture have no per-field pin. R8 does
  not exempt it: a wiring pin is not a score expectation. Close it in this file's own style - way 800000007's
  profile gives elevation_gain 18+23+27+22+31 = 121.0 and relief 392-300 = 92.0, two literals on the RAW record
  from record_from_row, red with M1 then green.
  BLOCKING 2 - the two distance fields are unpinned (M3). Nothing holds DEFAULT_TUNNEL_M / 
  DEFAULT_MOTORWAY_DISTANCE_M to the score.py defaults they say they restate, and six of the eight rows rely on
  them. Assert inf / 0.0 on a row that omits them and the two read values (90.0, 120.0).
  BLOCKING 3 - the ported `no_access` gate is half of the rule whose name it pins, and "five FURTHER rules" is
  false at this head. `assemble.gate_reason({'highway':'residential','motor_vehicle':'no','surface':'asphalt'})`
  -> None; Gates.swift:161 refuses it as `.noAccess`, the case GateReason.swift:31 documents as "`access`
  forbids the public, or `motor_vehicle = no`". `git grep motor_vehicle -- services/etl/` is empty. Gates.verdict
  has nine refusal branches, three ported, SIX unported - the docstring (:42-43), R5 and the STILL OPEN bullet
  all say five. Implement the rule with a fixture row and a red by name, or correct the enumeration to six and
  pin the delta; do not leave "five" standing in three places.

  RULED, on the scope question. The 20:57:28Z cut is about the osmium seam and cannot move a gate RULE. The gate
  list is CLAUDE.md's three, and R5 ported exactly those, so declining refusedTracktypes, refusedSmoothness, the
  locked-barrier rule, ford=yes and refusedServiceValues is CORRECT for T-0146 and is not a defect. They are not
  T-0168's by default either: T-0168 writes the first corpus, and a corpus that scores a ford as scenic is a
  defect the moment it is written - file the port task and make it block the corpus write (RECORDABLE).
  `motor_vehicle=no` is not one of those five and is in scope here (BLOCKING 3).

  RECORDABLE, not blocking: the fixture is nearly degenerate on the elevation_gain/relief axis (four of six ways
  share both ranks, which is why M1 moves only two scores); CLAUDE.md's ops/mutate obligation for a new module
  under services/etl/etl/ is not ruled on anywhere in this Log, although no Python ETL module has a population
  yet (T-0154's precedent, T-0176 in flight) - either rule assemble.py a wiring module or add it to T-0176;
  test_gate_every_term_is_in_the_unit_interval can only catch a non-number, since score_kwargs() raises first;
  metres()'s INFINITY branch is unobservable (`float("Infinity")` is already inf); R10's named refusals are
  uneven (bare KeyError for a missing coords / landcover_codes / elevation_profile / sinuosity); every disclosed
  gap re-checked and still accurately described (the three typed literals, now regenerable since 232fef3; the
  UNPAVED_SURFACES copy, T-0181; no real extract, T-0168; points_of_interest absent, T-0164; no 0..10 column,
  T-0168/T-0171).

  NOT DONE, as instructed: `ops/test` and the full `ops/check-pins` were not run; `--source-only` was, once.
  Nothing in the repository was changed by this review - no queue transition, no reviewer field, no commit.

- 2026-09-19T03:30:00Z FIX by agent/claude-opus-5, the OWNER of this task, acting on agent/rv1-pr102's FAIL above. Not the
  reviewer and not the orchestrator. In `.worktrees/T-0146` on `task/T-0146`, from eff7f3c. No other worktree
  was created, nothing was merged, and `ops/test` and the full `ops/check-pins` were NOT run (`--source-only`
  was, once, bare). All three blocking findings are CONFIRMED and none is disputed.

  R11, RULED BEFORE ANY CODE WAS WRITTEN, on the one place the review left a choice. BLOCKING 3 offered
  either "implement the rule with a fixture row and a red by name" or "correct the enumeration to six and pin
  the delta". IMPLEMENTED, because the two are not symmetric: `motor_vehicle=no` is CLAUDE.md's own
  "private/no access" gate and `GateReason.swift:31` spells that one case as "`access` forbids the public, or
  `motor_vehicle = no`" - one reason, two branches - so leaving it out was not a scope cut like the five the
  review RULED correctly declined, it was half a rule. Implementing it also makes the standing "five further
  rules" TRUE at the new head, so the enumeration is pinned as a count rather than re-typed as prose, and the
  dated correction below is about what the RECORD said at eff7f3c.

  REPRODUCED FIRST, each mutant alone on this worktree, applied and restored by writing the original bytes
  back - `services/etl/etl/assemble.py` md5 07870eecbd06525ff01c640151d87335 before AND after every one -
  with 1.1 s between the run and the restore, `__pycache__` purged before every pytest run, and `git status
  --short` carrying only this task file between them:
    M1 `elevation_gain=terrain.relief(profile)` + `relief=terrain.elevation_gain(profile)` (mutant md5
       931adb4c37ff0b27ffc5d7110a3e6c52) -> `15 passed in 0.49s`. SURVIVED.
    M3 `DEFAULT_MOTORWAY_DISTANCE_M = 0.0` (mutant md5 d957d16316454bacde838d582ba274c0) -> `15 passed in
       0.62s`. SURVIVED.
    B3 needed no mutant, only a call: `assemble.gate_reason({'highway': 'residential', 'motor_vehicle': 'no',
       'surface': 'asphalt'})` -> `None`, where `Gates.swift:161` answers `.refused(.noAccess)`.

  WHAT CHANGED - four files, one new.

  1. BLOCKING 1, closed by `services/etl/tests/test_assemble_wiring.py` (NEW, 216 lines, one concern: what
  `record_from_row` read off which producer, asserted on the RAW record before `normalise_region` exists).
  `test_assemble.py` is 281 -> 299 and could not have carried it: it is at the cap, and every assertion in it
  is made on the table, where all five RANKED terms are already ranks. One hand-computed RAW value per ranked
  term, on named ways, with the arithmetic typed beside it:
    elevation_gain  way 800000007 [300,318,341,329,356,378,361,392] -> 18+23+27+22+31 = 121.0; also
                    800000009 = 48.0, 800000010 = 3.0 (one step up), 800000006 = 0.0 (seven steps of exactly
                    +0.5, none ABOVE the 0.5 noise floor).
    relief          way 800000007 392 - 300 = 92.0; 800000009 = 12.0, 800000010 = 150.0, 800000006 = 3.5.
    curvature       `curvature.way_curvature(<way 800000007's seven coordinates>, 800000007)` ->
                    476.08176703651884, the ONE call, made once outside the suite and recorded with its
                    decomposition: six segments, each an arm of the same zig-zag, each circumcircle radius
                    ~55.2766 m, which is band 3 of `curvature.LEVELS` (under 60, not under 30), weight 1.6;
                    4 * 49.591790115721246 + 2 * 49.59197196746963 = 297.55110439782424 m, * 1.6 =
                    476.0817670365188, the last digit being the summation order.
    furniture       way 800000005's three furniture nodes over `snap.length_m` of its seven coordinates,
                    132.14281164945845 m, recorded once from that call: 3 / 0.13214281164945845 km.
    sinuosity       the fifth ranked term and the only one READ rather than produced: 1.8 on way 800000007.
  No test in that file calls a producer to compute its own expectation - that would assert the wiring against
  itself and pass under M1. `test_the_mapped_terms_are_what_their_producers_return`'s docstring no longer
  claims the guard it cannot give; it says which four terms it covers and names the file that covers the five.

  2. RECORDABLE 1, TAKEN, and it is what makes (1) worth having. The fixture was nearly degenerate on the
  elevation axis: over a population of six, ways 800000003, 800000004, 800000007 and 800000008 held the SAME
  rank in `elevation_gain` and in `relief`, so M1 was a permutation of one ladder onto itself for four of the
  six and moved only two scores. TWO ROWS ADDED, at 8 -> 10 ways:
    800000009 `motor_vehicle=no` residential, profile [100,112,100,112,100,112,100,112]: gain 48.0, relief
              12.0 - much climbing, almost no range. It is also BLOCKING 3's fixture row.
    800000010 tertiary, profile [400,380,355,358,330,310,290,250]: gain 3.0, relief 150.0 - the reverse.
  EVERY TYPED RANK RE-DERIVED, and which moved and why, since a rank is a statement about its population:
    * elevation_gain and relief are ranked over a population of EIGHT (ten ways less the two zero classes,
      which are EXCLUDED and not dropped, normalise.py:33), so the ladder is (i + 0.5*1)/8 = 0.0625, 0.1875,
      0.3125, 0.4375, 0.5625, 0.6875, 0.8125, 0.9375. gain sorts 0.0(006) 3.0(010) 4.0(005) 48.0(009)
      51.0(003) 67.0(008) 84.0(004) 121.0(007); relief sorts 2.0(005) 3.5(006) 12.0(009) 51.0(003) 53.0(008)
      67.0(004) 92.0(007) 150.0(010). NO way now holds the same rank in both terms - the four that did are
      separated by 800000009 and 800000010 sorting between them - and both orders are asserted as tables, so
      a red run names the way that moved.
    * sinuosity is ranked over a population of SEVEN (eight, less the closed loop, which DECLINED), so
      `ANSWERING_SINUOSITY_RANKS` is no longer the fifths 0.1/0.3/0.5/0.7/0.9 the 23:45:11Z entry recorded:
      every one of those five moved, because the divisor went 5 -> 7 and the two new literals sort into the
      middle. It is now (i + 0.5*1)/7 over 1.02(006) 1.15(004) 1.25(010) 1.30(003) 1.45(008) 1.60(009)
      1.80(007), typed as the division rather than a transcribed decimal because sevenths do not terminate.
      The loop still holds `DECLINED_RANK` exactly, which the estimator cannot produce.
    * `curvature` and `furniture` are ranked over the same population of eight and their ranks moved too, but
      no test types a rank for either: they are pinned as RAW values, so there is nothing to re-derive.
    * the count line moved `ways=8 gated=2 points_of_interest_absent=8` -> `ways=10 gated=3
      points_of_interest_absent=10`. `gated=3` is the new `motor_vehicle=no` row; `zero_class=2` and
      `sinuosity_declined=1` are unchanged, and `null_score=0` is the one that must be zero.

  3. BLOCKING 2, closed three ways in the same new file. `test_the_restated_distance_defaults_are_score_pys_own`
  reads `inspect.signature(score.score).parameters` and asserts `DEFAULT_TUNNEL_M` and
  `DEFAULT_MOTORWAY_DISTANCE_M` ARE those defaults - anchored on the function object, because the claim the
  constants make is about what `score.score` does when the argument is left out, not about a line number.
  `test_a_row_that_omits_a_distance_field_takes_the_restated_default` asserts `math.inf` and `0.0` on the raw
  record of all six rows that omit both. `test_the_distance_literals_a_row_does_carry_reach_the_record_
  unchanged` pins way 800000008's 90.0 and way 800000007's 120.0 as READ, so a default cannot swallow a value
  that is in the row.

  4. BLOCKING 3, ported. `assemble.gate_reason` is now FOUR rules in `Gates.verdict`'s own order (:154, :156,
  :160, :161) answering THREE reasons, with `MOTOR_VEHICLE_KEY` / `MOTOR_VEHICLE_REFUSED` beside the two sets.
  One value and not a set: `motor_vehicle=destination` and `=permit` are NOT refused by `Gates.swift:161`, and
  widening it to `CLOSED_ACCESS` would make the corpus stricter than the router, which is the same drift in
  the other direction. `test_the_unported_gate_rules_are_counted_against_gates_verdict_and_not_described`
  COUNTS `return .refused(` in `Gates.swift` with the `//` lines dropped - code, never a comment - asserts it
  is 9, asserts 4 ported + 5 unported == 9, asserts the four ported keys are in `consideredTagKeys`, and
  asserts each of the five unported rules is still ALLOWED here. Porting or adding one without moving the
  count is now red.

  RED RUNS, each BY NAME, each restored; `git status --short` clean of source between them.
    RED 1 (BLOCKING 3, before the port, with the fixture row and the tests in place):
      cd services/etl && python -m pytest tests/test_assemble.py tests/test_assemble_wiring.py -rf --tb=line
      FAILED tests/test_assemble.py::test_the_count_line_names_every_absence
      FAILED tests/test_assemble_wiring.py::test_motor_vehicle_no_is_refused_as_no_access_the_way_gates_swift_refuses_it
      2 failed, 20 passed in 1.80s
    GREEN 1, after the port, same command: `22 passed in 0.75s`.
    RED 2 (BLOCKING 1) - M1 re-applied at the FIXED head (assemble.py md5 30ff6f8946debfcf112279e063124678 ->
      5b736ffefd76ec82f3b027d44879199a, restored to 30ff6f89 after 1.1 s):
      FAILED tests/test_assemble_wiring.py::test_the_ranked_terms_are_the_raw_numbers_their_producers_returned
      FAILED tests/test_assemble_wiring.py::test_the_gain_and_relief_ladders_are_not_one_ladder
      2 failed, 20 passed in 0.73s
      The same swap was `15 passed` at eff7f3c. The second failure is the fixture's own half of the answer.
    RED 3 (BLOCKING 2) - `DEFAULT_MOTORWAY_DISTANCE_M = 0.0` (md5 de6244e690147ad255c7d115543d1e76):
      FAILED tests/test_assemble_wiring.py::test_the_restated_distance_defaults_are_score_pys_own
      FAILED tests/test_assemble_wiring.py::test_a_row_that_omits_a_distance_field_takes_the_restated_default
      2 failed, 20 passed in 0.70s
    RED 4 (BLOCKING 2, the other restated default) - `DEFAULT_TUNNEL_M = 300.0` (md5
      ab78a2770acb2e8d0ed124c9a9fe97ba): the same two tests, `2 failed, 20 passed in 0.84s`.

  THE R5 CORRECTION, by this dated line and not by an edit to the entries that carry the wrong number. AT
  eff7f3c the record was false in three places: the module docstring's "five FURTHER rules", R5, and the
  STILL OPEN bullet all said FIVE unported, and the true count was SIX. `Gates.verdict` holds NINE refusal
  branches (Gates.swift:154, :156, :157, :158, :160, :161, :166, :169, :172); three were ported
  (`unpavedSurfaces`, `highway=track`, `closedAccess`); the six unported were `tracktype`, `smoothness`,
  `motor_vehicle=no`, a locked barrier, a ford and a refused `service` value - and `motor_vehicle=no` was
  missing from the enumeration entirely, which is why the wrong number read as right. AT THIS COMMIT the port
  in (4) makes it four ported and FIVE unported, so the sentence is true again, and it is no longer prose: the
  nine is counted in `Gates.swift` by a test.

  ACCEPTANCE BLOCK RE-RUN AT THIS COMMIT, whole, every gate bare, never piped into `tail`/`head` before a
  `&&`. The measured files are final; the only edit after these runs is this Log entry's own text, which no
  gate reads except `ops/queue-check`, re-run after it.

  ACCEPTANCE 1 - the closed-loop RED then green: unchanged by this fix and not re-demonstrated. The loop's
  `DECLINED_RANK` assertions are among the 22 below, and its rank did not move: it never had one.

  ACCEPTANCE 2 - the four `ops/sane` check-4 gates, each red by name first: the reds stand in the 23:39:52Z
  entry (RED 2 through RED 6); no gate code changed here except the ADDED `motor_vehicle` branch, whose own
  red by name is RED 1 above. All four gate tests are among the 22 below.

  ACCEPTANCE 3 - the whole ETL suite and every `wc -l`, RE-MEASURED at this commit:
    cd services/etl && python -m pytest tests -rs
    992 passed in 143.79s (0:02:23)
  985 -> 992 is the seven new tests in `test_assemble_wiring.py` and nothing else. No `short test summary
  info` section, so zero skips.
    cd services/etl && python -m pytest tests/test_assemble.py tests/test_assemble_wiring.py -rs
    22 passed in 0.67s
    wc -l services/etl/etl/assemble.py services/etl/tests/test_assemble.py \
          services/etl/tests/test_assemble_wiring.py services/etl/tests/fixtures/assembly_fixture.json \
          services/etl/etl/sinuosity.py
      273 services/etl/etl/assemble.py
      299 services/etl/tests/test_assemble.py
      216 services/etl/tests/test_assemble_wiring.py
      109 services/etl/tests/fixtures/assembly_fixture.json
       83 services/etl/etl/sinuosity.py
      980 total
  `assemble.py` 250 -> 273 (the R5 paragraph rewritten, the new rule and its two constants). `test_assemble.py`
  281 -> 299 - 1 line under the cap, which is why the new tests are a new file. The fixture 92 -> 109 (two
  rows and an `elevation_note`). `sinuosity.py` unchanged and re-quoted because the swap depends on it.

    cd services/etl && python -m etl.assemble --input tests/fixtures/assembly_fixture.json --out <scratch>
    ASSEMBLE ways=10 zero_class=2 gated=3 sinuosity_declined=1 points_of_interest_absent=10 null_score=0

  THE OTHER GATES, bare:
    bash ops/lib/check-line-cap
    P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines
    check-line-cap exit=0

    bash ops/queue-check
    QUEUE OK (175 tasks)
    queue-check exit=0

    bash ops/check-pins --source-only
    PINS ok=11 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only
    check-pins exit=0
  Every number is the review's own, unchanged: no Swift file, no pin and no queue task was added or removed
  by this fix, and the three new Python files are not Swift, so P-SRC-02's 71 does not move. `ops/queue-check`
  is the one gate that reads this file, and it was re-run after this entry was appended - `QUEUE OK (175
  tasks)`, exit 0 - with `state: claimed` and `reviewer: null` untouched, as instructed.

  STILL OPEN - what this fix did NOT do.
  * THE FIVE UNPORTED `Gates.verdict` RULES are still unported, which the review RULED correct for T-0146.
    They are now asserted as behaviour (allowed here, refused by ScenicKit) and counted against `Gates.swift`,
    not described. The review's RECORDABLE - file the port task and make it BLOCK T-0168's corpus write,
    because a corpus that scores a ford as scenic is a defect the moment it is written - is NOT done here: a
    new file under `queue/` is outside this task's `touches: [services/etl/etl/, services/etl/tests/]` and the
    pre-commit hook would reject it. It needs the panel, and it is the one open item with a deadline attached.
  * THE THREE LITERAL FIXTURE FIELDS. `sinuosity`, `tunnel_meters` and `meters_to_nearest_motorway` are still
    hand-typed, and the two new rows type `sinuosity` like every other row, so this fix made that item two
    rows larger. Regenerating the column from `sinuosity.way_sinuosity` re-derives the seven ranks above.
  * CLAUDE.md'S `ops/mutate` OBLIGATION for `assemble.py` is still not ruled on anywhere in this Log, exactly
    as the review recorded it. The four mutants above are a demonstration, not a population with a floor.
    Either rule `assemble.py` a wiring module or add it to T-0176; this fix did neither.
  * `test_gate_every_term_is_in_the_unit_interval` still can only catch a non-number; `metres()`'s `INFINITY`
    branch is still unobservable; R10's named refusals are still uneven (bare `KeyError` for a missing
    `coords` / `landcover_codes` / `elevation_profile` / `sinuosity`). None of the three is touched here.
  * The fixture is still hand-written and synthetic. No real extract (T-0168), no `points_of_interest`
    (T-0164), no 0..10 `scenic_score` column (T-0168/T-0171), and the `UNPAVED_SURFACES` copy is T-0181.
