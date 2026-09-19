---
id: T-0165
title: PMTiles build - the M2 exit clause nobody owns: an LA Protomaps extract (regions/la) under 120 MB, with a style that keeps the attribution corner free
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T04:48:18Z
lease_expires_at: 2026-09-19T10:48:18Z
worktree: .worktrees/T-0165
branch: task/T-0165
exclusive: []
touches: [services/tiles/, ops/publish-tiles]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "services/tiles/ holds the extract recipe (a digest-pinned go-pmtiles image run through WSL, regions/la's bbox read from services/etl/regions/la/region.json, the max zoom RULED in the Log) and the built LA PMTiles measured: bytes printed by the build command and quoted, under 120 MB (plan M2 exit) - the number comes from the command, never from prose"
  - "RED BY NAME first: a check (ops/lib/check-pmtiles or a pytest) that refuses a PMTiles whose header bounds do not cover the region bbox or whose size exceeds 120 MB, red on a fixture, then green on the built file"
  - "light and dark style JSON recoloured to the DesignTokens table with the lower-right corner reserved for attribution; a test that every colour in the style is one of the tokens' values"
---
## Brief

The plan's M2 exit includes "PMTiles <120 MB" and its architecture lists `services/tiles/` (pmtiles extract,
style JSON, sprites/glyphs -> R2). The 13:13 panel's grounding pass found no task for it anywhere in `queue/`
(a grep for pmtiles hits only T-0147 and T-0141, neither a tiles build) and no `services/tiles` directory.
Off M2's critical path - the walking skeleton runs on MapLibre demo tiles today - but it is an exit clause,
and the app cannot credit "(c) OpenStreetMap contributors - Protomaps" honestly until the tiles ARE Protomaps.

Scope to rule in the Log before code: the extract command (`pmtiles extract` from a Protomaps planet build by
bbox - the LA bbox is `services/etl/regions/la/region.json` (sfbay second)), the digest-pinned `go-pmtiles` image (plan:
images pinned by digest; docker runs on this box through WSL only), max zoom vs the 120 MB budget (measure,
do not guess), the light/dark style JSON recoloured to the design tokens with the lower-right corner reserved
for attribution, where the artifact lives (R2 needs the human's Cloudflare credentials - build and measure
here, publish is a separate `exclusive: [prod]` step). `meta.region` and `built_at` for P-DATA-03.

## Log
- 2026-09-18T19:52:17Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
- 2026-09-18T23:04:01Z PROMOTED to ready/ by agent/claude-fable-5-1 (16:13 panel, STRATEGY second slot, grounded): a plan M2
  exit clause, `depends_on: []`, unowned since the 13:13 panel, and unclaimable in backlog/ with an empty
  acceptance block. Needs docker through WSL; start it when a slot frees after T-0146.
