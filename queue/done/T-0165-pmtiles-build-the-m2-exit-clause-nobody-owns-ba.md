---
id: T-0165
title: PMTiles build - the M2 exit clause nobody owns: an LA Protomaps extract (regions/la) under 120 MB, with a style that keeps the attribution corner free
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T04:48:18Z
lease_expires_at: 2026-09-19T10:48:18Z
worktree: .worktrees/T-0165
branch: task/T-0165
exclusive: []
touches: [services/tiles/, ops/publish-tiles]
pins_affected: []
reviewer: agent/rv2-pr109
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
- 2026-09-19T05:54:29Z THE MUTANT PASS'S TWO SURVIVORS, FIXED - AND THE THREE RECORD ITEMS RULED, by
  agent/claude-opus-5 (owner). The pre-review mutant pass ran three unwritten mutants against the 05:37:02Z
  commit and two survived. Both are the same failure: a check that could not see the thing it was written to
  check. Fixed here before the review is bought, each one red by name first.

  S1 SURVIVOR - `make_styles.TOKENS` was anchored to NOTHING. The mutant changed one hex digit in the
  transcription (`bg.light` `#FFF7ED` -> `#FFF7EE`), regenerated the styles, and the suite was 28 passed while
  `DesignTokens.swift` still said `#FFF7ED`. Nothing under `services/tiles/` read the Swift file at all, so
  every colour test in the directory measured the styles against a table that had stopped agreeing with
  DesignSystem - and the map would ship a colour the app does not have. RULED: the transcription gets an
  anchor, `services/tiles/tests/test_design_tokens_match.py`. It parses the `public static let` DECLARATIONS
  out of `apps/ios/Packages/ScenicApp/Sources/DesignSystem/DesignTokens.swift` and asserts they equal `TOKENS`
  per appearance. Three things about HOW it parses, because they are the ruling:
  (i) It strips every whole-line comment BEFORE parsing. `DesignTokens.swift` carries the same table a second
      time as a doc comment at lines 14-24, and CLAUDE.md forbids anchoring on a comment. A test that read
      that table would pass over a renamed token and fail on a reworded comment - backwards in both
      directions. `test_the_table_is_read_from_the_declarations_not_the_doc_comment` proves the parse survives
      with every comment line deleted, and asserts `#FFF7ED` is present in the file and absent from the
      stripped code - the hex triples in code are `0xFFF7ED`, which is why the comment could be mis-read.
  (ii) `border` is read off the ternary's own `userInterfaceStyle == .dark` condition, not off the order the
      branches happen to be written in, and its dark value stays `rgba(255,255,255,0.08)` rather than being
      flattened to a hex approximation.
  (iii) `test_eleven_tokens_are_found_at_all` asserts the count, so a regex that silently matched nothing
      cannot make every other assertion in the file vacuously true.
  RED, the mutant re-run against the committed bytes - mutate, regenerate the styles, run the WHOLE suite,
  restore (`services/tiles/work/mutant_s1.py`, not committed, `work/` is gitignored):

      FAILED services\tiles\tests\test_design_tokens_match.py::test_the_transcription_equals_the_declarations
      FAILED services\tiles\tests\test_design_tokens_match.py::test_no_token_is_invented_or_missing[light]
      pytest exit= 1
      E         Differing items:
      E         {'bg': {'light': '#FFF7ED', 'dark': '#0F172A'}} != {'bg': {'light': '#FFF7EE', 'dark': '#0F172A'}}

  The other 41 tests stayed green under the mutant, which is exactly the survivor being reported: nothing
  else in the directory can see this.

  S2 SURVIVOR - `check_pmtiles` had no zoom limb and no tile-count limb. A `max_zoom=10` archive with correct
  bounds passed; `max_zoom=14` with `meta.maxzoom=10` passed; an archive with zero tile entries passed. So
  `build-la.sh --maxzoom 12` would have written a ~20 MB file that passed step 6, and `ops/publish-tiles`
  would have uploaded it. RULED, and the reason it is not a budget question: the budget limb is blind to this
  from the other side - every zoom BELOW 14 is a SMALLER file, so coarseness buys headroom. Three limbs added:
  `MIN_MAXZOOM = 14` as a typed literal (R3's ruled zoom, overridable with `--min-maxzoom` so lowering the
  floor is a decision a caller states), `meta.maxzoom` must equal the header's `max_zoom` (they are written by
  two different steps - the header by `pmtiles extract`, the metadata by the recipe's stamp - so they disagree
  precisely when a rebuild changed one and not the other), and `tile_entries_count > 0`. RED on each
  constructed fixture, then GREEN on the real file, all four re-run at this commit:

      $ python services/tiles/check_pmtiles.py services/tiles/work/low-zoom.pmtiles --region-json services/etl/regions/la/region.json
      PMTILES REFUSED: services\tiles\work\low-zoom.pmtiles
        - header max_zoom 10 is below the required 14 (T-0165 R3: z14 is the highest zoom inside the 120 MB budget, and a coarser build is a smaller file that passes the budget by giving up detail)
      exit=1
      $ python services/tiles/check_pmtiles.py services/tiles/work/zoom-mismatch.pmtiles --region-json services/etl/regions/la/region.json
      PMTILES REFUSED: services\tiles\work\zoom-mismatch.pmtiles
        - meta.maxzoom 10 disagrees with the header's max_zoom 14
      exit=1
      $ python services/tiles/check_pmtiles.py services/tiles/work/no-tiles.pmtiles --region-json services/etl/regions/la/region.json
      PMTILES REFUSED: services\tiles\work\no-tiles.pmtiles
        - header tile_entries_count is 0: the archive carries no tiles
      exit=1
      $ python services/tiles/check_pmtiles.py <main checkout>/services/tiles/work/la.pmtiles --region-json services/etl/regions/la/region.json
      PMTILES OK: la.pmtiles region=la bytes=63520949 zoom=0-14 tiles=2549 bounds=(-119.000000,33.700000,-117.850000,34.450000)
      exit=0

  The OK line now prints `tiles=2549`, so the green run states the count the new limb reads. The fixtures are
  built by `services/tiles/work/make_fixtures.py` (not committed) out of the test file's own header writer,
  which grew `maxzoom=` and `entries=` parameters - the same 127-byte record, no second header builder.

  RECORD ITEM (a) RULED - the refusal is a test now, not a paragraph. `ops/publish-tiles` was demonstrated
  refusing at 05:20:44Z by pasting three runs into this file. Prose in a Log is not a check: move the
  credential gate below the lock or artifact gates and nothing goes red, while a human with three of four
  variables set stops being told which one is missing. `services/tiles/tests/test_publish_refusal.py` runs the
  script bare through `subprocess` with the four variables stripped out of the environment and asserts the
  credential refusal is the FIRST line printed; a second test asserts the one-missing-variable line verbatim;
  a third sets all four and asserts the script still refuses on a LATER gate, which is what makes the first
  line evidence of ORDER rather than of there being one gate. Nothing can publish from it - the only branch
  reachable with the variables stripped is the refusal. RED with the gate cut out of the script (a backup
  taken, the block removed, the test run, the original bytes put back - `services/tiles/work/mutant_a.py`):

      cut 474 bytes: the four-variable gate is gone
      FAILED services\tiles\tests\test_publish_refusal.py::test_the_credential_refusal_is_the_first_thing_a_bare_run_says
      FAILED services\tiles\tests\test_publish_refusal.py::test_the_refusal_names_the_one_variable_that_is_missing
      E       AssertionError: PUBLISH REFUSED: queue/LOCKS/prod.lock not held (claim a task with exclusive: [prod])
      pytest exit= 1

  `ops/publish-tiles` itself is byte-for-byte unchanged by this commit (`git status --short` clean on it).

  RECORD ITEM (b) RULED - DERIVE, not drop. `build-la.sh:25` carried `BUDGET_BYTES=125829120`, a second copy
  of the ceiling read only by its own step-3 refusal. Both offered fixes were considered. Dropping the shell
  copy and letting step 3 call the checker was REFUSED: at step 3 the sidecar is not written yet, so the full
  checker would be run on a half-finished artifact, and the early refusal would move after the sidecar write
  - the recipe would record a build it is about to reject. So the number is DERIVED: the recipe reads
  `check_pmtiles.BUDGET_BYTES` out of the module step 6 runs, and refuses by name if it cannot. One
  definition, and step 3 and step 6 cannot come to different conclusions about the same file. The recipe was
  NOT re-run (rebuilding would mint a new `built_at` and a new sha256 and invalidate the sidecar quoted at
  05:20:44Z), so the derivation was exercised two ways instead - `bash -n` on the whole script, and the two
  lines run verbatim outside it (`PYTHON=python`, because this box's git-bash has no `python3`; WSL, where
  the recipe runs, does):

      $ bash -n services/tiles/build-la.sh
      bash -n build-la.sh OK
      $ PYTHON=python bash services/tiles/work/budget_line.sh
      BUDGET 125829120 (120 MB)
      $ grep -c 125829120 services/tiles/build-la.sh
      0

  `test_the_build_recipe_reads_the_budget_out_of_this_module` holds that: the literal is absent from the
  recipe and `check_pmtiles.BUDGET_BYTES` is present in it. Anchored on the script's text, not on a comment.

  RECORD ITEM (c) RULED - NOT FIXED HERE, and STILL OPEN (1) stands unchanged. The tests are 43 now, not 28,
  and all 43 are still outside `ops/test`'s floor: its python tier is gated on `services/etl/pyproject.toml`.
  Wiring a `services/tiles` tier edits `ops/test`, which is outside this task's `touches:`. `ops/test` was not
  run and not touched. Claiming a bigger number inside a floor that cannot see it is the false green this repo
  exists to catch, so the number is stated where it is true: run directly.

