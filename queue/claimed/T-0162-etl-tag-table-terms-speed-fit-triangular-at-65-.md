---
id: T-0162
title: ETL tag-table terms - speed_fit (triangular at 65 km/h) and furniture, from OSM tags alone
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T19:52:35Z
lease_expires_at: 2026-09-19T03:52:35Z
worktree: .worktrees/T-0162
branch: task/T-0162
exclusive: []
touches: [services/etl/etl/speedfit.py, services/etl/etl/furniture.py, services/etl/etl/tagfilter.py, services/etl/tests/test_speedfit.py, services/etl/tests/test_furniture.py, services/etl/tests/test_tagfilter.py]
pins_affected: []
reviewer: null
depends_on: [T-0154]
verify: [ops/test, ops/check-pins]
acceptance:
  - "THE WHOLE ETL SUITE, run bare at the final commit: `cd services/etl && python -m pytest tests -rs` -> `589 passed in 66.99s (0:01:06)` re-run at it, `589 passed in 64.67s (0:01:04)` on the run before the acceptance block was written - the wall clock moves on a shared box, the 589 and the zero skips do not. Exit 0, and NO `short test summary info` section at all - zero skips, zero xfails (`-rs` prints a skip section when there is one). The same command on this worktree before any file was added printed `472 passed in 74.56s (0:01:14)`, so this task adds 589 - 472 = 117 tests, which is what `python -m pytest tests/test_speedfit.py tests/test_furniture.py -rs` printed on its own: `117 passed in 0.37s`"
  - "`bash ops/lib/check-pipe-consumers`, run bare -> `PIPE-CONSUMERS OK: no gate decides with 'producer | grep -q' (57 scanned, 58 tracked, floor 42)`, exit 0"
  - "`bash ops/queue-check`, run bare -> `QUEUE OK (158 tasks)`, exit 0"
  - "`speed_fit` IS THE PLAN'S TRIANGLE AND ITS FEET ARE A RECORDED RULING, not a computed one. `services/etl/etl/speedfit.py` carries `APEX_KMH = 65.0` (plan:89), `LOWER_FOOT_KMH = 25.0` and `UPPER_FOOT_KMH = 105.0` (R1), and every expected value in `tests/test_speedfit.py` is typed out with its division shown in the comment above it - 1.0 at the apex, 0.0 at both feet, 0.5 at BOTH 45 and 85 ((45-25)/40 and (105-85)/40), 0.875 at 60 and at 70, 0.25 at 35 and at 95. Three tests are properties rather than values and say so in the file's docstring (symmetry compares speed_fit(65-d) with speed_fit(65+d); `walk` is pinned to WALK_PACE_KMH; the unknown-class fallback is pinned to DEFAULT_SPEED_KMH['road'] as well as to the literal 50.0); no other expectation is obtained by calling the function under test or by re-deriving it from the module's constants"
  - "THE SPEED IS READ FROM TAGS, WITH EVERY NON-NUMERIC RULED BY NAME: a bare number is km/h, `NN mph` converts by the exact international mile `MPH_TO_KMH = 1.609344` - the tests pin `45 mph` at 72.42048 km/h, `25 mph` at 40.2336 km/h, and the term for a primary posted `55 mph` at 0.412152, which is (105 - 88.51392)/40 written out - `NN km/h` parses redundantly, and `signals` / `none` (`NO_NUMBER_VALUES`) fall to the class default while `walk` parses to `WALK_PACE_KMH = 5.0` and therefore to 0.0 (R3, R4, R5). `CA:urban`, `50 @ (22:00-06:00)`, `30;50`, `60 knots`, `''`, `0`, `-20` are all None (R2, R6)"
  - "THE DEFAULT TABLE IS LOCAL AND PINNED AGAINST LITERALS. `DEFAULT_SPEED_KMH` is compared entry by entry to a literal dict in `TestTheDefaultTable.EXPECTED`, and two tests hold it to exactly the `highway` values the extract keeps: `test_every_highway_value_the_extract_keeps_has_a_default` and `test_the_table_has_no_entry_the_extract_does_not_keep`, both iterating `tagfilter.WAY_CLASSES` (R8). `UNKNOWN_CLASS_SPEED_KMH == 50.0 == DEFAULT_SPEED_KMH['road']` is pinned as an equality so the two cannot drift (R7). `services/routing/profiles/` is neither read nor written and `speedfit.py` imports only `math` and `re`"
  - "`furniture` IS RAW, AND A TEST GOES RED IF SOMEBODY NORMALISES IT HERE. `test_the_rate_is_unbounded_and_is_not_normalised_here` pins 30 pieces on 200 m at 150.0 per km, and `test_the_rate_is_not_inverted_here` pins 3.0 against 0.0 on 1000 m so the sign cannot be flipped into score.py's `1 - furniture` twice. `furniture_per_km` is 2.0 for 3 pieces on 1500 m and 4.0 for 1 piece on 250 m, both typed out from the division"
  - "THE ACCEPTED SET IS ENUMERATED AND COMPARED TO A LITERAL: `FURNITURE_VALUES == {'highway': frozenset({'crossing','stop','street_lamp','traffic_signals'}), 'barrier': frozenset({'bollard'})}`, `FURNITURE_KEYS_ANY_VALUE == frozenset({'traffic_calming'})`, `ANY_VALUE_EXCEPTIONS == frozenset({'no'})` (R11). Thirteen tags are pinned as NOT counted; the module docstring gives the reason for ten of them, and `highway=residential`, `tourism=viewpoint` and `name=*` are pinned without a stated reason - `barrier=gate`/`lift_gate`/`cycle_barrier`, `highway=turning_circle`/`passing_place`/`mini_roundabout`/`bus_stop`, `amenity=*`, `shop=*`, `railway=level_crossing` (R12). One node with `highway=crossing` AND `traffic_calming=table` counts ONCE (R10), and a length that cannot carry a rate returns None rather than 0.0 (R13)"
  - "SIX MUTATIONS, three per new module, each applied alone and restored, none survived - the table with the verbatim FAILED lines is in the Log. Because both modules are new files, `git checkout --` cannot restore them: each was restored by copying back from a pristine copy in the gitignored `services/etl/work/T-0162-pristine/` and `diff` printed `RESTORED identical` every time. The mutation worth naming: `furniture_count` summing matched KEYS instead of nodes is caught by exactly one test, `test_one_node_carrying_two_accepted_tags_counts_once`"
  - "UNDER THE 300-LINE CAP, measured by `wc -l` at the final commit: `services/etl/etl/speedfit.py` 150, `services/etl/etl/furniture.py` 96, `services/etl/tests/test_speedfit.py` 239, `services/etl/tests/test_furniture.py` 152"
  - "NOT IN THIS TASK. `tagfilter.py` and `test_tagfilter.py` are unchanged (R14): the furniture tags arrive as the referenced nodes of kept ways, and the one genuine gap - `highway=street_lamp` mapped off the carriageway - would need a third dict in the filter and a NEW `street_lamp` key in `services/etl/regions/*/region.json`'s recorded counts, moving no existing per-class count; re-recording needs the container (T-0024's gate). No normaliser, no way record, no corpus column, no geometry and no sibling module is imported - T-0161 and T-0163 own those. `ops/test` and `ops/check-pins` were NOT run: on this box the default swift scratch path does not build inside a worktree. `gh pr checks` on the PR is the only run of them, read once after pushing"
