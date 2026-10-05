---
id: T-0266
title: the ETL extract emits a places array from an OSM allowlist (viewpoint, peak, beach, waterfall, trailhead, park, garden, museum, cafe, town), chain-blocklisted, so the corpus places table, its FTS5 index and the Surprise pool are no longer empty
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T21:00:41Z
lease_expires_at: 2026-10-06T09:00:41Z
worktree: .worktrees/T-0266
branch: task/T-0266
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, services/etl/regions/la/, ops/mutate/, ops/lib/mutate-population-allowlist.json]
pins_affected: [P-PROD-03, P-DATA-01]
reviewer: null
depends_on: [T-0254]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST (CLAUDE.md): run the allowlist over the LA region (the tagged extract ops/etl-region already builds, via WSL docker, never git in WSL) and quote per-class counts, named-vs-unnamed, and 20 sampled rows in the Log BEFORE writing any count predicate"
  - "the extract's places array (the T-0254 load_places schema: osm_type, osm_id, cls, name, lat, lon) is produced from a typed allowlist of OSM tag -> cls, named features only, a literal chain/brand blocklist (brand=* / brand:wikidata on a blocklist, plus name matches) - each allowlist row and each blocklist row a test by name over a fixture OSM XML; every place passes load_places' validation (the T-0254 range table) unchanged"
  - "a corpus built from the LA extract has places > 0 per allowed class at the measured counts (within a ruled tolerance), PlaceStore.search finds three named LA features by prefix (e.g. a peak, a beach, a viewpoint chosen from the measured rows) - quoted; ODbL: places live in the OSM half (terms_osm) of the corpus"
  - "a mutation population under ops/mutate/ with a literal floor (allowlist row dropped, blocklist row dropped, unnamed accepted, cls swapped)"
---
## Brief

T-0254 (PR #152) shipped places + places_fts + PlaceStore.search but every corpus has zero places rows - the POI join
was explicitly deferred. Plan: 'Places: 30 curated seeds + Foursquare OS Places x Overture x OSM allowlist,
chain-blocklisted'. This is the OSM-allowlist third only (no FSQ/Overture downloads, no curation prose). T-0241
(OSM viewpoints/peaks feed the why-line) measured the canyon-window population on 2026-09-25; reuse its probe.

## Log
- 2026-10-05T20:58:07Z filed by agent/claude-opus-5 (orchestrator) after PR #152 merged: the plan sheet's typed search and the Surprise pool have no rows.
- 2026-10-05T21:00:41Z claimed by agent/claude-opus-5; lease until 2026-10-06T09:00:41Z
