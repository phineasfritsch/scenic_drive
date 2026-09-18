---
id: T-0163
title: ETL way record and region normaliser - raw per-way terms in, the 0..1 terms score.py consumes out, deterministically
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:52:39Z
lease_expires_at: 2026-09-19T03:52:39Z
worktree: .worktrees/T-0163
branch: task/T-0163
exclusive: []
touches: [services/etl/etl/way_record.py, services/etl/etl/normalise.py, services/etl/tests/test_way_record.py, services/etl/tests/test_normalise.py, services/etl/tests/test_way_records_fixture.py, services/etl/tests/fixtures/, Tests/Fixtures/scoring/]
pins_affected: []
reviewer: null
depends_on: [T-0154]
verify: [ops/test, ops/check-pins]
acceptance:
  - "THE END-TO-END CHECK THIS TASK EXISTS FOR, green: `cd services/etl && python -m pytest tests/test_way_records_fixture.py -rs` inside the full run below. 240 raw ways from `tests/fixtures/way_records_fixture.json` -> `normalise.normalise_region` -> `score.score` for every row: `test_no_row_is_refused_and_every_score_is_in_zero_to_one`, `test_every_zero_class_row_scores_exactly_zero` (exactly 0.0, on all 51), `test_no_scorable_row_scores_zero` (ruling R2's consequence), `test_every_expected_rank_is_the_rank_the_normaliser_computes` (exact equality against the generator's pairwise oracle, `populationCount * len(RANKED_TERMS)` ranks checked, asserted in the test)"
  - "`cd services/etl && python -m pytest tests -rs` -> `549 passed in 79.04s (0:01:19)` at bf17b30 and `549 passed in 71.18s (0:01:11)` re-run at this tree, exit 0 both times, and the `-rs` short summary printed NOTHING either time: zero skips. The wall clock moves on a shared box; the 549 and the zero skips do not. The same command at the merge-base (9939d39, before this task) printed `472 passed in 80.53s (0:01:20)`. The three new files alone: `python -m pytest tests/test_way_record.py tests/test_normalise.py tests/test_way_records_fixture.py -rs` -> `77 passed in 0.34s`"
  - "`bash ops/lib/check-pipe-consumers` -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0"
  - "`bash ops/queue-check` -> `QUEUE OK (158 tasks)`, exit 0"
  - "THE FIXTURE IS DETERMINISTIC AND ITS EXPECTATIONS ARE COMPUTED BY NOTHING IN `etl/`. `python services/etl/tests/fixtures/generate_way_records.py` at the committed tree -> `ways=240 covering=80 random=160` / `population=189 excluded=51 tied values across ranked terms=369` / `distinct highway classes=14  ways with a byway status=110  ways with points_of_interest=5`, and `git status --short` printed nothing afterwards. `naive_rank` in the generator counts ways below and ways equal pairwise; `normalise.percentile_ranks` groups a sorted order. The generator imports `json`, `pathlib`, `random` and nothing else"
  - "NINE MUTATIONS, three per new module plus three on the fixture and its oracle, each applied ALONE and restored to its pristine md5, each caught by a NAMED test. NO SURVIVORS. The table with the exact `FAILED` lines is in the Log at 2026-09-18T20:16:29Z. The sharpest: the sort key (`sorted(values, key=lambda way_id: (values[way_id], way_id))` -> `values[way_id]`) is caught by exactly one test in the repository, `test_the_order_is_by_value_then_way_id_not_insertion_order`, because the mid-rank formula makes the within-tie order invisible in the numbers - which is why `ranked_order` is public"
  - "ONE GENUINE RED FOUND WITHOUT MUTATING, quoted verbatim in the Log: `test_the_raw_rows_could_not_have_been_scored` asserted that raw producer units always answer None and printed `AssertionError: [(700000037, 0.3325295375632337)]` - the way at the region's floor (curvature 0.0, elevation_gain 0.0, relief 0.0, sinuosity 1.0, furniture 0.0) is inside 0..1 and scores a plausible number. The test now asserts the true and sharper property (`test_and_the_scorer_alone_would_not_have_caught_them`): a scorer can only refuse units it can SEE, so the guard has to be the record's state"
  - "`wc -l` at the final commit, and `len(text.splitlines())` agrees on every one: `way_record.py` 233, `normalise.py` 128, `test_way_record.py` 212, `test_normalise.py` 185, `test_way_records_fixture.py` 213, `generate_way_records.py` 251, `way_records_fixture.json` 254. Under the 300-line cap, unenforced on Python though it is (T-0058). One type per file: `WayRecord` is the only class in `way_record.py`; `normalise.py` is functions, as `score.py` is"
  - "NOT IN THIS TASK: the producers themselves (`sinuosity`, `tunnel_meters`, `meters_to_nearest_motorway` are T-0161; `speed_fit` and `furniture` T-0162; `points_of_interest` T-0164), the `scenic_score` 0..10 column, the corpus writer, and any run over a real region - no real raw terms exist on main yet, so the normaliser has never seen one. `ops/test` and `ops/check-pins` were NOT run: on this box the default swift scratch path does not build inside a worktree. `Tests/Fixtures/scoring/` is in `touches:` and was not touched. No pin added (P-DATA-01 is the plan's). See STILL OPEN"
