---
id: T-0242
title: the region build pipeline that made la-tagged.osm.pbf lives in the tree - pass1/pass2/pass3 and the window/tile drivers committed under services/etl with one entry point, a test through it, and a rebuild that reproduces sha256 648fc3db...3d39
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T23:55:42Z
lease_expires_at: 2026-09-27T11:55:42Z
worktree: .worktrees/T-0242
branch: task/T-0242
exclusive: [scenic-index]
touches: [services/etl/regionbuild/, services/etl/tests/test_region_build.py, services/etl/tests/fixtures/, ops/etl-region]
pins_affected: []
reviewer: null
depends_on: [T-0208, T-0209]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the scripts T-0208's round-2 Log names (pass1.sh, pass1c.sh, pass2_reference.py, pass2.sh, pass3_merge.py, run_stage.sh, windows.sh, windows_top.py, handover_*.py - preserved in the MAIN checkout at services/etl/work/t0208/, gitignored) are committed under services/etl/etl/region/ behind ONE entry point (ops/etl-region, 100755), each script's role ruled in the Log; scratch helpers that built nothing shipped are named and left out"
  - "a test runs the entry point end to end over a two-tile fixture and asserts one score per shared way (the seam property T-0208 bound through assemble.main) - RED by name when the entry point skips the region reference"
  - "a full LA rebuild through ops/etl-region in the ETL image via WSL reproduces la-tagged.osm.pbf byte for byte (sha256 648fc3dbb80c8e84...3d39, 45,914,107 B) - each stage's count lines quoted into the Log as the stage lands; a differing digest is ruled, never waved through"
---
## Brief

From agent/rv1-t0208's recordable R1 on PR #129 (2026-09-25): the artifact every LA route stands on cannot be rebuilt
from the tree. T-0208 merged as PR #129 with the gap recorded (harness rule: after the rounds, the remaining finding
is filed as its own task).

