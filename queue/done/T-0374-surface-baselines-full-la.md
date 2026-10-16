---
id: T-0374
title: Re-measure surfacecoverage.BASELINES over the FULL LA corpus - the canyon-window baselines put motorway and motorway_link red on full LA
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T07:25:12Z
lease_expires_at: 2026-10-17T07:25:12Z
worktree: .worktrees/T-0374
branch: task/T-0374
exclusive: []
touches: [services/etl/etl/surfacecoverage.py, services/etl/tests/, ops/lib/, ops/mutate/, pins/PINS.yaml, queue/]
pins_affected: [P-OPS-09, P-DATA-04]
reviewer: agent/rv1-t0374
depends_on: [T-0372]
verify: [ops/check-pins]
acceptance:
  - "A1 BASELINES == the full LA measurement x 0.75 truncated, 15 classes (R1-R3): (cd services/etl && python -m pytest -q tests/test_surfacecoverage.py) all pass, including test_baselines_are_exactly_the_measurement_times_the_ruled_margin over tests/fixtures/surface_coverage_la_full.json"
  - "A2 RED FIRST: the new/moved tests run against the OLD literals fail by name (the exactly-measurement test, the green-over-full-LA test), then pass with the new literals"
  - "A3 python ops/mutate/surfacecoverage.py -> MUTATE OK caught=25/25 equivalent_caught=0; --prove-vacuity -> VACUITY PROVED"
  - "A4 wsl python3 ops/lib/sane_corpus.py --corpus /home/phineas/t0242/la-corpus.sqlite -> corpus-surface ok, rc 0 (was rc 4 on motorway, motorway_link); the canyon window through the same command -> corpus-surface FAIL naming the R4 classes (the check seen red)"
  - "A5 bash ops/lib/check-sane-corpus green on every row; P-DATA-04's assertion green (bash -c over its PINS.yaml text)"
  - "A6 gates on the merged head: bash ops/lib/check-sane-corpus, bash ops/lib/check-sane-exit-order, python ops/lib/check-mutate-population.py, python ops/lib/check-pins-yaml.py, bash ops/queue-check"
  - "A7 wc -l <= 300: services/etl/etl/surfacecoverage.py, services/etl/tests/test_surfacecoverage.py, ops/mutate/surfacecoverage.py"
---
## Brief

Filed by agent/claude-opus-5 from T-0372 round 2 (2026-10-16). surfacecoverage.BASELINES were measured on T-0205's
canyon window (x 0.75). T-0372 measured the FULL LA corpus (T-0275, /home/phineas/t0242/la-corpus.sqlite in WSL,
560208 ways, 874391 segments, schema 3) through `python3 ops/lib/sane_corpus.py --corpus`: rc=4,
`FAIL corpus-surface motorway: surface coverage 0.4297 is below the baseline 0.593 (3217 known of 7486 ways);
motorway_link: surface coverage 0.1905 is below the baseline 0.318 (1887 known of 9908 ways)`. The canyon window
itself is green ([] verdict). So ops/sane exit 4 goes red the moment a full LA corpus sits at
$SCENIC_REGION_WORK/la-corpus.sqlite - correctly by today's numbers, wrongly by intent.

MEASURE first, read-only: every class's known/total over the full LA corpus's meta.surface_coverage (quote the whole
table), next to the canyon window's. RULE whether BASELINES become per-region (la full vs the CI golden set) or one
table re-derived from the full region, and the 0.75 margin. Then: the new literals, the surfacecoverage tests and
its mutation population re-run, check-sane-corpus (its rows place classes on BASELINES, so they follow), and the full
LA corpus through sane_corpus.py green on corpus-surface. Do NOT touch prod/R2.