- 2026-09-19T00:49:41Z LA FIRST, by agent/claude-fable-5-1 (the owner lives in Los Angeles - memory user-lives-in-la): the first PMTiles extract is LA (regions/la's bbox), sfbay second - the owner's phone shows LA.
- 2026-09-19T02:11:14Z WORDS FOLLOW THE RULING, by agent/claude-fable-5-1 (19:13 panel, grounded): the 00:49:41Z LA FIRST line and the acceptance block disagreed - an author obeying the block would have shipped Bay Area tiles and passed. The acceptance and brief now say regions/la (3 replacements).
- 2026-09-19T03:29:43Z TITLE FOLLOWS THE RULING, by agent/claude-fable-5-1 (21:13 panel, grounded): the title still said 'a Bay Area Protomaps extract' over an acceptance rewritten LA-first at 02:11:14Z; a claimer reads the title first. Frontmatter title only; nothing else changed.
- 2026-09-19T04:48:18Z claimed by agent/claude-opus-5; lease until 2026-09-19T10:48:18Z
- 2026-09-19T05:00:11Z R1 SOURCE AND COMMAND RULED, by agent/claude-opus-5 (owner). The extract is
  `pmtiles extract https://build.protomaps.com/20260915.pmtiles <out> --bbox=-119.0,33.7,-117.85,34.45 --maxzoom=N`,
  run over HTTP range requests against the Protomaps daily planet build - no planet download. The build DATE is
  pinned in `services/tiles/build-la.sh` as `PLANET_BUILD=20260915` and recorded in the sidecar. MEASURED, not
  assumed, and it changes the design: build.protomaps.com keeps only the last few days. Probed 2026-09-19T04:53Z
  with a one-byte range request, `curl -o /dev/null -w '%{http_code}' -r 0-0`:
  20260918 206, 20260917 206, 20260916 206, 20260915 206, 20260914 206, 20260913 206, 20260912 404, 20260911 404,
  20260910 404, 20260908 404, 20260901 404, 20260825 404. Retention is about six days, so a pinned date is a pin
  that EXPIRES - within a week this URL is a 404. Three consequences, all taken: (1) the date is the first variable
  in the recipe and overridable as `--build YYYYMMDD`, (2) the recipe probes the URL first and refuses with a named
  message rather than letting `pmtiles extract` fail obscurely, (3) the durable provenance is not the URL but the
  planet build's own stamps, which the sidecar copies out of the source header:
  `planetiler:osm:osmosisreplicationtime 2026-09-15T04:00:00Z`, `planetiler:version 0.10.2`,
  `planetiler:githash 0e5588c4a6e8c29a270a33afe8df62027d889604`, `version 4.15.2` (Protomaps Basemap). A manifest
  entry under `services/etl/inputs/manifest.yaml` was considered and REFUSED: that file is outside this task's
  `touches:`, and a `verify: sha256` on a URL that 404s in six days is the exact "pending" state that file forbids.
- 2026-09-19T05:00:11Z R2 IMAGE PINNED BY REPODIGEST, by agent/claude-opus-5 (owner). `docker pull
  protomaps/go-pmtiles:latest` in WSL, then `docker inspect --format '{{index .RepoDigests 0}}'`:
  `protomaps/go-pmtiles@sha256:06574f01f55a78f78f887bc7ebf729a5c093c0d6e17d9876300cfcb0758b59d3`
  (`pmtiles v1.31.2`, from `docker run --rm <digest> version`). The recipe runs THAT digest, never `:latest` - same
  rule as `services/routing/Dockerfile`, which pins both its stages by digest. The tag is used exactly once, in a
  comment-free `PMTILES_IMAGE=` assignment the recipe can be diffed on.
- 2026-09-19T05:00:11Z R3 MAX ZOOM RULED AT 14 BY MEASUREMENT, by agent/claude-opus-5 (owner). The source planet
  build's own max zoom is 15 (`pmtiles show` on the remote), so 15 is full resolution and there is nothing above it.
  `pmtiles extract --dry-run` walks the real directory entries for the LA bbox and prints the archive size it would
  write - a computed byte accounting, not an estimate - so the zoom ladder was measured before any download:
  maxzoom 15 -> region tiles 11828, result tile entries 9667, "archive size of 197 MB" - OVER the 120 MB M2 ceiling;
  maxzoom 14 -> region tiles 3030, result tile entries 2549, "archive size of 64 MB" - under;
  maxzoom 13 -> region tiles 804, result tile entries 708, "archive size of 20 MB" - under, and needlessly coarse.
  Ruled: maxzoom 14, the highest zoom that fits the ceiling, minzoom 0. The dry-run number is only admissible if it
  matches the real file, so the real build's `stat -c %s` is compared against the 64 MB dry run in the build
  measurement line below; that comparison is what licenses the z15 rejection without downloading 206 MB to prove it.
  What z14 costs, stated rather than hidden: one zoom level of road and label detail at the closest zoom, which for
  a driving map is the difference between house-number-level and block-level rendering. The renderer overzooms z14
  tiles past z14, so the map does not go blank - it goes soft.
- 2026-09-19T05:00:11Z R4 THE ARTIFACT LIVES IN THE MAIN CHECKOUT, by agent/claude-opus-5 (owner).
  `C:/Users/phineasf/Documents/GitHub/scenic_drive/services/tiles/work/`, NOT
  `.worktrees/T-0165/services/tiles/work/`. `git worktree remove` deletes a worktree's ignored files with it
  (memory: worktree-removal-deletes-gitignored-inputs), and a 64 MB artifact that dies when this task's worktree is
  cleaned up is not an artifact. `services/routing/.gitignore` (`work/`) is the precedent and
  `services/tiles/.gitignore` copies it; the recipe defaults `--out` to the main checkout's `work/` and takes
  `--out` for anywhere else. Nothing built lands in the tree: the commit carries the recipe, the styles, the check
  and the tests, never the PMTiles.
- 2026-09-19T05:00:11Z R5 meta.region AND built_at: BOTH INSIDE THE FILE, AND A SIDECAR, by agent/claude-opus-5
  (owner). What go-pmtiles CAN do, read from `pmtiles edit --help` on the pinned image: `edit --metadata=FILE`
  replaces the archive's JSON metadata with arbitrary JSON, and `edit --header-json=FILE` rewrites part of the
  header. So `meta.region` and `built_at` CAN live inside the .pmtiles, and the recipe puts them there: it reads the
  source metadata with `show --metadata`, adds `region: "la"`, `built_at`, `bbox`, `maxzoom`, `source_build` and
  `source_replication_time` at the top level, and writes it back with `edit --metadata`. What it CANNOT do: the v3
  header has no free-form field - it is 127 fixed bytes (magic, offsets, lengths, counts, compression, tile type,
  min/max zoom, bounds, center), so a region string cannot go in the header, and `pmtiles show` prints metadata keys
  it does not interpret. P-DATA-03 reads `meta.region` and a `built_at` under 30 days; the metadata JSON is where
  that lives. The sidecar `<out>.json` is written ANYWAY, beside the artifact, carrying bbox, maxzoom, bytes,
  sha256, source build date and source replication time - because the sha256 of the artifact cannot be inside the
  artifact, and because a downloader (the app's first-run sheet) needs the size and digest before it has the file.
  Honest statement of the split: region/built_at are authoritative INSIDE the file; the sidecar is a convenience
  copy plus the two facts that cannot be inside it.
- 2026-09-19T05:00:11Z R6 THE STYLE IS HAND-WRITTEN, GENERATED FROM ONE SPEC, by agent/claude-opus-5 (owner).
  `npx @protomaps/basemaps` was considered and REFUSED. Its layer generator emits ~100 layers coloured from a
  `Flavor` of ~40 keys; recolouring it to this app's eight semantic tokens is still a hand-written key->token table,
  the output is a generated file nobody in this repo can regenerate without a node_modules nobody has pinned, and
  the repo has no pinned node toolchain for it (services/api uses npx against a lockfile; there is no such lockfile
  here). Instead `services/tiles/make_styles.py` holds ONE layer spec plus the DesignTokens table transcribed as
  literals, and emits both `styles/scenic-light.json` and `styles/scenic-dark.json` from it, so light and dark
  cannot drift apart. Layer names are not invented: they are the `vector_layers` of the built archive, quoted in the
  build measurement below, and `make_styles.py --check` refuses a layer the archive does not carry.
  RULED COMMITTED: the two style JSONs are committed, pretty-printed, under `services/tiles/styles/`. A generated
  artifact is normally not source, but these are what the app ships and what the token test asserts over; a style
  that only exists after someone runs a generator is a style the app cannot load. The 300-line cap is read as a cap
  on the FILE, so they are pretty-printed and kept under it (`wc -l` quoted at the final commit) rather than
  minified to one line to dodge it - a one-line 60 KB JSON passes a line count and is undiffable, which is the
  opposite of what the cap is for.
  THE ATTRIBUTION CORNER: a style cannot "reserve" a corner - there is no such construct in the MapLibre style
  spec. What it can do is contribute nothing there, and that is what is ruled: the style declares NO MapLibre
  attribution control content (`sources[].attribution` is absent, so the renderer's own control renders empty) and
  no symbol layer is anchored to the viewport. The lower-right belongs to `AttributionFooter` (DesignSystem), which
  draws "(c) OpenStreetMap contributors - Protomaps" over the map at bottom-trailing. Two parties must not both
  claim it: a renderer-drawn attribution control plus our footer is the same credit twice, and the one we control
  is the one the product invariant names. `MapStyle.attributionText` must gain the Protomaps string when a case for
  these styles is added - that is in `apps/ios/`, outside this task's `touches:`, and is STILL OPEN below.
- 2026-09-19T05:00:11Z R7 ops/publish-tiles REFUSES WITHOUT CREDENTIALS, by agent/claude-opus-5 (owner). R2 upload
  needs the human's Cloudflare credentials and this task does NOT hold `exclusive: [prod]`, so the script is
  written, committed executable and demonstrated REFUSING; it never publishes here. It refuses on any of: the named
  env vars absent (`CLOUDFLARE_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`), the artifact
  or its sidecar missing, the sidecar's sha256 disagreeing with the file, or `queue/LOCKS/prod.lock` not held -
  the same lock gate `ops/deploy` uses, for the same reason (publishes are serial and the task holding the lock is
  accountable). Refusal messages are `PUBLISH REFUSED: ...` and name the missing thing.
- 2026-09-19T05:00:11Z R8 WHERE THE CHECK LIVES, AND WHAT ops/test CAN SEE, by agent/claude-opus-5 (owner). The
  acceptance block offers "ops/lib/check-pmtiles or a pytest". `ops/lib/` is NOT in this task's `touches:`
  (`services/tiles/`, `ops/publish-tiles`), so the check is a pytest: `services/tiles/check_pmtiles.py` (the
  checker, importable and runnable as a script) with `services/tiles/tests/test_pmtiles_budget.py` over it.
  DISAGREEMENT RULED: the task's `verify:` says `ops/test`, but `ops/test`'s python tier is gated on
  `services/etl/pyproject.toml` and knows nothing about `services/tiles/` - adding a tier means editing `ops/test`,
  which is outside `touches:`. So these tests do not count toward the floor today and are run directly
  (`python -m pytest services/tiles/tests -q`, quoted at the final commit). Wiring the tier is STILL OPEN below,
  and claiming `ops/test` covers them would be exactly the false green this repo exists to catch.
  The checker parses the 127-byte PMTiles v3 header in pure Python rather than shelling out to the image: a pytest
  that needs docker cannot run in CI, and a header-only fixture with wrong bounds can then be constructed in-process
  for the red run. The parser is only trustworthy if it agrees with the tool, so its output is compared against
  `pmtiles show --header-json` on the real built file, quoted below.
- 2026-09-19T05:20:44Z BUILT AND MEASURED, by agent/claude-opus-5 (owner). `bash services/tiles/build-la.sh`
  through WSL, against the pinned build and the pinned image, bbox read out of regions/la/region.json:

      == 0. the pinned planet build ==
      https://build.protomaps.com/20260915.pmtiles -> HTTP 206
      == 1. extract -119.0,33.7,-117.85,34.45 maxzoom=14 ==
      extract.go:441: Region tiles 3030, result tile entries 2549
      extract.go:606: Completed in 9.756294001s with 4 download threads (261.2672342692787 tiles/s).
      extract.go:611: Extract required 52 total requests.
      extract.go:612: Extract transferred 67 MB (overfetch 0.05) for an archive size of 64 MB
      == 3. measure ==
      BYTES 63520949 /mnt/c/.../scenic_drive/services/tiles/work/la.pmtiles
      BUDGET 125829120 (120 MB)

  63,520,949 bytes, 50.5% of the 120 MB ceiling, from `stat -c %s` in the build command - not from prose.
  THE DRY RUN IS VINDICATED, which is what licenses rejecting z15 without downloading it: the z14 dry run said
  "an archive size of 64 MB" and the real file is 63,520,949 bytes = 63.5 MB. Same number. The z15 dry run's
  197 MB is therefore a measurement of a real 197 MB archive, and 197 > 120.
  `pmtiles show` on the built file, via the pinned image:

      pmtiles spec version: 3
      tile type: mvt
      bounds: (long: -119.000000, lat: 33.700000) (long: -117.850000, lat: 34.450000)
      min zoom: 0
      max zoom: 14
      center: (long: -118.425000, lat: 34.075000)
      addressed tiles count: 3030
      tile entries count: 2549
      tile contents count: 2500
      clustered: true
      internal compression: gzip
      tile compression: gzip
      region la
      built_at 2026-09-19T05:02:38Z
      source_build 20260915
      source_replication_time 2026-09-15T04:00:00Z
      attribution <a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap</a>
      version 4.15.2

  R5 CONFIRMED BY THE ARTIFACT: `region` and `built_at` are INSIDE the file, printed by the tool's own `show`,
  and the source's `attribution` and `vector_layers` survived the metadata rewrite. The sidecar beside it:

      {"bbox": "-119.0,33.7,-117.85,34.45", "built_at": "2026-09-19T05:02:38Z", "bytes": 63520949,
       "file": "la.pmtiles", "maxzoom": 14, "region": "la",
       "sha256": "3b711c7918f7ba7dcf88998e150c3423056aafe3c2948d19bb0ce290ae2b5a0a",
       "source_build": "20260915", "source_replication_time": "2026-09-15T04:00:00Z",
       "source_url": "https://build.protomaps.com/20260915.pmtiles"}
- 2026-09-19T05:20:44Z THE PARSER AGREES WITH THE TOOL, by agent/claude-opus-5 (owner). R8 said a pure-Python
  header parser is only admissible if it agrees with go-pmtiles. `show --header-json` on the built file gives
  `{"tile_compression": "gzip", "tile_type": "mvt", "minzoom": 0, "maxzoom": 14,
  "bounds": [-119, 33.7, -117.85, 34.45], "center": [-118.425, 34.075, 0]}`; `check_pmtiles.parse_header`
  on the same bytes gives `min_lon -119.0, min_lat 33.7, max_lon -117.85, max_lat 34.45, min_zoom 0, max_zoom 14,
  tile_type 1 (mvt), tile_compression 2 (gzip), internal_compression 2 (gzip), spec_version 3`, plus the offsets
  the tool does not print (`metadata_offset 6431, metadata_length 1286, tile_data_length 63513232,
  tile_entries_count 2549, tile_contents_count 2500, addressed_tiles_count 3030`). Field for field, no
  disagreement. The archive's `vector_layers`, which the style's source-layers are anchored on rather than guessed:
  ['boundaries', 'buildings', 'earth', 'landcover', 'landuse', 'places', 'pois', 'roads', 'water'].
- 2026-09-19T05:20:44Z RED BY NAME, THEN GREEN - THE PMTILES CHECK, by agent/claude-opus-5 (owner).
  `services/tiles/check_pmtiles.py`, run as a script. RED 1, a constructed fixture whose bounds stop at -118.0
  instead of -117.85 (Angeles Crest and the San Gabriel front simply absent, and it still looks like a basemap):

      PMTILES REFUSED: .../work/wrong-bounds.pmtiles
        - header bounds (-119.000000,33.700000,-118.000000,34.450000) do not cover the region bbox (-119.0,33.7,-117.85,34.45)
      exit=1

  RED 2, the real built file against a 60 MiB budget, so the size limb is seen red on a real archive rather than
  on a fixture:

      PMTILES REFUSED: .../work/la.pmtiles
        - 63520949 bytes exceeds the 62914560-byte budget by 606389
      exit=1

  GREEN, the same script on the same real file at the real 120 MB budget:

      PMTILES OK: la.pmtiles region=la bytes=63520949 zoom=0-14 bounds=(-119.000000,33.700000,-117.850000,34.450000)
      exit=0

  `services/tiles/tests/test_pmtiles_budget.py` holds the population: every edge of the bbox short in turn, a wider
  archive accepted (bounds snap out to whole tiles, so cover - not equal - is the rule), the wrong region, a
  built_at 31 days old, a missing built_at, a v4 archive and a file that is not PMTiles at all.
- 2026-09-19T05:20:44Z RED BY NAME, THEN GREEN - THE STYLE TOKEN TEST, by agent/claude-opus-5 (owner). One colour
  in `styles/scenic-light.json` changed from `#FFF7ED` to `#4264FB` (MapLibre's own default blue), then
  `python -m pytest tests/test_style_tokens.py -q`:

      E         Left contains one more item: '#4264FB'
      tests\test_style_tokens.py:59: AssertionError
      E         - color": "#FFF7ED"
      E         + color": "#4264FB"
      tests\test_style_tokens.py:105: AssertionError
      FAILED tests/test_style_tokens.py::test_every_colour_is_a_token_of_that_appearance[light]
      FAILED tests/test_style_tokens.py::test_the_committed_file_is_what_the_generator_emits[light]

  Two tests, and the second one matters as much as the first: it is what stops the styles being hand-edited until
  the generator is decoration. Colour restored, whole suite green: `python -m pytest tests -q` ->
  `............................ [100%]`, 28 passed.
- 2026-09-19T05:20:44Z THE 300-LINE CAP CAUGHT THE STYLES, AND THEY WERE RE-MEASURED, by agent/claude-opus-5
  (owner). First generation was `json.dumps(indent=2)`: `wc -l` 309 lines each, OVER the cap I ruled they would
  stay under at R6. Fixed at the generator rather than by minifying: `make_styles.dumps` keeps any list with no
  object in it - a filter, an `interpolate` expression - on ONE line. Re-measured after the change, as the rule
  requires: 194 lines each. A one-line minified style would also have passed a line count, which is why that was
  not the fix.
- 2026-09-19T05:20:44Z ops/publish-tiles DEMONSTRATED REFUSING, by agent/claude-opus-5 (owner). It has never
  published; `exclusive: [prod]` is not held by this task. Three runs:

      $ bash ops/publish-tiles
      PUBLISH REFUSED: 4 credential(s) not set: CLOUDFLARE_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET
      exit=1
      $ CLOUDFLARE_ACCOUNT_ID=x R2_ACCESS_KEY_ID=x R2_SECRET_ACCESS_KEY=x R2_BUCKET=x bash ops/publish-tiles
      PUBLISH REFUSED: queue/LOCKS/prod.lock not held (claim a task with exclusive: [prod])
      exit=1
      $ CLOUDFLARE_ACCOUNT_ID=x R2_ACCESS_KEY_ID=x R2_BUCKET=x bash ops/publish-tiles
      PUBLISH REFUSED: 1 credential(s) not set: R2_SECRET_ACCESS_KEY
      exit=1

  The third run is the one that matters: it names the ONE missing variable rather than saying "credentials", so a
  human with three of four set is told which one.
- 2026-09-19T05:37:02Z FINAL PRE-REVIEW COMMIT - THE WHOLE ACCEPTANCE BLOCK, RE-RUN AND RE-QUOTED BARE, by
  agent/claude-opus-5 (owner). Every command below was run again at this commit, not copied from above. The
  artifact itself was NOT rebuilt - rebuilding would mint a new built_at and a new sha256 and quietly invalidate
  the sidecar quoted at 05:20:44Z. Re-verifying the bytes and the digest of the file that was built is the
  stronger check, and that is what item 1 is.

      === 1. the artifact, re-measured ===
      63520949 .../scenic_drive/services/tiles/work/la.pmtiles
      3b711c7918f7ba7dcf88998e150c3423056aafe3c2948d19bb0ce290ae2b5a0a *.../work/la.pmtiles
      === 2. the check GREEN on the built file ===
      PMTILES OK: la.pmtiles region=la bytes=63520949 zoom=0-14 bounds=(-119.000000,33.700000,-117.850000,34.450000)
      exit=0
      === 3. the check RED on wrong-bounds.pmtiles ===
      PMTILES REFUSED: ...\work\wrong-bounds.pmtiles
        - header bounds (-119.000000,33.700000,-118.000000,34.450000) do not cover the region bbox (-119.0,33.7,-117.85,34.45)
      exit=1
      === 4. pytest services/tiles/tests ===
      ............................                                             [100%]
      exit=0
      === 5. ops/publish-tiles bare ===
      PUBLISH REFUSED: 4 credential(s) not set: CLOUDFLARE_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET
      exit=1
      === 6. pmtiles show (pinned image) ===
      pmtiles spec version: 3
      tile type: mvt
      bounds: (long: -119.000000, lat: 33.700000) (long: -117.850000, lat: 34.450000)
      min zoom: 0
      max zoom: 14
      addressed tiles count: 3030
      tile entries count: 2549
      tile contents count: 2500
      clustered: true
      === 7. check-line-cap ===
      P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines
      exit=0
      === 8. check-exec-bits ===
      P-OPS-01: 64 files, 23 required present, all modes correct
      exit=0
      === 9. queue-check ===
      QUEUE OK (186 tasks)
      === 10. wc -l, every new source file, 300-line cap ===
        117 services/tiles/build-la.sh
        169 services/tiles/check_pmtiles.py
        233 services/tiles/make_styles.py
        116 services/tiles/tile_meta.py
        139 services/tiles/tests/test_pmtiles_budget.py
        124 services/tiles/tests/test_style_tokens.py
        194 services/tiles/styles/scenic-light.json
        194 services/tiles/styles/scenic-dark.json
         68 services/tiles/README.md
         12 services/tiles/pyproject.toml
          5 services/tiles/.gitignore
         87 ops/publish-tiles
      === 11. ops/check-pins --source-only ===
      PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0

  `check-exec-bits` reporting "all modes correct" over 64 files is the one that covers `ops/publish-tiles`: it was
  staged and then `git update-index --chmod=+x`'d, because core.filemode is false on this checkout and git would
  otherwise commit it 100644 while every run through `bash ops/publish-tiles` stayed green.
  STILL OPEN, and none of it is claimed by this task:
  (1) `ops/test` cannot see `services/tiles/tests` - its python tier is gated on `services/etl/pyproject.toml`.
      These 28 tests are run directly and are NOT in the floor. Wiring the tier touches `ops/test`.
  (2) No glyphs and no sprites, so the basemap draws NO LABELS. Deliberate: a `glyphs` URL that 404s renders
      nothing while claiming it has them. A driving basemap without street names is not shippable, so this is the
      next tiles task, not a nicety.
  (3) `MapStyle` still has only the `maplibreDemoTiles` case and still credits "(c) MapLibre - Natural Earth".
      The Protomaps case and the plan's "(c) OpenStreetMap contributors - Protomaps" string land in `apps/ios/`,
      outside this task's `touches:`. Until then the app does not render these tiles.
  (4) Nothing is published. `ops/publish-tiles` needs the human's four env vars and a task holding
      `exclusive: [prod]`; the R2 prefix it writes (`tiles/v1/`) is a proposal, not an agreed layout.
  (5) The pinned `PLANET_BUILD=20260915` 404s in about a week. The recipe refuses by name when it does, but
      nothing reminds anybody; a scheduled rebuild belongs with the weekly ETL run.
  (6) P-ATTR-01 and P-DATA-03 are still not in `pins/PINS.yaml` (`grep -c P-DATA-03 pins/PINS.yaml` -> 0). This
      task built the artifact those pins would assert over; filing them touches `pins/`.
