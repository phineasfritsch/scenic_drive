---
id: T-0289
title: P-SAFE-03 fails OPEN through the Xcode project - pin project.pbxproj by digest, every root-package Swift file the app links, and make P-ATTR-01 call the whole-app content pin
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T21:12:14Z
lease_expires_at: 2026-10-07T11:12:14Z
worktree: .worktrees/T-0289
branch: task/T-0289
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
- 2026-10-06T21:12:14Z claimed by agent/claude-opus-5; lease until 2026-10-07T11:12:14Z
- 2026-10-06T21:18:32Z RULINGS before code. agent/claude-opus-5 (owner).
  - R1 WHERE. A new sourced lib ops/lib/check-safety-disclaimer-linked holds the new limb, require_pinned_linked
    APP_TREE ROOT; -pinned sources it and require_pinned_app_swift calls it as its LAST step, so every caller of the
    whole-app pin (check-safety-disclaimer today, check-map-attribution from this task) gets it with no second call
    site to forget. check-safety-disclaimer is at 300 lines and stays there (its summary echo line edited in place).
  - R2 ROOT, no new knob. The root tree is DERIVED: APP_TREE/../.. (apps/ios -> the repo top on every real run). No
    --root-tree flag and no env var a caller could point at a copy. The mutation table lays each copy out as
    m<N>/apps/ios beside m<N>/Package.swift and m<N>/Sources/, so rows 1-43 run unchanged and a row edits a root file
    as ../../Sources/... . check-map-attribution's table copies apps/ios bare; its rows are refused by earlier limbs
    and never reach this one (fail exits), and its --prove-red pre-probe runs the real tree, so it is not relaid.
  - R3 WHAT IS PINNED, all WHITELISTS by exact path + sha256 (CRLF->LF, pinned_digest): (a) every NON-Swift
    non-directory entry under apps/ios (project.pbxproj, Package.resolved, the shared scheme, ci_post_clone.sh,
    Info.plist, assets, bundled data - 13 today) - not the pbxproj alone, because the shell is an Xcode 26 BUILDABLE
    FOLDER (a .m/.c file dropped into ScenicDrive/ compiles with no pbxproj edit), a scheme pre-action and
    ci_post_clone.sh run shell at build time, and a pbxproj-only pin would be the next round's blacklist; the only
    allowance is ScenicDrive/Tiles/*.pmtiles and *.pmtiles.json (git-ignored twice, the owner's 63 MB archive in the
    MAIN checkout; neither compiles). (b) the root Package.swift. (c) EVERY non-directory entry under Sources/ (any
    extension, any depth; non-regular refused) - 109 *.swift today, ScenicPlanCLI included: the acceptance says every
    *.swift under Sources/, and a list of the products the app links would be a second list to keep true.
  - R4 path:/sources:. Every root Package.swift line carrying `path:` or `sources:` (trimmed, //-lines dropped) is
    compared WHOLE to a typed list (the six Sources/<T> targets and the six Tests/<T> test targets). Tests/ is not
    pinned and is not linked: the app's manifest depends on the root PRODUCTS, whose targets' path lines are the
    typed Sources ones; moving a Tests path onto a library is a digest change. ScenicApp's Package.swift path lines
    are already a whole-line whitelist in -doors (rv1-t0273 B2) and it is in PINNED_APP_SWIFT.
  - R5 RED FIRST. Rows 44-47 (T-0289) are committed to the table BEFORE the limb, then run against the unchanged
    guard in a detached worktree of that commit; each must come back UNREFUSED. 44 = rv3-t0273 recordable 1 exactly
    (pbxproj PBXFileReference + PBXBuildFile + Sources-phase entry for ../../tools/xcode-shell/SurpriseCard.swift,
    the file itself declaring a SurpriseCard whose button opens Apple Maps), 45 a one-line edit to
    Sources/Handoff/AppleMapsDirections.swift, 46 a new Sources/ScenicKit/Shadow.swift, 47 (beyond the acceptance)
    Handoff's root path: swapped to a new Vendor/Handoff. Only these rows run (owner-approved faster verification).
  - R6 COST, named so nobody reads it as free: every edit to any file under Sources/, to the root Package.swift or
    to any non-Swift file under apps/ios now re-approves its digest in -linked in the same commit. On a Mac whose
    Xcode wrote xcuserdata/ or .swiftpm/ under apps/ios the guard refuses (fail-closed by design; an xcuserdata
    scheme's pre-action runs shell). Not seen: remote package code (MapLibre, GRDB - Package.resolved pins the
    revision only), Swift reached by an absolute path outside the repo through a future pbxproj (the pbxproj is
    pinned, so that needs an approved digest first), and anything the -frozen/-doors readers cannot parse.
