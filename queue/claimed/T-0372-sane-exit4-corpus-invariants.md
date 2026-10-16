---
id: T-0372
title: ops/sane exit 4 checks the corpus invariants it can see without the graph - no motorway/trunk/private/unpaved way scores above 0, no NULL scores, viewpoints >= the measured floor, surface coverage per class >= baseline - over a corpus.sqlite, local fixture first
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T04:52:58Z
lease_expires_at: 2026-10-17T04:52:58Z
worktree: .worktrees/T-0372
branch: task/T-0372
exclusive: []
touches: [ops/sane, ops/lib/, ops/mutate/sane_corpus.py, services/etl/tests/, pins/PINS.yaml, queue/claimed/T-0372-sane-exit4-corpus-invariants.md, queue/backlog/T-0374-surface-baselines-full-la.md]
pins_affected: [P-OPS-08, P-PROD-04]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "A1 MEASURED: the Log quotes both LA corpora's schema_version, way/segment/place counts, viewpoint count, terms_osm/terms_raster row counts and surface_coverage verdict, read read-only"
  - "A2 bash ops/lib/check-sane-corpus prints SANE-CORPUS ok N/N: the clean fixture is green (exit 0, every corpus-* row ok, corpus-score skip) and every predicate has a red row by name through the SHIPPED ops/sane (exit 4, exactly that FAIL row); bounds rows: viewpoints at the floor ok and floor-1 FAIL; term values 0.0 and 1.0 ok, nextafter(0,-1), nextafter(1,2), +inf, -inf FAIL, each in terms_osm AND terms_raster; a meta-check refuses unless every sane_corpus.PREDICATES name has a red row"
  - "A3 seen RED: the table against main's ops/sane (corpus rows absent) fails by case name; python ops/mutate/sane_corpus.py kills every mutant of ops/lib/sane_corpus.py by case name with a literal FLOOR"
  - "A4 bash ops/lib/check-sane-exit-order green with EXIT_ORDER unchanged (2 7 3 6 9 8 4 10); bash ops/lib/check-sane-prod --only on a sample of rows green (SANE_SCOPE=prod, no SANE_CORPUS: corpus row is skip)"
  - "A5 the FULL LA corpus (T-0275, /home/phineas/t0242/la-corpus.sqlite in WSL) through python3 ops/lib/sane_corpus.py --corpus: exit and rows quoted as measured (expected: corpus-surface FAIL on motorway + motorway_link, viewpoints 102 >= 76 ok, terms 0 rows ok)"
  - "A6 gates bare: check-pins-yaml, check-exec-bits, queue-check, check-mutate-population; wc -l of every touched file <= 300; pin P-OPS-09 added (quoted per pins-yaml-strict)"
  - "A7 (round 2, rv1-t0372) bash ops/lib/check-sane-corpus holds d-store-two-second-red and d-store-two-first-red (two <region>-corpus.sqlite files in the store, one status per discovered corpus) and l-local-store-red and l-local-store-clean (the SHIPPED ops/sane in its default scope, SANE_CORPUS unset, SCENIC_REGION_WORK set); python ops/mutate/sane_corpus.py --only 27,28,29 kills paths[:1], paths[1:] and the default-scope mutant by those row names; MIN_MUTATIONS 29; T-0374 filed for the full-LA surface baselines"
---
## Brief

Milestone survey 2026-10-10: `ops/sane` exit 4 checks only the region meta.json counts (ops/sane ~L121-137); the
plan's exit 4 also asks for "no NULL scores; no motorway/trunk/private/unpaved way with score > 0; viewpoints >= 400;
surface-coverage per class >= baseline". The graph-hash half needs the R2 graph (T-0008, owner-gated); the
corpus-only invariants are buildable now against a corpus.sqlite.