---
## Brief

One of three disjoint pieces T-0146 was split into by the 2026-09-18 13:13 panel (CODE lens, grounded; the
grounding pass ruled against a separate "seam" PR - `score.py:119-122`'s keyword-only names ARE the seam, so
the record type rides in this task). The producers on main return different kinds of number:
`curvature.way_curvature` (curvature.py:172), `terrain.elevation_gain` / `relief` (terrain.py:85, :112) are
unbounded raw units; `landcover.fractions` is already 0..1; T-0161 will add raw `sinuosity` and metres, T-0162
a 0..1 `speed_fit` and a raw `furniture` rate. `score.py` wants every UNIT_TERM in 0..1.

**Owner's ruling on what gets ranked (the plan and T-0146's brief disagree; this settles it - record it in
your Log with both pointers and argue if the code proves it wrong):** plan:89 rank-normalises only photo
density; T-0146's brief says rank-normalise "each". RULED: a term that arrives UNBOUNDED - curvature,
elevation_gain, relief, sinuosity, furniture - becomes its REGION PERCENTILE RANK in [0,1], computed over the
SCORABLE ways of the region only (the four zero classes are excluded from the population: they score 0
whatever their terms, and 15k motorway segments must not set the curve for back roads). A term that arrives
as a fraction - canopy, impervious, water - or as a designed 0..1 function - speed_fit - is MAPPED as is,
never ranked. `points_of_interest` is neither: it is ranked within 50 km with its top decile penalised
(plan:89), needs the network, and is T-0164 - until it lands the record carries it as an explicit
`None -> 0.0 with a flag`, never a silent default.

**Build:**
1. `way_record.py` - the per-way record: fields 1:1 with `score.score`'s keyword names, each declared RAW or
   UNIT, plus `way_id`, `highway`, `surface`, `byway_status`, `tunnel_meters`, `meters_to_nearest_motorway`;
   a validator that REFUSES by field name (a UNIT field outside 0..1, a RAW field negative or non-finite, an
   unknown field). One type per file.
2. `normalise.py` - region percentile rank: deterministic (sort by value then `way_id`; ties take the average
   rank; a population of one, or all-equal values, is a NAMED case with a stated answer, not a division by
   zero); idempotent (normalising an already-normalised region is refused by name, not silently re-ranked -
   the record says which state it is in); zero classes excluded from the population and passed through.
   P-DATA-01 (ETL idempotent) is the plan's pin for this property - do not add a pin here, say so under STILL
   OPEN.
