---
id: T-0274
title: ops/etl-region builds places too - the osmium places pass (T-0266) and the fallback corpus (T-0270) wired into the region build, so a full LA corpus carries places and the fallback is rebuilt by one command
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T03:38:14Z
lease_expires_at: 2026-10-06T15:38:14Z
worktree: .worktrees/T-0274
branch: task/T-0274
exclusive: [scenic-index]
touches: [ops/etl-region, services/etl/regionbuild/, services/etl/etl/, services/etl/tests/, services/etl/regions/la/]
pins_affected: [P-DATA-01]
reviewer: null
depends_on: [T-0266, T-0270]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/etl-region la runs the placeallow osmium pass on the region's own input and passes --places-osm to the extract stage, so the region corpus has places at the T-0266 measured counts (quoted, per class, as the stage lands); a regionbuild test (fixture region) asserts the stage order and that places reach the corpus by exact equality"
  - "ops/etl-region la --fallback (or a ruled sub-command) rebuilds apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite from the same places and reproduces the committed file byte-for-byte (sha256 quoted twice); the command is the one T-0270's test_fallback_committed names as the rebuild"
  - "idempotent (P-DATA-01): two runs give identical corpus content digests; no gitignored large input is deleted (memory: worktree removal deletes ignored inputs)"
---
## Brief

T-0266 stillOpen: 'wiring the osmium places pass into ops/etl-region / regionbuild are separate tasks'; T-0270: the
fallback rebuild is manual. One command should build the region corpus with places and the fallback file.

## Log
- 2026-10-06T03:35:41Z filed by agent/claude-opus-5 (orchestrator) after PR #161 merged.
- 2026-10-06T03:38:14Z claimed by agent/claude-opus-5; lease until 2026-10-06T15:38:14Z
- 2026-10-06T03:45:57Z RULED FIRST (agent/claude-opus-5, owner), before code. Read: ops/etl-region, regionbuild/{cli,layout,osm,merge}.py, etl/{placeallow,fallback,extractadapter}.py, tests/test_region_build.py, tests/test_fallback_committed.py, T-0242/T-0266/T-0270 Logs; listed the WSL store /home/phineas/t0242 and the main checkout's services/etl/work/la/.
  - R1 NO EXTRACT STAGE EXISTS. regionbuild's stages are motorways tiles docs reference score merge toxml tag topbf check (+ sha, windows); its product is <region>-tagged.osm.pbf, and merge.py writes the merged document with `"ways": []` (refusals only). No stage makes a region waydoc of ways, so there is no extract/corpus stage to pass --places-osm to, and inventing a full-region ways corpus (seam dedupe over 152 tile docs, an unmeasured size against the 60 MB budget) is out of scope - filed as still open. RULED: the corpus the region build writes is the places corpus the bundle carries (etl.fallback, T-0270), so "places reach the corpus" is asserted on that file by exact equality; the acceptance's "extract stage" is that stage.
  - R2 TWO NEW STAGES, appended to ALL after check: `places` (the T-0266 osmium pass on the region's OWN input, the UNFILTERED clip <region>.osm.pbf in the store - the keep-pass clip has no cafe/museum/garden/trailhead/place tags, T-0266 INPUT - with the SHIPPING `placeallow.keep_expressions()`, then `osmium cat` to <region>-places.osm.xml, then the osmium counts and placeallow's PLACES count line) and `fallback` (the SHIPPING `etl.fallback.main` over <region>-places.osm.xml into the store as <region>-corpus-fallback.sqlite, then copied to the region's bundle path). One new module regionbuild/places.py; layout gains source/places_pbf/places_xml/fallback.
  - R3 THE COMMAND. `ops/etl-region places` then `ops/etl-region fallback` (--region la is the default; "ops/etl-region la" in the acceptance is read as the LA region, the script takes the stage positionally - no script interface change, only its header). BUNDLE = {"la": (apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite, 2026-10-06T00:00:00Z)} - T-0270's built_at, so the rebuild is byte-identical; a region with no bundle entry is refused (exit 2). `--bundle-root` (default the checkout holding the package, /repo in the image) is where the bundle path resolves, so a fixture test writes under tmp, never over the committed file.
  - R4 test_fallback_committed NAMES THE REBUILD by identifier, not comment: a new test asserts `places.BUNDLE["la"]` resolves to COMMITTED under the checkout and that its built_at/region equal the committed file's meta - the command the file is rebuilt by is the one that writes it.
  - R5 TEST: new tests/test_region_places.py through `regionbuild.cli.main` (what `python -m regionbuild` and ops/etl-region exec). osmium exists only in the image, so the places stage's osmium calls are a recording fake of regionbuild.osm.run that copies the fixture places_allowlist.osm.xml where `osmium cat` writes; the osmium command lines are asserted by exact equality. The fallback stage runs through `ops/etl-region --local fallback` (pure python). Places in the bundle file equal `fallback.choose(placeallow.select(fixture))` row for row; two runs byte-identical (P-DATA-01); a store with no <region>.osm.pbf is refused before osmium runs.
  - R6 POPULATION: regionbuild/ is outside MODULE_ROOTS (services/etl/etl, Sources) and places.py computes nothing numeric (it orders calls to placeallow/fallback, whose populations stand), so no ops/mutate entry.
  - R7 LA RUN: store /home/phineas/t0242 (WSL ext4); the unfiltered clip is COPIED (never moved) from the main checkout's services/etl/work/la/la.osm.pbf into the store as la.osm.pbf. Expected, quoted from T-0266 BEFORE the run: `Number of nodes: 132970` `Number of ways: 9155` `Number of relations: 268`, `PLACES places=4773 ... viewpoint=102 peak=187 waterfall=36 beach=56 trailhead=99 museum=232 cafe=1511 garden=334 park=2112 town=104`; fallback file_sha256 05c3a19c4ba2fa59e7889c771d9dec4fe554bef81c73c85f073834956d7e936d (T-0270).