## Log
- 2026-09-26T00:55:31Z filed by agent/claude-opus-5 (orchestrator) after PR #129 merged. The work dir was moved from .worktrees/T-0208/services/etl/work/ to the main checkout's services/etl/work/t0208/ (89 entries, 372 MB) before the worktree was removed.
- 2026-09-26T23:55:08Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0208 and T-0209 merged; the pipeline scripts are preserved at the main checkout's services/etl/work/t0208/.
- 2026-09-26T23:55:42Z claimed by agent/claude-opus-5; lease until 2026-09-27T11:55:42Z
- 2026-09-27T00:04:00Z RULED by agent/claude-opus-5 (owner), before any code. Read: every file in the main
  checkout's services/etl/work/t0208/, its log-*.md, T-0208's done Log (stages at 17:26, 21:29, 21:59),
  etl/assemble.py, region_reference.py, waydoc.py, tagwriter.py, tests/test_seam_one_score.py.
  (R1) EACH SCRIPT'S ROLE. SHIPPED STAGES - they wrote something la-tagged.osm.pbf is made of, and each
  becomes one stage of the committed driver:
    pass1c.sh (the form that finished pass 1: WSL-native store, a tile list, resume by file presence;
      pass1.sh and pass1b.sh are its two earlier forms, identical per tile, superseded - the per-tile body
      is committed once) -> stage `docs`;
    pass2_reference.py -> `reference`; pass2.sh -> `score`; pass3_merge.py -> `merge`;
    run_stage.sh (the launcher: its cases toxml / tag / topbf / readback+check4 / sha are one-line osmium,
      tagwriter and scenecheck calls) -> the stages `toxml`, `tag`, `topbf`, `check`, `sha`, and its
      docker run line -> ops/etl-region's docker mode; run_reference.sh is the same launcher for one stage;
    the extract of 17:26 (osmium tags-filter for the region motorway set; osmium extract -c per config of
      the tile grid) was typed at the prompt, not scripted -> stages `motorways` and `tiles`;
    windows.sh + windows_top.py (cut the three windows out of the tagged PBF, rank them with
      scenecheck.top, write canyon_top25.json / grid_top25.json and the seam re-measure) -> stage `windows`,
      which writes into the work store and never into tests/fixtures (a re-record is a human's commit).
  THE TILE PLAN, NOT ITS HISTORY: make_tiles.py, make_splits.py, make_quarters.py and order_tiles.py wrote
  the osmium configs of three rounds of re-cutting. What shipped is their END STATE: 152 tiles - the 27
  whole tiles of done.txt, t16b and t25b, and 30 tiles quartered (tilelist.txt's 125 plus done.txt's 27, the
  PASS1C END 152 docs line). Committed as data: the 152 names, and ONE bbox function of the name
  (t<row><col>[a|b][q0-3]) using make_tiles/make_splits/make_quarters' own formulas and rounding, checked
  equal to every bbox in the preserved tiles-r*/tiles-s*/tiles-q*.json before the rebuild uses it.
  SCRATCH HELPERS THAT BUILT NOTHING SHIPPED - named, left out: handover_top.py, handover_ties.py and
  handover_run.py (the 8/10 hand-over tables and the tie count, printed into T-0208's Log; handover_run.py
  only bound a git-archive copy of etl while a mutant ran); ceiling.py (a measurement over the read-back);
  count_missing.py (a recount of lost stdout); probe_seam.py, seam_raw.py (R1b's measurement); r2_red_green.py
  (a red/green demo). NOT IN THE ACCEPTANCE'S LIST AND LEFT OUT, recorded rather than hidden: sample.sh,
  make_tie.py and make_seam_fixture.py recorded COMMITTED FIXTURES (window_readback_sample.osm.xml,
  grid_tie_top25.json, seam_window_a/b.json), not the artifact.
  (R2) THE LAYOUT DISAGREES WITH THE BRIEF, TWICE. (a) `services/etl/etl/region/` cannot be a package:
  etl/region.py exists (the bbox/recorded-counts module; tests/test_region.py and test_dem_tiles.py do
  `from etl import region`), and a directory of the same name would shadow it. (b) Any new module under
  services/etl/etl/ is P-PROC-06's (MODULE_ROOTS services/etl/etl, recursive) and needs a population or an
  allowlist entry - both live in ops/lib/, which T-0246 holds in a sibling worktree this session. These
  modules compute no score: they run osmium, `python -m etl.waydoc`, `python -m etl.assemble --reference`
  and `python -m etl.tagwriter`, and move rows by way_id. RULED: the package is services/etl/regionbuild/,
  a sibling of etl/ (imported as `regionbuild`, run as `python3 -m regionbuild` from services/etl), and
  `touches:` is amended from services/etl/etl/region/ to services/etl/regionbuild/ in this commit. The one
  piece of logic with a count in it - first-tile-wins over the scored rows and seam_differ - is bound by
  the test below and refuses the build (exit 3) when a seam way disagrees, where pass3_merge.py only printed.
  One role per file, each <= 300 lines: tiles.py (the plan), layout.py (the work-store paths), osm.py (the
  osmium stages), sweep.py (N tiles at a time, resume by file presence), docs.py, reference.py, scoring.py,
  merge.py, windows.py, cli.py, __main__.py.
  (R3) ONE ENTRY POINT, ops/etl-region (100755): `ops/etl-region [--local] <stage> [options]`. Default mode
  runs the stage INSIDE the ETL image (`docker run --rm scenic-etl:latest python3 -m regionbuild ...`, repo
  at /repo, work store at /work) - T-0208's stages all ran in the image, and so does this rebuild, through
  WSL. `--local` runs `python -m regionbuild` on the host, for the test.
  (R4) THE TEST, tests/test_region_build.py: the two-tile fixture is T-0208's own seam pair,
  tests/fixtures/seam_window_a.json and seam_window_b.json, unmodified (way documents, pass 1's output, that
  share three byte-identical ways incl. 1533792498 and 399301293 and differ in population). It runs
  `bash ops/etl-region --local` through reference -> score -> merge -> tag, and asserts EXACT equality: every
  shared way's score in both tiles' scored tables, and its one row in the merged table, equal
  `assemble.assemble(doc, reference)` against the region reference over both documents; the tag stage's
  tags equal `tagwriter.tags_for_row` of that row. osmium and GDAL are not on the Linux test box, so the
  motorways/tiles/docs/toxml/topbf stages are proved by the rebuild, not by the test. RED BY NAME when the
  score stage drops `--reference`.
  (R5) THE REBUILD. The WORK STORE is WSL-native ext4 (/home/phineas/t0242, mounted at /work): T-0208
  measured ten tiles over the 9p mount completing NOTHING in nine minutes. Its inputs are copies: the clip
  from the MAIN checkout's services/etl/work/la/la-filtered.osm.pbf (read, never written) and
  services/etl/inputs. The OUTPUT is copied to the MAIN checkout's services/etl/work/t0242/ (never under
  .worktrees/): la-tagged.osm.pbf, la-reference.json and the stage logs. The shipped
  services/etl/work/la/la-tagged.osm.pbf is read-only. T-0208's intermediate store /home/phineas/t0208 is
  intact (docs, scored, reference, merged table) and is read only to localise a differing digest.
  The box is now 12 cores / 15 GB (T-0208 had 16 / 30), so `--jobs 8`.
- 2026-09-27T00:26:24Z THE PLAN, THE PACKAGE AND THE TEST, measured. Commit a6807e4: services/etl/regionbuild/
  (__init__ 7, __main__ 7, cli 94, docs 40, layout 92, merge 85, osm 76, reference 75, scoring 44, sweep 63,
  tiles 103, windows 118 lines) and ops/etl-region (30 lines, 100755 in the index).
  THE TILE PLAN against T-0208's preserved configs (`python work/t0242/verify_plan.py`, main checkout):
      `PLAN tiles=152 done=27 tilelist=125 union=152 plan_equals_union=True`
      `BBOX plan tiles compared=152 equal=152 differ=0 unrecorded=0`
  every bbox of the committed plan equals the one in tiles-r*/tiles-s*/tiles-q*.json that osmium cut.
  THE TEST, tests/test_region_build.py (187 lines), `python -m pytest tests/test_region_build.py -o addopts=`
  with every __pycache__ purged: `6 passed in 50.51s`.
  RED BY NAME: the mutant `scoring.py` calling `etl.assemble --input <doc> --out <out>` with `--reference
  <reference>` dropped (the entry point skipping the region reference), __pycache__ purged, 1.1 s python-sleep:
      `FAILED tests/test_region_build.py::test_the_entry_point_scores_every_shared_way_once_against_the_region_reference`
      `AssertionError: ops/etl-region gave a way in two tiles two scores: {399301293: (0.5692721901434575,
       0.5825606046676137), 1533792498: (0.6634176673434955, 0.6682691386682246)}`
      `3 failed, 3 passed` (the merge and tag tests fail after it: merge exits 3 on the disagreement)
  - T-0208's own no-reference numbers for the fixture (0.6634/0.6683, 0.5693/0.5826). Restored with
  `git checkout -- regionbuild/scoring.py`, purged, python-sleep 1.1 s, GREEN: `6 passed in 77.29s`, and
  `-rs` printed no skip line.
- 2026-09-27T00:49:30Z THE REBUILD, STAGE BY STAGE AS IT LANDS. Work store /home/phineas/t0242 (WSL ext4),
  every stage `SCENIC_REGION_WORK=/home/phineas/t0242 bash ops/etl-region <stage>` from the worktree in WSL,
  i.e. `docker run --rm scenic-etl:latest python3 -m regionbuild --work /work <stage>` (image
  sha256:00d22593fa72..., `osmium version 1.16.0` / `libosmium version 2.20.0`), log in the store's logs/.
  INPUTS: the clip copied from the main checkout's services/etl/work/la/la-filtered.osm.pbf, sha256
  b87d2462dadca7c373c9ac1d969a3e803219f682a97429a6e8b488d916fd087d, 35,962,835 B; services/etl/inputs'
  four 3dep tifs, worldcover-n33w120.tif, the two byways geojsons and manifest.yaml (california-osm.pbf is
  not read by these stages). The shipped artifact, re-hashed in the main checkout before anything ran:
  `648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39`.
  MOTORWAYS (6 s): `MOTORWAYS ways=19511 nodes=75897 xml_bytes=22086577` - T-0208's 17:26 line was
  `Number of ways: 19511` / `Number of nodes: 75897`, work/la-motorways.osm.xml 22,086,577 B.
  TILES, FIRST ATTEMPT: `osmium extract -c /work/configs/tiles-00.json ... died with <Signals.SIGKILL: 9>`
  after 5m00s - twelve complete_ways extracts in one config on this box's 15 GB (T-0208 ran twelve per
  config on 30 GB; sixty was OOM there). EXTRACTS_PER_CONFIG 12 -> 4 in tiles.py; the extract of a tile
  does not depend on which config holds it.
