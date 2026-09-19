---
id: T-0205
title: ETL - surface-coverage per class in meta (plan:283): the corpus manifest carries surface known/unknown/unpaved counts per highway class over the region clip, with the pytest and a pin; nothing writes it today
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T10:49:25Z
lease_expires_at: 2026-09-19T15:49:25Z
worktree: .worktrees/T-0205
branch: task/T-0205
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, pins/PINS.yaml, ops/mutate/, ops/lib/check-mutate-population.py]
pins_affected: []
reviewer: null
depends_on: [T-0168, T-0173]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the corpus meta (manifest.py / corpus.py - rule which owns it) carries, per highway class, the count of ways with a positive surface tag, with surface unknown (the three-state column T-0173 shipped), and gated unpaved; written by the assembly over the scored table - RED BY NAME first: a test that reads meta from a fixture corpus and asserts the per-class table, red until the writer exists; the ops/sane check-4 'surface-coverage per class >= baseline' clause becomes a number printed by a check that refuses below a literal baseline per class (the baseline recorded from the LA window's real counts, quoted)"
  - "a pin in pins/PINS.yaml (P-DATA-01's neighbour or its own id - rule it) whose assertion runs the check over the committed fixture; cd services/etl && python -m pytest tests -rs -o addopts= count line and zero skips"
---
## Brief

From the 01:13 panel (STRATEGY, grounded): plan:283's M2 exit names 'surface-coverage per class in meta' and
nothing in services/etl/etl/manifest.py, corpus.py or schema.py writes a coverage key - T-0024 is per-class
COUNTS, T-0173 is the three-state surface column. The plan's own rationale: the absent-surface rule (primary/
secondary/tertiary assumed paved, residential x0.8 with a surface_unknown flag) is only honest if the per-class
coverage is measured and watched.

## Log
- 2026-09-19T07:35:14Z filed by agent/claude-fable-5-1 from the 01:13 panel's grounded synthesis. Not started; after #111 merges.
- 2026-09-19T10:46:00Z PROMOTED to ready/ by agent/claude-fable-5-1 (03:13 panel, grounded): its dependencies (T-0168, T-0173) are in done/, no lock; an unmet M2 exit clause (plan:283); the fallback START while #113 holds the scenic-index lock.
- 2026-09-19T10:49:25Z claimed by agent/claude-opus-5; lease until 2026-09-19T15:49:25Z
- 2026-09-19T10:52:47Z MEASURED FIRST, before any predicate was written (CLAUDE.md's acceptance-predicate
  sentence). Population: the REAL scored LA canyon window, services/etl/work/la/window-doc.json in the main
  checkout, 11,740 ways, 15 highway classes. Per class, off the RAW `surface` tag: known = a positive tag that
  is not an unpaved value; unpaved = a positive tag in the plan:80 unpaved set (the gated ones); unknown = NO
  surface tag at all. The three partition the class, so known+unknown+unpaved == total.

        class              known unknown unpaved   total  known_frac
        service              268    6502      48    6818  0.0393
        residential          313    2229      20    2562  0.1222
        track                 18     870     100     988  0.0182
        tertiary             119     287       0     406  0.2931
        secondary            106     171       0     277  0.3827
        trunk                 82     169       0     251  0.3267
        primary               91      90       0     181  0.5028
        unclassified          13      79       2      94  0.1383
        motorway_link         31      42       0      73  0.4247
        motorway              38      10       0      48  0.7917
        trunk_link             3      11       0      14  0.2143
        primary_link           1       9       0      10  0.1000
        tertiary_link          2       6       0       8  0.2500
        secondary_link         0       6       0       6  0.0000
        living_street          0       4       0       4  0.0000
        TOTAL ways=11740 classes=15

  Measured with a throwaway under the gitignored services/etl/work/ (measure_surface.py); nothing of it is
  committed. Everything below is written against these numbers and not against a guess.
