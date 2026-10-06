---
id: T-0273
title: FeatureSurpriseMe - the Surprise card on the home screen, picking from the bundled fallback corpus with Surprise.pick, showing name, hook, round-trip estimate, golden-hour line and four 'not this' buttons, with Open in Apple Maps
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Sources/FeatureSurpriseMe/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/, Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, .github/workflows/ios-screenshot.yml, ops/lib/, pins/PINS.yaml]
pins_affected: [P-PROD-02, P-PROD-03, P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0270, T-0271, T-0263]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a new Apple target FeatureSurpriseMe (imports DesignSystem, ScenicKit, PlaceStore only; added to the FeatureScenicHome LIBRARY PRODUCT's targets so no pbxproj edit) opens apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite read-only through PlaceStore, maps places to SurpriseCandidate, and calls Surprise.pick with an OFFLINE reach (ruled: straight-line distance x a ruled road factor / a ruled speed, labelled 'estimate' on the card; the /isochrone reach replaces it when the client exists) - the mapping and the offline reach are Linux-tested in ScenicKit by full equality"
  - "the card shows the place name, its class, the round-trip minutes with the estimate badge, the golden-hour line from SurpriseReason when present, Open in Apple Maps (through the same safety-disclaimer gate as home - P-SAFE-03's whitelist extended, never bypassed) and four 'not this' buttons feeding SurpriseFeedback; the attribution footer stays visible; every control has an accessibility identifier"
  - "ios-compile and ios-screenshot dispatched GREEN on the branch with a '-screen surprise' shot in both themes, downloaded and described in the Log; the P-SAFE-03 / P-ATTR-01 guards updated by whitelist and seen red by a mutant (the card's Apple Maps button bypassing the gate)"
---
## Brief

M5 'Surprise card: hook, golden-hour line, round-trip + return leg, Take me there / Just drive a loop, 4 not-this'.
The engine (T-0253), the Swift reach port (T-0263) and the bundled corpus (T-0270) are merged; T-0271 shows how a new
Apple target ships through the FeatureScenicHome product without the xcodeproj lock. Places only carry name + class
today, so the hook line is ruled from class (no curation prose yet - T-0183).

## Log
- 2026-10-06T03:35:41Z filed by agent/claude-opus-5 (orchestrator) after PR #161 (T-0270) merged; starts when T-0271 releases package-swift.
- 2026-10-06T04:50:07Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0271 (#162) merged and released package-swift; copy its Entitlements-in-the-FeatureScenicHome-product shape and its frozen-block/digest updates.
