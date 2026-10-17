---
id: T-0400
title: Preview "Learned from N drives" needs the corridor sample count on PlanPreview
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/, ops/lib/, queue/]
pins_affected: [P-SAFE-07]
reviewer: null
depends_on: [T-0396]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Owner ruling 2026-10-17 ("go with recs"): after a corridor has >= 5 learned samples the preview's estimate tag is
replaced by .footnote "Learned from N drives" with the count shown (library "Plan preview" row 5, Flighty #097).
T-0396 R4 ruled it out: PlanPreview carries only `etaIsEstimate`; RetimedPreview folds the provider's retime into
one Bool, so the sheet never has N in hand.

Scope: carry the minimum learned-sample count over the drawn route's corridor edges from the traffic provider's
retime through RetimedPreview onto PlanPreview (nil when the Worker's ETA stands), and show the successor line only
when that count is >= 5 AND the ETA is not an estimate. The badge-until-5 invariant (P-SAFE-07) must hold on every
path; table-test every bound (4, 5, nil, estimate true with count 9).

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0396 R4.