- 2026-09-19T10:55:10Z RULINGS, before code.
  R1 WHO OWNS THE WRITER. The computation is a NEW module, services/etl/etl/surfacecoverage.py: one function,
  `coverage(ways)`, over the ExtractWay rows the corpus is built from. The WRITE is `corpus.build` - the
  shipping entry point `python -m etl.corpus` runs - which calls `writer.set_meta(surfacecoverage.META_KEY,
  surfacecoverage.encode(surfacecoverage.coverage(ways)))` beside the other meta keys. The Brief's "the
  assembly over the scored table" is RULED AGAINST on two grounds and this is the disagreement CLAUDE.md's
  author rule wants ruled here: (a) the meta table is corpus.sqlite's and `assemble` writes a JSON table and
  no corpus at all; (b) `assemble.scored_row` DROPS the raw surface tag (assemble.py:217-219), so the scored
  table cannot answer the coverage question, while `ExtractWay.surface` (extractway.py:38) carries the raw
  OSM value. ONE COMPUTATION: the check below never recounts anything - it reads the table the writer wrote.
  R1b WHY NOT THE CORPUS `surface` COLUMN. `osm_features.surface` is the three-state column T-0173 shipped and
  it CANNOT answer this: surface.py's docstring says so in those words - an absent tag on primary/secondary/
  tertiary is PAVED(1), indistinguishable from `surface=asphalt`. Coverage is "was this road surveyed", so it
  is computed off the raw tag and the three buckets are the ones in the measurement above. A consequence worth
  stating: for motorway the column would claim 100% and the honest number is 79%.
  R2 THE KEY'S SHAPE AND SCHEMA_VERSION. One meta key, `surface_coverage`, one JSON value: an object keyed by
  highway class, each `{"known":n,"unknown":n,"unpaved":n,"total":n}`, sort_keys=True and compact separators so
  two builds of one extract agree byte for byte (P-DATA-01). SCHEMA_VERSION DOES NOT MOVE and stays 2:
  schema.py's rule 1 says adding a meta key must not be a DDL change, because a DDL change forces a version
  bump and invalidates every device's corpus over the air; no column, index or CHECK is added here. P-PROD-05
  (corpus == Worker) is therefore untouched, and check-schema-version.py stays green on 2 == 2. The key IS
  added to schema.REQUIRED_META_KEYS, which is not DDL either: it makes `CorpusWriter.finalize` refuse a corpus
  that forgot to write it, which is the integrity rule 1 says REQUIRED_META_KEYS exists to recover. It is NOT
  added to DIGEST_EXCLUDED_META: it is derived from the extract's own content, so it belongs in content_sha256.
  R3 THE BASELINE. `ops/sane` check 4's plan clause becomes `python -m etl.surfacecoverage`, which PRINTS the
  per-class known fraction as a number and exits 1 naming the class it refuses on. Literals, from the
  measurement above with a 25% margin: known_frac x 0.75, truncated to three decimals - service 0.029,
  residential 0.091, track 0.013, tertiary 0.219, secondary 0.287, trunk 0.245, primary 0.377, unclassified
  0.103, motorway_link 0.318, motorway 0.593. WHY 25%: the defect this watches is the pipeline losing the tag
  (tags-filter drops `surface`, an extract rebuilt against the retired `paved` key, a class relabelled), which
  sends a fraction to ~0 - an order of magnitude below any baseline here. What it must NOT fire on is ordinary
  OSM editing between rebuilds of the same region; a quarter of the measured coverage is far more headroom than
  mappers remove in a window that took years to reach these numbers. MINIMUM COUNT: 25 ways, and a class with
  fewer gets no baseline and is only printed. 25 because below it one way moves the fraction by over four
  points: the five classes under it here (trunk_link 14, primary_link 10, tertiary_link 8, secondary_link 6,
  living_street 4) have fractions of 0.21/0.10/0.25/0.00/0.00 that are noise, while unclassified at 94 and
  motorway at 48 are worth watching. The floor applies to the table being checked, so a class present with
  fewer than 25 ways is never refused on a fraction that cannot mean anything.
  R4 IT IS A NUMERIC MODULE. surfacecoverage.py computes fractions that GATE a run (exit 1), so CLAUDE.md's
  rule and P-PROC-06 both apply: it ships ops/mutate/surfacecoverage.py with a literal MIN_MUTATIONS floor in
  this PR, the scenic_tags.py shape, declared in SUBJECT_MODULES and registered in DRIVERS and COVERED_FLOOR.
  TOUCHES WIDENED, this line is the record: ops/mutate/ and ops/lib/check-mutate-population.py (DRIVERS +
  COVERED_FLOOR only) are added to the task's touches for R4. No allowlist entry is taken - allowlisting a
  module whose numbers refuse a build would be exactly the dishonest entry that file's header warns about.
