---
id: T-0207
title: residential and service ways reach scenic_score 7 and escape the anti-rat-run clause - rule a class cap (score or profile) with the LA grid window's hillside streets and fire roads as the fixture
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T11:30:53Z
lease_expires_at: 2026-09-19T17:30:53Z
worktree: .worktrees/T-0207
branch: task/T-0207
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0204]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code, with the plan's profile block quoted (road_class == RESIDENTIAL && scenic_score < 7 -> 0.5): T-0204's grid window puts Crescent Drive, Scenario Lane and Oakmont Street (highway=residential) and Sullivan Fire Road / Sullivan Ridge Fire Road (highway=service) at scenic_score 7 (unit 0.7189-0.7228), so the router's rat-run demotion never touches them; rule WHERE the cap lives (score.py class factor, the quantiser, or the routing profile's threshold) and what it is for residential, living_street, service and unclassified"
  - "RED BY NAME first on a fixture of those five real rows (from services/etl/tests/fixtures/grid_top25.json): no residential/living_street/service way quantises to >= 7 (or the profile clause demotes it regardless) - then green; the ops/mutate population for the touched module gains the cap's mutants with the floor raised"
  - "tagwriter writes ONE number twice: scenic_score is quantise() of the UNROUNDED score while scenic_score_unit is the score fixed at four decimals, so 17 of 46,436 real ways (1 grid-a, 14 grid-b, 2 canyon; e.g. way 13332407 ships 5 beside 0.5500) fail the hardened oracle's quantise(unit) == score clause - quantise the SAME rounded value the unit carries, RED BY NAME first on a fixture row at a .x5 fourth-decimal boundary, then green; the three real read-backs re-checked: malformed=0"
  - "cd services/etl && python -m pytest tests -rs -o addopts= count line and zero skips; the canyon window's top ten unchanged (quoted)"
---
## Brief

From T-0204's real run (PR #113): in the Westwood/Brentwood/Bel Air window the top ten holds three residential
hillside streets and two service fire roads at scenic_score 7, one unit-score hair under Topanga's tenth (0.7284).
The plan's anti-rat-run rule only demotes RESIDENTIAL ways scoring BELOW 7, and the owner's bar is zero rat-runs -
one cut-through past a school and the app is deleted. T-0168 recorded the service-way half as STILL OPEN 3. The
four bits do not separate Topanga from a Bel Air cul-de-sac; something class-aware must.

