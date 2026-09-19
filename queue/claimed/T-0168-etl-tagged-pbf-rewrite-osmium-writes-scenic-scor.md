---
id: T-0168
title: ETL tagged-PBF rewrite - osmium writes scenic_score 0..10 and its terms onto ways, in the container, over a real extract
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T05:16:14Z
lease_expires_at: 2026-09-19T13:16:14Z
worktree: .worktrees/T-0168
branch: task/T-0168
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, services/etl/Dockerfile, services/etl/inputs/manifest.yaml, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0146, T-0169, T-0161, T-0189, T-0142]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED BY NAME before code: a test that runs the tagged-PBF writer twice over the same input and asserts byte-identical output (P-DATA-01), red until the writer exists; then green with both sha256 values quoted"
  - "the manifest line re-recorded the same day as the fetch: the fetcher's `verified california-osm.pbf bytes=<N> retrieved=<YYYY-MM-DD> md5 ok` line quoted, and manifest.yaml's bytes:/retrieved: equal it in the same commit (the T-0169 copy is gone - see the INPUT ruling)"
  - "`osmium fileinfo -e` over the output PBF, run in WSL, with its node/way counts quoted; the count of ways carrying scenic_score printed by the writer equals the way count the assembler scored"
  - "the two `ops/sane` check-4 clauses printed as NUMBERS by a check that refuses on either: ways with a NULL scenic_score = 0; motorway/trunk/private/unpaved ways with scenic_score > 0 = 0"
  - "the ranked top-10 ways by scenic_score printed with name, highway class and a coordinate, for the human's '8/10 are roads you'd drive' read (plan M2 exit); the list is quoted, the judgement is not made by the agent"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit; every wc -l re-measured there"
---
## Brief

The WSL half of what T-0146 used to be (cut by the 2026-09-18 14:13 panel, grounded). T-0146 proves the
assembly and the check-4 gates over a committed fixture with native Python; THIS task runs it over a real
extract inside the pinned ETL image (docker on this box works only through WSL) and has `osmium` write
`scenic_score=0..10` plus the terms back onto the ways of the tagged PBF that T-0031 imports into GraphHopper.

It deliberately carries what a hand-written fixture cannot surprise its author with: real tag coverage
(per-class surface coverage goes into `meta`, plan M2 row), NULLs from ways with no DEM or land-cover sample,
and the plan's human exit clause - "8/10 top-scored ways are roads you'd drive" - printed as a ranked list
with names and coordinates for the human to read. `ops/sane` check 4's clauses run for real here: no NULL
scores; no motorway/trunk/private/unpaved way with a score above 0.

