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

`check_pmtiles.py` refuses an archive whose header bounds do not cover the region bbox, whose size exceeds
120 MB, whose `meta.region` is not the region's id, or whose `built_at` is over 30 days old (P-DATA-03). It
parses the 127-byte v3 header itself rather than shelling out to the image, so it runs where there is no
docker and so a wrong-bounds fixture can be constructed in-process.

These tests are **not** in `ops/test`'s floor: its python tier is gated on `services/etl/pyproject.toml`
and does not know this directory exists. Wiring that tier is a task that touches `ops/test`.

## The styles

`make_styles.py` emits `styles/scenic-light.json` and `styles/scenic-dark.json` from one layer spec plus
the DesignTokens table, so the two appearances cannot drift. Every colour in either file is a token value
of that appearance, and `tests/test_style_tokens.py` asserts it.

The **lower-right corner is reserved for attribution** by contributing nothing to it: no source declares
`attribution`, so the renderer's own control draws nothing, and there is no `symbol` layer, so no label can
be placed there. `DesignSystem.AttributionFooter` owns that corner and draws the credit.

Not built here, and deliberately absent rather than faked: **glyphs and sprites**. There is no `glyphs` URL
in either style, so the basemap draws no labels — a style pointing `glyphs` at a URL that 404s would render
nothing while claiming it had them. `sources.protomaps.url` is `pmtiles://la.pmtiles`; the app rewrites it
to the on-device file URL after the first-run download.

## Publishing

`ops/publish-tiles` uploads the archive, its sidecar and both styles to R2. It **refuses** without
`CLOUDFLARE_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_BUCKET`, without
`queue/LOCKS/prod.lock`, and when the artifact's sha256 disagrees with its sidecar. It has never run: R2 is
the human's account and a publish needs a task holding `exclusive: [prod]`.
