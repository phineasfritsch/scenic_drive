---
id: T-0196
title: basemap labels - glyphs and sprites pinned by digest and served with the tiles, the style's glyphs/sprite URLs set, a check that every symbol layer's text-font exists in the glyph set
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T06:04:45Z
lease_expires_at: 2026-10-18T06:04:45Z
worktree: .worktrees/T-0196
branch: task/T-0196
exclusive: []
touches: [services/tiles/, ops/publish-tiles, apps/ios/Packages/ScenicApp/Sources/MapAdapter/ScenicLightStyle.swift, apps/ios/Packages/ScenicApp/Sources/MapAdapter/ScenicDarkStyle.swift, ops/lib/check-safety-disclaimer-pinned]
pins_affected: []
reviewer: null
depends_on: [T-0165]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a glyph set (PBF ranges) and a sprite sheet for the fonts the style uses, fetched from a pinned source (protomaps/basemaps-assets or fontnik output; URL + sha256 recorded the way inputs/manifest.yaml records inputs), built into services/tiles/work/ beside la.pmtiles, sizes quoted"
  - "make_styles.py sets glyphs and sprite URLs from one variable; a test refuses a style whose symbol layer names a text-font with no glyph range on disk, RED first on a font that does not exist, then green; the style gains the label layers (road names, place names) it lacked, still recoloured to the tokens"
  - "ops/publish-tiles uploads glyphs/ and sprites/ with the tiles under the same prefix (still refusing without credentials and the prod lock); python -m pytest services/tiles/tests -q count line at the final commit"
---
## Brief

From T-0165's STILL OPEN 2 (PR #109): the LA basemap ships with NO glyphs or sprites, so it draws no labels -
deliberate (a glyphs URL that 404s renders nothing while claiming it has them) but a driving basemap without
street names is not shippable. The next tiles task, not a nicety.

## Log
- 2026-09-19T05:38:57Z filed by agent/claude-fable-5-1 from T-0165's STILL OPEN 2 (PR #109). Not started; after #109 merges.
- 2026-10-17T06:04:45Z claimed by agent/claude-opus-5; lease until 2026-10-18T06:04:45Z
- 2026-10-17T06:10:37Z agent/claude-opus-5 MEASURED (before any code):
  - M1 styles today: `services/tiles/styles/scenic-{light,dark}.json` carry NO `glyphs`, NO `sprite`, no
    symbol layer; `tests/test_style_tokens.py::test_no_glyphs_url_is_declared` and `::test_nothing_claims_the_lower_right_corner`
    (`symbols == []`) assert that absence. The app embeds both files byte-equal as raw literals
    (`MapAdapter/ScenicLightStyle.swift`, `ScenicDarkStyle.swift`, 221 lines each; `test_embedded_style_identity.py`
    SIZES light=4563 dark=4591) and `ScenicStyleDocument.materialize` rewrites ONLY `archivePlaceholder = "pmtiles://la.pmtiles"`.
  - M2 the archive (`services/tiles/work/la.pmtiles.meta.json`, main checkout, built 2026-09-19T05:02:38Z, planetiler
    0.10.2, Protomaps Basemap 4.15.2 per README): vector_layers fields (non-`name:xx`): roads = access is_bridge is_link
    is_tunnel kind kind_detail min_zoom name name2 name3 network.. oneway ref route script.. service shield_text.. sort_rank;
    places = capital kind kind_detail min_zoom name name2 name3 population population_rank ref script.. sort_key wikidata;
    landuse = kind sort_rank; water = bridge kind kind_detail layer min_zoom name.. sort_rank tunnel. There is NO `pmap:kind`
    field in any layer (the v3 spelling); every filter in today's style reads `["get", "pmap:kind"]`.
  - M3 upstream style (protomaps/basemaps `styles/src/base_layers.ts` @ main, package 5.7.2): text-font stacks
    `[t.regular || "Noto Sans Regular"]` x5, `[t.bold || "Noto Sans Medium"]` x2, `[t.italic || "Noto Sans Italic"]` x5;
    icon-image: "arrow" x1 plus 3 expression forms (POI kinds, shields). glyphs/sprite point at
    `https://protomaps.github.io/basemaps-assets/...` (a third-party CDN).
  - M4 the glyph/sprite source: `protomaps/basemaps-assets` has 0 releases and 0 tags; its README's own "Downloading
    Assets" names the repo archive as the distribution. Default branch `main` head = commit
    `028c18f713baecad011301ff7a69acc39bcc2ae7` (2025-10-31T07:55:36Z). Archive
    `https://github.com/protomaps/basemaps-assets/archive/028c18f713baecad011301ff7a69acc39bcc2ae7.tar.gz`:
    6,379,327 bytes, sha256 `57e40e8c512bd8042d0a3a251f19d0d1c8523ad963c666c3c6643bada4dc92d0`. Licences per README:
    `fonts/` SIL Open Font License (`fonts/OFL.txt` in the archive); `sprites/` derived from MIT-licensed tangrams/icons.
    Contents: fonts/Noto Sans Regular 256 files 6,240,473 B; Medium 256 / 3,613,867 B; Italic 256 / 1,224,916 B;
    Devanagari 4 / 391,985 B; sprites/v4 20 files 146,578 B (light.json 3549, light.png 16174, light@2x.json 3579,
    light@2x.png 28852, dark.json 3549, dark.png 16054, dark@2x.json 3579, dark@2x.png 28407; 53 icon names in light.json).
  - M5 attribution: `DesignSystem/AttributionFooter.swift` is a SwiftUI view over the map with its own ground
    (`surface.opacity(0.85)` + hairline); MapView keeps MapLibre's attribution button at topRight.