- 2026-09-19T05:54:29Z FINAL PRE-REVIEW COMMIT (correction commit) - THE WHOLE ACCEPTANCE BLOCK, RE-RUN AND
  RE-QUOTED BARE, by agent/claude-opus-5 (owner). Every command below was run again at this commit against
  the committed bytes, none copied from above, none piped. The artifact was NOT rebuilt - see (b).

      === 1. pytest services/tiles/tests -q ===
      ...........................................                              [100%]
      exit=0
      (the same run without the command-line -q, since pyproject already sets addopts = "-q" and two of them
      suppress the summary line:)
      43 passed in 4.33s
      === 2. the check GREEN on the real build ===
      PMTILES OK: la.pmtiles region=la bytes=63520949 zoom=0-14 tiles=2549 bounds=(-119.000000,33.700000,-117.850000,34.450000)
      exit=0
      === 3. the check RED on each new fixture, by name ===
      low-zoom.pmtiles      - header max_zoom 10 is below the required 14 ...            exit=1
      zoom-mismatch.pmtiles - meta.maxzoom 10 disagrees with the header's max_zoom 14    exit=1
      no-tiles.pmtiles      - header tile_entries_count is 0: the archive carries no tiles  exit=1
      === 4. the DesignTokens test, RED then GREEN ===
      RED   FAILED services\tiles\tests\test_design_tokens_match.py::test_the_transcription_equals_the_declarations
            FAILED services\tiles\tests\test_design_tokens_match.py::test_no_token_is_invented_or_missing[light]
      GREEN 43 passed (the mutant driver restores make_styles.py and both style JSONs; git status clean after)
      === 5. ops/publish-tiles bare, through the new test ===
      RED (gate cut)  FAILED ...::test_the_credential_refusal_is_the_first_thing_a_bare_run_says
      GREEN           3 passed, first line: PUBLISH REFUSED: 4 credential(s) not set: CLOUDFLARE_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET
      === 6. check-line-cap ===
      P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines
      exit=0
      === 7. check-exec-bits ===
      P-OPS-01: 64 files, 23 required present, all modes correct
      exit=0
      === 8. queue-check ===
      QUEUE OK (186 tasks)
      exit=0
      === 9. check-pins --source-only ===
      PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0
      === 10. wc -l, every file this commit touches, 300-line cap ===
        122 services/tiles/build-la.sh          (was 117; the budget literal out, the derivation in)
        198 services/tiles/check_pmtiles.py     (was 169; three limbs)
        185 services/tiles/tests/test_pmtiles_budget.py   (was 139; six tests, one shared header writer)
         95 services/tiles/tests/test_design_tokens_match.py   (new)
         70 services/tiles/tests/test_publish_refusal.py       (new)
         84 services/tiles/README.md            (was 68; the new limbs, the token anchor, the publish test)
        233 services/tiles/make_styles.py       (unchanged, re-measured after the mutant restore)
        194 services/tiles/styles/scenic-light.json  194 services/tiles/styles/scenic-dark.json (unchanged, re-measured)
         87 ops/publish-tiles                   (unchanged)

  Nothing is over 300 and nothing needed splitting. The two measured files that a mutant driver rewrote and
  restored (`make_styles.py`, both styles) were re-measured after the restore rather than assumed, which is
  what the correction-commit rule asks for.
  STILL OPEN, restated in full at this commit - none of it claimed by this task, and (1) is the only one
  whose wording changed:
  (1) `ops/test` cannot see `services/tiles/tests` - its python tier is gated on `services/etl/pyproject.toml`.
      There are 43 of them now (28 at 05:37:02Z) and they are still run directly and still NOT in the floor.
      Wiring the tier touches `ops/test`.
  (2) No glyphs and no sprites, so the basemap draws NO LABELS. Deliberate; the next tiles task, not a nicety.
  (3) `MapStyle` still has only the `maplibreDemoTiles` case and still credits "(c) MapLibre - Natural Earth".
      The Protomaps case and the plan's "(c) OpenStreetMap contributors - Protomaps" string land in
      `apps/ios/`, outside this task's `touches:`. Until then the app does not render these tiles.
  (4) Nothing is published. `ops/publish-tiles` needs the human's four env vars and a task holding
      `exclusive: [prod]`; the R2 prefix it writes (`tiles/v1/`) is a proposal, not an agreed layout.
  (5) The pinned `PLANET_BUILD=20260915` 404s in about a week. The recipe refuses by name when it does, but
      nothing reminds anybody; a scheduled rebuild belongs with the weekly ETL run.
  (6) P-ATTR-01 and P-DATA-03 are still not in `pins/PINS.yaml`. This task built the artifact those pins would
      assert over; filing them touches `pins/`.
  (7) NEW, from S2: nothing re-runs `check_pmtiles.py` against the artifact in `work/` on a schedule. The
      limbs added here only fire when somebody runs the recipe or the publish script; a 30-day-old `built_at`
      goes unnoticed until the next publish attempt. Same owner as (5) - the weekly rebuild.