---
## Brief

One of three disjoint pieces T-0146 was split into by the 2026-09-18 13:13 panel (CODE lens, grounded).
`services/etl/etl/score.py` takes keyword-only `speed_fit` and `furniture` in 0..1 (UNIT_TERMS, score.py:72-73)
and nothing produces either. Both come from tags alone - no geometry library, no raster, no container.

**Build:**
1. `speedfit.py` - the plan's `speed_fit`: "triangular at 65 km/h" (plan:89). 1.0 at 65 km/h, falling linearly
   to 0.0 at the two feet. The plan gives the apex and not the feet: RULE the feet in your Log before code
   (owner's starting ruling: 0 at 25 km/h and at 105 km/h - symmetric, so a 45 and an 85 km/h road score the
   same 0.5; argue against it in the Log if the plan's intent reads otherwise). The speed comes from `maxspeed`
   when it parses (km/h bare number, `NN mph`, the common `signals`/`none`/`walk` non-numerics each ruled by
   name) and otherwise from a per-`highway`-class default table LOCAL TO THIS MODULE, typed out and pinned by
   a test against literals. NEVER read or write `services/routing/profiles/` - serial-only files another task
   owns. Output is already 0..1: it is mapped, never region-ranked.
2. `furniture.py` - RAW street-furniture count per kilometre for a way: nodes on or tagged along it that make
   a road feel urban (`highway=street_lamp`, `highway=traffic_signals`, `highway=stop`, `highway=crossing`,
   `traffic_calming=*`, `barrier=bollard` - enumerate the accepted set as a named constant pinned against
   literals; say in the docstring what is deliberately NOT counted and why). Unbounded raw value; the region
   normaliser (T-0163) maps it to 0..1 and score.py inverts it (`1 - furniture`). Do not normalise here.
3. If - and only if - the extract's tag filter drops a tag either module needs, this task is the SOLE owner of
   `tagfilter.py` for the duration: add the tag, extend `test_tagfilter.py`'s literal expectations, and say in
   the Log which per-class count in `regions/*/region.json` that would move (do NOT re-record counts - that
   needs the container and is T-0024's gate; state it as STILL OPEN).

**The author rule (it took PR #89 through review in one round):** rule every place the plan, score.py and the
OSM wiki's tag semantics disagree in your Log BEFORE writing code; re-run and quote the whole acceptance
block at your FINAL commit; close your own verifier's findings before the review is bought. Expected values
typed out from arithmetic shown in a comment, never computed by the function under test. Every new test
demonstrated RED by name (three mutations per module), then green. Whole ETL suite green with zero skips.

## Log
- 2026-09-18T20:20:00Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
- 2026-09-18T19:52:36Z claimed by agent/claude-opus-5; lease until 2026-09-19T03:52:35Z
- 2026-09-18T19:56:50Z READ, before any code: CLAUDE.md; the plan's "Score per way" block
  (`~/.claude/plans/i-want-to-make-synthetic-twilight.md:75-93`, the only two lines about either term are
  plan:78-87 for the weights and plan:89 "`speed_fit` triangular at 65 km/h"); `services/etl/etl/score.py`
  end to end (the consumer: `UNIT_TERMS` at score.py:72-73, `drive_mean` keyword `speed_fit` at score.py:76,
  `scenery_mean` keyword `furniture` entering as `1.0 - furniture` at score.py:92, and the float-typed
  signature of `score` at score.py:119-122); `services/etl/etl/tagfilter.py` and
  `services/etl/tests/test_tagfilter.py` in full; `services/etl/etl/curvature.py` and
  `services/etl/tests/test_curvature.py` for the house style of a literal table pinned by test;
  `services/etl/regions/sfbay/region.json` for the shape of the recorded per-class counts.
  Baseline before any edit, on this worktree at 9939d39: `cd services/etl && python -m pytest tests -rs` ->
  `472 passed in 74.56s (0:01:14)`, zero skips.

- 2026-09-18T19:56:50Z RULINGS. Where the plan, score.py, the existing modules and OSM's tag semantics
  disagree or are silent, decided here BEFORE code. Every ruling below is implemented as written.

  R1 - THE TWO FEET OF THE TRIANGLE. plan:89 gives the apex ("triangular at 65 km/h") and neither foot;
  score.py:72-73 requires a value in 0..1. RULED: the owner's starting ruling stands - 0.0 at 25 km/h and
  0.0 at 105 km/h, symmetric, so a 45 km/h and an 85 km/h road both score 0.5. Argued for: with no further
  qualification "triangular at 65" reads as "how far from 65 km/h", and a symmetric triangle is the only
  shape that says exactly that and nothing more. Considered and REJECTED: a foot at 0 km/h (asymmetric,
  rising over the whole slow range) would give a 25 km/h residential street 0.385 and would make speed_fit a
  partial duplicate of road-class information the formula already carries twice - the zero classes
  (score.py:139) and the plan's anti-rat-run residential rule (plan:108). The apex value, both feet and the
  0.5 pair are typed out in `tests/test_speedfit.py` from arithmetic shown in the comment above each.

  R2 - WHICH `maxspeed` STRINGS PARSE. The plan says nothing about maxspeed; OSM's semantics are: a bare
  number is km/h, a unit-suffixed value is `NN mph` (`NN km/h` also occurs, redundantly). RULED: those three
  shapes parse, case-insensitively and with the space optional; every other string returns None and the way
  falls to the per-class default table. That deliberately includes country-implicit values (`CA:urban`),
  conditional values (`50 @ (22:00-06:00)`) and multi-valued strings (`30;50`): each of them needs a
  resolver this task does not have, and a wrong number read confidently is worse than the class default.

  R3 - `maxspeed=signals`. RULED: None -> class default. A variable-limit sign states that the posted number
  changes; there is no number in the tag to read, so there is nothing to be confident about.

  R4 - `maxspeed=none`. RULED: None -> class default, NOT the upper foot. `none` is a German-network value;
  on a California way it is a mis-tag, and converting it into speed_fit 0.0 would fabricate positive
  evidence about a road from a tag that carries none - the same discipline CLAUDE.md's "Product invariants"
  imposes on the unpaved gate. Where `none` is genuinely right the way is a motorway, whose class default is
  already at the upper foot and which score.py:139 zeroes regardless of any term.

  R5 - `maxspeed=walk`. RULED: unlike R3 and R4 this one IS a speed statement - walking pace - and it is
  positive evidence of a shared-space street, so it parses, to a named `WALK_PACE_KMH = 5.0`. The constant's
  exact value is not load-bearing: every plausible walking pace is below the lower foot and yields 0.0, and
  the test pins the 0.0 rather than the 5.

  R6 - NO ABSURDITY CEILING on a parsed number. A typo'd `maxspeed=400` scores 0.0 rather than the 0.375 a
  40 would have scored. RULED: accepted. The error direction of an out-of-range number is always "less
  scenic", never more, and a ceiling would need a threshold the plan does not give. Zero and negative
  numbers are not speeds and return None.

  R7 - THE DEFAULT TABLE. Local to `speedfit.py` per the Brief; `services/routing/profiles/` is a
  serial-only file another task owns and is neither read nor written. Values are California posted limits
  converted from mph and rounded to 5 km/h, typed out, pinned against literals by test. An unrecognised
  `highway` value RULED to `UNKNOWN_CLASS_SPEED_KMH = 50.0`, the same number as `highway=road`, because "a
  highway value we do not recognise" and OSM's `highway=road` ("classification unknown") are the same
  epistemic state; a test pins that equality so the two cannot drift apart. `default_speed_kmh` returns None
  for an unknown class so the absence stays visible to a caller that wants it, while `speed_fit_for_tags`
  always returns a float, because score.py:119-122 takes floats and `out_of_range` (score.py:95) turns a
  None into a whole-row failure.

  R8 - TABLE COVERAGE IS A TEST, NOT A COMMENT. `tests/test_speedfit.py` iterates
  `tagfilter.WAY_CLASSES`'s values and requires a default entry for every `highway` value the extract keeps,
  so a class added to the filter cannot silently arrive at the fallback. The module itself does not import
  tagfilter - the Brief requires the table to be local.

  R9 - `furniture` IS RAW HERE. The Brief and score.py disagree in appearance only: score.py:92 consumes a
  0..1 term, this module emits an unbounded count per kilometre, and T-0163's region normaliser is the step
  between. RULED: no normalisation, no clamping and no inversion in this module; `furniture_per_km` is the
  raw rate and its docstring names its consumer.

  R10 - ONE NODE COUNTS ONCE. A raised crossing carries `highway=crossing` AND `traffic_calming=table` on
  the same node. RULED: the unit counted is the NODE, not the matching tag - an implementation that adds up
  per-key matches would double-count precisely the most urban nodes, and the resulting rate would be a
  number with no unit. Pinned by name in `tests/test_furniture.py`.

  R11 - `traffic_calming=no`. OSM uses `=no` on this key to state that a junction explicitly has no calming.
  RULED: it does not count, and every other value of the key does. The key is accepted by key rather than by
  an enumerated value list (the Brief's `traffic_calming=*`) because the wiki's value list grows and an
  enumeration here would silently drop new calming types into "not urban"; `no` is the one value that means
  the opposite of the key.

  R12 - WHAT IS DELIBERATELY NOT COUNTED (stated in the module docstring, with these reasons):
  `barrier=gate`/`lift_gate`/`cycle_barrier` - access furniture, and plan:81 already makes a locked gate a
  safety gate, so counting it here would penalise one rural tag twice in two different terms;
  `highway=turning_circle`/`passing_place`/`mini_roundabout` - the geometry of narrow and rural roads, and a
  passing place is evidence of the opposite of urban; `highway=bus_stop`, `amenity=*`, `shop=*` - roadside
  land use, which is what score.py's `impervious` (score.py:89) and `points_of_interest` (score.py:91) terms
  are for, and the same evidence must not enter E twice with two different signs;
  `railway=level_crossing` - rural rail crossings are common and carry no urbanness.

  R13 - A WAY WITH NO LENGTH HAS NO RATE. RULED: `furniture_per_km` returns None for a length that is zero,
  negative or not finite, never 0.0. Returning 0.0 would state "this way is rural", which is a claim about a
  way that does not exist; None is "no opinion" and T-0163's rank normaliser decides what to do with a
  missing raw value.

  R14 - `tagfilter.py` IS NOT CHANGED, and the per-class count that a change would move is named. The
  furniture keys are not in the filter's keep set, but they do not need to be: `osmium tags-filter` keeps the
  nodes a kept way refers to, as whole objects with their tags - this repository's own statement of that is
  `tagfilter.py`'s `typed_expression` docstring, which is why an `nw/` filter's node tally is "tagged nodes
  PLUS way geometry". `highway=traffic_signals`/`stop`/`crossing`, `traffic_calming=*` and `barrier=bollard`
  are way-member nodes by construction - each has meaning only at a point ON the carriageway - so they
  arrive with the ways. `highway=street_lamp` is the exception: a lamp mapped beside the carriageway is not a
  way node, so it is outside the extract, and R15 records what that costs. RULED: no filter change, because
  neither of the filter's two dicts is the right home for a third kind of thing - `WAY_CLASSES` is a
  `w/highway=` grouping for road classes, and `POI_CLASSES` is the deliberately narrow Surprise Me
  allowlist, so putting street lamps there would inject them into the `points_of_interest` term (score.py:91)
  as candidate destinations. WHICH RECORDED PER-CLASS COUNT IT WOULD MOVE: none of the existing ones. The
  recorded counts in `services/etl/regions/*/region.json` are keyed one per class in
  `WAY_CLASSES | POI_CLASSES` and each is measured by its own single-type filter (`typed_expression`), so a
  new furniture class would ADD a `street_lamp` key and leave every current key's number unchanged - the
  furniture keys share no `highway` value with `WAY_CLASSES` and no key/value pair with `POI_CLASSES`.
  Recording that new key needs the container and is T-0024's gate; under STILL OPEN, not done here.

  R15 - THE STREET-LAMP UNDERCOUNT IS DOCUMENTED, NOT HIDDEN. `highway=street_lamp` stays in the accepted
  set (the Brief enumerates it, and lit streets are the strongest single "feels urban" signal available from
  tags), and the module docstring states that lamps mapped off the carriageway are not way nodes and are
  therefore missing. Considered and REJECTED: dropping `street_lamp` from the set, which trades an undercount
  whose direction is uniform - and which a rank normaliser can still order rows with - for losing the signal
  outright.

  R16 - A NON-FINITE SPEED, ruled while writing `speed_fit` and recorded here rather than left implicit.
  RULED: 0.0. Infinity is genuinely above the upper foot; NaN cannot be placed on the triangle at all, and
  0.0 is the answer whose error direction is "less scenic", which is the direction R4 and R6 already fail
  in. Pinned by `test_a_non_finite_speed_is_zero`.

- 2026-09-18T20:09:43Z BUILT. New files, no existing file changed: `services/etl/etl/speedfit.py`,
  `services/etl/etl/furniture.py`, `services/etl/tests/test_speedfit.py`,
  `services/etl/tests/test_furniture.py`. `tagfilter.py` and `test_tagfilter.py` were read in full and NOT
  changed (R14); they stay in `touches:` because the Brief gave this task their ownership for the duration.
  No sibling task's module is imported: the code is written against score.py's keyword names
  (`speed_fit`, `furniture`), which is the seam.

- 2026-09-18T20:09:43Z MUTATION TABLE. Six mutations, three per new module, each applied ALONE and then
  restored (both new modules are untracked, so restoring is a copy back from a pristine copy kept in the
  gitignored `services/etl/work/T-0162-pristine/`, not `git checkout --`; `diff` against the pristine copy
  printed `RESTORED identical` after each, and `git status --short` showed only the four intended untracked
  files plus this task file). Red runs were
  `cd services/etl && python -m pytest tests/test_<module>.py --tb=no -q -rf`; the FAILED lines below are
  copied from those runs. This pytest prints the `short test summary info` FAILED list and no trailing count
  line under `-q -rf --tb=no`, so the NAMES are the record.

  | # | module | mutation | a NAMED test that went red |
  |---|--------|----------|----------------------------|
  | M1 | speedfit.py | `APEX_KMH = 65.0` -> `60.0` (a plausible "round it off" retune) | `tests/test_speedfit.py::TestTheTriangle::test_the_apex_is_one_at_sixty_five` |
  | M2 | speedfit.py | `MPH_TO_KMH = 1.609344` -> `1.6` (a plausible simplification) | `tests/test_speedfit.py::TestMaxspeedParsing::test_mph_is_converted_with_the_exact_international_mile` |
  | M3 | speedfit.py | `speed_kmh_for_tags` precedence swapped: class default first, parsed `maxspeed` only as the fallback | `tests/test_speedfit.py::TestFromTagsToTheTerm::test_a_parsed_maxspeed_beats_the_class_default` |
  | M4 | furniture.py | `ANY_VALUE_EXCEPTIONS = frozenset({"no"})` -> `frozenset()` | `tests/test_furniture.py::TestWhatCounts::test_traffic_calming_no_does_not_count` |
  | M5 | furniture.py | `furniture_count` sums MATCHED KEYS per node instead of counting nodes | `tests/test_furniture.py::TestCounting::test_one_node_carrying_two_accepted_tags_counts_once` |
  | M6 | furniture.py | `furniture_per_km` returns `0.0` instead of `None` for a length that cannot carry a rate | `tests/test_furniture.py::TestTheRawRate::test_a_zero_length_way_has_no_rate` |

  Verbatim FAILED lines, in the order the runs printed them:

  M1: `FAILED tests/test_speedfit.py::TestTheTriangle::test_the_apex_is_one_at_sixty_five`,
  `...::TestTheTriangle::test_forty_five_and_eighty_five_are_both_a_half`,
  `...::TestTheTriangle::test_the_rising_limb_at_thirty_five`,
  `...::TestTheTriangle::test_the_falling_limb_at_seventy`,
  `...::TestTheTriangle::test_the_triangle_is_symmetric_about_the_apex[1.0]` (and [5.0], [10.0], [20.0],
  [39.0]), `...::TestMaxspeedParsing::test_signals_falls_to_the_class_default`,
  `...::TestMaxspeedParsing::test_none_falls_to_the_class_default_rather_than_to_zero`,
  `...::TestFromTagsToTheTerm::test_a_parsed_maxspeed_beats_the_class_default`,
  `...::TestFromTagsToTheTerm::test_an_unreadable_maxspeed_falls_back_to_the_class`,
  `...::TestFromTagsToTheTerm::test_the_class_defaults_score_what_the_arithmetic_says[residential-0.375]`
  (and [tertiary-0.875], [unclassified-0.75], [secondary-0.875], [primary-0.375], [trunk-0.125]),
  `...::TestFromTagsToTheTerm::test_a_road_posted_in_mph`,
  `...::TestFromTagsToTheTerm::test_an_unrecognised_class_with_no_tag_uses_the_fallback`.

  M2: `FAILED tests/test_speedfit.py::TestMaxspeedParsing::test_mph_is_converted_with_the_exact_international_mile`,
  `...::TestMaxspeedParsing::test_the_suffix_is_case_insensitive_and_the_space_optional[45mph]` (and
  `[45 MPH]`, `[45Mph]`, `[  45 mph  ]`), `...::TestFromTagsToTheTerm::test_a_road_posted_in_mph`.

  M3: `FAILED tests/test_speedfit.py::TestMaxspeedParsing::test_walk_parses_and_lands_below_the_lower_foot`,
  `...::TestMaxspeedParsing::test_an_absurd_number_is_accepted_and_scores_zero`,
  `...::TestFromTagsToTheTerm::test_a_parsed_maxspeed_beats_the_class_default`,
  `...::TestFromTagsToTheTerm::test_a_road_posted_in_mph`.

  M4: `FAILED tests/test_furniture.py::TestWhatCounts::test_the_any_value_keys_are_the_ones_that_were_argued`,
  `...::TestWhatCounts::test_traffic_calming_no_does_not_count`.

  M5: `FAILED tests/test_furniture.py::TestCounting::test_one_node_carrying_two_accepted_tags_counts_once`.

  M6: `FAILED tests/test_furniture.py::TestTheRawRate::test_a_zero_length_way_has_no_rate`,
  `...::TestTheRawRate::test_a_length_that_cannot_carry_a_rate_has_no_rate[-1.0]` (and `[-1500.0]`,
  `[nan]`, `[inf]`, `[-inf]`).

  No mutation survived, so no test was added in response to this campaign. M5 is the one worth naming twice:
  it is the defect R10 exists to prevent, and exactly one test - the raised crossing - separates the correct
  implementation from it.

- 2026-09-18T20:09:43Z STILL OPEN, none of it claimed as done here.
  * `ops/test` and `ops/check-pins` were NOT run locally: on this Windows box the default swift scratch path
    does not build inside a worktree, which is what `verify:` asks for. `gh pr checks` on the PR is the
    check that covers them, read once after pushing.
  * The `street_lamp` undercount (R14/R15) is real and unfixed: lamps mapped beside the carriageway are
    outside the extract. Fixing it needs a third dict in `tagfilter.py` and a new `street_lamp` key in the
    recorded per-class counts of `services/etl/regions/*/region.json`; re-recording those counts needs the
    container and is T-0024's gate, so neither is done here. No existing recorded count moves either way.
  * Short-way outliers in the raw rate: a 1 m way with one signal is 1000.0 per km, which is arithmetic
    rather than a defect, but it will distort a naive rank normaliser. Whether to floor the length or to
    aggregate before ranking is T-0163's decision and is deliberately not pre-empted here; the behaviour is
    pinned by `test_a_one_metre_way_still_produces_its_arithmetic_rather_than_a_special_case` so the
    normaliser's author can see it.
  * Nothing wires either term into a way record or the corpus - that is T-0163 and T-0030. The only
    consumer-side check here is `score.out_of_range`, in `TestTheSeamWithScore`.
  * The default speed table is argued from California posted limits, not measured against probe data. It is
    the kind of constant the plan's Bradley-Terry tuning step (plan:93) can revisit; nothing in it is
    claimed to be fitted.
- 2026-09-18T20:41:32Z **Record corrections from the read-only verification of this build, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. The verifier found the code and tests sound and the whole ETL suite green
  (`589 passed`, no skip section) at 3383e34; these are text.** (a) `furniture.py`'s docstring and Log R12 and
  R14 cite `points_of_interest` at score.py:91; that line is `+ WATER_WEIGHT * water`, and the term is at :90.
  The docstring is corrected; the two dated Log lines stay as written and this is their correction. (b) The
  20:09:43Z mutation table calls M1's list "verbatim" and gives 21 names; replaying APEX_KMH 65.0 -> 60.0 gives
  `23 failed, 94 passed`, and the two missing are `TestTheTriangle::test_the_falling_limb_at_ninety_five` and
  `::test_the_rising_limb_at_sixty` (the author's own capture has all 23). (c) The acceptance block and
  `test_speedfit.py`'s docstring said no expectation calls the function under test; three tests are properties
  that do (symmetry, the `walk` pace constant, the unknown-class fallback against the table). Both now say
  so. (d) "Thirteen tags ... with the reason in the module docstring": thirteen are pinned, ten have a reason
  there. Acceptance corrected. (e) "Sixteen rulings BEFORE any code": R16's own text says it was ruled while
  writing `speed_fit`, and rulings, code and tests are one commit, so git shows no order. The entries stay.
