---
id: T-0276
title: DECIDE how the full LA corpus fits the 60 MiB budget - measured 214126592 B, options from T-0275
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/regionbuild/, services/etl/tests/]
pins_affected: [P-DATA-01, P-PROD-05]
reviewer: null
depends_on: [T-0275]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the OWNER picks one option (or a combination) from the table below, quoted with its measured bytes; the pick is recorded in this Log before any code"
  - "the picked reduction ships in the corpus stage (regionbuild corpus / etl.corpus) and `ops/etl-region corpus` on LA exits 0 with CORPUS-FILE bytes under 62914560, quoted from the run; a second run gives the same content digest (P-DATA-01)"
  - "what the pick drops is measured, not asserted: the ways/segments/places lost, by class, quoted from the run; if residential ways are dropped, the named LA drives the owner cares about (Saddle Peak Road among them) are checked present or absent by way id"
---
## Brief

T-0275 built the FULL LA corpus (ways + segments + places) from the region build's 152 seam-deduped tile
docs through extractadapter --places-osm into etl.corpus (`ops/etl-region corpus`, store /home/phineas/t0242)
and measured it, twice, identical content digest 60cc4058...ab63b15:

    CORPUS-MERGE tiles=152 rows_seen=574396 ways=560304 seam_ways=13946 seam_differ=0
    CORPUS-ROWS osm_features=560208 segments=874391 places=4773
    CORPUS-FILE bytes=214126592 budget=62914560 over_by=151212032   (3.40x the plan's corpus < 60 MiB)
    CORPUS-DBSTAT segments=83640320 osm_features=44040192 segments_rtree_node=35864576 segments_by_way=18804736
                  segments_rtree_rowid=15728640 osm_features_by_cls=14569472  (places, all tables: ~1.1 MB)

Ways by class: service=312645 residential=99715 primary=45535 secondary=43198 tertiary=25798 motorway=17394
track=8148 unclassified=5460 trunk=2117 living_street=195 road=3.

THE OPTIONS, each a real file built by the shipping etl.corpus.build over T-0275's LA extract (T-0275 Log):

    option                                          bytes        vs 62914560   what it loses
    (A) drop service-class ways                     117,960,704  OVER 55.0 MB  312,645 driveways/aisles/alleys
    (B) drop service+residential+living_street       62,836,736  under 77,824  412,555 ways incl. residential hillside streets
    (C) geometry as zigzag-varint deltas, e7         197,713,920  OVER 134.8 MB lossless; schema CHECK + decoder change
        same, e6 (~0.1 m) / e5 (~1.1 m)             193,548,288 / 190,640,128  OVER; geometry is only 32 MB of the file
    (B)+(C e6)                                       56,586,240  under 6.3 MB  both of the above
    (D) shard by window, 2 halves at lon -118.2326  113,065,984 + 101,658,624  each OVER; needs >= 4 shards, cross-shard drives
    (E) not built: segment R-tree 51.9 MB + segments_by_way/osm_features_by_cls 33.4 MB (dbstat), 40% of the file

(B) alone has 0.12% headroom - any OSM growth tips it over. No option was picked by T-0275 (a measurement task).
This is the owner's call: which roads the device corpus may lose is a product decision (owner route intent:
winding back roads beat the obvious highway), not an agent's.

## Log
- 2026-10-06T07:22:28Z filed by agent/claude-opus-5 (T-0275 owner) from T-0275's measured LA corpus; backlog until the owner picks.