- 2026-09-19T11:24:00Z RED FIRST, BY NAME, quoted as it landed. With the writer removed from `corpus.build`
  (`git stash push -- services/etl/etl/corpus.py`, schema.REQUIRED_META_KEYS already carrying the key),
  `cd services/etl && python -m pytest tests/test_surfacecoverage.py -o addopts= -q` gives
  `4 failed, 12 passed in 1.54s` with `RuntimeError: meta is missing required keys: surface_coverage` at
  corpuswriter.py:189, the four being test_corpus_meta_carries_the_surface_coverage_table_per_class,
  test_an_untagged_motorway_is_unknown_and_not_known, test_a_gravel_way_counts_as_unpaved_and_not_as_unknown
  and test_a_corpus_without_the_key_is_a_refusal_not_an_empty_verdict. The CHECK red by name on the committed
  below-baseline fixture: `SURFACE REFUSED residential: surface coverage 0.0234 is below the baseline 0.091
  (60 known of 2562 ways)`, exit 1; green over the committed real window table, `SURFACE classes=15
  refused=0`, exit 0. Stash popped; every test green.
- 2026-09-19T11:40:00Z ACCEPTANCE BLOCK, re-run bare at the final pre-review commit (the amend that carries
  this Log entry changes no file any of it measures; the only other change since the sweep is
  `git update-index --chmod=-x ops/mutate/surfacecoverage.py`, because ops/*.py is 100644 house style and
  P-OPS-01 said so by name).
  * the MEASUREMENT: the 15-class table above, unchanged; committed verbatim as
    services/etl/tests/fixtures/surface_coverage_la_window.json and read by the check and by
    test_every_baseline_is_met_by_the_window_it_was_measured_from.
  * the CHECK over the real window: `SURFACE service ... known_frac=0.0393 baseline 0.029` ...
    `SURFACE motorway ... known_frac=0.7917 baseline 0.593` ... `SURFACE classes=15 refused=0`, exit 0.
    Over the below-baseline fixture: exit 1, residential named. The pin assertion runs both, exit 0.
  * `cd services/etl && python -m pytest tests -rs -o addopts=` -> `1158 passed in 96.26s`, zero skips
    (test_surfacecoverage.py contributes 16).
  * `python ops/lib/check-mutate-population.py` -> `P-PROC-06: 72 modules, 23 covered by 11 populations,
    25 allowlisted, 0 added by this branch` / `every added module is covered or allowlisted; the floor of 23
    holds`, exit 0.
  * `python ops/mutate/surfacecoverage.py` -> `BASELINE exit=0, 18 mutations, floor 18` ...
    `MUTATIONS: 18 caught, 0 missed, 0 skipped, of 18` / `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2` /
    `MUTATE OK  caught=18/18 equivalent_caught=0`. `--prove-vacuity` -> `VACUITY: 0 caught, 18 missed,
    0 skipped, of 18` / `VACUITY PROVED`.
  * `bash ops/lib/check-line-cap` -> `P-SRC-02: 83 Swift files tracked ... none over 300 lines`, exit 0.
  * `bash ops/lib/check-exec-bits` -> `P-OPS-01: 77 files, 23 required present, all modes correct`, exit 0
    (run bare, not through a pipe).
  * `bash ops/queue-check` -> `QUEUE OK (205 tasks)`, exit 0.
  * `bash ops/check-pins --source-only` -> quoted in the PR body.
  * `wc -l` on every touched file: surfacecoverage.py 185, tests/test_surfacecoverage.py 162,
    ops/mutate/surfacecoverage.py 226, corpus.py 174, schema.py 270, check-mutate-population.py 294,
    pins/PINS.yaml 278. All under the 300 cap.
  STILL OPEN, for the reviewer: (i) the baselines are one window's; T-0204's Westwood window and T-0209's LA
  graph will give a second population, and the honest move then is to re-measure and take the LOWER of the two
  per class rather than to widen the margin; (ii) `ops/sane` itself is not edited here - the plan's check-4
  clause is now a runnable check with a pin, and wiring it into `ops/sane`'s exit-code ladder belongs with
  the sane-check work (its serial file and its exit-order test), not in an ETL PR.
- 2026-09-19T11:31:11Z RULINGS on the pre-review mutant pass's four survivors and the orchestrator's pin-id
  collision, written BEFORE the code that closes them. All five close in one commit.
  S0 THE PIN ID IS TAKEN, and this is a CORRECTION to the 2026-09-19T11:40:00Z entry above and to every
  earlier line that says P-DATA-03 (those entries are dated and stay as written): P-DATA-03 is the plan's
  "PMTiles/corpus meta.region == active region, built_at < 30 d" - services/tiles/check_pmtiles.py,
  tile_meta.py and services/tiles/README.md have used that id by name since T-0165, and queue task T-0197 is
  filed to ENTER it in pins/PINS.yaml. This task's pin is renamed to P-DATA-04, which is free: the only
  P-DATA ids on origin/main are P-DATA-01 and P-DATA-02, and a scan of every origin ref's pins/PINS.yaml
  (`git grep "id: P-DATA-0" <ref> -- pins/PINS.yaml` over all 60 remote heads, including the open PRs 113,
  115, 116) returns P-DATA-02 as the highest. The rename touches pins/PINS.yaml only: no source file, test
  or assertion here ever spelled the id.
  S1 THE --corpus PATH WAS BOUND BY NOTHING. `python -m etl.surfacecoverage --corpus <collapsed corpus>`
  exited 0 with 16 tests passing, because every check test went through `--table`; the mutant
  `bad = refusals(table) if args.table else []` survived. The path that a build actually runs was the one
  path no test ran. FIX: a test that builds a REAL corpus with `corpus.build` - the shipping entry point,
  not a helper - from an extract carrying all ten baseline classes, and runs the module as a SUBPROCESS
  (`sys.executable -m etl.surfacecoverage --corpus <file>`), asserting exit 1 and the class named on stderr
  for a below-baseline residential and exit 0 for an above-baseline one. Subprocess, not `main(argv)`, so
  the `__main__` block's `sys.exit(main())` is covered too. The extract is GENERATED in the test rather than
  committed: 250-plus ways of real geometry through `load_extract` and the segmenter is a real corpus either
  way, and two 40 KB blobs of synthetic JSON in tests/fixtures/ would be data nobody can check by eye.
  S2 NOTHING BOUND BASELINES TO THE MEASUREMENT. `"motorway": 0.593` -> `0.001` passed: the only test over
  the literals asserted `baseline > 0.0` and `fraction >= baseline`, which any small number satisfies. FIX:
  test_baselines_are_exactly_the_measurement_times_the_ruled_margin recomputes the whole dict from the
  committed measurement fixture with R3's rule - known/total x 0.75 truncated to three decimals, for every
  class with total >= MIN_CLASS_WAYS - and asserts `BASELINES == recomputed`, key set included. The margin
  and the floor are read from the module, so the test cannot drift from the rule it enforces; the NUMBERS
  come only from the fixture.
  S3 THE CHECK WAS GREEN OVER A TABLE WHERE NOTHING WAS JUDGED. On pristine code `{}` exited 0, a table with
  every class relabelled `road_<cls>` exited 0, and a table of nothing but tiny classes exited 0 - because
  `refusals` only ever looked at classes that were present AND large AND in BASELINES. A check whose verdict
  is "nothing to say" must not print a pass. FIX: a WHITELIST, `required_missing`: every key of BASELINES
  must be present in the table with `total >= MIN_CLASS_WAYS`, or the check refuses BY NAME - "class
  residential is missing from the table" / "class motorway has only 9 ways, under MIN_CLASS_WAYS=25". It is
  a whitelist over the identifiers the baselines already name, never a blacklist of shapes a bad table might
  take (CLAUDE.md). A class the table carries that no baseline names is REPORTED, not refused:
  `SURFACE UNKNOWN CLASS <cls>` on stderr for any such class at or over MIN_CLASS_WAYS, because an unknown
  large class is either a relabel upstream or a new OSM class worth a measured baseline, and both want a
  human, while `living_street` at 4 ways is neither.
  WHAT A GENUINELY SMALL REGION DOES: IT IS REFUSED, and there is no flag. Ruled against a
  `--allow-missing-classes` escape on the ground that a flag which turns a refusal into a pass is the exact
  move the 25% margin and MIN_CLASS_WAYS exist to make unnecessary, and the first build that trips it will
  be run with the flag rather than fixed. The baselines are ONE region's measurement (the STILL OPEN note
  above says so); a region with no motorway or under 25 residential ways is not a region these numbers can
  speak about, and the honest recourse is to measure that region and ship its own baseline set under its own
  ruling - not to let it pass unmeasured. The refusal says which classes and how many ways, so the operator
  is told exactly that.
  S4 THE BOUNDARY, `<` vs `<=`. RULED: a class whose fraction is EXACTLY its baseline PASSES. The comparison
  stays `fraction < baseline`. The baseline is a floor, and a floor is a value that is allowed; the margin
  is already 25%, so nothing real sits on the boundary, and the rule that reads the way it is written -
  "below the baseline is refused" - is the one a reader will assume. Asserted both ways:
  test_a_class_exactly_at_its_baseline_passes (91 known of 1000 residential ways, 0.091 exactly) and
  test_a_class_one_way_below_its_baseline_is_refused (90 of 1000).
  EVERY new rule gets its mutant: `bad = refusals(table) if args.table else []` (S1), motorway 0.593 ->
  0.001 and an extra BASELINES key (S2), `required_missing` returning [] and its MIN_CLASS_WAYS arm dropped
  and the unknown-class report silenced (S3), `fraction <= baseline` (S4). MIN_MUTATIONS rises 18 -> 25.
  KNOWN_MISSED stays [] and stays a true claim.
- 2026-09-19T11:31:11Z ACCEPTANCE BLOCK, re-run BARE at the final pre-review commit of the hardening (the
  amend that carries this entry changes only this task file, which nothing below measures except its own
  `wc -l`, given after it). The earlier acceptance block at 11:40:00Z stands as it was run; this one
  supersedes it.
  * the CHECK, `--table`, over the committed real measurement: `SURFACE classes=15 refused=0`, exit 0, with
    `SURFACE secondary_link ... no baseline (class is not in BASELINES)` and `SURFACE living_street ...
    no baseline (class is not in BASELINES)` printed and neither refused nor reported (both under
    MIN_CLASS_WAYS). Over the committed below-baseline table: exit 1, `SURFACE REFUSED residential: surface
    coverage 0.0234 is below the baseline 0.091 (60 known of 2562 ways)`.
  * the CHECK, `--corpus`, over a corpus `python -m etl.corpus` really built from the committed seven-way
    extract (`CORPUS region=fixture ways=7 segments=79 collisions=0`): exit 1, `SURFACE classes=5 refused=10`,
    naming each one - `SURFACE REFUSED class motorway has only 1 ways, under MIN_CLASS_WAYS=25 - too few to
    judge`, `SURFACE REFUSED class motorway_link is missing from the table - every baselined class must be
    measured`, and the same for primary, residential, secondary, service, tertiary, track, trunk,
    unclassified. On pristine code before this commit that corpus exited 0 (S3). Over the two corpora the
    tests build from a ten-class extract (250 ways): the collapsed one exits 1 naming residential below its
    baseline, the covered one exits 0 with `refused=0`.
  * P-DATA-04's assertion, run bare as check-pins runs it (both `--table` fixtures and a corpus built in a
    mktemp dir): exit 0.
  * `cd services/etl && python -m pytest tests -rs -o addopts=` -> `1165 passed in 75.86s`, zero skips
    (test_surfacecoverage.py contributes 23, up from 16).
  * `python ops/mutate/surfacecoverage.py` -> `BASELINE exit=0, 25 mutations, floor 25` /
    `MUTATIONS: 25 caught, 0 missed, 0 skipped, of 25` / `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2` /
    `MUTATE OK  caught=25/25 equivalent_caught=0`. `--prove-vacuity` -> `VACUITY: 0 caught, 25 missed,
    0 skipped, of 25` / `VACUITY PROVED`. KNOWN_MISSED is still [] and still a true claim.
  * `python ops/lib/check-mutate-population.py` -> `P-PROC-06: 72 modules, 23 covered by 11 populations,
    25 allowlisted, 1 added by this branch` / `every added module is covered or allowlisted; the floor of 23
    holds`, exit 0. (The "1 added" is surfacecoverage.py itself, covered.)
  * `bash ops/lib/check-line-cap` -> `P-SRC-02: 83 Swift files tracked ... none over 300 lines`, exit 0.
  * `bash ops/lib/check-exec-bits` -> `P-OPS-01: 77 files, 23 required present, all modes correct`, exit 0.
  * `bash ops/queue-check` -> `QUEUE OK (205 tasks)`, exit 0.
  * `bash ops/check-pins --source-only` -> quoted in the PR body.
  * `wc -l` on every file this commit touches: services/etl/etl/surfacecoverage.py 231,
    services/etl/tests/test_surfacecoverage.py 267, ops/mutate/surfacecoverage.py 246, pins/PINS.yaml 278,
    and this task file 242 after this entry. All under the 300 cap; ops/lib/check-mutate-population.py is
    unchanged at 294 (the registration it needed landed in the first commit).
  STILL OPEN, for the reviewer: (i) and (ii) from the 11:40:00Z block stand unchanged - one window's
  baselines, and `ops/sane`'s check-4 wiring belongs with the sane-check work; (iii) NEW: the required-class
  whitelist makes this check a statement about a FULL region build, so the first small-region build will be
  refused by name and will want its own measured baseline set under its own ruling - that is the ruled
  behaviour (S3), not an oversight, and the refusal says which classes and how many ways.
- 2026-09-19T11:55:27Z P-OPS-03 CAUGHT THE NEW ASSERTION, and this is the record. The first spelling of
  P-DATA-04's added `--corpus` clause ended `... --corpus "$T/c.sqlite" 2>&1 >/dev/null | grep -q 'SURFACE
  REFUSED class residential'`, which passed when run by hand and FAILED under `ops/check-pins --source-only`:
  `ops/lib/check-pipe-consumers` names it by file and line, because a gate that decides with
  `producer | grep -q` throws the producer's exit status away and reports the grep's. Rewritten with no pipe
  at all: the check's stderr goes to `"$T/err"`, the refusal itself is asserted as `! "$P" -m
  etl.surfacecoverage --corpus ...` (exit non-zero REQUIRED), and `grep -q ... "$T/err"` then reads a file.
  Re-run bare: the assertion exits 0, and `bash ops/lib/check-pipe-consumers` -> `PIPE-CONSUMERS OK: no gate
  decides with 'producer | grep -q' (77 scanned, 78 tracked, floor 42)`, exit 0. Nothing else in the
  acceptance block above is affected - pins/PINS.yaml is the only file this correction touches, and it is not
  a file any measurement there ranges over except its own `wc -l`, re-measured here: pins/PINS.yaml 278 and
  this task file 254 at the final commit. Every other number in the 11:31:11Z block stands as run.
