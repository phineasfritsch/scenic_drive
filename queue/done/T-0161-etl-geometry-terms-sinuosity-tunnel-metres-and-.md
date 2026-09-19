---
id: T-0161
title: ETL geometry terms - sinuosity, tunnel metres and metres to the nearest motorway, from way geometry alone
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:52:32Z
lease_expires_at: 2026-09-19T03:52:32Z
worktree: .worktrees/T-0161
branch: task/T-0161
exclusive: []
touches: [services/etl/etl/sinuosity.py, services/etl/etl/proximity.py, services/etl/tests/test_sinuosity.py, services/etl/tests/test_proximity.py, services/etl/tests/test_proximity_bends.py, services/etl/tests/test_proximity_interior.py, services/etl/tests/fixtures/]
pins_affected: []
reviewer: agent/rv4-pr94
depends_on: [T-0154]
verify: [ops/test, ops/check-pins]
acceptance:
  - "WHAT IS NEW, AND THAT NOTHING OLD MOVED. Three code commits. 69f1d8c built the two modules: `6 files changed, 889 insertions(+)`, five of them `create mode 100644` and the sixth this task file, which the commit MODIFIES. The round-2 commit added fixture cases and tests across four files plus this one. ROUND 4 ADDS ONE NEW FILE AND ELEVEN LINES OF FIXTURE, EDITS NO CODE AND CHANGES NO EXISTING TEST: `services/etl/tests/test_proximity_interior.py` (new, 178 lines, 4 tests, one concern) and `services/etl/tests/fixtures/geometry_bends_fixture.json` 67 -> 78 lines (one motorway case appended and one sentence added to its `note`), plus this task file, whose `touches:` gains the new test path. `services/etl/etl/proximity.py` is UNCHANGED for the THIRD round running - rounds 1, 2 and 3 all judged the shipped code correct and all three blocking findings were holes in the fixture, the third of them a hole the round-3 record had itself ruled unreachable - and so are sinuosity.py, score.py, snap.py, curvature.py, byways.py, test_proximity.py, test_sinuosity.py and geometry_terms_fixture.json, all bit-identical to 71a6a83, and `services/etl/tests/test_proximity_bends.py` is bit-identical to c0dfe1a. `git status --short` at the final commit prints nothing. `wc -l` at the final commit: sinuosity.py 83, proximity.py 143, test_sinuosity.py 178, test_proximity.py 300, geometry_terms_fixture.json 263, test_proximity_bends.py 278, geometry_bends_fixture.json 78, test_proximity_interior.py 178 - all at or under the 300-line cap, and `awk 'END{print NR}'` prints 300, 178, 278 and 178 for the four test files, which is the count the cap is measured by"
  - "THE WHOLE SUITE, re-run at the final commit. `cd services/etl && python -m pytest tests -rs` -> `608 passed`, exit 0. Zero failures, zero skips - `-rs` prints no short-summary section at all, and `grep -c 'short test summary'` over the captured output prints 0. The COUNT and the exit status are the claim; the wall time is not one and is not stable on this box, and this tree read `608 passed in 102.10s (0:01:42)`. 136 of the 608 are this task's four files (`python -m pytest tests/test_proximity.py tests/test_sinuosity.py tests/test_proximity_bends.py tests/test_proximity_interior.py` -> `136 passed`; `--collect-only -q` -> `tests/test_proximity.py: 60`, `tests/test_proximity_bends.py: 24`, `tests/test_proximity_interior.py: 4`, `tests/test_sinuosity.py: 48`). 608 minus 136 is 472, which is exactly the count T-0154's acceptance block recorded for the suite it left behind: round 4 added 6 tests - the four in the new file, plus two parametrized ids the new fixture case gives the two per-case tests already in `test_proximity_bends.py` - and changed no existing test's meaning"
  - "`bash ops/lib/check-pipe-consumers` (bare, nothing piped into it) -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0"
  - "`bash ops/queue-check` (bare) -> `QUEUE OK (158 tasks)`, exit 0. `state: claimed` and `reviewer: null` are unchanged; the reviewer of this task is not its owner and will not be a subagent of this session"
  - "REPRODUCED BEFORE ANYTHING WAS TOUCHED. Round 4's blocking finding is the reviewer's P1 mutant - `line_distance_m` restricted to `min(segment_distance_m(line[i], line[i+1], other[j], other[j+1]) for i in range(n) for j in range(m) if i in (0, n-1) or j in (0, m-1))`, the interior-interior segment pairs dropped - and it was reproduced at 0bc238f (c0dfe1a plus the reviewer's entry, tree clean) BEFORE the fixture or the new test file was opened: applied ALONE to `proximity.py`, `python -m pytest tests/test_proximity.py tests/test_sinuosity.py tests/test_proximity_bends.py` -> `130 passed in 0.93s`, exit 0, NOTHING RED, against a control of `130 passed in 1.08s` on the same three files; `services/etl/etl/__pycache__` purged before every pytest run and 1.1 s slept before each write, the original bytes written back, md5 re-read `254632996234f9bd1c1e130db0244bea` and `git status --short` empty. ROUND 3's reproductions, kept for the record: that finding was one root cause with two reproductions, and both were reproduced at 71a6a83 with that reviewer's own mutants, each applied ALONE to `proximity.py` and restored byte-for-byte: O1 (`tunnel_meters` -> `length_m([coords[0], coords[-1]])`) -> `108 passed in 0.43s` on the two test files and `580 passed in 70.61s` on the whole suite, no named test red; O2 (`line_distance_m`'s candidate loop -> `[(other[0], other[-1])]`) -> `108 passed in 0.26s` and `580 passed in 66.87s`, no named test red. Controls `108 passed in 0.46s` before and `108 passed in 0.27s` after, and `git status --short` carried nothing but this task file. `services/etl/etl/__pycache__` was purged before EVERY pytest invocation and the driver sleeps 1.1 s before writing - round 2's recordable 3: the .pyc header stores the source mtime in WHOLE SECONDS, so a mutate-restore inside one second leaves stale bytecode that pytest imports and reports a false green. Rounds 1 and 2 reproduced their own findings at 61a0f6c and those counts are in the Log"
  - "RED BY NAME AT THE FINAL TREE. ROUND 4's three mutants, each applied ALONE and restored byte-for-byte with the md5 re-read after every restore, run over the FOUR test files, `__pycache__` purged before every pytest run and 1.1 s slept before every write, control `136 passed in 0.79s`. P1, the reviewer's (the interior-interior pairs dropped) -> `3 failed, 133 passed in 1.09s`: `tests/test_proximity_interior.py::TestNearestApproachInteriorToBothPolylines::test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines`, `...::test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold` and `tests/test_proximity_bends.py::TestNearestApproachOffTheChord::test_the_metres_to_the_nearest_motorway_match_the_fixture[nearest_approach_interior_to_both_polylines]`. N4, MY OWN NEIGHBOUR and not the reviewer's - the same comprehension keeping only `j in (0, m-1)`, so every pair whose MOTORWAY segment is interior is dropped -> `3 failed, 133 passed in 6.75s`, the same three names. F2, a FIXTURE mutant and the only way the structural guard can be seen red at all, since no code mutant can reach it: `geometry_bends_fixture.json` exactly as it stood at c0dfe1a, round 4's case removed -> `4 failed, 130 passed in 1.43s`, the two named tests above plus BOTH guards, `tests/test_proximity_interior.py::TestInteriorPairShape::test_some_motorway_case_has_its_minimum_at_a_pair_interior_to_both_polylines` and `::test_the_interior_case_matrix_is_the_one_its_workings_types_out` - the guard is red on the fixtures as the last round reviewed them and green with the new case, which is the whole of its claim. `proximity.py` md5 back to `254632996234f9bd1c1e130db0244bea` and the fixture's back to `5b8263ec58a6403841e79fdf286b57ff` after each, `git status --short` carrying nothing but the round-4 paths. ROUND 3's table, kept for the record and NOT restated as a claim about this tree, whose control is 136 and not 130 - five code mutants and one fixture mutant over the three files as they stood at c0dfe1a, control `130 passed in 0.30s` before and `130 passed in 0.24s` after: O1 -> `5 failed, 125 passed in 0.24s`; O2 -> `3 failed, 127 passed in 0.30s`; N1 (`tunnel_meters` sums every segment but the last) -> `15 failed, 115 passed in 0.31s`; N2 (`line_distance_m` walks only the way's FIRST AND LAST segments) -> `2 failed, 128 passed in 0.44s`, both failures in the new file, so N2 was green on the suite as it was reviewed and is a genuine survivor of it; N3 (`segment_distance_m` drops both candidate-endpoint terms) -> `8 failed, 122 passed in 0.28s`. The structural guard that no code mutant can reach was demonstrated red against a FIXTURE mutant, F1, which puts the kinked bore's interior node and the V motorway's apex back ON their chords - exactly the shape round 2 found: `6 failed, 16 passed in 0.10s` on the new file, including `TestFixtureShape::test_no_multi_node_geometry_is_collinear_unless_it_is_named` and `TestFixtureShape::test_some_motorway_case_needs_an_interior_vertex_of_the_candidate`. Every failing test is named in the Log's round-3 table. Round 2's ten mutants were red by name at c5a3538 against the two files as they stood then and that table stays in the Log; it is NOT restated as a claim about this tree, whose control is 130 and not 108"
  - "EVERY EXPECTED VALUE IS TYPED OUT AND NONE COMES FROM THE CODE IT CHECKS. The fixture's `workings` field carries the arithmetic per case, and the round-2 numbers were settled with a scratch calculator under `.build-scratch-T0161/` (gitignored by the `.build-*/` rule, not committed) that imports nothing from `etl/` and writes out the spherical law of cosines and the flat factors itself. What it printed: `0.0001 deg meridian = 11.122983322959863`, `0.002 = 222.45966645919725`, `0.003 = 333.6894996887959`, `0.03 = 3336.8949968879583`, `111320*cos(37.495deg) = 88322.00731942503`, `0.0011323 * that = 100.00700888778496`, `0.0566 * that = 4999.025614279457`, `hypot(100.00700889, 552.7) = 561.6748986973528`, `0.00135 * 110540 = 149.229`, `0.00137 * 110540 = 151.4398`, `CASE A LINE MIN = 100.0070088878274` against `first motorway segment only = 4999.025614280254`, `CASE B LINE MIN = 100.0070088878274` against `first way segment only = 4999.025614280254`, `3-node unequal: seg1 2224.5966651497265 seg2 1112.2983303665126 total 3336.894995516239`, `under: 222.45963417307252`, `over: 333.6895120686278`, `inside min = 149.22900000028312`, `outside min = 151.43980000028387`, and `gap 11.122679686212527 path 4223.177983475064 raw ratio 379.69069528362303` ROUND 3 used the same kind of scratch calculator (`services/etl/work/T-0161/calc.py`, under the gitignored `services/etl/work/` rule, not committed), which imports nothing from `etl/` and writes out the spherical law of cosines and the flat factors itself. What it printed: `6373000*pi/180 = 111229.83322959862`; kinked bore legs `161.05218685226583` and `161.05157088880296`, path `322.10375774106876`, chord `284.74838365197985`; switchback legs `205.01898472467474` and `135.31187217317827`, path `340.330856897853`, chord `72.29944495517711`; bent-under legs `125.97062385859606` and `125.97026590279613`, path `251.94088976139219`, chord `222.45967472089902`; the V motorway `full = 100.0070088878274` against `chord = 4999.025614280254` with `motorway[:2]` and `motorway[1:]` both `100.0070088878274`; the U way `full = 99.48600000003353`, `chord = 1105.3999999999069`, `first and last segments only = 1240.503829769365`; and `0.0009 * 110540 = 99.486`. ROUND 4 used the same kind of scratch calculator (`services/etl/work/T-0161/calc4.py`, under the gitignored `services/etl/work/` rule, not committed), which imports nothing from `etl/` and writes out the flat projection itself. What it printed for the new case - the whole per-pair matrix, way segment i x motorway segment j - `i=0 [2069.787581, 2083.699146, 3701.099603]`, `i=1 [406.484208, 99.486000, 888.629160]`, `i=2 [888.629160, 99.486000, 406.484208]`, `i=3 [3701.099603, 2083.699146, 2069.787581]`; `argmin over ALL pairs: (99.48600000003353, 1, 1)` with `every cell attaining it: [(1, 1), (2, 1)]` - both interior x interior; `P1 (drop interior-interior) minimum: 406.4842081198996` and `N4 (keep only j on the boundary) minimum: 406.4842081198996`; `0.0009 * 110540 = 99.486`; `foot from motorway n1 onto way segment s1: metres 406.4842081198996 t 0.7211147242319178`; `way chord -> 2210.8000000002794` and `mot chord -> 2310.286000000313`, both past MOTORWAY_SEARCH_RADIUS_M; and the cross-track of every interior node off its own chord, 1105.40 / 2111.31 / 1105.40 for the way and 2210.80 / 2210.80 for the motorway, all far past the bends guard's MIN_CROSS_TRACK_M = 10.0. The 99.486 is typed at abs 0.001 rather than the 0.05 the round-4 brief suggested, because the value reproduces to 1e-11 and the tighter bound is the one the arithmetic supports"
  - "NOT RUN HERE, and why. `ops/test` and `ops/check-pins` were not run on this box: the default swift scratch path does not build inside a worktree here and both wrap swift, exactly as the task instructed. `verify:` still names them; CI decides them. `gh pr checks 94` is read once after the push and reported back with the PR"
  - "NOT IN THIS TASK, unchanged from the Brief: the way record, the region rank-normaliser that maps raw sinuosity into score.py's 0..1 term, and the `scenic_score` column (all T-0163); the tag-table terms (T-0162); any spatial index over candidate motorways (the caller narrows the set - stated in the module docstring and under STILL OPEN); any multiplier or threshold, which stay in score.py alone. Changing the SHAPE of the declined sinuosity answer is a seam change across T-0163 and T-0146 and is under STILL OPEN rather than taken here. No serial-only file was touched and both `pins/floor_*.txt` are unchanged"
