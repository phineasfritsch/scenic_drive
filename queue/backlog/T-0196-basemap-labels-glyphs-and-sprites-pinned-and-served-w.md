---
id: T-0196
title: basemap labels - glyphs and sprites pinned by digest and served with the tiles, the style's glyphs/sprite URLs set, a check that every symbol layer's text-font exists in the glyph set
state: backlog
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
