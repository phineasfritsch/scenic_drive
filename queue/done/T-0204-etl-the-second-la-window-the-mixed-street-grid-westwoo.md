---
id: T-0204
title: ETL - the second LA window: the mixed street grid (Westwood/Brentwood/Santa Monica, -118.55,33.98,-118.35,34.15) scored through the same tagwriter + scenecheck path; acceptance: the grid's top ten rank BELOW the canyon window's, or the index is wrong
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T07:50:16Z
lease_expires_at: 2026-09-19T13:50:16Z
worktree: .worktrees/T-0204
branch: task/T-0204
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, ops/mutate/]
pins_affected: []
reviewer: agent/rv1-pr113
depends_on: [T-0168]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the five container commands T-0168's Log records, run over --bbox -118.55,33.98,-118.35,34.15 (the probe bbox T-0168's Log names) in the pinned scenic-etl image through WSL, each foreground and timed; the WAYDOC/ASSEMBLE/WRITE count lines quoted; two writes byte-identical (the P-DATA-01 shape, sha256 quoted); osmium fileinfo -e node/way counts quoted; CHECK4 both clauses zero"
  - "the grid's top ten by scenic_score printed the way scenecheck --top 10 prints them, beside the canyon window's top ten (T-0168's Log): every one of the grid's ten scores BELOW the canyon window's tenth, asserted by a test over the two scored tables (committed as small fixtures of the top-N rows, not the 7 MB JSON) - RED first on a swapped table; if the assertion is false the task FAILS its own acceptance and the Log says which grid ways outrank Topanga and why - that is the finding, not a defect to hide"
  - "the second read for the owner: the grid's top ten with name, class and a coordinate, the way T-0168 printed the canyon's; the judgement stays the owner's"
  - "scenecheck's read-back oracle hardened first (rv1-pr111's recordables on PR #111): the checker asserts every scenic_score is an int in 0..10 (today a tertiary at 42 counts as scored and ranks #1; a motorway at -3 clears clause 2 because value > 0 is false); counts() and top() give ONE answer for a way that is both scenic_refused=1 and scored (today counts() skips it and top() ranks it); a non-integer tag value is a refusal naming the way, not a traceback - each RED first on a hand-built read-back file, then green; the population in ops/mutate/scenic_tags.py gains the three"
  - "cd services/etl && python -m pytest tests -rs -o addopts= -> count line and zero skips at the final commit; wc -l re-measured"
---
## Brief

From the 01:13 panel (STRATEGY, grounded): T-0168's window is one massif - all ten top-scored ways are Santa Monica
Mountains canyon roads (Topanga x3, Stunt, Old Topanga x2, Piuma, Fernwood Pacific) - so plan:283's '8/10
top-scored ways are roads you'd drive' cannot fail there and measures nothing. The mixed grid east of the window is
the one queued thing that can DISCONFIRM the index: if Wilshire, Sunset through Brentwood, or a Westwood
residential grid outranks Topanga, the score is wrong and the Log says so. Same commands, same gates, the
scenic-index lock (one container run at a time).

## Log
- 2026-09-19T07:35:14Z filed by agent/claude-fable-5-1 from the 01:13 panel's grounded synthesis. Not started; after #111 merges - the NEXT START after T-0178/T-0195.
- 2026-09-19T07:46:16Z bullet added by agent/claude-fable-5-1 from rv1-pr111's PASS on PR #111 (recordables R-a, R-b, R-c): the checker over the shipped bytes does not restate the 0..10 int contract the writer keeps, its two halves disagree on a refused-and-scored way, and a non-integer value is a traceback. Shapes tagwriter cannot emit today, so gaps in the independent oracle, not in the bytes that ship - hardened before this window's second read so the oracle the owner reads is stricter than the writer.
- 2026-09-19T07:50:12Z PROMOTED to ready/ by agent/claude-fable-5-1: #111 (T-0168) merged and the scenic-index lock released; the LA extract, the filtered clip and the canyon window's scored table are in the MAIN checkout's gitignored services/etl/work/la/ (moved there before T-0168's worktree was removed, 551 MB) - this run clips the grid from la-filtered.osm.pbf, no refetch.
- 2026-09-19T07:50:16Z claimed by agent/claude-opus-5; lease until 2026-09-19T13:50:16Z
- 2026-09-19T07:53:05Z touches: WIDENED to `ops/mutate/` by agent/claude-opus-5 (the owner), because R1 below adds three
  mutations to `ops/mutate/scenic_tags.py` and raises its floor (a numeric change ships its population - CLAUDE.md,
  Verification). The pre-commit hook reads `touches:` from the header, so the widening is in the header and its reason
  is this line. The fixtures R3 commits are under `services/etl/tests/fixtures/`, already inside `services/etl/tests/`.
  Nothing else outside `touches:` is staged.
