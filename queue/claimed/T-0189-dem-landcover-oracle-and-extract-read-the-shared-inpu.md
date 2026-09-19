---
id: T-0189
title: dem, landcover, oracle and extract read the shared inputs directory - the silent None from a per-worktree path is a refusal by name
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T03:45:22Z
lease_expires_at: 2026-09-19T09:45:22Z
worktree: .worktrees/T-0189
branch: task/T-0189
exclusive: []
touches: [services/etl/etl/dem.py, services/etl/etl/landcover.py, services/etl/etl/oracle.py, services/etl/etl/extract.py, services/etl/tests/]
pins_affected: []
reviewer: null
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
