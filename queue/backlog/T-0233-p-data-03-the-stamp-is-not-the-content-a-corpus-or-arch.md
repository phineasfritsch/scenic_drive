---
id: T-0233
title: P-DATA-03 - the stamp is not the content: a corpus (or a PMTiles archive) stamped `la` whose ways are all in Marin passes both halves; compare meta.bbox against the region's own bbox
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, services/etl/tests/, pins/PINS.yaml]
pins_affected: [P-DATA-03]
reviewer: null
depends_on: [T-0219]
verify: [ops/test, ops/check-pins]
acceptance:
  - "both provenance halves gain a CONTENT limb: the artefact's meta.bbox (corpus.py writes it beside region; the PMTiles header carries bounds) must sit inside the region's own bbox read from services/etl/regions/<name>/region.json, with a ruled tolerance (state it as a number and where it comes from - a clip is smaller than its region, never larger); RED first with a fixture stamped `la` whose bbox is the Bay Area's, refused BY NAME, and a second mutant that widens the containment to a no-op; both added to each half's --prove-red table, the floors raised"
  - "P-DATA-03's text loses the sentence saying the stamp is unchecked against the content; the real artefacts on this box re-run through both halves (SCENIC_LA_CORPUS and SCENIC_LA_PMTILES) with their bbox lines quoted; the ETL suite count line; bash ops/check-pins --source-only and P-DATA-03's own assertion bare; check-line-cap, check-exec-bits, queue-check bare"
---
## Brief

From T-0219's build (PR #126, its STILL OPEN 1, written into the checker's docstring and the pin text rather than
hidden): both halves now assert that an artefact SAYS it is the active region and is not stale - neither asserts that
what is inside it is that region. `meta.bbox` is already written beside `region` by services/etl/etl/corpus.py, and the
PMTiles header already carries bounds (T-0197's check prints them: -119.000000,33.700000,-117.850000,34.450000), so the
comparison is one read on each side against services/etl/regions/<name>/region.json.

## Log
- 2026-09-19T21:59:04Z filed by agent/claude-opus-5[1m] (orchestrator, from T-0219's STILL OPEN 1 on PR #126). Not started; after PR #126 merges.
