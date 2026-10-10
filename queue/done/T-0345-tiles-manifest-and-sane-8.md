---
id: T-0345
title: A tiles (PMTiles) OTA manifest shape exists, and ops/sane --prod's exit 8 checks it against this checkout as it checks the corpus manifest
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T23:24:24Z
lease_expires_at: 2026-10-10T05:24:24Z
worktree: .worktrees/T-0345
branch: task/T-0345
exclusive: []
touches: [ops/sane, ops/lib/, services/tiles/, pins/PINS.yaml]
pins_affected: [P-OPS-08, P-DATA-03]
reviewer: agent/rv3-t0345
depends_on: [T-0344]
verify: [ops/check-pins]
acceptance:
  - "A1 Shape as code: services/tiles/tiles_manifest.py carries FIELDS = (version, region, file, built_at, maxzoom, min_app_build, sha256, bytes) and problems(manifest, region=, file=, now=), the ONE decision both the writer and ops/sane run; its writer (`python services/tiles/tiles_manifest.py --archive <x.pmtiles> --region-json <region.json> --min-app-build N [--out P]`) reads region, built_at and maxzoom out of the archive's own metadata, measures bytes and sha256 off the bytes on disk, and refuses (exit 1, nothing written) any manifest problems() refuses. services/tiles/tests/test_tiles_manifest.py, through main(), asserts the written manifest by FULL equality against an independent recomputation, each refusal by name with no file written, and that the shipped `python ops/lib/sane_prod.py tiles ...` accepts the writer's output over this checkout's real region.json and BasemapResolver.swift; `python -m pytest -q services/tiles/tests` exits 0."
  - "A2 ops/sane --prod exit 8 checks the tiles manifest: the `tiles skip ... T-0345` row is gone; with TILES_MANIFEST_URL or ops/tiles-manifest-url unset it prints `tiles skip` naming the missing URL; unreachable or not 200 is FAIL 8; otherwise `sane_prod.py tiles services/etl/regions/la/region.json <BasemapResolver.swift>` decides: exact key set, version non-empty string, region == region.json id, file == the basename of BasemapResolver.applicationSupportPath (read as one whole line), built_at YYYY-MM-DDTHH:MM:SSZ not older than 30 days nor more than 1 h ahead, maxzoom int in [14, 15], min_app_build int >= 1, sha256 64 lowercase hex, bytes int in [1048576, 125829120] (check_pmtiles.MIN_BYTES/BUDGET_BYTES, imported, not retyped)."
  - "A3 Table (local fake only, never prod): ops/lib/check_sane_prod.py gains t- rows through the SHIPPED ops/sane (every field's checkout disagreement, both sides of every bound by margin, unset, 404, not-JSON, not-object, missing/extra key, precedence 7>6>8 with a bad tiles manifest), GENERATED xt-<field>-<variant> rows for every tiles field and variant its kind requires, and b- rows calling sane_prod.tiles with a FIXED clock on the exact bounds (30 d old ok / +1 s refused, 1 h ahead ok / +1 s refused); the meta-check refuses unless the tiles kinds equal tiles_manifest.FIELDS. Every existing row now also asserts `tiles ok`. `bash ops/lib/check-sane-prod --only <every t-, xt-, b- row plus q-green,m-green,m-unset,p-6-over-8,p-7-over-6-and-8>` exits 0 (the bare 60-min table is not re-run on this box; said so)."
  - "A4 RED first: the A3 --only set against the pre-change ops/sane (main's copy, via --sane) FAILS, quoted; and three one-line mutants of tiles_manifest.problems (age `<` -> `<=` off by the bound, maxzoom upper bound dropped, region compare dropped) each FAIL by case name, then green."
  - "A5 Line cap and split: check_sane_prod.py (300 lines at start) is split at a real seam - the fake Worker and the row parser move to ops/lib/sane_prod_fake.py, the tiles rows to ops/lib/sane_prod_tiles_cases.py; `wc -l` of every touched .py quoted, each <= 300."
  - "A6 Pins: P-OPS-08's statement names the tiles manifest and its new case count; P-DATA-03 records that the published tiles manifest carries the archive's own meta.region/built_at under the same thresholds; `python ops/lib/check-pins-yaml.py` passes. On the merged head the bare gates check-sane-exit-order, check-mutate-population, check-line-cap, check-pins-yaml, check-exec-bits and ops/queue-check each exit 0, quoted."
  - "A7 (rv1 B1) Checkout-side readers on TEMP files: ops/lib/sane_prod_checkout_cases.py carries c-<region>.<resolver> rows, the whole cross product of 8 region.json variants (id la, no id, int id, empty id, null id, not JSON, not an object, absent) x 9 BasemapResolver.swift variants (one la line, one CRLF la line, #if/#else la+other, two la lines, //-comment only, comment other + real la, comment la + real other, no line, absent), each calling the SHIPPED sane_prod.tiles(body, region, resolver, now=NOW) and comparing (accepted, line) by FULL equality to a line typed per pair (no string id or not exactly one whole applicationSupportPath line -> `cannot tell`; la.pmtiles -> accepted; other.pmtiles -> the file mismatch); the meta-check refuses unless the rows are the whole cross product and reach all four outcomes. RED by row name, then green: sane_prod.py mutants R1 checkout_tiles_file exactly-one -> first-wins, R2 RESOLVER_LINE_RE.fullmatch -> .search, R3 checkout_region string-id check dropped each FAIL. `bash ops/lib/check-sane-prod --only <the 72 c- rows + b-green,b-age-exactly-30-days,b-age-30-days-and-1s,b-future-exactly-1h,b-future-1h-and-1s,t-green,t-file-other,t-file-with-dir>` exits 0 on the merged head."
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
- 2026-10-10T02:08:19Z ACCEPTANCE re-run on the merged head c3af42b9 (origin/main 4f47d06f merged):
  - A1 `python -m pytest -o addopts= -q services/tiles/tests` -> `81 passed in 5.16s` (72 before + 9 new).
  - A2/A3 `bash ops/lib/check-sane-prod --only <123 names: 29 t-/p-tiles, 84 xt-, 5 b-, q-green, m-green,
    m-unset, p-6-over-8, p-7-over-6-and-8>` -> `SANE-PROD ok 123/123 cases passed (5 b- rows at a fixed clock;
    sane=ops/sane ...)`, rc=0. It took ~140 min on this loaded box (unbuffered rate ~17 s/case unloaded). The other
    133 pre-existing q-/m-/x- rows were NOT re-run: their only change is the added `tiles ok` assertion and the
    tiles default body, which every one of the 123 exercises (faster-verification-in-rounds); said so.
  - A4 as quoted above (6/6 red against main's ops/sane; M1, M2, M3 each FAILED by name; restored byte-identical).
  - A5 wc -l unchanged since 23:41: 266, 66, 156, 163, 130, 98 - all <= 300.
  - A6 `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=20`; check-mutate-population
    `P-PROC-06: every added module is covered or allowlisted; the floor of 147 holds` rc=0; check-line-cap
    `P-SRC-02: 563 Swift files tracked ... none over 300 lines` rc=0; `PINS-YAML ok pins=50 fields=403`; check-exec-bits
    rc=0; `QUEUE OK (344 tasks)`. PR #238 CI: core pass, pins-source-only pass.
  - main then moved to ae8267fe (T-0340: services/api, ops/lib hazard/disclaimer digests, ops/mutate hazardcopy) -
    none of this task's surfaces; merged as the last step, the fast gates re-run on that head below the push.
- 2026-10-10T02:53:15Z rv1-t0345 FAIL (PR #238, head 8a044aa0) B1 - RULED before code:
  - B1 stands: every row reads the one real BasemapResolver.swift and region.json, so the checkout-side readers
    are untested. R1 `checkout_tiles_file` exactly-one -> first-wins and R2 `RESOLVER_LINE_RE.fullmatch` ->
    `.search` (a // line counts) both survive the 81 pytest + 8 rows; checkout_region's `has no string id` too.
  - Disagreement brief vs reality: the brief says every new row "must fail closed ('cannot tell')", but its row
    (b) - a //-commented la.pmtiles line plus a real line naming other.pmtiles - CORRECTLY reads other.pmtiles, so
    the shipped check refuses on the file mismatch (`tiles manifest: file is 'la.pmtiles', BasemapResolver reads
    'other.pmtiles'`), not `cannot tell`; under R2 it becomes `cannot tell` (two lines). A row that demanded only
    `cannot tell` there would PASS under R2. Ruled: every c- row asserts (accepted, line) by FULL equality to a
    line typed in the table (full-equality-oracle), so (b) is red under R2 by its line, and two more rows pin R2
    from both sides: a comment-only resolver (cannot tell; R2 accepts) and a commented other.pmtiles line plus a
    real la line (accepted; R2 says cannot tell).
  - Shape (table-rows-as-functions-of-input): new ops/lib/sane_prod_checkout_cases.py, c-<region>.<resolver>
    rows = the cross product of 8 region.json variants (id la, no id, int id, empty id, null id, not JSON, not an
    object, absent) x 9 BasemapResolver variants (one la line, one CRLF la line, #if/#else la+other, two la lines,
    comment-only, comment other + real la, comment la + real other, no line, absent) = 72 rows, each written to
    TEMP files and run through the SHIPPED sane_prod.tiles(body, region, resolver, now=NOW). The expected line
    is a function of the pair (region checked first, then the resolver's typed file: None -> cannot tell,
    la.pmtiles -> accepted, other.pmtiles -> file mismatch); the meta-check refuses unless the table is the
    whole cross product and all four outcomes occur. check_sane_prod.py runs them beside the b- rows.
  - Recorded, not this PR: ops/sane's ops/tiles-manifest-url fallback is untested by construction (the table
    refuses to run while that file exists), the same as the corpus side's ops/corpus-manifest-url.
- 2026-10-10T02:56:09Z rv1 B1 BUILT: ops/lib/sane_prod_checkout_cases.py (110 lines; 72 c- rows = 8 region x 9
  resolver variants), check_sane_prod.py runs them beside the b- rows and its meta-check adds checkout_meta_problems
  and the c- names to the duplicate check (270 lines). sane_prod.py unchanged.
  - GREEN: `bash ops/lib/check-sane-prod --only <the 72 c- rows>` -> `SANE-PROD ok 72/72 cases passed (72 b-/c-
    rows through sane_prod.tiles at a fixed clock; ...)` rc=0.
  - RED, mutants of ops/lib/sane_prod.py (exact single-occurrence replace, __pycache__ purged, 1.1 s waits,
    `restored byte-identical: True`), each against the same 72 rows, each rc=1:
    R1 exactly-one -> first-wins: `FAIL c-id-la.if-else: got (True, 'tiles ... file la.pmtiles == checkout ...'),
    want (False, 'cannot tell: ...BasemapResolver.swift does not hold exactly one ...')`, `FAIL c-id-la.two-la`
    (same), `2 of 72 cases failed`.
    R2 fullmatch -> search: `FAIL c-id-la.comment-only: got (True, ...)`, `FAIL c-id-la.comment-other-real-la:
    got (False, 'cannot tell: ...'), want (True, ...)`, `FAIL c-id-la.comment-la-real-other: got (False, 'cannot
    tell: ...'), want (False, "tiles manifest: file is 'la.pmtiles', ...")`, `3 of 72 cases failed`.
    R3 checkout_region `isinstance(rid, str) and rid` dropped: `FAIL c-id-int.one-la: got (False, "tiles
    manifest: region is 'la', this checkout's region is 7"), want (False, 'cannot tell: ...region.json has no
    string id')` ... all 9 c-id-int.* rows, `9 of 72 cases failed`.
- 2026-10-10T03:01:57Z rv1 ACCEPTANCE on the merged head a0923050 (origin/main a16d2a98 merged last; only a queue
  move of T-0352 came in). Per faster-verification-in-rounds only the touched rows re-run:
  - A1 `python -m pytest -o addopts= -q services/tiles/tests` -> `81 passed in 8.89s` rc=0.
  - A3/A7 `bash ops/lib/check-sane-prod --only <72 c- rows + b-green,b-age-exactly-30-days,b-age-30-days-and-1s,
    b-future-exactly-1h,b-future-1h-and-1s,t-green,t-file-other,t-file-with-dir>` -> `SANE-PROD ok 80/80 cases
    passed (77 b-/c- rows through sane_prod.tiles at a fixed clock; sane=ops/sane, ...)` rc=0.
  - A7 RED as quoted at 02:56 (R1 2, R2 3, R3 9 of 72 failed by name; restored byte-identical).
  - A5 wc -l: check_sane_prod.py 270, sane_prod_checkout_cases.py 110, sane_prod_tiles_cases.py 156,
    sane_prod.py 163 - all <= 300.
  - A6 bare gates: `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=20` rc=0;
    `P-PROC-06: every added module is covered or allowlisted; the floor of 147 holds` rc=0; `PINS-YAML ok
    pins=50 fields=403` rc=0; check-exec-bits `P-OPS-01: 207 files, 23 required present, all modes correct` rc=0;
    `QUEUE OK (344 tasks)` rc=0.
- 2026-10-10T03:33:59Z agent/claude-opus-5 (owner): rv2-t0345 FAIL was ancestry-only (main gained PR #237 T-0308 and PR #239 T-0353; no sane/tiles file). Merged origin/main last as b24e6dbc. On the merged head, bare: check-mutate-population "every added module is covered or allowlisted; the floor of 147 holds" rc=0; check-pins-yaml rc=0; queue-check "QUEUE OK (351 tasks)" rc=0; check-sane-exit-order "SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10" rc=0; services/tiles pytest "81 passed". The c- rows (72) and R1/R2 reds stand from 44c7bf9c (rv2-t0345 76/76 green, R1/R2/M3/M4 red by name); the merge touched no file they read.
- 2026-10-10T03:50:40Z agent/rv3-t0345 (reviewer, round 3, ancestry only): review PASS on 26363ac9 (detached
  worktree .worktrees/rv3-t0345). `bash ops/lib/check-sane-prod --only <72 c- rows from
  sane_prod_checkout_cases.checkout_rows()>,b-green,t-green,t-file-other,t-file-with-dir` -> `SANE-PROD ok 76/76
  cases passed (73 b-/c- rows through sane_prod.tiles at a fixed clock; ...)` rc=0. Bare: check-mutate-population
  `P-PROC-06: every added module is covered or allowlisted; the floor of 147 holds` rc=0; check-pins-yaml
  `PINS-YAML ok pins=50 fields=403` rc=0; queue-check `QUEUE OK (351 tasks)` rc=0; check-sane-exit-order
  `SANE-EXIT-ORDER ok documented=2,7,3,6,9,8,4,10 code=2,7,3,6,9,8,4,10 calls=20` rc=0; `python -m pytest -o
  addopts= -q services/tiles/tests` -> `81 passed` rc=0. `gh pr checks 238` on 26363ac9: core pass (8m20s),
  pins-source-only pass (3m22s). Ancestry after a fresh fetch: origin/main moved 3fb61801 -> 309e5eab with
  queue-only drift (2c82e264 and 309e5eab: T-0359 backlog -> ready -> claimed, one file
  queue/claimed/T-0359-photon-search-local.md), so `merge-base --is-ancestor origin/main origin/task/T-0345` is 1
  on that drift alone; no gate, sane, tiles or pin file moved. Signed off; queue/claimed/ -> queue/done/.