- 2026-09-19T07:53:05Z R1 THE ORACLE HARDENING (rv1-pr111's three recordables), ruled by agent/claude-opus-5 before code.
  WHAT IS WRONG TODAY, restated from the shipped module rather than from the review: `scenecheck.scored_value` is
  `int(raw)` with no contract at all, so (a) a tertiary tagged `scenic_score=42` is counted as `scored` and ranks #1 in
  the read the owner makes, (b) a motorway at `-3` clears clause 2 because `-3 > 0` is false, and (c) `scenic_score=abc`
  or `7.5` is a ValueError traceback out of `counts()` - the oracle crashes instead of naming the way. And `counts()`
  and `top()` disagree about ONE way: `counts()` tests `scenic_refused` FIRST and `continue`s, so a way carrying BOTH
  `scenic_refused=1` and a score is counted as `refused` and never as `scored`, while `top()` never looks at
  `scenic_refused` at all and ranks it. Two halves of one oracle with two answers about one road.
  THE RULING, three parts:
  (1) THE CONTRACT IS RESTATED IN THE CHECKER, DELIBERATELY. The writer keeps 0..10 (`tagwriter.quantise` clamps);
      the checker reads the BYTES THAT SHIP and may not assume the writer wrote them - a hand-edited PBF, a second
      producer, or a future writer is exactly what an independent oracle is for. `scenic_score` must be an INTEGER
      LITERAL in `SCORE_MIN..SCORE_MAX`, and those two bounds are IMPORTED from `tagwriter` by identity (the R8
      principle: the rules are imported, never restated - a second copy of a bound is how the writer and the checker
      agree with each other while both are wrong about a road). What is restated is that the value must SATISFY the
      contract; the numbers themselves are not copied.
  (2) THE REFUSAL SHAPE: a third CHECK4 clause, `malformed=N`, printed on the same line between `gated_scored` and
      `scored`, and `refuses()` exits 4 (`ops/sane`'s corpus-bounds code) when any of the three is non-zero. The
      CHECK4 line becomes `CHECK4 null_score=N gated_scored=N malformed=N scored=N refused=N not_a_road=N`. A
      malformed way is NAMED on stderr, one line per way (`way <id> scenic_score=<raw>: <why>`), capped at the first
      20 with a `... and N more` tail, because an oracle that prints 12,000 lines is an oracle nobody reads. A
      non-integer tag value is therefore a refusal that names the way, never a traceback.
      WHAT COUNTS AS MALFORMED, the three shapes: a `scenic_score` that is not an integer literal (`7.5`, `abc`, ``);
      an integer outside 0..10; and a way carrying BOTH `scenic_refused` and a `scenic_score`, which ruling R2 of
      T-0168 forbids ("`scenic_refused=1` and NO `scenic_score` tag - never a silent 0"). The third is the ONE ANSWER
      the acceptance asks for: a contradictory way is neither `refused` nor `scored`, it is `malformed`, in both
      halves.
  (3) ONE ANSWER BY CONSTRUCTION, not by two matching edits. `counts()` and `top()` stop classifying ways
      independently: a single `classify(way_id, tags) -> (kind, detail)` returns exactly one of
      `not_a_road / refused / malformed / null_score / scored`, `counts()` tallies its answer and `top()` ranks only
      the ways it calls `scored`. Two halves that each decide what a way is can drift; two halves that ask the same
      function cannot. A malformed way is excluded from the ranking - it cannot rank on a number the writer could not
      have written.
  THE POPULATION (a numeric module ships one): `ops/mutate/scenic_tags.py` gains three mutations, one per part -
  accept a score outside the range; let `top()` rank a way `classify` refused; let the non-integer value raise instead
  of being named - and `MIN_MUTATIONS` 25 -> 28. Each is demonstrated RED first on a hand-built read-back file, then
  green. `scenecheck.py` is 151 lines today; if the hardening crosses 300 it splits along a boundary of meaning (the
  classification and the CLI), not at a line number.
- 2026-09-19T07:53:05Z R2 THE GRID WINDOW and its way-count bound, ruled by agent/claude-opus-5 on MEASUREMENT, not on
  an estimate. The window is T-0168's own `--bbox -118.55,33.98,-118.35,34.15` (its 06:05:31Z entry: "They are a LATER
  RUN of the same five commands"), clipped from the MAIN checkout's `services/etl/work/la/la-filtered.osm.pbf`
  read-only. Clipped and counted first, before any scoring, `osmium extract` 11.018s + `osmium fileinfo -e`:
  **35,126 ways / 205,193 nodes / 26 relations, 2,859,589 B**, bounding box (-118.5883364,33.9597942,-118.3176785,
  34.1597259). That is 2.8x the canyon window's 12,402 and past this task's own ~25,000 bound, so THE RUN SPLITS, as
  the bound says: T-0168 measured `waydoc` at 1m56.591s and `assemble` at 3m33.557s for 11,740 rows (18.2 ms/row in
  the assembler), and every container step in this session must finish inside ONE foreground call.
  TWO SUB-WINDOWS, cut at longitude -118.45, both measured:
    grid-a  -118.55,33.98,-118.45,34.15   11,451 ways /  75,752 nodes  (Santa Monica, Brentwood, Pacific Palisades)
    grid-b  -118.45,33.98,-118.35,34.15   23,887 ways / 135,023 nodes  (Westwood, Century City, Culver City, Mar Vista)
  grid-b is above the canyon window and below the bound only if the urban per-row cost is at or under the mountain's;
  it runs SECOND and each of its stages is its own foreground call, and if `waydoc` on grid-a shows a per-row cost
  that puts grid-b's `assemble` over ~500s, grid-b splits again at -118.40. Measured, then decided - not assumed.
  THE SEAM: `osmium extract` completes every way that crosses the boundary (T-0168 measured the same effect on the
  canyon window's bbox), so a way crossing -118.45 is in BOTH clips with its full geometry and is scored twice. The
  merged grid ranking is over the UNION KEYED BY way_id; a way present in both must carry the SAME score, and that
  equality is checked and quoted rather than assumed - if the two clips disagree about one road, that is a finding
  about the score's dependence on its window, and it goes in the Log.
- 2026-09-19T07:53:05Z R3 THE COMPARISON - the exact predicate and the fixture shape, ruled by agent/claude-opus-5.
  THE PREDICATE, stated so it can be false: let `C10` be the canyon window's TENTH row by the ranking
  `scenecheck.top` prints - way 1237332026, Fernwood Pacific Drive, `scenic_score_unit` **0.7284** (T-0168's
  06:05:31Z entry, re-read here from the shipped read-back rather than copied from prose). The grid window's top ten
  RANK BELOW the canyon window's top ten iff **every one of the grid's ten `scenic_score_unit` values is strictly
  less than C10's**. The unit value and not the 0..10 integer, because the integer is a 4-bit quantisation in which
  the canyon's tenth and a grid way could tie at 7 while differing by 0.04 - a tie is not "below", and the acceptance
  word is BELOW.
  THE FIXTURES: the top **25** rows of each window - `way_id, name, highway, lat, lon, scenic_score,
  scenic_score_unit` exactly as `scenecheck.top` produces them - as
  `services/etl/tests/fixtures/canyon_top25.json` and `services/etl/tests/fixtures/grid_top25.json`, each carrying a
  `meta` naming the window bbox, the read-back file it was produced from, its way counts and the run that made it.
  Twenty-five and not ten so the fixture shows the shoulder of each distribution - a reviewer can see HOW FAR below,
  and a later window can be compared without a new run. The 7 MB scored tables are NOT committed (the work dir is
  gitignored and per-checkout).
  THE TEST: `tests/test_window_ranking.py::test_the_grid_windows_top_ten_ranks_below_the_canyon_windows` over the two
  fixtures, RED FIRST with the two fixture paths swapped (the canyon read as the grid), then green - or NOT green:
  IF THE PREDICATE IS FALSE ON THE REAL DATA THE TASK FAILS ITS OWN ACCEPTANCE. The test stays red, the Log names
  which grid ways outrank Topanga and why (the terms, from the scored table), and the PR says so on its first line.
  That is the finding this window was queued to produce - the one queued thing that can DISCONFIRM the index - and
  hiding it would make every other number here worthless.
- 2026-09-19T07:53:05Z R4 WHICH OF T-0168's STILL OPEN THIS RUN INHERITS, named and NOT fixed, by
  agent/claude-opus-5:
  INHERITED F1 SERVICE WAYS RANK WITH ROADS - and this is the window where it bites, not a footnote: 312,645 of the
  LA clip's 561,000 ways are `highway=service`, and they are concentrated exactly here (Westwood's alleys, Century
  City's parking aisles, Santa Monica's driveways), not in the canyons. Nothing in the score knows a driveway from a
  road. Unfixed here - a class prior or T-0164's POI term is the fix, and both are another task - but every service
  way that reaches the grid's top ten is NAMED in the read, because the owner's judgement needs to know which rows
  are roads.
  INHERITED F3 `points_of_interest_absent` ON EVERY WAY (T-0164 has not landed): 0.14 of E is a constant across both
  windows, so the comparison is between two rankings missing the SAME term - which is what makes it a fair
  comparison, and also what makes it provisional. Named in the PR.
  INHERITED F2 the gates: whatever fraction of the grid is gated is reported as a number, not smoothed.
  INHERITED F5 `extract.Osmium.rel()` cannot see the shared inputs directory from a worktree. This run does not call
  `etl.extract` at all - it clips with `osmium extract` directly out of the MAIN checkout's `la-filtered.osm.pbf`,
  mounted read-only at /src - so the defect is not hit; it is still there, still unfixed, and still named.
  NOT INHERITED, because this run cannot reach it: T-0168's F4 (the licence count) was a one-time re-record.
- 2026-09-19T09:25:57Z SESSION RESTART, declared. An earlier run of this task was cut off mid-container-run. What
  survived and is KEPT: the four rulings above, the commit abfef68 (the R1 hardening of `scenecheck`, its three
  mutations and the floor 25 -> 28), and the clipped PBFs under this worktree's own
  `.worktrees/T-0204/services/etl/work/la/`. What did NOT survive: the stdout of the grid-a `waydoc`/`assemble`
  steps. Rather than quote numbers I could not see, EVERY stage below was RE-RUN in this session and every count
  line here is from output I read. The work dir is this worktree's own; the MAIN checkout's
  `services/etl/work/la/` and `services/etl/inputs/` were mounted READ-ONLY (`:ro`) and nothing was written there.
- 2026-09-19T09:25:57Z THE R1 HARDENING, red then green. The three mutations R1 ruled are in
  `ops/mutate/scenic_tags.py` and each one is a way the hardened checker can be broken; each is CAUGHT by the test
  written for it, and `--prove-vacuity` shows each one MISSED when the test files are emptied - that is the red:
      caught  accept a score outside the 0..10 the router can hold - a tertiary at 42 ranks #1
                <- tests/test_scenecheck.py::test_a_score_above_the_range_the_router_holds_is_malformed_and_does_not_rank
      caught  let the ranking decide for itself instead of asking classify - the two halves drift apart
                <- tests/test_scenecheck.py::test_a_score_above_the_range_the_router_holds_is_malformed_and_does_not_rank
      caught  let a non-integer score raise instead of naming the way - a crash is not a refusal
                <- tests/test_scenecheck.py::test_a_non_integer_score_names_the_way_instead_of_raising
  `MUTATIONS: 28 caught, 0 missed, 0 skipped, of 28` / `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2` /
  `MUTATE OK  caught=28/28 equivalent_caught=0`; `VACUITY: 0 caught, 28 missed, 0 skipped, of 28` / `VACUITY PROVED`.
  `scenecheck.py` is 215 lines, under the 300 cap, so R1's split did not fire.
- 2026-09-19T09:25:57Z THE GRID RUN, in the pinned `scenic-etl:latest` through WSL, every step FOREGROUND and timed
  (`services/etl/work/run-clip.sh`, `run-step.sh`, `emit_fixtures.py` - all under the gitignored work dir).
  THE CLIP (R2): `osmium extract --bbox -118.55,33.98,-118.35,34.15` off the MAIN checkout's
  `la-filtered.osm.pbf` -> **35,126 ways / 205,193 nodes / 26 relations**, past R2's ~25,000 bound, so the run SPLIT
  at -118.45 into grid-a (11,451 ways / 75,752 nodes) and grid-b (23,887 ways / 135,023 nodes). Outputs are under
  `.worktrees/T-0204/services/etl/work/la/`.
  grid-a `-118.55,33.98,-118.45,34.15`:
      WAYDOC ways=11239 refused=0 not_a_road=212 byways=865 byways_no_route_key=793      real 2m17.880s
      ASSEMBLE ways=11239 zero_class=476 gated=1927 sinuosity_declined=575 points_of_interest_absent=11239 null_score=0
                                                                                        real 0m42.148s
      WRITE ways=11451 scored=11239 refused=0 gated=1927 not_a_road=212                  real 0m11.839s / 0m13.451s
      sha256 08f15f95b57f26cdfdf98bed27bd6a01fd0b21948831940137fd5d388da1bc54  grid-a-tagged-1.osm.pbf
      sha256 08f15f95b57f26cdfdf98bed27bd6a01fd0b21948831940137fd5d388da1bc54  grid-a-tagged-2.osm.pbf  (identical)
      osmium fileinfo -e: nodes 75752, ways 11451, relations 14, bbox (-118.5883364,33.9768257,-118.3400603,34.1597259)
      CHECK4 null_score=0 gated_scored=0 malformed=0 scored=11239 refused=0 not_a_road=212   exit 0
  grid-b `-118.45,33.98,-118.35,34.15`:
      WAYDOC ways=23474 refused=0 not_a_road=413 byways=865 byways_no_route_key=793      real 5m27.528s
      ASSEMBLE ways=23474 zero_class=772 gated=3696 sinuosity_declined=1074 points_of_interest_absent=23474 null_score=0
                                                                                        real 0m51.981s
      WRITE ways=23887 scored=23474 refused=0 gated=3696 not_a_road=413                  real 0m16.940s / 0m20.670s
      sha256 115ec2943101091d2872544e4ad850589d15e6f4005995fb6403b2ba0eec4d2c  grid-b-tagged-1.osm.pbf
      sha256 115ec2943101091d2872544e4ad850589d15e6f4005995fb6403b2ba0eec4d2c  grid-b-tagged-2.osm.pbf  (identical)
      osmium fileinfo -e: nodes 135023, ways 23887, relations 14, bbox (-118.5883364,33.9597942,-118.3176785,34.1576638)
      CHECK4 null_score=0 gated_scored=0 malformed=0 scored=23474 refused=0 not_a_road=413   exit 0
  R2's assemble bound was set from T-0168's 3m33.557s for 11,740 rows; the assembler measured 42s and 52s here
  (3.7 ms/row, not 18.2), so grid-b never came near the 600 s cap and the second split at -118.40 did not fire.
  THE GATES, as a number and not smoothed (inherited F2): 1,927/11,239 = 17.1% of grid-a and 3,696/23,474 = 15.7%
  of grid-b are gated; `points_of_interest_absent` is every row in both, which is inherited F3.
- 2026-09-19T09:25:57Z THE SEAM, measured rather than assumed (R2 said it would be). The union over `way_id` is
  **34,523 scored ways**, 190 of them in BOTH clips, and **160 of those 190 carry DIFFERENT scores in the two
  clips** - grid-b's value is the higher one in every case I printed:
      way 1533792498 Mulholland Drive (secondary):   grid-a 0.6988 vs grid-b 0.7022
      way 225322766  Stone Canyon Road (residential): grid-a 0.6798 vs grid-b 0.6830
      way 399301293  West Sunset Boulevard (secondary): grid-a 0.6308 vs grid-b 0.6372
      way 958032573  (service):                      grid-a 0.5041 vs grid-b 0.5167
  So a way's score DEPENDS ON THE WINDOW IT WAS SCORED IN, by up to ~0.013 unit here. `osmium extract` completes
  every way that crosses the boundary, so this is not truncated geometry - it is a term computed against the
  clip's own population. NOT FIXED here (it is not this task's acceptance and fixing it changes the index): it is
  STILL OPEN 4 below, and the merged fixture takes the HIGHER of the two values for an overlapping way so that the
  seam can never make this task's predicate true by a choice of mine.
- 2026-09-19T09:25:57Z THE COMPARISON (R3): **THE PREDICATE IS FALSE. T-0204 FAILS ITS OWN ACCEPTANCE, and that
  refutation is this task's deliverable.** `C10`, re-read from the shipped canyon read-back rather than copied from
  prose, is way 1237332026 Fernwood Pacific Drive at **0.7284** - exactly the number R3 ruled. Two ways in the grid
  window's top ten are NOT below it:
      way 518410361 Mulholland Drive (secondary) 0.7361   - above C10 by 0.0077
      way 787842196 Mulholland Drive (secondary) 0.7299   - above C10 by 0.0015
  WHY, from the scored rows and not from a story: both are Mulholland Drive, and this window's northern edge
  (34.15) runs along the Santa Monica Mountains crest, so the "mixed street grid" bbox the Brief chose CONTAINS
  ridge road. The disconfirmation the Brief hoped for - "Wilshire, Sunset through Brentwood, or a Westwood
  residential grid outranks Topanga" - DID NOT HAPPEN: no Westwood, Century City, Culver City or Mar Vista grid
  way is anywhere in either clip's top 25, and the best flat-grid way in the whole window is West Sunset Boulevard
  at 0.6372, 0.09 below C10. What outranks Fernwood Pacific is other canyon-rim road. The index is not shown wrong
  by this window; the ACCEPTANCE as written is shown false, because the window is not the pure street grid the
  Brief assumed it was. The honest verdict is BOTH, and the test stays red until a task re-rules it with a window
  that is measured before its acceptance is written.
  `tests/test_window_ranking.py::test_the_grid_windows_top_ten_ranks_below_the_canyon_windows` therefore FAILS on
  the committed fixtures, by design and in the open. RED FIRST, as R3 ruled, on the swapped fixtures (the canyon
  read as the grid): `10 of the grid window's top ten are not below the canyon window's tenth (0.7189, Oakmont
  Street)`. And NOT VACUOUS: `test_the_predicate_can_hold` passes the same `outranking()` over a window shifted
  0.2 below, so the red is a fact about the data, not about the test.
  Fixtures: `services/etl/tests/fixtures/canyon_top25.json` and `grid_top25.json`, top 25 rows each, exactly the
  fields `scenecheck.top` produces, each with a `meta` naming its window, its read-back file, its way counts and
  the run that made it; the grid's `meta` carries the 160 seam disagreements. The 7 MB and 14.7 MB scored tables
  are not committed.
- 2026-09-19T09:25:57Z THE SECOND READ FOR THE OWNER - the grid window's top ten beside the canyon's. THE
  JUDGEMENT IS THE OWNER'S; what follows is the list, with every `highway=service` row named as R4 requires.
      THE GRID WINDOW (-118.55,33.98,-118.35,34.15), 34,523 scored ways:
       1  518410361  Mulholland Drive          secondary    34.12901,-118.41419  7 (0.7361)
       2  787842196  Mulholland Drive          secondary    34.12190,-118.39168  7 (0.7299)
       3  44327906   Mulholland Drive          secondary    34.12966,-118.49984  7 (0.7261)
       4  13419334   Crescent Drive            residential  34.11136,-118.38281  7 (0.7228)
       5  632613339  Sullivan Fire Road        SERVICE      34.08006,-118.51514  7 (0.7227)
       6  518410363  Mulholland Drive          secondary    34.12639,-118.41513  7 (0.7226)
       7  13290126   Sullivan Ridge Fire Road  SERVICE      34.06745,-118.50683  7 (0.7215)
       8  13292286   Franklin Canyon Drive     unclassified 34.12590,-118.40986  7 (0.7203)
       9  13379402   Scenario Lane             residential  34.10865,-118.44870  7 (0.7201)
      10  121304178  Oakmont Street            residential  34.07124,-118.49427  7 (0.7189)
      THE CANYON WINDOW (T-0168, -118.75,34.02,-118.55,34.15), 11,740 scored ways:
       1  74344132   Topanga Canyon Boulevard        primary   34.07333,-118.58840  8 (0.7722)
       2  74344113   Topanga Canyon Boulevard        primary   34.05578,-118.58240  8 (0.7697)
       3  667514937  North Topanga Canyon Boulevard  primary   34.10243,-118.59144  8 (0.7679)
       4  358703394  Stunt Road                      tertiary  34.08832,-118.66132  8 (0.7563)
       5  456361801  North Topanga Canyon Boulevard  primary   34.12122,-118.59311  7 (0.7464)
       6  38311860   Topanga Canyon Boulevard        primary   34.14147,-118.60791  7 (0.7401)
       7  1079750100 Old Topanga Canyon Road         secondary 34.12402,-118.63121  7 (0.7367)
       8  46752395   Old Topanga Canyon Road         secondary 34.10879,-118.62923  7 (0.7314)
       9  13346012   Piuma Road                      tertiary  34.07117,-118.69433  7 (0.7306)
      10  1237332026 Fernwood Pacific Drive          tertiary  34.08117,-118.60260  7 (0.7284)
  TWO of the grid's ten are `highway=service` fire roads (rows 5 and 7) - inherited F1, named as ruled: they are
  dirt/paved fire roads above Brentwood, and whether the owner would DRIVE them is exactly the judgement no agent
  makes here. The canyon window's ten carry four 8s; the grid window's ten carry none. Quantised to the 0..10 the
  router holds, EVERY row of both lists is a 7 or an 8 - which is itself worth the owner's eye: the four bits do
  not separate Topanga from a Brentwood residential street, only the unit score does.
- 2026-09-19T09:25:57Z STILL OPEN after this task (named, not fixed):
  1. THE ACCEPTANCE IS REFUTED: the grid window's top ten do NOT all rank below the canyon window's tenth (two
     Mulholland Drive segments, above). `test_window_ranking.py` is RED on `main` until a task rules on it. The
     two candidate rulings - "the index is wrong" and "the bbox was not a street grid" - are both live, and this
     task does not get to pick, because its own author chose the bbox.
  2. THE SEAM: a way scored in two overlapping clips gets two different scores (160 of 190 overlaps). The score is
     window-relative. Nothing downstream knows that.
  3. INHERITED F1: `highway=service` ranks with roads; two fire roads are in the grid's top ten.
  4. INHERITED F3: `points_of_interest_absent` on every way in both windows (T-0164 has not landed) - the two
     rankings are missing the SAME term, which is what makes the comparison fair AND provisional.
  5. INHERITED F5: `extract.Osmium.rel()` still cannot see the shared inputs directory from a worktree. This run
     did not call `etl.extract`, so it did not hit it.
- 2026-09-19T09:25:57Z THE ACCEPTANCE BLOCK, re-run bare at the final pre-review commit and re-quoted:
      python ops/mutate/scenic_tags.py -> MUTATIONS: 28 caught, 0 missed, 0 skipped, of 28 / EQUIVALENT: 0 caught,
        2 missed, 0 skipped, of 2 / MUTATE OK  caught=28/28 equivalent_caught=0 (floor 28)
      python ops/mutate/scenic_tags.py --prove-vacuity -> VACUITY: 0 caught, 28 missed, 0 skipped, of 28 /
        VACUITY PROVED
      cd services/etl && python -m pytest tests -rs -o addopts= -> 1 failed, 1149 passed in 80.35s - ZERO SKIPS.
        The one failure is `test_the_grid_windows_top_ten_ranks_below_the_canyon_windows`, this task's finding.
        `ops/test` and CI are RED on this branch for that reason and no other.
      bash ops/lib/check-line-cap -> P-SRC-02: 78 Swift files tracked (Sources=27, Tests=38, apps/ios=13), none
        over 300 lines
      bash ops/lib/check-exec-bits -> P-OPS-01: 73 files, 23 required present, all modes correct
      bash ops/queue-check -> QUEUE OK (199 tasks)
      bash ops/check-pins --source-only -> quoted in the commit that follows
      wc -l: scenecheck.py 215, test_scenecheck.py 217, test_window_ranking.py 60, scenic_tags.py 300,
        this task file 136 before this block
- 2026-09-19T10:07:37Z THE ORCHESTRATOR'S RULING ON THE REFUTATION, received from agent/claude-fable-5-1 (the
  filer of this task) and recorded VERBATIM before any code was written, as the author rule requires:
  "The acceptance predicate was mis-specified by its filer: the bbox it named contains canyon-rim road. The
  finding stands as written and is not hidden. The committed test becomes the WHITELIST form of the same
  fact (CLAUDE.md: anchor on a whitelist): the ONLY grid-window ways at or above the canyon window's tenth
  score are the ridge segments named in a typed allowlist - today exactly ways 518410361 and 787842196,
  both named Mulholland Drive - and any OTHER way reaching the bound (a Westwood, Brentwood or Bel Air
  street, a fire road) is RED by name. The bound is pinned to way 1237332026 Fernwood Pacific Drive at
  0.7284. The product findings are filed: T-0207 (three residential hillside streets and two service fire
  roads reach scenic_score 7 and escape the plan's anti-rat-run clause) and T-0208 (scores are
  window-relative: 160 of 190 seam ways differ)."
  WHAT I CHANGED UNDER IT, and what I did not: the measured numbers, the fixtures and the two named
  offenders are untouched - the refutation is still asserted, way by way. What changed is its FORM: a test
  that was red on main (hiding any later regression under an already-red name) becomes a whitelist that is
  green today and names the way on the day a third road reaches the bound. `ops/test` and CI core go green
  with this commit for that reason and no other.
