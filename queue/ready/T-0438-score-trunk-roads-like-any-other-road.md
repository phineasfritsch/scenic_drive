---
id: T-0438
title: Score trunk roads like any other road: only motorway and motorway_link carry scenic_score 0
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index, routing-config]
touches: [services/etl/, Sources/ScenicKit/, Tests/, ops/mutate/, ops/lib/, pins/, CLAUDE.md, services/routing/, docs/STATUS.md, queue/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "python -m pytest services/etl/tests -q: all pass, with byways.SCENIC_ZERO_CLASSES == {motorway, motorway_link}"
  - "ops/test prints TESTS linux=N/0 and ops/check-pins exits 0"
  - "the red run: the old four-class set restored makes the new trunk-is-scored tests fail"
  - "the rebuilt LA graph's Palisades Beach Rd / Malibu PCH edges carry scenic_score > 0 (router readback)"
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
