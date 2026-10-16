---
id: T-0374
title: Re-measure surfacecoverage.BASELINES over the FULL LA corpus - the canyon-window baselines put motorway and motorway_link red on full LA
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T07:25:12Z
lease_expires_at: 2026-10-17T07:25:12Z
worktree: .worktrees/T-0374
branch: task/T-0374
exclusive: []
touches: [services/etl/etl/surfacecoverage.py, services/etl/tests/, ops/lib/, ops/mutate/, pins/PINS.yaml, queue/]
pins_affected: [P-OPS-09, P-DATA-04]
reviewer: null
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
