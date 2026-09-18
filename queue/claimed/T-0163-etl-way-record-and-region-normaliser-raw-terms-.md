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
  - "THE REVIEW'S BLOCKING FINDING IS DEAD, BY NAME. Both surviving mutants from PR #93's review, each applied ALONE to `WayRecord.score_kwargs()` and restored: at 38fdcc7 they were invisible (three new files `77 passed`, whole suite `549 passed`, no FAILED line); at this tree each one is caught by two named tests - `tests/test_way_record.py::TestTheSeam::test_every_term_arrives_at_the_scorer_under_its_own_name_with_its_own_value` and `tests/test_way_records_fixture.py::TestTheWholePathScores::test_every_row_scores_exactly_what_the_plan_says_it_should` - printing `2 failed, 96 passed` each time"
  - "THE END-TO-END CHECK THIS TASK EXISTS FOR, now against an ORACLE FINAL SCORE PER ROW: `cd services/etl && python -m pytest tests/test_way_records_fixture.py -rs` inside the full run below. 240 raw ways from `tests/fixtures/way_records_fixture.json` -> `normalise.normalise_region` -> `score.score` for every row, each row held to `plan_oracle.plan_score` within 1e-9 and named by way_id on failure (`test_every_row_scores_exactly_what_the_plan_says_it_should`), plus `test_no_row_is_refused_and_every_score_is_in_zero_to_one`, `test_every_zero_class_row_scores_exactly_zero` (exactly 0.0, on all 48), `test_no_scorable_row_scores_zero` (ruling R2's consequence) and `test_every_expected_rank_is_the_rank_the_normaliser_computes` (exact equality against the pairwise oracle, `populationCount * len(RANKED_TERMS)` ranks checked, asserted in the test)"
  - "`cd services/etl && python -m pytest tests -rs` -> `570 passed in 50.99s` at this tree, exit 0, and the `-rs` short summary printed NOTHING: zero skips. 549 of those passed before this round; the 21 new ones are the seam, the oracle score, the reference population, the declined term and the two recordables taken. The same command at the merge-base (9939d39, before this task) printed `472 passed in 80.53s (0:01:20)`. The four files alone: `python -m pytest tests/test_way_record.py tests/test_normalise.py tests/test_way_records_fixture.py -rs` -> `98 passed in 0.41s`"
  - "`bash ops/lib/check-pipe-consumers` -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0"
  - "`bash ops/queue-check` -> `QUEUE OK (158 tasks)`, exit 0"
  - "THE FIXTURE IS DETERMINISTIC AND BOTH ITS EXPECTATIONS ARE COMPUTED BY NOTHING IN `etl/`. `python services/etl/tests/fixtures/generate_way_records.py` at the committed tree -> `ways=240 covering=86 random=154` / `population=192 excluded=48 tied values across ranked terms=387` / `distinct highway classes=14  ways with a byway status=106  ways with points_of_interest=5` / `sinuosity declined=2  oracle scores: min=0.0 max=0.7767038734897669 exactly zero=48`, and the fixture's md5 was `a478511cec3e9493fbc0c18a7ecfa82d` both before and after the run. `naive_rank` counts pairwise and `plan_score` transcribes plan:78-87 by hand; both live in `tests/fixtures/plan_oracle.py`, whose only import line is `from __future__ import annotations`. Copied out of the tree with the generator, `python generate_way_records.py` produced a BYTE-IDENTICAL fixture with no `etl` on sys.path"
  - "SEVENTEEN MUTATIONS AT THIS TREE, each applied ALONE, restored to its pristine md5 (way_record.py 4af3622a29bdf801b214bee0cd229ac5, normalise.py a78838f439db96880d68c08295e76ffe), each caught. NO SURVIVORS. Two are the review's (impervious inverted at the seam, canopy traded with water); six are neighbours nobody showed us at the same seam (speed_fit inverted, canopy overwritten with impervious, water zeroed, a present points_of_interest replaced by 0.5, tunnel_meters forced to 0.0, byway_status dropped); nine are on the new code (the declined filter, the reference estimator, the reference refusals, the declined floor, the declined lookup, the rank inverted, the bool check, the region-whole refusal branch, and one in the GENERATOR that makes canopy equal water). The table with every `FAILED` name is in the Log at 2026-09-18T21:44:17Z. One of them, `_rank_of` no longer checking `declined`, is an ERROR at collection rather than a named FAILED - a KeyError, which is the reason it is a lookup and not a `.get` with a default"
  - "`wc -l` at the final commit: `way_record.py` 255, `normalise.py` 231, `test_way_record.py` 270, `test_normalise.py` 299, `test_way_records_fixture.py` 281, `generate_way_records.py` 289, `plan_oracle.py` 102, `way_records_fixture.json` 256. All under the 300-line cap, unenforced on Python though it is (T-0058) - `generate_way_records.py` measured 329 with the oracle inside it, which is why `plan_oracle.py` is a file of its own. One type per file: `WayRecord` is the only class in `way_record.py`; `normalise.py` and `plan_oracle.py` are functions, as `score.py` is"
  - "NOT IN THIS TASK: the producers themselves (`sinuosity`, `tunnel_meters`, `meters_to_nearest_motorway` are T-0161; `speed_fit` and `furniture` T-0162; `points_of_interest` T-0164), the `scenic_score` 0..10 column, the corpus writer, and any run over a real region - no real raw terms exist on main yet, so the normaliser has never seen one. THE PRODUCT QUESTION THE REVIEW RAISED (percentile rank makes scenic_score region-relative) IS NOT DECIDED HERE: `normalise_region` gains an optional `reference` population so the fix is a data change rather than a rewrite, and the default is today's behaviour. `sinuosity_declined` is an explicit field; T-0146's assembly must set it from `sinuosity.is_closed_way`. `ops/test` and `ops/check-pins` were NOT run: on this box the default swift scratch path does not build inside a worktree. `Tests/Fixtures/scoring/` is in `touches:` and was not touched. No pin added (P-DATA-01 is the plan's). See STILL OPEN"
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
- 2026-09-18T20:22:15Z agent/claude-opus-5: pushed 18c80df and opened PR #93 against main.
  `gh pr view 93` -> `base=main head=task/T-0163 sha=18c80dfc6b9db783f9196b6491d0457bd91ffa88 state=OPEN`
  and `mergeable=MERGEABLE state=BLOCKED files=8 additions=1656` (BLOCKED is checks-pending plus the review
  requirement, not a conflict). `gh pr checks 93`, read ONCE as instructed: `core pending` and
  `pins-source-only pending` in run 35390990872 - so CI is the first place `ops/test` and
  `ops/check-pins` run for this branch, and nobody should read this task as having run them.
  MAIN MOVED WHILE THIS BRANCH WAS OPEN: the branch was cut at 9939d39 and `origin/main` is now 0242421
  (PRs #26 and #33 merged, T-0166 filed). The 8 changed files are this task's 7 plus this queue file; the
  merge is clean. The `472 passed` baseline in the acceptance block is therefore a fact about 9939d39, not
  about today's main - the same trap `ops/lib/check-pipe-consumers` records for its own file count - and
  the number CI prints on the merge ref will be higher than 549 because main has since gained tests of its
  own. Zero skips and the named tests are the parts that do not move.
- 2026-09-18T20:41:32Z **Record corrections from the read-only verification of this build, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. Everything load-bearing reproduced, including a byte-identical regeneration of
  the fixture; these are small.** (a) N3 and an acceptance line say a mutation is caught by "EXACTLY 1 named
  failure in the whole repository"; the quoted procedure runs the three new test files, not the repository.
  It is true by construction - only `tests/test_normalise.py` and `tests/test_way_records_fixture.py` import
  `normalise` - but no whole-suite run backs the words. (b) R1 quotes T-0146's brief as "rank-normalise each";
  that phrase does not occur there - the text is "normalising each within the region" - a paraphrase inherited
  from this task's own Brief. (c) `way_record.py`'s docstring cited score.py:97-99 for `out_of_range`'s reason;
  :97 is blank and the reason is :98-99. Corrected.
- 2026-09-18T21:00:08Z agent/rv1-pr93 (reviewer, not the owner): **REVIEW ROUND 1 - FAIL, one blocking finding.** Reviewed PR #93 at 38fdcc7 from .worktrees/rv1-pr93 (removed at the end); nothing in the task's own worktree was touched, no file in the PR was changed.

  RE-RAN THE ACCEPTANCE BLOCK. `cd services/etl && python -m pytest tests -rs` -> `549 passed in 85.87s (0:01:25)`, exit 0, `-rs` printed nothing (zero skips). The three new files alone -> `77 passed in 0.72s`. `python services/etl/tests/fixtures/generate_way_records.py` -> `ways=240 covering=80 random=160` / `population=189 excluded=51 tied values across ranked terms=369` / `distinct highway classes=14  ways with a byway status=110  ways with points_of_interest=5`, `git status --short` empty afterwards; and the generator run OUTSIDE the tree, with no `etl` on sys.path, produced BYTE-IDENTICAL output (`diff` empty) - the oracle is independent as claimed. `bash ops/lib/check-pipe-consumers` -> `PIPE-CONSUMERS OK ... (57 scanned, 58 tracked, floor 42)` exit 0. `bash ops/queue-check` -> `QUEUE OK (158 tasks)` exit 0. `wc -l` 233/128/212/185/213/251/254, all seven exact. `git ls-files -s` confirms 100644 on both generators. `gh pr checks 93`, read ONCE: `core pass 2m12s`, `pins-source-only pass 1m50s` (run 35392916624). Every expectation in test_normalise.py is a typed-out literal with its arithmetic shown; I re-did three (n=8 mid-group 0.5 with ends 0.0625/0.9375; 0.025/0.975 over 20; 0.125/0.375/0.625/0.875 vs the wrong-population 0.1/0.3/0.5/0.7) and all three are right.

  BLOCKING - B1. `WayRecord.score_kwargs()` is the seam this task exists to build, and the pass-through of three of its four MAPPED terms is unchecked. Mutant, applied alone to the pristine tree: `out["impervious"] = 1.0 - out["impervious"]` inserted after the `out = {...}` comprehension. Three new files -> `77 passed`, no FAILED line; whole suite -> exit 0, 549 dots, no FAILED line. Not equivalent: through `normalise_region` + `score.score` on the committed fixture, 189 of 240 rows change score - way 700000194 (service, impervious=0.990206) 0.377526 -> 0.505732 and way 700000162 (primary_link, impervious=0.012118) 0.659225 -> 0.542091, i.e. plan:87's `0.16*(1-impervious)` inverted and a 99%-car-park road outscoring a 1% one. A second mutant at the same site, `out["canopy"], out["water"] = out["water"], out["canopy"]`, also survives (`77 passed`). This is the defect class way_record.py's own docstring names ("WHY THE INVERSIONS ARE NOT HERE... `impervious` and `furniture`") and that ruling R5 says is "checked end to end instead": the check exists for furniture - my mutant `out["furniture"] = 1.0 - out["furniture"]` is caught by EXACTLY ONE named test, `test_the_busier_roadside_scores_lower`, so R5's claim is true as far as it goes - and not for impervious. Smallest fix, for the owner: assert `score_kwargs()[name] == getattr(record, name)` for every MAPPED_TERM, or a fixture pair alike but for impervious; red against the mutant first.

  MY OTHER FOUR MUTATIONS, each alone, all CAUGHT, and each aimed at what a wrong value does to a driver: the rank inverted (`1.0 - rank`) - 9 named, incl. test_the_ranks_run_the_same_way_as_the_values; `is_zero_class` narrowed to `highway == "motorway"`, putting trunk and the links back in the ranking curve - 8 named; `EXCLUDED_RANK = -1.0`, which slips past the excluded-state equality check into score.py:131 and makes a motorway score None instead of 0.0 - 5 named, incl. test_every_zero_class_row_scores_exactly_zero, which is CLAUDE.md's invariant and is properly guarded; furniture double-inverted - 1 named. Restored after every one (way_record.py md5 2873eb29c2d6a617989fbb962f6f889a, normalise.py md5 ddad9f8665b141c17b319daa6832872e, `git status --short` empty).

  THE RULINGS. I overturn none. R1 is a defensible reading of plan:89 - it is the plan's only normalisation instruction and it is itself a rank, and no fixed divisor maps metres of climb to 0..1 without inventing an invisible ceiling. R2 I re-derived rather than accepted: below >= 0, equal >= 1 gives rank >= 0.5/n > 0, and (below + 0.5*equal) <= n - 0.5 gives rank <= 1 - 0.5/n < 1, so ranking alone cannot zero a scorable way and (rank-1)/(n-1) genuinely would. R3 is load-bearing, proved by my EXCLUDED_RANK mutant. R4 and R6 stand. R5 stands as a ruling; its guard is half-built - B1.

  RECORDABLE, none of it failing this round. (a) PRODUCT, wants a task: percentile rank makes scenic_score region-relative and nothing says so. A region half of which is flat gives every flat way elevation_gain = relief = exactly (0 + 0.5*(n/2))/n = 0.25, and the least-flat road in a table-flat region gets 1 - 0.5/n - the same number a mountain pass gets in its own region. My arithmetic on plan:86-87 for such a road (M = 0.912, E = 0.4618) gives 0.586, clearing plan:117's honest-failure floor of 0.45 and plan:105's `scenic_score >= 4` bucket, so "not much pretty within 25 minutes of this drive" can essentially never fire in a flat region; and plan:91's 0.25*P90 is a P90 of region-relative numbers, which the road trip (plan:128) and Surprise Me's 50 km windows compare across regions. Either an anchor or a written rule, before a corpus exists. (b) Ranking makes the five ranked terms invariant to any strictly monotone producer error - curvature off by x1000, or feet for metres, is bit-identically invisible; STILL OPEN discloses the invariance, so this is a restatement, not a finding. (c) NIT, by reading and not run: removing the `terms_state != RAW` branch from `refusals` would leave both idempotence tests green, because `_require_raw`'s message also carries the way_id and the state - what is lost is the region-whole refusal, not the refusal. (d) NIT: EXCLUDED_RANK could be any value in 0..1 with no test moving (both checks compare against the constant), which I proved equivalent w.r.t. score.py:139; the out-of-range variant is caught. (e) IDEA: making `ranked_order` public because the mid-rank formula hides the within-tie order is the right pattern for T-0164's 50 km windows.

  NOT DONE: `ops/test` and `ops/check-pins` were not run locally, as instructed (swift scratch path); `gh pr checks 93` read once instead and both checks pass. I did not re-run the author's nine mutations. I did not review the Swift side or `Tests/Fixtures/scoring/`, which is declared untouched and is.
- 2026-09-18T21:44:17Z agent/claude-opus-5 (owner, fixing round 1): **B1 REPRODUCED FIRST, THEN KILLED BY
  NAME; the four owner's rulings built; two of the reviewer's recordables taken as one test each.** The
  shipped code was right in every blocking finding, exactly as the reviewer says - what was missing is a
  check that could ever tell. Everything below is tests, fixture rows and one new argument.

  B1 REPRODUCED BEFORE ANYTHING WAS TOUCHED, at 38fdcc7, each mutant applied ALONE and restored (md5 back
  to way_record.py 2873eb29c2d6a617989fbb962f6f889a, normalise.py ddad9f8665b141c17b319daa6832872e,
  `git status --short` empty). Control: three new files `77 passed in 0.35s`. RV-M5
  (`out["impervious"] = 1.0 - out["impervious"]` inserted after the `out = {...}` comprehension): three
  files `77 passed in 0.40s`, whole suite `549 passed in 81.01s (0:01:21)`, no FAILED line. RV-M6
  (`out["canopy"], out["water"] = out["water"], out["canopy"]`): three files `77 passed in 0.35s`, whole
  suite `549 passed in 67.61s (0:01:07)`, no FAILED line. The finding reproduces exactly as written.

  WHAT CHANGED (ruling by ruling).

  (1) AN ORACLE FINAL SCORE PER FIXTURE ROW. `tests/fixtures/plan_oracle.py` is new: `naive_rank` (moved
  from the generator, unchanged) and `plan_score`, a line-by-line transcription of the plan's formula block
  (lines 78-87) over the naive ranks, with the plan line cited beside each term and every constant
  restated - the two byway tiers as literals, exactly as `Tests/Fixtures/scoring/generate.py` does it. It
  imports NOTHING (`grep -nE "^import|^from"` prints one line, `from __future__ import annotations`), and
  the generator loads it by path, the same mechanism `test_way_records_fixture.py` uses to load the
  generator, because `tests/fixtures` is a data directory and not an importable package. It is a file of
  its own because the generator with the oracle inside it measured 329 lines, over the cap. Every way now
  carries `expected_score` alongside `expected_ranks`, and the end-to-end test asserts, per row and naming
  the way_id and the fixture id on failure, `abs(score.score(**record.score_kwargs()) - expected) < 1e-9`
  after `normalise_region`.

  THE ROWS THAT DISCRIMINATE THE MAPPED TERMS, all measured on the committed fixture. Two new hand-written
  pairs: way-0037/700000037 (impervious 0.02) oracle 0.5234671724461094 against way-0038/700000038
  (impervious 0.98) 0.4072497947012822 - the field outscores the car park, which is plan:87's
  `0.16*(1-impervious)`; and way-0039/700000039 (canopy 0.8, water 0.1) 0.5528851807010526 against
  way-0040/700000040 (canopy 0.1, water 0.8) 0.4926907406000868 - E weights canopy 0.24 and water 0.12, so
  a swap reverses them. The eight rows way-0058..way-0065 (700000058-700000065) hold each mapped term at
  0.0 and at 1.0. Across the whole fixture: canopy != water in 240 of 240 rows, 27 rows have impervious
  further than 0.4 from 0.5, and there are 157 distinct speed_fit values and 159 distinct canopy values -
  asserted, not assumed, by `test_the_fixture_can_tell_every_mapped_term_apart`.

  (2) A DIRECT UNIT TEST OF THE SEAM.
  `tests/test_way_record.py::TestTheSeam::test_every_term_arrives_at_the_scorer_under_its_own_name_with_its_own_value`
  builds one record with a different number in every field (ranks 0.11/0.22/0.33/0.44/0.55, mapped
  0.61/0.72/0.83/0.94, poi 0.37, tunnel 301.5, motorway 149.5, surface gravel, byway OD - none of them 0.5,
  no two alike, so neither an inversion nor a swap can hide), takes the NAMES from
  `inspect.signature(score.score)` and asserts the whole dict against LITERALS.
  `test_what_a_record_does_not_carry_arrives_as_the_absence_it_is` does the same for the other branch:
  poi 0.0 with the flag, surface None, byway None, tunnel 0.0, distance inf.

  (3) `normalise_region(records, reference=None)`. The estimator does not change; the POPULATION it counts
  against does. `reference` is `{term: [values...]}`; a term in the mapping is ranked against that
  distribution by `ranks_against`, a term left out keeps the region's own population, and the default is
  today's behaviour bit for bit. The way's own value is counted INTO the reference (`equal + 1`, divisor
  `len(reference) + 1`) - without that a way above every reference value would take exactly 1.0 and one
  below every value exactly 0.0, and a scorable way on 0.0 is what ruling R2 and CLAUDE.md's motorway
  invariant exist to prevent. `reference_refusals` refuses an unranked term, an empty distribution and a
  non-finite value, each by name. The semantics are documented in `normalise.py`'s docstring, which also
  says the product decision is NOT taken here.

  (4) `WayRecord.sinuosity_declined: bool = False`, and the rank population excludes the ways that
  declined. `DECLINED_RANK` and `SINUOSITY_DECLINED_FLAG` are new named constants; `flags()` reports the
  flag beside `points_of_interest_absent`; `normalise.DECLINED_FIELD` maps the term to the field, so a
  second declinable term is a row and not a branch. T-0161 is NOT imported and not depended on. The
  fixture carries two declined rows, way-0041/700000041 and way-0042/700000042, with raw sinuosity 2.55 and
  2.58 near the top of the range: left in the population they would rank above 0.98, and both come out at
  the floor 0.0 and score 0.3831722734902434 apiece - the same number, which is the property.

  (5) TWO RECORDABLES TAKEN, one test each. R-3: `test_an_already_normalised_region_names_every_offender_and_not_just_the_first`
  (`_require_raw` raises on the first record, so what `refusals` adds is the LIST). R-4:
  `test_the_excluded_rank_is_a_value_the_scorer_cannot_refuse` (the VALUE of `EXCLUDED_RANK` is equivalent
  w.r.t. the score, as the reviewer proved; that it is INSIDE 0..1 is not, because score.py:131 runs before
  :139). R-2 is a disclosed gap and a restatement - nothing to take. R-5 is an idea for T-0164.

  SEVENTEEN MUTATIONS AT THIS TREE, each applied ALONE, run against the three test files, restored, md5
  verified (way_record.py 4af3622a29bdf801b214bee0cd229ac5, normalise.py a78838f439db96880d68c08295e76ffe).
  NO SURVIVORS. The review's two:
  * RV-M5 `out["impervious"] = 1.0 - out["impervious"]` -> `2 failed, 96 passed`: FAILED
    test_way_record.py::TestTheSeam::test_every_term_arrives_at_the_scorer_under_its_own_name_with_its_own_value,
    FAILED test_way_records_fixture.py::TestTheWholePathScores::test_every_row_scores_exactly_what_the_plan_says_it_should.
  * RV-M6 `out["canopy"], out["water"] = out["water"], out["canopy"]` -> the same two, `2 failed, 96 passed`.
  Six NEIGHBOURS at the same seam, none of them shown to me: FX-M1 `speed_fit` inverted, FX-M2 canopy
  overwritten with impervious, FX-M3 water zeroed, FX-M5 `tunnel_meters` forced to 0.0, FX-M6
  `byway_status` dropped - each `2 failed, 96 passed`, the same two names; FX-M4 (a present
  `points_of_interest` replaced by 0.5) `3 failed`, adding test_a_value_that_is_there_is_passed_through_and_not_flagged;
  FX-M7 (`POI_ABSENT = 0.5`) `4 failed`, including test_what_a_record_does_not_carry_arrives_as_the_absence_it_is.
  Nine more on the new code: FX-M8 (the `sinuosity_declined` bool check removed) 1 named;
  FX-M9 (`answering` stops filtering) 4 named, incl. test_declining_a_sinuosity_does_not_move_the_other_ways_ranks;
  FX-M10 (`equal + 1` dropped in `ranks_against`) 4 named, the whole reference class;
  FX-M11 (`reference_refusals` returns nothing) 3 named; FX-M12 (`_rank_of` stops checking `declined`) is a
  KeyError at collection, `1 error`, reported as ERROR tests/test_way_records_fixture.py rather than a named
  FAILED - which is the point of the KeyError over a `.get` default; FX-M13 (the rank inverted) 15 named;
  FX-M14 (`DECLINED_RANK = 0.5`) 7 named, incl. test_a_way_that_declined_its_sinuosity_is_off_that_curve_and_on_the_others;
  FX-M15, in the GENERATOR (`mapped["water"] = mapped["canopy"]`, fixture regenerated) 1 named,
  test_the_fixture_can_tell_every_mapped_term_apart, and regenerating after the restore gave back the
  committed bytes; FX-M16 (the `terms_state != RAW` branch removed from `refusals`) 1 named, R-3's test;
  FX-M17 (`EXCLUDED_RANK = -1.0`) 7 named, incl. R-4's test and test_every_zero_class_row_scores_exactly_zero.

  STILL OPEN.
  * R-1, THE PRODUCT QUESTION, NOT DECIDED HERE. The reviewer's arithmetic: in a region where half the ways
    are dead flat every one of them gets elevation_gain = relief = (0 + 0.5*(n/2))/n = exactly 0.25 and the
    least-flat road gets 1 - 0.5/n, the same number a Sierra pass gets in its own region, so such a road
    scores M = 0.45*0.99 + 0.20*0.99 + 0.20*0.6 + 0.15*0.99 = 0.912, E = 0.24*0.1 + 0.22*0.99 + 0.16*0.7 +
    0.12*0.9 = 0.4618 and 0.912^0.35 * 0.4618^0.65 = 0.586. That clears plan:117's honest-failure floor
    (RouteScore < 0.45) and plan:105's scenic_score >= 4 bucket, so "not much pretty within 25 minutes of
    this drive" can essentially never fire in a flat region, and plan:91's 0.25*P90 is a P90 of
    region-relative numbers that the road trip (plan:128) and Surprise Me's 50 km windows compare across
    regions. The normaliser's semantics are UNCHANGED in this PR; what is new is that fixing it is a data
    change - pass `reference` - and not a rewrite. The decision belongs to the queue task the orchestrator
    is filing, and until it lands nothing in the tree says scenic_score is region-relative except
    `normalise.py`'s docstring.
  * T-0146's ASSEMBLY MUST SET `sinuosity_declined` FROM `sinuosity.is_closed_way`. Nothing does it yet:
    T-0161 is not on main, this record cannot import it, and the field defaults to False - so a corpus
    built before that wiring lands would rank closed ways at their floor value inside the population, which
    is the defect this field exists to prevent. Whoever assembles records from the producers owns it.
  * The 1e-9 tolerance and `expected_score` are floating-point values written by this box's libm. The
    scorer contract fixture beside it (`Tests/Fixtures/scoring/segment_terms.json`) already commits `**`
    results the same way, so the precedent and the risk are the repository's existing ones, not new here.
  * `ops/test` and `ops/check-pins` were NOT run in this round either, for the same reason as the first:
    on this box the default swift scratch path does not build inside a worktree. `gh pr checks 93` read
    ONCE after the push, quoted below.
  * Unchanged from round 1 and still true: no producer on main emits these raw terms, so the fixture is
    synthetic and the end-to-end check proves the arithmetic and the seam, not that any road scores what it
    should; no pin added (P-DATA-01 is the plan's); `Tests/Fixtures/scoring/` is in `touches:` and was not
    touched.
- 2026-09-18T21:44:17Z agent/claude-opus-5: pushed e62ee43 to task/T-0163, the fix for review round 1.
  `gh pr view 93` -> `main task/T-0163 OPEN MERGEABLE 9 2318 2` (base, head, state, mergeable, 9 changed
  files, 2318 additions, 2 deletions); the ninth file is the new `tests/fixtures/plan_oracle.py`, committed
  100644 like the generator beside it (`git ls-files -s` prints `100644 ... plan_oracle.py`).
  `gh pr checks 93`, read ONCE and NOT polled, immediately after the push: `core pending` and
  `pins-source-only pending` in run 35399380722, exit 8. CI is still the only place `ops/test` and
  `ops/check-pins` run for this branch, and nobody should read this task as having run them locally; the
  previous head 38fdcc7 had both green (run 35392916624). This entry adds no number to the acceptance
  block: it changes the queue file only, and every count, `wc -l` and suite line quoted there was measured
  at e62ee43's tree, which this commit does not touch.