## Log
- 2026-09-19T09:51:35Z filed by agent/claude-fable-5-1 from T-0204's grid-window top ten. Not started. Safety-adjacent: before T-0031's second half routes over LA scores.
- 2026-09-19T11:17:30Z bullet added by agent/claude-fable-5-1 from T-0204's fixer and rv1-pr113 (PR #113, merged): the hardened oracle found malformed=17 on real data, cause read out of tagwriter.tags_for_row. Same module and same re-run as the class cap, so it lands here.
- 2026-09-19T11:17:30Z PROMOTED to ready/ by agent/claude-fable-5-1: #113 (T-0204) merged, its fixture is on main; the 03:13 panel's NEXT START (safety: zero rat-runs).
- 2026-09-19T11:30:53Z claimed by agent/claude-opus-5; lease until 2026-09-19T17:30:53Z
- 2026-09-19T11:38:11Z MEASURED FIRST by agent/claude-opus-5, before any predicate, over the three real
  scored tables in the MAIN checkout (`services/etl/work/la/window-scored.json`,
  `services/etl/work/la-grid/grid-{a,b}-scored.json`; throwaway reader `services/etl/work/measure_T0207.py`,
  gitignored). Populations: canyon 11,740 · grid-a 11,239 · grid-b 23,474 = **46,453 scored rows**. Per class,
  over all three, `n / max unit / ways quantising to >= 7 / ways >= 4`:

      service        24020  0.7227  ge7=109  ge4=2972
      residential     9901  0.7228  ge7=131  ge4=3383
      secondary       3677  0.7367  ge7=42   ge4=664
      primary         2750  0.7722  ge7=11   ge4=235
      tertiary        2371  0.7563  ge7=33   ge4=463
      track           1154  0.0000  ge7=0    ge4=0     (gated: assemble.GATE_TRACK -> GATE_SCORE)
      motorway_link    635  0.0000  ge7=0    ge4=0
      unclassified     570  0.7203  ge7=5    ge4=102
      motorway         501  0.0000  ge7=0    ge4=0
      trunk            474  0.0000  ge7=0    ge4=0
      primary_link     189  0.5649  ge7=0    ge4=51
      secondary_link   132  0.5952  ge7=0    ge4=34
      tertiary_link     42  0.4546  ge7=0    ge4=6
      trunk_link        24  0.0000  ge7=0    ge4=0
      living_street     11  0.5805  ge7=0    ge4=2
      footway            2  0.0000  ge7=0    ge4=0

  So **240 of the 46,453 ways that reach the router's high band are residential or service** (131 + 109), and
  five more are unclassified. Top five of each offending class by unit, by name:

      residential  0.7228 13419334 Crescent Drive · 0.7201 13379402 Scenario Lane · 0.7189 121304178 Oakmont
                   Street · 0.7133 13293766 Beverly Glen Terrace · 0.7121 13419340 Crescent Drive
      service      0.7227 632613339 Sullivan Fire Road · 0.7215 13290126 Sullivan Ridge Fire Road ·
                   0.7118 721642253 (unnamed) · 0.7098 386470272 (unnamed) · 0.7097 822134900 (unnamed)
      unclassified 0.7203 13292286 Franklin Canyon Drive · 0.7141 13437453 Ramera Motorway ·
                   0.6925 13292289 Franklin Canyon Drive · 0.6878 24561984 Lake Drive ·
                   0.6636 435695311 Temescal Canyon Road
      living_street max 0.5805 over 11 ways - NONE reaches 7, and none reaches 6
      track         all 1154 already 0.0 (gated, safety - not this task's business)

  The quantise mismatch (R2) measured on the same three tables with the same reader: canyon 2, grid-a 1,
  grid-b 14 = **17 of 46,453**, every one of them a row whose unrounded score is a hair under a `.x5`
  fourth-decimal boundary that the unit's `%.4f` rounds UP: way 13332407 (Yoakum Drive) 0.5499510668 ->
  `scenic_score=5` beside `scenic_score_unit=0.5500`, way 13377783 0.4499826450 -> 4 beside 0.4500, way
  13359647 0.1499689499 -> 1 beside 0.1500, way 170301018 0.0499647216 -> 0 beside 0.0500.
- 2026-09-19T11:38:11Z RULED by agent/claude-opus-5, before code.

  **R1 WHERE THE CAP LIVES: `assemble.scored_row`, beside the gate - NOT `score.py`, NOT the quantiser, NOT
  the profile.** The plan's block is `road_class == RESIDENTIAL && scenic_score < 7 -> 0.5`: the demotion is
  written to fire on a residential way that is NOT in the high band, so a residential way that reaches 7
  collects `bands.high` and escapes the anti-rat-run clause entirely. 131 real residential ways do exactly
  that. Of the three candidates the task names:

  - (b) a ceiling at quantisation is REFUSED: `tagwriter` writes `scenic_score` and `scenic_score_unit` from
    one number and T-0204's hardened oracle requires `quantise(unit) == score`; a ceiling applied to the
    integer alone ships 6 beside 0.7228 and is malformed on its face. R2 below makes that clause tighter, not
    looser.
  - (c) changing only the routing clause is REFUSED as this task's fix, because `services/routing/profiles/*.json`
    and `services/api/src/customModel.ts` are serial/other files (T-0190/T-0209) and because the corpus would
    still SAY a Bel Air cul-de-sac is a 7. RECORDED FOR T-0190/T-0209 anyway (below), because the profile
    clause is still too narrow.
  - (a) a class factor in `score.py` is REFUSED for two reasons. First, parity: `score.score` is the symbol
    `services/etl/tests/test_assemble.py::test_gate_scenickit_parity_to_1e_6_over_the_shared_scoring_fixture`
    drives through `assemble.score_record` against the same 1000-row hand-transcribed fixture
    `Tests/ScenicKitTests/SegmentScoreContractTests.swift` reads, and `Sources/ScenicKit/Scoring/SegmentScore.swift`
    is that formula and nothing else. A class factor there is a Swift change too, and P-PROD-01's statement
    ("one fixture set through all three") is what makes the two implementations one. Second, a MULTIPLIER
    cannot bound anything by construction: `score.score` returns up to 1.0, so any factor >= 0.65 still
    permits a 7 and any factor below it is a number chosen to fit today's maximum.

  So the cap is a CEILING (`min`) on the table's `score`, applied in `assemble.scored_row` AFTER
  `score_record` has run - exactly where and why the safety gate already forces `GATE_SCORE` (assemble.py's
  own ruling: "score.py:29-31 puts them in ScenicKit.Gates and out of the scorer ... So a gate here forces
  `score` to GATE_SCORE AFTER the scorer has run"). PARITY IS THEREFORE UNTOUCHED: `score.py` and
  `SegmentScore.swift` keep the identical formula, the parity gate drives `score_record` which is upstream of
  the ceiling, and NO Swift change is required by this task. What ScenicKit consumes downstream is
  `ScoredEdge.scenic_score`, the 0..10 column the corpus ships, so the ceiling reaches the router and the app
  through the data, which is where a corpus policy belongs. STILL OPEN if `SegmentScore` is ever made a
  PRODUCER of the shipped column rather than the formula's oracle: the ceiling moves with it.

  **WHAT THE CAP IS, per class** (`assemble.CLASS_SCORE_CEILING`):

      residential    0.6499   living_street  0.6499   service  0.0

  0.6499 is the largest value the tag can carry at its four decimals that `tagwriter.quantise` sends BELOW
  the router's high band: `quantise(0.6499) = floor(6.499 + 0.5) = 6`, and 0.6500 would be 7. It is bound to
  the quantiser by a test rather than asserted in prose. `living_street` is capped although not one of its 11
  ways reaches 6 today: the class is the plan's rat-run class by meaning, and a cap that only exists where the
  data already complies is a cap that has never been red - the fixture row drives it.

  **SERVICE: zero-class, not a cap** (T-0168 STILL OPEN 3, 312,645 LA ways). A `highway=service` way is a
  driveway, a parking aisle, a fire road or an alley: it is never a scenic DRIVE, and the measurement agrees -
  the five highest-scoring named ones are two fire roads and three unnamed stubs. Capping service at 0.6499
  would leave 559 of them at 6 and 2,972 at or above 4, collecting `bands.mid` with NO demotion clause of any
  kind (the Worker's clause names RESIDENTIAL only), which is the same defect one band down. So service scores
  0.0, for the same reason and with the same consequence as a motorway: **penalized, not excluded** - the
  invariant holds, a service way stays routable, a park entrance or a driveway is still drivable to a
  destination on it, it is simply never a reason to lengthen a drive. This is expressed as a ceiling of 0.0 in
  the same table rather than as a new member of `byways.SCENIC_ZERO_CLASSES`, because that set lives inside
  `score.score` and is parity-bound (see R1), and because the two facts are different: motorway/trunk are the
  plan's zero classes, service is this corpus's.

  **UNCLASSIFIED: NOT capped, ruled explicitly.** GraphHopper's `road_class` for `highway=unclassified` is not
  RESIDENTIAL, the plan's rat-run clause never named it, and the measurement says it is not a rat-run class
  here: 5 of 570 reach 7 and the top of them are Franklin Canyon Drive and Temescal Canyon Road - genuine
  named canyon drives, the roads this product exists to find. Capping it would delete rank 8 of the grid
  window's top ten to buy nothing. Franklin Canyon Drive 13292286 is asserted UNCHANGED at 7 in the test, so
  an agent who later extends the ceiling table over `unclassified` turns it red by name.

  **A GENUINELY SCENIC RESIDENTIAL ROAD, ruled honestly.** It exists - Crescent Drive really is pretty, and
  0.7228 is not a measurement error. The owner's bar is ZERO rat-runs: one cut-through past a school and the
  app is deleted. A residential street is therefore never routed onto FOR BEAUTY, and the cap says so out
  loud: a residential way can still carry up to 6, still be routed through when it is the way to the
  destination, and still be demoted by the profile's 0.5 clause for a detour. What it loses is the ability to
  be the REASON for a detour. That is the trade, taken deliberately, and it is the safety-conservative
  direction.

  **RECORDED FOR T-0190/T-0209** (the profiles and the Worker, not mine): the anti-rat-run clause is
  `road_class == RESIDENTIAL` only. With this cap no residential way reaches 7 so the clause now always fires
  on them, but LIVING_STREET and SERVICE have no demotion clause at all in `customModel.ts:219`. The corpus
  answer here (service 0.0, living_street <= 6) makes that gap harmless today; the clause should still name
  all three, and the band thresholds (`scenic_score >= 7` / `>= 4`) must stay where they are or 0.6499 stops
  meaning what it means - a second anchor for the same number, which is why the test binds the ceiling to
  `tagwriter.quantise` and to the literal 7.

  **R2 THE QUANTISE MISMATCH.** `tagwriter.tags_for_row` computes `quantise(row["score"])` from the UNROUNDED
  score and `fixed(row["score"])` at four decimals from the same source, so the two tags are derived from two
  different numbers and disagree whenever rounding to four decimals crosses a `.x5` boundary - 17 real ways.
  FIX: the unit STRING is produced first and the integer is quantised from the number that string carries
  (`quantise(float(unit))`), so the way ships ONE number written twice and the oracle's `quantise(unit) ==
  score` clause is true by construction rather than by luck. Read-back row 13332407 (Yoakum Drive,
  residential, 0.5499510668) is the boundary fixture: 5 today, 6 after. It is also residential, and 0.5499 is
  below the ceiling, so the two rulings are independent on that row and the fixture proves both.
- 2026-09-19T12:04:50Z RED THEN GREEN, and the real re-run, by agent/claude-opus-5. Count lines quoted as
  each stage landed.

  RED FIRST, by name, before a line of the fix, `services/etl/tests/test_class_cap.py` over the shipping
  path `assemble.scored_row -> tagwriter.tags_for_row`: **11 failed, 5 passed in 0.60s**. The eleven were
  `test_no_capped_class_way_reaches_the_routers_high_band` (five real ways ship 7), the five
  `test_each_measured_offender_was_a_seven_and_now_is_not[Crescent Drive|Sullivan Fire Road|Sullivan Ridge
  Fire Road|Scenario Lane|Oakmont Street]`, `test_a_service_way_scores_zero_like_a_motorway_and_is_not_excluded`,
  `test_a_living_street_is_capped_although_no_real_one_reaches_six`,
  `test_the_ceiling_is_the_boundary_of_the_high_band_read_through_the_shipping_quantiser` (AttributeError:
  no `CLASS_SCORE_CEILING`), `test_the_integer_and_the_unit_are_one_number_on_the_boundary_row` (5 != 6) and
  `test_every_row_ships_an_integer_that_is_the_quantisation_of_the_unit_beside_it` ("Yoakum Drive
  (residential, way 13332407) ships scenic_score=5 beside 0.5500"). GREEN after: **16 passed in 0.30s**.

  Whole suite: `cd services/etl && python -m pytest tests -rs -o addopts=` -> **1186 passed in 80.31s**, zero
  skips (the `-rs` section is empty).

  MUTATION POPULATION, `python ops/mutate/scenic_tags.py`, floor 35 -> 44 with `assemble.py` added as a third
  subject: **MUTATIONS: 44 caught, 0 missed, 0 skipped, of 44 / EQUIVALENT: 0 caught, 3 missed, 0 skipped, of
  3 / MUTATE OK caught=44/44 equivalent_caught=0**. The nine new ones and their catchers:
  `quantise the UNROUNDED score ...` <- test_class_cap.py::test_the_integer_and_the_unit_are_one_number_on_the_boundary_row;
  `re-derive the unit from the integer ...` <- test_tagwriter.py::test_a_scored_way_carries_the_integer_the_unit_score_and_every_term;
  `drop the ceiling ...`, `raise the ceiling BY one step ...`, `forget residential ...`, `forget
  living_street ...`, `read the ceiling off the gate reason ...` <-
  test_class_cap.py::test_no_capped_class_way_reaches_the_routers_high_band; `cap a service way instead of
  zeroing it ...` <- test_class_cap.py::test_a_service_way_scores_zero_like_a_motorway_and_is_not_excluded;
  `cap unclassified too ...` <- test_class_cap.py::test_the_scenic_roads_do_not_move[13292286].
  `python ops/mutate/scenic_tags.py --prove-vacuity` -> **VACUITY: 0 caught, 44 missed, 0 skipped, of 44 /
  VACUITY PROVED**.

  THE THREE REAL WINDOWS RE-TAGGED with the new code, natively for `assemble`/`tagwriter` and through the
  pinned container for `osmium cat` (inputs read-only from the MAIN checkout, outputs under this worktree's
  gitignored `services/etl/work/`):

      ASSEMBLE ways=11740 zero_class=386 gated=5589 sinuosity_declined=619 points_of_interest_absent=11740 null_score=0
      WRITE ways=12402 scored=11740 refused=0 gated=5589 not_a_road=662      (canyon, twice, byte-identical)
      sha256 472b2a34f292f61f69afdb30ba8a43ecd7d7d50f88b317682f7b8972aaf78da1  window-tagged-{1,2}.osm.xml
      CHECK4 null_score=0 gated_scored=0 malformed=0 scored=11740 refused=0 not_a_road=662

      ASSEMBLE ways=11239 zero_class=476 gated=1927 sinuosity_declined=575 points_of_interest_absent=11239 null_score=0
      WRITE ways=11451 scored=11239 refused=0 gated=1927 not_a_road=212      (grid-a, twice, byte-identical)
      sha256 09dca32904457ad9d14f63a8f95d3b35f34fa9506066b37518a1f1193a4b2057  grid-a-tagged-{1,2}.osm.xml
      CHECK4 null_score=0 gated_scored=0 malformed=0 scored=11239 refused=0 not_a_road=212

      ASSEMBLE ways=23474 zero_class=772 gated=3696 sinuosity_declined=1074 points_of_interest_absent=23474 null_score=0
      WRITE ways=23887 scored=23474 refused=0 gated=3696 not_a_road=413      (grid-b, twice, byte-identical)
      sha256 03245c2954b9952e7aed189cad1933f2e16332c364da4a6d276ff7e5d90b7108  grid-b-tagged-{1,2}.osm.xml
      CHECK4 null_score=0 gated_scored=0 malformed=0 scored=23474 refused=0 not_a_road=413

  **malformed=0 on ALL THREE** - the 17 are gone, measured on the shipped bytes and not on the table.

  THE TOP TENS, new beside old (`python -m etl.scenecheck <readback> --top 10`):

      CANYON - IDENTICAL, all ten ways, all ten integers, all ten units:
        1 74344132 Topanga Canyon Boulevard primary 8 (0.7722) - 2 74344113 Topanga 8 (0.7697)
        3 667514937 North Topanga 8 (0.7679) - 4 358703394 Stunt Road 8 (0.7563)
        5 456361801 North Topanga 7 (0.7464) - 6 38311860 Topanga 7 (0.7401)
        7 1079750100 Old Topanga Canyon Road 7 (0.7367) - 8 46752395 Old Topanga 7 (0.7314)
        9 13346012 Piuma Road 7 (0.7306) - 10 1237332026 Fernwood Pacific Drive 7 (0.7284)

      GRID-A  old: 44327906 Mulholland 0.7261 - 632613339 Sullivan Fire Road 0.7227 - 13290126 Sullivan
        Ridge Fire Road 0.7215 - 121304178 Oakmont Street 0.7189 - 13293766 Beverly Glen Terrace 0.7133 -
        13377650 Mandeville Canyon Road 0.7125 - 721642253 (service) 0.7118 - 121254098 Will Rogers State
        Park Road 0.7079 - 405362186 Mulholland 0.7064 - 581817596 (service) 0.7057
      GRID-A  new: 1 44327906 Mulholland secondary 7 (0.7261) - 2 13377650 Mandeville Canyon Road tertiary
        7 (0.7125) - 3 405362186 Mulholland 7 (0.7064) - 4 1533792498 Mulholland 7 (0.6988) - 5 13377647
        Mandeville Canyon Road 7 (0.6688) - 6 399156621 West Sunset Boulevard 7 (0.6669) - 7 435695311
        Temescal Canyon Road unclassified 7 (0.6636) - 8 13313778 Chautauqua Boulevard 7 (0.6541) -
        9 13278980 Round Valley Drive residential 6 (0.6499) - 10 13278983 Round Valley Drive 6 (0.6499)

      GRID-B  old: 518410361 Mulholland 0.7361 - 787842196 Mulholland 0.7299 - 13419334 Crescent Drive
        0.7228 - 518410363 Mulholland 0.7226 - 13292286 Franklin Canyon Drive 0.7203 - 13379402 Scenario
        Lane 0.7201 - 13419340 Crescent Drive 0.7121 - 159524496 Mulholland 0.7100 - 386470272 (service)
        0.7098 - 822134900 (service) 0.7097
      GRID-B  new: 1 518410361 Mulholland 7 (0.7361) - 2 787842196 Mulholland 7 (0.7299) - 3 518410363
        Mulholland 7 (0.7226) - 4 13292286 Franklin Canyon Drive unclassified 7 (0.7203) - 5 159524496
        Mulholland 7 (0.7100) - 6 399262414 Laurel Canyon Boulevard 7 (0.7081) - 7 1533792498 Mulholland
        7 (0.7022) - 8 518410359 Mulholland 7 (0.7013) - 9 38555783 Laurel Canyon Boulevard 7 (0.6994) -
        10 1174237703 West Sunset Boulevard 7 (0.6975)

  Every residential street and every fire road is out of both grid top tens; Mulholland, Topanga, Stunt,
  Piuma, Fernwood Pacific, Mandeville Canyon and Franklin Canyon Drive are all where they were.

  THE FIXTURES ARE NOT RE-RECORDED, ruled. `grid_top25.json` and `canyon_top25.json` are T-0204's dated
  recording of ITS run ("produced_by: etl.scenecheck.top, T-0204's hardened build"), the ranking tests in
  `tests/test_window_ranking.py` read only those committed files, and none of them requires a new recording:
  the whole suite is green above. The whitelist test keeps its two Mulholland ids untouched, and it is TRUE
  on the NEW read-backs as well - the only merged grid ways at or above the canyon bound 0.7284 are 518410361
  (0.7361) and 787842196 (0.7299), checked against `scenecheck.top(grid-{a,b}-readback, 25)` from this run.
  A re-recording is a snapshot reference, which CLAUDE.md reserves for a human-initiated commit reviewed by a
  different agent; the new numbers are in this Log and in the PR body instead.

  STILL OPEN, recorded rather than hidden:
  1. The profile/Worker clause (`customModel.ts:219`) names RESIDENTIAL only. With the cap that is harmless -
     service is 0 and living_street cannot reach 7 - but LIVING_STREET and SERVICE have no demotion of their
     own. T-0190/T-0209.
  2. `unclassified` is uncapped by ruling. 5 of 570 reach 7 and today they are canyon drives; the class is
     watched by `test_the_scenic_roads_do_not_move[13292286]` in one direction only.
  3. P-PROD-01's assertion is still `TODO` (pending T-0012), so parity is held by
     `test_gate_scenickit_parity_to_1e_6_over_the_shared_scoring_fixture` and not by a pin. This task keeps
     the ceiling OUT of `score.py` precisely so that gate stays true; if `SegmentScore.swift` is ever made a
     producer of the shipped 0..10 column, the ceiling must move with it.
  4. The corpus itself is not re-published here: these three windows are the evidence, not the shipped LA
     graph. Whoever re-runs the region pays the re-tag.
- 2026-09-19T12:04:50Z FINAL PRE-REVIEW ACCEPTANCE, re-run bare by agent/claude-opus-5 over the code as it
  is committed (the only thing this commit adds on top of e05bd89, which every number below was produced
  against, is this Log - no subject, test, fixture or population file changed after the runs):

      cd services/etl && python -m pytest tests -rs -o addopts=
        -> 1186 passed in 99.86s (0:01:39)        zero skips, the -rs section is empty
      python ops/mutate/scenic_tags.py
        -> MUTATIONS: 44 caught, 0 missed, 0 skipped, of 44
           EQUIVALENT: 0 caught, 3 missed, 0 skipped, of 3
           MUTATE OK  caught=44/44 equivalent_caught=0            (exit 0)
      python ops/mutate/scenic_tags.py --prove-vacuity
        -> VACUITY: 0 caught, 44 missed, 0 skipped, of 44 / VACUITY PROVED   (exit 0)
      python ops/lib/check-mutate-population.py
        -> P-PROC-06: 71 modules, 23 covered by 10 populations, 25 allowlisted, 0 added by this branch
           P-PROC-06: every added module is covered or allowlisted; the floor of 22 holds   (exit 0)
           [22 -> 23 covered: services/etl/etl/assemble.py leaves the DEBT list, 24 -> 23]
      bash ops/lib/check-line-cap
        -> P-SRC-02: 83 Swift files tracked (Sources=27, Tests=38, apps/ios=18), none over 300 lines (exit 0)
      bash ops/lib/check-exec-bits
        -> P-OPS-01: 77 files, 23 required present, all modes correct   (exit 0)
      bash ops/queue-check
        -> QUEUE OK (205 tasks)   (exit 0)

  No Swift changed, so `swift test --filter ScenicKitTests` was NOT run and is not claimed: the ceiling is
  deliberately outside `score.py` and `SegmentScore.swift` is byte-for-byte what it was on main (R1).

  `wc -l` on every touched file, at this commit:

      293  services/etl/etl/assemble.py
      165  services/etl/etl/tagwriter.py
      195  services/etl/tests/test_class_cap.py
      237  services/etl/tests/fixtures/class_cap_rows.json
      186  ops/mutate/scenic_tags.py
      233  ops/mutate/scenic_tags_mutations.py
      (the task file's own `wc -l` is deliberately NOT quoted: this block lives in it, so any number
       written here is wrong the moment it is written. It carries no 300-line cap - `ops/lib/check-line-cap`
       counts tracked Swift - and it is above 300.)

  `assemble.py` is 293 of the 300-line cap: the next agent to touch it splits it rather than squeezing.
  `state: claimed` and `reviewer: null` are untouched; the Log is appended to and nothing above it is edited.
- 2026-09-19T13:08:13Z MERGED origin/main (#115, #116) into task/T-0207 by agent/claude-opus-5, merge
  commit f76fe98, no conflict: main's `surfacecoverage.py` is a new module and `ops/lib/check-mutate-population.py`
  and `ops/mutate/scenic_tags*.py` came back unchanged on main's side. The acceptance block below is re-run on
  the MERGED head, not on e05bd89.
- 2026-09-19T13:08:13Z **R3 THE CEILING IS UNCONDITIONAL**, ruled by agent/claude-opus-5 after the pre-review
  mutant pass, which ran three unwritten mutants and found TWO BLOCKING SURVIVORS of ONE class: the ceiling in
  `assemble.scored_row` can be CONDITIONED ON AN INPUT and nothing goes red.

      M2  `if ceiling is not None and value is not None:` -> `... and value < 0.75:`   (demote the 7s only)
          zero test_class_cap.py reds; a residential, a living_street and a service row at raw 1.0 each ship
          scenic_score=10.
      M5  `... and record.byway_status is None:`   (no ceiling on a way that matched a byway)
          zero reds; a residential stub geometrically matched to Topanga Canyon Boulevard - an ELIGIBLE byway
          in the canyon window, so a real match, not a hypothetical - ships 10.

  CAUSE, not spelling: every capped-class fixture row carried the SAME shape of input - score 0.72-0.73, no
  byway status, surface `asphalt` or `paved`, terms from one real street. A fixture that does not span the
  inputs cannot see a condition on one. RULING: the ceiling holds for its classes on EVERY input
  `scored_row` can read on its way to it, and that is proved through the SHIPPING path
  (`assemble.scored_row` -> `tagwriter.tags_for_row`), never at the ceiling's own line. The code is NOT
  changed - it was already unconditional - so this ruling is spent entirely on evidence:

  1. `services/etl/tests/fixtures/class_cap_rows.json` gains TWO synthetic rows, each `"synthetic": true`
     with its reason in its own `why` field (never in a comment): way 999999999998, every ranked term at the
     end `score.score` REWARDS - furniture and impervious are penalties, so their maximum is 0.0 - which is
     raw score **1.0**, the largest input the ceiling can ever be handed; and way 999999999997, every term
     literally at 1.0, penalties included, raw score **0.8077298313366432**, the 0.75+ row. Both are
     re-derived through `assemble.score_record` by the fixture's own drift test. The existing living_street
     row is labelled `"synthetic": true` as well, and `test_every_fixture_row_is_a_real_way_or_says_it_is_synthetic`
     holds 9 real / 3 synthetic and binds the label to the row's `window` field.
  2. `test_the_ceiling_is_unconditional_over_every_input_scored_row_reads` runs the MATRIX: 4 rows (the real
     Crescent Drive profile, the living_street row, raw 1.0, every-term-1.0) x 3 byway statuses (None,
     `byways.ELIGIBLE`, `byways.DESIGNATED` - read from the module, not spelled as literals) x 3 surfaces
     (None, asphalt, paved) = 36 cases, each shipped as residential, as living_street, as service and as the
     UNCAPPED CONTROL tertiary: 144 shipped rows. residential/living_street never reach 7, service is exactly
     `0` beside `0.0000`, and the tertiary control ships `uncapped_integer(row)` on every one of the 36 - the
     assertion that keeps this a cap on rat-runs and not a cap on scenery. NON-VACUITY is asserted, not
     assumed: all 36 control rows reach 7 without a ceiling, so a capped class staying below it means something.
  3. `ops/mutate/scenic_tags_mutations.py` ships the CLASS, not the two spellings: the two survivors by name
     plus the other two inputs of the same kind (a TERM - `and record.canopy < 0.9`; the SURFACE -
     `and record.surface != "asphalt"`). Floor **44 -> 48**.

  RED FIRST, by name, each of the four applied to `services/etl/etl/assemble.py` with `__pycache__` purged and
  1.1 s of settle either side (throwaway `services/etl/work/red_T0207.py`, gitignored), then restored:

      demote only the sevens (M2)          exit=1  test_the_ceiling_is_unconditional_over_every_input_scored_row_reads
                                                   (+ test_no_capped_class_way_reaches_the_routers_high_band)
      no ceiling on a matched byway (M5)   exit=1  test_the_ceiling_is_unconditional_over_every_input_scored_row_reads
                                                   - THE ONLY RED. M5 is invisible to every other test in the file.
      condition on a TERM                  exit=1  test_the_ceiling_is_unconditional... (+ 4 others)
      condition on the SURFACE             exit=1  test_the_ceiling_is_unconditional... (+ 5 others)

  Pristine: `tests/test_class_cap.py` 18 passed after each restore.
- 2026-09-19T13:08:13Z **THE PASS'S UNSUPPORTED NOTE, measured rather than asserted** (agent/claude-opus-5;
  throwaway `services/etl/work/diff_T0207.py` and `diff2_T0207.py`, gitignored; both read the MAIN checkout's
  OLD scored tables and this worktree's NEW ones, 46,453 rows, way ids identical on all three windows).
  WHAT ELSE DIFFERS between the old and the new real tables besides the ceiling - the honest answer is NOT
  "the 17 integers of R2". Ways whose shipped `scenic_score_unit` string changed, by class:

      class            n      unit_moved  int_moved  int_moved_with_unit_unchanged
      service        24020       15412      15339          0
      residential     9901        1952        154          6
      secondary       3677         778          7          4
      primary         2750         592          4          1
      tertiary        2371         503          2          0
      unclassified     570         100          3          0
      primary_link     189          23          0          0
      secondary_link   132          16          0          0
      tertiary_link     42          10          0          0
      track/motorway/motorway_link/trunk/trunk_link/living_street/footway  0  0  0
      TOTAL          46453       19386      15509         11

  THE CEILING explains the capped classes (service 15,412 zeroed, residential 1,952 pulled to 0.6499,
  living_street 0 - no real one was ever above it). R2's one-number fix explains the LAST column: 11 ways
  whose integer moved with the unit byte-identical. It is 11 and not 17 because 6 of the 17 boundary ways
  ALSO had their unit move (inference from 17 - 11 = 6, not measured separately), for the third reason:
  **2,022 ways of UNCAPPED classes moved their unit although no ceiling can touch them - the CURVATURE term
  moved under them** (778 secondary + 592 primary + 503 tertiary + 100 unclassified + 49 of the three link
  classes). Per term, over all three windows:
  `curvature` moved on 39,612 of 46,453 rows (max delta 0.4504), `furniture` on 375 (max 0.000186), and
  elevation_gain, speed_fit, sinuosity, canopy, relief, impervious, water, points_of_interest on **0**.
  The curvature column's MEAN is identical old vs new and its distinct-value count is 8,478 vs 8,477 in the
  canyon window, so this is a rank-normalised term whose ranking shifted, not a new formula.
  NOT THIS BRANCH: `git diff bcb7000..HEAD -- curvature.py normalise.py way_record.py geom.py snap.py
  sinuosity.py assemble.py` is `assemble.py | 20 ++` and nothing else - the ceiling, this task's own twenty
  lines. And the pipeline at the merged head is DETERMINISTIC and reproduces the owner's new tables exactly:
  `python -m etl.assemble --input <MAIN>/work/la/window-doc.json` run TWICE
  (`ASSEMBLE ways=11740 zero_class=386 gated=5589 sinuosity_declined=619 points_of_interest_absent=11740
  null_score=0`, both runs) differs from run 2 on **0** ways' curvature and from the owner's new
  `window-scored.json` on **0** ways' curvature - and from the OLD main-checkout table on **8,929**.
  So the OLD tables were not produced by the committed producers this head carries, and they are a valid
  baseline for the CLASS comparison (which ways are residential/service, which reached 7) and NOT for a
  byte comparison of any uncapped way's unit. STILL OPEN 5, filed rather than hidden: name the build that
  wrote `services/etl/work/la*/`'s scored tables on 2026-09-18, or re-run all three windows from the
  committed head before any future task quotes those files as a baseline. Nothing in this task's acceptance
  depends on them: the three top tens and CHECK4 below are read off the NEW read-backs only.
