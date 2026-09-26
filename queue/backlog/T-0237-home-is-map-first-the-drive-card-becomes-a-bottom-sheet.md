---
id: T-0237
title: Home is map-first - the map fills the screen, the drive card becomes a bottom sheet with detents, the chips float over the map; attribution and the conditions line visible at every detent; re-shot
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapView.swift, apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapRouteCoordinator.swift, apps/ios/ScenicDriveUITests/, .github/workflows/ios-screenshot.yml, ops/lib/check-map-attribution, ops/lib/check-drive-copy, Sources/Handoff/, Tests/HandoffTests/]
pins_affected: [P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0236]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code, from the T-0236 screenshots (.artifacts/screens/home-light-T0236*.png): today the header is four paragraphs (title, road list, crow-flies line, timing, the 'Preview build' caption) and the map starts at 456 pt of 874 - the drive the app exists to show gets the bottom half. The ruling names: the sheet's detents (a collapsed height that shows the title, the conditions line and 'Open in Apple Maps'; a medium that adds the road list and the timing sentence; whether large exists), which copy moves where, whether the 'Preview build' caption survives (and where), and the camera padding per detent so the whole route stays in frame above the sheet"
  - "attribution: the composed map credit (T-0236 round 2) is visible and unobscured at EVERY detent in both themes - check-map-attribution binds the new mount (whitelist, identifier-anchored) and its --prove-red gains a row that hides the credit behind the sheet; the safety line 'Conditions change. Verify locally.' stays visible at every detent (P-SAFE-03's route-screen half)"
  - "the sheet cannot be dismissed (interactiveDismissDisabled) and the map stays interactive above it (presentationBackgroundInteraction); the chips sit over the map below the status bar with a legible background in both themes; every tap target >= 44 pt"
  - "ios-compile green on the head; ios-screenshot green on the SAME head producing light + dark at the collapsed AND medium detents (a launch argument selects the detent - four PNGs), downloaded to the main checkout's .artifacts/screens/home-*-T0237-*.png and DESCRIBED in the Log: where the route sits, the credit, the conditions line, the button"
  - "the credit pill never breaks a party across lines (T-0236 round 2's pill wrapped '... Natural Earth · ©' / 'OpenStreetMap contributors'): a non-breaking space after each copyright sign in the composed credit, or a layout that keeps each party whole - seen in the re-shot screenshots"
---
## Brief

The owner asked for a presentable app. The engine's Saddle Peak line is on the map as of T-0236, but the screen reads
as a document with a map under it. Every maps app the owner already uses is map-first with a sheet (Apple Maps,
Google Maps); the plan's UI section says 'sheets for planning' and 'lower-right reserved for attribution'.
Positioning is 'calm adventure' and the tagline 'Take the long way. Unwind.' - the collapsed sheet is the first thing
anyone sees, so its words are unhurried and few. No thrill words.

## Log
- 2026-09-25T23:35:28Z filed by agent/claude-opus-5 (orchestrator) from the T-0236 round-1 screenshot. Promote to ready/ when PR #130 merges (touches overlap FeatureScenicHome and check-map-attribution).
- 2026-09-26T01:30:07Z added by agent/claude-opus-5 (orchestrator): the pill-wrap cosmetic from rv2-t0236's recordable (3), deferred here because this task re-shoots the screen.
