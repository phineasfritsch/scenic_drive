---
id: T-0189
title: dem, landcover, oracle and extract read the shared inputs directory - the silent None from a per-worktree path is a refusal by name
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T03:45:22Z
lease_expires_at: 2026-09-19T09:45:22Z
worktree: .worktrees/T-0189
branch: task/T-0189
exclusive: []
touches: [services/etl/etl/dem.py, services/etl/etl/landcover.py, services/etl/etl/oracle.py, services/etl/etl/extract.py, services/etl/tests/]
pins_affected: []
reviewer: agent/rv1-pr108
depends_on: [T-0177]
verify: [ops/test, ops/check-pins]
acceptance:
  - "dem.py, landcover.py, oracle.py and extract.py resolve their inputs directory through fetch.resolve_inputs_dir (SCENIC_ETL_INPUTS, else the main checkout's services/etl/inputs/ from a worktree path), never ROOT / 'inputs' - RED BY NAME first: a test that runs dem.sample_tile from a fake worktree path with the tile present only in the shared directory and asserts a sample, red today (None), then green"
  - "a missing tile or land-cover raster is a REFUSAL that names the path (the way extract.py already refuses), never a silent None list - RED by name on a test that today gets [None] * n back; the 'absent means absent' semantics for a point OUTSIDE every served region stay as they are (T-0142) and are asserted separately"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From agent/rv1-pr104's PASS entry on PR #104 (T-0177) - the recordable it asked to file before any sampling runs
from a worktree. T-0177's resolver reaches etl.fetch only (its ruling R3: the four consumers were outside its
touches). extract.py refuses loudly when its source is missing; dem.sample_tile returns `[None] * len(points)`
when the tile file is absent and landcover.sample_codes `continue`s past a missing raster - neither names a path.
Both still compute a per-worktree `ROOT / "inputs"`, while the California extract and the four LA 3DEP tiles
exist ONLY in the main checkout's shared directory (T-0169/T-0142). T-0168 will run from a worktree and sample
LA terrain: without this it gets zeroed terrain and a green suite.

