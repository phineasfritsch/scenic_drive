---
id: T-0275
title: MEASUREMENT - build the full-region LA corpus (ways + segments + places) from the region build's seam-deduped tile docs and measure it against the plan's 60 MB budget, before any acceptance predicate is written over it
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/regionbuild/, services/etl/etl/, services/etl/tests/, ops/etl-region]
pins_affected: [P-DATA-01, P-PROD-05]
reviewer: null
depends_on: [T-0274]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a ruled 'corpus' stage (after merge/places) feeds the merged tile docs through extractadapter --places-osm into etl.corpus for LA, run in the WSL image; the Log quotes, as each stage lands: ways in, segments out, places, per-table row counts, file bytes, build seconds, and the sqlite page/freelist stats - against the plan's corpus < 60 MB budget"
  - "if over budget, the Log measures at least two ruled reductions (e.g. drop geometry precision, drop low-score residential segments, shard by window) with their bytes and what each loses - the task does NOT pick one; it files the decision as the follow-up with the numbers"
  - "the stage is idempotent (two runs, identical content digest - P-DATA-01) and a regionbuild test over the fixture region pins the stage order and the corpus row counts by equality; no gitignored input deleted"
---
## Brief

T-0274 R1/stillOpen: regionbuild's merge writes "ways": [], so no full-region corpus exists - the device has only the
places-only fallback. Plan M2 exit: 'corpus < 60 MB; PMTiles < 120 MB'. CLAUDE.md: an acceptance over real data is
written AFTER its population is measured, so this is filed as a measurement task.

## Log
- 2026-10-06T05:42:16Z filed by agent/claude-opus-5 (orchestrator) after PR #163 (T-0274) merged.