- 2026-09-19T10:07:37Z R5 THE UNIT IS PART OF THE CONTRACT, ruled by agent/claude-opus-5 before code, on the pre-review
  mutant pass's survivors. The predicate this whole task turns on is read on `scenic_score_unit`, and that
  number had NO contract: `top()` did `float(tags.get(KEY_UNIT, detail) or 0.0)`, which ranks a way whose
  unit is ABSENT on its integer (silently, off by a factor of ten), raises ValueError on `abc`, and sorts a
  `nan` wherever the sort leaves it - every comparison against NaN being False. So `classify` - the ONE
  place a way is judged, both halves asking it - now names a way MALFORMED (CHECK4 malformed=N, exit 4,
  never a traceback out of `top()` or `main()`) when its unit is missing on a scored way, is not a real
  ASCII number, is outside 0..1, or does NOT quantise to the integer beside it. The quantiser is IMPORTED
  AND CALLED (`tagwriter.quantise(unit) != value`), never restated: a second copy of the rounding is how
  the writer and the checker agree with each other while both are wrong about a road.
  THE POPULATION: seven new mutations in `ops/mutate/scenic_tags.py`, floor 28 -> 35, and the runner hit
  the 300-line cap, so the table moved to `ops/mutate/scenic_tags_mutations.py` the way
  `geometry_mutations.py` is split out of `geometry.py` - the runner is the protocol, that file is the
  evidence. `tests/test_scenecheck_unit.py` is the third file the harness empties for `--prove-vacuity`.
  ONE EQUIVALENT with a witness, not prose: the NaN guard in `unit_or_none` cannot change what this module
  answers today, because `classify` asks the range next and `not 0.0 <= nan <= 1.0` is True either way; it
  is kept so the parser never hands a NaN to a future caller. It is an EQUIVALENT entry and must go MISSED.
