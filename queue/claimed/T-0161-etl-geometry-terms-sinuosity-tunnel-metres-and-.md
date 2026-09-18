---
id: T-0161
title: ETL geometry terms - sinuosity, tunnel metres and metres to the nearest motorway, from way geometry alone
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:52:32Z
lease_expires_at: 2026-09-19T03:52:32Z
worktree: .worktrees/T-0161
branch: task/T-0161
exclusive: []
touches: [services/etl/etl/sinuosity.py, services/etl/etl/proximity.py, services/etl/tests/test_sinuosity.py, services/etl/tests/test_proximity.py, services/etl/tests/fixtures/]
pins_affected: []
reviewer: null
depends_on: [T-0154]
verify: [ops/test, ops/check-pins]
acceptance:
  - "WHAT IS NEW, AND THAT NOTHING OLD MOVED. The code commit is 69f1d8c: `6 files changed, 889 insertions(+)`, every one of them a `create mode 100644` - `services/etl/etl/sinuosity.py`, `services/etl/etl/proximity.py`, `services/etl/tests/test_sinuosity.py`, `services/etl/tests/test_proximity.py`, `services/etl/tests/fixtures/geometry_terms_fixture.json` and this task file. No existing file was edited, which was the Brief's first constraint: score.py, snap.py, curvature.py and byways.py are untouched and the seam between this task and its two siblings is score.py's keyword names alone. `wc -l` at the final commit: sinuosity.py 78, proximity.py 143, test_sinuosity.py 135, test_proximity.py 208, the fixture 190 - all under the 300-line cap"
  - "THE WHOLE SUITE, re-run at the final commit (20:17:16Z, against 69f1d8c). `cd services/etl && python -m pytest tests -rs` -> `555 passed in 66.00s (0:01:05)`, exit 0. Zero failures, zero skips - `-rs` prints no short-summary section because there is nothing to report. 83 of the 555 are this task's two files (`python -m pytest tests/test_proximity.py tests/test_sinuosity.py` -> `83 passed in 0.52s`; 41 in test_sinuosity.py, 42 in test_proximity.py). 555 minus 83 is 472, which is exactly the count T-0154's acceptance block recorded for the suite it left behind: this task added tests and changed no existing one"
  - "`bash ops/lib/check-pipe-consumers` -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0"
  - "`bash ops/queue-check` -> `QUEUE OK (158 tasks)`, exit 0. `state: claimed` and `reviewer: null` are unchanged; the reviewer of this task is not its owner and will not be a subagent of this session"
  - "RED FIRST, then RED BY NAME. With both modules moved out of the tree: `2 errors in 1.71s`, `E   ImportError: cannot import name 'proximity' from 'etl'` and the same for `sinuosity`. Red by name is the six-mutation table in the Log, each mutation applied alone and restored - `5 failed, 36 passed`, `4 failed, 37 passed`, `7 failed, 75 passed`, `5 failed, 36 passed`, `3 failed, 38 passed`, `2 failed, 39 passed`, and 26 named failing tests in total. No survivors. `git status --short` prints nothing at the final commit and `diff -q` against the pristine copies printed `BOTH_RESTORED` after the last restore"
  - "EVERY EXPECTED VALUE IS TYPED OUT AND NONE COMES FROM THE CODE IT CHECKS. The fixture's `workings` field carries the arithmetic per case; the numbers were settled with a scratch calculator under `services/etl/work/T-0161/` (gitignored, not committed) that imports nothing from `etl/` and writes out the spherical law of cosines and the flat factors itself. What it printed, and what the fixture therefore claims: `dogleg sinuosity = 1.4141662205310273  rel err vs sqrt2 = 3.3475737560070365e-05` (so sqrt(2) is typed as 1.4142136 at rel=1e-4, three times the spherical excess); `hairpin ratio=2.999999996681494` (typed as 3.0, the ratio of 0.03 deg to 0.01 deg on one meridian); `closed_loop_rectangle gap=0.000000`; `lasso gap=5.027772 path=4223.129108 raw ratio=839.96`; `just_open gap=22.245967 ratio=189.85`; `mid-segment = 55.27000000048429` against `way vertices only = 884.8975559533108`; `crossing endpoint-only min = 441.61003659665585`; and the two earth models side by side at `0.0005 deg * ky = 55.27` versus `0.0005 deg gc = 55.61485786852174`, which is ruling R3's evidence"
  - "NOT RUN HERE, and why. `ops/test` and `ops/check-pins` were not run on this box: the default swift scratch path does not build inside a worktree here and both wrap swift, exactly as the task instructed. `verify:` still names them; CI decides them. `gh pr checks` is read once after the push and reported back with the PR, since it cannot exist before this commit"
  - "NOT IN THIS TASK, unchanged from the Brief: the way record, the region rank-normaliser that maps raw sinuosity into score.py's 0..1 term, and the `scenic_score` column (all T-0163); the tag-table terms (T-0162); any spatial index over candidate motorways (the caller narrows the set - stated in the module docstring and under STILL OPEN); any multiplier or threshold, which stay in score.py alone. No serial-only file was touched and both `pins/floor_*.txt` are unchanged"
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
