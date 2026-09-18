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
