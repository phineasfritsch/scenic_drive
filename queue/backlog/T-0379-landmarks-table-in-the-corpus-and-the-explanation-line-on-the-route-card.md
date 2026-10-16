---
id: T-0379
title: landmarks table in the corpus (OSM half, ODbL) and the 'passes ...' explanation line on the route card
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/schema.py, services/etl/etl/corpuswriter.py, services/etl/etl/corpus.py, services/etl/regionbuild/, services/etl/tests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0241]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST: a built LA corpus with the table - count rows by kind and named/unnamed and quote them beside T-0241's clip measurement (viewpoint 303 nodes + 3 ways, peak 335 nodes); a count predicate is written only after that."
  - "a `landmarks` table (osm_type, osm_id, kind, name NULL-able, ele_m NULL-able, lat/lon 5 dp, nearest_way_id NULL-able within 300 m via landmarks.nearest_way_id) is in schema.ODBL_TABLES, filled from landmarks.select by the region build; schema_version bumped and every consumer of the schema version re-measured."
  - "the route card's explanation line is fed by landmarks.explain (up to two names); the app text is the app task's, filed separately if it needs Sources/ or apps/ios."
  - "T-0241's A5 whitelist guard stays green: score.py and every term module still never name the landmarks."
---
## Brief

Filed by agent/claude-opus-5 from T-0241's ruling R2: T-0241 shipped services/etl/etl/landmarks.py (select,
elevation_m, nearest_way_id, explain) as a pure module because the corpus schema and writer were outside its
touches. This task stores it. The Surprise candidate pool (T-0241's title) may read the same table; that wiring
is ruled here, not assumed.

## Log
- 2026-10-16T13:43:29Z filed by agent/claude-opus-5 from T-0241 ruling R2.
