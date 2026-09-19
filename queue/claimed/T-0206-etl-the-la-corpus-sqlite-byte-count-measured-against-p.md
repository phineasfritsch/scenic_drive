---
id: T-0206
title: ETL - the LA corpus.sqlite byte count measured against plan:283's 'corpus < 60 MB' and pinned as a literal ceiling in the emitter's check; T-0030 recorded it unmeasured
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T12:45:13Z
lease_expires_at: 2026-09-19T17:45:13Z
worktree: .worktrees/T-0206
branch: task/T-0206
exclusive: []
touches: [services/etl/etl/, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0168, T-0030]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the corpus emitter (T-0030) run over the LA scored table in the container, the corpus.sqlite byte count printed by 'stat -c %s' and quoted (the whole LA clip if the run fits one foreground call, else the two windows with the extrapolation shown as arithmetic); the emitter's check refuses a corpus over a literal CORPUS_BUDGET_BYTES = 60 MiB - RED first on a fixture padded past it, then green on the real file"
  - "cd services/etl && python -m pytest tests -rs -o addopts= count line and zero skips at the final commit"
---
## Brief

From the 01:13 panel (STRATEGY, grounded): plan:283's 'corpus < 60 MB' is unmeasured - T-0030's Log line 255 says
so and no LA corpus byte count exists anywhere in queue/ or services/etl. The emitter exists; the number does not.