3. A committed raw-term fixture with a generator in the style of `Tests/Fixtures/scoring/generate.py` (seeded,
   deterministic, re-running leaves `git diff` empty), whose expected ranks come from a naive transcription
   inside the generator, NEVER from `normalise.py`. Then the end-to-end check this task exists for: raw
   fixture -> `normalise` -> `score.score` for every row runs with no refusal and every score in [0,1], the
   zero-class rows exactly 0.0.

**The author rule (it took PR #89 through review in one round):** rule every source disagreement in your Log
BEFORE writing code (the ranking ruling above is the first entry); re-run and quote the whole acceptance
block at your FINAL commit; close your own verifier's findings before the review is bought. Every new test
RED by name first (three mutations per module: the tie rule, the population filter, the sort key), then green.
Check `queue/*/T-0112-*` and `queue/*/T-0050-*` for overlap before you start and say what you found.

## Log
- 2026-09-18T20:20:00Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
- 2026-09-18T19:52:39Z claimed by agent/claude-opus-5; lease until 2026-09-19T03:52:39Z
- 2026-09-18T19:59:41Z agent/claude-opus-5 (owner, author). READ BEFORE ANY CODE: CLAUDE.md; the plan's
  "Score per way" block (plan:75-91); `services/etl/etl/score.py` end to end; `services/etl/etl/byways.py`
  (`SCENIC_ZERO_CLASSES`, `status_bonus`, `apply_to_e`); `services/etl/tests/test_score_contract.py`;
  `Tests/Fixtures/scoring/generate.py`; the producer signatures `curvature.way_curvature` (curvature.py:172),
  `terrain.elevation_gain` (terrain.py:85), `terrain.relief` (terrain.py:112), `landcover.fractions`
  (landcover.py:87); `services/etl/tests/test_landcover_fixture.py` for the fixture-test style;
  `.githooks/pre-commit`'s `touches:` matcher (prefix match, `queue/*` always allowed).

  RULING R1 - WHAT GETS RANKED. Pointers: plan:89 ("Commons photo density rank-normalized in 50 km, top
  decile penalized" - photo density and nothing else) vs T-0146's brief ("rank-normalise each") vs this
  task's Brief (the owner's ruling above). RULED as the Brief states, and the code agrees rather than merely
  permitting it: `curvature.way_curvature` returns a sum of weighted segment lengths (curvature.py:172-186),
  `terrain.elevation_gain` returns metres of climb (terrain.py:85-102) and `terrain.relief` metres of range
  (terrain.py:112-130) - three different unbounded units, and no fixed divisor can map metres of climb to
  0..1 without inventing a ceiling; `landcover.fractions` already returns 0..1 per class (landcover.py:87-103)
  and ranking a fraction would throw away the only absolute scale in the mean. So: RANKED_TERMS = curvature,
  elevation_gain, relief, sinuosity, furniture. MAPPED_TERMS = canopy, impervious, water, speed_fit.
  DEFERRED_TERMS = points_of_interest (T-0164). Their union is asserted equal to `score.UNIT_TERMS` by name,
  so a term added to score.py cannot arrive unclassified.

  RULING R2 - WHICH PERCENTILE ESTIMATOR. plan:89 says "rank-normalized" and names no estimator; the Brief
  adds three requirements (ties take the average rank; a population of one and an all-equal population are
  NAMED cases with a stated answer; never a division by zero). Two candidates: (a) `(rank-1)/(n-1)`, which
  reaches exactly 0.0 and 1.0 and is 0/0 at n=1; (b) the mid-rank form `(below + 0.5*equal)/n`, which IS the
  tie group's average 1-based rank mapped by `(rank - 0.5)/n`. RULED (b): one formula satisfies all three
  requirements with no special case - n=1 gives 0.5, an all-equal population gives 0.5 to every way, and n>=1
  makes the divisor non-zero by construction. Stated consequence, now an asserted end-to-end property: a rank
  is never exactly 0.0 or 1.0, so ranking alone cannot zero a scorable way's score, and "only motorway/trunk
  score 0" (CLAUDE.md, Product invariants) stays true of the normalised corpus.

  RULING R3 - WHAT A ZERO-CLASS WAY CARRIES. The Brief says the four zero classes are "excluded from the
  population and passed through" and is silent on what their ranked terms then hold. The code decides it:
  `score.score` refuses out-of-range terms at score.py:131-132 and only reaches the zero-class branch at
  score.py:139-140, so a motorway row still carrying raw metres returns **None, not 0.0** - the end-to-end
  check this task exists for would fail on exactly the rows it is about. RULED: a third record state,
  `EXCLUDED`, in which the five ranked fields hold the named constant `EXCLUDED_RANK = 0.0` and are not
  readable as measurements, while the mapped terms pass through untouched. The validator enforces that
  equality by field name, so an excluded record cannot quietly carry a rank.

  RULING R4 - IDEMPOTENCE IS A REFUSAL. Brief: normalising an already-normalised region is refused by name.
  `terms_state` on the record is that name (`raw` / `normalised` / `excluded`), and `score_kwargs()` refuses
  in the `raw` state rather than handing raw metres to a scorer that would answer None. P-DATA-01 is the
  plan's pin for ETL idempotence; no pin is added here - see STILL OPEN.

  RULING R5 - FURNITURE IS RANKED, NOT INVERTED HERE. `score.scenery_mean` enters furniture as
  `(1 - furniture)` (score.py:92). T-0162 produces a raw furniture RATE. So the record carries the rank and
  score.py keeps the inversion: two inversions would cancel and no single-module test would see it. Asserted
  end to end instead: of two ways alike but for their furniture rate, the busier roadside scores lower.

  RULING R6 - SINUOSITY GETS NO FLOOR. Sinuosity is >= 1.0 by construction (path length / straight-line
  distance), but the Brief's RAW rule is "negative or non-finite" and a >= 1.0 floor here would be a claim
  about T-0161's not-yet-existing output that this task cannot verify. Not added; the rank is invariant to
  any monotone shift anyway.

  OVERLAP, as the Brief asks. `queue/backlog/T-0112-*` (curvature-per-km saturates and ranks rat-runs):
  touches `services/etl/etl/score.py`, `tests/test_score_rank_order.py`, `tests/fixtures/`. It argues which
  raw number `curvature.py` should hand over - per-km or the raw sum - which is upstream of this task; this
  normaliser ranks whatever non-negative raw value arrives and its tests use both scales. No overlap with
  `way_record.py` or `normalise.py`. `queue/claimed/T-0050-*` (whether the scenic index adopts Curvature's
  six squash post-processors): the same upstream shape, a product decision about the raw value, `touches:
  [services/etl/]`. Neither blocks nor is blocked by this task. Sibling T-0161 shares the
  `services/etl/tests/fixtures/` touches prefix with this task; the filenames are disjoint
  (`way_records_fixture.json` / `generate_way_records.py` here).

  TOUCHES AMENDED in this commit: `services/etl/tests/test_way_records_fixture.py` added. The end-to-end
  check wants the repo's own `test_*_fixture.py` name (`test_landcover_fixture.py`,
  `test_terrain_fixture.py`, `test_byways_fixture.py`) and folding it into `test_normalise.py` would push
  that file at the 300-line cap. `Tests/Fixtures/scoring/` stays in the list and is NOT touched: the shared
  cross-language fixture is a snapshot reference (CLAUDE.md, Verification).
