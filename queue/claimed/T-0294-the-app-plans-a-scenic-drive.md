---
id: T-0294
title: The app plans a scenic drive - typed destination from the corpus search, extra-minutes, Plan calls the Worker through ScenicAPIClient, and the preview shows the route, ETA vs fastest, the hazard strip and one copy line per PlanError
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T11:14:19Z
lease_expires_at: 2026-10-08T07:14:19Z
worktree: .worktrees/T-0294
branch: task/T-0294
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Sources/, apps/ios/Packages/ScenicApp/Tests/, apps/ios/ScenicDrive/ScenicDriveApp.swift, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/, pins/PINS.yaml, ops/mutate/]
pins_affected: [P-SAFE-03, P-PRIV-06, P-ATTR-01]
reviewer: null
depends_on: [T-0251, T-0254, T-0289]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: how the app composes features today (FeatureScenicHome product carries Entitlements + FeatureSurpriseMe to avoid pbxproj edits - T-0271/T-0273), what P-SAFE-03 / T-0289 content-pins cover in apps/ios, and the seam: feature targets import only DesignSystem, ScenicKit, PlaceStore and their own protocols (CLAUDE.md), so planning is a protocol in the feature and ScenicAPIClient is imported only by one new adapter target (like MapAdapter for MapLibre), carried in the product the shell already links - no project.pbxproj edit"
  - "The plan-sheet state machine lives in ScenicKit (Linux-testable): idle -> searching(query) -> destination chosen -> planning -> preview(route) | failed(PlanError); every PlanError case maps to exactly one copy line and one action per the plan's Degraded states row (quotaExhausted, planningPaused, routingOffline, noRoute, attestUnsupported, regionUnsupported, offlineDuringDrive, noScenicAlternative, unknownPlace, planRefused, invalidRequest, refusedOnDevice, unexpectedResponse) - a table test by full equality with a meta-test that the table covers every case of the enum (compile-time exhaustive switch plus a count)"
  - "The safety disclaimer still gates the first plan (P-SAFE-03): a test drives the state machine from first launch and shows no PlanClient call before acceptance (counting transport = 0), seen red then green"
  - "Location denied path (P-PRIV-06): the origin can be a typed place; no CoreLocation import in the root package; the request carries one coordinate at 2 dp (the existing PlanRequestBody guard)"
  - "The preview shows the AttributionFooter at every detent (P-ATTR-01 unchanged) and the 'estimate · no traffic data' badge; ios-compile and ios-screenshot CI green; content pins re-approved in the same diff for every apps/ios file touched"
  - "Mutation population for the state machine and the error-copy table with a literal floor; three entries MISSED before, CAUGHT by name after"
---
## Brief

Milestone M4: "Plan sheet (corpus FTS5 + Photon; departs-at); Route preview (hazard strip, explanation, badge);
PlanError states". Today the app never calls PlanClient (grep: only Sources/ScenicAPIClient uses it), so the core promise
- "Take the long way. Unwind." (memory owner-route-intent) - is not reachable from the phone. Photon is not deployed:
search is the corpus FTS5 only (PlaceStore T-0254); typed street addresses are a later task. Departs-at is out of scope.

## Log
- 2026-10-07T03:23:40Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M4 plan sheet); claim after T-0289 merges.
- 2026-10-07T11:14:19Z claimed by agent/claude-opus-5; lease until 2026-10-08T07:14:19Z
