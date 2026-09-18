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