- 2026-10-17T06:10:37Z RULINGS:
  - R1 (Brief "URL + sha256 the way inputs/manifest.yaml records inputs" vs no upstream release): the pin is the commit
    archive above (url, verify sha256, sha256, bytes, licence, retrieved, consumed_by - manifest.yaml's field names) in
    `services/tiles/basemap_assets.json`, PLUS a tree digest of exactly the files extracted, because GitHub can
    regenerate an archive's bytes while the tree is unchanged; the tree digest is what proves the served files.
  - R2 (where served): same prefix as the archive. Layout `<prefix>/la.pmtiles`, `<prefix>/glyphs/<fontstack>/<range>.pbf`,
    `<prefix>/sprites/v4/<sheet>{,@2x}.{json,png}`; built into `services/tiles/work/` beside la.pmtiles (main checkout);
    `ops/publish-tiles` PUTs exactly the list `basemap_assets.py publish-list` prints, after the credential and lock gates,
    after `basemap_assets.py check`. No third-party CDN URL is ever in a committed style.
  - R3 (the URL value): `make_styles.ASSETS_BASE = "basemap://"` is the ONE variable; glyphs =
    `basemap://glyphs/{fontstack}/{range}.pbf`, sprite = `basemap://sprites/v4/<appearance>`. It is a placeholder
    exactly like `pmtiles://la.pmtiles`: the app must replace `basemap://` with the directory that holds la.pmtiles.
    `ScenicStyleDocument` does not do that yet (Swift, MapLibre-only target, not buildable on this box) - so ON DEVICE
    LABELS STAY ABSENT until that follow-up lands; recorded in STILL OPEN, not claimed.
  - R4 (fonts): the style uses `Noto Sans Regular` (road names) and `Noto Sans Medium` (place names). Only the stacks
    the styles reference are built (2 x 256 ranges, 9,854,340 B), not Italic/Devanagari. The check computes the font
    set from both committed styles and compares it WHOLE to the font directories on disk (missing AND extra refuse),
    and every referenced stack must have all 256 ranges. Sprites: the sheets the style URLs name (v4 light, dark, @1x/@2x)
    compared whole; every `icon-image` the style names must be a key of that sheet's JSON (none today: no icon layer -
    POI icons are not a driving-map feature; the check still refuses a named icon that is absent).
  - R5 (`pmap:kind` vs M2): the archive has `kind`, not `pmap:kind`; today's filters match nothing (roads-major and
    roads-motorway draw nothing, roads-minor draws every road, landuse-built draws parks). The label layers must filter
    on `kind`, and two spellings in one spec is the defect, so the field is fixed to `kind` here and
    `make_styles --check` gains a field check: every `["get", F]` on a protomaps layer must be a field the archive
    declares for that source-layer (test anchored on a field table typed in the test, not imported).
  - R6 (attribution vs label layers): `test_nothing_claims_the_lower_right_corner`'s `symbols == []` contradicts the
    acceptance's label layers. The footer is SwiftUI above the map with an 85% ground, so a map label cannot cover it;
    the assertion becomes: no source declares `attribution` (kept), owner metadata (kept), and the symbol layers are
    EXACTLY the whitelisted label ids (a new symbol layer is a deliberate edit of the test).
  - R7 (touches): regenerating the styles forces the two embedded Swift literals (byte-equal test) and their digest
    digest rows (`ops/lib/check-safety-disclaimer-pinned`, P-SAFE-03); touches widened to those three paths. No Swift
    logic changes.
  - R8 (screenshot): ios-screenshot runs without la.pmtiles on the simulator, so the home shot draws the demo
    basemap, not this style, and R3 keeps labels off-device anyway: a home shot CANNOT show these street labels. Not run
    as evidence of labels; said so in STILL OPEN.
  - R9 (mutation population): `basemap_assets.py` is set/path comparison, not a numeric module; no ops/mutate population.
