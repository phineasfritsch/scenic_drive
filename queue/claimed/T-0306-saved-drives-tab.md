---
id: T-0306
title: Saved drives in the app - save from the route preview, a Saved list (newest first, rename, delete), "needs a re-plan" shown honestly, and replay as one plan with the saved waypoints at today's time
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T19:10:14Z
lease_expires_at: 2026-10-08T15:10:14Z
worktree: .worktrees/T-0306
branch: task/T-0306
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/PlaceStore/, Tests/PlaceStoreTests/, Sources/ScenicAPIClient/ClientPlanner.swift, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/Packages/ScenicApp/Tests/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
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
- 2026-10-07T19:10:14Z claimed by agent/claude-opus-5; lease until 2026-10-08T15:10:14Z
- 2026-10-07T19:15:04Z MEASURE, then RULINGS before code. agent/claude-opus-5 (owner).
  MEASURED: root Package.swift - PlaceStore depends on GRDB only, ScenicKit on nothing, ScenicAPIClient on ScenicKit;
  no root target sees both ScenicKit and PlaceStore. ScenicApp/Package.swift - FeaturePlanSheet already depends on
  DesignSystem + ScenicKit + PlaceStore and rides the FeatureScenicHome product the shell links. PlanResponse carries
  route, lambda and `waypoints` (scenicPlanner.ts `decisionPoints(chosen)`) and NO segment ids; PlanPreview (what the
  sheet sees) carries neither waypoints nor lambda. SavedDrive (T-0290 R3): name, segments (segmentID + 5-dp
  midpoint), lambdaE5, budgetMinutes, createdAt, needsReplan - no origin, no destination place, no ETA. FiveDecimals
  REFUSES more than 5 dp (never rounds). services/api/src/planRequest.ts: BODY_KEYS = ["origin", "destination",
  "budget_minutes", "departs_at"], ORIGIN_KEYS lat/lon at 2 dp, DESTINATION_KEYS = ["place"] (a corpus place id).
  check-map-attribution-sheet SHEET_PRESENTERS = .sheet( .fullScreenCover( .popover( .inspector( presentationDetents.
  - R1 WHERE: the Saved list lives in FeaturePlanSheet as in-sheet content of the full-height plan sheet (a "Saved"
    toolbar button switches the sheet's content; no NavigationLink push, no .sheet/.alert/.confirmationDialog). NO new
    target, NO Package.swift edit, NO new presentation, so P-ATTR-01's whitelist is unchanged.
  - R2 CONVERSION, in three hops because no root target sees both ScenicKit and PlaceStore: (a) ClientPlanner.preview
    now carries PlanResponse.waypoints and .lambda into PlanPreview (two new fields); (b) ScenicKit `SavedDraft.of(
    preview, budgetMinutes:, name:, createdAt:)` is THE rounding site: midpoints = [route.first] + waypoints +
    [route.last], each axis and lambda rounded ONCE to 5 dp, half away from zero ((v * 1e5).rounded() / 1e5); an empty
    route gives nil (nothing to save, the Save button is not offered); (c) PlaceStore `SavedDrive.unresolved(...)`
    builds the T-0290 value through the existing refusing gate (FiveDecimals refuses, never rounds - so a value is
    rounded once, never twice), every segment id `SavedSegment.unplaced` = -1, and the app then runs the shipped
    `SavedDriveResolver.resolve` against the bundled corpus (nearest within 25 m, else needsReplan) before saving. The
    route's two ends are kept so replay has an origin and a destination: the T-0290 shape holds neither otherwise.
    Full-equality tables: ScenicAPIClientTests (PlanResponse -> ClientPlanner.preview -> SavedDraft.of, one table) and
    PlaceStoreTests (SavedDraft-shaped doubles -> SavedDrive.unresolved, not GRDB-gated).
  - R3 REPLAY vs THE INVARIANT. The plan says "replay = one /plan with the saved waypoints"; CLAUDE.md says "the server
    never receives more than one coordinate per user action, never more than 2 decimal places", and the whitelist
    accepts exactly origin{lat,lon at 2 dp} + destination{place} + budget_minutes + departs_at. RULED: the invariant
    wins and the whitelist is not widened. A replay is ONE /plan whose origin is the saved first point at 2 dp (the
    one coordinate), whose destination is the corpus place nearest the saved last point (found on the device, within
    0.01 deg), and whose budget is the saved budget; the waypoints never leave the device - they key the re-resolve
    and decide needsReplan. "At today's time": like every plan today, no departs_at is sent, so the Worker plans for
    now. The replay goes through PlanSheet's one gate (`PlanSheet.replay(from:to:budgetMinutes:)` -> startPlanning),
    so P-SAFE-03 holds. "+31 not +25, say so": NOT shipped - a SavedDrive holds no ETA (T-0290 shape, nothing else),
    so there is nothing to compare against; recorded, not faked.
  - R4 STATE MACHINE: ScenicKit `SavedList` over `SavedRow` (id, name, createdAt, needsReplan, start, end, budget -
    no address field; the row's shown lines are its name and a detail line with no coordinate). States loading, list,
    renaming(id, text), confirmDelete(id), needsReplan(id), replaying(id). A rename commits the trimmed text of 1...60
    characters, otherwise stays renaming. Replay of a needsReplan drive (or one with no nearby place) goes to
    needsReplan with its own copy line and issues nothing. Rows are kept newest first (createdAt desc, id desc).
  - R5 PROOF: tests first, run RED by name; population ops/mutate/savedlist.py (+_mutations, _run) with a literal
    floor; digests re-approved for every touched Sources/ and apps/ios file; ios-compile + ios-screenshot dispatched.
  - R6 TOUCHES WIDENED (ruled on contact, the pre-commit hook refused): R2 hop (a) is ClientPlanner.preview, so
    `Sources/ScenicAPIClient/ClientPlanner.swift` and `Tests/ScenicAPIClientTests/` join touches; the existing
    PlanSheetGateTests "a 200 reaches the sheet as the preview of exactly that response" now expects the waypoints
    and lambda too (its full-equality oracle, widened by the two new fields).