## Log
- 2026-09-19T03:45:19Z filed by agent/claude-fable-5-1 from PR #104's review; ready/ with its acceptance block; T-0168 now depends on it. Not started.
- 2026-09-19T03:45:22Z claimed by agent/claude-opus-5; lease until 2026-09-19T09:45:22Z
- 2026-09-18 agent/claude-opus-5 (owner, author). RULINGS FIRST, before any code.

  **R1 - one resolver call per module, at IMPORT time.** T-0177 chose import time for `fetch.DEST`, and a
  second convention in the four consumers would be a second answer to the same question. So each module
  keeps a module-level `INPUTS` (oracle: `KMZ`) assigned from `fetch.resolve_inputs_dir(ROOT)` once, and
  `tile_path`/`sample_tile`/`sample_codes`/`main` read that attribute. Per-call resolution was rejected for
  a concrete reason, not a stylistic one: every sampling test in this suite already says
  `monkeypatch.setattr(dem, "INPUTS", tmp_path)` (15 occurrences in `tests/test_dem.py`, 4 in
  `tests/test_landcover_sampling.py`), and a `tile_path` that re-resolved from `ROOT` per call would ignore
  all of them - the patch would still "work" in the sense of not erroring, and every one of those tests
  would quietly start reading the real inputs directory. A resolution that per-call code can silently
  bypass is how this defect got here in the first place.
  THE COROLLARY THE BRIEF ASKS FOR: a test that monkeypatches the ENV VAR must still work, and with
  import-time resolution setting `SCENIC_ETL_INPUTS` after import changes nothing. Ruled: such a test
  re-imports. `tests/test_inputs_dir_consumers.py` ships the `reload_with_inputs` fixture, which sets the
  variable and calls `importlib.reload`; reload re-executes the module in its OWN namespace and returns the
  SAME object, so no other test module is left holding a stale import, and the fixture reloads once more at
  teardown to put the real directory back. That is why the full suite is run bare below rather than only
  the touched files - a reload fixture that leaked would show up as a failure somewhere else.

  **R2 - what "absent" means after this task.** Two things were one value and are now two:
  * a tile or raster file MISSING from the resolved directory is a REFUSAL naming the path -
    `FileNotFoundError("dem: tile n38w123 is missing at <path> - run ops/etl-fetch-inputs")`, and the
    landcover equivalent. This is a fetch that did not happen. It is fixable, and it now says how.
  * a point OUTSIDE every served region's tile set is still ABSENT: `None`, silently, without reaching
    GDAL. That is T-0142's semantics and it is geography - there is no path to name and no fetch that would
    help. `dem.group_by_tile` keeps those points under the `None` key and `sample` skips them, which is
    untouched here; landcover's `tile_for` returns `""` for NaN and `sample_codes` still `continue`s on it.
  Both are asserted separately, in `TestAMissingPayloadIsARefusalThatNamesThePath` and
  `TestAbsenceThatIsGeographyStaysAbsence`, so a later widening of the refusal over the second cannot pass.

  **R3 - the manifest stays per-checkout; only the PAYLOAD moves.** `oracle.py`'s `KMZ` now resolves through
  the resolver, and `oracle.pinned_digest`'s default (`ROOT / "inputs" / "manifest.yaml"`, oracle.py:47)
  deliberately does not. manifest.yaml is TRACKED, and a task that edits its own manifest must be checked
  against that edit rather than against the main checkout's copy - T-0177's R2, and
  `test_inputs_dir.py::test_the_manifest_stays_in_this_checkout` already pins the same rule for
  `fetch.MANIFEST`. `test_the_oracles_manifest_stays_in_this_checkout` pins it for oracle.
  Same reasoning, recorded here because it is a second judgement of the same kind: `extract.WORK` stays
  `ROOT / "work"`. A work directory is this run's output, not a 1.2 GB download worth sharing, and two
  worktrees extracting different `region.json` edits into one `work/sfbay` would overwrite each other.

  **R4 - the CI job that has no payloads at all must stay green.** Read the tests that rely on today's
  silent `None` before changing anything: there are exactly two, and every other sampling test already
  writes a tile file into its `tmp_path` first (`b"not really a tiff"`). The two are
  `test_dem.py::TestSampling::test_a_missing_tile_file_yields_misses_rather_than_raising` and
  `test_landcover_sampling.py::TestWhereItLooksForATile::test_a_missing_tile_file_is_a_miss_rather_than_a_crash`.
  Both are rewritten in place to assert the named refusal - they are the RED-BY-NAME evidence for
  acceptance (2), not collateral. Nothing else in `services/etl/tests/` calls `sample_tile`, `sample`,
  `sample_codes` or `tile_path` without a file on disk (`grep -rn "sample_tile\|sample_codes\|tile_path\|
  dem.sample\|landcover.sample" tests/`), so no fixture raster has to be shipped and CI does not go red.

  **R5 - the "tiny GeoTIFF" the Brief allows a smaller honest alternative for.** Not needed, and shipping
  one would have been the dishonest option. `sample_tile` and `sample_codes` only ever ask
  `path.is_file()`; the value comes from the INJECTED `runner`, and no code under test opens the file.
  `tests/test_landcover_sampling.py`'s own `tiles` fixture already says so out loud ("Tile files that exist
  and are not rasters. Nothing opens them"). So the new tests write `b"not really a tiff"` into the shared
  directory, exactly as the existing ones do, and no library that can author a GeoTIFF is added to the tree.
  What is under test is WHICH directory was looked in, and that is fully observable this way.

  **R6 - the refusal's shape: a library raises, a CLI exits.** The Brief names extract.py:165 as the pattern
  to copy, and extract.py is a `main()` - it prints to stderr and returns 2, which is right for a command
  and wrong for `dem.sample_tile`, whose caller is the pipeline. So the library layer raises
  `FileNotFoundError` naming the path, and `extract.main` keeps its print-and-return-2 unchanged; what moves
  in extract.py is only WHERE it looks. Builtin `FileNotFoundError` rather than a new exception class,
  because the class would have had to live in a module all four import and `etl/fetch.py` is outside this
  task's `touches:` - and two module-local copies of one error type is two answers to one question (R1).

  **R7 - merge order with PR #106 (T-0142), which is NOT on main.** Read
  `git show origin/task/T-0142:services/etl/etl/dem.py` before designing. T-0142 rewrites the TILE-SET
  logic (`UNSERVED`, `tiles_for_region`, `region_ids`, `served_tiles`, `_SERVED_CACHE`, and a `tiles=`
  parameter threaded through `tile_for`/`group_by_tile`/`sample`/`sample_smoothed`). This task touches
  NEITHER of those: only the `INPUTS` assignment and `sample_tile`'s absent-file branch, both of which are
  byte-identical on the two branches today. Verified rather than asserted, with a three-way trial merge of
  dem.py alone (base = main 3911650, ours = this branch, theirs = origin/task/T-0142):
  `git merge-file -p ours base theirs` -> exit 1, `grep -c "<<<<<<<"` -> **1**, and the one conflict is the
  import line alone:
  ```
  <<<<<<< ours.py
  from . import fetch
  =======
  from . import region as rg
  >>>>>>> theirs.py
  ```
  Both branches insert one import at the same anchor. The resolution is to KEEP BOTH LINES; the `INPUTS`
  paragraph, the `sample_tile` refusal and every one of T-0142's tile-set changes merge clean around it.
  Contorting dem.py's import order to dodge two adjacent lines would leave a permanent oddity in the file
  to serve a temporary branch state, so it is recorded (STILL OPEN below) instead. T-0142's new
  `tests/test_dem_tiles.py` has exactly one sampling call,
  `dem.sample([(34.07, -118.45)], runner=None, tiles=frozenset()) == [None]` (line 160), which is the
  no-tile-covers-this-point path (R2's second half) and not the missing-file path, so it stays green under
  the merge. landcover.py, oracle.py and extract.py are not touched by T-0142 at all
  (`git diff --stat 3911650...origin/task/T-0142 -- services/etl`: dem.py, inputs/manifest.yaml,
  regions/la/region.json, tests/test_dem_tiles.py).

- 2026-09-18 RED BY NAME, before the modules were touched. 16 failing, 3 passing, from the worktree
  `.worktrees/T-0189`. `cd services/etl && python -m pytest tests/test_inputs_dir_consumers.py
  tests/test_dem.py::TestSampling::test_a_missing_tile_file_is_a_refusal_naming_the_path
  "tests/test_landcover_sampling.py::TestWhereItLooksForATile::test_a_missing_tile_file_is_a_refusal_naming_the_path"
  -rf --tb=no` -> exit 1:
  ```
  FFFFFFFF.FFFFFF..FF                                                      [100%]
  =========================== short test summary info ===========================
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_inputs_directory_is_never_inside_a_worktree[etl.dem]
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_inputs_directory_is_never_inside_a_worktree[etl.landcover]
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_inputs_directory_is_never_inside_a_worktree[etl.extract]
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_oracle_kmz_is_never_inside_a_worktree
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_inputs_directory_is_the_resolvers_answer[etl.dem]
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_inputs_directory_is_the_resolvers_answer[etl.landcover]
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_inputs_directory_is_the_resolvers_answer[etl.extract]
  FAILED tests/test_inputs_dir_consumers.py::TestEveryConsumerResolvesRatherThanComputing::test_the_oracle_kmz_lives_in_the_resolved_directory
  FAILED tests/test_inputs_dir_consumers.py::TestAPayloadOnlyInTheSharedDirectoryIsRead::test_dem_samples_a_tile_that_is_not_under_its_own_root
  FAILED tests/test_inputs_dir_consumers.py::TestAPayloadOnlyInTheSharedDirectoryIsRead::test_landcover_samples_a_raster_that_is_not_under_its_own_root
  FAILED tests/test_inputs_dir_consumers.py::TestAPayloadOnlyInTheSharedDirectoryIsRead::test_extract_defaults_its_source_to_the_shared_directory
  FAILED tests/test_inputs_dir_consumers.py::TestAMissingPayloadIsARefusalThatNamesThePath::test_dem_refuses_a_tile_that_is_not_on_disk
  FAILED tests/test_inputs_dir_consumers.py::TestAMissingPayloadIsARefusalThatNamesThePath::test_dems_whole_sample_refuses_too
  FAILED tests/test_inputs_dir_consumers.py::TestAMissingPayloadIsARefusalThatNamesThePath::test_landcover_refuses_a_raster_that_is_not_on_disk
  FAILED tests/test_dem.py::TestSampling::test_a_missing_tile_file_is_a_refusal_naming_the_path
  FAILED tests/test_landcover_sampling.py::TestWhereItLooksForATile::test_a_missing_tile_file_is_a_refusal_naming_the_path
  16 failed, 3 passed in 0.96s
  ```
  The three that passed are the ones that MUST pass before and after: the two absence-is-geography tests
  and `test_the_oracles_manifest_stays_in_this_checkout` (R3 - the manifest was already right).
  Named failure text, quoted from the `--tb=line` run of the same selection:
  ```
  E   assert [None] == [123.0]                       # dem, tile only in the shared directory
  E   assert [None] == [10]                          # landcover, raster only in the shared directory
  E   Failed: DID NOT RAISE FileNotFoundError        # x5, the missing-tile refusals
  C:\...\test_inputs_dir_consumers.py:95: AssertionError: WindowsPath('C:/Users/phineasf/Documents/GitHub/scenic_drive/.worktrees/T-0189/services/etl/inputs/vermont-curvature.kmz')
  E   AssertionError: assert '...\\test_extract_defaults_its_sour0\\services\\etl\\inputs\\california-osm.pbf' in 'extract: C:\\Users\\phineasf\\Documents\\GitHub\\scenic_drive\\.worktrees\\T-0189\\services\\etl\\inputs\\california-osm.pbf is missing - run ops/etl-fetch-inputs first\n'
  ```
  That last line is the whole task in one assertion: the refusal was already loud and was naming a
  directory inside `.worktrees/T-0189` that the California extract has never been in.

- 2026-09-18 MUTATION POPULATION. This task changes existing modules and adds no new numeric module, so it
  ships no new population under `ops/mutate/` (CLAUDE.md: a NEW numeric module ships one). The mutants this
  change introduces belong to the populations T-0186 and T-0187 are filed to build, and are recorded here
  so those tasks can pick them up: (m1) `not path.is_file()` -> `path.is_file()` in `dem.sample_tile`;
  (m2) the same in `landcover.sample_codes`; (m3) `if not name: continue` -> `if name: continue` in
  `sample_codes`; (m4) `fetch.resolve_inputs_dir(ROOT)` -> `ROOT / "inputs"` in each of dem, landcover,
  extract and oracle (four mutants, one per module); (m5) dropping the path from either refusal message.
  Each is killed by a test in this change: m1/m2 by the two rewritten `..._is_a_refusal_naming_the_path`
  tests, m3 by `test_a_nan_point_is_none_rather_than_a_refusal`, m4 by
  `test_the_inputs_directory_is_the_resolvers_answer` / `test_the_oracle_kmz_lives_in_the_resolved_directory`,
  m5 by the `str(path) in str(e.value)` assertion each refusal test carries.
- 2026-09-18 ACCEPTANCE BLOCK RE-RUN AND RE-QUOTED IN FULL at the final pre-review commit, from
  `.worktrees/T-0189` on `task/T-0189`, every command bare (no pipe to swallow an exit status).

  **(1) dem.py, landcover.py, oracle.py and extract.py resolve their inputs directory through
  `fetch.resolve_inputs_dir`, never `ROOT / "inputs"`; RED BY NAME first.**
  RED (before the modules were touched, quoted in full in the entry above): 8 of the 16 failures are this
  half - `test_the_inputs_directory_is_never_inside_a_worktree[etl.dem|etl.landcover|etl.extract]`,
  `test_the_oracle_kmz_is_never_inside_a_worktree`,
  `test_the_inputs_directory_is_the_resolvers_answer[etl.dem|etl.landcover|etl.extract]` and
  `test_the_oracle_kmz_lives_in_the_resolved_directory`; plus the three end-to-end ones,
  `test_dem_samples_a_tile_that_is_not_under_its_own_root` (`assert [None] == [123.0]` - the Brief's "red
  today (None)"), `test_landcover_samples_a_raster_that_is_not_under_its_own_root` (`assert [None] == [10]`)
  and `test_extract_defaults_its_source_to_the_shared_directory`, whose failure named
  `.worktrees/T-0189/services/etl/inputs/california-osm.pbf` - a directory the extract has never been in.
  GREEN now. `cd services/etl && python -m pytest tests/test_inputs_dir_consumers.py tests/test_dem.py
  tests/test_landcover_sampling.py tests/test_inputs_dir.py tests/test_oracle_report.py
  tests/test_oracle_select.py -rs` -> exit 0:
  ```
  ........................................................................ [ 69%]
  ................................                                         [100%]
  104 passed in 3.23s
  ```
  `tests/test_inputs_dir.py` is in that selection on purpose: T-0177's own resolver tests still pass
  unchanged, so this task moved the CONSUMERS and not the rule.

  **(2) a missing tile or land-cover raster is a REFUSAL that names the path, never a silent None list; the
  "absent means absent" semantics for a point outside every served region stay as they are (T-0142) and are
  asserted separately.**
  RED (quoted above): `Failed: DID NOT RAISE FileNotFoundError` five times -
  `test_dem_refuses_a_tile_that_is_not_on_disk`, `test_dems_whole_sample_refuses_too`,
  `test_landcover_refuses_a_raster_that_is_not_on_disk`, plus the two existing tests rewritten in place,
  `tests/test_dem.py::TestSampling::test_a_missing_tile_file_is_a_refusal_naming_the_path` and
  `tests/test_landcover_sampling.py::TestWhereItLooksForATile::test_a_missing_tile_file_is_a_refusal_naming_the_path`.
  GREEN now, in the 104-passed run above. The refusals as they read:
  `dem: tile n38w123 is missing at <resolved>/3dep-n38w123.tif - run ops/etl-fetch-inputs` and
  `landcover: tile N36W123 is missing at <resolved>/worldcover-n36w123.tif - run ops/etl-fetch-inputs`;
  each test asserts `str(path) in str(e.value)`, so dropping the path from either message is a failure.
  The separate half PASSED BEFORE AND AFTER, which is the point: `TestAbsenceThatIsGeographyStaysAbsence`
  - `test_a_point_no_region_serves_is_none_and_never_reaches_gdal` (`dem.sample([(0.0, 0.0), (10.0, 10.0)])
  == [None, None]` with `runner.calls == []`) and `test_a_nan_point_is_none_rather_than_a_refusal` for both
  dem and landcover. Two of the three tests that passed in the red run are these.

  **(3) `cd services/etl && python -m pytest tests -rs` -> count line and zero skips at the final commit.**
  Bare, exit 0:
  ```
  ........................................................................ [ 95%]
  ...................................................                      [100%]
  1059 passed in 111.64s (0:01:51)
  ```
  Zero skips: `grep -c "SKIPPED\|short test summary"` over that output -> `0`, i.e. `-rs` printed no
  short-summary section at all. Where 1059 comes from, derived from the quoted runs rather than asserted:
  the red selection collected 19 (16 failed + 3 passed) and was `tests/test_inputs_dir_consumers.py` plus
  two named tests, so the new file contributes 17 collected tests (its two three-way parametrisations count
  as three each). The two rewritten tests are REPLACEMENTS, not additions - nothing was deleted - so the
  suite went 1042 -> 1059, +17, 0 removed.

  OTHER GATES at this commit. `bash ops/lib/check-line-cap` -> exit 0,
  `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines` - it covers
  Swift only (T-0058 is the open task for Python), so every touched Python file is measured by hand here:
  `wc -l` -> `209 etl/dem.py`, `283 etl/landcover.py`, `189 etl/oracle.py`, `204 etl/extract.py`,
  `173 tests/test_inputs_dir_consumers.py`, `237 tests/test_dem.py`, `155 tests/test_landcover_sampling.py`
  - largest 283, under the 300-line cap. dem.py is 209 against T-0142's 258 on its own branch; the change
  is small on purpose (R7).
  `bash ops/queue-check` -> exit 0, `QUEUE OK (183 tasks)`.
  `bash ops/check-pins --source-only` -> exit 0,
  `PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only`. Run against the source as
  committed; the only change after it was this Log append, which touches no source file.
  `bash ops/test` and a full `bash ops/check-pins` were NOT run - out of scope for this task per its
  instructions, and the Linux/iOS halves are untouched by it. `state: claimed` and `reviewer: null` stand.

- 2026-09-18 STILL OPEN, for the reviewer and for whoever merges.
  1. **MERGE ORDER WITH PR #106 (T-0142).** T-0142's dem.py is not on main. A three-way trial merge
     (`git merge-file -p ours base theirs`, base = main 3911650) leaves EXACTLY ONE conflict in dem.py, the
     two adjacent import lines - ours `from . import fetch`, theirs `from . import region as rg` - and the
     resolution is to KEEP BOTH. Everything else merges clean: this task's `INPUTS` paragraph and
     `sample_tile` refusal on one side, T-0142's `UNSERVED`/`tiles_for_region`/`served_tiles`/`tiles=`
     thread on the other. Merging either PR first is fine; the second one merged resolves that hunk.
     T-0142's `tests/test_dem_tiles.py:160`
     (`dem.sample([(34.07, -118.45)], runner=None, tiles=frozenset()) == [None]`) is the
     no-tile-covers-this-point path and stays green under this change - it is NOT the missing-file path.
  2. **`queue/README.md` now contradicts the code.** Its "Still per-worktree" paragraph (lines ~117-120)
     says `etl/extract.py`, `etl/dem.py`, `etl/landcover.py` and `etl/oracle.py` each compute their own
     `ROOT / "inputs"` and tells the reader to pass `ops/etl-extract --input <main checkout>/...`. That is
     false as of this commit and the workaround is no longer needed. `queue/README.md` is outside this
     task's `touches:` and was left alone deliberately; it needs a one-paragraph follow-up.
  3. **`ops/etl-extract` still execs inside the current checkout.** Only the INPUTS resolution moved, not
     the wrapper, so the `--input` escape hatch keeps working for anyone who wants a different payload.
     Nothing depends on the old default any more, but the wrapper was not in `touches:` either.
  4. **No payload was fetched or sampled by this task.** Every test here writes `b"not really a tiff"` and
     injects the runner (R5), so nothing in this change has been exercised against a real 3DEP tile or the
     1.2 GB California extract. T-0168 is the task that will do that, and it is the first real test of
     whether the resolved directory is the one the payloads are actually in on this box.
  5. **`landcover.py` is at 283 of 300 lines.** The next change to it should expect to split the file.
- 2026-09-19T04:40:25Z REVIEW PASS by agent/rv1-pr108 (reviewer, not the owner). PR #108, head 2f0b6da,
  base main, from a detached worktree `.worktrees/rv1-pr108` at that sha. No blocking finding; three
  recordables below. Nothing in the branch was changed by this review.

  **Shape.** `git diff main...2f0b6da --stat` -> 8 files, 471 insertions, 14 deletions: the four etl modules
  (dem 20, extract 6, landcover 22, oracle 8), three test files (test_inputs_dir_consumers.py 173 new,
  test_dem.py 9, test_landcover_sampling.py 10) and the task file. The task-file diff is APPEND-ONLY:
  `git diff main...2f0b6da -- queue/ | grep -c "^-[^-]"` -> `0`, `--stat` -> `237 +++...`, 34 -> 271 lines.

  **Acceptance re-run, bare, in this worktree.** `cd services/etl && python -m pytest tests -rs -o addopts=`
  -> `1059 passed in 107.41s (0:01:47)`, exit 0, no short-summary section, i.e. zero skips - the Log's
  count line reproduced exactly. The author's red-by-name trio,
  `python -m pytest tests/test_inputs_dir_consumers.py
  tests/test_dem.py::TestSampling::test_a_missing_tile_file_is_a_refusal_naming_the_path
  "tests/test_landcover_sampling.py::TestWhereItLooksForATile::test_a_missing_tile_file_is_a_refusal_naming_the_path"
  -rs -o addopts=` -> `19 passed in 1.23s`, which is the 16+3 of the red run, so the new file's 17 collected
  tests are the +17 the Log derives. `bash ops/lib/check-line-cap` -> exit 0,
  `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines`.
  `bash ops/queue-check` -> exit 0, `QUEUE OK (183 tasks)`. `bash ops/check-pins --source-only` -> exit 0,
  `PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only`. Every `wc -l` the Log quotes
  re-measured and identical: `209 etl/dem.py`, `283 etl/landcover.py`, `189 etl/oracle.py`,
  `204 etl/extract.py`, `173 tests/test_inputs_dir_consumers.py`, `237 tests/test_dem.py`,
  `155 tests/test_landcover_sampling.py`.

  **Five mutants of the reviewer's own**, each applied ALONE by literal replacement and restored with
  `git checkout --` (`git status --short` empty after each), run against
  `tests/test_inputs_dir_consumers.py tests/test_dem.py tests/test_landcover_sampling.py`, baseline
  `75 passed`. The product question was "from a worktree, can LA terrain be sampled as zero/None with the
  suite green?".
  1. `reload_with_inputs` made a NO-OP (`return module` instead of `importlib.reload(module)`) -> KILLED,
     `3 failed`: `test_dem_samples_a_tile_that_is_not_under_its_own_root`,
     `test_landcover_samples_a_raster_that_is_not_under_its_own_root`,
     `test_extract_defaults_its_source_to_the_shared_directory`. The fixture guards itself; a fixture that
     stopped reloading takes its own tests red rather than passing vacuously (R1's corollary holds).
  2. `landcover`'s refusal branch widened back to the pre-task `path = tile_path(name) if name else None;
     if not path or not path.is_file(): continue` -> KILLED, `2 failed`:
     `test_landcover_refuses_a_raster_that_is_not_on_disk` and
     `test_landcover_sampling.py::TestWhereItLooksForATile::test_a_missing_tile_file_is_a_refusal_naming_the_path`.
     `test_a_nan_point_is_none_rather_than_a_refusal` stayed GREEN under it, so R2's two halves really are
     separable and the geography half does not ride on the refusal branch.
  3. dem's refusal message with the path REMOVED (`f"dem: tile {name} is missing - run ops/etl-fetch-inputs"`)
     -> KILLED, `3 failed`: `test_dem_refuses_a_tile_that_is_not_on_disk`, `test_dems_whole_sample_refuses_too`,
     `test_dem.py::TestSampling::test_a_missing_tile_file_is_a_refusal_naming_the_path`. "names the path" is
     an assertion, not a wish.
  4. `oracle.KMZ = ROOT / "inputs" / "vermont-curvature.kmz"` (per-checkout again; the pre-review pass
     mutated only dem and landcover) -> KILLED HERE, `2 failed`:
     `test_the_oracle_kmz_is_never_inside_a_worktree`, `test_the_oracle_kmz_lives_in_the_resolved_directory`.
     RECORDABLE (a): the pass's OBSERVATION extended and measured. A plain-checkout copy of `services/etl`
     at `.artifacts/rv1-plain/` (no `.worktrees` component, so `resolve_inputs_dir` returns `ROOT/"inputs"`
     - CI's layout) runs the same mutant `75 passed`: a SURVIVOR in CI. The equivalent mutant on `extract`
     was run in that same plain copy and is KILLED there, `1 failed`
     (`test_extract_defaults_its_source_to_the_shared_directory`), and dem/landcover have the same
     env-planting tests. `oracle.KMZ` is the one of the four with NO `reload_with_inputs` test, so it is
     the one whose resolver binding CI cannot see. Not blocking - in a plain checkout the two expressions
     are the same directory, so the mutant is equivalent there and differs only in a worktree, where it is
     red by name - but a fourth `reload_with_inputs` case for oracle would close it.
  5. `oracle.pinned_digest`'s default moved to the shared directory
     (`path = manifest or (fetch.resolve_inputs_dir(ROOT) / "manifest.yaml")`, i.e. R3's line deleted)
     -> SURVIVOR: `python -m pytest tests/test_inputs_dir_consumers.py tests/test_dem.py
     tests/test_landcover_sampling.py tests/test_oracle_report.py tests/test_oracle_select.py
     tests/test_inputs_dir.py -o addopts= -q` -> `104 passed`, from the worktree. RECORDABLE (b):
     `test_the_oracles_manifest_stays_in_this_checkout` asserts
     `pinned_digest(name) == pinned_digest(name, oracle.ROOT / "inputs" / "manifest.yaml")`, a comparison of
     two DIGESTS, so it can only go red when the two manifest files differ in CONTENT - which is exactly the
     case R3 exists for and exactly the case no test creates. T-0177's own pin is anchored on the PATH
     (`test_inputs_dir.py:68`, `assert fetch.MANIFEST == fetch.ROOT / "inputs" / "manifest.yaml"`) and
     would be red under the same edit. The oracle pin should be anchored the same way, or plant two
     different manifests. R3's RULING is right and matches T-0177's R2; it is the check for it that has
     never been seen red.

  **R1 judged, against the next consumer rather than in the abstract.** Import-time binding is the right
  call and it fires for T-0168. From this worktree, with `SCENIC_ETL_INPUTS` unset,
  `python -c "from etl import dem, landcover, extract, oracle, fetch; print(...)"` gives
  `dem.INPUTS`, `landcover.INPUTS`, `extract.INPUTS` and `fetch.DEST` all
  `C:/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/inputs`, `oracle.KMZ` that directory's
  `vermont-curvature.kmz`, while `extract.WORK` and `fetch.MANIFEST` stay under
  `.worktrees/rv1-pr108/services/etl` - R3's line exactly. `ls` of the resolved directory:
  `3dep-n34w118.tif 3dep-n34w119.tif 3dep-n35w118.tif 3dep-n35w119.tif california-osm.pbf manifest.yaml`,
  so the four LA tiles and the extract are where the resolver points. Per-call resolution would indeed have
  silently bypassed the 19 `monkeypatch.setattr(module, "INPUTS", ...)` tests; R1's reason is the real one.
  RECORDABLE (c), the cost of the choice: a process that sets `SCENIC_ETL_INPUTS` AFTER importing `etl.dem`
  gets the old directory with no error and nothing says so. Low risk (the variable is a box-level setting)
  and cheaper than the alternative, but it is a second thing only the convention protects.

  **The product question, answered.** From a worktree, an LA point STILL comes back a silent `None` on this
  branch - and not for the reason this task fixes. `python -c "from etl import dem; print(dem.tile_for(34.07,
  -118.45)); print(dem.group_by_tile([(34.07,-118.45)])); print(dem.sample([(34.07,-118.45)], runner=...))"`
  -> `None`, `{None: [0]}`, `[None]`: `dem.TILES` is still sfbay's eight, so LA is the no-tile-covers-this-
  point path (R2's second half), which this task deliberately preserves and PR #106 (T-0142) is the task
  that changes. That is correct scoping, not a defect - the Log's STILL OPEN 4 says as much - but it means
  merging #108 alone does NOT make LA sampling work, and main commit 712f3b0 has already made T-0142 a hard
  prerequisite of T-0168.

  **Not findings, confirmed as the Log describes them.** STILL OPEN 1: `queue/README.md:117-120`'s "Still
  per-worktree" paragraph reads as quoted and is now false - outside `touches:`, a follow-up. STILL OPEN 2/3
  likewise. One merge note for whoever merges: `origin/main` has moved past the 3911650 this PR measured
  against (db2b93a merged PR #102 / T-0146, adding `services/etl/etl/assemble.py`,
  `tests/test_assemble.py`, `tests/test_assemble_wiring.py` and a fixture - new files only, no overlap with
  the four modules), so the post-merge suite count will exceed 1059.

  **Sign-off.** `git status --short` in `.worktrees/rv1-pr108` empty, HEAD == `origin/task/T-0189` ==
  2f0b6da. `reviewer: agent/rv1-pr108`, `state: done`, `git mv` to `queue/done/`.