MEASURE FIRST: the corpus.sqlite schema (tables/columns for ways, scores, highway class, access, surface, viewpoints,
meta surface coverage) from services/etl, and the LA corpus's actual counts if a built corpus is on disk (quote them;
a predicate over a population nobody measured is a measurement task, CLAUDE.md). RULE each predicate and its literal
threshold from the measurement (viewpoints >= 400 is the plan's Bay Area number - LA's may differ), where the corpus
path comes from (ops/sane is read-only, never mutates), and the skip line when no corpus is present. Then: the checks
in a sane_corpus module (300-line cap), a fixture corpus per predicate side (a violating row per predicate, red by
name; a clean fixture green), exit 4 ordering unchanged (check-sane-exit-order), cases in the sane test table.

## Log
- 2026-10-16T02:30:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (ids checked
  on main and task/T-0361, task/T-0365: highest T-0371).
- 2026-10-16T04:52:58Z claimed by agent/claude-opus-5; lease until 2026-10-17T04:52:58Z
- 2026-10-16T05:05:27Z MEASURED (agent/claude-opus-5), read-only, sqlite3 mode=ro, script services/etl/work/t0372/measure.py
  (gitignored scratch):
  - SCHEMA (services/etl/etl/schema.py, SCHEMA_VERSION 3): NO score column and no score view - rule 6 ("Score is computed
    from terms_* at query time"); osm_features(way_id, cls, highway, surface IN (-1,0,1), access_ok IN (0,1), ...);
    terms_osm / terms_raster(segment_id, term_id, value REAL NOT NULL CHECK (value = value)); places(cls, ...);
    meta key surface_coverage (etl/surfacecoverage.py, BASELINES from T-0205's canyon window x 0.75).
  - CANYON WINDOW services/etl/work/t0266/la-corpus.sqlite (built 2026-10-05, schema 3, region la): osm_features 11740,
    segments 24205, places 4773 (viewpoint 102), terms_osm 0, terms_raster 0, surface verdict [] (the window the
    baselines were measured on).
  - FULL LA (T-0275's /home/phineas/t0242/la-corpus.sqlite in WSL, built 2026-10-06, schema 3, region la, python3 in
    WSL, no git): osm_features 560208, segments 874391, places 4773 (viewpoint 102), terms_osm 0, terms_raster 0,
    surface verdict ['motorway: surface coverage 0.4297 is below the baseline 0.593 (3217 known of 7486 ways)',
    'motorway_link: surface coverage 0.1905 is below the baseline 0.318 (1887 known of 9908 ways)'].
  - OLDER services/etl/work/t0206/la-union-corpus.sqlite: schema 2, places 0 - not the current schema, not used.
  - region.json la counts viewpoint 302 is the EXTRACT's tag count (meta.json, checked by exit 4 "bounds"); the
    corpus keeps 102 of them as places (T-0275's PLACES line: unnamed=5906 refused_access=48 dropped).
- 2026-10-16T05:05:27Z RULINGS (agent/claude-opus-5), before code:
  - R1 SCORE PREDICATES ARE NOT CORPUS PROPERTIES. "no NULL scores" and "no motorway/trunk/private/unpaved way scores
    above 0" range over a score the corpus does not store (schema rule 6) and over terms that are 0 rows in both
    measured LA corpora. The zero classes and the gates are P-PROD-01's (score.SCENIC_ZERO_CLASSES, the router profile,
    ScenicKit.Gates); the 0..10 scenic_score is the graph's (T-0008, owner-gated). ops/sane prints a `corpus-score`
    SKIP row naming this; no number is invented.
  - R2 THE CORPUS-VISIBLE HALF OF "no NULL scores" IS checked: score.score returns None when any unit term is outside
    0..1 or not finite (score.out_of_range), so `corpus-terms` FAILS on any terms_osm or terms_raster row with value
    < 0 or > 1 (inf included; NaN is NULL in sqlite and the schema's NOT NULL refuses it). Bounds 0.0 and 1.0 are
    allowed. Over the measured LA corpora it ranges over 0 rows and the ok row SAYS "0 term rows".
  - R3 VIEWPOINTS: the plan's 400 is the Bay Area's; LA's measured corpus count is 102 (both LA corpora). Floor =
    int(102 * 0.75) = 76, T-0205 R3's margin rule; the defect watched is the pipeline losing places (-> ~0).
    VIEWPOINT_FLOORS = {"la": 76} keyed by meta.region; a region with no measured floor is REFUSED by name (whitelist,
    as surfacecoverage S3) - sfbay gets no invented number. Exactly the floor passes.
  - R4 SURFACE COVERAGE: reuse surfacecoverage.decode + verdict over meta.surface_coverage (one definition; never
    recount). Absent key / malformed table FAIL. The FULL LA corpus is RED here (motorway, motorway_link) - a real
    finding about window-measured baselines; changing BASELINES is not this task's (services/etl/etl untouched) and is
    reported for a follow-up task.
  - R5 CANNOT-TELL IS 4: `corpus-open` FAILS on a missing/unreadable file, no meta, schema_version != schema.py's
    SCHEMA_VERSION, or build_complete != "1". Opened with sqlite mode=ro URI: ops/sane never mutates.
  - R6 CORPUS PATH: SANE_CORPUS (one path, checked under ANY SANE_SCOPE - the test table's handle), else
    $SCENIC_REGION_WORK/<region>-corpus.sqlite for each services/etl/regions/<region>/ (ops/etl-region's output),
    else ONE skip row "no corpus built here". services/etl/work/ is NOT scanned: it holds per-task scratch and
    deliberate mutants (t0270/rv1-mutant-la.sqlite).
  - R7 PLACEMENT: a new block after "bounds" and before "worktrees", fail() code 4, so EXIT_ORDER (2 7 3 6 9 8 4 10)
    and check-sane-exit-order are unchanged.
  - R8 PINS: P-PROD-04 does not exist in PINS.yaml (it is the planned graph-hash three-way pin, T-0209's Log) - not
    created. P-OPS-08 is --prod against the fake Worker and does not change. New pin P-OPS-09 (no collision on main or
    any origin branch, checked 05:02Z) asserts `bash ops/lib/check-sane-corpus`.
  - R9 MUTATION: ops/lib is not a MODULE_ROOT of check-mutate-population, but sane_corpus.py is numeric (floor, bounds),
    so it ships ops/mutate/sane_corpus.py with SUBJECT_MODULES and a literal FLOOR; each mutant must turn
    check-sane-corpus red by case name.
  - R10 TABLE: a new table ops/lib/check-sane-corpus (+ check_sane_corpus.py), not rows in check-sane-prod: that table
    runs --prod against a fake Worker; these rows run SANE_SCOPE=prod SANE_CORPUS=<fixture> bash ops/sane (no --prod),
    so only the corpus block decides the exit. Fixtures are built per case in a temp dir by schema.apply_schema plus
    inserts - no binary fixture is committed.
- 2026-10-16T05:27:10Z BUILT (agent/claude-opus-5): ops/lib/sane_corpus.py (175 lines), its block in ops/sane after
  "bounds" (fail() code 4), ops/lib/check-sane-corpus (100755) + check_sane_corpus.py + sane_corpus_cases.py,
  ops/mutate/sane_corpus.py (PROBES entry in ops/lib/mutate_population_table.py), pin P-OPS-09.
  - A5 FULL LA (WSL python3 3.12.3, read-only, no git): `python3 ops/lib/sane_corpus.py --corpus
    /home/phineas/t0242/la-corpus.sqlite` -> rc=4: `ok corpus-open schema_version 3, build_complete 1, region 'la'`,
    `ok corpus-terms 0 term rows, every value within 0..1`, `ok corpus-viewpoints 102 viewpoints >= region la's floor 76`,
    `FAIL corpus-surface motorway: surface coverage 0.4297 is below the baseline 0.593 (3217 known of 7486 ways);
    motorway_link: surface coverage 0.1905 is below the baseline 0.318 (1887 known of 9908 ways)`, `skip corpus-score`.
    Canyon window (t0266) through the shipped ops/sane with SANE_SCOPE=prod SANE_CORPUS=...: all four ok, SANE OK.
  - A3 RED FIRST: `bash ops/lib/check-sane-corpus --sane <main's ops/sane>` -> `SANE-CORPUS FAIL 47 of 53 cases failed`
    (e.g. `clean-on-every-bound: row corpus-open None, want [ok]`; `p-prod-scope: row corpus-db None, want [skip]`;
    the 6 d- rows run sane_corpus.py directly and pass). Green on this branch: `SANE-CORPUS ok 53/53`, then 56/56 with
    the p-python-false / p-python-echo rows.
  - A3 MUTANTS: `python ops/mutate/sane_corpus.py` -> 25 killed by case name, #9 SURVIVED: it widened the range to
    +-1e308 and named the inf rows as killers, but 2.0 rows are what kill a widening and the infinities stay outside
    1e308 - a duplicate of #7, not an inf mutant. Replaced by `... AND abs(value) < 1e308` (infinities exempted):
    `MUTATE killed #9 ... by terms-terms_osm-plus-inf, terms-terms_raster-minus-inf`, `MUTATE ok 1/1` (faster-verification:
    only the touched mutant re-run). Population 26, MIN_MUTATIONS 26.
  - A4/A6 gates: `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=23`; `SANE-PROD ok 3/3`
    (--only q-kill,m-schema-other,x-version-string); `PINS-YAML ok pins=51 fields=411`; `P-OPS-01: 230 files, 23 required
    present, all modes correct`; `P-PROC-06: ... every added module is covered or allowlisted; the floor of 165 holds`;
    `QUEUE OK (360 tasks)`.
  - FOLLOW-UP (not this task's): surfacecoverage.BASELINES were measured on the canyon window (T-0205) and the FULL LA
    corpus is below them on motorway and motorway_link; re-measure over the full region before a full corpus is put
    where ops/sane finds it, or exit 4 will be red - correctly, by what the baselines say today.
- 2026-10-16T05:29:41Z CORRECTION (agent/claude-opus-5): the table is 55 rows, not 56 - 46 s- rows, 6 d- rows, 3 p- rows; "53/53" above
  was before p-python-false and p-python-echo were added (46 + 6 + p-prod-scope). Re-run on the merged head (origin/main
  aa1b1b22, merge a no-op): `SANE-CORPUS ok 55/55 cases passed`; exit-order, PINS-YAML (pins=51 fields=411), P-OPS-01,
  QUEUE OK (360 tasks), P-PROC-06 floor 165 all green; wc -l ops/sane 212, sane_corpus.py 175, sane_corpus_cases.py 141,
  check_sane_corpus.py 182, check-sane-corpus 8, ops/mutate/sane_corpus.py 151, mutate_population_table.py 114.
  P-OPS-09 text corrected to 46 / 55.
- 2026-10-16T05:52:18Z ROUND 2 RULINGS (agent/claude-opus-5), rv1-t0372 FAIL on PR #253 head 3dbd201a, before code:
  - B1 (M2 `paths[:1]` in sane_corpus.main survives 55/55): no d- row put two <region>-corpus.sqlite files in the store;
    d-store-wrong-name's corpus.sqlite / sfbay.sqlite are names discover() never returns. RULING: the d- rows over a
    TWO-region store become rows as functions of input - each store file carries the predicate it breaks (or None)
    and the row's wanted output is derived from that list in discovery order (la, sfbay): d-store-two-second-red
    (la clean, sfbay region sfbay with 0 viewpoints -> exit 4, corpus-viewpoints [ok, FAIL]) and
    d-store-two-first-red (la below the floor, sfbay-corpus.sqlite carrying region la and the clean fixture -> exit 4,
    corpus-viewpoints [FAIL, ok]); the second kills `paths[1:]` / `paths[-1:]` the way the first kills `paths[:1]`.
    compare() takes a list of statuses per row (one per discovered corpus) so the row counts the corpora checked.
  - B2 (M1 `if [[ -z "${SANE_CORPUS:-}" ]]` in ops/sane survives): every s-/p- row sets SANE_SCOPE=prod and the d- rows
    call the helper, so nothing ran the SHIPPED ops/sane in its default local scope with SANE_CORPUS unset. RULING: two
    l- rows run `bash ops/sane` with neither SANE_SCOPE nor SANE_CORPUS and SCENIC_REGION_WORK=<store holding
    la-corpus.sqlite>, over {red (FLOOR_LA - 1 viewpoints), clean}: the corpus-* rows must equal want(broken) exactly
    (no corpus-db row), and the exit must be the FIRST code of the typed EXIT_ORDER (2 7 3 6 9 8 4 10, pinned equal to
    ops/sane's by P-OPS-05) among the blocks that FAILed - local scope runs repo/crlf/autocrlf/gitattrs (2), bounds (4),
    the corpus rows (4) and worktrees (10, red on this box today: 3 of 98), so the red row is 4 unless a repo row is red
    and the clean row is whatever the other blocks say; a FAIL row of no known block refuses. Measured: a local-scope
    ops/sane takes 17 s here (rc=10, worktrees), so two l- rows cost ~35 s.
  - Population: M1 and M2 join ops/mutate/sane_corpus.py (26 -> 28) with their new killer rows; MIN_MUTATIONS 26 -> 28.
    Faster-verification: only the new rows, the two new mutants and the existing #22/#26 neighbours re-run, plus the
    whole table once (it is the gate).
  - FILED (recordable): surfacecoverage.BASELINES re-measure over the FULL LA corpus, as its own task (id = next free
    after main and every open task/* branch).
- 2026-10-16T06:05:00Z ROUND 2 RESULTS (agent/claude-opus-5):
  - New rows green on the pristine subjects: `SANE-CORPUS ok 4/4 cases passed` (--only d-store-two-second-red,
    d-store-two-first-red, l-local-store-red, l-local-store-clean).
  - SEEN RED by the new row names (ops/mutate/sane_corpus.py --only 20,21,22,26,27,28,29, faster-verification):
    `MUTATE killed #27 ops/lib/sane_corpus.py: 'rows = [r for path in paths[:1] for r in check(path)]' by
    d-store-two-second-red` (B1/M2); `MUTATE killed #28 ... paths[1:] ... by d-store-two-first-red`; `MUTATE killed
    #29 ops/sane: 'if [[ -z "${SANE_CORPUS:-}" ]]' by l-local-store-red, l-local-store-clean` (B2/M1); neighbours #20,
    #21, #22, #26 still killed; `MUTATE ok 7/7 killed (floor 29, population 29)`. Population 26 -> 29, MIN_MUTATIONS 29.
  - T-0374 filed in queue/backlog/ (ids checked on origin/main, every open PR head and every origin/task/* branch:
    highest T-0373; `T-0374 free` gated); its path added to this task's touches:.
  - Gates on the merged head (git fetch origin in the main checkout; origin/main aa1b1b22; merge `Already up to date`,
    HEAD 24fdb982), run bare: `SANE-CORPUS ok 59/59 cases passed (sane=ops/sane)` (46 s-, 8 d-, 3 p-, 2 l-);
    `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=23`; `P-PROC-06: every added module is
    covered or allowlisted; the floor of 165 holds`; `PINS-YAML ok pins=51 fields=411`; `P-OPS-01: 230 files, 23
    required present, all modes correct`; `QUEUE OK (361 tasks)`. wc -l: check_sane_corpus.py 260,
    ops/mutate/sane_corpus.py 157, sane_corpus.py 175, ops/sane 212, sane_corpus_cases.py 141, T-0374 file 33.
  - CORRECTION before push: P-OPS-09's round-2 sentence first said 61 rows; the table printed 59/59 - corrected to 59.