---
## Brief

One of three disjoint pieces T-0146 was split into by the 2026-09-18 13:13 panel (CODE lens, grounded). The
seam already exists and is code: `services/etl/etl/score.py` takes keyword-only `sinuosity`, `tunnel_meters`
(default 0.0) and `meters_to_nearest_motorway` (default `math.inf`) (score.py:119-122). Nothing under
`services/etl/etl/` produces any of the three. All three need only tags and coordinates - no raster, no
container - so they are built and tested on the Windows box (`cd services/etl && python -m pytest tests -rs`).

**Build, editing NOTHING that exists** (read `snap.py`: `length_m` at :106, `distance_to_line_m` at :58):
1. `sinuosity.py` - RAW sinuosity of a way: path length over the straight-line distance between its
   endpoints, as an unbounded value >= 1.0 (the region normaliser, T-0163, maps it to 0..1; do not normalise
   here). A closed way or coincident endpoints is its own named case, never a division by zero and never a
   silently huge number: decide the rule, say it in the docstring, pin it with a test.
2. `proximity.py` - `tunnel_meters(way)`: metres of the way tagged as tunnel (`tunnel=yes|building_passage|
   ...` - enumerate the OSM values you accept as a named constant and pin the set against literals; `tunnel=no`
   is NOT a tunnel). `meters_to_nearest_motorway(way, motorways)`: the minimum distance from the way's
   geometry to any motorway/motorway_link/trunk/trunk_link geometry, `math.inf` when none is within a stated
   search radius. The plan's thresholds (tunnel > 300 m x0.15; within 150 m of a motorway x0.7, plan:85) live in
   score.py ALREADY - do not restate them here; this task produces metres, not multipliers.
3. Fixtures: small committed geometries with hand-checkable answers (a straight line, a right-angle dog-leg
   whose sinuosity is sqrt(2) to the digit, a way parallel to a motorway at a typed-out offset, a way that
   crosses one). Expected values typed out from arithmetic you show in a comment, NEVER computed by the
   function under test.

**Owner's rulings, so the Log starts from them:** distances are metres on the same spherical model snap.py
uses (import it; do not add a second earth radius); the zero classes themselves still get values (the scorer
zeroes them, this module does not gate); a way with fewer than two coordinates REFUSES by name.

**The author rule (it took PR #89 through review in one round):** rule every place the plan, score.py and
snap.py disagree in your Log BEFORE writing code; re-run and quote the whole acceptance block at your FINAL
commit; close your own verifier's findings before the review is bought. Every new test demonstrated RED by
name (three mutations of each new module nobody else will write), then green. No number in prose that a
command did not print.

## Log
- 2026-09-18T20:20:00Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
- 2026-09-18T19:52:32Z claimed by agent/claude-opus-5; lease until 2026-09-19T03:52:32Z
- 2026-09-18T19:59:34Z read end to end before writing anything, by agent/claude-opus-5 (owner and author):
  CLAUDE.md; the plan's `Score per way` block (plan:75-93); `services/etl/etl/score.py` whole (the consumer:
  `score(... sinuosity=, tunnel_meters=0.0, meters_to_nearest_motorway=math.inf)` at :119-122, the two
  boundaries at :61-64, the non-finite rejections at :133-136); `snap.py` whole (`point_to_segment_m` :43,
  `distance_to_line_m` :58, `overlap_m` :72, `length_m` :106); `curvature.distance_on_earth` (:31, with
  `RAD_EARTH_M = 6373000` at :21); `byways.SCENIC_ZERO_CLASSES` (:111); `tagfilter.WAY_CLASSES` (:14);
  `tests/test_snap.py` whole, for the house style of a tolerance that is typed out rather than taken from the
  constant under test (test_snap.py:78-92). No sibling's file was opened or imported: T-0162 and T-0163 are
  building in their own worktrees and the seam between us is score.py's keyword names, not each other's code.
- 2026-09-18T20:00Z RULINGS, all nine settled before the first line of module code was written. Every one is
  a place the Brief, the plan, score.py, snap.py or OSM's own tag semantics disagree or say nothing.
  - R1. WHAT A `way` IS AT THIS SEAM. The Brief writes `tunnel_meters(way)`; there is no way record under
    `services/etl/etl/` and the way record is T-0163's (its `touches:`, not mine). RULED: the functions take
    `coords` and `tags` as separate arguments, the shape `curvature.way_curvature(coords)` and
    `terrain.summarise(coords, profile)` already use. Duck-typing a `.coordinates` / `.tags` record would be
    a seam that imports cleanly and does not fit, and the seam this task was given is score.py's keyword
    names - `sinuosity`, `tunnel_meters`, `meters_to_nearest_motorway` - which the three function names match.
  - R2. THE SINUOSITY FUNCTION'S NAME. The module is `sinuosity.py` and the keyword is `sinuosity=`.
    RULED: `sinuosity.way_sinuosity(coords)`, after `curvature.way_curvature(coords)`, which is the same
    relation to score.py's `curvature=` keyword. `sinuosity.sinuosity` would have been the other option and
    has no precedent here.
  - R3. SNAP.PY CARRIES TWO EARTH MODELS AND THE OWNER'S RULING NAMES ONE. `point_to_segment_m` (snap.py:45-47)
    is a flat local projection, 111320*cos(lat) by 110540; `length_m` (:106-108) and the one-point branch of
    `distance_to_line_m` (:61) are `curvature.distance_on_earth`, spherical with R = 6373000. The owner's
    ruling says "the same spherical model snap.py uses (import it; do not add a second earth radius)".
    RULED: LENGTHS ALONG a way - sinuosity's numerator and denominator, tunnel metres - are `snap.length_m`,
    the spherical one. DISTANCES BETWEEN geometries are `snap.point_to_segment_m`, the flat one, because it
    is the only point-to-line distance snap has and it is what snap itself measures a tolerance with. This
    module introduces no constant of its own, which is what the ruling forbids. The two models are NOT
    interchangeable and the difference is recorded rather than assumed: the fixture case
    `nearest_point_inside_a_long_way_segment` is 55.27 m flat and 55.61 m spherical (`0.0005 deg * ky` and
    `0.0005 deg gc`, printed side by side by the scratch calculator), 0.6% apart, which is why that case's
    tolerance is 0.01 m against the flat value and why this ruling exists at all.
  - R4. THE CLOSED WAY. The plan names the term (plan:86) and says nothing about a way whose endpoints are
    one point; score.py would reject `inf` outright once normalised (`out_of_range` refuses a non-finite
    term, score.py:104). RULED: `CLOSED_WAY_SINUOSITY = 1.0`, the floor of the raw scale, for any way whose
    ends are within `CLOSED_ENDPOINT_M = 10.0` metres of each other - the width of a road junction, absolute
    rather than a fraction of the way's length so the rule reads the same for a 40 m cul-de-sac and a 40 km
    loop. Not `inf`, not a large number: T-0163 rank-normalises this inside a region, so a lasso reported at
    its raw 840 would take the top of the region's range away from every genuinely sinuous road. A loop's
    curviness is carried by `curvature.way_curvature`, which weighs 0.45 against this term's 0.15 and
    measures a loop perfectly well. The under-claim is deliberate and is in the docstring.
  - R5. THE TUNNEL VALUE SET. The Brief writes `tunnel=yes|building_passage|...` and leaves the tail to me;
    the plan says only "tunnel >300 m" (plan:85). OSM's `tunnel` key also carries `no`, `culvert`, `flooded`
    and `avalanche_protector`. RULED, as an allowlist of the values that mean a driver on THIS way is
    enclosed: `TUNNEL_VALUES = {yes, building_passage, avalanche_protector}`. `no` is excluded because it is
    how a mapper records that a way is NOT a tunnel - any `"tunnel" in tags` or truthiness test gets it
    backwards, which is mutation P1 below. `culvert` is excluded because it belongs to the waterway running
    through the pipe, not to the road over it, and honouring it on a highway would take a scenic lane to
    x0.15 for a drainage pipe. `flooded` is excluded for the same reason in reverse: it describes water, not
    a road being driven, and a flooded way is the routing profile's safety business. `covered=yes` is a
    different key and is not read. Widening this set is a decision with a constant and a test, not an edit.
  - R6. THE MOTORWAY CLASS SET IS IMPORTED. The Brief lists motorway/motorway_link/trunk/trunk_link; plan:83
    lists the same four; `byways.SCENIC_ZERO_CLASSES` (byways.py:111) IS those four and score.py imports it
    rather than copying it, for the reason stated at score.py:23-27. RULED: `MOTORWAY_CLASSES` is that
    import, and `tests/test_proximity.py` pins it against the four literals. The risk of importing runs the
    other way here and is worth naming: the constant is called ZERO_CLASSES because it is about scoring 0,
    and this module uses it for "what counts as a motorway to be near". They are the same four values today;
    the literal pin is what turns a change of meaning there into a red test here instead of a quietly wider
    penalty in the corpus.
  - R7. THE SEARCH RADIUS. The Brief requires "a stated search radius"; the plan states none; score.py owns
    the 150 m the answer is compared against (score.py:63). RULED: `MOTORWAY_SEARCH_RADIUS_M = 1000.0`, a
    REPORTING limit and not a threshold - nothing is pruned, the metres simply stop being a fact about this
    way - and inclusive at the boundary. Neither number is restated in the module or in the assertion: the
    test asserts `MOTORWAY_SEARCH_RADIUS_M >= 2 * score.MOTORWAY_PROXIMITY_M`, so if the scorer's boundary
    ever moves up to the radius, this goes red and the relation gets decided again instead of the radius
    silently deciding the multiplier.
  - R8. POLYLINE TO POLYLINE, NOT SAMPLED. snap has no polyline-to-polyline distance: `distance_to_line_m`
    is point-to-line (:58) and `overlap_m` judges midpoints of pieces at most `SAMPLE_STEP_M = 25.0` long
    (:40, :89-95), an error bound of +/-12.5 m. RULED: this term is not sampled. 12.5 m is 8% of the 150 m
    boundary and a crossing way would read up to 12.5 m instead of 0. So every segment of the way is
    measured against every segment of the candidate, from both ends, and a proper crossing is detected
    separately and returns 0.0. The crossing predicate is decided on the raw (lon, lat) numbers with no
    earth model at all: the projection to metres multiplies x by 111320*cos(lat) and y by 110540, a diagonal
    map with a positive determinant, and that cannot change the SIGN of a cross product. Collinear and
    touching pairs are deliberately NOT proper crossings and fall through to the endpoint distances, which
    already answer 0.0 for them (pinned by `test_a_collinear_pair_falls_through_to_the_endpoints`).
  - R9. WHERE THE REFUSAL LIVES. The owner's ruling is that a way with fewer than two coordinates refuses by
    name; snap.py's own choice for that input is to RETURN (`overlap_m` returns `0.0, 0.0`, snap.py:81-82)
    and snap.py may not be edited by this task. RULED: one refusal, `sinuosity.require_geometry(coords,
    caller)`, raising `ValueError` naming the caller and the count - the repo's convention (counts.py:29,
    streetview.py:73), not a new exception class. `proximity` imports it instead of writing a second message
    for one rule, and the candidate motorways are refused the same way, naming which one (`motorway[1]`).
    The mutation that makes it stop refusing is caught by seven named tests across both files (S3 below).
  - R10, from the Brief's third owner ruling, recorded because it is implemented by ABSENCE and a reader
    cannot see absence: neither module gates on `highway`. A motorway way gets real metres and a real
    sinuosity here; score.py zeroes it at :139. The only place `highway` is read is `is_motorway`, which
    selects the candidates a way is measured AGAINST. Pinned by
    `TestTheZeroClassesAreNotGatedHere::test_a_motorway_s_own_geometry_still_gets_both_terms`.