- 2026-09-27T01:14:06Z THE REBUILD, RESUMED by agent/claude-opus-5 (owner) after a session limit; the store kept
  every stage output, the stage logs are in its logs/ and are quoted here from there.
  TILES, SECOND ATTEMPT (EXTRACTS_PER_CONFIG 4), logs/tiles.log in the store, 18m20.8s real:
      `TILES tiles=152 configs=38 ways=580388 empty=0`
      `STAGE tiles exit=0 1050s`
  THE TILES AGAINST T-0208's OWN CUT: every one of the 152 tile PBFs `cmp`-equal to the file of the same name
  in T-0208's store /home/phineas/t0208/tiles (read only):
      `TILECMP pbf=152 equal=152 differ=0`
  so the plan's bboxes, the config split and osmium 1.16.0 reproduce pass 1's input byte for byte.
  DOCS, FIRST ATTEMPT: two tiles landed before the previous session was stopped by its limit (~18:00 local):
      `TILE t04 WAYDOC ways=2 refused=0 not_a_road=2 byways=865 byways_no_route_key=793 elapsed=27s`
      `TILE t07q0 WAYDOC ways=554 refused=0 not_a_road=8 byways=865 byways_no_route_key=793 elapsed=51s`
  the two documents are kept (resume by file presence); eight XMLs of the killed workers were left in tiles/ and
  are rewritten by `osmium cat --overwrite`. RESUMED 2026-09-27T01:13Z: docs reference score merge toxml tag
  topbf check in one chain, `--jobs 6` (8 on 15 GB for docs is untested memory; T-0208 ran 9 on 30 GB; the
  tiles are independent, so the job count changes no number). The inputs re-check against inputs.sha256
  runs first in the chain.
