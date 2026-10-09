---
id: T-0345
title: A tiles (PMTiles) OTA manifest shape exists, and ops/sane --prod's exit 8 checks it against this checkout as it checks the corpus manifest
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T23:24:24Z
lease_expires_at: 2026-10-10T05:24:24Z
worktree: .worktrees/T-0345
branch: task/T-0345
exclusive: []
touches: [ops/sane, ops/lib/, services/tiles/, pins/PINS.yaml]
pins_affected: [P-OPS-08, P-DATA-03]
reviewer: null
depends_on: [T-0344]
verify: [ops/check-pins]
acceptance:
  - "A1 Shape as code: services/tiles/tiles_manifest.py carries FIELDS = (version, region, file, built_at, maxzoom, min_app_build, sha256, bytes) and problems(manifest, region=, file=, now=), the ONE decision both the writer and ops/sane run; its writer (`python services/tiles/tiles_manifest.py --archive <x.pmtiles> --region-json <region.json> --min-app-build N [--out P]`) reads region, built_at and maxzoom out of the archive's own metadata, measures bytes and sha256 off the bytes on disk, and refuses (exit 1, nothing written) any manifest problems() refuses. services/tiles/tests/test_tiles_manifest.py, through main(), asserts the written manifest by FULL equality against an independent recomputation, each refusal by name with no file written, and that the shipped `python ops/lib/sane_prod.py tiles ...` accepts the writer's output over this checkout's real region.json and BasemapResolver.swift; `python -m pytest -q services/tiles/tests` exits 0."
  - "A2 ops/sane --prod exit 8 checks the tiles manifest: the `tiles skip ... T-0345` row is gone; with TILES_MANIFEST_URL or ops/tiles-manifest-url unset it prints `tiles skip` naming the missing URL; unreachable or not 200 is FAIL 8; otherwise `sane_prod.py tiles services/etl/regions/la/region.json <BasemapResolver.swift>` decides: exact key set, version non-empty string, region == region.json id, file == the basename of BasemapResolver.applicationSupportPath (read as one whole line), built_at YYYY-MM-DDTHH:MM:SSZ not older than 30 days nor more than 1 h ahead, maxzoom int in [14, 15], min_app_build int >= 1, sha256 64 lowercase hex, bytes int in [1048576, 125829120] (check_pmtiles.MIN_BYTES/BUDGET_BYTES, imported, not retyped)."
  - "A3 Table (local fake only, never prod): ops/lib/check_sane_prod.py gains t- rows through the SHIPPED ops/sane (every field's checkout disagreement, both sides of every bound by margin, unset, 404, not-JSON, not-object, missing/extra key, precedence 7>6>8 with a bad tiles manifest), GENERATED xt-<field>-<variant> rows for every tiles field and variant its kind requires, and b- rows calling sane_prod.tiles with a FIXED clock on the exact bounds (30 d old ok / +1 s refused, 1 h ahead ok / +1 s refused); the meta-check refuses unless the tiles kinds equal tiles_manifest.FIELDS. Every existing row now also asserts `tiles ok`. `bash ops/lib/check-sane-prod --only <every t-, xt-, b- row plus q-green,m-green,m-unset,p-6-over-8,p-7-over-6-and-8>` exits 0 (the bare 60-min table is not re-run on this box; said so)."
  - "A4 RED first: the A3 --only set against the pre-change ops/sane (main's copy, via --sane) FAILS, quoted; and three one-line mutants of tiles_manifest.problems (age `<` -> `<=` off by the bound, maxzoom upper bound dropped, region compare dropped) each FAIL by case name, then green."
  - "A5 Line cap and split: check_sane_prod.py (300 lines at start) is split at a real seam - the fake Worker and the row parser move to ops/lib/sane_prod_fake.py, the tiles rows to ops/lib/sane_prod_tiles_cases.py; `wc -l` of every touched .py quoted, each <= 300."
  - "A6 Pins: P-OPS-08's statement names the tiles manifest and its new case count; P-DATA-03 records that the published tiles manifest carries the archive's own meta.region/built_at under the same thresholds; `python ops/lib/check-pins-yaml.py` passes. On the merged head the bare gates check-sane-exit-order, check-mutate-population, check-line-cap, check-pins-yaml, check-exec-bits and ops/queue-check each exit 0, quoted."