- ACCEPTANCE (re-run and re-quoted at the final commit):
  - A1 `python -m pytest services/tiles/tests -q -p no:cacheprovider -o addopts=` -> count line, 0 failed.
  - A2 `python services/tiles/basemap_assets.py build --work <main>/services/tiles/work --archive <tarball>` then
    `python services/tiles/basemap_assets.py check --work <main>/services/tiles/work` -> exit 0, counts + sizes quoted.
  - A3 `python services/tiles/make_styles.py --check --archive <main>/services/tiles/work/la.pmtiles` -> exit 0.
  - A4 `bash ops/publish-tiles` with no credentials -> `PUBLISH REFUSED: 4 credential(s) not set ...`, exit 1.
  - A5 RED-then-GREEN by name: `test_a_style_naming_a_font_with_no_glyphs_is_refused` (font `Noto Sans Bold`).
  - A6 bare gates: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-pins-yaml.py,
    check-exec-bits, queue-check; `wc -l` of every touched file <= 300.
- 2026-10-17T06:38:12Z agent/claude-opus-5 RED then GREEN, by name:
  - A5 RED: `basemap_assets.check` written first WITHOUT the glyph limb (sprites + tree digest only); the fixture
    style names `Noto Sans Bold`, the tree built for the committed styles, the fixture pin records that tree:
    `FAILED test_basemap_assets.py::test_a_style_naming_a_font_with_no_glyphs_is_refused` -
    `AssertionError: assert 0 == 1` (test_basemap_assets.py:102); same run `6 failed, 12 passed`
    (also red: the extra-glyph-directory, two off-layout URLs, the text-font expression, the publish-tiles anchor).
    GREEN after the glyph limb (stacks compared whole + every requested range on disk) and the publish-tiles
    check/list lines: `18 passed in 78.73s`.
  - R5 RED: `KIND = "pmap:kind"` restored for one run: `test_style_tokens.py::test_every_field_a_layer_reads_is_in_the_archive`
    `AssertionError: assert 1 == 0` (`make_styles --check` refuses the v3 field), `1 failed`; `KIND = "kind"` back: `1 passed`.
  - A2 real build (main checkout `services/tiles/work`, from the downloaded tarball, sha256 verified by `build`):
    `basemap_assets: OK 2 font stack(s) ['Noto Sans Medium', 'Noto Sans Regular'] x 256 ranges, 2 sprite sheet(s),
    521 files 9962457 bytes, tree cd04e163d6f21932145c77046b2a5a527ad2e8a41764c7e9ed63289827f68f4b`, exit 0; sizes on
    disk: Noto Sans Regular 6,240,473 B, Medium 3,613,867 B, OFL.txt 4,374 B, sprites/v4 103,743 B. `publish-list` 521 lines.
  - A3 `make_styles: all 9 source-layers and every field the layers read present in la.pmtiles`, exit 0.
  - A4 `PUBLISH REFUSED: 4 credential(s) not set: CLOUDFLARE_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET`, exit 1.
  - Styles now write LF (`newline="\n"`): on this box `write_text` wrote CRLF and the embedded-literal sizes would
    have been measured over bytes git never commits. Re-measured SIZES light=5751 dark=5778; Swift literals 259 lines;
    P-SAFE-03 digests re-approved in `ops/lib/check-safety-disclaimer-pinned` (Dark 2a6175f3…, Light 7b0985dd…).