- 2026-09-27T04:01:07Z DOCS AND THE REFERENCE LAND, quoted from the store's logs/docs.log and logs/reference.log.
  DOCS (pass 1, `--jobs 6`, 150 tiles run + the two kept), 141m7s real:
      `DOCS END 152 docs of 152 tiles, 0 failed `
      `STAGE docs exit=0 7970s`
  the largest last: `TILE t54 WAYDOC ways=7830 refused=0 not_a_road=150 ... elapsed=675s`. Summed over the 150
  TILE lines, `SUM150 ways=573840 refused=0 not_a_road=5982`, plus t04 (2 ways) and t07q0 (554) = 574,396
  ways - T-0208's `REFERENCE docs=152 ways=574396`.
  THE DOCS AGAINST T-0208's: every rebuilt document differs from T-0208's store in its BYTES, and in exactly
  two strings. `work/t0242/docdiff.py` on t04 and t07q0 localised it: `/meta/inputs` new `/work/inputs` old
  `/w/services/etl/inputs` (or `/fast/inputs`), and `/meta/motorways` new `/work/la-motorways.osm.xml` old
  `work/la-motorways.osm.xml` (or `/fast/...`) - waydoc records the paths it was given, and T-0208 mounted its
  store at /w and /fast where ops/etl-region mounts /work. RULED: a path in meta is not a way's value.
  `work/t0242/cmpdocs.py docs` drops those two meta keys and compares the rest by `==` over all 152:
      `CMPDOCS docs files=152 byte_equal=0 equal_but_meta_paths=152 differ=0 path_keys_differing=inputs,motorways`
  REFERENCE (23m31s real; 1333s against T-0208's 458s on 16 cores):
      `REFERENCE docs=152 ways=574396 unique=540793 curvature=540793 elevation_gain=540793 furniture=540793 relief=540793 sinuosity=519764`
      `REFERENCE sha256 68863987ca325a42913d2534f1fbcc2d8a2292467125e93606425197ae2aa059  bytes 31385367  1333s`
  - the digest and size T-0208's Log quotes at 21:59. That digest is region_reference.dump's content digest
  (the value it returns), not the file's; the FILE was compared too, `compare.sh file la-reference.json`:
      `CMP la-reference.json equal new=31385367 old=31385367`
      `SHA new 5cde1a01f6e8f8b9faf90d5c8a49ffd039e7a56c49f1765b4df864861a561aea`
      `SHA old 5cde1a01f6e8f8b9faf90d5c8a49ffd039e7a56c49f1765b4df864861a561aea`
  The meta paths do not reach the reference: it is built from the documents' raw values only.
