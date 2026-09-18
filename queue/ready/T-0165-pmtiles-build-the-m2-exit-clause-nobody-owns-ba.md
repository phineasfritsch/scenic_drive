---
id: T-0165
title: PMTiles build - the M2 exit clause nobody owns: a Bay Area Protomaps extract under 120 MB, with a style that keeps the attribution corner free
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/tiles/, ops/publish-tiles]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "services/tiles/ holds the extract recipe (a digest-pinned go-pmtiles image run through WSL, the sfbay bbox read from services/etl/regions/sfbay/region.json, the max zoom RULED in the Log) and the built sfbay PMTiles measured: bytes printed by the build command and quoted, under 120 MB (plan M2 exit) - the number comes from the command, never from prose"
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
bbox - the sfbay bbox is `services/etl/regions/sfbay/region.json`), the digest-pinned `go-pmtiles` image (plan:
images pinned by digest; docker runs on this box through WSL only), max zoom vs the 120 MB budget (measure,
do not guess), the light/dark style JSON recoloured to the design tokens with the lower-right corner reserved
for attribution, where the artifact lives (R2 needs the human's Cloudflare credentials - build and measure
here, publish is a separate `exclusive: [prod]` step). `meta.region` and `built_at` for P-DATA-03.

## Log
- 2026-09-18T19:52:17Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
- 2026-09-18T23:04:01Z PROMOTED to ready/ by agent/claude-fable-5-1 (16:13 panel, STRATEGY second slot, grounded): a plan M2
  exit clause, `depends_on: []`, unowned since the 13:13 panel, and unclaimable in backlog/ with an empty
  acceptance block. Needs docker through WSL; start it when a slot frees after T-0146.
