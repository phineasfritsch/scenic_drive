---
id: T-0028
title: Scenic score: designated byway overlay (Caltrans + FHWA), snapped to OSM ways
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Caltrans Scenic Highway System GIS layer + FHWA America's Byways. Public domain / state open data.
Snap to OSM ways and set a byway flag worth +0.15 to E, capped.

ORACLE: byway-flagged ways must rank materially above class- and region-matched non-byway ways. That is the
second external oracle in the plan (the first being Curvature).

## Log