## Log
- 2026-10-16T07:25:12Z claimed by agent/claude-opus-5; lease until 2026-10-17T07:25:12Z
- 2026-10-16T07:28:19Z MEASURED, read-only (sqlite `mode=ro` through WSL python3; script in the ignored
  services/etl/work/t0374-measure.py; the last column is the frac x 0.75 truncated to three decimals, R3's rule).
  FULL LA, /home/phineas/t0242/la-corpus.sqlite: meta.region `la`, bbox -1190609263,336832753,-1177641001,344920674,
  osm_features 560208 rows, 16 classes in meta.surface_coverage:
  ```
  service          known=27188   unknown=284512  unpaved=945    total=312645  frac=0.0870 x0.75trunc3=0.065
  residential      known=21832   unknown=77759   unpaved=124    total=99715   frac=0.2189 x0.75trunc3=0.164
  primary          known=26952   unknown=16858   unpaved=5      total=43815   frac=0.6151 x0.75trunc3=0.461
  secondary        known=24224   unknown=18013   unpaved=0      total=42237   frac=0.5735 x0.75trunc3=0.430
  tertiary         known=14113   unknown=11267   unpaved=0      total=25380   frac=0.5561 x0.75trunc3=0.417
  motorway_link    known=1887    unknown=8021    unpaved=0      total=9908    frac=0.1905 x0.75trunc3=0.142
  track            known=359     unknown=6545    unpaved=1244   total=8148    frac=0.0441 x0.75trunc3=0.033
  motorway         known=3217    unknown=4269    unpaved=0      total=7486    frac=0.4297 x0.75trunc3=0.322
  unclassified     known=1761    unknown=3670    unpaved=29     total=5460    frac=0.3225 x0.75trunc3=0.241
  trunk            known=1380    unknown=559     unpaved=0      total=1939    frac=0.7117 x0.75trunc3=0.533
  primary_link     known=986     unknown=733     unpaved=1      total=1720    frac=0.5733 x0.75trunc3=0.429
  secondary_link   known=532     unknown=429     unpaved=0      total=961     frac=0.5536 x0.75trunc3=0.415
  tertiary_link    known=225     unknown=193     unpaved=0      total=418     frac=0.5383 x0.75trunc3=0.403
  living_street    known=58      unknown=137     unpaved=0      total=195     frac=0.2974 x0.75trunc3=0.223
  trunk_link       known=132     unknown=46      unpaved=0      total=178     frac=0.7416 x0.75trunc3=0.556
  road             known=1       unknown=2       unpaved=0      total=3       frac=0.3333 x0.75trunc3=0.250
  ```
  CANYON WINDOW, services/etl/work/t0266/la-corpus.sqlite (main checkout): meta.region `la` (the SAME value),
  bbox -1189683133,340026669,-1185138948,341723550, osm_features 11740 rows, 15 classes:
  ```
  service          known=268     unknown=6502    unpaved=48     total=6818    frac=0.0393 x0.75trunc3=0.029
  residential      known=313     unknown=2229    unpaved=20     total=2562    frac=0.1222 x0.75trunc3=0.091
  track            known=18      unknown=870     unpaved=100    total=988     frac=0.0182 x0.75trunc3=0.013
  tertiary         known=119     unknown=287     unpaved=0      total=406     frac=0.2931 x0.75trunc3=0.219
  secondary        known=106     unknown=171     unpaved=0      total=277     frac=0.3827 x0.75trunc3=0.287
  trunk            known=82      unknown=169     unpaved=0      total=251     frac=0.3267 x0.75trunc3=0.245
  primary          known=91      unknown=90      unpaved=0      total=181     frac=0.5028 x0.75trunc3=0.377
  unclassified     known=13      unknown=79      unpaved=2      total=94      frac=0.1383 x0.75trunc3=0.103
  motorway_link    known=31      unknown=42      unpaved=0      total=73      frac=0.4247 x0.75trunc3=0.318
  motorway         known=38      unknown=10      unpaved=0      total=48      frac=0.7917 x0.75trunc3=0.593
  trunk_link       known=3       unknown=11      unpaved=0      total=14      frac=0.2143 x0.75trunc3=0.160
  primary_link     known=1       unknown=9       unpaved=0      total=10      frac=0.1000 x0.75trunc3=0.075
  tertiary_link    known=2       unknown=6       unpaved=0      total=8       frac=0.2500 x0.75trunc3=0.187
  secondary_link   known=0       unknown=6       unpaved=0      total=6       frac=0.0000 x0.75trunc3=0.000
  living_street    known=0       unknown=4       unpaved=0      total=4       frac=0.0000 x0.75trunc3=0.000
  ```
  The window's last column reproduces today's BASELINES exactly (10 of 10), so the derivation rule is the one
  shipped. Full LA is ABOVE the window in 8 of 10 baselined classes and below it only in motorway (0.4297 vs
  0.7917) and motorway_link (0.1905 vs 0.4247) - the two T-0372 saw red. A window is not a sample of its region.
- 2026-10-16T07:31:00Z RULINGS (before any code).
  R1 ONE TABLE, RE-DERIVED FROM THE FULL REGION; NOT PER-REGION. The only per-region key a corpus carries is
  meta.region, and it reads `la` on BOTH corpora above, so a table keyed by region cannot tell the window from the
  region - the thing that went wrong here. The plan's CI golden set (Bay Area) has no built corpus and no
  measurement, so it has no row to key; a keyed table today is a dict of one. The shipped corpus is the full
  region, and the plan says the baselines guard a REBUILD of it: a floor under what the full region measures by
  more than the margin (the window's trunk 0.245 against full LA's 0.7117) cannot see half the tags lost, and a
  floor above it (motorway 0.593 against 0.4297) fails every honest build. The module docstring's existing rule
  stands: a region without its own measurement is refused by name, and its recourse is its own measured set - a
  later task when a second region is built, not a key added now.
  R2 THE MARGIN STAYS 0.75, TRUNCATED TO THREE DECIMALS. The defect sends a fraction to ~0; full LA's lowest
  baseline is track 0.033 (359 known of 8148), still 0.033 above a collapse. The other side: every class of the
  full region passes its floor by 25% relative; the smallest baselined class (trunk_link, 178 ways) would have to
  lose 33 surveyed ways between two rebuilds to go red - not ordinary editing. No region-wide evidence argues for a
  different number, and moving it would change two things at once.
  R3 THE CLASS SET FOLLOWS THE EXISTING S2 DERIVATION: every class with total >= MIN_CLASS_WAYS (25). Over full LA
  that is 15 classes - the 10 of today plus living_street 0.223, primary_link 0.429, secondary_link 0.415,
  tertiary_link 0.403, trunk_link 0.556; `road` (3 ways) stays unbaselined. Keeping the old 10 would need a
  second, hand-picked whitelist rule beside the derivation the test already enforces.
  R4 THE CANYON WINDOW IS REFUSED under the new table, by name: service 0.0393<0.065, residential 0.1222<0.164,
  track 0.0182<0.033, tertiary 0.2931<0.417, secondary 0.3827<0.430, trunk 0.3267<0.533, unclassified
  0.1383<0.241, and the five new classes too small (4-14 ways). Intended (R1): it is a window. Consequence quoted
  so nobody rediscovers it: ops/sane exits 4 on a box whose $SCENIC_REGION_WORK/la-corpus.sqlite IS the window.
  The window fixture stays (print/encode/relabel tests read it) and one test asserts it is refused.
  R5 tests/fixtures/surface_coverage_la_full.json is the committed measurement the tests bind BASELINES to (the 16
  rows above, sorted, indent 2, exactly meta.surface_coverage's numbers); the green-over-measurement, every-
  baseline-met and exactly-measurement-x-margin tests move to it. The S4 boundary rows move with residential's
  literal (164/1000 on it, 163/1000 one under). The --corpus-form extract adds five (cls, highway) pairs from
  tagfilter.WAY_CLASSES (trunk/trunk_link, primary/primary_link, secondary/secondary_link, tertiary/tertiary_link,
  living_street/living_street) so the healthy built corpus still carries every baselined class.
  R6 P-DATA-04's assertion runs the check green over the WINDOW fixture; it moves to the full-LA fixture and its
  why text gets a dated T-0374 paragraph (older sentences are history, not rewritten). P-OPS-09's closing
  sentence ("The FULL LA corpus is RED here today") gets the same dated paragraph. pins_affected gains P-DATA-04.
  R7 ops/mutate/surfacecoverage.py has no --only (refuse_unsupported), so the Brief's "--only the touched rows" is
  not available; the population is ~2 minutes, so it runs WHOLE (and --prove-vacuity) rather than adding a flag
  here. Touched anchors: the residential, service and motorway literals, and the "add a baseline" mutant moves
  from living_street (now a real baseline) to `road` (3 ways, which the derivation omits). MIN_MUTATIONS stays 25.
- 2026-10-16T07:31:00Z ACCEPTANCE written (front matter), before any code.
- 2026-10-16T07:37:31Z CORRECTION to the two entries above: their `07:31:00Z` stamps were typed, not read from
  `date -u`; both were written between 07:28:19Z and 07:30:50Z (`date -u` at the next run) and committed in
  9f9dbe74 before any code. Stamps below are read from `date -u`.
- 2026-10-16T07:30:50Z A2 RED FIRST. Tests edited (R5), module literals still the window's:
  `python -m pytest -q -o addopts= tests/test_surfacecoverage.py` -> `7 failed, 17 passed`, FAILED:
  test_the_check_is_green_over_the_measured_full_la_region, test_the_check_refuses_the_canyon_window_because_a_
  window_is_not_its_region, test_every_baseline_is_met_by_the_region_it_was_measured_from,
  test_baselines_are_exactly_the_measurement_times_the_ruled_margin, test_a_large_class_with_no_baseline_is_
  reported_by_name, test_a_class_exactly_at_its_baseline_passes, test_a_class_one_way_below_its_baseline_is_refused.
  New literals in: `1 failed, 23 passed` - test_a_class_with_no_baseline_is_never_refused_however_bare used
  living_street as its unbaselined class, which R3 now baselines; moved to `road` (3 ways region-wide, unbaselined).
  Then `24 passed in 6.03s` (Windows python); in the pinned image (`docker run ... scenic-etl python3 -m pytest
  -q -p no:cacheprovider -o addopts= tests/test_surfacecoverage.py`, 07:37Z) `24 passed in 2.69s`.
- 2026-10-16T07:31:46Z A4. `wsl -e python3 ops/lib/sane_corpus.py --corpus /home/phineas/t0242/la-corpus.sqlite`
  (SCENIC_REGION_WORK unset) at d164c4f3:
  ```
  ok	corpus-open	la-corpus.sqlite: schema_version 3, build_complete 1, region 'la'
  ok	corpus-terms	la-corpus.sqlite: 0 term rows, every value within 0..1
  ok	corpus-viewpoints	la-corpus.sqlite: 102 viewpoints >= region la's floor 76
  ok	corpus-surface	la-corpus.sqlite: 16 classes, none below its baseline
  skip	corpus-score	the corpus stores no score (schema.py rule 6): ...
  rc=0
  ```
  The canyon window through the same command: corpus-open/terms/viewpoints ok, then `FAIL corpus-surface
  la-corpus.sqlite: class living_street has only 4 ways ...; class primary_link has only 10 ways ...; class
  secondary_link has only 6 ways ...; class tertiary_link has only 8 ways ...; class trunk_link has only 14 ways
  ...; residential: surface coverage 0.1222 is below the baseline 0.164 (313 known of 2562 ways); secondary: 0.3827
  < 0.430 (106 of 277); service: 0.0393 < 0.065 (268 of 6818); tertiary: 0.2931 < 0.417 (119 of 406); track:
  0.0182 < 0.033 (18 of 988); trunk: 0.3267 < 0.533 (82 of 251); unclassified: 0.1383 < 0.241 (13 of 94)`, rc=4 -
  exactly R4's twelve.
- 2026-10-16T07:37:13Z A3 (finished before this stamp) at d164c4f3 (`python ops/mutate/surfacecoverage.py`): `BASELINE exit=0, 25 mutations,
  floor 25` ... `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2`, `MUTATE OK  caught=25/25 equivalent_caught=0`,
  rc=0. The four touched rows: residential -> 0.0 caught by test_the_check_refuses_residential_below_its_baseline_
  by_name; service -> 0.9 caught by test_the_check_is_green_over_the_measured_full_la_region; motorway -> 0.001
  caught by test_baselines_are_exactly_the_measurement_times_the_ruled_margin; `"road": 0.001` added caught by
  test_the_check_is_green_over_the_measured_full_la_region. `--prove-vacuity`: `VACUITY: 0 caught, 25 missed, 0
  skipped, of 25`, `VACUITY PROVED`, rc=0. (Run whole, R7: the driver has no --only.)
- 2026-10-16T07:37:13Z A5. `bash ops/lib/check-sane-corpus` -> `SANE-CORPUS ok       59/59 cases passed
  (sane=ops/sane)` rc=0. P-DATA-04's assertion, extracted from PINS.yaml by yaml.safe_load and run with bash
  (PYTHON=python) -> rc=0. `python ops/lib/check-pins-yaml.py` -> `PINS-YAML ok pins=51 fields=411`.
- 2026-10-16T07:40:09Z FINAL, ACCEPTANCE RE-QUOTED on 86621ac9 after `git fetch origin` (main checkout) and
  `git merge origin/main` -> `Already up to date.` (origin/main a137f16c, this branch's base). services/etl and
  ops/mutate are byte-identical to d164c4f3 (the later commits touch only pins/PINS.yaml and this file), so:
  A1 `24 passed` (Windows python 6.03s; pinned image 2.69s). A2 red 7/24 on the window literals, then 24/24 (above).
  A3 `MUTATE OK  caught=25/25 equivalent_caught=0`; `VACUITY PROVED` (0 caught, 25 missed). A4 full LA rc=0
  corpus-surface `16 classes, none below its baseline`; canyon window rc=4 naming the twelve. A5 check-sane-corpus
  `59/59 cases passed`; P-DATA-04 assertion rc=0. A6 on 86621ac9: check-sane-corpus rc=0 `59/59`;
  check-sane-exit-order rc=0 `documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=23`;
  check-mutate-population rc=0 `every added module is covered or allowlisted; the floor of 165 holds`;
  check-pins-yaml rc=0 `pins=51 fields=411`; queue-check rc=0 `QUEUE OK (365 tasks)`. A7 `wc -l`: 240
  services/etl/etl/surfacecoverage.py, 284 services/etl/tests/test_surfacecoverage.py, 248
  ops/mutate/surfacecoverage.py.
  OPEN (not this task): a second region's corpus is judged against LA's table until it has its own measured set
  (R1) - file when one is built; a box whose $SCENIC_REGION_WORK/la-corpus.sqlite is the canyon window now sees
  ops/sane exit 4 by design (R4).
- 2026-10-16T07:59:37Z REVIEW PASS by agent/rv1-t0374 (PR #256, head f091f897). Arithmetic: all 15 BASELINES
  == floor(quoted frac x 0.75, 3dp). Re-measured read-only (WSL python3, sqlite mode=ro) on the full LA corpus
  meta.surface_coverage: motorway 3217/7486 = 0.429736 -> 0.322; trunk_link 132/178 = 0.741573 -> 0.556;
  living_street 58/195 = 0.297436 -> 0.223; osm_features totals agree (7486, 178, 195); fixture rows match.
  Mutant trunk_link 0.556 -> 0.742 (just above 0.7416): pytest RED by name (green_over_full_la_region,
  every_baseline_is_met_by_the_region, baselines_are_exactly_the_measurement_times_the_ruled_margin,
  a_large_class_with_no_baseline_is_reported_by_name); check-sane-corpus stayed 59/59; restored byte-equal.
  A1 24 passed; A3 MUTATE OK caught=25/25 equivalent_caught=0; A4 full LA rc=0 `ok corpus-surface ... 16
  classes, none below its baseline`, window rc=4 naming the 12 R4 classes; A5 check-sane-corpus 59/59,
  P-DATA-04 assertion rc=0; A6 sane-exit-order, mutate-population, pins-yaml, queue-check (365) all rc=0;
  A7 240/284/248. gh pr checks: core pass, pins-source-only pass. merge-base --is-ancestor origin/main
  origin/task/T-0374 rc=0.
