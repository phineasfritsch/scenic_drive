# services/tiles — the Protomaps basemap

The LA PMTiles extract and the two styles the app renders it with. Built by T-0165 as the plan's M2 exit
clause ("PMTiles <120 MB"), and as the first half of crediting
`© OpenStreetMap contributors · Protomaps` honestly: until these tiles exist the app draws MapLibre's demo
basemap, which contains no OpenStreetMap data at all.

## Build

Docker is only reachable through WSL on the Windows box this repo is driven from:

    wsl -e bash -lc "bash /mnt/c/.../scenic_drive/.worktrees/<task>/services/tiles/build-la.sh"

It probes the pinned planet build, cuts the region bbox out of it over HTTP range requests (no planet
download — 52 requests, ~10 s, 67 MB transferred), stamps `region` and `built_at` into the archive's own
JSON metadata, measures, refuses over 120 MB, writes the sidecar and runs `check_pmtiles.py`.

| | |
|---|---|
| source | `https://build.protomaps.com/20260915.pmtiles` (Protomaps Basemap 4.15.2, planetiler 0.10.2, OSM replication 2026-09-15T04:00:00Z) |
| image | `protomaps/go-pmtiles@sha256:06574f01f55a78f78f887bc7ebf729a5c093c0d6e17d9876300cfcb0758b59d3` (pmtiles v1.31.2) |
| bbox | read from `services/etl/regions/la/region.json`, never typed here |
| maxzoom | 14 — measured: z15 is 197 MB, z14 is 64 MB, z13 is 20 MB |
| result | 63,520,949 bytes, zoom 0–14, 3030 addressed tiles |

**The pinned build date expires.** `build.protomaps.com` keeps only the last few days (measured 2026-09-19:
`20260913` live, `20260912` gone). When `PLANET_BUILD` 404s the recipe refuses by name; re-pin it, rebuild,
and **re-measure** — the zoom ladder is a property of the build, not a constant.

## Where the artifact lives

`services/tiles/work/` **in the main checkout**, never in a worktree: `git worktree remove` deletes a
worktree's ignored files with it. `--out` overrides. Nothing built is committed.

## The check

    python -m pytest services/tiles/tests -q
    python services/tiles/check_pmtiles.py <file.pmtiles> --region-json services/etl/regions/la/region.json

`check_pmtiles.py` refuses an archive whose header bounds do not cover the region bbox, whose header
`max_zoom` is below the ruled 14 (`--min-maxzoom`), whose header `max_zoom` and `meta.maxzoom` disagree,
which carries no tile entries at all, whose size exceeds 120 MB, whose `meta.region` is not the region's
id, or whose `built_at` is over 30 days old (P-DATA-03). It parses the 127-byte v3 header itself rather
than shelling out to the image, so it runs where there is no docker and so every one of those fixtures can
be constructed in-process.

The zoom floor is the limb the budget cannot supply: every zoom *below* 14 is a **smaller** file, so
`build-la.sh --maxzoom 12` writes a ~20 MB archive that fits the ceiling while the map goes soft two zoom
levels early. The 120 MB ceiling itself has one definition, `check_pmtiles.BUDGET_BYTES`, which the recipe
reads at step 3 rather than keeping a second copy of the number.

These tests are **not** in `ops/test`'s floor: its python tier is gated on `services/etl/pyproject.toml`
and does not know this directory exists. Wiring that tier is a task that touches `ops/test`.

## The styles

`make_styles.py` emits `styles/scenic-light.json` and `styles/scenic-dark.json` from one layer spec plus
the DesignTokens table, so the two appearances cannot drift. Every colour in either file is a token value
of that appearance, and `tests/test_style_tokens.py` asserts it.

`make_styles.TOKENS` is a transcription, so `tests/test_design_tokens_match.py` anchors it: it parses the
`public static let` declarations out of `DesignSystem/DesignTokens.swift` — never the doc-comment table
above them — and asserts the transcription equals them per appearance. Without it, editing a hex digit in
`TOKENS` and regenerating moves the whole suite with it and ships a colour the app does not have.

The **lower-right corner belongs to attribution**: no source declares `attribution`, so the renderer's own
control adds nothing, and `DesignSystem.AttributionFooter` is drawn above the map on its own 85% `surface`
ground, so a label underneath cannot cover the credit. The symbol layers are exactly `roads-label` and
`places-label`; the test lists them, so a new one is a deliberate edit.

## Labels: glyphs and sprites

`glyphs` and `sprite` hang off one variable, `make_styles.ASSETS_BASE = "basemap://"`, a placeholder like
`pmtiles://la.pmtiles`: the files sit beside the archive under the same prefix
(`glyphs/<fontstack>/<range>.pbf`, `sprites/v4/<appearance>{,@2x}.{json,png}`), never on a third-party CDN.
Only the PUBLISHED styles (`styles/scenic-<appearance>.json`) carry them. `ScenicStyleDocument` rewrites only
`pmtiles://la.pmtiles`, and a glyph request MapLibre native cannot load leaves every labelled tile without ANY
layer, so the EMBEDDED styles (`styles/embedded/`, byte-equal to the Swift literals in MapAdapter) carry no
`glyphs`, no `sprite` and no symbol layer until the app rewrites `basemap://` to the archive's directory
(`test_the_device_style_requests_nothing_the_app_does_not_rewrite`). `make_styles.py` writes all four.

    python services/tiles/basemap_assets.py build --work services/tiles/work [--archive TARBALL]
    python services/tiles/basemap_assets.py check --work services/tiles/work

`basemap_assets.json` pins the source: protomaps/basemaps-assets has no releases, so the pin is the commit
archive (`028c18f`, 6,379,327 bytes, sha256 `57e40e8c…`) plus a digest of the extracted tree (521 files,
9,962,457 bytes: Noto Sans Regular and Medium x 256 ranges, `OFL.txt`, the v4 light/dark sheets). Fonts are
SIL OFL 1.1 (`glyphs/OFL.txt` ships with them); sprites derive from MIT-licensed tangrams/icons. `check`
computes the font stacks and sheets from both committed styles and compares them WHOLE to what is on disk.

## Publishing

`ops/publish-tiles` uploads the archive, its sidecar, both styles and exactly the files
`basemap_assets.py publish-list` names (after `basemap_assets.py check`) to R2 under one prefix. It **refuses** without
`CLOUDFLARE_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_BUCKET`, without
`queue/LOCKS/prod.lock`, and when the artifact's sha256 disagrees with its sidecar. It has never run: R2 is
the human's account and a publish needs a task holding `exclusive: [prod]`.

That refusal is a test, not a paragraph: `tests/test_publish_refusal.py` runs the script bare with the four
variables stripped from the environment and asserts the credential refusal is the **first** line it prints.
Move the credential gate below the lock or artifact gates and the test goes red.
