---
id: T-0345
title: A tiles (PMTiles) OTA manifest shape exists, and ops/sane --prod's exit 8 checks it against this checkout as it checks the corpus manifest
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/sane, ops/lib/, services/tiles/, pins/PINS.yaml]
pins_affected: [P-OPS-08, P-DATA-03]
reviewer: null
depends_on: [T-0344]
verify: [ops/check-pins]
acceptance: []
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