- 2026-09-19T06:14:44Z REVIEW FAIL - PR #109, by agent/rv1-pr109 (reviewer, not the owner). Reviewed at
  936b259bc8aa38c325f7ee98583ce4395fe2262d in a detached worktree; `git status --short` empty after every
  mutant; worktree removed; nothing in the tree, the queue or the PR changed.
  SCOPE, re-derived off the merge-base (f4dae24) because df0c235 is the wrong base: 15 files, 2192
  insertions, 0 deletions, all inside `touches: [services/tiles/, ops/publish-tiles]` plus this task file,
  whose diff is append-only (0 removed lines). Modes 100755 on ops/publish-tiles and build-la.sh, 100644 on
  the rest.
  ACCEPTANCE BLOCK RE-RUN BARE AND MATCHED: 43 passed in 3.27s; `PMTILES OK: la.pmtiles region=la
  bytes=63520949 zoom=0-14 tiles=2549 bounds=(-119.000000,33.700000,-117.850000,34.450000)` exit=0;
  stat 63520949 and sha256 3b711c79...ae2b5a0a both equal to the sidecar; one `pmtiles show` through the
  pinned digest agreeing field for field (bounds, zoom 0-14, entries 2549, region la, built_at
  2026-09-19T05:02:38Z); the region bbox re-derived by hand from region.json (-119.0,33.7,-117.85,34.45)
  and covered with zero slack on all four edges; `PUBLISH REFUSED: 4 credential(s) not set: ...` first and
  exit 1; check-line-cap, check-exec-bits, queue-check (186 tasks), check-pins --source-only (ok=12
  skipped=13 pending=1 expired=0 failed=0) all green; every quoted `wc -l` identical. CI on #109: core pass,
  pins-source-only pass.
  S1 AND S2 RE-APPLIED, RED BY NAME: one hex digit in TOKENS + regenerate ->
  test_the_transcription_equals_the_declarations and test_no_token_is_invented_or_missing[light]; a
  max_zoom=10 fixture through the shipped CLI -> `header max_zoom 10 is below the required 14` exit=1.
  THREE MUTANTS OF MY OWN, TWO BLOCKING SURVIVORS:
  (B1) check_pmtiles.py:181 - replacing `bbox_from_region(args.region_json)` with the bbox as a literal
  leaves all 43 tests green. `test_the_bbox_is_read_from_the_region_file_not_typed` asserts on the helper,
  not on main(), and NOTHING in the suite calls main() at all. With region.json's max_lon corrected to
  -117.5 (a T-0142-shaped edit) the mutated checker prints PMTILES OK exit=0 on an archive the shipped
  checker refuses with `do not cover the region bbox (-119.0,33.7,-117.5,34.45)` exit=1. A tile set cut to
  a stale box passes the publish gate green.
  (B2) make_styles.py:59 with test_style_tokens.py:93 - adding "waters" to SOURCE_LAYERS and pointing the
  water layer at it regenerates both styles and leaves all 43 tests green, while
  `make_styles.py --check --archive la.pmtiles` says `archive is missing source-layer(s): ['waters']`
  exit=1. The guard is circular: the test asserts against the module's own typed tuple, and the one
  executable anchor to the archive's vector_layers is invoked by nothing - not build-la.sh, not
  ops/publish-tiles, not a test - although R6 cites it as the reason the layer names are not invented. It
  is the S1 defect (an unanchored transcription) left in place on the sibling table.
  RECORDABLE, not blocking: a future `built_at` passes the age limb (`built_at=2099-01-01` -> check() ==
  []) and the shipped stamp is already ahead of this box's clock; the tile-count limb is entries==0 only,
  so a 330-byte archive with 3 entries, right bounds and right stamp returns []; tile_meta.py (116 lines)
  has no test, so a hardcoded region or built_at there survives the suite; the archive's OWN metadata
  carries `attribution <a href=...>&copy; OpenStreetMap</a>`, so R6's "the renderer's control renders
  empty" needs MapAdapter to disable the control and does not follow from the style (apps/ios, outside
  touches - for T-0195); R6 vs @protomaps/basemaps and R1's six-day retention both judged SOUND as ruled.
  `pytest ... -q` prints no count because pyproject already sets addopts="-q".
  STILL OPEN 1-7 are known and were not re-litigated. reviewer: null and state: claimed left untouched.
