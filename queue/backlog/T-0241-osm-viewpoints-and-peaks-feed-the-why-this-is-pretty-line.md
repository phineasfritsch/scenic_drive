---
id: T-0241
title: OSM viewpoints and peaks feed the 'why this is pretty' line and the Surprise candidate pool - never the per-way score
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/landmarks.py, services/etl/tests/test_landmarks.py, services/etl/tests/fixtures/]
pins_affected: []
reviewer: null
depends_on: [T-0208]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURED population (OSM POI probe, 2026-09-25, .artifacts/data-probe/osm-poi/, Geofabrik california sha256 c5f9b5b2...ecda4b): in the canyon window plus 2 km, 100 tourism=viewpoint, 73 natural=peak, 16 waterfalls, 4 saddles, 59 cliffs; as a per-way score term every form points the wrong way (AUC 0.30-0.475 over the owner's 8 good vs 4 busy roads; PCH 11.5 weight/km, Latigo 0.21, Old Topanga 0.19), so this task does NOT touch score.py - a guard test fails if score.py reads the landmark table"
  - "a landmark table (id, kind, name, lat/lon 5 dp, nearest way id within 300 m) lands in the OSM half of the corpus (ODbL); a route's explanation can name up to two landmarks it passes within 300 m, e.g. 'passes the Saddle Peak viewpoint' - a test over the T1 recorded route names at least one"
---
## Brief

The probe's recommendation: keep the extraction for destinations and explanation, not scoring. ops/sane's
'viewpoints >= 400' check (plan) will read this table.

## Log
- 2026-09-25T23:46:40Z filed by agent/claude-opus-5 (orchestrator) from the OSM POI probe.