- 2026-09-18T20:07:55Z RED FIRST. With both new modules moved out of the tree and the tests, the fixture and
  nothing else in place, `cd services/etl && python -m pytest tests -rs`:
  `E   ImportError: cannot import name 'proximity' from 'etl'` / `E   ImportError: cannot import name
  'sinuosity' from 'etl'` / `!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection
  !!!!!!!!!!!!!!!!!!!` / `2 errors in 1.71s`. That is red by FILE, not by test name; the red-by-name
  demonstration is the mutation table below, which puts 26 named failures on the board across six
  mutations. Both modules were restored from a pristine copy kept outside the tree
  (`services/etl/work/T-0161/pristine/`, gitignored) - `git checkout --` cannot restore a file git has never
  seen, which is why the copy exists.
- 2026-09-18T20:09Z GREEN, the whole suite: `554 passed in 56.80s`, zero skips, zero errors.
- 2026-09-18T20:14:12Z MUTATION TABLE. Six mutations nobody else will write, three per new module, each
  applied ALONE and restored before the next (`diff -q` against the pristine copies printed
  `BOTH_RESTORED`, and `git status --short` showed only the five untracked files of this task). Each run
  below is `python -m pytest <file(s)> --tb=no -rf`.

  | # | module | mutation, applied alone | run | named tests that went red |
  |---|--------|-------------------------|-----|---------------------------|
  | S1 | sinuosity.py | the `gap <= CLOSED_ENDPOINT_M` branch of `way_sinuosity` deleted, so the ratio is always divided out | `5 failed, 36 passed in 0.12s` | `TestCases::test_the_sinuosity_matches_the_fixture[closed_loop_rectangle]`, `...[near_closed_lasso]`, `TestCases::test_no_case_is_below_the_floor[closed_loop_rectangle]`, `TestRawNotNormalised::test_a_lasso_is_declined_rather_than_credited`, `TestRawNotNormalised::test_a_closed_loop_does_not_divide_by_zero` |
  | S2 | sinuosity.py | `CLOSED_ENDPOINT_M = 10.0` -> `0.0` (the exactly-repeated node still caught, the lasso no longer) | `4 failed, 37 passed in 0.14s` | `TestConstants::test_the_closed_threshold_is_a_real_distance`, `TestCases::test_closedness_matches_the_fixture[near_closed_lasso]`, `TestCases::test_the_sinuosity_matches_the_fixture[near_closed_lasso]`, `TestRawNotNormalised::test_a_lasso_is_declined_rather_than_credited` |
  | S3 | sinuosity.py | `require_geometry`: `if n < MIN_COORDINATES` -> `if n < 0`, so a one-node way returns a plausible 1.0 instead of refusing | `7 failed, 75 passed in 1.24s` (both test files) | `test_sinuosity.py::TestRefusal::test_a_one_coordinate_way_refuses_by_name`, `::test_an_empty_way_refuses_by_name`, `::test_the_gap_refuses_on_its_own_name`, `::test_the_refusal_names_its_caller`, `test_proximity.py::TestRefusal::test_a_one_coordinate_way_refuses_by_name_before_the_tags_are_read`, `::test_a_one_coordinate_way_refuses_the_motorway_distance_by_name`, `::test_a_degenerate_candidate_refuses_and_says_which_one` |
  | P1 | proximity.py | `is_tunnel` -> `return "tunnel" in tags`, the key-presence test the docstring forbids | `5 failed, 36 passed in 0.16s` | `TestTunnelValues::test_a_non_string_value_is_not_a_tunnel`, `TestTunnelCases::test_the_tunnel_metres_match_the_fixture[tunnel_no_is_not_a_tunnel]`, `...[tunnel_culvert_is_refused]`, `TestTunnelCases::test_is_tunnel_agrees_with_the_metres[tunnel_no_is_not_a_tunnel]`, `...[tunnel_culvert_is_refused]` |
  | P2 | proximity.py | the `_crosses` branch of `segment_distance_m` deleted, so a crossing is measured from its endpoints | `3 failed, 38 passed in 0.17s` | `TestSearchRadius::test_the_radius_is_inclusive`, `TestMotorwayCases::test_the_metres_to_the_nearest_motorway_match_the_fixture[crossing_a_motorway]`, `TestSegmentGeometry::test_a_crossing_is_zero_where_every_endpoint_is_hundreds_of_metres_away` |
  | P3 | proximity.py | `segment_distance_m` minimises over the way's two endpoints only, dropping the candidate's - node sampling by another name | `2 failed, 39 passed in 0.13s` | `TestMotorwayCases::test_the_metres_to_the_nearest_motorway_match_the_fixture[nearest_point_inside_a_long_way_segment]`, `TestSegmentGeometry::test_the_nearest_point_may_be_inside_a_long_segment_of_either_line` |

  No survivors, so nothing was added to close a hole. One test WAS added after the table, on R10's account:
  `TestTheZeroClassesAreNotGatedHere::test_a_motorway_s_own_geometry_still_gets_both_terms`, which takes
  `tests/test_proximity.py` from 41 tests to 42 (`tests/test_sinuosity.py` is 41; `83 passed in 0.52s` over
  the two files together). It is not one of the tests any mutation above was caught by, and the six mutation
  runs were not repeated for it.
- 2026-09-18T20:14Z STILL OPEN, and deliberately not done here.
  - `ops/test` and `ops/check-pins` were NOT run on this box, as instructed: the default swift scratch path
    does not build inside a worktree here, and both wrap swift. `verify:` still names them, and
    `gh pr checks` is read once after the push - recorded in the acceptance block, whatever it says.
  - No spatial index. `meters_to_nearest_motorway` measures every candidate handed to it, so it is
    O(way segments x candidate segments) and the CALLER must narrow the candidate set (the corpus carries an
    R-tree over segments). Stated in the module docstring too. Handing it a whole region's motorways would
    be quadratic and that is not a bound this module enforces.
  - Nothing calls either module yet. The way record and the region rank-normaliser that would map raw
    sinuosity into score.py's 0..1 term are T-0163; the tag-table terms are T-0162. score.py is untouched by
    this task and its keyword names are the whole of the contract between us.
  - `tunnel_meters` is all-or-nothing per way because `tunnel=` is a way tag. A road that enters a tunnel
    halfway along is two ways in OSM; where it is not, the metres are wrong in the data and not here.
  - The R5 tag-semantics rulings (`avalanche_protector` in, `culvert` and `flooded` out) are judgements about
    what OSM values mean, not measurements. If a region's curated data ever carries a drivable
    `tunnel=flooded`, it is one constant and one fixture case.
  - No serial-only file was touched: both `pins/floor_*.txt` are unchanged and are not in `touches:`.
- 2026-09-18T20:19Z acceptance block filled in from runs made AFTER the code commit (69f1d8c) and against
  it, so every output quoted there is a fact about the tree this PR ships: the suite at 20:17:16Z,
  `check-pipe-consumers` and `queue-check` straight after it, each run bare with nothing piped into it. This
  second commit changes this file only. `state: claimed` and `reviewer: null` are untouched - the review is
  somebody else's, and not a subagent of this session (MEMORY: reviewer != owner, same session).
- 2026-09-18T20:41:32Z **Record corrections from the read-only verification of this build, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. The verifier reproduced the code, the tests, the mutation table and the
  gates; these are text.** (a) Acceptance line 1 said all six paths of 69f1d8c were `create mode 100644`;
  `git show --summary 69f1d8c` prints five creates, and the sixth path is this task file, which the commit
  modifies. Corrected in the acceptance block. (b) The 20:00Z entry says "RULINGS, all nine"; ten are listed
  (R1-R10), R10's pinning test was by that entry's own words added after the mutation table, and rulings, code
  and tests landed in ONE commit, so git cannot show that the rulings came first (T-0163 committed its rulings
  separately, which is the form to copy). The entry stays as written. (c) Fixture `parallel_100_m_east`:
  `100 / 88322.007` is 0.0011322, not 0.0011323 - the fixture's offset is that value rounded UP, and the 7 mm
  it then measures is the rounding, not the projection. The `workings` prose is corrected; no coordinate and
  no expected value changed, and the JSON still parses. (d) `test_sinuosity.py`'s docstring called two cases
  exact; only the two-node way is, the hairpin is asserted at rel=1e-8. Corrected. (e) NOT changed, on a
  measurement: the verifier read the dog-leg gap as 1573.0274; `python -c "print(round(2**0.5*1112.2983,4))"`
  prints 1573.0273, which is what the fixture says.