- 2026-09-19T06:22:10Z ROUND-2 RULINGS by agent/claude-opus-5 (owner), before any code, on rv1-pr109's two
  BLOCKING findings and its four recordables. Both findings are ACCEPTED as stated and not argued: in each
  case the test named for the defect asserts on something other than the thing that can break, which is the
  S1 defect (an unanchored transcription) a second and a third time. The rulings below are about the SHAPE of
  the fix, because each one has a choice in it that the reviewer left to the owner.
  (B1) ACCEPTED. `check_pmtiles.main()` is the only entry point `build-la.sh` step 6 and `ops/publish-tiles`
  line 63 call, and nothing in the suite calls it; `test_the_bbox_is_read_from_the_region_file_not_typed`
  proves only that `bbox_from_region` can read a file. FIX: a subprocess test that runs the shipped CLI end to
  end - `python check_pmtiles.py <archive> --region-json <region.json>` - and asserts on stdout and the exit
  code, so main()'s wiring of the region file into check() is the subject. The RED subject is a fixture
  archive cut to the LA bounds against a tmp region.json whose `max_lon` is WIDER (-117.5, the T-0142 shape):
  the shipped CLI must print `PMTILES REFUSED` naming `(-119.0,33.7,-117.5,34.45)` and exit 1, which the
  literal-bbox mutant cannot do.
  (B1, the skip question) RULED: THE DOCUMENTED ENV VAR, `SCENIC_LA_PMTILES`, not the recipe's default path.
  The in-process fixture is the PRIMARY subject and it always runs, so the test named for the defect never
  depends on a 63 MB file being on the box. The real artifact is a SECOND SUBJECT of the same test, taken from
  `$SCENIC_LA_PMTILES` when it is set, and when it is set the test asserts `.is_file()` before it runs -
  a set-but-wrong path FAILS by name, it does not skip. No `pytest.skip`, no `skipif`, no empty parametrize
  anywhere in the new file: the suite must never report a green that is really an absence. The recipe's
  default path (`<main checkout>/services/tiles/work/la.pmtiles`) is rejected as the guard because that
  directory is gitignored and empty on CI and on every fresh clone, and a test that fails there is a test
  somebody deletes within the week - which would cost more than it buys. STILL OPEN (7) already owns the
  "nothing re-runs the checker against `work/` on a schedule" half, and this is the same gap, not a new one.
  (B2) ACCEPTED, and the circularity is exactly as described: `test_every_source_layer_exists_in_the_archive`
  asserts `layer['source-layer'] in SOURCE_LAYERS`, the typed tuple inside the module under test, so the
  tuple and the styles are two transcriptions checked against each other and against nothing. FIX, two parts.
  (a) The test reads `vector_layers` out of an ARCHIVE and asserts every committed style's source-layers are
  in it. The archive is a fixture built in-process whose metadata carries the nine layer ids typed IN THE
  TEST - the anchor moves out of the module under test, which is the whole point - and, when
  `$SCENIC_LA_PMTILES` is set, the real `la.pmtiles` as a second subject under the same rule.
  (b) `build-la.sh` gains step 7 running `make_styles.py --check --archive`, so the recipe refuses a style the
  archive it just built cannot draw, and a test asserts the recipe carries that invocation. That assertion is
  anchored on the command string `make_styles.py --check --archive`, an executable line, never on a comment.
  (R1) RECORDED AND FIXED. A future `built_at` passes the age limb because the limb is one-sided. The upper
  bound gets a literal skew tolerance, RULED at 1 hour (`MAX_FUTURE_SKEW = timedelta(hours=1)`): the recipe
  stamps `built_at` at step 1 and the check runs at step 6 on the SAME clock minutes later, and across two
  hosts the only legitimate gap is NTP drift, which is seconds. One hour is three orders of magnitude under
  the 30-day staleness floor, so it cannot mask a stale build, and it still refuses every wrong-DATE stamp -
  a year typed wrong, a host set to next month - which is what the limb is for.
  (R2) RECORDED AND FIXED. `tile_entries_count == 0` is the only tile limb, so a 330-byte truncation with
  entries=3 returns []. Two typed floors, both stated as parameters of `check()` so another region can state
  its own rather than inherit LA's. `MIN_TILE_ENTRIES = 256`: the real build measures 2549 entries, and 256 is
  an order of magnitude below it (2549/10 = 254.9, rounded up to a power of two) - far enough under that a
  re-pinned planet build or a bbox nudged by a tenth of a degree cannot trip it, and far enough over 3 that a
  truncated or half-written archive is refused. `MIN_BYTES = 1_048_576` (1 MiB): deliberately NOT an order of
  magnitude under the measured 63,520,949 but about sixty, because a byte floor's job is to catch a
  truncation or a half-finished download, not to track the size of the build - a floor set near the real size
  is a floor that refuses the first legitimate smaller region and gets lowered in a hurry by whoever hits it.
  (R3) RECORDED AND FIXED. `tile_meta.py` (116 lines) has no test at all, so a hardcoded region or built_at in
  the stamp survives the suite. A new `tests/test_tile_meta.py` drives both subcommands and asserts region,
  built_at, bbox, maxzoom and source_build appear in BOTH the merged metadata dict and the sidecar, and that
  the sidecar's `bytes` and `sha256` equal the file's own - measured with a second, independent hashlib pass
  over the bytes, not by calling `sha256_of` back.
  (R4, the attribution recordable) RULED SOUND and NOT FIXED HERE, unchanged from the earlier ruling: the
  archive's own metadata carries a `attribution` string, so making the renderer's control draw nothing needs
  `MapAdapter` to disable it, and `apps/ios/` is outside this task's `touches:`. It is T-0195's, and STILL
  OPEN (3) already names that boundary.
  FILE SHAPE, ruled before writing: the CLI tests do not go into `test_pmtiles_budget.py`. That file is 185
  lines of `check()`-limb tests and the new work would put it near the 300 cap with two kinds of test in it.
  The boundary of meaning is the subject: `test_pmtiles_budget.py` keeps the limbs of the FUNCTION, and a new
  `tests/test_check_pmtiles_cli.py` owns the COMMAND the recipe and the publish script actually run.
  `write_pmtiles`'s `entries` and `padding` defaults move up to the new floors so the existing limb tests keep
  their subjects unchanged rather than being edited one by one to dodge a floor they are not about.
  Every one of the five new checks is demonstrated RED first - B1 under the reviewer's own `sed` literal-bbox
  mutant, B2 under the reviewer's own "waters" mutant, R1/R2/R3 on fixtures - and quoted by name in the entry
  at the final commit.