---
## Brief

T-0344 R5: the plan's exit 8 is "R2 manifest != config" for the corpus AND the tiles, but no tiles manifest shape
exists anywhere - BasemapResolver reads Application Support tiles/la.pmtiles and services/tiles builds the archive
with no manifest beside it - so ops/sane prints `tiles skip` naming this task. MEASURE FIRST: what services/tiles
(tile_meta.py, check_pmtiles.py) records about a built archive, what the app would need to download and verify one
(the corpus manifest's {version, schema_version, min_app_build, sha256, bytes} is the model), and what this checkout
pins that a published tiles manifest could disagree with (region, style archive name `la.pmtiles`, P-DATA-03's
meta.region and built_at). Then rule the shape and write the acceptance; the ops/sane half reuses
ops/lib/sane_prod.py and gains cases in ops/lib/check_sane_prod.py (local fake only, never prod).

## Log
- 2026-10-09T14:21:53Z filed by agent/claude-opus-5 from T-0344 R5 (tiles manifest out of scope there: no shape).
- 2026-10-09T23:24:24Z claimed by agent/claude-opus-5; lease until 2026-10-10T05:24:24Z
- 2026-10-09T23:30:04Z MEASURED (read, on main 423517b5):
  - services/tiles/tile_meta.py `sidecar` writes `<archive>.json` = {region, built_at, bbox, maxzoom, source_build,
    source_url, source_replication_time, bytes, sha256, file}; region/built_at/maxzoom come from the ARGUMENTS
    (only source_replication_time is read back out of the archive). Its docstring: bytes and sha256 are "the two
    facts that cannot be inside the file ... A first-run download sheet needs both before it has the file".
  - services/tiles/check_pmtiles.py decides an archive: meta.region == region.json id, built_at not older than
    MAX_AGE_DAYS=30 nor more than MAX_FUTURE_SKEW=1 h ahead, header max_zoom >= MIN_MAXZOOM=14 and == meta.maxzoom,
    entries >= 256, MIN_BYTES=1_048_576 <= size <= BUDGET_BYTES=125_829_120.
  - BasemapResolver.swift: `applicationSupportPath = "tiles/la.pmtiles"` (line 35, M4's download target),
    `minimumArchiveBytes = 1_048_576` (= MIN_BYTES). To download and verify it needs the file name, bytes, sha256.
  - Corpus manifest (CorpusManifest.swift, sane_prod.manifest): exactly {version, schema_version, min_app_build,
    sha256, bytes}; version non-empty string, schema_version == checkout schema.py, min_app_build int >= 1, sha256
    64 lowercase hex, bytes int >= 1; ops/sane fails 8 on unreachable or refused.
  - This checkout pins: services/etl/regions/la/region.json id `la`; `la.pmtiles`; P-DATA-03 meta.region == la and
    built_at < 30 days. ops/publish-tiles PUTs the archive and the SIDECAR to $PREFIX/ - no manifest is published.
  - The Protomaps planet build's own maxzoom is 15: an extract cannot be finer than its source.
- RULINGS:
  - R1 A SEPARATE manifest, not the sidecar. The sidecar is provenance (7 build fields nobody on the phone reads),
    copies region/built_at from argv rather than the archive, has no min_app_build/version, and is the input
    ops/publish-tiles verifies; an exact-key-set rule like CorpusManifest's would refuse it. The tiles manifest is
    {version, region, file, built_at, maxzoom, min_app_build, sha256, bytes} with the A2 rules; version is the
    compact built_at (`20261006T000000Z`, the corpus's version form) and is only checked non-empty, as the corpus's.
  - R2 One decision: services/tiles/tiles_manifest.py `problems()` is imported by the writer AND by
    ops/lib/sane_prod.py, and imports MIN_BYTES/BUDGET_BYTES/MIN_MAXZOOM/MAX_AGE_DAYS/MAX_FUTURE_SKEW from
    check_pmtiles - one number per fact. MAX_MAXZOOM=15 is new (the planet build's maxzoom; both bounds tested).
  - R3 What "this checkout" means for tiles: region from region.json `id` (read), file from BasemapResolver's
    applicationSupportPath line (one whole line, a whitelist read, never a comment); built_at against the host clock.
    Exact clock bounds cannot be hit through ops/sane (the run takes seconds), so they are b- rows calling the
    shipping function sane_prod.tiles(..., now=FIXED); the ops/sane rows test each side by a 10-minute margin,
    their bodies computed when the case RUNS (the full table takes ~60 min, an import-time stamp would drift).
  - R4 Exit code 8 for tiles too (plan: "R2 manifest != config" for corpus AND tiles); TILES_MANIFEST_URL or
    ops/tiles-manifest-url, unset is a skip naming the missing URL, as the corpus side. EXIT_ORDER unchanged.
  - R5 Out of scope, recorded: publishing the manifest (ops/publish-tiles is not in touches) and wiring the writer
    into build-la.sh (docker, not runnable here); the app's downloader (M4). services/tiles is not a
    check-mutate-population root (MODULE_ROOTS = services/etl/etl, Sources), so no ops/mutate population is
    required; A4's three mutants are the kill evidence. P-DATA-03's assertion command stays (pin assertions run
    no pytest anywhere in PINS.yaml); its statement records the manifest half.
- 2026-10-09T23:41:40Z BUILT: services/tiles/tiles_manifest.py (FIELDS, problems(), build(), main()),
  services/tiles/tests/test_tiles_manifest.py, ops/lib/sane_prod.py `tiles`, ops/sane exit-8 tiles block (the
  `tiles skip ... T-0345` row is gone), check_sane_prod.py split: fake + row parser -> sane_prod_fake.py, tiles
  rows -> sane_prod_tiles_cases.py. Case count: 251 ops/sane cases (138 before + 113 tiles: 29 hand-written, 84
  generated xt-) + 5 b- rows; meta-check `[]`. `bash ops/lib/check-sane-exit-order` ->
  `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=20`. wc -l: check_sane_prod.py 266,
  sane_prod_fake.py 66, sane_prod_tiles_cases.py 156, sane_prod.py 163, tiles_manifest.py 130,
  test_tiles_manifest.py 98. A pre-pytest run caught my own fixture bug (good_metadata got built_at twice); fixed.
- 2026-10-09T23:41:40Z A4 RED FIRST, against main's ops/sane (`--sane <git-common-dir>/T0345-sane-main`,
  `--only t-green,t-404,t-region-other,t-maxzoom-above,xt-sha256-under-long,p-7-over-tiles-8`):
  `SANE-PROD FAIL t-green: row tiles ['skip'], want [ok]` ... `t-404: exit 0, want 8; row tiles ['skip'], want
  [FAIL]` ... `SANE-PROD FAIL 6 of 6 cases failed`. (A subset: the old script prints `tiles skip` for every row.)
- 2026-10-09T23:41:40Z A4 MUTANTS of problems(), byte-checked restore (`restored byte-identical: True`):
  M1 age `<` -> `<=`: exit 1, `FAIL b-age-exactly-30-days: accepted=False, want True`;
  M2 maxzoom upper bound dropped: exit 1, `t-maxzoom-ceiling` pass, `FAIL t-maxzoom-above: exit 0, want 8`;
  M3 region compare dropped: exit 1, `FAIL t-region-other` and `FAIL t-region-case` (exit 0, want 8).
  Green before them: `--only t-green,t-unset,t-region-other,b-*(5)` -> `SANE-PROD ok 8/8 cases passed`.