- 2026-09-19T10:07:37Z THE BOUNDARIES AND THE BINDING, as tests over the SHIPPING symbols (`scenecheck.counts`, `.top`,
  `.main`), never a helper: the integer at 11 and -1 (an off-by-one bound is the bound a 42 never tests)
  and at 10 and 0 the other way; the non-ASCII digit guard on BOTH halves (`int("\u0667")` is 7 and
  `float("\u0660.\u0665")` is 0.5 to Python); and `test_the_fixture_row_is_the_shape_the_shipping_oracle_produces`,
  which runs `etl.scenecheck.top` over a COMMITTED read-back
  (`tests/fixtures/window_readback_sample.osm.xml`, four real canyon ways with their own 198 nodes and
  their shipped `scenic_*` tags, cut out of `window-readback.osm.xml`, 23,794 B) and requires the rows to
  carry exactly the fixtures' fields, contiguous ranks, descending units, `malformed=0`, and the same
  values the canyon fixture holds for the ways they share. The fixtures can no longer drift away from what
  the oracle produces without a test saying so.
- 2026-09-19T10:07:37Z THE WHITELIST TEST, RED FOUR WAYS THEN GREEN (`services/etl/work/reddemo.py`, under the
  gitignored work dir; caches purged and 1.1 s slept between runs so no stale .pyc reports a false colour):
      GREEN BEFORE                                                     10 passed
      RED 1  the bound read from canyon row 0 instead of its tenth     2 failed - assert 74344132 == 1237332026
             FAILED test_the_bound_is_the_canyon_windows_tenth_way_by_the_unit_and_its_measured_value
      RED 2  the grid fixture stored sorted by way_id                  1 failed - assert [7, 8, 11, 25, ...] == [1, 2, 3, ...]
             FAILED test_each_fixture_is_twenty_five_rows_ranked_contiguously_and_descending_by_the_unit[grid]
      RED 3  the two offender rows deleted from the grid fixture       2 failed - assert 23 == 25; assert set() == {518410361, 787842196}
      RED 4  Crescent Drive (residential) raised above the bound       1 failed - Extra items in the left set: 13419334
             FAILED test_the_only_grid_ways_reaching_the_bound_are_the_named_ridge_segments
      GREEN AFTER                                                      10 passed
  A TIE AT THE BOUND IS NOT BELOW, pinned by a fixture and not by prose: `tests/fixtures/grid_tie_top25.json`
  is the grid's 25 rows with the two allowlisted Mulhollands lowered 0.05 and way 44327906 set EXACTLY to
  0.7284; `test_a_tie_at_the_bound_counts_as_not_below` requires that row to be an offender, which is the
  `>=` R3 ruled and not `>`.
  THE SEAM-MERGE RULE that built `grid_top25.json` is now recorded in the fixture's own `meta.seam_merge` -
  the merged ranking is the UNION KEYED BY way_id and an overlapping way is taken at the MAX of its two
  clips, so the seam can never make this task's predicate true by a choice of mine - and
  `test_the_seam_merge_rule_is_recorded_and_the_rows_obey_it` checks every seam row in the fixture against
  `max(grid_a, grid_b)`.