- 2026-09-19T06:34:36Z ROUND-2 FIX by agent/claude-opus-5 (owner), one commit closing rv1-pr109's two BLOCKING findings
  and all three recordables. Every new assertion was seen RED first, by name, under a mutant of the defect it
  exists for, and the tree was restored BYTE FOR BYTE after each one: the driver snapshots every file a
  mutant can touch before the run and compares the copy-back with `filecmp.cmp(shallow=False)`, printing the
  comparison. It does not restore with `git checkout --`, which would have thrown away the uncommitted work.
  WHAT CHANGED, and nothing else: `check_pmtiles.py` (the two floors, the future-stamp limb, the naive-stamp
  normalisation, the floors as parameters), `build-la.sh` (step 7), `tests/test_pmtiles_budget.py` (the two
  fixture defaults moved onto the floors, six new limb tests), `tests/test_style_tokens.py` (the circular
  source-layer test replaced by an archive-anchored one, plus the table and the recipe), and two new files,
  `tests/test_check_pmtiles_cli.py` and `tests/test_tile_meta.py`. 43 tests -> 58 (15 new ids).
  RED THEN GREEN, quoted from the driver (`services/tiles/work/red_driver.py`, gitignored):
  (M1, B1) `main()` carries the bbox as a literal instead of reading region.json ->
    FAILED test_check_pmtiles_cli.py::test_the_cli_reads_the_bbox_from_the_region_file_it_is_given
    1 failed, 2 passed. Restored byte for byte: YES.
  (M2, B2) "waters" added to SOURCE_LAYERS and used by the water fill, both styles regenerated ->
    FAILED test_style_tokens.py::test_every_source_layer_exists_in_the_archive[light]
    FAILED test_style_tokens.py::test_every_source_layer_exists_in_the_archive[dark]
    FAILED test_style_tokens.py::test_the_generators_source_layer_table_is_the_archives
    3 failed, 14 passed. Restored byte for byte: YES (make_styles.py AND both style files).
  (M3, B2) the recipe stops running `make_styles.py --check --archive` ->
    FAILED test_style_tokens.py::test_the_build_recipe_checks_the_styles_against_the_archive
    1 failed, 16 passed. Restored byte for byte: YES.
  (M4, R1) the age limb looks backwards only, as it did ->
    FAILED test_pmtiles_budget.py::test_refuses_a_build_stamped_in_the_future[2099-01-01T00:00:00Z]
    FAILED test_pmtiles_budget.py::test_refuses_a_build_stamped_in_the_future[2099-01-01T00:00:00]
    2 failed, 23 passed. Restored byte for byte: YES.
  (M5, R2) neither floor fires, as neither did ->
    FAILED test_pmtiles_budget.py::test_refuses_a_truncated_archive
    1 failed, 24 passed. Restored byte for byte: YES.
  (M6, R3) the stamp hardcodes its region instead of reading the argument ->
    FAILED test_tile_meta.py::test_merge_stamps_the_arguments_into_the_source_metadata
    1 failed, 3 passed. Restored byte for byte: YES.
  THE SKIP QUESTION, as ruled at 06:22:10Z and as built: there is no `pytest.skip`, no `skipif` and no empty
  parametrize anywhere in `services/tiles/tests`. The fixture is the primary subject of both archive-anchored
  tests and always runs; the real build is a second subject named by `$SCENIC_LA_PMTILES`, and when that
  variable is set the test asserts `.is_file()` first, so a set-but-wrong path FAILS by name. Both runs are
  quoted below: 58 passed with the variable unset, 58 passed with it pointing at the built artifact - which
  is the run in which the shipped CLI and the real `vector_layers` are the subjects.
  ACCEPTANCE BLOCK RE-RUN BARE AT THIS COMMIT, every line quoted from the command:
  - `python -m pytest services/tiles/tests` -> `58 passed in 3.92s`, exit 0. With
    `SCENIC_LA_PMTILES=<main checkout>/services/tiles/work/la.pmtiles` -> `58 passed in 10.87s`, exit 0.
  - `python services/tiles/check_pmtiles.py <main>/services/tiles/work/la.pmtiles --region-json
    services/etl/regions/la/region.json` -> `PMTILES OK: la.pmtiles region=la bytes=63520949 zoom=0-14
    tiles=2549 bounds=(-119.000000,33.700000,-117.850000,34.450000)`, exit 0. The artifact is untouched by
    this round: 63,520,949 bytes, 2549 entries, the same numbers the floors were ruled from.
  - `python services/tiles/make_styles.py --check --archive <main>/services/tiles/work/la.pmtiles` ->
    `make_styles: all 9 source-layers present in la.pmtiles`, exit 0. This is step 7, and it is the first
    round in which anything runs it.
  - `bash -n services/tiles/build-la.sh` exit 0; `bash services/tiles/build-la.sh --help` prints the usage
    and exits 0. NO REBUILD: the extract, its sidecar and its digest are the ones measured at 05:02:38Z.
  - `bash ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8),
    none over 300 lines`, exit 0. It reads Swift only (T-0058), so the Python cap is measured by hand below.
  - `bash ops/lib/check-exec-bits` -> `P-OPS-01: 64 files, 23 required present, all modes correct`, exit 0.
  - `bash ops/queue-check` -> `QUEUE OK (186 tasks)`, exit 0.
  - `bash ops/check-pins --source-only` -> `PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux
    source-only`, exit 0. Run once, on this tree.
  - `git status --short` after the commit: empty.
  WC -L ON EVERY TOUCHED FILE, re-measured at this commit and not carried forward from the last entry:
        240 services/tiles/check_pmtiles.py   (198 before; the floors, the future limb and their rulings)
        128 services/tiles/build-la.sh        (122 before; step 7)
        231 services/tiles/tests/test_pmtiles_budget.py     (185 before)
        172 services/tiles/tests/test_style_tokens.py       (124 before)
         99 services/tiles/tests/test_check_pmtiles_cli.py  (new)
         87 services/tiles/tests/test_tile_meta.py          (new)
        233 services/tiles/make_styles.py     (unchanged, re-measured after M2 restored it)
        116 services/tiles/tile_meta.py       (unchanged, re-measured after M6 restored it)
         95 services/tiles/tests/test_design_tokens_match.py   70 services/tiles/tests/test_publish_refusal.py
         87 ops/publish-tiles                 (unchanged this round)
  Nothing is over 300. The CLI tests were NOT added to `test_pmtiles_budget.py`: that file is the limbs of
  the function and would have landed near the cap carrying two kinds of test, so the new file owns the
  command the recipe and the publish script actually run - the split ruled at 06:22:10Z, along the subject.
  STILL OPEN, restated in full at this commit - none of it claimed by this task, and (1) and (7) are the
  only ones whose wording changed:
  (1) `ops/test` cannot see `services/tiles/tests` - its python tier is gated on `services/etl/pyproject.toml`.
      There are 58 of them now (43 at 06:14:44Z) and they are still run directly and still NOT in the floor.
      Wiring the tier touches `ops/test`. T-0198 is filed for it.
  (2) No glyphs and no sprites, so the basemap draws NO LABELS. Deliberate; the next tiles task, not a nicety.
  (3) `MapStyle` still has only the `maplibreDemoTiles` case and still credits "(c) MapLibre - Natural Earth".
      The Protomaps case and the plan's "(c) OpenStreetMap contributors - Protomaps" string land in
      `apps/ios/`, outside this task's `touches:`. Until then the app does not render these tiles. T-0195.
  (4) Nothing is published. `ops/publish-tiles` needs the human's four env vars and a task holding
      `exclusive: [prod]`; the R2 prefix it writes (`tiles/v1/`) is a proposal, not an agreed layout.
  (5) The pinned `PLANET_BUILD=20260915` 404s in about a week. The recipe refuses by name when it does, but
      nothing reminds anybody; a scheduled rebuild belongs with the weekly ETL run.
  (6) P-ATTR-01 and P-DATA-03 are still not in `pins/PINS.yaml`. This task built the artifact those pins would
      assert over; filing them touches `pins/`. T-0197.
  (7) REWORDED: nothing runs the checker or the new style-vs-archive check against the artifact in `work/` on
      a schedule, and nothing sets `$SCENIC_LA_PMTILES` in CI. The limbs added here - both floors, the future
      stamp, the source-layers - fire when somebody runs the recipe, runs the publish script, or exports that
      variable before the suite. A `built_at` going 30 days old still goes unnoticed until the next publish
      attempt. Same owner as (5), the weekly rebuild, and it is the reason the real artifact is a second
      subject rather than a required one.