- 2026-09-18T20:16:29Z agent/claude-opus-5 (owner, author): the red runs and the mutation table, at
  bf17b30 + this entry.

  THE ONE RED I DID NOT HAVE TO MANUFACTURE. The first run of the fixture suite failed by name:
  `FAILED tests/test_way_records_fixture.py::TestTheWholePathScores::test_the_raw_rows_could_not_have_been_scored`,
  `AssertionError: [(700000037, 0.3325295375632337)]`, `1 failed, 75 passed in 0.55s`. I had asserted that
  raw producer units always answer None through `score.score`. They do not: way 700000037 is the fixture's
  region-floor row (curvature 0.0, elevation_gain 0.0, relief 0.0, sinuosity 1.0, furniture 0.0), every raw
  value of which happens to lie inside 0..1, so the scorer answered 0.3325295375632337 - a completely
  plausible number for a way whose terms had not been normalised. The assertion was wrong and the argument
  it was making was too weak: a scorer can only refuse units it can SEE. Replaced by two tests - every raw
  record refuses `score_kwargs()` by state (`test_no_raw_row_can_be_scored_through_the_record`), and the
  rows the scorer WOULD answer are measured and shown to answer something other than their normalised score
  (`test_and_the_scorer_alone_would_not_have_caught_them`). This is the strongest evidence in the task that
  ruling R3's state field is load-bearing rather than decoration.

  MUTATION TABLE. Nine mutations, each applied ALONE, the three new test files run with `--tb=no -q -rf`,
  then the file restored from a pristine copy kept outside the tree (a new file cannot be restored with
  `git checkout --`) and its md5 re-printed. `git status --short` at the end of the nine listed exactly the
  seven new files as untracked and nothing modified; `way_record.py` md5=e705f0c98d87731d8ff4ac76c55c3438,
  `normalise.py` md5=ddad9f8665b141c17b319daa6832872e,
  `generate_way_records.py` md5=ba675e91e14d5bc443bc6917c826ad2f,
  `way_records_fixture.json` md5=672a83aea9521f4e4214a22f1abc8904 before and after every one.

  N1 THE TIE RULE. `normalise.py`: `rank = (start + 0.5 * equal) / population` -> `(start + equal) /
  population`. 10 named failures, the estimator wholesale: `test_four_distinct_values_take_the_eighths`,
  `test_a_tie_group_takes_the_average_rank`, `test_a_tie_group_in_the_middle_takes_the_average_rank`,
  `test_a_population_of_one_is_its_own_median`, `test_an_all_equal_population_is_all_median`,
  `test_a_rank_is_never_exactly_zero_or_one`, `test_the_ranks_do_not_depend_on_the_order_rows_arrive_in`,
  `test_the_zero_classes_do_not_set_the_curve`,
  `test_normalising_returns_new_records_and_leaves_the_input_raw`,
  `test_every_expected_rank_is_the_rank_the_normaliser_computes`.

  N2 THE POPULATION FILTER. `normalise.py`: `population_of` returns `list(records)` - the zero classes back
  in the curve. 3 named failures: `test_the_zero_classes_do_not_set_the_curve`,
  `test_population_of_names_the_scorable_ways`,
  `test_every_expected_rank_is_the_rank_the_normaliser_computes`.

  N3 THE SORT KEY. `normalise.py`: `sorted(values, key=lambda way_id: (values[way_id], way_id))` ->
  `key=lambda way_id: values[way_id]`. EXACTLY 1 named failure in the whole repository:
  `test_the_order_is_by_value_then_way_id_not_insertion_order`. That is the point of making `ranked_order`
  public: with ties taking the average rank the within-tie order is invisible in the ranks, so nothing else
  could ever have caught it, and determinism across the order rows arrive in is a property this ETL is held
  to (P-DATA-01) rather than a preference.

  W1 A RAW TERM'S SIGN. `way_record.py`: `if value < 0.0:` -> `if value < -1.0:` in `_ranked_problems`.
  2 named failures: `test_a_raw_term_that_is_negative_is_refused_by_name`,
  `test_a_refused_region_leaves_its_input_untouched`.

  W2 A MAPPED TERM'S CEILING. `way_record.py`: `number > 1.0` -> `number > 1.0001` in `_unit_problem` - the
  sloppy tolerance somebody reaches for when a producer overshoots. 1 named failure:
  `test_a_mapped_term_above_one_is_refused_by_name`.

  W3 A SILENT DEFAULT FOR `points_of_interest`. `way_record.py`: `POI_ABSENT if poi is None` -> `0.5 if poi
  is None` - the exact defect the Brief's `None -> 0.0 with a flag` forbids, and the one that would be
  invisible in the corpus. 2 named failures:
  `test_an_absent_value_is_flagged_and_substituted_rather_than_guessed`,
  `test_the_substitution_is_visible_in_the_score`.

  F1 A HAND-EDITED FIXTURE. `way_records_fixture.json`: `  "wayCount": 240,` -> `241`. 2 named failures:
  `test_the_committed_bytes_are_what_the_generator_produces`, `test_it_is_the_population_it_claims`.

  F2 THE ORACLE'S TIE RULE, REGENERATED. `generate_way_records.py`: `naive_rank` returns
  `(below + equal) / len(population)`, then the fixture regenerated from the mutated generator so its bytes
  match again. 1 named failure: `test_every_expected_rank_is_the_rank_the_normaliser_computes`. This is the
  run that proves the oracle is load-bearing and independent: the byte-compare test stayed GREEN and only
  the differential went red.

  F3 THE ORACLE'S POPULATION, REGENERATED. `generate_way_records.py`: `expect()` ranks over `list(ways)`
  instead of excluding `PLAN_ZERO_CLASSES`, regenerated. 1 named failure:
  `test_every_expected_rank_is_the_rank_the_normaliser_computes`.

  NO SURVIVORS, so no test was added after the table.

  STILL OPEN, and none of it is in this PR.
  * `ops/test` and `ops/check-pins` were NOT run here. On this box the default swift scratch path does not
    build inside a worktree, and both wrap `swift test`; the task instruction is to say so and read
    `gh pr checks` once after pushing instead. The Python half of `ops/test` is the suite quoted above.
  * NO PIN ADDED, as the Brief directs: P-DATA-01 (ETL idempotent) is the plan's pin for the idempotence
    property, and `normalise_region`'s refusal of an already-normalised region is what it would assert.
    Nothing in `pins/` was touched and `pins_affected:` stays empty.
  * THE NORMALISER HAS NEVER SEEN A REAL REGION. No producer on main emits `sinuosity`, `furniture`,
    `speed_fit`, `tunnel_meters` or `meters_to_nearest_motorway` yet (T-0161, T-0162), and
    `points_of_interest` is T-0164, so the fixture is synthetic and says so in its own `note` field. The
    first run over real ways belongs to whoever wires `curvature`/`terrain`/`landcover` into a corpus
    (T-0030, T-0146's remainder). Until then the end-to-end check proves the ARITHMETIC and the seam, not
    that any road scores what it should.
  * WHICH RAW NUMBER CURVATURE HANDS OVER is still undecided (T-0112 per-km vs raw sum, T-0050's squashes).
    The rank is invariant to any strictly monotone transform, so the estimator here is unaffected - but the
    ORDER is not, and nothing in this task can settle it. The test named
    `test_a_raw_term_is_allowed_to_be_far_outside_zero_to_one` carries T-0112's measured 1817.5, so the
    record cannot start refusing that scale without a named failure.
  * POI's POPULATION IS NOT A REGION. plan:89 ranks photo density within 50 km with the top decile
    penalised. `percentile_ranks` ranks whatever population it is handed, so a 50 km window is expressible
    with no change here, but no windowing function and no decile penalty exists in this module - T-0164.
  * `generate_way_records.py` is committed 100644, matching `Tests/Fixtures/scoring/generate.py` (both
    verified with `git ls-files -s`). The exec-bit rule (P-OPS-01) covers `ops/` and `.githooks/` only, and
    this is run as `python <path>` exactly as the other generator is.
  * THE 300-LINE CAP IS STILL SWIFT-ONLY (`ops/lib/check-line-cap`, T-0058 open). Every file here is under
    it by measurement, not by the cap.
