---
id: T-0306
title: Saved drives in the app - save from the route preview, a Saved list (newest first, rename, delete), "needs a re-plan" shown honestly, and replay as one plan with the saved waypoints at today's time
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/PlaceStore/, Tests/PlaceStoreTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/Packages/ScenicApp/Tests/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05, P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0290, T-0294, T-0303]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULE FIRST in a dated Log entry: where the Saved list lives without a Package.swift edit (an existing feature target that already imports PlaceStore - no new target; if one is unavoidable, stop and rule it with the package-swift lock), how a PlanResponse becomes a SavedDrive (segment ids + 5-dp midpoints + lambda + budget - T-0290's shape, nothing else), and how replay builds one /plan request - RULE the disagreement between the plan's 'replay = one /plan with the saved waypoints' and the invariant 'the server never receives more than one coordinate per user action, never more than 2 dp' (read services/api/src/plan.ts's body whitelist: what can a replay send today?) and quote the ruling; never widen the Worker whitelist in this task"
  - "A ScenicKit state machine for the Saved list (loading, list, renaming, confirmDelete, needsReplan, replaying) with a table test over every transition by full equality; replay of a needsReplan drive is refused with its own copy line; the Saved list never shows an address (P-PRIV-05)"
  - "The PlanResponse -> SavedDrive conversion is a full-equality table including more-than-5-dp midpoints (rounded once, at save, with a ruled rule - never silently twice) and an empty route"
  - "Every map surface keeps AttributionFooter visible (P-ATTR-01: no partial-detent sheet over the map; any new presentation gets a typed whole-line approval); ios-compile + ios-screenshot pass on the head; digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt"
  - "A mutation population for the conversion and the state machine with a literal floor; three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Runtime lifecycles, Saved drives: "On-device (GRDB) only: segment ids + 5-dp midpoints + lambda + B; re-resolve on
corpus activation; mark needs re-plan if unresolved; replay = one /plan with the saved waypoints at the new time; if today
is +31 not +25, say so." T-0290 shipped the store; T-0294 the plan sheet and preview. Calm copy (memory owner-route-intent).

## Log
- 2026-10-07T19:09:58Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 saved drives UI).