- 2026-09-19T06:45:16Z REVIEW PASS - PR #109 round 2, by agent/rv2-pr109 (reviewer, not the owner, not
  rv1-pr109). Reviewed at a3a697adda6766a8f5add5feac35e17f46122de4 in a detached worktree
  (.worktrees/rv2-pr109); `git status --short` empty after every mutant; worktree removed; nothing in the
  tree, the queue or the PR changed by the review itself.
  SCOPE `git diff 936b259..HEAD --stat`: 7 files, 539 insertions, 11 deletions - `services/tiles/`
  (build-la.sh, check_pmtiles.py, tests/test_pmtiles_budget.py, tests/test_style_tokens.py and the two new
  test files) plus this task file, all inside `touches: [services/tiles/, ops/publish-tiles]`. The task-file
  diff is append-only: `git diff 936b259..HEAD -- queue/ | grep -c '^-[^-]'` -> 0, and rv1-pr109's 06:14:44Z
  entry stands before the owner's 06:22:10Z rulings and 06:34:36Z fix. `git ls-files -s ops/publish-tiles
  services/tiles/build-la.sh` -> 100755 on both. ops/publish-tiles is unchanged this round.
  (B1) CLOSED. rv1's own mutant re-applied at the call site in `main()` - `bbox_from_region(args.region_json)`
  replaced by `(-119.0, 33.7, -117.85, 34.45)` -> FAILED
  test_check_pmtiles_cli.py::test_the_cli_reads_the_bbox_from_the_region_file_it_is_given, `1 failed, 2
  passed`, exit 1. The CLI is now the subject: the test runs the shipped file in a subprocess and the refusal
  names the box that came out of the region file.
  (B2) CLOSED. rv1's own "waters" mutant re-applied - `"waters"` added to SOURCE_LAYERS and the water fill
  pointed at it, both styles regenerated (`make_styles.py` exit 0) -> FAILED
  test_style_tokens.py::test_every_source_layer_exists_in_the_archive[light], [dark] and
  test_the_generators_source_layer_table_is_the_archives, `3 failed, 14 passed`, exit 1. The anchor now lives
  outside the module under test: the layer ids are read out of an archive's `vector_layers`.
  (R1) RED on a fixture: the future-stamp limb removed -> FAILED test_refuses_a_build_stamped_in_the_future
  [2099-01-01T00:00:00Z] and [2099-01-01T00:00:00], `2 failed, 23 passed`, exit 1.
  (R2) RED on a fixture: both truncation floors removed -> FAILED test_refuses_a_truncated_archive,
  `1 failed, 24 passed`, exit 1.
  (R3) RED on a fixture: `_provenance` hardcodes `"region": "la"` -> FAILED
  test_merge_stamps_the_arguments_into_the_source_metadata, `1 failed, 3 passed`, exit 1.
  Every mutant restored with `git checkout --`, `__pycache__` purged and 1.1s slept between runs (a .pyc
  keeps whole-second mtimes); `git status --short` printed empty after each of the six.
  NOTHING REGRESSED, every line quoted from the command, run bare: `python -m pytest services/tiles/tests` ->
  `58 passed in 3.45s` exit 0 (43 at 06:14:44Z, 15 new ids); with
  `SCENIC_LA_PMTILES=<main checkout>/services/tiles/work/la.pmtiles` -> `58 passed in 13.02s` exit 0. The
  real artifact is untouched, 63520949 bytes: `python services/tiles/check_pmtiles.py <main>/services/tiles/
  work/la.pmtiles --region-json services/etl/regions/la/region.json` -> `PMTILES OK: la.pmtiles region=la
  bytes=63520949 zoom=0-14 tiles=2549 bounds=(-119.000000,33.700000,-117.850000,34.450000)` exit 0, and step
  7 on the same file -> `make_styles: all 9 source-layers present in la.pmtiles` exit 0. `bash
  ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over
  300 lines` exit 0; `bash ops/lib/check-exec-bits` -> `P-OPS-01: 64 files, 23 required present, all modes
  correct` exit 0; `bash ops/queue-check` -> `QUEUE OK (186 tasks)` exit 0. Every `wc -l` the 06:34:36Z entry
  quotes re-measured on this tree and identical, file for file (240, 128, 231, 172, 99, 87, 233, 116, 95, 70,
  87). `bash ops/check-pins --source-only` was launched once on this tree in the background and died with
  the shell that started it before printing, so NO local pins result is claimed here; the same gate ran on
  this same commit in CI. CI on #109 (`gh pr checks 109`): core pass 1m58s, pins-source-only pass 1m4s.
  MY OWN MUTANT, ONE SURVIVOR - RECORDABLE, NOT BLOCKING. Same class as B1/B2 (the named test asserts on
  something other than the thing that breaks): comment out step 7 in build-la.sh -
  `# python3 "$TILES/make_styles.py" --check --archive "$OUT"` - and the whole suite is `58 passed` exit 0,
  test_the_build_recipe_checks_the_styles_against_the_archive included, although the recipe now runs no style
  check at all. The test greps the recipe's TEXT (`assert "--check --archive" in recipe`), which a commented
  -out invocation satisfies; its docstring's claim "anchored on the invocation, which is executed, never on a
  comment" does not hold, and CLAUDE.md forbids anchoring a guard on a comment for exactly this reason. NOT
  blocking: the mutant alone ships no wrong artifact - rv1's B2 subject is still caught by the
  archive-anchored test (the "waters" mutant is red above), and `ops/publish-tiles` line 63 still runs
  `check_pmtiles.py`. What it costs is the recipe-level style-vs-archive guard, which is the only executable
  comparison against the REAL archive while `$SCENIC_LA_PMTILES` is unset in CI - STILL OPEN (7) already owns
  that half. The fix is one line (search the recipe's non-comment lines only), and per CLAUDE.md's two-round
  clause it is filed rather than bought as a third round; this paragraph is the gap on the record.
  STILL OPEN (1)-(7) are known, unchanged and were not re-litigated. reviewer: agent/rv2-pr109, state: done,
  queue/claimed/ -> queue/done/. Do not merge from here; the merge is the owner's or the human's.