- 2026-10-17T06:54:18Z agent/claude-opus-5 ACCEPTANCE re-run at the final commit (`git fetch origin`: origin/main
  cf085098 is an ancestor of task/T-0196 - nothing to merge):
  - A1 `SCENIC_TILES_WORK=<main>/services/tiles/work SCENIC_LA_PMTILES=<main>/services/tiles/work/la.pmtiles
    python -m pytest services/tiles/tests -q -p no:cacheprovider -o addopts=` -> `104 passed in 50.27s`
    (`104 tests collected`; 18 of them in test_basemap_assets.py, 4 new in test_style_tokens.py).
  - A2 `basemap_assets: OK 2 font stack(s) ['Noto Sans Medium', 'Noto Sans Regular'] x 256 ranges, 2 sprite sheet(s),
    521 files 9962457 bytes, tree cd04e163…f68f4b`, exit 0. A3 exit 0 (quoted above). A4 refusal exit 1 (quoted above).
  - A5 RED/GREEN quoted in the 06:38:12Z entry.
  - A6 `EXIT 0` each: check-safety-disclaimer; check-mutate-population.py (`the floor of 171 holds`); check-mutate-only.py
    (`241 of 241 driver runs refused`); check-pins-yaml.py (`pins=52 fields=418`); check-exec-bits (`244 files, 23
    required present, all modes correct`; ops/publish-tiles 100755); queue-check (`QUEUE OK (379 tasks)`).
    `timeout 600 bash ops/lib/check-line-cap` -> EXIT 124 (timed out; not a pass). `wc -l` instead: make_styles.py 285,
    basemap_assets.py 201, test_basemap_assets.py 220, test_style_tokens.py 214, test_embedded_style_identity.py 139,
    README.md 98, build-la.sh 133, ops/publish-tiles 112, ScenicLightStyle.swift 259, ScenicDarkStyle.swift 259,
    scenic-light.json 232, scenic-dark.json 232 - all <= 300.
- STILL OPEN: (1) R3 - `ScenicStyleDocument` must replace `basemap://` with the directory holding la.pmtiles (and the
  glyphs/sprites must be copied/downloaded there) before ANY label draws on a device; Swift, MapLibre-only target, next
  task. (2) R8 - no ios-screenshot home shot can show these labels (no archive on the simulator; R3). (3) these tests
  are still outside ops/test's floor (T-0198 in flight wires services/*/pyproject.toml). (4) check-line-cap timed out.
