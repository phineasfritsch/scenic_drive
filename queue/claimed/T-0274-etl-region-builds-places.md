---
id: T-0274
title: ops/etl-region builds places too - the osmium places pass (T-0266) and the fallback corpus (T-0270) wired into the region build, so a full LA corpus carries places and the fallback is rebuilt by one command
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T03:38:14Z
lease_expires_at: 2026-10-06T15:38:14Z
worktree: .worktrees/T-0274
branch: task/T-0274
exclusive: [scenic-index]
touches: [ops/etl-region, services/etl/regionbuild/, services/etl/etl/, services/etl/tests/, services/etl/regions/la/]
pins_affected: [P-DATA-01]
reviewer: null
depends_on: [T-0266, T-0270]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/etl-region la runs the placeallow osmium pass on the region's own input and passes --places-osm to the extract stage, so the region corpus has places at the T-0266 measured counts (quoted, per class, as the stage lands); a regionbuild test (fixture region) asserts the stage order and that places reach the corpus by exact equality"
  - "ops/etl-region la --fallback (or a ruled sub-command) rebuilds apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite from the same places and reproduces the committed file byte-for-byte (sha256 quoted twice); the command is the one T-0270's test_fallback_committed names as the rebuild"
  - "idempotent (P-DATA-01): two runs give identical corpus content digests; no gitignored large input is deleted (memory: worktree removal deletes ignored inputs)"
---
## Brief

T-0266 stillOpen: 'wiring the osmium places pass into ops/etl-region / regionbuild are separate tasks'; T-0270: the
fallback rebuild is manual. One command should build the region corpus with places and the fallback file.

## Log
- 2026-10-06T03:35:41Z filed by agent/claude-opus-5 (orchestrator) after PR #161 merged.
- 2026-10-06T03:38:14Z claimed by agent/claude-opus-5; lease until 2026-10-06T15:38:14Z
