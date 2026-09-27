---
id: T-0247
title: the muted menu lines stack into darker ticks where they overlap - draw the unselected rows opaque (or as one merged geometry) so the map reads calm
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/MapAdapter/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, ops/lib/check-safety-disclaimer-pinned, .github/workflows/ios-screenshot.yml]
pins_affected: [P-ATTR-01]
reviewer: null
depends_on: [T-0246]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the unselected menu rows render with no alpha stacking: an opaque muted colour token (both themes) or one merged, deduplicated geometry - RULED in the Log; the pinned digests updated in the same commit; ios-screenshot on the head shows no darker ticks where rows overlap or double back (row 1's loop top, the Tuna Canyon wiggles, the Cold Canyon descent - rv1-t0246's list), described in the Log with a PIL measurement of the muted line's colour at two overlap points"
---
## Brief

From rv1-t0246's recordable (3) and the author's own note on PR #136: the 35%-alpha muted lines stack into small
darker ticks. Calm adventure is the positioning; a map with noise on it reads busier than it is.

## Log
- 2026-09-27T00:35:01Z filed by agent/claude-opus-5 (orchestrator) from PR #136's review.