- 2026-10-17T07:24:36Z agent/claude-opus-5 PRE-REVIEW FINDINGS closed by class (no BLOCKING survivor; two gaps):
  - G1 (class: a pin field no typed test reads). Mutant 3b, `tree_sha256` edited in basemap_assets.json, was green in
    CI because test_the_pin_records_the_measured_archive compared five fields one by one. Closed by WHITELIST: the test
    now asserts the WHOLE parsed pin `== MEASURED_PIN` (all 15 keys and values), so any field added, dropped or edited
    is a diff in that typed test - not one more field appended. MISSED (07:19:17Z, SCENIC_TILES_WORK unset, test
    unchanged): `MUTANT tree_sha256: exit 0`, `18 passed in 64.93s`. CAUGHT (07:21:51Z, same mutant, new test):
    `FAILED services\tiles\tests\test_basemap_assets.py::test_the_pin_records_the_measured_archive`,
    `1 failed, 17 passed in 87.25s`.
  - G2 (class: a publish-tiles refusal limb only ever shown in prose). A4 quoted the credential refusal; the prod-lock
    refusal the Brief's third line names was pre-existing and never re-demonstrated, and
    test_the_credential_gate_runs_before_every_other_gate accepts ANY refusal after the credentials. Closed fail-closed:
    the shipping ops/publish-tiles is copied alone into a fresh `git init` tree under tmp_path (no artifact, no styles,
    so nothing past the gates is reachable, and the lock's presence is set by the test, never by this box), run with
    all four credentials set to `x`; test_with_credentials_and_no_prod_lock_the_lock_refuses asserts the exact first
    line `PUBLISH REFUSED: queue/LOCKS/prod.lock not held (claim a task with exclusive: [prod])`, exit 1, and its pair
    test_with_the_prod_lock_held_the_lock_no_longer_refuses asserts the next gate's exact line
    (`... services/tiles/work/la.pmtiles does not exist - run services/tiles/build-la.sh first`), so the first line is
    the lock deciding. MISSED (07:19:17Z, mutant `if [ ! -f queue/LOCKS/prod.lock ]; then` -> `if false; then`, old
    tests): `MUTANT lock_gate_deleted: exit 0`, `3 passed in 12.39s`. CAUGHT (07:21:51Z, same mutant):
    `FAILED services\tiles\tests\test_publish_refusal.py::test_with_credentials_and_no_prod_lock_the_lock_refuses`,
    `1 failed, 4 passed in 26.11s`. Mutant driver: services/tiles/work/mutants_t0196.py (gitignored scratch; exact-once
    site, __pycache__ purged and 1.1 s between runs, file restored byte-for-byte).
  - Re-measured: test_basemap_assets.py 237, test_publish_refusal.py 107 (`wc -l`, both <= 300).
  - R3 stays STILL OPEN as recorded above (ScenicStyleDocument does not rewrite `basemap://`; Swift, outside touches);
    nothing here claims on-device labels.
- 2026-10-17T07:46:11Z agent/claude-opus-5 ACCEPTANCE re-run on the merged head (`git fetch origin`; origin/main 14727772 merged, one
  queue file, T-0389 backlog):
  - A1 `SCENIC_TILES_WORK=<main>/services/tiles/work SCENIC_LA_PMTILES=<main>/services/tiles/work/la.pmtiles
    python -m pytest services/tiles/tests -q -p no:cacheprovider -o addopts=` -> `106 passed in 118.51s` (104 + the
    two prod-lock tests).
  - A2 `basemap_assets: OK 2 font stack(s) ['Noto Sans Medium', 'Noto Sans Regular'] x 256 ranges, 2 sprite sheet(s),
    521 files 9962457 bytes, tree cd04e163d6f21932145c77046b2a5a527ad2e8a41764c7e9ed63289827f68f4b`, exit 0.
  - A3 `make_styles: all 9 source-layers and every field the layers read present in la.pmtiles`, exit 0.
  - A4 credentials: `PUBLISH REFUSED: 4 credential(s) not set: CLOUDFLARE_ACCOUNT_ID R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY R2_BUCKET`, exit 1; prod lock: test_with_credentials_and_no_prod_lock_the_lock_refuses passed
    in A1 (exact line, exit 1), red by name above.
  - A6 EXIT 0 each: check-safety-disclaimer; check-mutate-population.py (`the floor of 171 holds`); check-mutate-only.py
    (`NAME-PAIRS OK: 239389 pair tokens over 48 id populations`); check-pins-yaml.py (`pins=52 fields=418`);
    check-exec-bits (`244 files, 23 required present, all modes correct`); queue-check (`QUEUE OK (380 tasks)`).
    check-line-cap NOT re-run (EXIT 124 at 600 s last round); `wc -l`: test_basemap_assets.py 237,
    test_publish_refusal.py 107, the other touched files unchanged since 06:54:18Z - all <= 300.
  - STILL OPEN unchanged: (1) R3, (2) R8, (3) tests outside ops/test's floor until T-0198, (4) check-line-cap timeout.
- 2026-10-17T11:47:17Z agent/claude-opus-5 RULINGS for rv1 FAIL (agent/rv1-t0196, head 58e88ce4), before any code:
  - B1 ruled for the reviewer's SECOND arm: the embedded Swift styles carry NO `glyphs`, NO `sprite` and NO symbol
    layer until `ScenicStyleDocument` rewrites `basemap://`; the labels ship in the PUBLISHED styles and the R2 assets
    only. Why not the first arm: the rewrite plus a Linux-testable resolver means a new type in a root target and logic
    in `ScenicStyleDocument.swift`/`BasemapResolver.swift`, both outside touches and neither buildable on this box; the
    smaller honest result is a device style that cannot request a URL nothing serves. Shape: `make_styles.style(...,
    labels=False)` drops exactly `LABEL_LAYERS` and the two URL keys; `main` writes it to `styles/embedded/scenic-<a>.json`;
    the Swift literals are byte-equal to THOSE files (identity test retargeted, sizes re-measured). New guard, anchored on
    the shipping Swift literal and a WHITELIST: its top-level keys are exactly version/name/metadata/sources/layers, no
    layer is of type symbol, and every `scheme://` string in it is `ScenicStyleDocument.archivePlaceholder` read off that
    file's `static let` code line - the only string the shipping `materialize` rewrites. The `kind` filter fix (R5)
    stays in both. R3 CORRECTED (supersedes its last sentence): the earlier text said "on device labels stay absent";
    that was never checked and was wrong - with `basemap://` in the embedded style MapLibre's glyph request fails and,
    per rv1, every tile with a labelled feature never finished layout, so the WHOLE basemap would have been blank at
    driving zooms on any device with la.pmtiles. After this round the device style requests no glyph or sprite at all.
  - B2: a test runs the shipping `ops/publish-tiles` in a fresh git tree under tmp_path with every gate satisfied
    (credentials, prod.lock, a check_pmtiles-valid fixture archive + sidecar, the copied styles, a fixture glyph/sprite
    tree and a pin whose tree digest is that tree's), `curl` and `docker` stubbed first on PATH recording argv, and asserts
    the SET of curl upload URLs == `<endpoint>/<bucket>/<prefix>/` + basename of sidecar and both styles + every
    publish-list entry with spaces as %20, and the docker upload argv's key == `<prefix>/la.pmtiles` with the bucket URL.
