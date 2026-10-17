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
