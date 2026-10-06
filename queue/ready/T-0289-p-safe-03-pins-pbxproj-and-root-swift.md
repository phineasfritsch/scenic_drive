---
id: T-0289
title: P-SAFE-03 fails OPEN through the Xcode project - pin project.pbxproj by digest, every root-package Swift file the app links, and make P-ATTR-01 call the whole-app content pin
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0273]
verify: [ops/test, ops/check-pins]
acceptance:
  - "check-safety-disclaimer refuses by name any change to apps/ios/ScenicDrive.xcodeproj/project.pbxproj (sha256 pin, CRLF-normalised; the file changes ~10 times ever) and to EVERY *.swift under Sources/ (the root package the app links by path: ScenicKit, Handoff, PlaceStore, ScenicAPIClient, Telemetry...) - exact file list + per-file digest, the T-0273 require_pinned_app_swift pattern; any SwiftPM Package.swift path:/sources: pointing outside the pinned trees refused"
  - "prove-red rows (run ONLY the new rows, ~25 min each on the box): rv3-t0273's exact mutant (a pbxproj PBXFileReference/PBXBuildFile/Sources entry for ../../tools/xcode-shell/SurpriseCard.swift declaring a shadow SurpriseCard that opens Apple Maps) refused; a one-line edit to a root-package Swift file refused; a new root-package file refused - each by name"
  - "check-map-attribution (P-ATTR-01) calls the same whole-app pin; P-SAFE-03 and P-ATTR-01 prose APPENDED with dates naming the re-approval duty for pbxproj and root Swift edits"
---
## Brief

rv3-t0273 recordable 1 (PR #166, 2026-10-06): a pbxproj edit adding a Swift file from OUTSIDE apps/ios that declares a
module-local SurpriseCard shadows the gated card; check-safety-disclaimer exits 0 - the guard reads no pbxproj and no
Swift outside apps/ios. Pre-existing (not introduced by T-0273), but CLAUDE.md: a P-SAFE fail-open buys a round - urgent.
Plus rv3 recordable 3: P-ATTR-01 does not call require_pinned_app_swift.

## Log
- 2026-10-06T21:04:48Z filed by agent/claude-opus-5 (orchestrator) from rv3-t0273's recordable findings; urgent (P-SAFE fail-open).