- 2026-09-19T10:07:37Z THE REAL READ-BACKS RE-RUN THROUGH THE HARDENED CHECKER, no container, `python -m etl.scenecheck
  <file> --top 10` on each of the three shipped read-back XMLs (grid-a and grid-b from this worktree's
  gitignored work dir, the canyon window's from the MAIN checkout, both read-only):
      grid-a-readback.osm.xml   CHECK4 null_score=0 gated_scored=0 malformed=1  scored=11238 refused=0 not_a_road=212
      grid-b-readback.osm.xml   CHECK4 null_score=0 gated_scored=0 malformed=14 scored=23460 refused=0 not_a_road=413
      window-readback.osm.xml   CHECK4 null_score=0 gated_scored=0 malformed=2  scored=11738 refused=0 not_a_road=662
  MALFORMED IS NOT 0 ON REAL DATA, and that is A FINDING, reported and not smoothed (STILL OPEN 6 below).
  All 17 are ONE shape - `scenic_score_unit` quantises to exactly one MORE than the `scenic_score` beside
  it, and every unit involved ends in `5` at the fourth decimal:
      way 170301018  scenic_score=0: scenic_score_unit=0.0500 quantises to 1, not the 0 beside it  (grid-a)
      way 13332407   scenic_score=5: scenic_score_unit=0.5500 quantises to 6, not the 5 beside it  (grid-b)
      way 13359647   scenic_score=1: scenic_score_unit=0.1500 quantises to 2, not the 1 beside it  (canyon)
      way 1280073443 scenic_score=2: scenic_score_unit=0.2500 quantises to 3, not the 2 beside it  (canyon)
      ... 14 of the 17 in grid-b, one in grid-a, two in the canyon window; every one named on stderr.
  THE CAUSE, from `tagwriter.tags_for_row` and not from a story: the integer is `quantise(row["score"])`
  off the UNROUNDED score and the unit is `fixed(row["score"])` at four decimals, so a score just under a
  `.x5` boundary (0.54999...) ships as a `5` beside a `0.5500`. The two tags are one fact written twice at
  two precisions, and 17 of 46,436 scored ways disagree. NOT FIXED HERE: fixing it changes bytes the whole
  window run is measured on and needs its own container re-run, which this task's acceptance does not cover
  and which would re-open every count above. The ranking is unaffected - none of the 17 is in either top
  25, and all sit at units 0.05..0.55. `ops/sane` check 4 over these three files now exits 4, correctly:
  the oracle is stricter than the writer, which is what an independent oracle is for.
- 2026-09-19T10:07:37Z STILL OPEN after this commit, amending nothing above (1-5 stand as written):
  6. THE WRITER'S TWO TAGS DISAGREE AT THE `.x5` BOUNDARY: 17 real ways carry a `scenic_score` that is not
     `quantise(scenic_score_unit)`. Found by R5's new rule, named on stderr, unfixed - it belongs to
     `tagwriter`, needs a container re-run, and is a task of its own.
- 2026-09-19T10:28:56Z THE ACCEPTANCE BLOCK, re-run BARE at this final pre-review commit and re-quoted whole (the
  author rule; the 09:25:57Z block above stands as the record of the run that produced the fixtures, and
  every line below was re-run after the whitelist and R5 landed):
      python ops/mutate/scenic_tags.py -> BASELINE exit=0, 35 mutations, floor 35 / MUTATIONS: 35 caught,
        0 missed, 0 skipped, of 35 / EQUIVALENT: 0 caught, 3 missed, 0 skipped, of 3 /
        MUTATE OK  caught=35/35 equivalent_caught=0
      python ops/mutate/scenic_tags.py --prove-vacuity -> VACUITY: 0 caught, 35 missed, 0 skipped, of 35 /
        VACUITY PROVED
      cd services/etl && python -m pytest tests -rs -o addopts= -> 1170 passed in 88.55s - ZERO FAILURES,
        ZERO SKIPS. The refutation is no longer carried as a red test: it is
        test_the_only_grid_ways_reaching_the_bound_are_the_named_ridge_segments, green, naming both ways.
      bash ops/lib/check-line-cap -> P-SRC-02: 78 Swift files tracked (Sources=27, Tests=38, apps/ios=13),
        none over 300 lines
      bash ops/lib/check-exec-bits -> P-OPS-01: 74 files, 23 required present, all modes correct
        (74 and not 73: ops/mutate/scenic_tags_mutations.py, a module and not a script, 100644 exactly as
        ops/mutate/geometry_mutations.py is)
      bash ops/queue-check -> QUEUE OK (199 tasks)
      bash ops/check-pins --source-only -> PINS ok=13 skipped=14 pending=1 expired=0 failed=0 tier=linux
        source-only (exit 0)
      python -m etl.scenecheck <the three real read-backs> --top 10 -> quoted in full in the entry above;
        malformed 1 / 14 / 2, which is still-open 6 and not a green
      wc -l (re-measured at this commit, the T-0162 rule): scenic_tags.py 179, scenic_tags_mutations.py 186,
        scenecheck.py 254, test_scenecheck.py 231, test_scenecheck_unit.py 173, test_window_ranking.py 173,
        this task file 364 before this block
- 2026-09-19T11:02:00Z REVIEW PASS by agent/rv1-pr113 on PR #113 at head 28e61e5 (== origin/task/T-0204), in a
  detached worktree .worktrees/rv1-pr113 at that sha. Everything below is a command I ran and output I read.
  THE GATES, bare: cd services/etl && python -m pytest tests -rs -o addopts= -q -> 1170 passed in 89.59s (zero
  failures, zero skips; -rs printed no skip summary). python ops/mutate/scenic_tags.py -> MUTATIONS: 35 caught,
  0 missed, 0 skipped, of 35 / EQUIVALENT: 0 caught, 3 missed, 0 skipped, of 3 / MUTATE OK caught=35/35
  equivalent_caught=0. --prove-vacuity -> VACUITY: 0 caught, 35 missed, 0 skipped, of 35 / VACUITY PROVED.
  bash ops/lib/check-line-cap -> P-SRC-02: 78 Swift files tracked, none over 300 lines. bash
  ops/lib/check-exec-bits -> P-OPS-01: 74 files, 23 required present, all modes correct. bash ops/queue-check ->
  QUEUE OK (199 tasks). wc -l re-measured independently: scenecheck.py 254, test_scenecheck.py 231,
  test_scenecheck_unit.py 173, test_window_ranking.py 173, scenic_tags.py 179, scenic_tags_mutations.py 186 -
  every number the 10:28:56Z block quotes, confirmed.
  THE THREE REAL READ-BACKS, re-run with python -m etl.scenecheck <file> --top 10 (grid-a and grid-b read-only
  from .worktrees/T-0204/services/etl/work/la/, the canyon window's from the MAIN checkout): CHECK4 malformed=1
  scored=11238 / malformed=14 scored=23460 / malformed=2 scored=11738, null_score=0 and gated_scored=0 on all
  three - the Log's numbers exactly, including still-open 6. The canyon top ten ends way 1237332026 Fernwood
  Pacific Drive 7 (0.7284), the bound the whitelist is read against; the union of the two grid clips' top tens
  under the MAX seam rule is the Log's merged grid top ten, 518410361 at 0.7361 and 787842196 at 0.7299 first.
  MUTANTS ON THE REVIEW WORKTREE, each restored with git checkout -- and git status --short empty after: the
  pre-review pass's four survivors REPLAYED - bound read from canyon row 0 -> 2 failed, named; grid fixture
  sorted by way_id -> test_each_fixture_is_twenty_five_rows_ranked_contiguously_and_descending_by_the_unit[grid];
  the two offender rows deleted -> 2 failed including
  test_the_only_grid_ways_reaching_the_bound_are_the_named_ridge_segments; Crescent Drive (residential) raised
  above the bound -> that same test, by name. THREE OF MY OWN, all RED: top() sorted ASCENDING -> 3 failed
  (test_the_fixture_row_is_the_shape_the_shipping_oracle_produces and two more); the quantise contradiction
  compared to ITSELF -> test_a_unit_that_does_not_quantise_to_the_integer_beside_it_is_malformed and
  test_the_quantisation_is_the_writers_own_and_not_a_second_copy; the committed read-back sample made MALFORMED
  (way 38311860 unit 0.7401 -> 0.9401 beside scenic_score 7) ->
  test_the_fixture_row_is_the_shape_the_shipping_oracle_produces, on the malformed==0 assertion. A FOURTH of my
  own: an allowlisted way RENAMED in the fixture (518410361 -> "Sullivan Fire Road") -> red, so the whitelist is
  read on id AND name. Neither a wrong ranking nor a malformed read-back passes green.
  THE RULING, judged: the whitelist form is an HONEST RESTATEMENT of the refutation, not a way to make a red
  test green. The two ways are still asserted by id and by value (the fixture rows are untouched), the bound is
  pinned to way 1237332026 at 0.7284, and a third way at the bound - or a renamed allowlisted one - is red BY
  NAME, which the red-4 replay demonstrates. The refutation is on the PR's title line, in the ruling quoted
  verbatim at 10:07:37Z before any code, and in the test file's own header; the PR body says the ORIGINAL
  acceptance is false in its first sentence. The Log is append-only (the only deletion anywhere under queue/ in
  the whole diff is the touches: line, widened at 07:53:05Z with its reason). Still-open 6 is reported, not
  smoothed, and reproduced above. NOTHING BLOCKING. Findings recorded for later tasks, none blocking: the
  whitelist reads the committed fixture, so it binds a re-run only through
  test_the_fixture_row_is_the_shape_the_shipping_oracle_produces (shape, not the window's values) - a fresh
  container run of either window is unmeasured until a task re-records the fixtures; and grid-a's own top ten
  holds three unnamed service ways, which is inherited F1 and T-0207's subject.
- 2026-09-19T11:27:25Z MERGE origin/main into task/T-0204 after sign-off (bc29eff), by agent/claude-fable-5-1 (orchestrator): one conflict, ops/mutate/scenic_tags.py - #114 (T-0186) added SUBJECT_MODULES beside path constants this branch had moved into scenic_tags_mutations.py; resolved by keeping this branch's split and adding only the SUBJECT_MODULES declaration; nothing else touched. Re-run at the merge commit: python ops/lib/check-mutate-population.py -> 'every added module is covered or allowlisted; the floor of 22 holds'; python ops/mutate/scenic_tags.py -> 'MUTATE OK  caught=35/35 equivalent_caught=0'; cd services/etl && python -m pytest tests -rs -o addopts= -> '1170 passed in 90.63s', zero skips.