Rule in the Log before code: the 0..1 -> 0..10 quantisation (round, floor, or keep one decimal - the
GraphHopper encoded value's bit width decides); what happens to a way a producer REFUSED (a named flag, never
a silent 0); idempotence (P-DATA-01: running twice over the same extract is byte-identical); which extract
(the refetched California file from T-0169, clipped to regions/la's bbox (sfbay second)).

## Log
- 2026-09-18T20:57:28Z filed by agent/claude-fable-5-1 from the 14:13 panel's grounded synthesis. Not started.
- 2026-09-19T00:40:47Z PROMOTED to ready/ with FOUR RULINGS and the input decision, by agent/claude-fable-5-1 (17:13 panel, STRATEGY
  + grounding). depends_on gains T-0161 (T-0146's Log already says this task keeps it; #94 is in its fourth
  round with proximity.py judged correct four times).
  R1 QUANTISATION: `scenic_score` 0..10 = round-half-up of the 0..1 score x 10 (an integer; GraphHopper's
  encoded value holds it in 4 bits); the 0..1 value stays in the corpus, so nothing downstream re-derives it.
  R2 REFUSED: a way a producer refused carries `scenic_refused=1` and NO `scenic_score` tag - never a silent 0
  (0 means "dull", the CLAUDE.md invariant for motorway/trunk); the check-4 NULL count therefore counts only
  ways that should have a score and lack one.
  R3 IDEMPOTENCE: running the writer twice over the same input is byte-identical (built_at is an INPUT, not a
  clock; osmium's output ordering is fixed by input order) - the first acceptance line.
  R4 INPUT: T-0169's verified 1,328,688,632-byte california-osm.pbf was DELETED with its worktree the hour
  #99 merged (only the unverifiable 2026-09-08 build survives as hardlinks in .worktrees/T-0028 and T-0107,
  1,482,437 bytes short of the manifest). REFETCH natively - `cd services/etl && python -m etl.fetch --only
  california-osm.pbf` (T-0169's run took 7m43s) - INTO THE MAIN CHECKOUT's gitignored services/etl/inputs/
  (C:/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/inputs/), never into a worktree, and point
  the extract at it; re-record manifest bytes:/retrieved: the same day. The 51 MB Sep-8 sfbay-filtered.osm.pbf
  in .worktrees/T-0028 may serve as a SMOKE input for the osmium write loop only, with its provenance gap
  named in the Log. T-0177 makes the shared inputs directory the rule.
- 2026-09-19T00:49:41Z LA FIRST, by agent/claude-fable-5-1 (the owner lives in Los Angeles - memory user-lives-in-la): the extract this task clips and scores is LA FIRST (`services/etl/regions/la/region.json`'s bbox), sfbay second - the owner drives in Los Angeles, and the plan's '8/10 top-scored ways are roads you'd drive' is a judgement only the owner can make over roads the owner knows; both clips come from the same statewide california-osm.pbf.
- 2026-09-19T02:11:14Z WORDS FOLLOW THE RULING, by agent/claude-fable-5-1 (19:13 panel, grounded): the Brief's 'clipped to the sfbay bbox' contradicted the 00:49:41Z LA FIRST line; corrected (1 replacement). The refetch into the main checkout's services/etl/inputs/ was started by the orchestrator at 2026-09-19T02:11:14Z (log under .artifacts/fetch/); re-record manifest bytes:/retrieved: from its printed line in this task's commit.
- 2026-09-19T02:54:47Z INPUT ON DISK, by agent/claude-fable-5-1: the refetch into the MAIN checkout's gitignored services/etl/inputs/ verified at 2026-09-19T02:54:47Z after one md5 race with Geofabrik's daily rebuild (the first attempt's sidecar changed mid-download; the fetcher deleted the file and retried, as T-0169 designed). The fetcher printed: `verified california-osm.pbf bytes=1328857020 retrieved=2026-09-19 md5 ok`. os.path.getsize -> 1328857020 (a newer build than T-0169's 1,328,688,632). This task's commit re-records manifest.yaml's bytes:/retrieved: from that line; the file survives worktree removal now (T-0177).
- 2026-09-19T03:45:19Z depends_on += T-0189 by agent/claude-fable-5-1 (rv1-pr104's finding): dem.py and landcover.py still read a per-worktree inputs/ and return None silently when a tile is absent; from a worktree this task would score LA with terrain zeroed and a green suite. T-0189 makes the four consumers read the shared directory and refuse by name.
- 2026-09-19T04:34:10Z depends_on += T-0142 by agent/claude-fable-5-1 (22:13 panel, grounded): T-0142's Log at 2026-09-19T02:58:56Z rules its finding 3 'a HARD prerequisite of T-0168' - dem.tile_for returned None for every point outside sfbay's eight tiles, so an LA clip would score with terrain silently zeroed and this task's check-4 numbers and top-10 read would mean nothing. The queue now says what that Log already rules: a claimer cannot start this before PR #106 merges.
- 2026-09-19T05:07:19Z CARRIED IN from rv2-pr106's PASS on PR #106 (T-0142), by agent/claude-fable-5-1: recordable R-A - dem._cache_key's st_mtime_ns half is correct but uncovered (a region.json bbox rewritten in-process leaves served_tiles stale while tiles_for_region moves; a mutant dropping the stamp passed 1045/1045). One extra line in test_served_tiles_notices_a_region_added_after_its_first_call (rewrite a region's bbox, assert the answer moves) closes it; this task touches services/etl/tests/ and runs from a worktree that reads regions/la, so it lands here, red by name first. Also from that entry: this task must pass tiles=dem.tiles_for_region('la') (the default is still sfbay's eight; an LA point with the default is a silent None by geography, not by file).
- 2026-09-19T05:16:14Z claimed by agent/claude-opus-5; lease until 2026-09-19T13:16:14Z
- 2026-09-19T05:34:07Z touches: WIDENED to `services/etl/inputs/manifest.yaml` by agent/claude-opus-5 (the owner), because
  acceptance bullet 2 is a re-record of that file's `bytes:`/`retrieved:` for california-osm.pbf and R5 below adds the
  LA land-cover entry this task consumes. The pre-commit hook reads `touches:`, so the widening is in the header and its
  reason is this line. Nothing else outside `touches:` is staged.
- 2026-09-19T05:34:07Z R5 WHICH TERMS ARE COMPUTABLE, by agent/claude-opus-5 (the owner), from what is on disk in the
  shared inputs directory C:/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/inputs/ (`ls -l`: california-osm.pbf
  1328857020, 3dep-n34w118.tif 351919765, 3dep-n34w119.tif 77566808, 3dep-n35w118.tif 422435036, 3dep-n35w119.tif
  454839551, manifest.yaml). Every producer `assemble.record_from_row` calls, its input, and whether that input exists:
    curvature.way_curvature(coords)            way geometry from the PBF                          ON DISK (the extract)
    sinuosity.way_sinuosity(coords)            way geometry                                       ON DISK
    speedfit.speed_fit_for_tags(highway,max)   way tags                                           ON DISK
    furniture.furniture_per_km(nodes,length)   tagged nodes the way REFERENCES, from the PBF       ON DISK
    terrain.elevation_gain/relief(profile)     dem.sample_smoothed -> 3dep-n34w118/n34w119/        ON DISK (all four)
                                               n35w118/n35w119.tif
    proximity.tunnel_meters(coords,tags)       tags + geometry                                    ON DISK
    proximity.meters_to_nearest_motorway       the clip's own motorway/trunk ways                 ON DISK
    landcover.fractions(codes)                 landcover.sample_codes -> worldcover-n33w120.tif   **NOT ON DISK**
    byways.match(coords,entries,ref)           byway_source.load -> byways-caltrans.geojson       **NOT ON DISK**
                                               + byways-fhwa.geojson
    points_of_interest                         DEFERRED (T-0164); the assembly already substitutes `POI_ABSENT` and
                                               flags `points_of_interest_absent` by name - unchanged here.
  THE DECISION, honestly: both absent inputs are FETCHED natively into the shared directory, because both are small and
  both are already-reviewed sources, not new dependencies:
    - byways-caltrans.geojson (8,764,515 B) and byways-fhwa.geojson (29,545,684 B) are ALREADY PINNED by sha256 in
      manifest.yaml (consumed_by T-0028) and `byway_source.load(inputs_dir)` already reads the pair into
      `byways.match`'s entry shape. Nothing to decide: `python -m etl.fetch --only <name>` for each.
    - land cover needs exactly ONE WorldCover tile for the whole LA bbox - `landcover.tile_for` over both bbox corners
      (33.7,-119.0) and (34.45,-117.85) answers N33W120 for both (3x3 tiles named by their south-west corner). The
      manifest pins the DATASET (ESA WorldCover 2021 v200, CC-BY-4.0, consumed_by T-0027) and two of its tiles, but only
      sfbay's N36W123/N36W126. LA's tile is a new entry OF AN ALREADY-REVIEWED SOURCE, ~100 MB, far under the ~3 GB bar,
      so it is added here - `--record-digest worldcover-n33w120.tif`, the printed sha256 committed deliberately,
      consumed_by T-0168 - rather than scoring Los Angeles with canopy, impervious and water absent. The alternative
      (running with those three ABSENT BY NAME) was costed and rejected: canopy and (1-impervious) are 0.40 of E, the
      assembly refuses a row whose land-cover buffer has no valid sample (assemble.py's `landcover buffer has no valid
      sample for ...`), and a top-10 read with no vegetation term is not the plan's M2 read at all.
  WHAT THE LA SCORE IS STILL MISSING, stated here and in the PR: `points_of_interest` (T-0164, substituted by
  `POI_ABSENT` and flagged on every row).
- 2026-09-19T05:34:07Z R6 THE WRITER, by agent/claude-opus-5. `osmium tags` does not exist, and osmium-tool 1.16.0 has NO
  subcommand that adds a tag to an object - checked against the installed tool, not assumed. PyOsmium is NOT in the
  pinned image: services/etl/Dockerfile installs osmium-tool, osm2pgsql, gdal-bin, python3, python3-pytest, python3-yaml,
  sqlite3, and `tests/test_dockerfile.py:15`'s REQUIRED_PACKAGES pins that list. Installing python3-pyosmium would mean
  editing and rebuilding the pinned image AND putting the writer in a module the host suite cannot import - the suite runs
  on the Windows host interpreter, so P-DATA-01's byte-identical test would have to skip, and this task's acceptance says
  zero skips. RULING: the tagged-PBF rewrite is `osmium cat` on both ends - `osmium cat -o clip.osm.xml clip.osm.pbf`,
  a pure-Python tag pass (`etl/osmxml.py` + `etl/tagwriter.py`) that copies the stream element by element IN INPUT ORDER
  and adds tags in one fixed key order, then `osmium cat -o clip-scored.osm.pbf clip-scored.osm.xml`. osmium does every
  PBF encode and decode; the tag pass is the only thing that writes a scenic tag, and it is testable on the host over a
  committed .osm.xml fixture with no container. R3 (idempotence) follows from the shape: output order is input order,
  every number is formatted with a fixed precision, and nothing reads a clock - `built_at` is an input.
  WHAT IS WRITTEN (R1, R2): a way with a `highway` tag and a score carries `scenic_score` = round-half-up(score x 10) as
  an integer 0..10, `scenic_score_unit` = the 0..1 score at 4 dp (written, never re-derived downstream - R1), the ten
  0..1 terms the score was computed from as `scenic_<term>` at 4 dp, `scenic_flags` when the record has any, and
  `scenic_gate` naming the safety gate when one fired. A way whose producer REFUSED carries `scenic_refused=1` and
  `scenic_refused_why=<reason>` and NO `scenic_score` (R2). A way with NO `highway` tag (the POI ways the tag filter
  keeps - park, nature_reserve, beach, attraction) is NOT a road, is not in the population, and is written through
  untouched: it is neither scored nor refused, and the check below counts it as neither.
- 2026-09-19T05:34:07Z R7 THE RUN SHAPE and the scoring window, by agent/claude-opus-5. Seven steps, each one command
  that finishes in the foreground, each timed:
    1. `python -m etl.fetch --only ...` natively on the host for the two byway files and the land-cover tile, and
       `--verify-only` over what is on disk. NEVER a plain fetch of california-osm.pbf: Geofabrik rebuilds daily and a
       failed md5 makes the fetcher DELETE the 1.3 GB payload (fetch.py's `never leave an unverified file ...`).
    2. `python3 -m etl.extract --region la --no-docker` in the pinned image.
    3. `osmium extract --bbox <window>` out of la-filtered.osm.pbf - THE SCORING WINDOW.
    4. `python3 -m etl.waydoc` - the clip's XML -> the assembly document (geometry, tags, furniture nodes, DEM profile,
       land-cover codes, byway entries).
    5. `python3 -m etl.assemble` - the scored table and its ASSEMBLE count line.
    6. `python3 -m etl.tagwriter` twice -> tagged XML -> `osmium cat` -> PBF twice -> two sha256 values.
    7. `python3 -m etl.scenecheck` - the check-4 numbers and the top-10.
  THE WINDOW, and why the whole LA clip is not scored today: the LA clip is 561,000 ways (the count line in step 2).
  Every term above is per-way Python over real geometry, and the plan's M2 exit clause is a JUDGEMENT THE OWNER MAKES
  over roads the owner knows - it does not need 561,000 ways, it needs the owner's own roads ranked against their own
  neighbourhood. So the scored population is a NAMED window of the LA clip, recorded in the document's own `meta` and
  in region-independent form on the command line: bbox -118.95,33.98,-118.35,34.15 (47,489 ways, 356,813 nodes,
  4,269,474 B measured with `osmium fileinfo -e`) - Westwood (where the owner lives), the Santa Monica Mountains crest,
  Mulholland, Topanga, Latigo and Decker canyons, and the PCH coast to Leo Carrillo, which is region.json's own
  `_comment_dem` rationale for the tile the manifest pins. Everything the window excludes is a LATER RUN of the same
  commands with a different `--bbox`, not different code. A smaller honest population beats a claimed larger one
  (CLAUDE.md, The premise).
  ONE THING THE RUN SHAPE WORKS AROUND AND DOES NOT FIX - STILL OPEN: `extract.Osmium.rel()` resolves every path
  relative to `ROOT` = THIS checkout's services/etl, while `extract.INPUTS` is `fetch.resolve_inputs_dir(ROOT)` = the
  MAIN checkout's services/etl/inputs (T-0177). From a worktree those two disagree and `rel(source)` raises ValueError
  before osmium is ever called, so `ops/etl-extract` cannot run from a worktree at all. The run mounts the shared inputs
  directory read-only at the worktree's own services/etl/inputs inside the container and sets SCENIC_ETL_INPUTS to it;
  the defect is recorded here and in the PR, unfixed, because fixing extract.py's mount is a change to a module three
  other tasks are measured against and this task's evidence does not depend on it.
- 2026-09-19T05:34:07Z R8 THE CHECK-4 CHECK, by agent/claude-opus-5: `etl/scenecheck.py`, a module and a CLI, reads the
  TAGGED OUTPUT read back out of the PBF by `osmium cat` (so the numbers are about the file that ships, not about the
  table in memory) and prints both `ops/sane` check-4 clauses as NUMBERS on one line -
  `CHECK4 null_score=<n> gated_scored=<n> scored=<n> refused=<n> not_a_road=<n>` - refusing with exit 4 (ops/sane's
  reserved code for corpus bounds) if EITHER of the first two is non-zero. `null_score` counts ways that SHOULD have a
  score and lack one: a `highway` way that is not `scenic_refused` and has no `scenic_score` (R2). `gated_scored` counts
  motorway/trunk/motorway_link/trunk_link, private/no-access, positive-evidence unpaved and track ways with
  `scenic_score > 0`, with the class set imported from `byways.SCENIC_ZERO_CLASSES` and the gate rules from
  `assemble.gate_reason` - never restated here, because two copies of a gate is how two answers for one road reach the
  corpus. RED BY NAME FIRST on two fixtures, one violating each clause.
- 2026-09-19T05:34:07Z R9 THE TOP-10 PRINT, by agent/claude-opus-5: `scenecheck --top 10` prints rank, way_id, name,
  highway class, one coordinate (the way's middle node at 5 dp - a local file, not the server, so CLAUDE.md's
  two-decimal server rule is not what is being satisfied here), `scenic_score` 0..10 and `scenic_score_unit`. It is
  printed verbatim into the PR. THE JUDGEMENT - "8/10 are roads you'd drive" - IS THE OWNER'S AND IS NOT MADE BY THIS
  AGENT OR ANY OTHER.
- 2026-09-19T05:34:07Z R10 THE CACHE-STAMP ONE-LINER carried in from rv2-pr106, by agent/claude-opus-5: the extra
  assertion goes in `tests/test_dem_tiles.py::test_served_tiles_notices_a_region_added_after_its_first_call` - after the
  two-region assertion, REWRITE `east`'s region.json bbox in place and assert `served_tiles` moves with it
  ({n45w100,n45w101} -> {n45w99,n45w101}). Red by name first on a copy of `dem._cache_key` with the `st_mtime_ns` stamp
  dropped. Deliberately still on the Dakota plains, for the reason the test's own docstring gives.
- 2026-09-19T05:34:07Z A NUMERIC MODULE SHIPS A MUTATION POPULATION (CLAUDE.md, Verification), ruled by
  agent/claude-opus-5: of the three new modules, `osmxml.py` is a stream copy and `waydoc.py` is wiring over producers
  that already carry their own populations (curvature, terrain, landcover, proximity, sinuosity, furniture) - neither
  computes a number of its own. `tagwriter.py` DOES: the R1 quantisation, round-half-up(score x 10) clamped to 0..10,
  is a number this repository computes nowhere else, and `scenecheck.py` computes the two check-4 counts. Both get a
  committed mutation population under `ops/mutate/` with a literal floor.
- 2026-09-19T06:05:31Z R7 CORRECTED - THE WINDOW MOVED, and why, by agent/claude-opus-5 (the owner). R7 named
  -118.95,33.98,-118.35,34.15 (47,489 ways). MEASURED, not guessed: `waydoc` runs at 11,740 rows in 1m56s and
  `assemble` at 3m34s for the same rows, so 47,489 ways is ~8 min in waydoc and ~14 min in assemble - and every
  container step in this session must FINISH inside one foreground call (600 s). Splitting a stage that has no resume
  is how a half-built document gets scored. So the window is the same box with its east edge at -118.55 instead of
  -118.35: **-118.95,33.98,-118.55,34.15, 12,402 ways / 155,208 nodes** (`osmium fileinfo -e`), which is Malibu from
  Leo Carrillo, the whole Santa Monica Mountains crest, Mulholland Highway, Decker, Latigo, Kanan Dume, Malibu Canyon,
  Stunt, Piuma and Topanga. WHAT IT NOW EXCLUDES, named: Westwood, Brentwood and Santa Monica - the owner's own
  streets, which were to be the dull contrast in the ranked read. They are a LATER RUN of the same five commands with
  `--bbox -118.55,33.98,-118.35,34.15`, not different code. The probe: -118.95,33.98,-118.55,34.15 -> 12,402 ways;
  -118.95,34.00,-118.60,34.15 -> 10,979; the R7 box -> 47,489.
- 2026-09-19T06:05:31Z RED BY NAME, then green, by agent/claude-opus-5. Four test modules were written against four
  docstring-only stubs and run BEFORE any of them had a function: `41 failed in 1.92s`, every one by name, including
  the acceptance's first line `tests/test_tagwriter.py::test_the_writer_is_byte_identical_over_two_runs_of_the_same_input`
  and both check-4 clauses, `tests/test_scenecheck.py::test_a_road_with_no_score_is_counted_as_a_number_and_refuses`
  and `::test_a_motorway_with_a_score_above_zero_is_counted_as_a_number_and_refuses`. After the four modules landed:
  `42 passed in 1.27s` over the same four files.
  R10's one-liner was demonstrated the same way and on the MUTANT the recordable names: with
  `dem._cache_key`'s `stamps` line replaced by `tuple(region_ids(root))` - the stamp dropped, nothing else touched -
  `FAILED tests/test_dem_tiles.py::test_served_tiles_notices_a_region_added_after_its_first_call`,
  `assert frozenset({'n45w100', 'n45w101'}) == {'n45w099', 'n45w101'}`, "served_tiles answered from its cache while
  the region's own bbox had moved under it". `dem.py` restored from its pristine copy (`git diff --stat` empty) and
  the file is 20 passed. The rewrite sets the new mtime with `os.utime` rather than trusting two writes inside one
  clock tick to differ, which on this box's filesystem they need not.
- 2026-09-19T06:05:31Z THE RUN, for real, in the pinned image (scenic-etl:latest, osmium 1.16.0 / libosmium 2.20.0,
  GDAL 3.8.4, python 3.12.3), docker through WSL, by agent/claude-opus-5. Every step a command that finished in the
  foreground; wall clock as printed by `time`:
    1. INPUTS. `python -m etl.fetch --only byways-caltrans.geojson` ->
       `verified byways-caltrans.geojson bytes=8764515 retrieved=2026-09-19 sha256 ok`; `--only byways-fhwa.geojson`
       -> `verified byways-fhwa.geojson bytes=29545684 retrieved=2026-09-19 sha256 ok`;
       `--record-digest worldcover-n33w120.tif` -> `worldcover-n33w120.tif sha256:
       61e0909a51e2e76a6f153599316753370be937d0ce150261d023006a80613385`, 101,202,142 bytes, committed into
       manifest.yaml in this commit with `bytes:` and `retrieved: 2026-09-19`. california-osm.pbf was NOT re-fetched -
       Geofabrik rebuilds daily and a failed md5 deletes the payload; its own fetch line is this task's 02:54:47Z
       entry, `verified california-osm.pbf bytes=1328857020 retrieved=2026-09-19 md5 ok`, and manifest.yaml's
       `bytes:`/`retrieved:` now equal it.
    2. EXTRACT, `python3 -m etl.extract --region la --no-docker`: `extract california-osm.pbf -> la.osm.pbf bbox
       -119.0,33.7,-117.85,34.45 / 312 MB in 98s`, `filter la.osm.pbf -> la-filtered.osm.pbf 19 expressions / 36 MB
       in 51s`, then the count line, class by class: motorway 17,394 · trunk 2,117 · primary 45,535 · secondary
       43,198 · tertiary 25,798 · unclassified 5,460 · residential 99,715 · living_street 195 · service 312,645 ·
       track 8,148 · road 3 · viewpoint 303 · picnic_site 591 · attraction 549 · peak 342 · waterfall 154 · beach 106
       · park 2,580 · nature_reserve 774, and `BOUNDS OK  19 class(es) within 15%`.
    3. WINDOW, `osmium extract --bbox -118.95,33.98,-118.55,34.15` + `osmium cat` to XML: 12,402 ways, 155,208 nodes,
       76 relations; window.osm.pbf 1,415,532 B, window.osm.xml 24,835,081 B (0.655 s for the cat).
    4. WAYDOC, 1m56.591s: `WAYDOC ways=11740 refused=0 not_a_road=662 byways=865 byways_no_route_key=793`.
       ZERO refusals - every way in the window had a DEM sample and a land-cover sample, which is what the four 3DEP
       tiles plus the new WorldCover tile buy. window-doc.json 43,473,749 B.
    5. ASSEMBLE, 3m33.557s: `ASSEMBLE ways=11740 zero_class=386 gated=5589 sinuosity_declined=619
       points_of_interest_absent=11740 null_score=0`. window-scored.json 7,283,786 B.
    6. WRITE, 19.983s: `WRITE ways=12402 scored=11740 refused=0 gated=5589 not_a_road=662` - the writer's scored
       count EQUALS the assembler's `ways=11740`, which is acceptance bullet 3's second half. Run twice into two
       files, each passed through `osmium cat` to PBF:
         06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  work/la/window-tagged-1.osm.pbf
         06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  work/la/window-tagged-2.osm.pbf
       Byte-identical over the real extract, not only over the fixture (P-DATA-01, ruling R3).
       `osmium fileinfo -e work/la/window-tagged-1.osm.pbf`: nodes 155,208 · ways 12,402 · relations 76 · bounding box
       (-119.0186574,33.9490449,-118.3400603,34.172355) - wider than the clip bbox because `osmium extract` completes
       every way that crosses the boundary. 1,670,643 B against the untagged clip's 1,415,532 B.
    7. CHECK, over the tagged PBF read BACK with `osmium cat`, 9.067s:
       `CHECK4 null_score=0 gated_scored=0 scored=11740 refused=0 not_a_road=662`.
  WHERE THE ARTEFACTS ARE (the extract's WORK dir is per-checkout and gitignored - nothing here is committed):
    C:/Users/phineasf/Documents/GitHub/scenic_drive/.worktrees/T-0168/services/etl/work/la/la.osm.pbf           312 MB
    .../work/la/la-filtered.osm.pbf                                                                              36 MB
    .../work/la/window.osm.pbf 1,415,532 B · window.osm.xml 24,835,081 B
    .../work/la/window-doc.json 43,473,749 B · window-scored.json 7,283,786 B
    .../work/la/window-tagged-1.osm.pbf 1,670,643 B · window-tagged-2.osm.pbf 1,670,643 B (the P-DATA-01 pair)
    .../work/la/window-readback.osm.xml (what `scenecheck` reads)
  THE TOP TEN, printed by `python3 -m etl.scenecheck ... --top 10`, VERBATIM. The judgement - the plan's M2 exit
  clause, "8 of 10 are roads you'd drive" - IS THE OWNER'S. No agent makes it here:
    rank  way_id      name                                highway        coordinate           scenic_score
       1  74344132    Topanga Canyon Boulevard            primary         34.07333,-118.58840   8  (0.7722)
       2  74344113    Topanga Canyon Boulevard            primary         34.05578,-118.58240   8  (0.7697)
       3  667514937   North Topanga Canyon Boulevard      primary         34.10243,-118.59144   8  (0.7679)
       4  358703394   Stunt Road                          tertiary        34.08832,-118.66132   8  (0.7563)
       5  456361801   North Topanga Canyon Boulevard      primary         34.12122,-118.59311   7  (0.7464)
       6  38311860    Topanga Canyon Boulevard            primary         34.14147,-118.60791   7  (0.7401)
       7  1079750100  Old Topanga Canyon Road             secondary       34.12402,-118.63121   7  (0.7367)
       8  46752395    Old Topanga Canyon Road             secondary       34.10879,-118.62923   7  (0.7314)
       9  13346012    Piuma Road                          tertiary        34.07117,-118.69433   7  (0.7306)
      10  1237332026  Fernwood Pacific Drive              tertiary        34.08117,-118.60260   7  (0.7284)
- 2026-09-19T06:05:31Z WHAT THE RUN SHOWS THAT NOBODY ASKED FOR - findings, by agent/claude-opus-5, recorded rather
  than fixed (this task is the writer, not the score):
  F1 SERVICE WAYS RANK WITH ROADS. On the first smoke window (-118.72,34.03,-118.66,34.08, 921 ways) four of the top
     ten were UNNAMED `highway=service` ways - Malibu driveways - at 6 and 7, between Piuma Road and Malibu Canyon.
     In the real window none reached the top ten, but 312,645 of the LA clip's 561,000 ways are `service`, and
     nothing in the score knows a driveway from a road. That is a term's job (T-0164's POI, or a class prior), not
     the writer's, and it is the first thing the owner will see when the window widens.
  F2 HALF THE WINDOW IS GATED: `gated=5589` of 11,740 scored ways, 47.6%, in a box that is mostly mountain - private
     drives, tracks and positive-evidence unpaved. Every one is scored 0.0 and stays in the file, which is the
     CLAUDE.md invariant working as written; it is recorded because a reviewer meeting that number cold will ask.
  F3 `points_of_interest_absent=11740` - every way. T-0164 has not landed, the assembly substitutes `POI_ABSENT` and
     flags it by name, and 0.14 of E is therefore a constant across the whole ranking above.
  F4 THE LICENCE COUNT WAS A SNAPSHOT: `tests/test_license_data.py::test_the_worldcover_credit_is_the_string_the_
     fixture_records` asserted `len(worldcover) == 2`. Adding LA's tile made it 3 and the suite went red, which is
     the guard doing its job - a WorldCover entry arriving without the recorded credit would do the same. The literal
     is re-recorded to 3 in this commit, deliberately, and the licence assertions around it are untouched.
  F5 STILL OPEN, unfixed here and named in the PR: `extract.Osmium.rel()` cannot see the shared inputs directory from
     a worktree (R7). The run mounts it read-only at the worktree's own path inside the container instead.
- 2026-09-19T06:20:44Z THE MUTATION POPULATION, by agent/claude-opus-5. `ops/mutate/scenic_tags.py` is the harness AND
  the population for the two numeric modules this task adds (the closing ruling above: osmxml is a stream copy and
  waydoc is wiring; tagwriter computes the R1 quantisation and scenecheck computes check 4's two clauses). 22
  mutations, `MIN_MUTATIONS = 22` so deleting one refuses the run, plus 2 EQUIVALENT asserted the other way round:
    `MUTATIONS: 22 caught, 0 missed, 0 skipped, of 22`
    `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2`
    `MUTATE OK  caught=22/22 equivalent_caught=0`
  THE VACUITY ARM CAUGHT ITS OWN HARNESS, which is the point of having one. Its first run reported
  `VACUITY: 21 caught, 1 missed, 0 skipped, of 22` with both test files EMPTIED - impossible, and the cause was
  `arm()` restoring every guarded file after each mutation, so the emptied tests came back after the first one. Fixed
  in commit afec6b5 (restore the SUBJECT files only); re-run: `VACUITY: 0 caught, 22 missed, 0 skipped, of 22`,
  `VACUITY PROVED`, every mutation `exit 5` - no tests ran. A harness whose clean sheet could not fail was worth
  nothing for the twenty minutes it existed, and it is recorded rather than quietly corrected.
- 2026-09-19T06:20:44Z THE ACCEPTANCE BLOCK, re-run bare at the final pre-review commit and re-quoted whole, by
  agent/claude-opus-5 (the author rule):
  (1) "RED BY NAME before code ... byte-identical (P-DATA-01) ... then green with both sha256 values quoted" -
      RED, against four docstring-only stubs, before any of the four modules had a function: `41 failed in 1.92s`,
      including `tests/test_tagwriter.py::test_the_writer_is_byte_identical_over_two_runs_of_the_same_input`.
      GREEN: `42 passed in 1.27s` over the same four files, `1134 passed in 79.03s` over the whole suite, and over
      the REAL extract, from two separate container invocations 15 minutes apart:
        06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  work/la/window-tagged-1.osm.pbf
        06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  work/la/window-tagged-2.osm.pbf
  (2) "the manifest line re-recorded the same day as the fetch" - the fetcher printed
      `verified california-osm.pbf bytes=1328857020 retrieved=2026-09-19 md5 ok` (this task's 02:54:47Z entry), and
      services/etl/inputs/manifest.yaml in THIS commit carries `  bytes: 1328857020` and `  retrieved: 2026-09-19`
      on that entry. The file was not re-fetched to produce a fresher line: Geofabrik rebuilds daily and a failed
      md5 makes the fetcher delete the 1.3 GB payload. Same-day fetches with their own lines:
      `verified byways-caltrans.geojson bytes=8764515 retrieved=2026-09-19 sha256 ok`,
      `verified byways-fhwa.geojson bytes=29545684 retrieved=2026-09-19 sha256 ok`, and
      `worldcover-n33w120.tif sha256: 61e0909a51e2e76a6f153599316753370be937d0ce150261d023006a80613385`
      (101,202,142 B), all three recorded in the manifest in this commit.
  (3) "`osmium fileinfo -e` over the output PBF ... the count of ways carrying scenic_score equals the way count the
      assembler scored" - `Number of nodes: 155208 / Number of ways: 12402 / Number of relations: 76`, bounding box
      (-119.0186574,33.9490449,-118.3400603,34.172355), 1,670,643 B. `WRITE ways=12402 scored=11740 refused=0
      gated=5589 not_a_road=662` against `ASSEMBLE ways=11740 ... null_score=0`: 11,740 = 11,740.
  (4) "the two `ops/sane` check-4 clauses printed as NUMBERS by a check that refuses on either" -
      `CHECK4 null_score=0 gated_scored=0 scored=11740 refused=0 not_a_road=662`, exit 0, over the tagged PBF read
      back with `osmium cat`. RED BY NAME first, one fixture per clause:
      `tests/test_scenecheck.py::test_a_road_with_no_score_is_counted_as_a_number_and_refuses` and
      `tests/test_scenecheck.py::test_a_motorway_with_a_score_above_zero_is_counted_as_a_number_and_refuses`,
      plus the private, unpaved and track halves of the gate clause.
  (5) "the ranked top-10 ... the judgement is not made by the agent" - printed verbatim in the 06:05:31Z entry and
      reproduced identically by the re-run at 06:15:17. THE JUDGEMENT IS THE OWNER'S.
  (6) "`cd services/etl && python -m pytest tests -rs` -> count line and zero skips; every wc -l re-measured" -
      `1134 passed in 79.03s (0:01:19)`, no `-rs` skip section at all, zero skips. Gates, each run bare:
      `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines` (exit 0);
      `P-OPS-01: 64 files, 23 required present, all modes correct` (exit 0); `QUEUE OK (186 tasks)` (exit 0);
      `PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only` (exit 0).
      `wc -l` on every touched file, re-measured here:
        111 services/etl/etl/osmxml.py          156 services/etl/etl/tagwriter.py
        151 services/etl/etl/scenecheck.py      257 services/etl/etl/waydoc.py
         77 services/etl/tests/test_osmxml.py   177 services/etl/tests/test_tagwriter.py
        128 services/etl/tests/test_scenecheck.py  118 services/etl/tests/test_waydoc.py
        296 services/etl/tests/test_dem_tiles.py   112 services/etl/tests/test_license_data.py
         53 services/etl/tests/fixtures/scenic_clip.osm.xml   248 ops/mutate/scenic_tags.py
        260 services/etl/inputs/manifest.yaml   278 queue/claimed/T-0168-...md (this file, before this entry)
      Nothing is over the 300-line cap. `ops/etl-extract` and `services/etl/Dockerfile` are in `touches:` and were
      NOT changed: the Dockerfile stays pinned because R6 rules PyOsmium out, and ops/etl-extract's own defect (F5)
      is recorded, not patched.
- 2026-09-19T07:04:53Z THE PRE-REVIEW MUTANT PASS: three mutations nobody had written down, run against the
  committed tests before the review was bought, by agent/claude-opus-5 (the owner). ONE BLOCKING SURVIVOR and
  two of one non-blocking class. All three fixed in commit 31512ef and all three now IN the population, so
  the next run of `ops/mutate/scenic_tags.py` keeps them killed.
  M1 BLOCKING - `scenecheck.counts`'s second clause `if value > 0 and is_gated(tags)` mutated to `value > 1`:
  26 passed over tests/test_tagwriter.py + tests/test_scenecheck.py, nothing red. A read-back file carrying a
  motorway at `scenic_score=1` and an `access=private` residential at 1 printed `gated_scored=0` and exited 0
  - a PBF violating the motorway/trunk/private clause of check 4 would have passed GREEN. The defect was in
  the FIXTURES, not the code: every gated way in them carries 3 (the motorway) or 7 (private, gravel, track),
  so the population's own `> 5` mutant was being killed by the 3 alone and nothing tested the boundary the
  clause states. R8 says `> 0`; the tests now say it too, at the smallest score above zero.
  M4 / M4b - `test_the_writer_is_byte_identical_over_two_runs_of_the_same_input` ran BOTH writes in ONE
  interpreter, so both shared one hash seed: `tagwriter.write` emitting ways in `sorted(held, key=hash(id))`
  order passed 26, and so did `tags_for_row`'s `FLAG_SEPARATOR.join(set(flags))`. Measured, not reasoned:
  under PYTHONHASHSEED=0..4 the six fixture ways sort into five different orders and none of them is input
  order, and the two-flag row joins both ways round (seeds 0,1,3 one order; 2,4 the other).
  WHY CROSS-PROCESS IS THE RIGHT SHAPE, ruled: P-DATA-01 is a property of the BYTES THAT SHIP, and the
  evidence it exists for is two container invocations fifteen minutes apart (the 06:05:31Z real-run entry) -
  two different processes, two different hash seeds. A test that takes both writes from one process cannot
  see any order chosen by `hash`, and therefore agrees with itself while the file disagrees with tomorrow's
  run. So the second write is now a child interpreter (`subprocess`, `PYTHONHASHSEED` 0..4, the same
  `table()` imported from this module so the two tables cannot drift), and the table carries a row with TWO
  flags, because one flag cannot show the order a set would have chosen for it.
  RED BY NAME, then green, each on the pristine tree (scratch driver in the gitignored services/etl/work/):
    `emit the ways in hash order instead of input order` ->
      FAILED tests/test_tagwriter.py::test_the_writer_is_byte_identical_over_two_runs_of_the_same_input
    `join the flags out of a set, which has no order` ->
      FAILED tests/test_tagwriter.py::test_the_writer_is_byte_identical_over_two_runs_of_the_same_input
    `only object to a gated way scoring above 1` ->
      FAILED tests/test_scenecheck.py::test_a_motorway_at_the_smallest_score_above_zero_is_counted_and_refuses
      FAILED tests/test_scenecheck.py::test_a_private_way_at_the_smallest_score_above_zero_is_counted_and_refuses
    PRISTINE -> `28 passed`, no failures.
  `MIN_MUTATIONS` 22 -> 25. NO PRODUCTION MODULE CHANGED: `tagwriter.py` (156) and `scenecheck.py` (151) are
  byte-for-byte what 4c5d02a had; this commit is two test files and the population.
- 2026-09-19T07:04:53Z THE ACCEPTANCE BLOCK RE-RUN AT THE FINAL PRE-REVIEW COMMIT (the author rule), bare and
  quoted, by agent/claude-opus-5. Everything below was measured against the tree of commit 31512ef; this
  entry is the only thing added after it, and the mutation harness's own `assert_pristine` compares its
  subjects, both emptied test files and itself to `git show HEAD:` - none of them is this file.
  (M) `python ops/mutate/scenic_tags.py`, bare, exit 0:
      `BASELINE exit=0, 25 mutations, floor 25`
      `MUTATIONS: 25 caught, 0 missed, 0 skipped, of 25`
      `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2`
      `MUTATE OK  caught=25/25 equivalent_caught=0`
      The three new ones, killed by the tests this commit adds and by name:
      `caught  emit the ways in hash order instead of input order  <- tests/test_tagwriter.py::test_the_writer_is_byte_identical_over_two_runs_of_the_same_input`
      `caught  join the flags out of a set, which has no order  <- tests/test_tagwriter.py::test_the_writer_is_byte_identical_over_two_runs_of_the_same_input`
      `caught  only object to a gated way scoring above 1  <- tests/test_scenecheck.py::test_a_motorway_at_the_smallest_score_above_zero_is_counted_and_refuses`
      `python ops/mutate/scenic_tags.py --prove-vacuity`, exit 0: `VACUITY: 0 caught, 25 missed, 0 skipped,
      of 25`, `VACUITY PROVED`, every mutation `exit 5` - no tests ran - and `git status --short` empty after
      the restore.
  (1) P-DATA-01 over the REAL extract, re-measured rather than assumed, because a correction that touches a
      measured file re-measures it. A THIRD tag pass over `work/la/window.osm.xml`, in a fresh
      `scenic-etl:latest` container (osmium 1.16.0), 18.647s: `WRITE ways=12402 scored=11740 refused=0
      gated=5589 not_a_road=662`, then `osmium cat` to PBF:
        06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  work/la/window-tagged-3.osm.pbf
        06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  work/la/window-tagged-1.osm.pbf
        06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  work/la/window-tagged-2.osm.pbf
      THE WRITER'S BYTES DID NOT CHANGE - the fix is in the tests, and the three digests are equal to each
      other and to the 06:05:31Z run's, three container invocations now instead of two.
  (4) `python3 -m etl.scenecheck work/la/window-readback.osm.xml --top 10` over the file that ships:
      `CHECK4 null_score=0 gated_scored=0 scored=11740 refused=0 not_a_road=662`, `SCENECHECK EXIT 0`, and
      the ranked ten identical to the 06:05:31Z print, Topanga 1-3, Stunt Road 4, Piuma 9, Fernwood 10. THE
      JUDGEMENT IS STILL THE OWNER'S.
  (6) `cd services/etl && python -m pytest tests -rs -o addopts=` -> `1136 passed in 105.29s (0:01:45)`, no
      `-rs` skip section at all, zero skips (1134 + the two new scenecheck boundary tests). Gates, each bare:
      `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines` (exit 0);
      `P-OPS-01: 64 files, 23 required present, all modes correct` (exit 0); `QUEUE OK (186 tasks)` (exit 0);
      `PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only` (exit 0). `wc -l` on every
      touched file, re-measured HERE and not carried forward:
        210 services/etl/tests/test_tagwriter.py   148 services/etl/tests/test_scenecheck.py
        275 ops/mutate/scenic_tags.py              156 services/etl/etl/tagwriter.py
        151 services/etl/etl/scenecheck.py         111 services/etl/etl/osmxml.py
        257 services/etl/etl/waydoc.py              77 services/etl/tests/test_osmxml.py
        118 services/etl/tests/test_waydoc.py      296 services/etl/tests/test_dem_tiles.py
        112 services/etl/tests/test_license_data.py  53 services/etl/tests/fixtures/scenic_clip.osm.xml
        260 services/etl/inputs/manifest.yaml      337 queue/claimed/T-0168-...md (this file, before this entry)
      Nothing is over the 300-line cap; `ops/mutate/scenic_tags.py` grew 248 -> 275 and stays one file, so the
      population table is NOT split out. Acceptance (2), (3) and (5) are measurements of inputs and of a run
      this commit does not touch and are quoted whole in the 06:20:44Z entry; nothing in this commit changes
      an input, a count line or the ranking, and (1) and (4) above re-measure the two that could have moved.
- 2026-09-19T07:04:53Z STILL OPEN, updated by agent/claude-opus-5 (items 1-6 stand as the 06:20:44Z entry and
  the PR body state them; nothing here closes one). ADDED:
  7. THE TWO NON-NUMERIC MODULES STILL SHIP NO POPULATION, and the mutant pass is why that is now worth
     re-stating: `osmxml.py` was ruled a stream copy and `waydoc.py` wiring, and both rulings stand - but
     every one of the three survivors above lived in how the TESTS were written, not in the arithmetic, and
     `osmxml.Writer` is where the byte order those tests are about is actually produced. P-DATA-01 now pins
     it from the outside, across processes, at fixture scale plus three real-extract container runs; CI has
     no extract and cannot run the second half. A population for `osmxml.py` is a later task, not this one.