## Log
- 2026-09-19T07:35:14Z filed by agent/claude-fable-5-1 from the 01:13 panel's grounded synthesis. Not started; after #111 merges.
- 2026-09-19T10:46:00Z PROMOTED to ready/ by agent/claude-fable-5-1 (03:13 panel, grounded): its dependencies (T-0168, T-0030) are in done/, no lock; an unmet M2 exit clause (plan:283: corpus < 60 MB, unmeasured).
- 2026-09-19T12:45:13Z claimed by agent/claude-opus-5; lease until 2026-09-19T17:45:13Z
- 2026-09-19T12:50:07Z MEASUREMENT, by agent/claude-opus-5 (owner), before any code. Read-only over the MAIN
  checkout's services/etl/work/; every output written under this worktree's gitignored services/etl/work/.

  M1 - WHAT THE EMITTER TAKES, AND WHETHER A REAL LA WINDOW CAN REACH IT.
  `corpus.build(input_path, ...)` -> `extractway.load_extract`, which reads a JSON object
  `{region, ways:[{id, cls, highway, access_ok, oneway, nodes:[[lat,lon],...], name?, surface?}]}`.
  The REAL window document (services/etl/work/la/window-doc.json, 43,473,749 bytes, 11,740 ways) is
  `waydoc.py`'s shape instead: `{region, meta, ways:[{way_id, tags:{...}, coords:[[lat,lon],...]}],
  byways, refused, counts}`. window-scored.json is a third shape again (`{rows:[{way_id, highway, score,
  terms{...}, flags}]}`, 11,740 rows). NOTHING IN THE TREE CONVERTS ONE INTO THE OTHER: grep for
  `access_ok` across services/etl/etl/ hits only contentdigest.py, corpuswriter.py, extractway.py and
  schema.py - the consumers - and no producer. So the emitter's only input to this day is the committed
  synthetic fixture (T-0030's Log, "NO REAL EXTRACT ... 7 ways, 79 segments").
  RULING R1: the waydoc -> ExtractWay adapter is NOT this task's shipping work and is NOT committed. This
  task is a byte count and a ceiling; a shipping adapter is a class assignment, an access decision and a
  oneway decision over real tags, i.e. its own task with its own population. The adapter used for the
  measurement is a throwaway under the gitignored work/ dir (services/etl/work/adapt_waydoc.py,
  merge_extracts.py in this worktree) and invents nothing: `cls` is the reverse of tagfilter.WAY_CLASSES,
  `highway`/`name`/`surface` are the raw OSM tag values, `access_ok=0` only when `access` or
  `motor_vehicle` is one of no/private/customers/delivery/permit/military, `oneway` from the `oneway` tag.
  No score is invented - the emitter writes `terms_osm`/`terms_raster` EMPTY today (T-0030 R3/R12), so
  window-scored.json is not an input to a byte count at all, and that is stated again in M3 as a caveat.
  RECORDED GAP (not fixed here): no real-extract adapter exists, so `corpus.build` has never been run on
  real data by anything that ships. This measurement is the first time it has been run on real data at all.

  M2 - THE BUILD, OVER THE LARGEST REAL POPULATION I HONESTLY CAN, IN THE FOREGROUND.
  Adapter, quoted as it landed:
      ADAPT in=11740 out=11740 skipped_class=0 skipped_short=0      (la/window-doc.json, the canyon window)
      ADAPT in=11239 out=11239 skipped_class=0 skipped_short=0      (la-grid/grid-a-doc.json)
      ADAPT in=23474 out=23472 skipped_class=2 skipped_short=0      (la-grid/grid-b-doc.json)
      MERGE inputs=3 unique_ways=46231                              (union, deduplicated by way id)
  Two builds, both one foreground call each:
    (a) canyon window alone
      CORPUS region=la ways=11740 segments=24205 collisions=0
      CORPUS content_sha256=97047605f0e150b6af4d34ecf62158eaa73eaac9c0cabbfb0e70381e34df8ed8
      real 0m8.106s ; stat -c %s work/window-corpus.sqlite -> 6135808
      => 6,135,808 B / 24,205 segments = 253.49 B per segment ; / 11,740 ways = 522.64 B per way
    (b) THE UNION (canyon window + grid-a + grid-b), the largest real population available on this box
      CORPUS region=la ways=46231 segments=79764 collisions=0
      CORPUS content_sha256=04d5582d25e6cb61a107e299afbc550ce53d5f74684f1ffe716c4a77e180e9e2
      real 0m18.673s ; stat -c %s work/la-union-corpus.sqlite -> 19906560
      => 19,906,560 B / 79,764 segments = 249.57 B per segment ; / 46,231 ways = 430.59 B per way
  SHARE OF WAYS THAT PRODUCE SEGMENTS: 46,231 of 46,231, i.e. 100%. `Segmenter.cut` cuts every way with
  >= 2 nodes and the adapter refuses fewer (skipped_short=0 on all three inputs); 79,764/46,231 = 1.725
  segments per way. There is no "some ways produce nothing" discount to take.
  The union is the number I extrapolate from, not the canyon window: it is 3.9x the population and its
  per-way cost is 17.6% LOWER (430.59 vs 522.64), because the canyon window is long rural ways.

  M3 - EXTRAPOLATION TO THE WHOLE LA CLIP. ARITHMETIC, SHOWN.
  The filtered clip is services/etl/work/la/la-filtered.osm.pbf, 35,962,835 B, and its per-class way counts
  are recorded in work/la/meta.json: motorway 17,394 + trunk 2,117 + primary 45,535 + secondary 43,198 +
  tertiary 25,798 + unclassified 5,460 + residential 99,715 + living_street 195 + service 312,645 +
  track 8,148 + road 3 = 560,208 filtered ways (the brief's "561,000").
  IS THE UNION REPRESENTATIVE? Its class mix against the clip's: service 51.8% vs 55.8%, residential 21.2%
  vs 17.8%, secondary 8.2% vs 7.7%, primary 6.3% vs 8.1%, tertiary 5.2% vs 4.6%, track 2.5% vs 1.5%,
  motorway 2.4% vs 3.1%, unclassified 1.2% vs 1.0%, trunk 1.1% vs 0.4%. Within a few points on every
  class; if anything the union is slightly SHORT on cheap service ways, so its per-way cost is if anything
  an over-estimate by a few percent, not a multiple.
      560,208 ways x 430.59 B/way = 241,224,000 B = 230.05 MiB = 241.22 MB
      the budget:                    60 MiB       =  62,914,560 B
      the ratio:                    241,224,000 / 62,914,560 = 3.83x
      what would have to be true to fit: 62,914,560 / 560,208 = 112.3 B per way, i.e. 3.8x cheaper.
  VERDICT, PLAINLY: THE FULL LA CLIP IS **OVER** plan:283's ceiling, by a factor of about 3.8. It is not
  close and it is not a rounding argument - the MB/MiB reading moves it by 4.9%, nowhere near 283%.
  AND THE MEASURED NUMBER UNDERSTATES THE SHIPPING CORPUS. This corpus carries `osm_features`, `segments`
  + `segments_rtree`, `term_defs` and `meta` only; `places`, `curated`, `terms_osm` and `terms_raster` are
  emitted EMPTY (T-0030 R3/R10/R12). A shipping LA corpus carries ten normalised terms per way (the shape
  in window-scored.json) plus the POI join plus FTS5 for the Plan sheet. 241 MB is a FLOOR, not a forecast.
  WHAT WOULD SHRINK IT - NAMED, NOT DONE, and none of it attempted in this task:
    * drop `service` ways from the corpus (312,645 of 560,208 = 55.8% of the population; they are driveways
      and parking aisles nobody plans a scenic drive down) - on its own roughly a 2.3x cut;
    * `VACUUM` + `PRAGMA page_size` (the writer takes sqlite's 4096 default and never vacuums);
    * column widths: `geom_sha256` is 32 B per way and `name` is stored per way in full;
    * `segments_rtree` is a second copy of every segment's bbox;
    * region-splitting the download (the plan's lifecycle row already says the corpus is a download, so a
      per-metro corpus is a product decision, not an emitter one).
  These are the finding's follow-ups; this task pins the ceiling and reports the overage.

  RULINGS, before code.
  R2 - WHERE THE LITERAL LIVES. `CORPUS_BUDGET_BYTES = 60 * 1024 * 1024` as a module constant in
  services/etl/etl/corpus.py, ONE literal, beside `build`, which is the emitter's own check. Not schema.py
  (that is the on-device contract - SCHEMA_VERSION, MIN_APP_BUILD, licences - and a build-time budget is
  not part of what the reader on the phone agrees to), and not a new module (see R5).
  R3 - MiB vs MB, against the plan's wording. plan:283 says "corpus <60 MB" and plan:140 says the download
  sheet shows "corpus (~50 MB)". The plan does not distinguish, so this is a real disagreement and I rule
  it: MiB, 60 * 1024 * 1024 = 62,914,560 B. Two reasons. (1) This task's own acceptance line fixes it -
  "a literal CORPUS_BUDGET_BYTES = 60 MiB" - and an acceptance line is the closer authority than a prose
  cell. (2) It is the LOOSER of the two readings (62,914,560 > 60,000,000), so the ceiling never refuses a
  corpus the plan's cell would have allowed; a budget should err toward refusing less than the plan, never
  more. It changes no verdict anywhere in M3.
  R4 - WHAT REFUSES, AND WHAT HAPPENS TO THE FILE. `corpus.build` raises `CorpusTooLargeError` after the
  file is finalised and closed, naming the byte count and the budget; `main` catches it, prints that
  message to stderr and returns 3 (2 is already --built-at's). THE FILE IS LEFT ON DISK, deliberately and
  stated in the message: the whole point of this task's finding is that somebody now has to open a
  241 MB corpus and find the 3.8x - deleting the evidence on refusal would make every shrink experiment
  (VACUUM, page_size, dropping service) start with a build that refuses to leave anything behind. The
  non-zero exit is what stops a pipeline; the bytes are what a human needs.
  R5 - P-PROC-06. This is a size comparison INSIDE an existing module (corpus.py), not a new module under
  services/etl/etl/, so no mutation population is added and none is narrowed. `python
  ops/lib/check-mutate-population.py` -> "P-PROC-06: every added module is covered or allowlisted; the
  floor of 23 holds", re-quoted at the final commit. If a reviewer rules that a one-comparison budget check
  is a "new numeric module" in spirit, the honest answer is an allowlist entry, not a two-mutant driver -
  but it is not a new file, so the gate is not even reached.
  R6 - HOW THE RED TEST PADS PAST THE BUDGET WITHOUT A 60 MB FIXTURE IN GIT. NOT by monkeypatching the
  literal: that binds the test to a name a defect can rename, and CLAUDE.md's defect-named-test rule wants
  the shipping symbol. So `build` takes `budget_bytes=CORPUS_BUDGET_BYTES` - a PARAMETER whose DEFAULT IS
  the literal - the CLI gets `--budget-bytes` with the same default, the committed 7-way fixture is refused
  under a small explicit budget through both `corpus.build` and the CLI run as a subprocess, and a separate
  test asserts `corpus.CORPUS_BUDGET_BYTES == 60 * 1024 * 1024` and that the parameter's default IS that
  constant (so lowering the default to make a suite pass is red by name).
- 2026-09-19T12:54:38Z RED FIRST BY NAME, then green, by agent/claude-opus-5 (owner).
  services/etl/tests/test_corpus_budget.py written before a line of etl/corpus.py moved. Red, quoted:
      FFFFFF                                                                   [100%]
      FAILED tests/test_corpus_budget.py::test_the_default_budget_is_exactly_60_mib
      FAILED tests/test_corpus_budget.py::test_build_refuses_a_corpus_over_the_budget_and_names_both_numbers
      FAILED tests/test_corpus_budget.py::test_the_refused_corpus_is_left_on_disk_for_inspection
      FAILED tests/test_corpus_budget.py::test_a_corpus_under_the_budget_is_built_and_reports_its_bytes
      FAILED tests/test_corpus_budget.py::test_the_cli_exits_non_zero_over_the_budget
      FAILED tests/test_corpus_budget.py::test_the_cli_builds_and_prints_the_bytes_under_the_default_budget
      6 failed in 0.97s
  (the first three fail on `AttributeError: module 'etl.corpus' has no attribute 'CORPUS_BUDGET_BYTES'` /
  no `CorpusTooLargeError`; the CLI ones on an exit of 0 and a stdout with no `CORPUS bytes=` line.)
  Then `CORPUS_BUDGET_BYTES`, `CorpusTooLargeError`, `BUDGET_EXIT = 3`, the `budget_bytes` parameter, the
  size check after `finalize`, `--budget-bytes` and the `CORPUS bytes=... budget=...` line went into
  etl/corpus.py. Green: `6 passed in 1.91s`.
  THE CHECK SEEN RED OVER REAL DATA TOO, not only over the fixture - the 46,231-way LA union corpus of M2,
  refused under an explicit 10,000,000 B budget through the shipping CLI:
      CORPUS REFUSED work/budget-demo.sqlite: the corpus is 19906560 bytes, over the budget of 10000000
      bytes (plan:283, 'corpus <60 MB'). The file is LEFT ON DISK so the overage can be inspected.
      exit=3 ; stat -c %s work/budget-demo.sqlite -> 19906560   (R4 held: the file is still there)
  And GREEN over the same real corpus under the real default: the M2 build reported
  `ways=46231 segments=79764` and 19,906,560 B < 62,914,560 B, so today's largest real LA population
  passes the very ceiling the extrapolation says the full clip fails. That asymmetry IS the finding.
  Full suite: `cd services/etl && python -m pytest tests -rs -o addopts=` -> `1199 passed in 85.19s`,
  zero skips (every __pycache__ under services/etl purged first).
- 2026-09-19T12:58:42Z FINAL PRE-REVIEW COMMIT, by agent/claude-opus-5 (owner). `git fetch origin && git
  merge --no-edit origin/main` FIRST -> "Already up to date.", head still a3cc165, so the merged head is
  this branch's head and the whole acceptance block was re-run on it:
    * acceptance 1, the measured byte count: `stat -c %s work/la-union-corpus.sqlite` -> 19906560 over
      ways=46231 segments=79764 (canyon window alone: 6135808 over ways=11740 segments=24205).
    * acceptance 1, the extrapolation: 560,208 filtered ways (work/la/meta.json's own per-class counts,
      summed) x 430.59 B/way = 241,224,000 B = 3.83x the 62,914,560 B budget. LA IS OVER. Floor, not
      forecast: terms_osm, terms_raster, places, curated and FTS are all still empty.
    * acceptance 1, the emitter's check, RED first then green, and red again over real data at exit 3 with
      the file left on disk - quoted in full in the entry above.
    * acceptance 2: `cd services/etl && python -m pytest tests -rs -o addopts=` on the merged head ->
      `1199 passed in 117.19s (0:01:57)`, ZERO skips (-rs printed no skip section), __pycache__ purged.
    * `python ops/lib/check-mutate-population.py` -> "P-PROC-06: every added module is covered or
      allowlisted; the floor of 23 holds". No population touched, so no population runner to re-run (R5).
    * `bash ops/lib/check-line-cap` -> "P-SRC-02: 90 Swift files tracked (Sources=29, Tests=40,
      apps/ios=21), none over 300 lines".
    * `bash ops/lib/check-exec-bits` -> "P-OPS-01: 78 files, 23 required present, all modes correct".
    * `bash ops/queue-check` -> "QUEUE OK (208 tasks)". state: claimed and reviewer: null untouched.
    * `wc -l` on every touched file: 210 services/etl/etl/corpus.py, 96
      services/etl/tests/test_corpus_budget.py, 164 this task file. All under the 300-line cap.
  NOT RUN LOCALLY AND SAID SO: `bash ops/test` and the full `bash ops/check-pins` (the brief forbids them
  here - they are CI's job on the PR), and `ops/check-pins --source-only` was skipped locally.
  STILL OPEN, carried into the PR body:
    1. LA AT FULL SIZE IS 3.8x OVER plan:283's ceiling. This task pins the ceiling and reports the
       overage; it shrinks nothing. The named candidates are in the 12:50:07Z entry (drop `service`, which
       is 55.8% of the population; VACUUM/page_size; column widths; the rtree copy; region-splitting).
       That is a product-and-schema decision, not an emitter tweak, and belongs to its own task.
    2. NO REAL-EXTRACT ADAPTER SHIPS (R1). The waydoc -> ExtractWay conversion used here lives in the
       gitignored work/ dir and is not committed. `corpus.build`'s only committed input is still the
       seven-way synthetic fixture.
    3. The budget is checked at the END of the build. A corpus 4x over budget is written in full before it
       is refused; nothing estimates the size up front and bails early.
- 2026-09-19T13:12:48Z RULINGS ON THE PRE-REVIEW MUTANT PASS, by agent/claude-opus-5 (owner), BEFORE any
  code. The Log is append-only: nothing above this line is edited; every correction below is a NEW statement
  that supersedes the one it names. The read-only pass is
  .artifacts/signoffs/t0206-mutant-pass.md (M1, M3a/M3b, M4 and three unsupported claims).
  FIRST, the author rule's newest sentence, now met: `git fetch origin && git merge --no-edit origin/main`
  -> "Merge made by the 'ort' strategy", merge commit 3282afc over 20 files, all under services/routing/,
  ops/ and queue/ - ZERO overlap with this branch's three files. Committed alone. The 12:58:42Z entry's
  "Already up to date." was true when written and is now stale: HEAD 3fd7865 was six commits behind
  origin/main. The whole acceptance block is re-run and re-quoted on the merged head in the next entry.

  R7 - M3b IS BLOCKING AND THE FIX IS TWO BINDINGS, NOT A THIRD ASSERTION ON A PRINTED LINE. The pass is
  right: every refusal any test proves today passes an EXPLICIT budget, and the only no-flag CLI test reads
  a printed number. So `python -m etl.corpus` with no `--budget-bytes` - exactly what a pipeline runs -
  could carry `budget_bytes=None` with the literal printed beside it and ship a 241 MB corpus at exit 0.
  The honest shape, ruled: (i) the CLI's argparse default must BE the literal, asserted THROUGH THE SHIPPING
  PARSER - `corpus.parse_args([...required args only...]).budget_bytes is corpus.CORPUS_BUDGET_BYTES` - not
  through `inspect.signature(build)`, which is the binding M3b walks around; and (ii) `build` REFUSES
  `budget_bytes=None` with a `TypeError` naming it, so "unlimited" is not spellable at all. (ii) is what
  makes the mutant dead rather than merely observed: with the None arm refused, a CLI default of None makes
  the no-flag subprocess exit non-zero on a TypeError, and the printed-line test fails on returncode. I do
  NOT write the honest form the pass sketched as an alternative - "a fixture that EXCEEDS a default" - for
  the reason the pass itself gives: the default is 62,914,560 B and no fixture in git is or should be that
  big. The comparison against the default is instead exercised both ways through the CLI: green with no
  flag (report bytes < budget, printed `budget=62914560`), red with `--budget-bytes` one byte under the
  built size.
  R8 - M1, THE TIE, RULED `>=`: A CORPUS OF EXACTLY THE BUDGET IS REFUSED. plan:283 says "corpus <60 MB",
  strictly less, and the code shipped `>` , which lets a corpus of exactly 62,914,560 B through - the one
  size the plan's own wording excludes. R3 already ruled the READING of the unit (MiB, the looser of the
  two); the reading of the RELATION is the plan's and the plan is strict, so `size >= budget_bytes`
  refuses. This refuses strictly more than the shipped code, never less, so it cannot hide an overage; it
  costs exactly one corpus size in the whole space and that size is the one plan:283 names. The refusal
  message stops saying "over the budget" and says "not under the budget of N bytes", because with `>=` the
  refused size may equal it. Tie fixture, red first: budget == the built size and budget == size-1 both
  refuse, budget == size+1 builds.
  R9 - M4: `test_the_cli_exits_non_zero_over_the_budget` asserts `returncode != 0`, which cannot tell
  BUDGET_EXIT 3 from `--built-at`'s 2 - and R4 chose 3 precisely to distinguish them. Ruled: assert
  `done.returncode == corpus.BUDGET_EXIT == 3` exactly, in one line, so both the constant and the wiring
  are bound.
  R10 - THE ARITHMETIC SLIP (pass, UNSUPPORTED 1), re-derived with python on this head and CORRECTED HERE.
  The rate is 19,906,560/46,231 = 430.5890 B per way. 560,208 x that rate = **241,219,402 B**
  (241,219,401.80, exact from the unrounded rate; 241,219,963 B if you multiply the rounded 430.59) =
  230.04 MiB = 241.22 MB, and the ratio to 62,914,560 B is **3.834x**. The 12:50:07Z entry's and the
  12:58:42Z entry's "241,224,000 B = 230.05 MiB" is WRONG BY ~4,600 B (0.002%) and is superseded by this
  line. THE VERDICT IS UNCHANGED: full LA is about 3.8x over plan:283's ceiling, a floor and not a
  forecast. The same wrong product sits in two committed files; in `etl/corpus.py` the number is REMOVED
  from the comment rather than corrected - CLAUDE.md says anchor nothing on a comment, and a hand-carried
  extrapolation in a source comment is a second copy of a Log measurement that nothing keeps true - and in
  the test docstring it is corrected in place, because that docstring is the defect's own statement.
  R11 - NO MUTATION POPULATION IS BUILT HERE, and the reason is now checked rather than asserted:
  `services/etl/etl/corpus.py` is ALLOWLISTED in ops/lib/mutate-population-allowlist.json with the reason
  "the `python -m etl.corpus` command line; wiring over corpuswriter and the producers", and
  `python ops/lib/check-mutate-population.py` prints "74 modules, 23 covered by 11 populations, 27
  allowlisted, 0 added by this branch" with corpus.py in NEITHER the DEBT list NOR any driver's
  SUBJECT_MODULES. So the three mutants M1/M3b/M4 are landed as NAMED TEST CASES (the tie fixture, the
  parser-default and None-refusal bindings, the exact exit code), not as entries in a population this
  branch has no standing to add. R5 stands, now with the allowlist entry quoted.
  R12 - the 12:58:42Z acceptance block measured this task file at 164 lines; it was 196 at HEAD 3fd7865.
  That measurement is superseded; `wc -l` on all three touched files is re-taken at the final commit below
  (CLAUDE.md: a correction commit that touches a measured file re-measures it).