- 2026-09-18T21:34:07Z REVIEW ROUND 1 - FAIL, by agent/rv1-pr94 (not the owner, not a subagent of the owner's session). Reviewed 61a0f6c in a detached worktree (.worktrees/rv1-pr94, removed; nothing written in .worktrees/T-0161). Acceptance re-run and reproduced: whole suite `555 passed in 118.32s`, zero skips, exit 0; `83 passed` over the two new files with 41 + 42 collected; `bash ops/lib/check-pipe-consumers` -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`; `bash ops/queue-check` -> `QUEUE OK (158 tasks)`; `git show --summary 69f1d8c` -> five creates plus this file modified, as corrected. `ops/test`/`ops/check-pins` not run (swift); `gh pr checks 94` read once -> `core pass 2m17s`, `pins-source-only pass 1m10s`. Three fixture arithmetics re-done independently: 6373000*0.01*pi/180 = 1112.2983322959863, sqrt(2)*1112.2983 = 1573.0273 (confirming correction (e)), 100/(111320*cos(37.495)) = 0.0011322206 (confirming correction (c)), plus 441.6100366, 55.27, 884.8946 and the spherical 55.6149166.
  SIX mutations nobody wrote, each alone and restored. THREE SURVIVED with no named test red, and each turns a plan multiplier off: (1) `line_distance_m` restricted to the candidate's first segment -> `83 passed`, and a 3-node motorway whose second segment closes to 100 m reads `inf` instead of 100.007 - the x0.7 lost; (2) `meters_to_nearest_motorway` taking the last candidate instead of the minimum -> `83 passed`, and [near, far] reads `inf` instead of 100.007 (the fixture only ever orders [far, near]); (3) `tunnel_meters` restricted to the first segment -> `83 passed`, and a 5-node 1112 m tunnel reads 55.615, under score.TUNNEL_THRESHOLD_M - the x0.15 lost. Root cause of all three: every polyline in `motorway_cases` and every way in `tunnel_cases` has exactly two nodes, so R8's own sentence ("every segment of the way is measured against every segment of the motorway") is asserted by nothing. Two mutations were CAUGHT and are worth recording as real pins: mixing earth models in the sinuosity ratio -> 10 named tests red; making `tunnel_meters` gate on `is_motorway` -> `TestTheZeroClassesAreNotGatedHere::test_a_motorway_s_own_geometry_still_gets_both_terms` red, so the CLAUDE.md motorway invariant is genuinely held.
  Rulings: R3, R5, R6, R8, R9, R10 upheld; the 0.6% between the two earth models is 0.94 m at score.py's 150 m boundary and cannot drift unseen (the 55.27 case is pinned at abs=0.01 against a spherical 55.6149). R4 upheld in direction, disputed in shape and recorded: 1.0 is indistinguishable from a straight two-node way, so T-0163 cannot exclude declined ways from the rank population; `is_closed_way` is public and nothing says to use it. Recordables: CLOSED_ENDPOINT_M unpinned over (10, 22.2] (10.0 -> 20.0 is green); the PR body still carries the retracted "all create mode"; no fixture case near the 150 m boundary; neither earth model is WGS84-true at this latitude.
  Nothing in the PR was changed. `state:` and `reviewer:` left as they are; the task stays in queue/claimed/ for a second round.
- 2026-09-18T21:39:07Z **ROUND 2 - the review's three BLOCKING findings and three of its recordables closed.
  Fixer working for the owner, in .worktrees/T-0161 on task/T-0161.** `state: claimed` and `reviewer: null`
  are unchanged. The shipped CODE was judged correct in all three blocking findings and
  `services/etl/etl/proximity.py` is NOT edited in this round: what was missing was a check that could ever
  tell, so what this round ships is fixture cases and tests.

  REPRODUCED FIRST, at 61a0f6c, before anything was touched. Each mutant applied ALONE and restored, with
  `cd services/etl && python -m pytest tests/test_proximity.py tests/test_sinuosity.py --tb=no` between:
  control `83 passed in 0.24s`; **M1** (`line_distance_m`'s candidate loop -> `zip(other[:2], other[1:2])`)
  `83 passed in 0.30s`; **M2** (`nearest = line_distance_m(coords, motorway)`, the last candidate winning)
  `83 passed in 0.32s`; **M3** (`length_m(coords[:2])` in `tunnel_meters`) `83 passed in 0.30s`; **M4**
  (`CLOSED_ENDPOINT_M = 20.0`) `83 passed in 0.34s`; control again `83 passed in 0.29s`. All four reproduce
  exactly as reported - green, no named test red - and `git status --short` printed nothing after each
  restore. Nothing was dropped and nothing failed to reproduce.

  WHAT WAS ADDED. Nine fixture cases, six tests and one docstring paragraph; no function changed. The
  fixture: `just_open_by_eleven_metres` (the rectangle 0.0001 deg = 11.1230 m short of closing, asserted
  OPEN); `tunnel_multi_segment_is_the_whole_way` (3 nodes, legs 0.02 and 0.01 deg, 2224.5967 + 1112.2983 =
  3336.8950 m); `tunnel_three_node_under_the_threshold` (2 * 111.2298 = 222.4597 m) and
  `tunnel_four_node_over_the_threshold` (3 * 111.2298 = 333.6895 m);
  `motorway_nearest_on_its_later_segment` and `way_nearest_on_its_later_segment` (the 3-node dog-leg against
  the 2-node line, both ways round, 0.0011323 * 88322.007 = 100.007 m, with the first segment 0.0566 *
  88322.007 = 4999.03 m away and past the radius); `two_motorways_nearest_first` (the [near, far] order);
  `just_inside_the_scorer_s_proximity_boundary` (0.00135 * 110540 = 149.229 m) and
  `just_outside_the_scorer_s_proximity_boundary` (0.00137 * 110540 = 151.4398 m). Every expected value is
  typed out from the arithmetic in its own `workings` and was settled with a calculator under
  `.build-scratch-T0161/` (gitignored, not committed) that imports nothing from `etl/` and writes out the
  spherical law of cosines and the flat factors itself. What it printed, against what the fixture claims:
  `0.0001 deg meridian = 11.122983322959863`, `0.002 = 222.45966645919725`, `0.003 = 333.6894996887959`,
  `0.03 = 3336.8949968879583`, `111320*cos(37.495deg) = 88322.00731942503`, `0.0011323 * that =
  100.00700888778496`, `0.0566 * that = 4999.025614279457`, `hypot(100.00700889, 552.7) = 561.6748986973528`,
  `0.00135 * 110540 = 149.229`, `0.00137 * 110540 = 151.4398`; and, walked pair by pair, `CASE A LINE MIN =
  100.0070088878274` with `first motorway segment only = 4999.025614280254`, `CASE B LINE MIN =
  100.0070088878274` with `first way segment only = 4999.025614280254`, `3-node unequal: seg1
  2224.5966651497265 seg2 1112.2983303665126 total 3336.894995516239`, `under: 222.45963417307252`, `over:
  333.6895120686278`, `inside min = 149.22900000028312`, `outside min = 151.43980000028387`, and the eleven-
  metre rectangle at `gap 11.122679686212527 path 4223.177983475064 raw ratio 379.69069528362303`.

  THE RULING THE THIRD FINDING NEEDED - WHAT "TUNNEL METRES" MEANS WHEN ONLY PART OF A WAY IS THE BORE.
  `tunnel=` is a tag on the WAY, not on a stretch of its geometry, so the answer is the way's WHOLE length,
  every segment of it, and there is no such thing here as a partly-tunnelled way: a road that enters a
  tunnel halfway along is two ways in OSM, and where a mapper did not split it the metres are wrong in the
  data and not in this module. That was already the module docstring's position; what it was not was
  checked, because all seven tunnel cases were the same two-node way. It is now pinned by
  `TestTunnelLength::test_a_multi_segment_tunnel_is_measured_end_to_end` on a 3-node way with DELIBERATELY
  UNEQUAL legs, so measuring the first segment (2224.5967) and measuring the last (1112.2983) are two
  different visible failures against the whole 3336.8950.

  RED BY NAME, at the final tree, each mutant applied ALONE and restored byte-for-byte (the driver writes
  the original bytes back and re-reads them rather than `git checkout --`, so an uncommitted edit elsewhere
  in the file cannot be lost). Control `108 passed in 0.55s` before and `108 passed in 0.56s` after.

  | # | mutant, applied alone | RED run | failures by name |
  |---|---|---|---|
  | M1 | `proximity.line_distance_m`: `zip(other, other[1:])` -> `zip(other[:2], other[1:2])` | `2 failed, 106 passed in 0.64s` | `TestMotorwayCases::test_the_metres_to_the_nearest_motorway_match_the_fixture[motorway_nearest_on_its_later_segment]`, `TestMultiSegmentGeometry::test_the_nearest_approach_may_be_on_a_later_segment_of_the_motorway` |
  | M2 | `proximity.meters_to_nearest_motorway`: `nearest = line_distance_m(coords, motorway)` | `2 failed, 106 passed in 0.59s` | `TestMotorwayCases::test_the_metres_to_the_nearest_motorway_match_the_fixture[two_motorways_nearest_first]`, `TestMultiSegmentGeometry::test_the_candidate_order_cannot_change_the_answer` |
  | M3 | `proximity.tunnel_meters`: `length_m(coords)` -> `length_m(coords[:2])` | `5 failed, 103 passed in 0.63s` | `TestTunnelCases::test_the_tunnel_metres_match_the_fixture[tunnel_multi_segment_is_the_whole_way]`, `[tunnel_three_node_under_the_threshold]`, `[tunnel_four_node_over_the_threshold]`, `TestTunnelLength::test_a_multi_segment_tunnel_is_measured_end_to_end`, `TestTunnelLength::test_the_metres_fall_either_side_of_the_threshold_score_cuts_at` |
  | M4 | `sinuosity.CLOSED_ENDPOINT_M = 10.0` -> `20.0` | `3 failed, 105 passed in 0.61s` | `TestConstants::test_the_closed_threshold_is_pinned_from_both_sides`, `TestCases::test_closedness_matches_the_fixture[just_open_by_eleven_metres]`, `TestCases::test_the_sinuosity_matches_the_fixture[just_open_by_eleven_metres]` |
  | N1 | MINE, neighbour of M1: `line_distance_m`'s WAY loop -> `zip(line[:2], line[1:2])` | `2 failed, 106 passed in 0.52s` | `TestMotorwayCases::test_the_metres_to_the_nearest_motorway_match_the_fixture[way_nearest_on_its_later_segment]`, `TestMultiSegmentGeometry::test_the_nearest_approach_may_be_on_a_later_segment_of_the_way` |
  | N2 | MINE, neighbour of M3: `tunnel_meters` -> `length_m(coords[-2:])` (the LAST segment) | `5 failed, 103 passed in 0.50s` | the same five as M3 |
  | N3 | MINE, neighbour of M1: `segment_distance_m` drops `point_to_segment_m(d, a, b)` | `2 failed, 106 passed in 0.53s` | the same two as M1 |
  | N4 | MINE: `snap.point_to_segment_m`'s `ky = 110540.0` -> `111234.7` (the spherical metres per degree) | `5 failed, 103 passed in 0.67s` | `TestMotorwayCases::test_the_metres_to_the_nearest_motorway_match_the_fixture[nearest_point_inside_a_long_way_segment]`, `[just_inside_the_scorer_s_proximity_boundary]`, `[just_outside_the_scorer_s_proximity_boundary]`, `TestSegmentGeometry::test_the_nearest_point_may_be_inside_a_long_segment_of_either_line`, `TestProximityBoundary::test_the_metres_fall_either_side_of_the_proximity_score_cuts_at` |
  | S1 | MINE: `is_closed_way` -> `<= CLOSED_ENDPOINT_M / 2`, drifting from the guard inside `way_sinuosity` | `2 failed, 106 passed in 0.61s` | `TestCases::test_closedness_matches_the_fixture[near_closed_lasso]`, `TestTheDeclinedAnswerAndTheRankPopulation::test_is_closed_way_is_true_exactly_where_a_non_straight_way_reads_the_floor` |
  | S2 | MINE: `way_sinuosity`'s declined answer -> `CLOSED_WAY_SINUOSITY + 1e-07` | `6 failed, 102 passed in 0.56s` | `TestCases::test_the_sinuosity_matches_the_fixture[closed_loop_rectangle]`, `[near_closed_lasso]`, `TestRawNotNormalised::test_a_lasso_is_declined_rather_than_credited`, `TestRawNotNormalised::test_a_closed_loop_does_not_divide_by_zero`, `TestTheDeclinedAnswerAndTheRankPopulation::test_the_floor_is_returned_for_a_loop_and_for_a_straight_way_alike`, and the second test of that class |

  N1-N4, S1 and S2 are six mutations the review did not write. N1, N2, N3 were first checked AGAINST THE
  SHIPPED SUITE at 61a0f6c and all three were GREEN there (`83 passed in 0.27s`, `83 passed in 0.42s`,
  `83 passed in 0.33s`), so they are neighbours that survived and not mutants the round-1 suite already
  caught; S1 and S2 were already caught there (`1 failed, 82 passed` and `4 failed, 79 passed`) and are
  carried only because they are what makes the two new seam tests red by name. N4 was applied to
  `services/etl/etl/snap.py`, which is NOT in `touches:`: it was restored byte-for-byte, is not in the diff,
  and `git status --short` at the commit lists only the four files this round edits.

  The one new check no code mutant reaches, `TestFixture::test_no_geometry_in_the_fixture_is_only_two_nodes`,
  was demonstrated red against the fixture this PR was reviewed with - `git show HEAD:...geometry_terms_fixture.json`
  swapped in, `python -m pytest tests/test_proximity.py::TestFixture tests/test_sinuosity.py::TestFixture
  --tb=no -rf` -> `3 failed, 4 passed in 0.10s`, naming
  `TestFixture::test_no_geometry_in_the_fixture_is_only_two_nodes` and both files'
  `TestFixture::test_the_shapes_that_matter_are_all_present` - then the fixture restored and `cmp` clean.

  RECORDABLES. (1) TAKEN, at the source seam rather than in the value: `way_sinuosity` still returns the
  floor and the ruling stands (the floor, never `inf`), but `sinuosity.py`'s docstring now says in one
  sentence that a caller ranking this value MUST use the public `is_closed_way` to keep declined ways out of
  the rank population, and `TestTheDeclinedAnswerAndTheRankPopulation` pins the contract that makes that
  possible - `is_closed_way` is true exactly where a non-straight geometry reads the floor. (2) TAKEN:
  `just_open_by_eleven_metres` plus `test_the_closed_threshold_is_pinned_from_both_sides` close the free
  band, which was (10, 22.2] and is now [5.03, 11.12). (3) TAKEN: the PR body is rewritten from this head
  and no longer carries the retracted "all `create mode`" sentence. (4) TAKEN as one sentence here: NEITHER
  earth model is WGS84-true at 37.5 deg - a real meridian degree is about 110996 m against the flat 110540
  and the spherical 111234.7 - so the 0.6% is a choice between two approximations and not a gap between a
  wrong model and a right one; a later reader should not "fix" the flat model toward the spherical one
  believing it is the truth. (5) TAKEN: the two boundary cases above put score.py's 150 m cut between two
  named cases, and N4 shows the 0.94 m between the two earth models is now visible at that cut rather than
  only at 55 m. (6) and (7) need no change and are answered under STILL OPEN.
- 2026-09-18T21:39:07Z STILL OPEN after round 2.
  - A CALLER THAT RANKS SINUOSITY MUST CALL `is_closed_way` AND LEAVE THE CLOSED WAYS OUT OF THE RANK
    POPULATION, because `way_sinuosity` returns exactly 1.0 both for a way that declined to answer and for a
    genuinely straight two-node way and the value alone cannot say which it is. This is T-0163's to act on:
    it is stated here and in `sinuosity.py`'s docstring, and nothing in this module can enforce it.
  - The shape of the declined answer is unchanged and is still an under-claim: a real mountain loop is
    credited nothing on this term, and its curviness is carried by `curvature.way_curvature` at 0.45 against
    this term's 0.15. Changing the shape (a `None`, a second return) is a seam change across T-0163 and
    T-0146 and is not one test, so it is not taken here.
  - `is_motorway` is exported and is NOT called by `meters_to_nearest_motorway`: the caller is trusted to
    have filtered the candidates. Recordable 6, recorded, no change - it is the documented contract.
  - No spatial index, unchanged from round 1: every candidate handed in is measured and the caller narrows
    the set.
  - `ops/test` and `ops/check-pins` were again NOT run on this box (both wrap swift; the default scratch
    path does not build inside a worktree here). CI decides them; `gh pr checks 94` is read once after the
    push.
  - Recordable 7 (the whole-suite wall time differing between boxes) is not a fact about the tree and needs
    nothing.
- 2026-09-18T21:48Z Acceptance block re-run at c5a3538, the round-2 commit, and one line corrected for it.
  `cd services/etl && python -m pytest tests -rs` -> `580 passed in 81.23s (0:01:21)`, exit 0, zero skips
  (`grep -c 'short test summary'` over the captured output prints 0); `python -m pytest
  tests/test_proximity.py tests/test_sinuosity.py` -> `108 passed in 0.47s`; `--collect-only -q` ->
  `tests/test_proximity.py: 60` and `tests/test_sinuosity.py: 48`; `wc -l` 83 / 143 / 178 / 300 / 263 and
  `awk 'END{print NR}' services/etl/tests/test_proximity.py` -> 300; `git status --short` empty at c5a3538.
  Every COUNT quoted in the block reproduced. The one quantity that did not was the whole-suite WALL TIME -
  70.21s at 21:39:07Z against the identical tree, 81.23s at c5a3538 - so that line now states the count and
  the exit status as the claim and carries both readings as evidence instead of one of them as a fact. This
  commit changes this file only; `state: claimed` and `reviewer: null` are untouched.
- 2026-09-18T22:32:13Z REVIEW ROUND 2 - FAIL, by agent/rv2-pr94 (not the owner, not the round-1 reviewer, not the fixer, not the orchestrator). Reviewed 71a6a83 in a detached worktree (.worktrees/rv2-pr94, removed at the end; `git worktree list` no longer lists it; nothing written in .worktrees/T-0161, whose `git status --short` is empty). SCOPE: `git diff --name-status 61a0f6c..HEAD` is five modified paths and no creates or deletes - the task file, one five-line docstring paragraph in `sinuosity.py`, the fixture, and the two test files; `proximity.py` and `snap.py` are absent from the diff, as claimed. ACCEPTANCE RE-RUN, every count reproduced: `python -m pytest tests -rs` -> `580 passed in 57.66s`, exit 0, no short-summary section at all (zero skips); `python -m pytest tests/test_proximity.py tests/test_sinuosity.py` -> `108 passed in 0.26s` with `--collect-only -q` giving `60` and `48`; `wc -l` 83 / 143 / 178 / 300 / 263 and `awk 'END{print NR}' services/etl/tests/test_proximity.py` -> 300; `bash ops/lib/check-pipe-consumers` bare -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)` exit 0; `bash ops/queue-check` bare -> `QUEUE OK (158 tasks)` exit 0; `git status --short` empty at 71a6a83. Wall time is not a claim and the block is right not to make it one: I read 57.66s, 56.42s, 58.80s, 60.05s and 62.14s for the same 580 tests. `ops/test` and `ops/check-pins` not run (swift); `gh pr checks 94` read once -> `core pass 2m35s`, `pins-source-only pass 1m6s`.
  ALL FOUR round-1 survivors re-applied ALONE at this head and each is now RED BY NAME, matching the round-2 table exactly: M1 -> `2 failed, 106 passed`, `TestMotorwayCases::test_the_metres_to_the_nearest_motorway_match_the_fixture[motorway_nearest_on_its_later_segment]` + `TestMultiSegmentGeometry::test_the_nearest_approach_may_be_on_a_later_segment_of_the_motorway`; M2 -> `2 failed, 106 passed`, `[two_motorways_nearest_first]` + `TestMultiSegmentGeometry::test_the_candidate_order_cannot_change_the_answer`; M3 -> `5 failed, 103 passed`, the three `TestTunnelCases` ids plus both `TestTunnelLength` tests; M4 -> `3 failed, 105 passed`, `TestConstants::test_the_closed_threshold_is_pinned_from_both_sides` + both `[just_open_by_eleven_metres]` ids. Controls `108 passed` before and after; `git status --short` empty after every restore. Arithmetic re-done on a calculator importing nothing from `etl/`: `6373000*0.02*pi/180 = 2224.5966651497265` and `*0.01 = 1112.2983303665126`, summing to `3336.894995516239` (fixture 3336.895 at abs 0.001); `111320*cos(37.495deg) = 88322.00731942503`, `*0.0011323 = 100.00700888778495` and `*0.0566 = 4999.025614279456`; `0.00135*110540 = 149.229` and `0.00137*110540 = 151.4398`; `6373000*0.0001*pi/180 = 11.122983322959863`; walked pair by pair, CASE A and CASE B both `100.0070088878274` against `4999.025614280254` for the first segment alone. Every figure the round-2 entry quotes reproduces.
  ONE BLOCKING FINDING, a mutant class the fix brief did not name. Round 1's B1/B3 asked for polylines with >= 3 nodes and cases either side of 300 m, and this round delivered exactly that - along the NODE-COUNT axis only. All ten `tunnel_cases` geometries lie on a single meridian (`distinct lon 1` for every one, the three new ones included), and replacing every polyline in the twelve `motorway_cases` by its first-to-last chord leaves all twelve answers bit-identical, so no case here has its nearest approach at an interior vertex. Consequence, each applied ALONE and restored, `__pycache__` purged before every run: `tunnel_meters` -> `length_m([coords[0], coords[-1]])` gives `580 passed`, and a 322 m bore with one ordinary kink (sinuosity 1.1312) reads `284.7484` m instead of `322.1038` m, dropping score.py's x0.15 - the cut is crossed by any bore whose path is in `(300, 300 x sinuosity]` m; `line_distance_m`'s candidate loop -> the candidate's chord gives `580 passed`, and a motorway whose nearest approach is its middle node reads `inf` instead of `100.0070088878274` m, dropping the x0.7. Nothing outside the two test files imports either module, so `580 passed` is the whole population that could have gone red. Fixture-only to close, as in round 1: one non-collinear tunnel whose chord falls on the other side of the 300 m cut, and one V- or U-shaped candidate, each with the assertion `TestMultiSegmentGeometry` already makes about `motorway[:2]`.
  RULINGS: I UPHOLD the declined-answer ruling - the floor keeps its shape, and the guard is adequate because `way_sinuosity`'s internal test and the public `is_closed_way` are the same expression, now pinned to each other by the biconditional test and pinned as a constant from both sides by `[5.03, 11.12)`. Carried to T-0163's brief: the declined value 1.0 is this module's raw FLOOR and simultaneously score.py's unit CEILING (`score.UNIT_TERMS` contains `sinuosity`), so a normaliser that passes raw through gives every roundabout the maximum credit and no range check can see it. Recordables: `111234.7` is not `6373000*pi/180` (it is `111229.83322959862`) and is repeated from round 1 in prose only - every derived claim, the 0.94 m at the boundary included, is unaffected; and a `__pycache__` note for the next mutation driver, since a mutate-restore inside one second leaves a stale `.pyc` that can report a mutant as surviving.
  Nothing in the PR was changed. `state:` and `reviewer:` left as they are; the task stays in queue/claimed/ for a third round.
- 2026-09-18T23:00Z ROUND 3 FIX by agent/claude-opus-5 (the owner), against review round 2's single
  blocking finding. THE RULE DISAGREEMENTS, ruled before a line was written. (1) The fix brief puts the new
  tests in `tests/test_proximity_bends.py`, which was NOT in `touches:`; `services/etl/tests/fixtures/` was,
  so the new fixture needed nothing. `touches:` therefore gains `services/etl/tests/test_proximity_bends.py`
  in this commit, and the pre-commit hook enforces the list from the same file that declares it. Recorded
  rather than widened quietly: the addition is one new test file and nothing else moved into scope. (2) The
  brief allows the fixture to split "if it grows past reason" and it had to - `geometry_terms_fixture.json`
  is 263 lines, six more cases put it past the 300-line cap, and `test_proximity.py` is AT 300. So round 3
  adds two files and edits NEITHER of the two the cap was already binding on: `test_proximity.py` and
  `geometry_terms_fixture.json` are bit-identical to 71a6a83. (3) The brief names a neighbouring mutant,
  "`line_distance_m` dropping the segment-to-segment term for interior-interior pairs". I did not write it,
  because it is EQUIVALENT and no fixture can catch it: in the plane the minimum distance between two
  disjoint segments is always attained at an endpoint of at least one of them, and every interior segment's
  endpoints are also endpoints of the first or the last segment, so dropping interior-interior pairs cannot
  change the answer. N2 below is the honest neighbour in that area instead - the way's FIRST AND LAST
  segments only, which a 4-node way can see and a 3-node one cannot. (4) The brief asks for a switchback
  bore; the reviewer's switchback lies on one meridian, which the new structural guard flags as collinear,
  so the case here is drawn 0.0005 deg off the meridian and is a hairpin that also bends.
  REPRODUCED FIRST, at 71a6a83, nothing else touched. O1 (`tunnel_meters` -> `length_m([coords[0],
  coords[-1]])`) applied ALONE: `108 passed in 0.43s` on `tests/test_proximity.py tests/test_sinuosity.py`
  and `580 passed in 70.61s` on `python -m pytest tests -rs`, no named test red. Restored, md5 back to
  `254632996234f9bd1c1e130db0244bea`. O2 (`line_distance_m`'s `zip(other, other[1:])` -> `[(other[0],
  other[-1])]`) applied ALONE: `108 passed in 0.26s` and `580 passed in 66.87s`, no named test red.
  Controls `108 passed in 0.46s` before and `108 passed in 0.27s` after; `git status --short` carried only
  this task file throughout. Every pytest invocation was preceded by deleting `services/etl/etl/__pycache__`
  and the driver sleeps 1.1 s before writing either the mutant or the original back, which is round 2's
  recordable 3 taken: the .pyc header records the source mtime in whole seconds.
  WHAT CHANGED - TESTS AND FIXTURE ONLY, and `proximity.py` is untouched for the second round running.
  `services/etl/tests/fixtures/geometry_bends_fixture.json` (new, 67 lines) carries six cases, every one of
  them with a bend and with its arithmetic typed out in `workings` from the spherical law of cosines
  (R = 6373000) and the flat 111320*cos(lat) / 110540 factors:
  `tunnel_kinked_bore_over_the_threshold_only_along_its_path`
  (the reviewer's 322 m bore, path 322.1038 m over score.TUNNEL_THRESHOLD_M, chord 284.7484
  m under it - the case that flips the x0.15 at sinuosity 1.1312), `tunnel_switchback_bore_doubles_back`
  (path 340.3309 m, chord 72.2994 m), `tunnel_bent_bore_under_the_threshold` (the control: path 251.9409 m
  and chord 222.4597 m, both UNDER the cut, so the pair cannot pass by accident of where 300 m sits),
  `motorway_nearest_at_its_middle_node` (the reviewer's V candidate: 100.0070 m at its apex, 4999.03 m by
  its chord - and BOTH of its segments touch the apex, so `motorway[:2]` and `motorway[1:]` each still
  answer 100.0070 and the subset cases in the other fixture cannot see this failure),
  `way_nearest_at_its_middle_node` (the mirror, a different line of the same function) and
  `way_bends_toward_the_motorway_between_its_end_nodes` (a 4-node U whose MIDDLE segment runs 99.4860 m from
  a 176 m motorway stub while both outer segments are 1240.5038 m away and its chord is 1105.40 m away -
  past MOTORWAY_SEARCH_RADIUS_M, so an implementation that walks only the outer segments answers inf).
  `services/etl/tests/test_proximity_bends.py` (new, 278 lines, 22 tests, one concern: a polyline is the sum
  or the minimum over its SEGMENTS and never its chord) holds them, plus `TestFixtureShape` - the structural
  guard the brief asked for. It measures every geometry of 3+ nodes in BOTH fixtures against its own
  first-to-last chord, with its own flat-projection cross-track written out in the test file rather than
  imported from the module it guards, and fails by name if any of them deviates by less than
  MIN_CROSS_TRACK_M = 10.0 m. The three meridian geometries that are deliberately straight are named in
  `COLLINEAR_BY_DESIGN` with the subset failure each one is there for, and the list is pinned from both
  sides: every name in it exists and every one of them really is collinear. It fails SAFE - a new straight
  case is red until somebody puts its name on the list on purpose.
  RED BY NAME AT THE FINAL TREE, over the three test files, control `130 passed in 0.30s` before and
  `130 passed in 0.24s` after, each mutant applied ALONE and restored with its md5 re-read.
  O1 -> `5 failed, 125 passed in 0.24s`, every failure in the new file:
  `TestBentTunnelBores::test_the_bore_measures_its_path_and_not_its_chord` at all three ids,
  `TestBentTunnelBores::test_a_bent_bore_crosses_the_threshold_only_along_its_path` and
  `TestBentTunnelBores::test_the_bent_bore_under_the_threshold_is_under_it_by_either_measure`.
  O2 -> `3 failed, 127 passed in 0.30s`, every failure in the new file:
  `TestNearestApproachOffTheChord::test_the_metres_to_the_nearest_motorway_match_the_fixture[motorway_nearest_at_its_middle_node]`,
  `TestNearestApproachOffTheChord::test_the_nearest_approach_may_be_at_an_interior_node_of_the_motorway` and
  `TestFixtureShape::test_some_motorway_case_needs_an_interior_vertex_of_the_candidate`.
  MY OWN THREE NEIGHBOURS, none of them the reviewer's. N1 `tunnel_meters` -> `length_m(coords[:-1])` (every
  segment but the last) -> `15 failed, 115 passed in 0.31s`, ten of them in `test_proximity.py` including
  `TestTunnelLength::test_a_multi_segment_tunnel_is_measured_end_to_end` and five in the new file. N2
  `line_distance_m` -> `for a, b in [(line[0], line[1]), (line[-2], line[-1])]` (the way's first and last
  segments only) -> `2 failed, 128 passed in 0.44s`, BOTH in the new file:
  `TestNearestApproachOffTheChord::test_the_metres_to_the_nearest_motorway_match_the_fixture[way_bends_toward_the_motorway_between_its_end_nodes]`
  and `TestNearestApproachOffTheChord::test_the_way_may_bend_toward_the_motorway_between_its_end_nodes` - so
  N2 is a survivor of the suite as it was reviewed and the 4-node way is the only geometry in either fixture
  that can see it. N3
  `segment_distance_m` -> `min(point_to_segment_m(a, c, d), point_to_segment_m(b, c, d))` (the candidate's
  own endpoints dropped) -> `8 failed, 122 passed in 0.28s`, four in `test_proximity.py` (including
  `TestSegmentGeometry::test_the_nearest_point_may_be_inside_a_long_segment_of_either_line`) and four in the
  new file. F1, a FIXTURE mutant, is how the structural guard was seen red: it puts the kinked bore's
  interior node and the V motorway's apex back ON their chords - the shape round 2 found - and gives
  `6 failed, 16 passed in 0.10s` on the new file alone, including
  `TestFixtureShape::test_no_multi_node_geometry_is_collinear_unless_it_is_named` and
  `TestFixtureShape::test_some_motorway_case_needs_an_interior_vertex_of_the_candidate`. Restored, with the
  md5 re-read after each; `git status --short` empty of every mutant afterwards.
  RECORDABLES from round 2. (1) UPHELD and carried: the declined-sinuosity ruling stands and the sharper
  reason - the declined 1.0 is this module's raw FLOOR and simultaneously score.py's unit CEILING, so a
  normaliser that passes raw through gives every roundabout maximum credit and no range check can see it -
  is T-0163's and is repeated under STILL OPEN below. (2) TAKEN, corrected once and not carried a third
  time: `111234.7` is NOT `6373000*pi/180`; the value is `111229.83322959862`, and no derived claim moves -
  the flat/spherical gap at the 150 m boundary is `150 * (111229.833/110540 - 1) = 0.936` m, which is the
  0.94 m already quoted. (3) TAKEN as the driver's method above. (4) and (5) need no change: the 1 mm
  tolerances pin THIS implementation's earth model, which is what the `workings` say, and
  MOTORWAY_SEARCH_RADIUS_M is still asserted by its relation to score.MOTORWAY_PROXIMITY_M alone.
- 2026-09-18T23:00Z STILL OPEN after round 3.
  - Unchanged from round 2 and still T-0163's: a caller that RANKS sinuosity must call `is_closed_way` and
    leave the declined ways out of the rank population. Round 2's reviewer sharpened why - the raw floor 1.0
    and score.py's unit ceiling 1.0 are the same number, so a normaliser that passes the raw value through
    gives every roundabout the MAXIMUM credit and no range check can see it.
  - The shape of the declined answer is unchanged and is still an under-claim; changing it is a seam change
    across T-0163 and T-0146 and is not one test, so it is not taken here.
  - `is_motorway` is exported and is NOT called by `meters_to_nearest_motorway`: the caller filters the
    candidates. No spatial index either - every candidate handed in is measured.
  - THE MUTANT CLASS THAT CANNOT BE CLOSED BY A FIXTURE, stated so round 4 does not hunt for it: dropping
    the interior-interior segment pairs from `line_distance_m` is an equivalent mutant in the plane, because
    the minimum distance between two disjoint segments is always attained at an endpoint of one of them and
    every interior segment's endpoints belong to the first or the last segment too. It is not a hole.
  - `ops/test` and `ops/check-pins` were again NOT run on this box (both wrap swift; the default scratch
    path does not build inside a worktree here). CI decides them; `gh pr checks 94` is read once after the
    push.
- 2026-09-18T23:25Z Acceptance block re-run at 474d0ad, the round-3 commit. `git status --short` empty at
  474d0ad; `wc -l` 83 / 143 / 178 / 300 / 263 / 278 / 67 for sinuosity.py, proximity.py, test_sinuosity.py,
  test_proximity.py, geometry_terms_fixture.json, test_proximity_bends.py and geometry_bends_fixture.json,
  with `awk 'END{print NR}'` 300 / 178 / 278 for the three test files; `cd services/etl && python -m pytest
  tests -rs` -> `602 passed in 62.98s (0:01:02)`, exit 0, and `grep -c 'short test summary'` over the
  captured output prints 0; `python -m pytest tests/test_proximity.py tests/test_sinuosity.py
  tests/test_proximity_bends.py` -> `130 passed in 0.35s`; `--collect-only -q` -> `tests/test_proximity.py:
  60`, `tests/test_proximity_bends.py: 22`, `tests/test_sinuosity.py: 48`; `bash
  ops/lib/check-pipe-consumers` bare -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57
  scanned, 58 tracked, floor 42)`, exit 0; `bash ops/queue-check` bare -> `QUEUE OK (158 tasks)`, exit 0.
  Every COUNT quoted in the block reproduced and no line needed correcting. The only quantity that moved is
  the whole-suite WALL TIME - 60.71s before the commit against 62.98s at it - which the block already
  carries as evidence and not as a claim. This commit changes this file only, and this file is not one the
  block measures, so nothing is re-measured by it; `state: claimed` and `reviewer: null` are untouched.
- 2026-09-18T23:19:36Z **Record corrections from the read-only verification of the round-3 fix, closed before round 3 is bought -
  agent/claude-fable-5-1 (orchestrator), for the owner. The verifier re-applied O1 and O2 to a copy (5 and 3
  named failures, exactly the names claimed), matched proximity.py's and the bends fixture's md5 to the
  fixer's, ran the whole suite with bytecode writing off, and found the tree clean throughout; these are
  text.** (a) The round-3 entry and PR #94's body say `TestFixtureShape` measures "every 3+-node geometry in
  BOTH fixtures"; `geometries_of()` walks `tunnel_cases` and `motorway_cases` (and their nested motorways)
  only - `sinuosity_cases` are not scanned. Their geometry is the sinuosity term's own subject and is
  asserted by value; the guard's scope is as the code says, not as the sentence said. (b) rv2's recordable 2
  (the printed constant 111234.7; correctly 111229.83322959862) was corrected in the Log, and the wrong
  figure still stands as PROSE in `geometry_terms_fixture.json` line 236's `workings` - that file was left
  bit-identical to 71a6a83 on purpose; no value depends on it. (c) "rv2's entry appended verbatim": present as
  the first appended block; no independent copy exists for a byte comparison (the orchestrator holds the
  reviewer's text at `.artifacts/signoffs/rv2-pr94-logentry.md`, gitignored). (d) The `touches:` line gained
  `services/etl/tests/test_proximity_bends.py`, disclosed in the round-3 entry as a ruled scope addition.


- 2026-09-18T23:31:53Z REVIEW ROUND 3 - FAIL, by agent/rv3-pr94 (not the owner, not the round-1 or round-2 reviewer, not the fixer, not the orchestrator). Reviewed c0dfe1a in a detached worktree (.worktrees/rv3-pr94, removed at the end; `git worktree list` no longer names it; nothing was written in .worktrees/T-0161, whose `git status --short` is empty at c0dfe1a).
  SCOPE. `git diff 71a6a83..c0dfe1a --stat` -> `3 files changed, 490 insertions(+), 6 deletions(-)`: this task file plus the two new files. `proximity.py`, `test_proximity.py` and `geometry_terms_fixture.json` are absent from the diff, so they are bit-identical to 71a6a83 as claimed.
  ACCEPTANCE RE-RUN AT c0dfe1a, every count reproduced. `cd services/etl && python -m pytest tests -rs` -> `602 passed in 96.40s (0:01:36)`, exit 0, `grep -c 'short test summary'` over the captured output `0`; `python -m pytest tests/test_proximity.py tests/test_sinuosity.py tests/test_proximity_bends.py` -> `130 passed in 0.62s`; `--collect-only -q` -> `tests/test_proximity.py: 60`, `tests/test_proximity_bends.py: 22`, `tests/test_sinuosity.py: 48`; `wc -l` 83 / 143 / 178 / 300 / 263 / 278 / 67 with `awk 'END{print NR}'` 300 / 178 / 278; `bash ops/lib/check-pipe-consumers` bare -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0; `bash ops/queue-check` bare -> `QUEUE OK (158 tasks)`, exit 0; `git status --short` empty. Wall time is again not a claim and the block is right not to make one: 96.40s clean against 63.89s for the same 602 tests with a mutant applied, same box, same session. `ops/test` / `ops/check-pins` not run (both wrap swift). `gh pr checks 94` read once at the end -> `core pass 2m21s`, `pins-source-only pass 1m0s`.
  ROUND 2's FINDING IS CLOSED. O1 and O2 re-applied ALONE at this head, `__pycache__` purged before every pytest run and 1.1 s slept before each write, md5 back to `254632996234f9bd1c1e130db0244bea` and `git status --short` empty after each; control `130 passed in 0.50s` before and `130 passed in 0.43s` after. O1 -> `5 failed, 125 passed in 0.55s`: `TestBentTunnelBores::test_the_bore_measures_its_path_and_not_its_chord` at all three ids, `::test_a_bent_bore_crosses_the_threshold_only_along_its_path`, `::test_the_bent_bore_under_the_threshold_is_under_it_by_either_measure`. O2 -> `3 failed, 127 passed in 0.57s`: `TestNearestApproachOffTheChord::test_the_metres_to_the_nearest_motorway_match_the_fixture[motorway_nearest_at_its_middle_node]`, `::test_the_nearest_approach_may_be_at_an_interior_node_of_the_motorway`, `TestFixtureShape::test_some_motorway_case_needs_an_interior_vertex_of_the_candidate`. Exactly the names and counts claimed.
  ARITHMETIC RE-DONE on my own calculator importing nothing from `etl/` (spherical law of cosines, R = 6373000): `R*pi/180 = 111229.83322959862`; kinked bore legs `161.05218685226583` and `161.05157088880296`, path `322.10375774106876`, chord `284.74838365197985` by the law of cosines and `284.7483730677725` as `0.00256 * R*pi/180`, sinuosity `1.1311873086336628`; `111320*cos(37.495deg) = 88322.00731942503`, the V motorway's apex `0.0011323 * that = 100.00700888732189` and `100.0070088878274` by my own unclamped flat point-to-segment at t = 0.49999999999978934, its end nodes `4999.025614279456`. Both workings reproduce.
  ONE BLOCKING FINDING: the round-3 fix rules a mutant EQUIVALENT that is not, and records the ruling under STILL OPEN as fact for round 4. The argument's clause (b) - "every interior segment's endpoints belong to the first or the last segment too" - is false for five or more nodes: for n0..n4 the node n2 is an endpoint of s1 and s2 and of neither s0 nor s3. Dropping interior-interior pairs therefore loses the answer whenever the nearest approach runs from such a node to a segment interior to the other polyline, which in production is the normal case. Reproduced at this head with `line_distance_m` restricted to `if i in (0, n-1) or j in (0, m-1)`: `130 passed in 0.60s` and `602 passed in 63.89s`, exit 0, NOTHING RED - while on way `[(37.480,-122.040),(37.490,-122.030),(37.4991,-122.000),(37.490,-121.970),(37.480,-121.960)]` against motorway `[(37.520,-122.030),(37.500,-122.010),(37.500,-121.990),(37.520,-121.970)]` the original answers `99.48600000003353` m (inside score.MOTORWAY_PROXIMITY_M = 150.0, x0.7) and the mutant answers `406.4842081198996` m (outside it, x1.0), a scenic score 43% higher than plan:85 gives it. `0.0009 * 110540 = 99.486` and the mutant's `406.48389958965134` were both re-derived without the module. The minimum lives only in the two dropped cells of the pair matrix (i=1,j=1) and (i=2,j=1). No geometry in either fixture has an interior segment on BOTH sides - the motorway cases are 3 nodes against 2, and the one 4-node way faces a 2-node stub whose single segment is first and last - and `TestFixtureShape` asks only whether geometries BEND, so it is green on this hole too. To close, fixture-and-test only again: the geometry above with `expected_meters` 99.486 and the retained-pair minimum 406.4842 typed out in `workings`; a test pinning both and the 150 m consequence; a `TestFixtureShape` companion guard "some case's nearest approach needs a segment interior to BOTH polylines"; and the STILL OPEN paragraph retracted, since as written it tells round 4 and T-0163 not to look here. The true statement is that the mutant is equivalent only when one of the two polylines has at most four nodes.
  RECORDABLES. (1) My second mutant, `is_tunnel` without `.strip().lower()`, is already red by name - `tunnel_value_is_case_and_space_normalised`, two ids - so round 4 need not spend a mutant on it. (2) Even once the finding is fixed, `TestFixtureShape`'s vocabulary is collinearity; the interior-interior axis wants its own named test. (3) The orchestrator's note (a) is accurate: `geometries_of()` walks `tunnel_cases` + `motorway_cases` and their nested `motorways` only. (4) Note (b) stands - `111234.7` is still prose in `geometry_terms_fixture.json`; my calculator prints `111229.83322959862`; no value depends on it. (5) Carried unchanged: the `is_closed_way` rank-population contract (T-0163), `is_motorway` not being called by `meters_to_nearest_motorway`, and no spatial index. Nothing in the PR was changed. `state:` and `reviewer:` left as they are; the task stays in queue/claimed/ for a fourth round.
- 2026-09-18T23:52Z **REVIEW ROUND 4 FIX - agent/claude-opus-5 (the owner), fixture and tests only.**
  THE ROUND-3 "EQUIVALENT" RULING WAS WRONG, and it is retracted here rather than amended, because as
  written it told round 4 and T-0163 not to look. The round-3 entry's STILL OPEN paragraph "THE MUTANT
  CLASS THAT CANNOT BE CLOSED BY A FIXTURE" argued that dropping the interior-interior segment pairs from
  `line_distance_m` is an equivalent mutant, on two clauses. Clause (a) - the minimum distance between two
  disjoint segments is attained at an endpoint of at least one of them - is TRUE in the plane. Clause (b) -
  "every interior segment's endpoints belong to the first or the last segment too" - is FALSE from five
  nodes on: for n0..n4 the segments are s0..s3 and the node n2 is an endpoint of s1 and of s2 and of
  NEITHER s0 nor s3. So when the nearest approach runs from such a node to a segment interior to the other
  polyline, the value is computed only in the dropped cells and no retained pair reproduces it. The mutant
  is equivalent ONLY when one of the two polylines has at most four nodes - which was the shape of every
  case in both fixtures, 3 nodes against 2 plus one 4-node way against a 2-node stub - and in production,
  where a way and a motorway both carry dozens of nodes and run past each other, interior-interior is the
  NORMAL case. The earlier entry is left byte-for-byte as it was written; the STILL OPEN list below no
  longer carries that paragraph, and this is the entry that supersedes it.
  REPRODUCED FIRST, at 0bc238f (c0dfe1a plus the reviewer's entry, tree clean), before the fixture or the
  new test file was opened. The reviewer's P1 applied ALONE to `proximity.py` - `line_distance_m` ->
  `min(segment_distance_m(line[i], line[i+1], other[j], other[j+1]) for i in range(n) for j in range(m) if
  i in (0, n-1) or j in (0, m-1))` - gives `130 passed in 0.93s`, exit 0, NOTHING RED on
  `tests/test_proximity.py tests/test_sinuosity.py tests/test_proximity_bends.py`, against a control of
  `130 passed in 1.08s`. `services/etl/etl/__pycache__` purged before EVERY pytest run and 1.1 s slept
  before each write (round 2's recordable 3); the original bytes written back, md5 re-read
  `254632996234f9bd1c1e130db0244bea`, `git status --short` empty.
  THE ARITHMETIC, on `services/etl/work/T-0161/calc4.py` (gitignored, not committed), which imports nothing
  from `etl/` and writes out the flat projection itself. The reviewer's geometry, typed as given: way
  `[(37.480,-122.040),(37.490,-122.030),(37.4991,-122.000),(37.490,-121.970),(37.480,-121.960)]` against
  motorway `[(37.520,-122.030),(37.500,-122.010),(37.500,-121.990),(37.520,-121.970)]`. The way's middle
  node sits 0.0009 deg of latitude south of the motorway's middle segment and inside its longitude span, so
  the true distance is a pure latitude difference, `0.0009 * 110540 = 99.486` m - inside
  score.MOTORWAY_PROXIMITY_M = 150.0, x0.7. The whole per-pair matrix (way segment i x motorway segment j):
  `i=0 [2069.787581, 2083.699146, 3701.099603]`, `i=1 [406.484208, 99.486000, 888.629160]`,
  `i=2 [888.629160, 99.486000, 406.484208]`, `i=3 [3701.099603, 2083.699146, 2069.787581]`. The minimum
  `99.48600000003353` is attained at `(i=1,j=1)` and `(i=2,j=1)` and NOWHERE else - both cells interior x
  interior - and the minimum over every pair the mutant retains is `406.4842081198996`, the way's s1
  against the motorway's FIRST segment, the foot of the perpendicular from (37.500,-122.010) at
  t = 0.7211147242319178. 406.484 is OUTSIDE 150.0, so the mutant does not lose precision, it loses the
  multiplier: the way keeps a scenic score 1/0.7 = 43% higher than plan:85 gives it, with the suite green.
  WHAT CHANGED, tests and fixture only - `proximity.py` is untouched for the THIRD round running and the
  shipped code is right for the fourth time.
  (1) `services/etl/tests/fixtures/geometry_bends_fixture.json` 67 -> 78 lines: the case
  `nearest_approach_interior_to_both_polylines` (the geometry above, `expected_meters` 99.486 at abs 0.001,
  `retained_pair_meters` 406.4842 at abs 0.001, `expected_chord_meters` "inf" - both chords are past
  MOTORWAY_SEARCH_RADIUS_M, 2210.8000 m and 2310.2860 m), with the whole matrix and both minimum cells
  named in its `workings`, plus one sentence in the file's `note` saying what the second axis is. The case
  is added to the bends fixture rather than to a new one because it is the same concern - a polyline is the
  minimum over its SEGMENTS - and because the two per-case tests already in `test_proximity_bends.py` then
  cover it for free (the 22 collected there become 24).
  (2) `services/etl/tests/test_proximity_interior.py` (new, 178 lines, 4 tests, one concern: the nearest
  approach can need a pair of segments interior to BOTH polylines). It went in its own file because
  `test_proximity_bends.py` is 278 lines and 178 more would break the 300-line cap.
  `TestNearestApproachInteriorToBothPolylines::test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines`
  pins 99.486 from the fixture (and the same answer from `line_distance_m(way[1:4], motorway[1:3])`, the
  two interior sub-polylines alone, and from `meters_to_nearest_motorway`), and
  `::test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold` pins the product cost:
  the retained-pair minimum is 406.4842 and is OUTSIDE score.MOTORWAY_PROXIMITY_M while the true answer is
  inside it. Neither the 150.0 nor the 0.7 is restated - the cut is imported from score.py and the metres
  come from the fixture.
  (3) THE SECOND STRUCTURAL GUARD, the reviewer's recordable 2, because `TestFixtureShape`'s vocabulary is
  collinearity and a fixture can bend everywhere and still have every minimum on an end segment - which is
  the state both fixtures were in at c0dfe1a.
  `TestInteriorPairShape::test_some_motorway_case_has_its_minimum_at_a_pair_interior_to_both_polylines`
  walks the motorway cases of BOTH fixtures, computes the argmin pair with this file's OWN flat
  segment-to-segment metric - written out in the test file, never `proximity`'s - and requires at least one
  case with `0 < i < n-1` and `0 < j < m-1`. Its companion
  `::test_the_interior_case_matrix_is_the_one_its_workings_types_out` pins the matrix the `workings` type
  out: the minimum is 99.486, the cells attaining it are exactly `[(1,1),(2,1)]`, and the best cell outside
  them is 406.4842. Both are red on the fixtures as they stood at c0dfe1a and green with the new case.
  (4) `touches:` gains `services/etl/tests/test_proximity_interior.py` - a ruled scope addition, the same
  kind round 3 disclosed for `test_proximity_bends.py`: the brief's "tests and fixture only" is satisfied,
  the 300-line cap forces the new path, and no serial-only file is involved.
  RED BY NAME AT THE FINAL TREE, over the four test files, control `136 passed in 0.79s`, each mutant
  applied ALONE with `__pycache__` purged before every run, 1.1 s slept before every write and the md5
  re-read after every restore (`proximity.py` `254632996234f9bd1c1e130db0244bea`, the bends fixture
  `5b8263ec58a6403841e79fdf286b57ff`).
  P1 (the reviewer's) -> `3 failed, 133 passed in 1.09s`:
  `tests/test_proximity_interior.py::TestNearestApproachInteriorToBothPolylines::test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines`,
  `...::test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold`, and
  `tests/test_proximity_bends.py::TestNearestApproachOffTheChord::test_the_metres_to_the_nearest_motorway_match_the_fixture[nearest_approach_interior_to_both_polylines]`.
  N4, MY OWN NEIGHBOUR and not the reviewer's - the same comprehension keeping only `j in (0, m-1)`, so
  every pair whose MOTORWAY segment is interior is dropped, a strictly different retained set from P1's ->
  `3 failed, 133 passed in 6.75s`, the same three names (both mutants lose the same two cells of column
  j=1, which is why the same tests are the ones that can see them).
  F2, a FIXTURE mutant and the only way a structural guard can be seen red at all: the bends fixture
  exactly as `git show c0dfe1a` prints it, round 4's case removed -> `4 failed, 130 passed in 1.43s`, the
  two value tests plus BOTH guards
  `tests/test_proximity_interior.py::TestInteriorPairShape::test_some_motorway_case_has_its_minimum_at_a_pair_interior_to_both_polylines`
  and `::test_the_interior_case_matrix_is_the_one_its_workings_types_out`.
  `git status --short` carried nothing but the three round-4 paths throughout.
  THE REVIEWER'S RECORDABLES. (1) TAKEN: `is_tunnel` without `.strip().lower()` is already red by name
  (`tunnel_value_is_case_and_space_normalised`, two ids in `test_proximity.py`), so round 5 need not spend a
  mutant on it - my own neighbour N4 was spent on the comprehension instead. (2) TAKEN in full: that is
  `TestInteriorPairShape`, on its own axis and in its own file. (3) and (5) need no action. (4) `111234.7`
  is still prose in `geometry_terms_fixture.json`'s `workings`; that file is deliberately bit-identical to
  71a6a83 and no value depends on the figure, so it is left for the next edit that file earns on its own.
  (6) carried into STILL OPEN below unchanged.
- 2026-09-18T23:52Z STILL OPEN after round 4. This list supersedes the round-3 one, which carried a wrong
  ruling; the retraction is the first item.
  - RETRACTED: "the mutant class that cannot be closed by a fixture". Dropping the interior-interior
    segment pairs from `line_distance_m` is NOT an equivalent mutant. It is equivalent only when one of the
    two polylines has at most four nodes, and it is now closed by `nearest_approach_interior_to_both_polylines`
    and by `TestInteriorPairShape`. Round 5 and T-0163 should read this axis as covered, not as unreachable.
  - Unchanged and still T-0163's: a caller that RANKS sinuosity must call `is_closed_way` and leave the
    declined ways out of the rank population - the raw floor 1.0 and score.py's unit ceiling 1.0 are the
    same number, so a normaliser that passes the raw value through gives every roundabout the MAXIMUM
    credit and no range check can see it.
  - The shape of the declined answer is unchanged and is still an under-claim; changing it is a seam change
    across T-0163 and T-0146 and is not one test, so it is not taken here.
  - `is_motorway` is exported and is NOT called by `meters_to_nearest_motorway`: the caller filters the
    candidates. No spatial index either - every candidate handed in is measured, and the matrix above is
    exactly why the measurement cannot be narrowed to the end segments.
  - `ops/test` and `ops/check-pins` were again NOT run on this box (both wrap swift; the default scratch
    path does not build inside a worktree here). CI decides them; `gh pr checks 94` is read once after the
    push.
- 2026-09-19T00:45Z Acceptance block re-run BARE at 1e3136a, the round-4 commit, and every line of it
  reproduced on a clean tree (`git status --short` prints nothing, `git rev-parse HEAD` ->
  `1e3136a9247cbd2125b77f16c34a82a5ead22345`). The round-4 session was cut off by a usage-limit pause after
  1e3136a was committed and before it was pushed; this entry is the confirmation run that the pause
  interrupted, and it changes no file but this one. `cd services/etl && python -m pytest tests -rs` ->
  `608 passed in 76.73s (0:01:16)`, exit 0, `grep -c 'short test summary'` over the captured output `0` -
  zero failures, zero skips. The four test files: `python -m pytest tests/test_proximity.py
  tests/test_sinuosity.py tests/test_proximity_bends.py tests/test_proximity_interior.py` -> `136 passed in
  0.71s`, exit 0, and `--collect-only -q` -> `tests/test_proximity.py: 60`,
  `tests/test_proximity_bends.py: 24`, `tests/test_proximity_interior.py: 4`, `tests/test_sinuosity.py: 48`.
  `wc -l` -> sinuosity.py 83, proximity.py 143, test_sinuosity.py 178, test_proximity.py 300,
  geometry_terms_fixture.json 263, test_proximity_bends.py 278, geometry_bends_fixture.json 78,
  test_proximity_interior.py 178, with `awk 'END{print NR}'` printing 300 / 178 / 278 / 178 for the four
  test files. `bash ops/lib/check-pipe-consumers` (bare) -> `PIPE-CONSUMERS OK: no gate decides with
  'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0; `bash ops/queue-check` (bare) ->
  `QUEUE OK (158 tasks)`, exit 0. `md5sum` at the final tree: `services/etl/etl/proximity.py`
  `254632996234f9bd1c1e130db0244bea` and `services/etl/tests/fixtures/geometry_bends_fixture.json`
  `5b8263ec58a6403841e79fdf286b57ff` - the two md5s the round-4 mutant table restores to, so the tree that
  was measured is the tree that is pushed. WALL TIME IS STILL NOT A CLAIM and this run is why the block is
  right not to make one: the same 608 tests read `76.73s` here against `102.10s` in the block, same box,
  same commit, a different session. NOT RE-RUN IN THIS PASS, and not restated as if it were: the round-4
  mutant table (P1, N4, F2) was measured at this same tree by the commit that recorded it and no file has
  changed since; `ops/test` and `ops/check-pins` are still not run on this box (both wrap swift). `state:
  claimed` and `reviewer: null` are untouched; the task stays in queue/claimed/ for the round-4 review.
- 2026-09-19T01:00:47Z **Record corrections from the read-only verification of the round-4 fix, closed before round 4 is bought -
  agent/claude-fable-5-1 (orchestrator), for the owner. The verifier re-applied P1 to a copy (red by the three
  names claimed), matched proximity.py's and the fixture's md5, and found the tree clean; these are shape.**
  (a) The 23:52Z round-4 entry had been glued onto the last line of rv3's entry: 0bc238f's append carried no
  trailing newline, so 1e3136a extended that line - which is also why `git show 1e3136a` counts 7 deletions on
  this file. This commit inserts the one missing newline between the two entries; no character of either
  entry changed. (b) PR #94's body headed its verification "at a6b6e5c (the head)"; the run was made at
  1e3136a (`git rev-parse HEAD` in the 00:45Z entry) and a6b6e5c only recorded it, touching this file alone -
  services/etl is byte-identical across the two. The heading now says so. (c) The `touches:` line gained
  `services/etl/tests/test_proximity_interior.py` in 1e3136a, disclosed there as a ruled scope addition - it is
  the one front-matter change outside the acceptance block. (d) N4 and F2 in the round-4 table are 1e3136a's
  runs; neither the resumed fixer nor the verifier repeated them.
- 2026-09-19T01:13:11Z REVIEW ROUND 4 - PASS, by agent/rv4-pr94 (not the owner, not rv1/rv2/rv3, not a
  fixer, not the orchestrator). Reviewed 41d7663 in a detached worktree (.worktrees/rv4-pr94, removed at the
  end); nothing was written in .worktrees/T-0161 but this entry and the two front-matter fields. Run under
  the 17:13 panel's last-round ruling: PASS if a check now exists that could tell for the classes found.
  SCOPE. `git diff c0dfe1a..41d7663 --stat` is three paths and no more - this task file, the fixture
  `services/etl/tests/fixtures/geometry_bends_fixture.json` (one motorway case and one sentence of `note`)
  and `services/etl/tests/test_proximity_interior.py` (178 +, new) - `3 files changed, 354 insertions(+), 7
  deletions(-)`. No code file is in the diff; `md5sum` at this head gives `services/etl/etl/proximity.py`
  `254632996234f9bd1c1e130db0244bea` and the fixture `5b8263ec58a6403841e79fdf286b57ff`, the two the round-4
  mutant table restores to. The dated entries are separated: `grep -c '^- 20'` -> `24` and a grep for a dated
  stamp with anything before it -> `0`, so no entry is glued onto another's last line any more.
  ROUND 3's BLOCKING FINDING IS CLOSED. rv3's P1 re-applied ALONE to `proximity.py` at this head
  (`line_distance_m` keeping only `if i in (0, n - 1) or j in (0, m - 1)`), `services/etl/etl/__pycache__`
  purged before every pytest run, 1.1 s slept before each write, the original bytes written back and the md5
  re-read: `3 failed, 133 passed`, exit 1, red BY NAME with exactly the three names the block claims -
  `tests/test_proximity_interior.py::TestNearestApproachInteriorToBothPolylines::test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines`,
  `tests/test_proximity_interior.py::TestNearestApproachInteriorToBothPolylines::test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold`
  and `tests/test_proximity_bends.py::TestNearestApproachOffTheChord::test_the_metres_to_the_nearest_motorway_match_the_fixture[nearest_approach_interior_to_both_polylines]`.
  Control on the same four files was green and `git status --short` was empty after the restore.
  ACCEPTANCE BLOCK RE-RUN AT 41d7663, every line reproduced. `cd services/etl && python -m pytest tests -rs`
  -> `608 passed in 85.91s (0:01:25)`, exit 0, `grep -c 'short test summary'` over the captured output `0` -
  zero failures, zero skips. The four test files -> `136 passed in 1.29s`, exit 0; `--collect-only -q` ->
  `tests/test_proximity.py: 60`, `tests/test_proximity_bends.py: 24`, `tests/test_proximity_interior.py: 4`,
  `tests/test_sinuosity.py: 48`. `wc -l` in the block's own order -> sinuosity.py 83, proximity.py 143,
  test_sinuosity.py 178, test_proximity.py 300, geometry_terms_fixture.json 263, test_proximity_bends.py 278,
  geometry_bends_fixture.json 78, test_proximity_interior.py 178, and `awk 'END{print NR}'` -> 300 / 178 /
  278 / 178 for the four test files. `bash ops/lib/check-pipe-consumers` bare -> `PIPE-CONSUMERS OK: no gate
  decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0. `bash ops/queue-check` bare
  -> `QUEUE OK (158 tasks)`, exit 0. `git status --short` empty at 41d7663. Wall time is still not a claim
  and this is its third reading: `85.91s` here against `76.73s` and `102.10s` in the record, same box, same
  commit.
  ARITHMETIC RE-DONE WITHOUT THE MODULE, in a calculator that imports nothing from `etl/` and writes the flat
  projection out itself: `0.0009 * 110540 = 99.486`; the whole per-pair matrix of the new case, row for row,
  `i=0 [2069.787581, 2083.699146, 3701.099603]`, `i=1 [406.484208, 99.486, 888.62916]`, `i=2 [888.62916,
  99.486, 406.484208]`, `i=3 [3701.099603, 2083.699146, 2069.787581]`; `argmin ALL = 99.48600000003353`
  attained at `[(1, 1), (2, 1)]` and nowhere else, both of them interior x interior; the retained-pair
  `406.4842081198996` as the foot of the perpendicular from the motorway's n1 onto the way's s1 at
  `t = 0.7211147242319178`; and both chords past the radius at `2210.8000000002794` and `2310.286000000313`.
  Every figure the fixture types out, independently.
  MY OWN MUTANTS, each applied ALONE and restored byte-for-byte (md5 back to
  `254632996234f9bd1c1e130db0244bea` and `git status --short` empty after each), aimed at the product
  question - can a wrong metre value reach `score.py`, in either direction. M1, `segment_distance_m` keeping
  only the CANDIDATE endpoint terms, `min(point_to_segment_m(c, a, b), point_to_segment_m(d, a, b))`: the
  untried mirror of round 3's N3, and the half that carries the new case's 99.486 -> `10 failed`, red by name
  across all three proximity files including both new interior tests. M2, `_crosses` dropping its second
  straddle test so two segments whose infinite lines separate read 0.0 m and a scenic road takes a SPURIOUS
  x0.7 -> `8 failed`, red by name including
  `tests/test_proximity_bends.py::TestNearestApproachOffTheChord::test_the_bending_polyline_reduced_to_its_chord_loses_the_encounter[nearest_approach_interior_to_both_polylines]`.
  Both killed.
  ONE RECORDABLE - A SIXTH GEOMETRY CLASS, for queue/ready/T-0176, NOT BLOCKING under this round's ruling.
  M3, a BANDED subset of the segment-pair matrix: `line_distance_m` keeping only `if abs(i - j) <= 1`, the
  shape a "monotone sweep" pruning would have. It SURVIVES - `136 passed` on the four test files and
  `608 passed` on the whole suite, exit 0, nothing red. It is none of the five classes the round-4 fix claims
  to cover: it KEEPS the interior-interior pairs, which is exactly why the new case cannot see it (that
  case's minimum sits at (1,1) and (2,1), both on or next to the diagonal); it keeps the first and last
  segments, so it is not the segment-subset class either; and it is not the chord, not the candidate order
  and not a normalisation. Witness, computed with my own flat metric and no module: the way
  `[(37.480,-122.040),(37.4805,-122.030),(37.480,-122.020),(37.4805,-122.010),(37.480,-122.000)]` against the
  2-node motorway `[(37.4809,-122.0055),(37.4809,-122.0045)]` has column j=0 equal to
  `[2164.7493, 1284.7685, 399.9755, 68.9527]`, a true minimum of `68.95267627751733` m at `(i=3, j=0)` -
  inside score.MOTORWAY_PROXIMITY_M = 150.0, x0.7 - while the band keeps only i in {0, 1} and answers
  `1284.7685` m, past MOTORWAY_SEARCH_RADIUS_M = 1000.0, so `meters_to_nearest_motorway` reports `math.inf`
  and the way keeps a scenic score 1/0.7 = 43% higher than plan:85 gives it. No fixture reaches
  `|i - j| >= 2` at all: the motorway cases are 3-vs-2, 4-vs-2, 3-vs-3 and the new 5-vs-4, and every one of
  their minima is on or next to the diagonal. T-0176 should carry this as "banded / diagonal-window subset of
  the segment-pair matrix", with the witness above, and give it a literal floor in the committed mutation
  population. It is a hole in the POPULATION, not a wrong value in the shipped code: `proximity.py` is
  unchanged since round 1 and answers `99.48600000003353` correctly here, as it has for four rounds.
  NOT RUN HERE, and not restated as if it were: `ops/test` and `ops/check-pins` (both wrap swift; not run on
  this box, exactly as the block says), and the round-4 table's N4 and F2, which were measured at 1e3136a by
  the commit that recorded them and whose files have not changed since. `gh pr checks 94` read once ->
  `core pass 2m21s`, `pins-source-only pass 54s`; `gh pr view 94` -> `base=main`, so nothing is stacked
  behind a task branch. PR #94 is signed off; it is not merged by me.
